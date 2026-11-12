"""Removal migration preserves evidence and enforces SQL-level workflow guards."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

ROOT = Path(__file__).resolve().parents[1]


def migrate(url, action, revision):
    env = {**os.environ, 'DATABASE_URL': url}
    env.pop('MIGRATION_DATABASE_URL', None)
    return subprocess.run([sys.executable, '-m', 'alembic', action, revision],
                          cwd=ROOT, env=env, capture_output=True, text=True)


def seed(conn):
    for statement in [
        "INSERT INTO organizations(id,name) VALUES (1,'Sentetik Belediye')",
        "INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2026,'active','verified')",
        "INSERT INTO departments(id,organization_id,name,is_active) VALUES (1,1,'Sentetik Müdürlük',true),(2,1,'Diğer Müdürlük',true)",
        "INSERT INTO users(id,email,full_name,role,password_hash,is_active,position,must_change_password,can_submit,department_id) VALUES (1,'test@invalid','Sentetik Müdür','department','unused',true,'staff',false,false,1),(2,'other@invalid','Diğer Müdür','department','unused',true,'staff',false,false,2)",
        "INSERT INTO ar_documents(id,organization_id,period_id,department_id,scope,definition_version,revision,created_by) VALUES (1,1,1,1,'birim:1',1,0,1),(2,1,1,2,'birim:2',1,0,2)",
    ]:
        conn.execute(text(statement))
    for photo_id in range(1, 4):
        conn.execute(text("""INSERT INTO ar_unit_photos(id,document_id,activity_key,caption,filename,sha256,file_data,created_by)
            VALUES (:id,1,'1:51','Sentetik fotoğraf','sentetik.png',:sha,:data,1)"""),
            {'id': photo_id, 'sha': 'a' * 64, 'data': b'photo'})


def test_sqlite_removal_migration_roundtrip_and_data_preservation(tmp_path):
    url = f'sqlite:///{tmp_path / "migration.db"}'
    for action, revision in [('upgrade', 'head'), ('downgrade', 'c219a1b2c3d4'), ('upgrade', 'head')]:
        result = migrate(url, action, revision)
        assert result.returncode == 0, result.stderr
    engine = create_engine(url)
    try:
        with engine.begin() as conn:
            seed(conn)
            conn.execute(text('INSERT INTO ar_unit_photo_removals(document_id,photo_id,created_by) VALUES (1,1,1)'))
        result = migrate(url, 'downgrade', 'c219a1b2c3d4')
        assert result.returncode != 0 and 'veriyi koruyan' in result.stderr
        with engine.connect() as conn:
            assert conn.execute(text('SELECT count(*) FROM ar_unit_photo_removals')).scalar() == 1
            assert conn.execute(text('SELECT count(*) FROM ar_unit_photos')).scalar() == 3
    finally:
        engine.dispose()


@pytest.mark.postgres
def test_postgres_removal_guards_and_data_preserving_downgrade(postgres_templates):
    with postgres_templates.clone('c219a1b2c3d4') as engine:
        url = engine.url.render_as_string(hide_password=False)
        with engine.begin() as conn:
            seed(conn)
        result = migrate(url, 'upgrade', 'head')
        assert result.returncode == 0, result.stderr
        def blocked(statement):
            with pytest.raises(DBAPIError):
                with engine.begin() as conn:
                    conn.execute(text(statement))
        # Wrong document/actor, immutable decisions, unique removal and truncate.
        blocked('INSERT INTO ar_unit_photo_removals(document_id,photo_id,created_by) VALUES (2,1,1)')
        blocked('INSERT INTO ar_unit_photo_removals(document_id,photo_id,created_by) VALUES (1,1,2)')
        with engine.begin() as conn:
            conn.execute(text('INSERT INTO ar_unit_photo_removals(document_id,photo_id,created_by) VALUES (1,1,1)'))
        for statement in ['UPDATE ar_unit_photo_removals SET created_by=2',
                          'DELETE FROM ar_unit_photo_removals', 'TRUNCATE ar_unit_photo_removals',
                          'INSERT INTO ar_unit_photo_removals(document_id,photo_id,created_by) VALUES (1,1,1)',
                          'DELETE FROM ar_unit_photos', "UPDATE ar_unit_photos SET caption='Başka'"]:
            blocked(statement)
        for revision, action, before, after in [(1, 'submit', 'draft', 'submitted'),
                                                (2, 'approve', 'submitted', 'approved')]:
            with engine.begin() as conn:
                conn.execute(text("""INSERT INTO ar_unit_workflow_events(document_id,revision,action,from_status,to_status,
                    reason,actor_id,actor_name,created_at,content_event_cursor,payload_json,sha256)
                    VALUES (1,:revision,:action,:before,:after,'',1,'Müdür',now(),0,'{}',repeat('a',64))"""),
                    dict(revision=revision, action=action, before=before, after=after))
            blocked('INSERT INTO ar_unit_photo_removals(document_id,photo_id,created_by) VALUES (1,2,1)')
        with engine.begin() as conn:
            conn.execute(text("""INSERT INTO ar_unit_workflow_events(document_id,revision,action,from_status,to_status,
                reason,actor_id,actor_name,created_at,content_event_cursor)
                VALUES (1,3,'reopen','approved','draft','Düzeltme',1,'Müdür',now(),0)"""))
            conn.execute(text('INSERT INTO ar_unit_photo_removals(document_id,photo_id,created_by) VALUES (1,2,1)'))
            conn.execute(text("""INSERT INTO ar_document_freezes(document_id,payload_json,sha256,created_by)
                VALUES (1,'{}',repeat('a',64),1)"""))
        blocked('INSERT INTO ar_unit_photo_removals(document_id,photo_id,created_by) VALUES (1,3,1)')
        result = migrate(url, 'downgrade', 'c219a1b2c3d4')
        assert result.returncode != 0 and 'veriyi koruyan' in result.stderr
        with engine.connect() as conn:
            assert conn.execute(text('SELECT count(*) FROM ar_unit_photo_removals')).scalar() == 2
            assert conn.execute(text('SELECT count(*) FROM ar_unit_photos')).scalar() == 3
            assert conn.execute(text('SELECT version_num FROM alembic_version')).scalar() == 'c219b1c2d3e4'
