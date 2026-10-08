"""New migration is additive and history is protected even through raw SQL."""
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


@pytest.mark.parametrize('backend', ['sqlite', 'postgres'])
def test_contract_migration_preserves_rows_and_blocks_sql_overwrites(tmp_path, backend):
    base_engine = None
    if backend == 'postgres':
        url = os.getenv('CIVENSA_TEST_POSTGRES_URL')
        if not url:
            pytest.skip('Disposable PostgreSQL test database not configured')
        base_engine = create_engine(url)
        schema = 'contract_migration_' + uuid4().hex
        with base_engine.begin() as conn:
            conn.execute(CreateSchema(schema))
        url = make_url(url).update_query_dict({'options': '-csearch_path=' + schema}).render_as_string(hide_password=False)
    else:
        url = f'sqlite:///{tmp_path / "contract-upgrade.db"}'
    engine = create_engine(url)
    env = {**os.environ, 'DATABASE_URL': url}
    def migrate(revision):
        result = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', revision], cwd=ROOT, env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    try:
        migrate('e5a0b1c2d3e4')
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO organizations(id,name) VALUES (1,'Test')"))
            conn.execute(text("INSERT INTO reporting_periods(id,year,status,template_status) VALUES (1,2027,'active','verified')"))
            conn.execute(text("INSERT INTO departments(id,organization_id,name) VALUES (1,1,'Müdürlük')"))
            conn.execute(text("INSERT INTO users(id,email,full_name,role,password_hash,department_id,is_active) VALUES (1,'x@test.invalid','Test','strategy','unused',NULL,true)"))
            conn.execute(text("INSERT INTO programs(id,period_id,name) VALUES (1,1,'Program')"))
            conn.execute(text("INSERT INTO subprograms(id,period_id,program_id,name,rationale,goal) VALUES (1,1,1,'Alt','','')"))
            conn.execute(text("INSERT INTO indicators(id,period_id,department_id,subprogram_id,name,unit,explanation,calculation_method,data_source,status) VALUES (1,1,1,1,'Kaynak gösterge','Adet','','','','draft')"))
            conn.execute(text("INSERT INTO indicator_values(id,indicator_id,year,value_kind,value,raw_text,state) VALUES (1,1,2027,'target',1.75,'1,75','verified')"))
            conn.execute(text("INSERT INTO publications(id,period_id,version,snapshot_json,sha256,template_version,created_by,created_at) VALUES (1,1,1,'{}','oldhash','5.0',1,CURRENT_TIMESTAMP)"))
        before_indexes = {t: {i['name'] for i in inspect(engine).get_indexes(t)} for t in ('notifications', 'submission_events', 'indicators')}
        migrate('f6b1c2d3e4f5')
        with engine.connect() as conn:
            row = conn.execute(text('SELECT * FROM indicators')).mappings().one()
            assert row['id'] == 1 and row['name'] == 'Kaynak gösterge' and row['persistent_indicator_id'] is None
            value = conn.execute(text('SELECT * FROM indicator_values')).mappings().one()
            assert str(value['value']).startswith('1.75') and value['raw_text'] == '1,75'
            assert conn.execute(text('SELECT snapshot_json FROM publications')).scalar() == '{}'
            assert conn.execute(text('SELECT count(*) FROM indicator_identities')).scalar() == 0
        for table, names in before_indexes.items():
            assert names <= {i['name'] for i in inspect(engine).get_indexes(table)}
        for statement in ("UPDATE publications SET snapshot_json='changed' WHERE id=1", 'DELETE FROM publications WHERE id=1'):
            with pytest.raises(DBAPIError, match='değiştirilemez'):
                with engine.begin() as conn:
                    conn.execute(text(statement))
        assert 'actual_revisions' in inspect(engine).get_table_names()
        assert 'activity_report_revisions' in inspect(engine).get_table_names()
        # Model-based fixtures cannot prove SQL triggers; exercise migrated tables.
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO indicator_identities(indicator_id,organization_id) VALUES ('test-identity',1)"))
            conn.execute(text("INSERT INTO indicator_definition_revisions(id,indicator_id,revision,period_id,definition_json,sha256,created_by,created_at) VALUES (1,'test-identity',1,1,'{}','hash',1,CURRENT_TIMESTAMP)"))
            conn.execute(text("INSERT INTO publication_indicator_bindings(id,publication_id,snapshot_indicator_id,definition_revision_id,department_id,created_by,reason,created_at) VALUES (1,1,1,1,1,1,'Explicit test',CURRENT_TIMESTAMP)"))
            conn.execute(text("INSERT INTO activity_reports(id,organization_id,period_id,current_revision,lock_version) VALUES (1,1,1,1,0)"))
            conn.execute(text("INSERT INTO activity_report_revisions(id,report_id,revision,publication_id,publication_sha256,contract_version,previous_revision_id,diff_json,created_by,created_at) VALUES (1,1,1,1,'oldhash','1.0',NULL,'[]',1,CURRENT_TIMESTAMP)"))
            conn.execute(text("INSERT INTO report_indicators(id,report_revision_id,publication_binding_id) VALUES (1,1,1)"))
            conn.execute(text("INSERT INTO activity_report_approvals(id,report_revision_id,created_by,created_at) VALUES (1,1,1,CURRENT_TIMESTAMP)"))
        # Apply the reason migration to populated immutable history, not empty tables.
        with engine.connect() as conn:
            previous_revision = dict(conn.execute(text('SELECT * FROM activity_report_revisions WHERE id=1')).mappings().one())
        migrate('head'); migrate('head')
        with engine.connect() as conn:
            migrated_revision = dict(conn.execute(text('SELECT * FROM activity_report_revisions WHERE id=1')).mappings().one())
            assert migrated_revision.pop('revision_reason') == ''
            assert migrated_revision == previous_revision
        with pytest.raises(DBAPIError, match='düzeltme gerekçesi'):
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO activity_report_revisions(id,report_id,revision,publication_id,publication_sha256,contract_version,previous_revision_id,diff_json,created_by,created_at) VALUES (2,1,2,1,'oldhash','1.0',1,'[]',1,CURRENT_TIMESTAMP)"))
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO activity_report_revisions(id,report_id,revision,publication_id,publication_sha256,contract_version,previous_revision_id,diff_json,created_by,created_at,revision_reason) VALUES (2,1,2,1,'oldhash','1.0',1,'[]',1,CURRENT_TIMESTAMP,'Kaynak düzeltmesi')"))
        with pytest.raises(DBAPIError, match='değiştirilemez'):
            with engine.begin() as conn:
                conn.execute(text("UPDATE activity_report_revisions SET revision_reason='Üzerine yaz' WHERE id=2"))
        with pytest.raises(DBAPIError, match='değiştirilemez'):
            with engine.begin() as conn:
                conn.execute(text("UPDATE indicator_definition_revisions SET definition_json='overwrite' WHERE id=1"))
        with pytest.raises(DBAPIError, match='kayıt eklenemez'):
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO actual_revisions(report_indicator_id,revision,supersedes_id,value,raw_text,state,evidence_json,explanation,deviation_json,created_by,created_at) VALUES (1,1,NULL,1,'1','verified','[]','','{}',1,CURRENT_TIMESTAMP)"))
    finally:
        engine.dispose()
        if base_engine:
            with base_engine.begin() as conn:
                conn.execute(DropSchema(schema, cascade=True, if_exists=True))
            base_engine.dispose()
