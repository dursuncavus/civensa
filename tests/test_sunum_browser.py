"""Offline Chrome acceptance and opt-in synthetic report screenshots."""
from io import BytesIO
import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright, expect
from pypdf import PdfReader

from app import activity_sections_service as service
from app.sunum import render_deck
from ar_unit_workflow_helpers import ensure_core_ready
from test_activity_sections import section_client, login, resource, save

pytestmark = pytest.mark.postgres


def browser_options():
    options = {'headless': True}
    if os.getenv('CIVENSA_CHROMIUM_PATH'):
        options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
    return options


def deck_url(page, path):
    # Some managed desktop policies block file://. This opt-in only serves the
    # same bytes through Playwright interception, without a network server.
    if os.getenv('CIVENSA_SUNUM_HTTP_FIXTURE') == '1':
        url = 'http://testserver/sunum.html'
        page.route(url, lambda route: route.fulfill(content_type='text/html', body=path.read_bytes()))
        return url
    return path.as_uri()


def test_served_deck_runs_with_actual_security_headers(section_client, sample):
    client, docs, _, _ = section_client
    doc = docs[f"birim:{sample['department'].id}"]
    response = client.get(f'/activity-sections/reports/{doc.id}/sunum')
    policy = response.headers['content-security-policy']
    assert "script-src 'unsafe-inline'" in policy
    assert "connect-src 'none'" in policy
    assert "script-src 'self'" in client.get('/modules').headers['content-security-policy']
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**browser_options())
        page = browser.new_page(viewport={'width': 1920, 'height': 1080}, offline=True)
        headers = dict(response.headers)
        headers.pop('set-cookie', None)
        url = f'http://testserver/activity-sections/reports/{doc.id}/sunum'
        page.route(url, lambda route: route.fulfill(status=response.status_code,
            headers=headers, body=response.content))
        page.goto(url)
        page.wait_for_function('() => window.sunumRendered === true')
        assert page.locator('section.present').get_attribute('data-type') == 'cover'
        expect(page.locator('section.present img.logo')).to_be_visible()
        browser.close()


