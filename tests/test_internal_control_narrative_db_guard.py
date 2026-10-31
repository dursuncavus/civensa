"""CIV-162: raw PostgreSQL authorship guards and populated function swaps."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.internal_control_narrative_guards import FUNCTIONS
from test_internal_control_monitoring import monitoring
from test_internal_control_narrative import second_director, synthetic

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[1]
OLD = 'c160a1b2c3d4'
NEW = 'c162a1b2c3d4'
ERROR = 'Görevler ayrılığı: veriyi giren veya değiştiren onaylayamaz.'


@pytest.fixture(params=[None, 'head'], ids=['metadata', 'migration-chain'])
def db(request, postgres_templates):
    with postgres_templates.clone(request.param) as engine:
        with Session(engine, expire_on_commit=False) as session:
            yield session


@pytest.fixture
def raw_event(db, monitoring):
    schema = db.get_bind().get_execution_options().get('schema_translate_map', {}).get(None)
    table = 'ic_narrative_events'
    if schema:
        table = db.bind.dialect.identifier_preparer.quote(schema) + '.' + table
    snapshot = json.dumps(synthetic(db, monitoring['period']))

    def insert(actor, revision, action, origin, destination):
        db.execute(text(f'INSERT INTO {table} '
            '(period_id, revision, action, from_status, to_status, actor_id, actor_name, reason, snapshot_json) '
            'VALUES (:period, :revision, :action, :origin, :destination, :actor, :name, :reason, :snapshot)'),
            dict(period=monitoring['period'].id, revision=revision, action=action,
                 origin=origin, destination=destination, actor=actor.id, name=actor.full_name,
                 reason='Test sentetik gerekçe', snapshot=snapshot))
        db.commit()
    return insert


def test_return_resubmit_does_not_clear_writer(db, monitoring, second_director, raw_event):
    a, b = monitoring['strategy'], second_director
    raw_event(a, 1, 'save', 'draft', 'draft')
    raw_event(a, 2, 'submit', 'draft', 'submitted')
    raw_event(b, 3, 'return', 'submitted', 'returned')
    raw_event(a, 4, 'submit', 'returned', 'submitted')
    with pytest.raises(DBAPIError, match=ERROR):
        raw_event(a, 5, 'approve', 'submitted', 'approved')
    db.rollback()
    raw_event(b, 5, 'approve', 'submitted', 'approved')


def test_last_approve_clears_earlier_save_but_new_save_blocks(db, monitoring, second_director, raw_event):
    a, b = monitoring['strategy'], second_director
    raw_event(a, 1, 'save', 'draft', 'draft')
    raw_event(a, 2, 'submit', 'draft', 'submitted')
    raw_event(b, 3, 'approve', 'submitted', 'approved')
    raw_event(b, 4, 'reopen', 'approved', 'draft')
    raw_event(a, 5, 'submit', 'draft', 'submitted')
    raw_event(a, 6, 'approve', 'submitted', 'approved')
    raw_event(b, 7, 'reopen', 'approved', 'draft')
    raw_event(a, 8, 'save', 'draft', 'draft')
    raw_event(a, 9, 'submit', 'draft', 'submitted')
    with pytest.raises(DBAPIError, match=ERROR):
        raw_event(a, 10, 'approve', 'submitted', 'approved')
    db.rollback()
    raw_event(b, 10, 'approve', 'submitted', 'approved')


def normalize(value):
    return ' '.join(value.split())


def function_body(db):
    schema = db.get_bind().get_execution_options().get('schema_translate_map', {}).get(None)
    return db.execute(text('SELECT p.prosrc FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace '
        "WHERE p.proname='civ160_event_guard' AND n.nspname=COALESCE(:schema, current_schema())"),
        {'schema': schema}).scalar_one()


def test_function_body_equals_metadata_sql(db):
    assert normalize(function_body(db)) == normalize(FUNCTIONS[1].split('$$')[1])


def test_migration_changes_only_approval_boundary():
    old = runpy.run_path(str(ROOT / 'migrations/versions/c160a1b2c3d4_internal_control_narrative.py'))['GUARDS'][1]
    migration = runpy.run_path(str(ROOT / 'migrations/versions/c162a1b2c3d4_narrative_approval_boundary.py'))
    frozen = old.replace('CREATE FUNCTION', 'CREATE OR REPLACE FUNCTION', 1)
    assert migration['OLD_FUNCTION'] == frozen
    assert migration['NEW_FUNCTION'] == frozen.replace(
        "WHERE period_id=p.id AND action IN ('return','reopen');",
        "WHERE period_id=p.id AND action = 'approve';")
    assert migration['NEW_FUNCTION'].replace('CREATE OR REPLACE FUNCTION', 'CREATE FUNCTION', 1) == FUNCTIONS[1]


def test_populated_migration_roundtrip(postgres_templates):
    # Start at c160 with real rows; each step replaces only the guard function.
    with postgres_templates.clone(OLD) as engine:
        with Session(engine) as session:
            session.execute(text("INSERT INTO organizations(id,name) VALUES (1,'Test sentetik')"))
            session.execute(text("INSERT INTO departments(id,organization_id,name) VALUES (1,1,'Test birim')"))
            session.execute(text("INSERT INTO users(id,email,full_name,role,password_hash,is_active,department_id,position) "
                "VALUES (1,'test@civ162.invalid','Test A','strategy','unused',true,1,'director')"))
            session.commit()
            from app import internal_control_service as ic
            from app import internal_control_monitoring_service as m
            from app import internal_control_narrative_service as n
            from app.models import User
            from test_internal_control import workbook, action_row
            actor = session.get(User, 1)
            batch, _ = ic.create_import(session, actor, workbook([action_row(**{'7': 'Test birim'})]), 'civ162-test.xlsx')
            plan = ic.commit_import(session, actor, batch.id)
            session.commit()
            ic.activate_plan(session, actor, plan.id)
            session.commit()
            period = m.open_period(session, actor, plan.id, 2027, 1, m.today(session))
            session.commit()
            n.save(session, actor, period.id, 0, {})
            session.commit()
            before = session.execute(text('SELECT * FROM ic_narrative_events ORDER BY id')).all()
            original = function_body(session)
        old_sql = runpy.run_path(str(ROOT / 'migrations/versions/c160a1b2c3d4_internal_control_narrative.py'))['GUARDS'][1]
        assert normalize(original) == normalize(old_sql.split('$$')[1])
        env = {**os.environ, 'DATABASE_URL': engine.url.render_as_string(hide_password=False)}
        env.pop('MIGRATION_DATABASE_URL', None)
        for direction, target in [('upgrade', NEW), ('downgrade', OLD), ('upgrade', NEW)]:
            result = subprocess.run([sys.executable, '-m', 'alembic', direction, target],
                cwd=ROOT, env=env, capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
            with Session(engine) as session:
                rows = session.execute(text('SELECT * FROM ic_narrative_events ORDER BY id')).all()
                assert len(rows) == len(before) == 1
                assert rows == before
                assert session.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == target
                expected = original if target == OLD else FUNCTIONS[1].split('$$')[1]
                assert normalize(function_body(session)) == normalize(expected)
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        scripts = ScriptDirectory.from_config(Config(str(ROOT / 'alembic.ini')))
        assert scripts.get_heads() == [NEW]
        assert scripts.get_revision(NEW).down_revision == OLD
