"""D-190 PostgreSQL upgrade/backfill, ownership constraints and safe downgrade."""
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.schema import CreateSchema, DropSchema

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def migrated():
    base = create_engine(os.environ['CIVENSA_TEST_POSTGRES_URL'])
    schema = 'civ086_migration_' + uuid4().hex
    with base.begin() as conn:
        conn.execute(CreateSchema(schema))
    url = make_url(os.environ['CIVENSA_TEST_POSTGRES_URL']).update_query_dict({'options':'-csearch_path='+schema}).render_as_string(hide_password=False)
    engine = create_engine(url)
    def migrate(command, revision, ok=True):
        result = subprocess.run([sys.executable, '-m', 'alembic', command, revision], cwd=ROOT,
            env={**os.environ, 'DATABASE_URL':url}, capture_output=True, text=True)
        assert (result.returncode == 0) == ok, result.stderr
        return result
    try:
        migrate('upgrade', 'c084a1b2c3d4')
        with engine.begin() as conn:
            for statement in (
                "INSERT INTO organizations(id,name) VALUES (1,'Sentetik Belediye')",
                "INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2027,'active','verified')",
                "INSERT INTO departments(id,organization_id,name,is_active) VALUES (1,1,'Test Müdürlüğü',true)",
                "INSERT INTO users(id,email,full_name,role,password_hash,is_active,position,department_id) VALUES (1,'test@invalid','Test','strategy','unused',true,'director',1)",
                "INSERT INTO ar_documents(id,organization_id,period_id,scope,definition_version,revision,created_by) VALUES (1,1,1,'idare',1,0,1)",
                "INSERT INTO ar_documents(id,organization_id,period_id,department_id,scope,definition_version,revision,created_by) VALUES (2,1,1,1,'birim:1',1,0,1)",
                "INSERT INTO ar_section_contents(id,document_id,definition_id,blocks_json,status,reason,copied_needs_review) VALUES (1,1,4,'[{\"type\":\"table\",\"rows\":[[\"A\",\"5\"],[\"A\",\"5\"]]}]','draft','',false)",
                "INSERT INTO ar_resource_rows(document_id,table_kind,position,name,category,address,purpose,ownership,count) VALUES (2,'hardware',0,'','Bilgisayar','','','',5),(2,'hardware',1,'','Bilgisayar','','','',5)",
                "INSERT INTO ar_financial_entries(document_id,kind,position,payload_json) VALUES (2,'aid',0,'{\"amount\":12500.23}'),(2,'aid',1,'{\"amount\":12500.23}')",
                "INSERT INTO ar_financial_statements(document_id,name,period,statement_date,explanation,figures_json,filename,sha256) VALUES (2,'Bilanço','2027','','Kaynak','[{\"label\":\"Toplam\",\"amount\":12500.23}]','','')",
                "INSERT INTO ar_document_freezes(id,document_id,version,payload_json,sha256,created_by) VALUES (1,1,1,'{\"retained\":true}','retained-hash',1)",
            ):
                conn.exec_driver_sql(statement)
        yield engine, migrate
    finally:
        engine.dispose()
        with base.begin() as conn:
            conn.execute(DropSchema(schema, cascade=True))
        base.dispose()


def test_single_head_and_parent():
    script = ScriptDirectory.from_config(Config(str(ROOT / 'alembic.ini')))
    assert script.get_heads() == ['c160a1b2c3d4']
    assert script.get_revision('c085a1b2c3d4').down_revision == 'c086a1b2c3d4'
    assert script.get_revision('c086a1b2c3d4').down_revision == 'c084a1b2c3d4'


