"""PostgreSQL round-trip and SQL guards, including data-preserving downgrade."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[1]


def test_migration_roundtrip_preserves_data_and_guards_approved_rows(postgres_templates):
    with postgres_templates.clone('c197a1b2c3d4') as engine:
        env = {**os.environ, 'DATABASE_URL': engine.url.render_as_string(hide_password=False)}
        env.pop('MIGRATION_DATABASE_URL', None)
        def migrate(action, revision):
            return subprocess.run([sys.executable, '-m', 'alembic', action, revision],
                cwd=ROOT, env=env, capture_output=True, text=True)
        for action, target in [('upgrade', 'head'), ('downgrade', 'c197a1b2c3d4'), ('upgrade', 'head')]:
            result = migrate(action, target)
            assert result.returncode == 0, result.stderr
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO organizations(id,name) VALUES (1,'Sentetik Belediye')"))
            conn.execute(text("INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2026,'active','verified')"))
            conn.execute(text("INSERT INTO departments(id,organization_id,name,is_active) VALUES (1,1,'Sentetik Müdürlük',true)"))
            conn.execute(text("INSERT INTO users(id,email,full_name,role,password_hash,is_active,position,must_change_password,can_submit) VALUES (1,'test@invalid','Sentetik Müdür','department','unused',true,'staff',false,false)"))
            conn.execute(text("INSERT INTO ar_documents(id,organization_id,period_id,department_id,scope,definition_version,revision,created_by) VALUES (1,1,1,1,'birim:1',1,0,1)"))
            conn.execute(text("INSERT INTO ar_unit_tables(document_id,kind,payload_json) VALUES (1,'1','{\"rows\":[]}')"))
            conn.execute(text("INSERT INTO ar_unit_photos(document_id,activity_key,caption,filename,sha256,file_data,created_by) VALUES (1,'1:51','Sentetik fotoğraf','sentetik.png',repeat('a',64),decode('01','hex'),1)"))
            conn.execute(text("""INSERT INTO ar_unit_workflow_events(document_id,revision,action,from_status,to_status,
                reason,actor_id,actor_name,created_at,content_event_cursor,payload_json,sha256)
                VALUES (1,1,'submit','draft','submitted','',1,'Müdür',now(),0,'{}',repeat('a',64))"""))
        for statement in ["UPDATE ar_unit_tables SET payload_json='{}'", 'DELETE FROM ar_unit_tables',
                          "INSERT INTO ar_unit_tables(document_id,kind,payload_json) VALUES (1,'2','{}')",
                          "UPDATE ar_unit_photos SET caption='Değiştirildi'", 'DELETE FROM ar_unit_photos',
                          'TRUNCATE ar_unit_tables']:
            with pytest.raises(DBAPIError):
                with engine.begin() as conn: conn.execute(text(statement))
        with engine.begin() as conn:
            conn.execute(text("""INSERT INTO ar_unit_workflow_events(document_id,revision,action,from_status,to_status,
                reason,actor_id,actor_name,created_at,content_event_cursor,payload_json,sha256)
                VALUES (1,2,'approve','submitted','approved','',1,'Strateji',now(),0,'{}',repeat('a',64))"""))
        with pytest.raises(DBAPIError):
            with engine.begin() as conn: conn.execute(text("UPDATE ar_unit_tables SET payload_json='{}'"))
        result = migrate('downgrade', 'c197a1b2c3d4')
        assert result.returncode != 0 and 'veriyi koruyan' in result.stderr
        with engine.connect() as conn:
            assert conn.execute(text('SELECT payload_json FROM ar_unit_tables')).scalar() == '{"rows":[]}'
            assert conn.execute(text('SELECT count(*) FROM ar_unit_photos')).scalar() == 1
            assert conn.execute(text('SELECT version_num FROM alembic_version')).scalar() == 'c219a1b2c3d4'
