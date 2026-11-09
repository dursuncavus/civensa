"""CIV-191: directorate guidance and export status on real rendered pages."""
import os
from pathlib import Path

import pytest
from test_activity_sections import section_client, login, ready_and_freeze
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
INFO = 'Bu bölümü Mali Hizmetler dolduracak; gönderiminizi engellemez.'
ACTION = 'giriş veya XLSX içe aktarma yapın'


@pytest.mark.parametrize('actor', ['user', 'finance', 'strategy'])
def test_finance_guidance_by_existing_role(section_client, sample, actor):
    client, docs, _, finance = section_client
    email = 'finance@example.invalid' if actor == 'finance' else sample[actor].email
    dep_id = finance.id if actor == 'finance' else sample['department'].id
    login(client, email)
    doc = docs['birim:' + str(dep_id)]
    for url in ['/activity-sections', f'/activity-sections/reports/{doc.id}?code=III.A.1']:
        response = client.get(url)
        assert response.status_code == 200
        assert (INFO in response.text) == (actor == 'user')
        assert (ACTION in response.text) == (actor != 'user')


def test_draft_and_approved_export_labels(section_client, sample):
    client, docs, _, _ = section_client
    doc = docs['birim:' + str(sample['department'].id)]
    token = login(client, sample['strategy'].email)
    urls = ['/activity-sections', f'/activity-sections/reports/{doc.id}']
    for url in urls:
        page = client.get(url).text
        assert 'Taslak — Word (onaysız)' in page
        assert 'Taslak — PDF (onaysız)' in page
    ready_and_freeze(client, token, doc)
    login(client, sample['user'].email)
    for url in urls:
        page = client.get(url).text
        assert 'Word olarak indir' in page and 'PDF olarak indir' in page
        assert 'Taslak — Word (onaysız)' not in page
        assert 'Taslak — PDF (onaysız)' not in page


def test_current_section_guidance(section_client, sample):
    client, docs, _, _ = section_client
    doc = docs['birim:' + str(sample['department'].id)]
    login(client, sample['user'].email)
    page = client.get(f'/activity-sections/reports/{doc.id}?code=III.B.1').text
    assert 'daha sonra eklenecek' not in page
    assert 'Bölüm içeriği alanına açıklamanızı yazın' in page
    assert '<textarea name="text"' in page
    readonly = client.get(f"/activity-sections/reports/{docs['idare'].id}?code=III.B.1")
    assert readonly.status_code == 200
    assert 'Bu bölüm Strateji tarafından doldurulur.' in readonly.text
    assert '<textarea name="text"' not in readonly.text


def test_capture_four_places(section_client, sample, browser):
    output = os.getenv('CIV191_SCREENSHOTS')
    if not output:
        return
    client, docs, _, _ = section_client
    doc = docs['birim:' + str(sample['department'].id)]
    login(client, sample['user'].email)
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    with browser.new_page(viewport={'width':1440, 'height':900}) as page:
        def serve(route):
            response = client.get(route.request.url)
            route.fulfill(status=response.status_code, body=response.content,
                          content_type=response.headers.get('content-type', ''))
        page.route('**/*', serve)
        for name, path, selector in [
            ('01-menu', '/activity-reports', None),
            ('02-taslak', f'/activity-sections/reports/{doc.id}', '.section-export'),
            ('03-mali', f'/activity-sections/reports/{doc.id}?code=III.A.1', '[aria-label="Malî bilgi uyarıları"]'),
            ('04-bolum', f'/activity-sections/reports/{doc.id}?code=III.B.1', '.section-writing')]:
            page.goto('http://testserver' + path)
            if name == '02-taslak':
                page.locator('.section-export').evaluate('(el) => el.open = true')
            if selector:
                page.locator(selector).first.scroll_into_view_if_needed()
            page.screenshot(path=str(target / (name + '.png')))
