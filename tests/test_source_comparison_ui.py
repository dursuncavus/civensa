"""Chromium PP navigation and complete Turkish source comparison, at both widths."""
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from app.main import app, require_user
from test_sidebar_ui import browser
from test_word_import import import_context, import_client
from test_source_comparison import imported

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('viewport', [(1366, 1000), (390, 844)])
def test_turkish_comparison_desktop_mobile(browser, db, import_client, import_context, viewport):
    batch, _ = imported(db, import_context, catalogue=True)
    app.dependency_overrides[require_user] = lambda: import_context.user
    errors = []
    with browser.new_context(viewport={'width': viewport[0], 'height': viewport[1]}) as context:
        def serve(route):
            request = route.request
            response = import_client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type':request.headers.get('content-type', '')}, follow_redirects=False)
            headers = dict(response.headers); headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page(); page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'http://testserver/dashboard?period_id={batch.period_id}')
        page.get_by_role('link', name='PP Kaynak Karşılaştırması', exact=True).click()
        expect(page).to_have_url(f'http://testserver/source-comparison?period_id={batch.period_id}')
        expect(page.get_by_role('heading', name='PP kaynak karşılaştırması', exact=True)).to_be_visible()
        expect(page.locator('html')).to_have_attribute('lang', 'tr')
        expect(page.locator('header')).to_contain_text('2027')
        table = page.locator('#source-comparison')
        for label in ('Kaynak değer', 'Güncel değer', 'Fark', 'Durum / karar'):
            expect(table.get_by_role('columnheader', name=label, exact=True)).to_be_visible()
        expect(table).to_contain_text('Tablo 2 · Satır 6 · Sütun 2 · Sayfa Bilinmiyor')
        totals = table.locator('tr[data-model="total"]').filter(has_text='2027')
        expect(totals).to_have_count(3)
        expect(totals.first).to_contain_text('Eşleşiyor')
        expect(totals.first).to_contain_text('1.234,50')
        expect(page.get_by_role('link', name='CSV indir')).to_have_attribute('href', f'/source-comparison.csv?period_id={batch.period_id}')
        assert page.locator('html').evaluate('(el) => el.scrollWidth <= el.clientWidth')
        # All cells remain reachable in the keyboard-scrollable table on mobile.
        region = page.get_by_role('region', name='Kaynak karşılaştırma tablosu')
        region.focus()
        table.get_by_role('columnheader', name='Durum / karar').scroll_into_view_if_needed()
        expect(table.get_by_role('columnheader', name='Durum / karar')).to_be_in_viewport()
        screenshots = os.getenv('CIVENSA_UI_SCREENSHOTS')
        if screenshots:
            folder = Path(screenshots); folder.mkdir(parents=True, exist_ok=True)
            page.goto(f'http://testserver/source-comparison?period_id={batch.period_id}')
            page.screenshot(path=str(folder / f'comparison-{viewport[0]}.png'))
            page.locator('tr[data-model="total"]').first.scroll_into_view_if_needed()
            page.screenshot(path=str(folder / f'comparison-totals-{viewport[0]}.png'))
        assert not errors
