"""CIV-166 browser evidence: one central-finance warning and successful submit."""
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

from test_activity_sections import section_client
from test_activity_financial import expenditure, programme
from test_activity_financial_warnings import prepare

INFO = 'Bu bölümü Mali Hizmetler dolduracak; gönderiminizi engellemez.'

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('width', [1366, 390])
def test_unit_finance_warning_index_and_submitted_count(section_client, db, sample, tmp_path, width):
    client, _, doc, _ = prepare(section_client, db, sample,
        expenditure(sample['department'].id, entered_final=12500.23), programme(sample))
    folder = Path(os.getenv('CIVENSA_UI_SCREENSHOTS', str(tmp_path)))
    folder.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        options = {'headless': True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'):
            options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        browser = playwright.chromium.launch(**options)
        context = browser.new_context(viewport={'width': width, 'height': 1000})
        errors = []

        def serve(route):
            request = route.request
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type': request.headers.get('content-type', '')}, follow_redirects=True)
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)

        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        url = f'http://testserver/activity-sections/reports/{doc.id}?code=III.A.1'
        page.goto(url)
        warning_panel = page.get_by_role('region', name='Malî bilgi uyarıları')
        expect(warning_panel.get_by_role('heading', name='Uyarılar (gönderimi engellemez)')).to_be_visible()
        expect(warning_panel.get_by_role('status')).to_have_text(INFO)
        expect(warning_panel.locator('.ar-warning')).to_have_count(0)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        warning_panel.evaluate('(el) => { el.scrollIntoView(); window.scrollBy(0, -24); }')
        page.screenshot(path=str(folder / f'unit-financial-warning-{width}.png'))

        page.goto('http://testserver/activity-sections?section=III.A.1')
        completion = page.locator(f'.report-group[aria-labelledby="report-{doc.id}"]')
        expect(completion.get_by_role('heading', name='Uyarılar (gönderimi engellemez)')).to_be_visible()
        expect(completion.get_by_role('status')).to_have_text(INFO)
        expect(completion.locator('.ar-warning')).to_have_count(0)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        completion.evaluate('(el) => { el.scrollIntoView(); window.scrollBy(0, -24); }')
        page.screenshot(path=str(folder / f'unit-section-warning-{width}.png'))

        page.goto(url)
        page.get_by_role('button', name='Strateji’ye gönder', exact=True).click()
        workflow = page.get_by_role('region', name='Birim raporu iş akışı')
        expect(workflow.locator('[data-ar-workflow-status]')).to_have_text('Gönderildi')
        expect(workflow.get_by_role('status')).to_have_text(
            'Birim faaliyet raporu gönderildi. Mali Hizmetler verisinde 1 uyarı var; '
            'Strateji ve Mali Hizmetler bilgilendirilmelidir.')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        workflow.evaluate('(el) => { el.scrollIntoView(); window.scrollBy(0, -24); }')
        page.screenshot(path=str(folder / f'unit-submitted-warning-{width}.png'))
        assert not errors, errors
        context.close()
        browser.close()
