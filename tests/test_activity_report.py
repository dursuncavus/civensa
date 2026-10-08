from decimal import Decimal
from sqlalchemy import select, func
from app.models import IndicatorValue, ReportingPeriod, Department, Indicator


def test_same_year_target_actual_and_no_forecast_fallback(client, db, sample):
    i = sample['indicator']
    db.add_all([IndicatorValue(indicator_id=i.id, year=2027, value_kind='actual', value=999),
                IndicatorValue(indicator_id=i.id, year=2026, value_kind='actual', value=888)])
    sample['period'].year = 2026
    db.add(IndicatorValue(indicator_id=i.id, year=2026, value_kind='target', value=0))
    db.commit()
    # The existing 2027 target belongs to the period but is not the selected year's target.
    r = client.get('/activity-report?year=2026')
    assert r.status_code == 200
    assert '<td>0</td>' in r.text and '<td>888</td>' in r.text
    assert '<td>999</td>' not in r.text and '<td>1,75</td>' not in r.text


def test_review_raw_text_escaped_and_missing_actual(client, db, sample):
    sample['period'].year = 2026
    v = db.scalar(select(IndicatorValue))
    v.year = 2026; v.value = Decimal('123'); v.state = 'needs_review'; v.raw_text = '<b>belirsiz</b>'
    db.commit()
    r = client.get('/activity-report?year=2026')
    assert 'Doğrulanmalı: &lt;b&gt;belirsiz&lt;/b&gt;' in r.text
    assert '<td>Kayıt yok</td>' in r.text and '<td>123</td>' not in r.text


def test_department_and_period_isolation(client, db, sample):
    sample['period'].year = 2026
    d = Department(organization_id=sample['department'].organization_id, name='Gizli Müdürlük')
    p = ReportingPeriod(year=2025); db.add_all([d,p]); db.flush()
    for did, pid, name in [(d.id,sample['period'].id,'Başka birim göstergesi'),
                           (sample['department'].id,p.id,'Başka yıl göstergesi')]:
        db.add(Indicator(period_id=pid,department_id=did,subprogram_id=sample['subprogram'].id,name=name,unit='Adet'))
    db.commit()
    before = db.scalar(select(func.count()).select_from(IndicatorValue))
    text = client.get('/activity-report?year=2026').text
    assert 'Hizmet sayısı' in text
    assert 'Başka birim göstergesi' not in text and 'Başka yıl göstergesi' not in text
    assert db.scalar(select(func.count()).select_from(IndicatorValue)) == before
    from app.main import app, require_user
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    assert 'Başka birim göstergesi' in client.get('/activity-report?year=2026').text


def test_missing_period_and_invalid_year(client):
    r = client.get('/activity-report?year=2022')
    assert r.status_code == 200 and 'gösterge kaydı yok' in r.text
    assert client.get('/activity-report?year=2027').status_code == 200
    assert client.get('/activity-report?year=2101').status_code == 422
    assert client.get('/activity-report?year=abc').status_code == 422


def test_forecast_is_not_actual_and_null_needs_review(client, db, sample):
    sample['period'].year = 2026
    v = db.scalar(select(IndicatorValue)); v.year = 2026; v.value = None
    db.add(IndicatorValue(indicator_id=sample['indicator'].id,year=2026,value_kind='year_end_estimate',value=555))
    db.commit()
    text = client.get('/activity-report?year=2026').text
    assert '<td>Doğrulanmalı</td>' in text and '<td>Kayıt yok</td>' in text
    assert '<td>555</td>' not in text
    assert client.post('/activity-report',data={'year':2026}).status_code == 405


def test_department_without_assignment_is_denied(client, sample):
    from app.main import app, require_user
    sample['user'].department_id = None
    app.dependency_overrides[require_user] = lambda: sample['user']
    assert client.get('/activity-report').status_code == 403


def test_activity_report_requires_authentication(db):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import get_db
    def database(): yield db
    app.dependency_overrides[get_db] = database
    try:
        with TestClient(app) as client:
            assert client.get('/activity-report',follow_redirects=False).status_code in (303,401)
    finally:
        app.dependency_overrides.clear()
