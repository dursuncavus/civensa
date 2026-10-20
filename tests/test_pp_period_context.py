"""PP requests must retain their department and reporting year across navigation."""
import re

import pytest
from sqlalchemy import select

from app.main import app, require_user
from app.models import (Activity, DepartmentCostValue, DepartmentScope, Indicator,
                        ReportingPeriod, Submission, SubmissionEvent)

pytestmark = pytest.mark.postgres


@pytest.fixture
def two_periods(db, sample):
    # The complete 2027 package is deliberately not the active period.
    sample['period'].status = 'draft'
    other = ReportingPeriod(year=2026, status='active')
    db.add(other)
    db.flush()
    db.add_all([
        DepartmentScope(period_id=other.id, department_id=sample['department'].id,
                        status='zero', reason='Bu yıl faaliyet bulunmuyor.'),
        Submission(period_id=other.id, department_id=sample['department'].id, status='draft'),
    ])
    db.commit()
    return sample['period'], other


def header(response, year):
    assert response.status_code == 200, response.text
    assert str(year) in re.search(r'<header[\s>].*?</header>', response.text, re.S).group()


def test_indicator_add_redirect_retains_period(client, db, sample, two_periods):
    period, other = two_periods
    did = sample['department'].id
    response = client.post(f'/program/{did}/indicator', data={
        'period_id': period.id, 'card_id': sample['card'].id,
        'name': 'Dönemi korunan gösterge', 'unit': 'Adet',
    }, follow_redirects=False)
    assert response.status_code == 303, response.text
    assert response.headers['location'] == f'/department/{did}?period_id={period.id}'
    page = client.get(response.headers['location'])
    header(page, period.year)
    assert 'Dönemi korunan gösterge' in page.text
    assert not db.scalar(select(Indicator.id).where(Indicator.period_id == other.id))


@pytest.mark.parametrize('flow', ['activity', 'personnel', 'submission'])
def test_api_write_retains_period(client, db, sample, two_periods, flow):
    period, other = two_periods
    did = sample['department'].id
    if flow == 'activity':
        response = client.post('/api/activities', json={
            'period_id': period.id, 'subprogram_id': sample['subprogram'].id,
            'name': '2027 faaliyeti',
        })
    elif flow == 'personnel':
        response = client.post(f'/api/departments/{did}/personnel-costs', json={
            'period_id': period.id, 'cost_2027_budget': '25',
        })
    else:
        response = client.post(f'/api/departments/{did}/submit?period_id={period.id}')
    assert response.status_code == 200, response.text
    assert response.json()['redirect_url'] == f'/department/{did}?period_id={period.id}'
    header(client.get(response.json()['redirect_url']), period.year)
    db.expire_all()
    if flow == 'activity':
        assert db.get(Activity, response.json()['id']).period_id == period.id
    elif flow == 'personnel':
        assert db.scalar(select(DepartmentCostValue).where(
            DepartmentCostValue.period_id == period.id,
            DepartmentCostValue.year == 2027)).amount == 25
        assert not db.scalar(select(DepartmentCostValue.id).where(DepartmentCostValue.period_id == other.id))
    else:
        assert db.scalar(select(SubmissionEvent)).period_id == period.id
        assert db.scalar(select(Submission).where(Submission.period_id == other.id)).status == 'draft'


@pytest.mark.parametrize('path', ['/dashboard', '/department/1', '/program/1'])
def test_department_headers_and_links(client, two_periods, path):
    period, _ = two_periods
    page = client.get(f'{path}?period_id={period.id}')
    header(page, period.year)
    for link in re.findall(r'href="([^"]+)"', page.text):
        if link.startswith(('/dashboard', '/department/', '/program/')):
            assert f'period_id={period.id}' in link


@pytest.mark.parametrize('path', ['/dashboard', '/review', '/report-builder', '/activity-mapping', '/structure',
                                 '/program/1/economic-split', '/operations', '/users', '/audit'])
def test_strategy_headers(client, db, sample, two_periods, path, monkeypatch):
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    period, _ = two_periods
    if path == '/operations':
        from app import main
        from sqlalchemy import text
        # Readiness inspects physical SQL tables, so use this test's PostgreSQL schema.
        with db.bind.begin() as connection:
            connection.execute(text('SET search_path TO ' + db.bind.get_execution_options()['schema_translate_map'][None]))
            connection.execute(text('CREATE TABLE alembic_version (version_num VARCHAR(100))'))
            connection.execute(text('INSERT INTO alembic_version VALUES (:head)'), {'head': main.migration_head()})
        # The connection-level search path must also apply to raw readiness SQL.
        from sqlalchemy import create_engine
        schema = db.bind.get_execution_options()['schema_translate_map'][None]
        runtime = create_engine(db.bind.url, connect_args={'options': '-csearch_path=' + schema})
        monkeypatch.setattr(main, 'engine', runtime)
        try:
            header(client.get(f'{path}?period_id={period.id}'), period.year)
        finally:
            runtime.dispose()
    else:
        header(client.get(f'{path}?period_id={period.id}'), period.year)


