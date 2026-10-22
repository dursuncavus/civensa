"""Upgrade populated legacy freezes; preserve bytes, guards and safe downgrade."""
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from uuid import uuid4
import zipfile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.schema import CreateSchema, DropSchema
from sqlalchemy.orm import Session

from app.activity_contract_service import digest
from app.ar_export import build_activity_report_docx, TEMPLATE_PATH
from app import activity_sections_service as sections
from app.models import User

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('backend', ['postgresql', 'sqlite'])
def test_upgrade_preserves_legacy_frozen_bytes_and_sql_guards_and_safe_downgrade(tmp_path, monkeypatch, backend):
    admin = None
    if backend == 'postgresql':
        admin = create_engine(os.environ['CIVENSA_TEST_POSTGRES_URL'])
        schema = 'civ074_migration_' + uuid4().hex
        with admin.begin() as conn: conn.execute(CreateSchema(schema))
        url = make_url(os.environ['CIVENSA_TEST_POSTGRES_URL']).update_query_dict(
            {'options':'-csearch_path='+schema}).render_as_string(hide_password=False)
    else:
        url = f'sqlite:///{tmp_path / "ar-workflow.db"}'
    engine = create_engine(url)
    env = {**os.environ, 'DATABASE_URL':url}; env.pop('MIGRATION_DATABASE_URL', None)
    def migrate(command, revision):
        return subprocess.run([sys.executable, '-m', 'alembic', command, revision], cwd=ROOT,
            env=env, capture_output=True, text=True)
    # DOCX is a ZIP whose packaging timestamps otherwise follow the wall clock.
    # Hold only that clock fixed to compare complete bytes across the migration.
    monkeypatch.setattr(zipfile, 'time', SimpleNamespace(time=lambda:0,
        localtime=lambda *_:(2026,10,22,12,0,0,3,295,0)))
    payload = {'id':1, 'year':2027, 'organization':'Tarihî Belediye', 'department_id':1,
        'department':'Tarihî Müdürlük', 'frozen':False, 'revision':5, 'scope':'birim:1',
        'resources':{}, 'financial':{'tables':{},'entries':{},'statements':[]},
        'core':{'indicators':[]}, 'sections':[{'code':'I.A','title':'A- Misyon ve Vizyon','position':4,
            'depth':1,'blocks':[{'type':'paragraph','text':'Önceden dondurulmuş içerik.'}],
            'status':'ready','reason':'','missing':[]}]}
    raw = json.dumps(payload, ensure_ascii=False); sha256 = digest(raw)
    frozen = {**payload, 'frozen':True, 'sha256':sha256}
    before = build_activity_report_docx(frozen, TEMPLATE_PATH)
    try:
        result = migrate('upgrade', 'c067a1b2c3d4'); assert result.returncode == 0, result.stderr
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO organizations(id,name) VALUES (1,'Belediye')"))
            conn.execute(text("INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2027,'active','verified')"))
            conn.execute(text("INSERT INTO departments(id,organization_id,name,is_active) VALUES (1,1,'Müdürlük',true)"))
            conn.execute(text("INSERT INTO users(id,email,full_name,role,password_hash,is_active,position,must_change_password,can_submit) VALUES (1,'test@invalid','Test','strategy','unused',true,'staff',false,false)"))
            conn.execute(text("INSERT INTO ar_documents(id,organization_id,period_id,department_id,scope,definition_version,revision,created_by) VALUES (1,1,1,1,'birim:1',1,5,1)"))
            conn.execute(text("INSERT INTO ar_section_contents(id,document_id,definition_id,blocks_json,status,reason,copied_needs_review) VALUES (1,1,4,'[]','ready','',false)"))
            conn.execute(text('INSERT INTO ar_document_freezes(id,document_id,payload_json,sha256,created_by) VALUES (1,1,:payload,:sha,1)'), {'payload':raw,'sha':sha256})
        for _ in range(2):
            result = migrate('upgrade', 'head'); assert result.returncode == 0, result.stderr
        with engine.connect() as conn:
            stored, stored_sha = conn.execute(text('SELECT payload_json,sha256 FROM ar_document_freezes')).one()
        assert stored.encode() == raw.encode() and stored_sha == sha256
        with Session(engine) as db:
            preserved = sections.report_data(db, db.get(User, 1), 1)
        exported = build_activity_report_docx(preserved, TEMPLATE_PATH)
        assert exported == before
        # Empty new journal can be removed, without changing legacy data/guards.
        result = migrate('downgrade','c067a1b2c3d4'); assert result.returncode == 0, result.stderr
        result = migrate('upgrade','head'); assert result.returncode == 0, result.stderr
        with pytest.raises(DBAPIError, match='değiştirilemez'):
            with engine.begin() as conn: conn.execute(text("UPDATE ar_section_contents SET reason='değişiklik'"))
        with engine.begin() as conn:
            conn.execute(text("""INSERT INTO ar_unit_workflow_events(document_id,revision,action,from_status,to_status,
                reason,actor_id,actor_name,created_at,content_event_cursor,payload_json,sha256)
                VALUES (1,6,'submit','draft','submitted','',1,'Test','2026-10-22 12:00:00+03:00',0,'{}',:sha)"""), {'sha':digest('{}')})
        statements = ["UPDATE ar_unit_workflow_events SET reason='değişiklik'", 'DELETE FROM ar_unit_workflow_events']
        if backend == 'postgresql': statements.append('TRUNCATE ar_unit_workflow_events CASCADE')
        for statement in statements:
            with pytest.raises(DBAPIError, match='değiştirilemez'):
                with engine.begin() as conn: conn.execute(text(statement))
        result = migrate('downgrade','c067a1b2c3d4')
        assert result.returncode != 0 and 'Veriyi koruyan' in result.stderr
        with engine.connect() as conn:
            assert conn.execute(text('SELECT payload_json FROM ar_document_freezes')).scalar() == raw
            assert conn.execute(text('SELECT count(*) FROM ar_unit_workflow_events')).scalar() == 1
    finally:
        engine.dispose()
        if admin:
            with admin.begin() as conn: conn.execute(DropSchema(schema, cascade=True))
            admin.dispose()
