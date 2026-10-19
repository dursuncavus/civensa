"""Migration seeds exact EK-1 data and protects approved copies through raw SQL."""
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

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('backend',['postgres','sqlite'])
def test_ek1_migration_and_immutable_sql(tmp_path,backend):
    base=None
    if backend=='postgres':
        url=os.getenv('CIVENSA_TEST_POSTGRES_URL')
        if not url:pytest.skip('Disposable PostgreSQL test database not configured')
        base=create_engine(url)
        schema='civ037_migration_'+uuid4().hex
        with base.begin() as conn:conn.execute(CreateSchema(schema))
        url=make_url(url).update_query_dict({'options':'-csearch_path='+schema}).render_as_string(hide_password=False)
    else:url=f'sqlite:///{tmp_path/"sections.db"}'
    engine=create_engine(url)
    env={**os.environ,'DATABASE_URL':url}
    def migrate(command,revision,ok=True):
        result=subprocess.run([sys.executable,'-m','alembic',command,revision],cwd=ROOT,env=env,capture_output=True,text=True)
        assert (result.returncode==0)==ok,result.stderr
        return result
    try:
        migrate('upgrade','b0262027a001')
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO organizations(id,name) VALUES (1,'Deneme Belediyesi')"))
            conn.execute(text("INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2027,'active','verified')"))
            conn.execute(text("INSERT INTO departments(id,organization_id,name,is_active) VALUES (1,1,'Test Müdürlüğü',true)"))
            conn.execute(text("INSERT INTO users(id,email,full_name,role,password_hash,is_active) VALUES (1,'test@invalid','Test','strategy','unused',true)"))
        before=set(inspect(engine).get_table_names())
        migrate('upgrade','head');migrate('upgrade','head')
        with engine.connect() as conn:
            from test_activity_sections import EXPECTED_TREE
            tree=conn.execute(text('SELECT code,title FROM ar_section_definitions ORDER BY position')).all()
            assert tree==EXPECTED_TREE
            assert conn.execute(text('SELECT name FROM organizations')).scalar()=='Deneme Belediyesi'
        assert before<=set(inspect(engine).get_table_names())
        # Empty-data downgrade succeeds and re-upgrade seeds once.
        migrate('downgrade','b0262027a001');migrate('upgrade','head')
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO ar_documents(id,organization_id,period_id,department_id,scope,definition_version,revision,created_by) VALUES (1,1,1,1,'birim:1',1,0,1)"))
            conn.execute(text("INSERT INTO ar_section_contents(id,document_id,definition_id,blocks_json,status,reason,copied_needs_review) VALUES (1,1,4,'[]','draft','',false)"))
            conn.execute(text("INSERT INTO ar_resource_rows(id,document_id,table_kind,position,name,category,address,purpose,ownership,count,area) VALUES (1,1,'hardware',0,'','Bilgisayar','','','',0,NULL)"))
            conn.execute(text("INSERT INTO ar_content_events(id,document_id,section_code,action,before_json,after_json,actor_id) VALUES (1,1,'I.A','save','{}','{}',1)"))
            conn.execute(text("INSERT INTO ar_document_freezes(id,document_id,payload_json,sha256,created_by) VALUES (1,1,'{}','hash',1)"))
        statements=[
            "UPDATE ar_document_freezes SET payload_json='changed' WHERE id=1",
            'DELETE FROM ar_document_freezes WHERE id=1',
            "UPDATE ar_content_events SET after_json='changed' WHERE id=1",
            'DELETE FROM ar_content_events WHERE id=1',
            "UPDATE ar_section_contents SET blocks_json='changed' WHERE id=1",
            'DELETE FROM ar_section_contents WHERE id=1',
            'UPDATE ar_resource_rows SET count=10 WHERE id=1',
            'DELETE FROM ar_resource_rows WHERE id=1',
            'UPDATE ar_documents SET revision=10 WHERE id=1',
            "INSERT INTO ar_section_contents(id,document_id,definition_id,blocks_json,status,reason,copied_needs_review) VALUES (2,1,5,'[]','draft','',false)",
            "INSERT INTO ar_resource_rows(id,document_id,table_kind,position,name,category,address,purpose,ownership,count,area) VALUES (2,1,'hardware',1,'','Telefon','','','',1,NULL)",
        ]
        for statement in statements:
            with pytest.raises(DBAPIError,match='değiştirilemez'):
                with engine.begin() as conn:conn.execute(text(statement))
        result=migrate('downgrade','b0262027a001',ok=False)
        assert 'Veriyi koruyan' in result.stderr
        with engine.connect() as conn:
            assert conn.execute(text('SELECT payload_json FROM ar_document_freezes')).scalar()=='{}'
            assert conn.execute(text('SELECT count FROM ar_resource_rows')).scalar()==0
    finally:
        engine.dispose()
        if base:
            with base.begin() as conn:conn.execute(DropSchema(schema,cascade=True))
            base.dispose()
