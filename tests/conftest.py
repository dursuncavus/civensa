import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.db import Base
from app.models import *

@pytest.fixture
def db():
    engine=create_engine('sqlite://',poolclass=StaticPool,connect_args={'check_same_thread':False})
    @event.listens_for(engine,'connect')
    def fk(connection,record):connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    with Session(engine,expire_on_commit=False) as session:
        yield session
    engine.dispose()

@pytest.fixture
def sample(db):
    org=Organization(name='Test Belediyesi');p=ReportingPeriod(year=2027,status='active');db.add_all([org,p]);db.flush()
    d=Department(organization_id=org.id,name='Test Müdürlüğü');db.add(d);db.flush()
    u=User(email='test@example.invalid',full_name='Test',role='department',password_hash='unused',department_id=d.id)
    strategy=User(email='strategy@example.invalid',full_name='Strateji',role='strategy',password_hash='unused')
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
    for y,k in [(2027,'budget'),(2028,'forecast'),(2029,'forecast')]:
        for fund,amount in [('inside','123.45'),('outside','10.05'),('total','133.50')]:db.add(ActivityCostValue(activity_id=a.id,year=y,value_kind=k,funding_type=fund,amount=amount))
        db.add(DepartmentCostValue(period_id=p.id,department_id=d.id,year=y,value_kind=k,category='personnel_sgk',amount='20.00'))
        for category,amount in [('goods_services','123.45'),('personnel','15.00'),('sgk','5.00')]:db.add(EconomicValue(period_id=p.id,department_id=d.id,year=y,value_kind=k,category=category,program_group='service',funding_type='inside',amount=amount))
        db.add(EconomicValue(period_id=p.id,department_id=d.id,year=y,value_kind=k,category='goods_services',program_group='service',funding_type='outside',amount='10.05'))
    from app.program_service import ECONOMIC_CATEGORIES
    db.flush()
    for y,k in [(2027,'budget'),(2028,'forecast'),(2029,'forecast')]:
        for cat in ECONOMIC_CATEGORIES:
            for fund in ['inside','outside']:
                if not db.scalar(select(EconomicValue.id).where(EconomicValue.year==y,EconomicValue.category==cat,EconomicValue.funding_type==fund)):
                    db.add(EconomicValue(period_id=p.id,department_id=d.id,year=y,value_kind=k,category=cat,program_group='service',funding_type=fund,amount='0'))
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
