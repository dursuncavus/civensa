import os
from uuid import uuid4
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, select, inspect, text, MetaData, Table, literal
from sqlalchemy.schema import CreateSchema, DropSchema
from sqlalchemy.orm import Session, with_expression
from sqlalchemy.pool import StaticPool
from app.db import Base
from app.models import *

def pytest_addoption(parser):
    parser.addoption('--require-postgres', action='store_true',
                     help='Fail if the disposable PostgreSQL test URL is missing.')


def pytest_configure(config):
    config.addinivalue_line('markers', 'postgres: requires a disposable PostgreSQL database')
    if config.getoption('--require-postgres') and not os.getenv('CIVENSA_TEST_POSTGRES_URL'):
        raise pytest.UsageError('--require-postgres needs CIVENSA_TEST_POSTGRES_URL')


@pytest.fixture(autouse=True)
def isolated_application_startup(tmp_path, monkeypatch):
    # TestClient lifespan must never migrate the developer's local database.
    from app import main
    url = f"sqlite:///{tmp_path / 'application-startup.db'}"
    runtime_engine = create_engine(url)
    monkeypatch.setenv('DATABASE_URL', url)
    monkeypatch.delenv('MIGRATION_DATABASE_URL', raising=False)
    monkeypatch.setenv('DEMO_SEED', '0')
    monkeypatch.setattr(main, 'engine', runtime_engine)
    yield
    runtime_engine.dispose()


@pytest.fixture
def db(request):
    if request.node.get_closest_marker('postgres'):
        url = os.getenv('CIVENSA_TEST_POSTGRES_URL')
        if not url:
            pytest.skip('Disposable PostgreSQL test database not configured')
        # Each scenario gets its own schema; migration tests retain the public schema.
        base_engine = create_engine(url, future=True)
        if base_engine.dialect.name != 'postgresql':
            base_engine.dispose()
            pytest.fail('CIVENSA_TEST_POSTGRES_URL must use PostgreSQL')
        schema = 'civensa_test_' + uuid4().hex
        try:
            with base_engine.begin() as connection:
                connection.execute(CreateSchema(schema))
            engine = base_engine.execution_options(schema_translate_map={None: schema})
            Base.metadata.create_all(engine)
            with Session(engine, expire_on_commit=False) as session:
                yield session
        finally:
            with base_engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True, if_exists=True))
            base_engine.dispose()
        return
    engine=create_engine('sqlite://',poolclass=StaticPool,connect_args={'check_same_thread':False})
    @event.listens_for(engine,'connect')
    def fk(connection,record):connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    with Session(engine,expire_on_commit=False) as session:
        yield session
    engine.dispose()