def test_upgrade_backfills_every_key_without_rewriting_frozen_bytes_and_downgrades(migrated):
    engine, migrate = migrated
    with engine.connect() as conn:
        original = conn.execute(text('SELECT payload_json,sha256 FROM ar_document_freezes')).one()
        original_blocks = conn.execute(text('SELECT blocks_json FROM ar_section_contents')).scalar_one()
    migrate('upgrade', 'head'); migrate('upgrade', 'head')
    expected = {'ar_section_table_keys':1,'ar_section_row_keys':2,'ar_resource_rows':2,
                'ar_financial_entries':2,'ar_statement_figure_keys':1}
    with engine.connect() as conn:
        for table, count in expected.items():
            keys = list(conn.execute(text(f'SELECT stable_key FROM {table}')).scalars())
            assert len(keys) == len(set(keys)) == count
            assert all(str(UUID(key)) == key for key in keys)
            assert next(c for c in inspect(engine).get_columns(table) if c['name'] == 'stable_key')['nullable'] is False
        assert conn.execute(text('SELECT payload_json,sha256 FROM ar_document_freezes')).one() == original
        assert conn.execute(text('SELECT blocks_json FROM ar_section_contents')).scalar_one() == original_blocks
        assert conn.execute(text('SELECT payload_json FROM ar_financial_entries LIMIT 1')).scalar_one() == '{"amount":12500.23}'
    # Old frozen parents protect their newly backfilled key records too.
    for statement in ('UPDATE ar_section_table_keys SET position=8', 'DELETE FROM ar_section_row_keys',
                      'TRUNCATE ar_section_row_keys'):
        with pytest.raises(DBAPIError, match='değiştirilemez'):
            with engine.begin() as conn:
                conn.exec_driver_sql(statement)
    for statement in ("UPDATE ar_resource_rows SET stable_key=NULL WHERE id=1",
                      "UPDATE ar_resource_rows SET stable_key=(SELECT stable_key FROM ar_resource_rows WHERE id=1) WHERE id=2",
                      "UPDATE ar_financial_entries SET stable_key=(SELECT stable_key FROM ar_financial_entries WHERE id=1) WHERE id=2"):
        with pytest.raises(DBAPIError):
            with engine.begin() as conn:
                conn.exec_driver_sql(statement)
    migrate('downgrade', 'c084a1b2c3d4')
    assert 'ar_section_table_keys' not in inspect(engine).get_table_names()
    assert 'stable_key' not in {c['name'] for c in inspect(engine).get_columns('ar_resource_rows')}
    with engine.connect() as conn:
        assert conn.execute(text('SELECT payload_json,sha256 FROM ar_document_freezes')).one() == original
        assert conn.execute(text('SELECT blocks_json FROM ar_section_contents')).scalar_one() == original_blocks
    migrate('upgrade', 'head')


@pytest.mark.parametrize('kind', ['idare', 'unit', 'submitted'])
def test_downgrade_refuses_frozen_keyed_snapshots_without_losing_data(migrated, kind):
    engine, migrate = migrated
    migrate('upgrade', 'head')
    payload = json.dumps({'_typeset':{'schema_version':'ar-source/1','complete':True}})
    with engine.begin() as conn:
        if kind == 'idare':
            conn.execute(text("INSERT INTO ar_document_freezes(id,document_id,version,payload_json,sha256,created_by) VALUES (2,1,2,:payload,:sha,1)"),
                         {'payload':payload,'sha':'a'*64})
        else:
            conn.execute(text("INSERT INTO ar_unit_workflow_events(document_id,revision,action,from_status,to_status,reason,actor_id,actor_name,created_at,content_event_cursor,payload_json,sha256) VALUES (2,1,:action,:before,:after,'',1,'Test',CURRENT_TIMESTAMP,0,:payload,:sha)"),
                         {'payload':payload,'sha':'a'*64,'action':'submit' if kind=='submitted' else 'approve',
                          'before':'draft' if kind=='submitted' else 'submitted','after':'submitted' if kind=='submitted' else 'approved'})
    result = migrate('downgrade', 'c084a1b2c3d4', ok=False)
    assert 'Dizgi anahtarı içeren sabit rapor kopyası var' in result.stderr
    assert 'Veriyi koruyan' in result.stderr
    assert 'ar_section_table_keys' in inspect(engine).get_table_names()
    with engine.connect() as conn:
        assert conn.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == 'c160a1b2c3d4'


def test_sqlite_upgrade_and_downgrade_retain_existing_checks(tmp_path):
    engine=create_engine(f"sqlite:///{tmp_path/'checks.db'}")
    env={**os.environ,'DATABASE_URL':str(engine.url)}
    def migrate(revision,command='upgrade'):
        result=subprocess.run([sys.executable,'-m','alembic',command,revision],cwd=ROOT,env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        assert 'is being omitted' not in result.stderr
    try:
        migrate('c084a1b2c3d4')
        before={table:{row['sqltext'] for row in inspect(engine).get_check_constraints(table)}
                for table in ('ar_resource_rows','ar_financial_entries')}
        for revision,command in [('head','upgrade'),('c084a1b2c3d4','downgrade')]:
            migrate(revision,command)
            for table,checks in before.items():
                assert {row['sqltext'] for row in inspect(engine).get_check_constraints(table)}==checks
    finally:
        engine.dispose()
