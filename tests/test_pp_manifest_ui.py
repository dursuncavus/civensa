"""CIV-071 real Chromium navigation, period isolation and copy conflict display."""
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import pytest
from playwright.sync_api import expect
from sqlalchemy import select

from app.main import app, require_user
from app.models import ReportSection, ReportingPeriod
from test_sidebar_ui import browser
from test_word_import import import_client, import_context
from test_pp_general_sections import section_document

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('viewport', [(1366, 1000), (390, 844)])
def test_manifest_turkish_links_keep_selected_period(browser, client, db, sample, viewport):
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    period = sample['period']
    other = ReportingPeriod(year=2028, status='active')
    period.status = 'draft'
    db.add(other); db.flush()
    db.add_all([
        ReportSection(period_id=period.id, title='Başkan Sunuşu', content_json='{"text":"Kentimiz için birlikte."}'),
        ReportSection(period_id=period.id, title='Teşkilat Yapısı', content_json='{"text":""}'),
        ReportSection(period_id=other.id, title='Başkan Sunuşu', content_json='{"text":"Başka dönem."}'),
    ]); db.commit()
    errors = []
    with browser.new_context(viewport={'width':viewport[0], 'height':viewport[1]}) as context:
        def serve(route):
            request = route.request
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type':request.headers.get('content-type','')}, follow_redirects=False)
            headers = dict(response.headers); headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page(); page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'http://testserver/dashboard?period_id={period.id}')
        page.get_by_role('link', name='PP Tamamlanma Listesi', exact=True).click()
        expect(page.get_by_role('heading', name='PP Tamamlanma Listesi', exact=True)).to_be_visible()
        expect(page.locator('html')).to_have_attribute('lang', 'tr')
        expect(page.locator('header')).to_contain_text('2027')
        for key, status in [('foreword','Tamam'), ('organization','Boş'), ('authority','Eksik')]:
            expect(page.locator(f'tr[data-key="{key}"]')).to_contain_text(status)
        # Another open period must not change any fix link's context.
        second = context.new_page(); second.goto(f'http://testserver/dashboard?period_id={other.id}')
        links = page.locator('#pp-manifest tbody a')
        destinations = set(links.evaluate_all('(links)=>links.map(a=>a.href)'))
        for href in destinations:
            assert parse_qs(urlparse(href).query)['period_id'] == [str(period.id)]
            response = client.get(href)
            assert response.status_code == 200, (href, response.text[:100])
        page.locator('tr[data-key="foreword"] a').click()
        expect(page).to_have_url(f'http://testserver/report-builder?period_id={period.id}#section-1')
        expect(page.locator('#section-1')).to_be_visible()
        page.goto(f'http://testserver/report-builder/manifest?period_id={period.id}')
        if os.getenv('CIVENSA_UI_SCREENSHOTS'):
            folder = Path(os.environ['CIVENSA_UI_SCREENSHOTS']); folder.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(folder / f'manifest-{viewport[0]}.png'), full_page=True)
        page.get_by_label('Raporlama dönemi').select_option(str(other.id))
        page.get_by_role('button', name='Dönemi Göster').click()
        expect(page).to_have_url(f'http://testserver/report-builder/manifest?period_id={other.id}')
        expect(page.locator('header')).to_contain_text('2028')
        assert not errors


def test_explicit_copy_form_lists_conflict_and_does_not_overwrite(browser, client, db, sample):
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    base = sample['period']; target = ReportingPeriod(year=2028)
    db.add(target); db.flush()
    original = ReportSection(period_id=base.id, title='Başkan Sunuşu', content_json='{"text":"Kaynak"}')
    edited = ReportSection(period_id=target.id, title='Başkan Sunuşu', content_json='{"text":"Elle düzenlendi"}')
    db.add_all([original, edited]); db.commit()
    with browser.new_context() as context:
        def serve(route):
            request = route.request
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type':request.headers.get('content-type','')}, follow_redirects=False)
            headers = dict(response.headers); headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.goto(f'http://testserver/report-builder?period_id={target.id}')
        page.get_by_text('Başka Dönemden Genel Bölümleri Kopyala', exact=True).click()
        page.get_by_label('Kaynak dönem').select_option(str(base.id))
        page.get_by_role('button', name='Genel Bölümleri Kopyala', exact=True).click()
        expect(page.get_by_role('status')).to_contain_text('Mevcut bölüm korundu')
        expect(page.get_by_role('status')).to_contain_text('1 mevcut bölüm korundu')
        page.get_by_role('status').get_by_role('link', name='Hedef Bölümü Aç').click()
        expect(page).to_have_url(f'http://testserver/report-builder?period_id={target.id}#section-{edited.id}')
    db.refresh(edited)
    assert edited.content_json == '{"text":"Elle düzenlendi"}'
    assert len(db.scalars(select(ReportSection).where(ReportSection.period_id == target.id)).all()) == 1


def test_word_preview_displays_sections_and_applies_and_reverts_in_browser(browser, db, import_client, import_context):
    app.dependency_overrides[require_user] = lambda: import_context.user
    period = import_context.period
    with browser.new_context() as context:
        errors = []
        def serve(route):
            request = route.request
            response = import_client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type':request.headers.get('content-type','')}, follow_redirects=False)
            headers = dict(response.headers); headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page(); page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'http://testserver/dashboard?period_id={period.id}')
        page.locator('#dataImportUpload').set_input_files({
            'name':'genel.docx', 'mimeType':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'buffer':section_document()})
        expect(page.locator('#importResult')).to_contain_text('Genel Kitap Bölümleri')
        expect(page.locator('#importResult')).to_contain_text('A- Yetki, Görev ve Sorumluluklar · Eklenecek')
        assert not db.scalar(select(ReportSection.id))
        page.get_by_role('link', name='Genel Bölüm İçeriklerini İncele').click()
        expect(page).to_have_url(f'http://testserver/report-builder/import/1?period_id={period.id}')
        page.get_by_text('A- Yetki, Görev ve Sorumluluklar · Eklenecek', exact=True).click()
        expect(page.get_by_text('5393 sayılı Kanun kapsamında hizmet sunulur.', exact=False)).to_be_visible()
        page.get_by_role('button', name='Önizlemeyi Uygula', exact=True).click()
        expect(page).to_have_url(f'http://testserver/report-builder/manifest?period_id={period.id}')
        expect(page.locator('tr[data-key="authority"]')).to_contain_text('Tamam')
        page.goto(f'http://testserver/report-builder/import/1?period_id={period.id}')
        page.get_by_role('button', name='İçe Aktarmayı Geri Al', exact=True).click()
        expect(page).to_have_url(f'http://testserver/report-builder/manifest?period_id={period.id}')
        expect(page.locator('tr[data-key="authority"]')).to_contain_text('Eksik')
        assert not errors
