"""One additive Alembic head and refusal to discard a populated preview store."""
import os
from pathlib import Path
import subprocess
import sys
import pytest
from sqlalchemy import inspect, text
from alembic.config import Config
from alembic.script import ScriptDirectory

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[1]


def test_actual_preview_migration(postgres_templates):
    scripts = ScriptDirectory.from_config(Config(str(ROOT/'alembic.ini')))
    assert scripts.get_heads() == ['c192a1b2c3d4']
    with postgres_templates.clone('c185a1b2c3d4') as engine:
        def migrate(action, revision, ok=True):
            result = subprocess.run([sys.executable, '-m', 'alembic', action, revision], cwd=ROOT,
                env={**os.environ, 'DATABASE_URL':engine.url.render_as_string(hide_password=False)},
                capture_output=True, text=True)
            assert (result.returncode == 0) == ok, result.stderr
            return result
        migrate('upgrade', 'head')
        assert 'actual_imports' in inspect(engine).get_table_names()
        migrate('downgrade', 'c185a1b2c3d4')
        assert 'actual_imports' not in inspect(engine).get_table_names()
        migrate('upgrade', 'head')
        with engine.begin() as c:
            c.exec_driver_sql("INSERT INTO organizations(id,name) VALUES (1,'Sentetik Belediye')")
            c.exec_driver_sql("INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2026,'active','verified')")
            c.exec_driver_sql("INSERT INTO users(id,email,full_name,role,password_hash,is_active,position) VALUES (1,'test@invalid','Test','strategy','unused',true,'staff')")
            c.exec_driver_sql("INSERT INTO publications(id,period_id,version,snapshot_json,sha256,template_version,created_by,created_at) VALUES (1,1,1,'{}','hash',1,1,now())")
            c.exec_driver_sql('INSERT INTO activity_reports(id,organization_id,period_id,current_revision,lock_version) VALUES (1,1,1,1,0)')
            c.exec_driver_sql("""INSERT INTO activity_report_revisions(id,report_id,revision,publication_id,publication_sha256,contract_version,diff_json,revision_reason,created_by,created_at)
                VALUES (1,1,1,1,'hash','1.0','[]','Sentetik',1,now())""")
            c.exec_driver_sql("""INSERT INTO actual_imports(report_revision_id,actor_id,source_sha256,preview_json,created_at)
                VALUES (1,1,'hash','{}',now())""")
        result = migrate('downgrade', 'c185a1b2c3d4', ok=False)
        assert 'veriyi koruyan aktarım' in result.stderr
        with engine.connect() as c:
            assert c.execute(text('SELECT count(*) FROM actual_imports')).scalar() == 1
            assert c.execute(text('SELECT version_num FROM alembic_version')).scalar() == 'c192a1b2c3d4'