@pytest.fixture
def sample(db):
    # Historical migration checkpoints predate the current Department model.
    # Adapt only model-based fixtures; raw migration tests seed the exact old
    # schema separately and verify CIV-018's real column addition.
    if not db.bind.get_execution_options().get('schema_translate_map') and 'is_active' not in {
        c['name'] for c in inspect(db.bind).get_columns('departments')
    }:
        db.execute(text('ALTER TABLE departments ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE'))
        db.commit()
    # Historical workflow-migration tests seed with today's ORM while deliberately
    # retaining old workflow guards. Supply only the new User fields in those
    # fixtures; CIV-025's own migration tests use raw pre-migration rows instead.
    schema = db.get_bind().get_execution_options().get('schema_translate_map', {}).get(None)
    # Historical workflow probes use today's Activity ORM before CIV-031. Supply
    # the default flag only for that seed; the dedicated raw migration test proves
    # CIV-031 adds it to a populated base without changing values.
    activity_columns = {column['name'] for column in inspect(db.get_bind()).get_columns('activities', schema=schema)}
    if 'contract_bound' not in activity_columns:
        db.execute(text('ALTER TABLE activities ADD COLUMN contract_bound BOOLEAN NOT NULL DEFAULT false'))
    user_columns = {column['name'] for column in inspect(db.get_bind()).get_columns('users', schema=schema)}
    if 'position' not in user_columns:
        db.execute(text("ALTER TABLE users ADD COLUMN position VARCHAR(20) NOT NULL DEFAULT 'staff' "
                        "CONSTRAINT ck_user_position CHECK (position IN ('staff', 'director')) "
                        "CONSTRAINT ck_director_department CHECK (position != 'director' OR department_id IS NOT NULL)"))
    if 'must_change_password' not in user_columns:
        # Only model-based historical workflow seeds use this adapter. The
        # CIV-044 migration test inserts raw c031 rows to exercise the real upgrade.
        db.execute(text('ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT false'))
    if 'can_submit' not in user_columns:
        db.execute(text("ALTER TABLE users ADD COLUMN can_submit BOOLEAN NOT NULL DEFAULT false"))
    # Historical checkpoints also predate CIV-027. Model-based fixtures need
    # today's nullable profile fields and empty journal tables so existing
    # workflow snapshot tests can still use the current ORM. The CIV-027
    # migration regression seeds raw c029 rows without this adapter.
    schema = db.get_bind().get_execution_options().get('schema_translate_map', {}).get(None)
    scope_columns = {c['name'] for c in inspect(db.connection()).get_columns('department_scopes', schema=schema)}
    for column, kind in [('budget_code', 'TEXT'), ('active_from', 'DATE'), ('active_to', 'DATE')]:
        if column not in scope_columns:
            db.execute(text(f'ALTER TABLE department_scopes ADD COLUMN {column} {kind}'))
    for model in (StructureChange, StructureChangeLink, StructureChangeTransfer, StructureChangeCancellation):
        model.__table__.create(db.connection(), checkfirst=True)
    db.commit()
    org=Organization(name='Test Belediyesi');p=ReportingPeriod(year=2027,status='active');db.add_all([org,p]);db.flush()
    d=Department(organization_id=org.id,name='Test Müdürlüğü');db.add(d);db.flush()
    u=User(email='test@example.invalid',full_name='Test',role='department',password_hash='unused',department_id=d.id,can_submit=True)
    strategy=User(email='strategy@example.invalid',full_name='Strateji',role='strategy',password_hash='unused',position='director',department_id=d.id)
    program=Program(period_id=p.id,name='Test Programı');db.add_all([u,strategy,program]);db.flush()
    sp=SubProgram(period_id=p.id,program_id=program.id,name='Test Alt Programı');db.add(sp);db.flush()
    card=ReportCard(period_id=p.id,department_id=d.id,subprogram_id=sp.id,source_title='2027/1',goal='Birinci hedef',rationale='Kaynak gerekçesi',responsible='Test Belediyesi',explanation='Ortak açıklama',calculation_method='Kaynak yöntemi',data_source='Kaynak kayıt')
    db.add(card);db.flush()
    i=Indicator(period_id=p.id,department_id=d.id,subprogram_id=sp.id,card_id=card.id,name='Hizmet sayısı',unit='Adet')
    a=Activity(period_id=p.id,department_id=d.id,subprogram_id=sp.id,card_id=card.id,name='Ortak faaliyet',explanation='Kaynak faaliyet açıklaması')
    db.add_all([i,a]);db.flush()
    db.add(IndicatorValue(indicator_id=i.id,year=2027,value_kind='target',value='1.75'))
    official=OfficialActivity(period_id=p.id,program_code='1',program_name='Test Programı',subprogram_code='1.1',subprogram_name='Test Alt Programı',code='1.1.1',name='Resmî faaliyet');db.add(official);db.flush()
    db.add_all([ActivityResponsibility(official_activity_id=official.id,department_id=d.id),ActivityCatalogueLink(activity_id=a.id,official_activity_id=official.id)])
    # The same seed is used before historical Alembic upgrades. Reflect the active
    # schema so current ORM defaults cannot insert columns absent at that revision.
    schema = db.get_bind().get_execution_options().get('schema_translate_map', {}).get(None)
    economic_table = Table('economic_values', MetaData(), schema=schema, autoload_with=db.connection())
    economic_defaults = dict(raw_text='', state='verified', issue='', source_context_json='{}',
                             source_card_id=None, source_table_number=None)
    if set(economic_defaults) - set(economic_table.c.keys()):
        @event.listens_for(db, 'do_orm_execute')
        def historical_economic_reads(query):
            # Historical workflow setup also snapshots these rows with today's
            # ORM. Supply only absent provenance fields, using the upgrade's
            # defaults. Reinspect so post-upgrade reads use real migrated data.
            if not query.is_select or not any(d.get('expr') is EconomicValue
                    for d in query.statement.column_descriptions):
                return
            columns = {c['name'] for c in inspect(db.connection()).get_columns('economic_values', schema=schema)}
            query.statement = query.statement.options(*(with_expression(getattr(EconomicValue, name),
                literal(value, type_=EconomicValue.__table__.c[name].type))
                for name, value in economic_defaults.items() if name not in columns))
    def economic(year, kind, category, fund, amount):
        row = dict(period_id=p.id, department_id=d.id, year=year, value_kind=kind,
                   category=category, program_group='service', funding_type=fund, amount=Decimal(amount))
        # create_all has Python defaults; migrated databases have server defaults.
        for name, value in economic_defaults.items():
            if name in economic_table.c:
                row[name] = value
        db.execute(economic_table.insert().values(**row))
    for y,k in [(2027,'budget'),(2028,'forecast'),(2029,'forecast')]:
        for fund,amount in [('inside','123.45'),('outside','10.05'),('total','133.50')]:
            if db.info.get('historical_cost_table') is not None:
                db.execute(db.info['historical_cost_table'].insert().values(activity_id=a.id,year=y,
                    value_kind=k,funding_type=fund,amount=amount,raw_text='',state='verified'))
            else:
                db.add(ActivityCostValue(activity_id=a.id,year=y,value_kind=k,funding_type=fund,amount=amount))
        db.add(DepartmentCostValue(period_id=p.id,department_id=d.id,year=y,value_kind=k,category='personnel_sgk',amount='20.00'))
        for category,amount in [('goods_services','123.45'),('personnel','15.00'),('sgk','5.00')]:economic(y,k,category,'inside',amount)
        economic(y,k,'goods_services','outside','10.05')
    from app.program_service import ECONOMIC_CATEGORIES
    db.flush()
    for y,k in [(2027,'budget'),(2028,'forecast'),(2029,'forecast')]:
        for cat in ECONOMIC_CATEGORIES:
            for fund in ['inside','outside']:
                if not db.scalar(select(EconomicValue.id).where(EconomicValue.year==y,EconomicValue.category==cat,EconomicValue.funding_type==fund)):
                    economic(y,k,cat,fund,'0')
    db.add_all([DepartmentScope(period_id=p.id,department_id=d.id,status='required'),Submission(period_id=p.id,department_id=d.id,status='draft')]);db.commit();db.expire_all()
    return dict(period=p,department=d,user=u,strategy=strategy,card=card,indicator=i,activity=a,subprogram=sp,official=official)

@pytest.fixture
def client(db,sample):
    from fastapi.testclient import TestClient
    from app.main import app,require_user
    from app.db import get_db
    def database():yield db
    app.dependency_overrides[get_db]=database
    app.dependency_overrides[require_user]=lambda:sample['user']
    client=TestClient(app)
    yield client
    client.close();app.dependency_overrides.clear()
