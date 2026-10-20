"""Exercise the actual PP JSON writes and navigation with two open browser tabs."""
import pytest
from playwright.sync_api import expect
from sqlalchemy import select

from test_sidebar_ui import browser
from test_pp_period_context import two_periods
from app.models import Activity, DepartmentCostValue, Submission

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('flow', ['activity', 'personnel', 'submission', 'fallback_personnel'])
def test_browser_write_keeps_displayed_period(browser, client, db, sample, two_periods, flow):
    period, other = two_periods
    if flow == 'fallback_personnel':
        period.status, other.status = 'active', 'draft'
        db.commit()
    with browser.new_context(viewport={'width': 1366, 'height': 1000}) as context:
        writes = []

        def serve(route):
            request = route.request
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                                      headers={'content-type': request.headers.get('content-type', '')},
                                      follow_redirects=False)
            if request.method == 'POST' and '/api/notifications/' not in request.url:
                writes.append((request.url, response.status_code, response.headers.get('location')))
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)

        context.route('http://testserver/**', serve)
        page = context.new_page()
        query = '' if flow == 'fallback_personnel' else f'?period_id={period.id}'
        page.goto('http://testserver/department/1' + query)
        if flow == 'fallback_personnel':
            # The active year changes after the editor has loaded. Its displayed
            # fallback year must remain the write and reload context.
            period.status, other.status = 'draft', 'active'
            db.commit()
        # Opening another period in another tab must not change the editor's year.
        second = context.new_page()
        second.goto(f'http://testserver/dashboard?period_id={other.id}')
        if flow == 'activity':
            page.get_by_role('button', name='Faaliyet Maliyetleri', exact=True).click()
            page.get_by_role('button', name='Faaliyet Ekle', exact=True).click()
            row = page.locator('tr[data-new="1"]')
            row.locator('.activity-name').fill('Tarayıcı faaliyeti')
            row.locator('.activity-subprogram').select_option(str(sample['subprogram'].id))
            with page.expect_navigation():
                row.get_by_role('button', name='Kaydet', exact=True).click()
            expect(page.locator('tr[data-new="1"]')).to_have_count(0)
        elif flow in {'personnel', 'fallback_personnel'}:
            page.get_by_role('button', name='Faaliyet Maliyetleri', exact=True).click()
            page.locator('.personnel-cost[data-year="2027"][data-kind="budget"]').fill('25')
            with page.expect_navigation():
                page.locator('#savePersonnel').click()
        else:
            with page.expect_navigation():
                page.locator('#submitDepartment').click()
            expect(page.locator('#submitDepartment')).to_have_count(0)
        expect(page).to_have_url(f'http://testserver/department/1?period_id={period.id}')
        expect(page.locator('header')).to_contain_text('2027')
        assert writes and writes[-1][1] in {200, 303}, writes
        assert f'period_id={period.id}' in writes[-1][0]
        db.expire_all()
        assert not db.scalar(select(Activity.id).where(Activity.period_id == other.id))
        assert not db.scalar(select(DepartmentCostValue.id).where(DepartmentCostValue.period_id == other.id))
        assert db.scalar(select(Submission).where(Submission.period_id == other.id)).status == 'draft'


@pytest.mark.parametrize('path', ['/program/1', '/program/1/economic-split', '/report-builder', '/structure'])
def test_pp_write_forms_include_selected_period(browser, client, db, sample, two_periods, path):
    from app.main import app, require_user
    app.dependency_overrides[require_user] = lambda: sample['user' if path == '/program/1' else 'strategy']
    period, _ = two_periods
    if path.endswith('economic-split'):
        from app.models import EconomicValue
        db.add(EconomicValue(period_id=period.id, department_id=1, year=period.year,
                             value_kind='budget', category='personnel', program_group='unallocated',
                             funding_type='inside', amount=25))
        db.commit()
    response = client.get(f'{path}?period_id={period.id}')
    assert response.status_code == 200, response.text
    with browser.new_page() as page:
        page.set_content(response.text)
        forms = page.locator('form[method="post"][action^="/program/"], form[method="post"][action^="/report-builder/"], form[method="post"][action^="/structure/"]')
        assert forms.count() > 0
        for form in forms.all():
            assert form.locator('input[name="period_id"]').input_value() == str(period.id), form.get_attribute('action')


def test_pp_json_helper_sends_period_for_every_write_route(browser, client, two_periods):
    from test_pp_required_period import WRITES
    from urllib.parse import parse_qs, urlparse
    period, _ = two_periods
    with browser.new_context() as context:
        writes = []

        def serve(route):
            request = route.request
            if request.method in {'POST', 'PUT', 'DELETE'}:
                writes.append(request.url)
                route.fulfill(status=200, content_type='application/json', body='{"ok":true}')
                return
            response = client.get(request.url)
            route.fulfill(status=response.status_code, headers=dict(response.headers), body=response.content)

        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.goto(f'http://testserver/department/1?period_id={period.id}')
        routes = [(method.upper(), path) for method, path, _, _ in WRITES if path.startswith('/api/')]
        for method, path in routes:
            page.evaluate('([method,path]) => jsonFetch(path,{method})', [method, path])
        assert len(writes) == len(routes)
        assert all(parse_qs(urlparse(url).query).get('period_id') == [str(period.id)] for url in writes)
