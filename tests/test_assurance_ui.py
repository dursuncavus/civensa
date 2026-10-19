"""Browser acceptance for variable fields, locked preview and EKLER navigation."""
import os
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright, expect
from test_activity_sections import section_client, login

pytestmark = pytest.mark.postgres


def test_assurance_form_and_locked_preview_in_browser(section_client, tmp_path):
    client, docs, _, _ = section_client
    login(client, 'strategy@example.invalid')
    doc = docs['idare']
    folder = Path(os.getenv('CIVENSA_UI_SCREENSHOTS', str(tmp_path))); folder.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        options = {'headless': True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'): options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        browser = p.chromium.launch(**options)
        context = browser.new_context(viewport={'width': 1440, 'height': 1060})
        def serve(route):
            request = route.request
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                # Resolve local form redirects inside TestClient as well.
                headers={'content-type': request.headers.get('content-type', '')}, follow_redirects=True)
            headers = dict(response.headers); headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.goto(f'http://testserver/activity-sections/reports/{doc.id}?code=EKLER')
        assert page.locator('textarea[name=text]').count() == 0
        page.get_by_role('link', name='Beyan alanlarını aç').first.click()
        page.locator('[name=place]').fill('Ankara')
        page.locator('[name=date]').fill('2028-02-15')
        for i, person in enumerate([
            {'person_ref': 'a', 'name': 'Ayşe Yılmaz', 'title': 'Belediye Başkanı', 'start_date': '2027-01-01', 'end_date': '2027-06-30'},
            {'person_ref': 'b', 'name': 'Mehmet Kaya', 'title': 'Belediye Başkanı', 'start_date': '2027-07-01', 'end_date': '2027-12-31'},
        ]):
            for key, value in person.items(): page.locator(f'[name={key}_{i}]').fill(value)
        page.locator('[name=reservation_text_0]').fill('Envanter sayımı eksik')
        page.locator('[name=reservation_justification_0]').fill('Arşivde kayıt bulunamadı.')
        page.get_by_role('button', name='Beyan alanlarını kaydet').click()
        preview = page.locator('[aria-label="Kilitli beyan metni"]')
        expect(preview).to_contain_text('benden önceki yönetici/yöneticilerden almış olduğum bilgiler ile desteklenmektedir.')
        expect(preview).to_contain_text('(Ankara - 15.02.2028)')
        expect(preview).to_contain_text('Ad-Soyad: Mehmet Kaya')
        expect(preview).to_contain_text('Gerekçe: Arşivde kayıt bulunamadı.')
        assert page.locator('[name=body], [name=signature], [name=predecessor_phrase]').count() == 0
        preview.screenshot(path=str(folder / 'assurance-locked-preview.png'))
        page.goto(f'http://testserver/activity-sections/reports/{doc.id}/assurances/EK-3')
        expect(page.get_by_text('Bu beyan salt okunurdur.')).to_be_visible()
        context.close(); browser.close()
