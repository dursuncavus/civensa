"""Real additive upgrade, deferred pair integrity and non-destructive downgrade."""
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[1]


def test_photo_model_registered_without_importing_routes():
    result = subprocess.run([sys.executable, '-c',
        'from app import models; from app.db import Base; '
        'assert Base.metadata.tables["sunum_photos"] is models.SunumPhoto.__table__'],
        cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_migration_pairs_and_data_preserving_downgrade(postgres_templates):
    with postgres_templates.clone('c162a1b2c3d4') as engine:
        def migrate(action, revision, ok=True):
            result = subprocess.run([sys.executable, '-m', 'alembic', action, revision], cwd=ROOT,
                env={**os.environ, 'DATABASE_URL': engine.url.render_as_string(hide_password=False)},
                capture_output=True, text=True)
            assert (result.returncode == 0) == ok, result.stderr
            return result

        migrate('upgrade', 'c184a1b2c3d4')
        migrate('upgrade', 'c184a1b2c3d4')
        with engine.begin() as conn:
            conn.exec_driver_sql("INSERT INTO organizations(id,name) VALUES (1,'Sentetik Belediye')")
            conn.exec_driver_sql("INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2027,'active','verified')")
            conn.exec_driver_sql("INSERT INTO departments(id,organization_id,name,is_active) VALUES (1,1,'Fen İşleri',true),(2,1,'Park ve Bahçeler',true)")
            conn.exec_driver_sql("INSERT INTO users(id,email,full_name,role,password_hash,is_active,position,department_id) VALUES (1,'test@invalid','Test','strategy','unused',true,'staff',1)")

        def insert(conn, key, kind, number, department=1, year=2027):
            conn.execute(text('''INSERT INTO sunum_photos(organization_id,period_id,year,department_id,
              caption,kind,pair_key,webp_data,thumb_data,width,height,sha256,byte_size,
              consent_confirmed,selected,sort_order,created_by,created_at)
              VALUES (1,1,:year,:dep,'Tamamlanan iş',:kind,:key,:data,:data,10,10,:sha,4,true,false,0,1,now())'''),
              dict(year=year, dep=department, kind=kind, key=key, data=b'test', sha=str(number).zfill(64)))

        # A standalone before is rejected at commit, not during the first insert.
        with pytest.raises(DBAPIError, match='aynı müdürlük ve yıldan'):
            with engine.begin() as conn:
                insert(conn, 'incomplete', 'before', 1)
        with engine.begin() as conn:
            insert(conn, 'valid-pair', 'before', 1)
            insert(conn, 'valid-pair', 'after', 2)
        for department, year in [(2,2027), (1,2028)]:
            with pytest.raises(DBAPIError, match='aynı müdürlük ve yıldan'):
                with engine.begin() as conn:
                    insert(conn, 'different-scope', 'before', 3)
                    insert(conn, 'different-scope', 'after', 4, department, year)
        with pytest.raises(DBAPIError):
            with engine.begin() as conn:
                insert(conn, 'valid-pair', 'before', 3)
        with pytest.raises(DBAPIError):
            with engine.begin() as conn:
                insert(conn, None, 'single', 1)
        result = migrate('downgrade', 'c162a1b2c3d4', ok=False)
        assert 'veriyi koruyan aktarım' in result.stderr
        with engine.connect() as conn:
            assert conn.execute(text('SELECT count(*) FROM sunum_photos')).scalar_one() == 2
            assert conn.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == 'c184a1b2c3d4'
        with pytest.raises(DBAPIError, match='aynı müdürlük ve yıldan'):
            with engine.begin() as conn:
                conn.exec_driver_sql("DELETE FROM sunum_photos WHERE kind='before'")
        # Deleting a pair together is the explicit photo UI's supported action.
        with engine.begin() as conn:
            conn.exec_driver_sql('DELETE FROM sunum_photos')
        migrate('downgrade', 'c162a1b2c3d4')
        assert 'sunum_photos' not in inspect(engine).get_table_names()
        with engine.connect() as conn:
            assert conn.execute(text('SELECT name FROM organizations')).scalar_one() == 'Sentetik Belediye'
        migrate('upgrade', 'c184a1b2c3d4')
