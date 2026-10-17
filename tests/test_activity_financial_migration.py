"""Real migration cycle, data-preserving downgrade and SQL freeze protections."""
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.schema import CreateSchema, DropSchema

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('backend',['postgres','sqlite'])
def test_financial_migration_guards_and_preservation(tmp_path,backend):
    base=None
    if backend=='postgres':
        url=os.getenv('CIVENSA_TEST_POSTGRES_URL')
        if not url:pytest.skip('Disposable PostgreSQL test database not configured')
        base=create_engine(url);schema='civ038_migration_'+uuid4().hex
        with base.begin() as conn:conn.execute(CreateSchema(schema))
        url=make_url(url).update_query_dict({'options':'-csearch_path='+schema}).render_as_string(hide_password=False)
    else:url=f'sqlite:///{tmp_path/"financial.db"}'
    engine=create_engine(url);env={**os.environ,'DATABASE_URL':url}
    def migrate(command,revision,ok=True):
        result=subprocess.run([sys.executable,'-m','alembic',command,revision],cwd=ROOT,env=env,capture_output=True,text=True)
        assert (result.returncode==0)==ok,result.stderr
        return result
    try:
        migrate('upgrade','head');migrate('downgrade','c0372027a001');migrate('upgrade','head')
        migrate('downgrade','c0372027a001')
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO organizations(id,name) VALUES (1,'Test Belediyesi')"))
            conn.execute(text("INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2027,'active','verified')"))
            conn.execute(text("INSERT INTO departments(id,organization_id,name,is_active) VALUES (1,1,'Test Müdürlüğü',true)"))
            conn.execute(text("INSERT INTO users(id,email,full_name,role,password_hash,is_active) VALUES (1,'test@invalid','Strateji','strategy','unused',true)"))
            conn.execute(text("INSERT INTO ar_documents(id,organization_id,period_id,scope,definition_version,revision,created_by) VALUES (1,1,1,'idare',1,0,1)"))
            conn.execute(text("INSERT INTO ar_documents(id,organization_id,period_id,department_id,scope,definition_version,revision,created_by) VALUES (2,1,1,1,'birim:1',1,0,1)"))
        before=set(inspect(engine).get_indexes('report_candidates')[i]['name'] for i in range(len(inspect(engine).get_indexes('report_candidates'))))
        migrate('upgrade','head');migrate('upgrade','head')
        after={i['name'] for i in inspect(engine).get_indexes('report_candidates')}
        assert before==after
        with engine.connect() as conn:
            assert conn.execute(text('SELECT name FROM ar_financial_statements ORDER BY id')).scalars().all()==['Bilanço','Faaliyet Sonuçları Tablosu']
            assert conn.execute(text('SELECT version_num FROM alembic_version')).scalar()=='c0382027a001'
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO ar_financial_imports(id,document_id,kind,revision,source_sha256,preview_json,actor_id) VALUES (1,1,'expenditure',0,'hash','{}',1)"))
            conn.execute(text("INSERT INTO ar_budget_rows(id,document_id,kind,row_key,department_id,economic_code,initial,explanation,import_id) VALUES (1,1,'expenditure','1:01:0:0',1,'01',12500.23,'',1)"))
            conn.execute(text("INSERT INTO ar_financial_policies(id,document_id,lower_rate,upper_rate) VALUES (1,1,NULL,NULL)"))
            conn.execute(text("INSERT INTO ar_financial_entries(id,document_id,kind,position,payload_json) VALUES (1,1,'assets',0,'{}')"))
        for sql in ("UPDATE ar_financial_imports SET preview_json='changed' WHERE id=1",'DELETE FROM ar_financial_imports WHERE id=1'):
            with pytest.raises(DBAPIError,match='değiştirilemez'):
                with engine.begin() as conn:conn.execute(text(sql))
        with pytest.raises(DBAPIError):
            with engine.begin() as conn:conn.execute(text('UPDATE ar_budget_rows SET initial=-1 WHERE id=1'))
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO ar_document_freezes(id,document_id,payload_json,sha256,created_by) VALUES (1,1,'{}','hash',1)"))
        for table in ('ar_budget_rows','ar_financial_entries','ar_financial_policies','ar_financial_statements','ar_financial_imports'):
            sqls=[f'DELETE FROM {table} WHERE id=1',f'UPDATE {table} SET document_id=2 WHERE id=1']
            for sql in sqls:
                with pytest.raises(DBAPIError,match='değiştirilemez'):
                    with engine.begin() as conn:conn.execute(text(sql))
        inserts=[
            "INSERT INTO ar_financial_entries(document_id,kind,position,payload_json) VALUES (1,'aid',1,'{}')",
            "INSERT INTO ar_financial_policies(document_id,lower_rate,upper_rate) VALUES (1,80,110)",
            "INSERT INTO ar_financial_statements(document_id,name,period,statement_date,explanation,figures_json,filename,sha256) VALUES (1,'Yeni','','','','[]','','')",
            "INSERT INTO ar_financial_imports(document_id,kind,revision,source_sha256,preview_json,actor_id) VALUES (1,'revenue',0,'hash','{}',1)",
            "INSERT INTO ar_budget_rows(document_id,kind,row_key,department_id,economic_code,explanation) VALUES (1,'expenditure','1:02:0:0',1,'02','')"]
        for sql in inserts:
            with pytest.raises(DBAPIError,match='değiştirilemez'):
                with engine.begin() as conn:conn.execute(text(sql))
        result=migrate('downgrade','c0372027a001',ok=False)
        assert 'Veriyi koruyan' in result.stderr
        with engine.connect() as conn:
            assert Decimal(str(conn.execute(text('SELECT initial FROM ar_budget_rows')).scalar()))==Decimal('12500.23')
            assert conn.execute(text('SELECT count(*) FROM ar_financial_imports')).scalar()==1
    finally:
        engine.dispose()
        if base:
            with base.begin() as conn:conn.execute(DropSchema(schema,cascade=True))
            base.dispose()
