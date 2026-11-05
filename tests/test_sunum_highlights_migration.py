"""One additive head, SET NULL photos and refusal to discard editorial rows."""
import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy import inspect, text
import pytest

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[1]


def test_upgrade_downgrade_preserves_existing_rows(postgres_templates):
    with postgres_templates.clone('c184a1b2c3d4') as engine:
        def migrate(action, revision, ok=True):
            result = subprocess.run([sys.executable, '-m', 'alembic', action, revision], cwd=ROOT,
                env={**os.environ, 'DATABASE_URL':engine.url.render_as_string(hide_password=False)},
                capture_output=True, text=True)
            assert (result.returncode == 0) == ok, result.stderr
            return result
        migrate('upgrade', 'head')
        assert 'sunum_highlights' in inspect(engine).get_table_names()
        migrate('downgrade', 'c184a1b2c3d4')
        assert 'sunum_highlights' not in inspect(engine).get_table_names()
        migrate('upgrade', 'head')
        with engine.begin() as c:
            c.exec_driver_sql("INSERT INTO organizations(id,name) VALUES (1,'Sentetik Belediye')")
            c.exec_driver_sql("INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2027,'active','verified')")
            c.exec_driver_sql("INSERT INTO departments(id,organization_id,name,is_active) VALUES (1,1,'Fen İşleri',true)")
            c.exec_driver_sql("INSERT INTO users(id,email,full_name,role,password_hash,is_active,position,department_id) VALUES (1,'test@invalid','Test','strategy','unused',true,'staff',1)")
            c.execute(text('''INSERT INTO sunum_photos(id,organization_id,period_id,year,department_id,
                caption,kind,webp_data,thumb_data,width,height,sha256,byte_size,consent_confirmed,
                selected,sort_order,created_by,created_at)
                VALUES (1,1,1,2027,1,'Tamamlanan iş','single',:data,:data,10,10,:sha,4,true,false,0,1,now())'''), dict(data=b'test',sha='0'*64))
            c.exec_driver_sql("""INSERT INTO sunum_highlights(organization_id,period_id,year,kind,department_id,
                fact_key,sentence,photo_id,selected,sort_order,created_by,created_at,updated_at)
                VALUES (1,1,2027,'feature',1,'unit:1:staff','İş tamamlandı.',1,true,0,1,now(),now())""")
        result = migrate('downgrade', 'c184a1b2c3d4', ok=False)
        assert 'veriyi koruyan aktarım' in result.stderr
        with engine.begin() as c:
            assert c.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == 'c185a1b2c3d4'
            assert c.execute(text('SELECT sentence FROM sunum_highlights')).scalar_one() == 'İş tamamlandı.'
            c.exec_driver_sql('DELETE FROM sunum_photos WHERE id=1')
            assert c.execute(text('SELECT photo_id FROM sunum_highlights')).scalar_one() is None
            # Only disposable fixture rows are cleared to exercise empty downgrade.
            c.exec_driver_sql('DELETE FROM sunum_highlights')
        migrate('downgrade', 'c184a1b2c3d4')
        with engine.connect() as c:
            assert c.execute(text('SELECT name FROM organizations')).scalar_one() == 'Sentetik Belediye'
        migrate('upgrade', 'head')


def test_model_registered_before_routes():
    result = subprocess.run([sys.executable,'-c',
        'from app import models; from app.db import Base; '
        'assert "sunum_highlights" in Base.metadata.tables'], cwd=ROOT,capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
