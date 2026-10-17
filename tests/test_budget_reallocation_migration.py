"""Single head; populated upgrade, immutable evidence, lossless downgrade/reupgrade."""
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.schema import CreateSchema, DropSchema

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('backend',['postgres','sqlite'])
def test_budget_migration_keeps_rows_and_history(tmp_path,backend):
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    scripts=ScriptDirectory.from_config(Config(str(ROOT/'alembic.ini')))
    assert scripts.get_heads()==['c031b1a2c3d4']
    assert scripts.get_revision('c031b1a2c3d4').down_revision=='b0262027a001'
    admin=None
    if backend=='postgres':
        admin=create_engine(os.environ['CIVENSA_TEST_POSTGRES_URL'])
        schema='civ031_migrate_'+uuid4().hex
        with admin.begin() as conn:conn.execute(CreateSchema(schema))
        url=make_url(os.environ['CIVENSA_TEST_POSTGRES_URL']).update_query_dict({'options':'-csearch_path='+schema}).render_as_string(hide_password=False)
    else:url=f'sqlite:///{tmp_path/"migration.db"}'
    engine=create_engine(url)
    def migrate(direction,revision):
        result=subprocess.run([sys.executable,'-m','alembic',direction,revision],cwd=ROOT,
            env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    try:
        migrate('upgrade','b0262027a001')
        with engine.begin() as c:
            c.execute(text("INSERT INTO organizations(id,name) VALUES (1,'Belediye')"))
            c.execute(text("INSERT INTO departments(id,organization_id,name) VALUES (1,1,'Strateji')"))
            c.execute(text("INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2027,'active','verified')"))
            c.execute(text("INSERT INTO users(id,email,full_name,role,password_hash,department_id) VALUES (1,'test@example.invalid','Test','strategy','unused',1)"))
            c.execute(text("INSERT INTO activities(id,period_id,department_id,code,position,name,explanation) VALUES (1,1,1,'A1',1,'Korunan faaliyet','Kaynak')"))
            c.execute(text("INSERT INTO activity_cost_values(id,activity_id,year,value_kind,funding_type,amount,raw_text,state) VALUES (1,1,2027,'budget','inside',123.45,'123,45','verified')"))
        migrate('upgrade','head')
        with engine.begin() as c:
            assert c.execute(text('SELECT contract_bound FROM activities WHERE id=1')).scalar() in (False,0)
            c.execute(text('UPDATE activities SET contract_bound=true WHERE id=1'))
            c.execute(text("INSERT INTO budget_operations(id,organization_id,period_id,actor_id,year,value_kind,phase,reference_type,reference_date,reference_number,reason,request_json,preview_json) VALUES(1,1,1,1,2027,'budget','before_adoption','mayor_instruction','2026-10-01','1','Gerekçe','{}','{}')"))
            c.execute(text("INSERT INTO budget_operation_lines(id,operation_id,department_id,value_table,value_id,label,funding_type,\"before\",\"after\",before_json,after_json) VALUES(1,1,1,'activity_cost_values',1,'Faaliyet','inside',123.45,120.45,'{}','{}')"))
        for statement in ["UPDATE budget_operations SET reason='değişiklik' WHERE id=1",'DELETE FROM budget_operations WHERE id=1', 'UPDATE budget_operation_lines SET "after"=0 WHERE id=1','DELETE FROM budget_operation_lines WHERE id=1']:
            with pytest.raises(DBAPIError),engine.begin() as c:c.execute(text(statement))
        migrate('downgrade','b0262027a001')
        migrate('upgrade','head')
        with engine.connect() as c:
            assert c.execute(text('SELECT COUNT(*) FROM budget_operations')).scalar()==1
            assert c.execute(text('SELECT COUNT(*) FROM budget_operation_lines')).scalar()==1
            assert c.execute(text('SELECT contract_bound FROM activities WHERE id=1')).scalar()
            assert str(c.execute(text('SELECT amount FROM activity_cost_values WHERE id=1')).scalar())=='123.45'
            assert c.execute(text('SELECT source_raw_text FROM activity_cost_values WHERE id=1')).scalar()==''
            if backend=='postgres':
                definitions=c.execute(text("SELECT pg_get_functiondef(p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname=current_schema() AND p.proname IN ('civensa_correction_decision_authorized', 'civensa_package_decision_authorized')")).scalars().all()
                assert definitions
                for definition in definitions:
                    assert "a.authority_kind='director_approval'" in definition
    finally:
        engine.dispose()
        if admin:
            with admin.begin() as c:c.execute(DropSchema(schema,cascade=True))
            admin.dispose()
