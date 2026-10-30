"""CIV-078 upgrade/backfill, append-only SQL guards and safe downgrade."""
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.schema import CreateSchema, DropSchema

pytestmark=pytest.mark.postgres
ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def migrated():
    base=create_engine(os.environ['CIVENSA_TEST_POSTGRES_URL'])
    schema='civ078_migration_'+uuid4().hex
    with base.begin() as conn:conn.execute(CreateSchema(schema))
    url=make_url(os.environ['CIVENSA_TEST_POSTGRES_URL']).update_query_dict({'options':'-csearch_path='+schema}).render_as_string(hide_password=False)
    engine=create_engine(url)
    env={**os.environ,'DATABASE_URL':url}
    def migrate(command,revision,ok=True):
        result=subprocess.run([sys.executable,'-m','alembic',command,revision],cwd=ROOT,env=env,capture_output=True,text=True)
        assert (result.returncode==0)==ok,result.stderr
        return result
    try:
        migrate('upgrade','c079a1b2c3d4')
        with engine.begin() as conn:
            for statement in (
                "INSERT INTO organizations(id,name) VALUES (1,'Deneme Belediyesi')",
                "INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2027,'active','verified')",
                "INSERT INTO departments(id,organization_id,name,is_active) VALUES (1,1,'Test Müdürlüğü',true)",
                "INSERT INTO users(id,email,full_name,role,password_hash,is_active,position,department_id) VALUES (1,'test@invalid','Test','strategy','unused',true,'director',1)",
                "INSERT INTO ar_documents(id,organization_id,period_id,scope,definition_version,revision,created_by) VALUES (1,1,1,'idare',1,0,1)",
                "INSERT INTO ar_documents(id,organization_id,period_id,department_id,scope,definition_version,revision,created_by) VALUES (2,1,1,1,'birim:1',1,0,1)",
                "INSERT INTO ar_section_contents(id,document_id,definition_id,blocks_json,status,reason,copied_needs_review) VALUES (1,1,4,'[]','draft','',false)",
                "INSERT INTO ar_document_freezes(id,document_id,payload_json,sha256,created_by) VALUES (1,1,'{\"retained\":true}','retained-hash',1),(2,2,'{}','unit-hash',1)",
            ):conn.exec_driver_sql(statement)
        yield engine,migrate
    finally:
        engine.dispose()
        with base.begin() as conn:conn.execute(DropSchema(schema,cascade=True))
        base.dispose()


def reopen_sql(conn):
    conn.execute(text("INSERT INTO ar_content_events(document_id,section_code,action,before_json,after_json,actor_id) VALUES (1,'','reopen','{}',:after,1)"),
        {'after':json.dumps({'freeze_id':1,'version':1,'reason':'Düzeltme gerekçesi','actor_name':'Test'})})


def test_backfill_and_safe_single_release_downgrade(migrated):
    engine,migrate=migrated
    migrate('upgrade','head');migrate('upgrade','head')
    with engine.connect() as conn:
        assert conn.execute(text('SELECT version FROM ar_document_freezes ORDER BY id')).scalars().all()==[1,1]
        assert conn.execute(text('SELECT payload_json,sha256 FROM ar_document_freezes WHERE id=1')).one()==('{"retained":true}','retained-hash')
    migrate('downgrade','c079a1b2c3d4')
    assert 'version' not in {c['name'] for c in inspect(engine).get_columns('ar_document_freezes')}
    with pytest.raises(DBAPIError,match='değiştirilemez'):
        with engine.begin() as conn:conn.execute(text('UPDATE ar_documents SET revision=revision+1 WHERE id=1'))
    migrate('upgrade','head')


@pytest.mark.parametrize('second_release',[False,True])
def test_reopen_preserves_immutable_history_and_blocks_unsafe_downgrade(migrated,second_release):
    engine,migrate=migrated
    migrate('upgrade','head')
    with pytest.raises(DBAPIError,match='değiştirilemez'):
        with engine.begin() as conn:conn.execute(text("UPDATE ar_section_contents SET blocks_json='changed' WHERE id=1"))
    with engine.begin() as conn:
        reopen_sql(conn)
        conn.execute(text("UPDATE ar_section_contents SET blocks_json='corrected' WHERE id=1"))
        conn.execute(text('UPDATE ar_documents SET revision=1 WHERE id=1'))
        if second_release:
            conn.exec_driver_sql("INSERT INTO ar_document_freezes(id,document_id,version,payload_json,sha256,created_by) VALUES (3,1,2,'{\"new\":true}','new-hash',1)")
    statements=[
        "UPDATE ar_document_freezes SET payload_json='changed' WHERE id=1",
        'DELETE FROM ar_document_freezes WHERE id=1',
        "UPDATE ar_content_events SET after_json='{}' WHERE action='reopen'",
        "DELETE FROM ar_content_events WHERE action='reopen'",
        'TRUNCATE ar_content_events',
        'TRUNCATE ar_document_freezes CASCADE',
        # A historical unit freeze is never opened by an idare reopen event.
        'UPDATE ar_documents SET revision=revision+1 WHERE id=2',
    ]
    if second_release:statements.append("UPDATE ar_section_contents SET blocks_json='changed-again' WHERE id=1")
    for statement in statements:
        with pytest.raises(DBAPIError,match='değiştirilemez'):
            with engine.begin() as conn:conn.execute(text(statement))
    with pytest.raises(DBAPIError):
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO ar_document_freezes(document_id,version,payload_json,sha256,created_by) VALUES (1,1,'{}','hash',1)"))
    result=migrate('downgrade','c079a1b2c3d4',ok=False)
    assert 'Veriyi koruyan' in result.stderr
    with engine.connect() as conn:
        assert conn.execute(text('SELECT payload_json,sha256 FROM ar_document_freezes WHERE id=1')).one()==('{"retained":true}','retained-hash')
        assert conn.execute(text("SELECT count(*) FROM ar_content_events WHERE action='reopen'")).scalar()==1
