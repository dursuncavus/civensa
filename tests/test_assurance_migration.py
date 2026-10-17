"""Upgrade from CIV-038, preserve data on downgrade, protect frozen variables in SQL."""
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4
import pytest
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.schema import CreateSchema, DropSchema

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('backend', ['postgres', 'sqlite'])
def test_assurance_migration_guards_and_lossless_downgrade(tmp_path, backend):
    base = None
    if backend == 'postgres':
        url = os.getenv('CIVENSA_TEST_POSTGRES_URL')
        if not url: pytest.skip('Disposable PostgreSQL required')
        base = create_engine(url); schema = 'civ029_' + uuid4().hex
        with base.begin() as conn: conn.execute(CreateSchema(schema))
        url = make_url(url).update_query_dict({'options': '-csearch_path=' + schema}).render_as_string(hide_password=False)
    else:
        url = f'sqlite:///{tmp_path / "assurance.db"}'
    engine = create_engine(url)
    def migrate(action, revision, success=True):
        result = subprocess.run([sys.executable, '-m', 'alembic', action, revision], cwd=ROOT,
            env={**os.environ, 'DATABASE_URL': url}, capture_output=True, text=True)
        assert (result.returncode == 0) == success, result.stderr
        return result.stderr
    try:
        migrate('upgrade', 'c0382027a001')
        migrate('upgrade', 'c0292027a001'); migrate('upgrade', 'c0292027a001')
        assert 'ar_assurance_statements' in inspect(engine).get_table_names()
        migrate('downgrade', 'c0382027a001')
        assert 'ar_assurance_statements' not in inspect(engine).get_table_names()
        migrate('upgrade', 'c0292027a001')
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO organizations(id,name) VALUES (1,'Belediye')"))
            conn.execute(text("INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2027,'active','verified')"))
            conn.execute(text("INSERT INTO users(id,email,full_name,role,password_hash,is_active) VALUES (1,'test@invalid','Test','strategy','unused',true)"))
            conn.execute(text("INSERT INTO ar_documents(id,organization_id,period_id,scope,definition_version,revision,created_by) VALUES (1,1,1,'idare',1,0,1)"))
            conn.execute(text("INSERT INTO ar_assurance_statements(id,document_id,code,version_id,file_sha256,variables_json) VALUES (1,1,'EK-1','version','hash','{}')"))
        error = migrate('downgrade', 'c0382027a001', success=False)
        assert 'Veriyi koruyan' in error
        with engine.begin() as conn:
            assert conn.execute(text('SELECT variables_json FROM ar_assurance_statements')).scalar() == '{}'
            conn.execute(text("INSERT INTO ar_document_freezes(document_id,payload_json,sha256,created_by) VALUES (1,'{}','hash',1)"))
        for query in ["UPDATE ar_assurance_statements SET variables_json='changed' WHERE id=1",
                      'DELETE FROM ar_assurance_statements WHERE id=1',
                      "INSERT INTO ar_assurance_statements(document_id,code,version_id,file_sha256,variables_json) VALUES (1,'EK-3','v','h','{}')"]:
            with pytest.raises(DBAPIError, match='değiştirilemez'):
                with engine.begin() as conn: conn.execute(text(query))
        with engine.connect() as conn:
            assert conn.execute(text('SELECT version_num FROM alembic_version')).scalar() == 'c0292027a001'
            assert conn.execute(text('SELECT variables_json FROM ar_assurance_statements')).scalar() == '{}'
    finally:
        engine.dispose()
        if base:
            with base.begin() as conn: conn.execute(DropSchema(schema, cascade=True))
            base.dispose()
