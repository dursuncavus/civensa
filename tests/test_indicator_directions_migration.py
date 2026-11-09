"""PostgreSQL upgrade/downgrade, constraints and append-only SQL guards."""
import os
from pathlib import Path
import subprocess
import sys

from alembic.config import Config
from alembic.script import ScriptDirectory
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[1]


def test_direction_migration_roundtrip_and_history_preservation(postgres_templates):
    scripts = ScriptDirectory.from_config(Config(str(ROOT / 'alembic.ini')))
    revision = scripts.get_revision('c197a1b2c3d4')
    assert scripts.get_heads() == [revision.revision]
    with postgres_templates.clone(revision.down_revision) as engine:
        def migrate(action, target, ok=True):
            result = subprocess.run([sys.executable, '-m', 'alembic', action, target], cwd=ROOT,
                env={**os.environ, 'DATABASE_URL': engine.url.render_as_string(hide_password=False)},
                capture_output=True, text=True)
            assert (result.returncode == 0) == ok, result.stderr
            return result
        migrate('upgrade', revision.revision)
        migrate('downgrade', revision.down_revision)
        assert 'indicator_directions' not in inspect(engine).get_table_names()
        migrate('upgrade', revision.revision)
        migrate('upgrade', revision.revision)
        with engine.begin() as c:
            c.exec_driver_sql("INSERT INTO organizations(id,name) VALUES (1,'Sentetik Belediye')")
            c.exec_driver_sql("INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2027,'active','verified')")
            c.exec_driver_sql("INSERT INTO users(id,email,full_name,role,password_hash,is_active) VALUES (1,'test@invalid','Test','strategy','unused',true)")
            c.exec_driver_sql("INSERT INTO indicator_identities(indicator_id,organization_id) VALUES ('synthetic-197',1)")
            c.exec_driver_sql("INSERT INTO indicator_directions(indicator_id,period_id,direction,reason,created_by,created_at) VALUES ('synthetic-197',1,'lower','Sentetik süre hedefi',1,now())")
        for statement in ["UPDATE indicator_directions SET direction='higher'", 'DELETE FROM indicator_directions', 'TRUNCATE indicator_directions']:
            with pytest.raises(DBAPIError, match='geçmişi değiştirilemez'):
                with engine.begin() as c:
                    c.exec_driver_sql(statement)
        for direction, reason in [('invalid', 'Gerekçe'), ('lower', '   ')]:
            with pytest.raises(DBAPIError):
                with engine.begin() as c:
                    c.execute(text("INSERT INTO indicator_directions(indicator_id,period_id,direction,reason,created_by,created_at) VALUES ('synthetic-197',1,:direction,:reason,1,now())"), dict(direction=direction, reason=reason))
        result = migrate('downgrade', revision.down_revision, ok=False)
        assert 'veriyi koruyan aktarım' in result.stderr
        with engine.connect() as c:
            assert c.exec_driver_sql('SELECT direction,reason FROM indicator_directions').one() == ('lower', 'Sentetik süre hedefi')
            assert c.exec_driver_sql('SELECT version_num FROM alembic_version').scalar_one() == revision.revision
