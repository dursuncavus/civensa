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