def test_real_report_offline_motion_all_slide_types_and_pdf(section_client, db, sample, tmp_path):
    client, docs, _, _ = section_client
    doc = docs[f"birim:{sample['department'].id}"]
    token = login(client, 'strategy@example.invalid')
    assert resource(client, token, doc, 'employment', [dict(category='memur', count=18),
        dict(category='işçi — kadrolu', count=4), dict(category='şirket personeli/hizmet alımı', count=110)]).status_code == 200
    assert resource(client, token, doc, 'buildings', [dict(name='Merkez hizmet binası', category='Hizmet binası',
        address='Merkez', area=250, ownership='mülk'), dict(name='Saha ofisi', category='Ofis',
        address='Saha', area=None, ownership='tahsis')]).status_code == 200
    assert save(client, token, doc, 'I.B', blocks=[dict(type='bullets', items=[
        'Vatandaş taleplerini değerlendirmek', 'Hizmetleri planlamak', 'Kaynakları verimli kullanmak',
        'Çalışmaları denetlemek', 'Sonuçları raporlamak'])]).status_code == 200
    assert save(client, token, doc, 'II.B', blocks=[dict(type='paragraph',
        text='Erişilebilir ve sürdürülebilir kamusal alanlar oluşturmak.'), dict(type='paragraph',
        text='Vatandaş katılımını destekleyen hizmetler sunmak.')]).status_code == 200
    assert save(client, token, doc, 'III.B.1', blocks=[dict(type='table', rows=[
        ['Faaliyet', 'Maliyet (TL)', 'Durum'], ['Park bakımı', '12.500,23', 'Tamamlandı'],
        ['Yol yenileme', '', 'Sürüyor']])]).status_code == 200
    idare = docs['idare']
    response = client.post(f'/api/activity-sections/reports/{idare.id}/financial/budget/expenditure',
        headers={'X-CSRF-Token': token}, json={'expected_revision': idare.revision, 'rows': [dict(
            department_id=doc.department_id, economic_code='03', initial='710.000.000,00', added='101.776.000,00',
            deducted='0', actual='613.713.763,78', cancelled='0', carried='0')]})
    assert response.status_code == 200, response.text
    ensure_core_ready(db, doc, sample['strategy'])
    db.commit()
    payload = service.report_data(db, sample['strategy'], doc.id)
    assert payload['financial']['tables']['expenditure']['rows']
    content = client.get(f'/activity-sections/reports/{doc.id}/sunum.html').content
    path = tmp_path / 'sunum.html'
    path.write_bytes(content)
    folder = Path(os.environ.get('CIVENSA_SUNUM_ARTIFACTS', tmp_path))
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'single-file-size.txt').write_text(f'{len(content)} bytes\n', encoding='utf-8')
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**browser_options())
        context = browser.new_context(viewport={'width': 1920, 'height': 1080}, offline=True)
        page = context.new_page()
        errors, network = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: network.append(request.url) if request.url.startswith(('http:', 'https:')) else None)
        url = deck_url(page, path)
        page.goto(url)
        page.wait_for_function('() => window.sunumRendered === true')
        assert page.evaluate('Reveal.VERSION') == '6.0.1'
        assert page.evaluate('echarts.version') == '6.1.0'
        assert page.locator('img.logo').first.evaluate('(el)=>el.naturalWidth') > 0
        assert page.evaluate('document.fonts.check(\'400 34px "Fira Sans"\')')
        for kind in ['cover', 'map', 'separator', 'kpi', 'chart', 'table', 'bullets', 'quote', 'closing']:
            page.evaluate('(kind)=>deck.slide(deck.getIndices(document.querySelector("section[data-type="+kind+"]")).h,0,-1)', kind)
            if kind == 'kpi':
                page.wait_for_timeout(150)
                assert ',' not in page.locator('section.present [data-count]').first.inner_text()
            page.wait_for_timeout(1000)
            if kind == 'bullets':
                assert page.locator('section.present .fragment.visible').count() == 0
                page.keyboard.press('ArrowRight')
                assert page.locator('section.present .fragment.visible').count() == 1
                for _ in range(4):
                    page.keyboard.press('ArrowRight')
                assert page.locator('section.present .fragment.visible').count() == 5
                page.wait_for_timeout(300)
            if kind == 'chart':
                expect(page.locator('section.present [data-chart] svg')).to_be_visible()
            if kind == 'table':
                page.wait_for_timeout(500)
                assert page.locator('section.present tr.row').evaluate_all('(rows)=>rows.every(r=>getComputedStyle(r).opacity==="1")')
            if kind == 'kpi':
                assert page.locator('section.present [data-count]').first.inner_text() == '132'
            page.screenshot(path=str(folder / f'{kind}.png'))
        # Viewing the final content slide of a section marks its map tile.
        page.evaluate('deck.slide(deck.getIndices(document.querySelector("section[data-sec=t1][data-type=quote]")).h)')
        page.wait_for_timeout(900)
        assert 'done' in page.locator('#harita [data-id=t1]').get_attribute('class')
        page.mouse.move(200, 200)
        expect(page.locator('#tools')).not_to_have_class('tools hide')
        page.wait_for_timeout(2700)
        expect(page.locator('#tools')).to_have_class('tools hide')
        page.mouse.move(201, 201)
        page.get_by_role('button', name='Haritaya dön', exact=True).click()
        expect(page.locator('section.present')).to_have_attribute('data-type', 'map')
        page.get_by_role('button', name='Sunum notları', exact=True).click()
        expect(page.locator('section.present .note')).to_be_visible()
        page.get_by_role('link', name='PDF görünümü', exact=True).click()
        page.wait_for_function('() => document.documentElement.classList.contains("pdf") && window.sunumRendered === true')
        expect(page.locator('.pdf-help')).to_contain_text('Yazdır → PDF olarak kaydet')
        assert page.locator('.tools').is_hidden()
        assert page.locator('.note:visible').count() == 0
        assert page.locator('.fragment').evaluate_all('(els)=>els.every(e=>getComputedStyle(e).opacity==="1")')
        assert page.locator('[data-count]').evaluate_all('(els)=>els.every(e=>e.textContent!=="0" || Number(e.dataset.count)===0)')
        assert page.evaluate('[...document.querySelectorAll("[data-chart]")].every(e=>echarts.getInstanceByDom(e).getOption().animation===false)')
        assert page.evaluate('echarts.getInstanceByDom(document.querySelector("section[data-sec=t2] [data-chart]")).getOption().yAxis[0].name') == 'milyon TL'
        first_page = page.locator('.pdf-page').first
        first_page.screenshot(path=str(folder / 'pdf.png'))
        pdf = page.pdf(prefer_css_page_size=True, print_background=True)
        reader = PdfReader(BytesIO(pdf))
        assert len(reader.pages) == page.locator('.slides>section, .slides>.pdf-page>section').count()
        assert all(abs(float(p.mediabox.width) / float(p.mediabox.height) - 16 / 9) < .001 for p in reader.pages)
        pdf_text = '\n'.join(p.extract_text() for p in reader.pages)
        for value in ['132', '811,78', '12.500,23', 'Sonuçları raporlamak']:
            assert value in pdf_text
        assert all(request == url for request in network)
        assert not errors, errors
        context.close()
        browser.close()


@pytest.mark.parametrize('variant', ['bar', 'horizontal', 'stacked'])
def test_generic_chart_variants_and_eight_kpis_offline(tmp_path, variant):
    slides = [dict(type='chart', title='Grafik', source='Test raporu', variant=variant,
        categories=['Birinci', 'İkinci'], series=[dict(name='Seri 1', values=[12.5, 0]),
            dict(name='Seri 2', values=[3, 7])]), dict(type='kpi', title='Sekiz rakam', source='Test raporu',
        figures=[dict(value=i, label=f'Rakam {i}', unit='adet') for i in range(8)])]
    path = tmp_path / 'generic.html'
    path.write_bytes(render_deck(slides, title='Test raporu', code='ABCD-1234'))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**browser_options())
        page = browser.new_page(viewport={'width': 1920, 'height': 1080}, offline=True)
        page.goto(deck_url(page, path) + '#pdf')
        page.wait_for_function('() => window.sunumRendered === true')
        assert page.locator('[data-chart] svg').count() == 1
        assert page.locator('.kpi').count() == 8
        option = page.evaluate('echarts.getInstanceByDom(document.querySelector("[data-chart]")).getOption()')
        assert option['series'][0]['data'] == [12.5, 0]
        assert (option['series'][0].get('stack') == 'total') == (variant == 'stacked')
        browser.close()
