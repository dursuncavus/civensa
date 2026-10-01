"""Upgrade a populated v4 database; compare raw values, row identity and indexes."""
import os,subprocess,sys
from pathlib import Path
from sqlalchemy import create_engine,MetaData,select,inspect

ROOT=Path(__file__).resolve().parents[1]

def test_populated_v4_migration(tmp_path):
    url=f'sqlite:///{tmp_path / "upgrade.db"}'
    env={**os.environ,'DATABASE_URL':url}
    def migrate(rev):
        result=subprocess.run([sys.executable,'-m','alembic','upgrade',rev],cwd=ROOT,env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    migrate('d4f0a1b2c3d4')
    engine=create_engine(url);meta=MetaData();meta.reflect(engine)
    data={
      'organizations':dict(id=1,name='Test'),
      'reporting_periods':dict(id=1,year=2027,status='active',template_status='verified'),
      'departments':dict(id=1,organization_id=1,name='Test Müdürlüğü'),
      'programs':dict(id=1,period_id=1,name='Program'),
      'subprograms':dict(id=1,period_id=1,program_id=1,name='Alt',rationale='',goal=''),
      'indicators':dict(id=1,period_id=1,department_id=1,subprogram_id=1,name='Gösterge',unit='Oran',explanation='',calculation_method='',data_source='',status='draft'),
      'indicator_values':dict(id=1,indicator_id=1,year=2025,value_kind='value',value=1.75),
      'activities':dict(id=1,period_id=1,department_id=1,subprogram_id=1,name='Faaliyet',explanation=''),
      'activity_cost_values':dict(id=1,activity_id=1,year=2027,value_kind='budget',funding_type='total',amount=1234567.89),
      'department_cost_values':dict(id=1,period_id=1,department_id=1,year=2027,value_kind='budget',category='personnel_sgk',amount=1.234)
    }
    with engine.begin() as conn:
        for name,row in data.items():conn.execute(meta.tables[name].insert().values(**row))
    old_indexes={t:{i['name'] for i in inspect(engine).get_indexes(t)} for t in data}
    engine.dispose();migrate('head')
    engine=create_engine(url);meta=MetaData();meta.reflect(engine)
    with engine.connect() as conn:
        for name in data:assert len(conn.execute(select(meta.tables[name])).all())==1
        value=conn.execute(select(meta.tables['indicator_values'])).mappings().one()
        assert str(value['value'])=='1.750000' and value['raw_text']=='1.75' and value['state']=='needs_review'
        cost=conn.execute(select(meta.tables['activity_cost_values'])).mappings().one()
        assert str(cost['amount'])=='1234567.89' and cost['raw_text']=='1234567.89'
        personnel=conn.execute(select(meta.tables['department_cost_values'])).mappings().one()
        assert personnel['state']=='needs_review' and personnel['raw_text']=='1.234'
        assert not conn.execute(select(meta.tables['report_cards'])).all()
    for table,names in old_indexes.items():assert names<={i['name'] for i in inspect(engine).get_indexes(table)}
    engine.dispose()