@pytest.mark.parametrize('access', ['excluded', 'missing'])
def test_unpermitted_period_names_year_and_next_action(client, db, sample, two_periods, access):
    period, _ = two_periods
    scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == period.id))
    if access == 'excluded':
        scope.status = 'excluded'
        scope.reason = 'Bu dönem kapsam dışı.'
    else:
        db.delete(scope)
    db.commit()
    for path in ['/dashboard', '/department/1', '/program/1']:
        response = client.get(f'{path}?period_id={period.id}')
        assert response.status_code == 403
        assert '2027' in response.json()['detail']
        assert 'Strateji' in response.json()['detail']
    response = client.post('/api/departments/1/personnel-costs', json={
        'period_id': period.id, 'cost_2027_budget': '999',
    })
    assert response.status_code == 403
    assert '2027' in response.json()['detail']


@pytest.mark.parametrize('status', ['closed', 'approved', 'submitted'])
@pytest.mark.parametrize('flow', ['indicator', 'activity', 'personnel', 'submission'])
def test_selected_period_locks_are_preserved(client, db, sample, two_periods, status, flow):
    period, _ = two_periods
    if status == 'closed':
        period.status = status
    else:
        db.scalar(select(Submission).where(Submission.period_id == period.id)).status = status
    db.commit()
    data = {'period_id': period.id}
    if flow == 'indicator':
        response = client.post('/program/1/indicator', data={**data, 'card_id': sample['card'].id,
                                                          'name': 'Engellenmeli', 'unit': 'Adet'})
    elif flow == 'activity':
        response = client.post('/api/activities', json={**data, 'name': 'Engellenmeli',
                                                       'subprogram_id': sample['subprogram'].id})
    elif flow == 'personnel':
        response = client.post('/api/departments/1/personnel-costs', json={**data, 'cost_2027_budget': '999'})
    else:
        response = client.post('/api/departments/1/submit', data=data)
    assert response.status_code == 409, response.text
    db.expire_all()
    assert not db.scalar(select(Indicator.id).where(Indicator.name == 'Engellenmeli'))
    assert not db.scalar(select(Activity.id).where(Activity.name == 'Engellenmeli'))
    assert db.scalar(select(DepartmentCostValue).where(
        DepartmentCostValue.period_id == period.id, DepartmentCostValue.year == 2027)).amount == 20


@pytest.mark.parametrize('path,method,data', [
    ('/api/indicators/1/save', 'post', {'name': 'Yanlış yıl'}),
    ('/api/activities/1', 'put', {'name': 'Yanlış yıl'}),
    ('/api/activities/1', 'delete', None),
    ('/api/activities/1/contract-bound', 'post', {'contract_bound': True}),
    ('/program/1/verify-value/1', 'post', {'value': '99'}),
])
def test_record_cannot_be_edited_from_another_period(client, db, sample, two_periods, path, method, data):
    period, other = two_periods
    args = {} if data is None else ({'data': data} if path.startswith('/program') else {'json': data})
    response = getattr(client, method)(f'{path}?period_id={other.id}', **args)
    assert response.status_code == 409, response.text
    assert '2026' in response.json()['detail'] and '2027' in response.json()['detail']
    db.expire_all()
    assert sample['indicator'].name == 'Hizmet sayısı'
    assert sample['activity'].name == 'Ortak faaliyet'


@pytest.mark.parametrize('value', ['', '0', 'bad', '99999'])
def test_explicit_invalid_period_never_falls_back(client, two_periods, value):
    response = client.get('/department/1?period_id=' + value)
    assert response.status_code in {404, 422}


def test_conflicting_query_and_body_refused(client, two_periods):
    period, other = two_periods
    response = client.post(f'/api/departments/1/personnel-costs?period_id={other.id}',
                           json={'period_id': period.id, 'cost_2027_budget': '999'})
    assert response.status_code == 422
    assert 'farklı raporlama dönemleri' in response.json()['detail']


def test_fallback_year_is_visible_and_pinned_in_links(client, two_periods):
    _, active = two_periods
    page = client.get('/dashboard')
    header(page, active.year)
    assert f'/department/1?period_id={active.id}' in page.text
    assert f'<meta name="pp-period-id" content="{active.id}">' in page.text


def test_submit_in_older_period_stays_in_older_period(client, db, two_periods):
    period, older = two_periods
    response = client.post('/api/departments/1/submit', data={'period_id': older.id})
    assert response.status_code == 200, response.text
    header(client.get(response.json()['redirect_url']), older.year)
    assert db.scalar(select(Submission).where(Submission.period_id == period.id)).status == 'draft'


def test_builder_write_returns_to_requested_period(client, sample, two_periods):
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    period, _ = two_periods
    response = client.post('/report-builder/section', data={
        'period_id': period.id, 'title': '2027 sunuş', 'kind': 'text', 'content': 'Dönem metni',
    }, follow_redirects=False)
    assert response.status_code == 303, response.text
    assert response.headers['location'] == f'/report-builder?period_id={period.id}'
    page = client.get(response.headers['location'])
    header(page, period.year)
    assert '2027 sunuş' in page.text


def test_review_decision_cannot_cross_periods(client, db, sample, two_periods):
    period, other = two_periods
    submission = db.scalar(select(Submission).where(Submission.period_id == period.id))
    submission.status = 'submitted'
    db.commit()
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    response = client.post(f'/api/submissions/{submission.id}/decision?period_id={other.id}',
                           json={'decision': 'return', 'note': 'Dönemi karıştırma.'})
    assert response.status_code == 409, response.text
    db.refresh(submission)
    assert submission.status == 'submitted'
    assert not db.scalar(select(SubmissionEvent))
