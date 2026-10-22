"""Chromium: department submit and Strategy reasoned return at two widths."""
import os
from pathlib import Path
import pytest
from playwright.sync_api import expect, sync_playwright
from test_activity_sections import section_client, login
from ar_unit_workflow_helpers import ready_unit

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('width', [1440, 390])
def test_submit_return_turkish_labels_desktop_and_mobile(section_client, db, sample, tmp_path, width):
    client, docs, _, _ = section_client
    doc = docs['birim:'+str(sample['department'].id)]
    ready_unit(db, doc, sample['user'])
    login(client, sample['user'].email)
    with sync_playwright() as playwright:
        options = {'headless':True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'): options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        browser = playwright.chromium.launch(**options)
        context = browser.new_context(viewport={'width':width, 'height':1000})
        errors = []
        def serve(route):
            request = route.request
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type':request.headers.get('content-type','')}, follow_redirects=True)
            headers = dict(response.headers); headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page(); page.on('pageerror', lambda error: errors.append(str(error)))
        url = f'http://testserver/activity-sections/reports/{doc.id}'
        page.goto(url)
        expect(page.locator('[data-ar-workflow-status]')).to_have_text('Taslak')
        page.get_by_role('button', name='Strateji’ye gönder', exact=True).click()
        expect(page.locator('[data-ar-workflow-status]')).to_have_text('Gönderildi')
        assert page.locator('form[data-ar-section-form]').count() == 0
        login(client, sample['strategy'].email)
        page.goto(url)
        reason = 'Gösterge kaynağının açıklamasını birim kaydıyla tamamlayın.'
        page.get_by_label('İade gerekçesi').fill(reason)
        page.get_by_role('button', name='Gerekçeyle iade et', exact=True).click()
        expect(page.locator('[data-ar-workflow-status]')).to_have_text('İade edildi')
        expect(page.get_by_text(reason, exact=False).first).to_be_visible()
        login(client, sample['user'].email)
        page.goto(url)
        expect(page.get_by_role('button', name='Yeniden gönder', exact=True)).to_be_visible()
        expect(page.locator('form[data-ar-section-form]')).to_be_visible()
        panel = page.get_by_role('region', name='Birim raporu iş akışı')
        assert panel.evaluate('(el) => el.getBoundingClientRect().right <= innerWidth')
        folder = Path(os.getenv('CIVENSA_UI_SCREENSHOTS', str(tmp_path)))
        folder.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(folder/f'ar-unit-return-{width}.png'), full_page=True)
        assert not errors, errors
        context.close(); browser.close()
