"""Run both Turkish decision controls in Chromium with real login/CSRF handlers."""
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from test_sidebar_ui import browser
from test_live_pilot_hardening import live_client, login
from test_source_conflicts import duplicated_personnel, source_total

pytestmark = pytest.mark.postgres


def route_application(context, client):
    def serve(route):
        request = route.request
        response = client.request(request.method, request.url, content=request.post_data_buffer,
            headers={key: value for key, value in request.headers.items() if key in ('content-type', 'x-csrf-token')},
            follow_redirects=False)
        headers = dict(response.headers)
        headers.pop('set-cookie', None)
        route.fulfill(status=response.status_code, headers=headers, body=response.content)
    context.route('http://testserver/**', serve)


def capture(page, name):
    folder = os.getenv('CIVENSA_UI_SCREENSHOTS')
    if folder:
        Path(folder).mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(Path(folder) / name))


def test_preview_conflict_control(browser, db, sample, live_client):
    client = live_client()
    login(client, sample['strategy'].email)
    sample['period'].template_status = 'verified'
    db.commit()
    with browser.new_context(viewport={'width': 1366, 'height': 1000}) as context:
        route_application(context, client)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver/dashboard')
        page.locator('#dataImportUpload').set_input_files({'name': 'kaynak.docx', 'mimeType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'buffer': duplicated_personnel()})
        item = page.locator('.import-conflict')
        expect(item).to_be_visible()
        expect(item).to_contain_text('20,00 (Tablo 2, satır 5)')
        expect(item).to_contain_text('30,00 (Tablo 3, satır 5)')
        expect(page.locator('#applyImport')).to_have_count(0)
        item.scroll_into_view_if_needed()
        capture(page, 'civ-011-preview-conflicts.png')
        item.locator('.conflict-amount').select_option('20.00')
        item.locator('.conflict-reason').fill('İlk tablo kontrol edilip doğrulandı.')
        item.get_by_role('button', name='Kararı Kaydet').click()
        expect(item).to_contain_text('Karar: 20,00')
        expect(page.locator('#applyImport')).to_be_visible()
        assert errors == []


def test_activity_decision_keeps_sibling_drafts(browser, db, sample, live_client):
    total = source_total(db, sample)
    client = live_client()
    login(client, sample['user'].email)
    with browser.new_context(viewport={'width': 1600, 'height': 1000}) as context:
        route_application(context, client)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f"http://testserver/department/{sample['department'].id}")
        draft = page.locator('.record [data-field="explanation"]').first
        draft.fill('Henüz kaydedilmemiş gösterge açıklaması.')
        page.get_by_role('button', name='Faaliyet Maliyetleri', exact=True).click()
        row = page.locator(f"tr[data-activity='{sample['activity'].id}']")
        box = row.locator('.source-disagreement').first
        expect(box).to_be_visible()
        expect(box).to_contain_text('Kaynak: 140,00 · Hesaplanan: 133,50')
        box.scroll_into_view_if_needed()
        capture(page, 'civ-011-activity-disagreement.png')
        box.locator('.source-total-reason').fill('Finansman dağılımı kontrol edilerek doğrulandı.')
        # Simulate an unsaved sibling cost draft as well as the indicator draft.
        row.get_by_role('button', name='Düzenle', exact=True).click()
        field = row.locator('.activity-cost[data-year="2028"][data-funding="inside"]')
        field.fill('150,00')
        box.get_by_role('button', name='Hesaplanan toplamı kullan', exact=True).click()
        expect(box).to_have_count(0)
        expect(field).to_have_value('150,00')
        db.expire(sample['activity'], ['cost_values'])
        assert str(next(v for v in sample['activity'].cost_values if v.year == 2028 and v.funding_type == 'inside').amount) == '123.45'
        expect(page.locator('[data-activity-total="2027:budget"]')).to_have_text('133,50')
        page.get_by_role('button', name='Performans Göstergeleri', exact=True).click()
        expect(draft).to_have_value('Henüz kaydedilmemiş gösterge açıklaması.')
        db.refresh(total)
        assert str(total.amount) == '133.50' and str(total.source_amount) == '140.00'
        assert errors == []
