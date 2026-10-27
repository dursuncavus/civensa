"""CIV-018 browser forms: real login/CSRF, attempted values and screenshots."""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import expect

from app.db import get_db
from app.main import app
from app.models import Department, Organization, ReportingPeriod, User
from app.security import hash_password
from tests.test_sidebar_ui import browser
from tests.test_live_pilot_hardening import login

pytestmark = pytest.mark.postgres


# Complete redirects inside TestClient so the synthetic testserver host never
# needs DNS/network access; the HTTP suite separately checks actual 303 results.
def route_to_client(context, client):
    def serve(route):
        req = route.request
        response = client.request(req.method, req.url, content=req.post_data_buffer,
            headers={'content-type': req.headers.get('content-type', '')}, follow_redirects=True)
        headers = dict(response.headers); headers.pop('set-cookie', None)
        route.fulfill(status=response.status_code, headers=headers, body=response.content)
    context.route('http://testserver/**', serve)


def screenshot(page, name):
    folder = os.getenv('CIVENSA_UI_SCREENSHOTS')
    if folder:
        path = Path(folder); path.mkdir(parents=True, exist_ok=True)
        page.evaluate("window.scrollTo(0, 0)")
        page.screenshot(path=str(path / name), full_page=True)


def test_master_data_browser_creation_error_preservation_and_period_responsibility(browser, db, sample):
    user = sample['strategy']; user.password_hash = hash_password('browser-test-only')
    db.add_all([Department(organization_id=sample['department'].organization_id, name='PARK VE BAHÇELER MÜDÜRLÜĞÜ'),
                Department(organization_id=sample['department'].organization_id, name='Park Ve Bahçeler Müdürlüğü')])
    db.commit(); app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app, follow_redirects=False) as client, browser.new_context(viewport={'width': 1366, 'height': 1000}) as context:
            login(client, user.email, 'browser-test-only'); route_to_client(context, client)
            page = context.new_page(); page.goto('http://testserver/structure')
            expect(page.get_by_role('heading', name='Aynı müdürlük olabilecek kayıtlar')).to_be_visible()
            page.locator('details summary').first.click()
            screenshot(page, 'institution-structure.png')
            form = page.locator('form[action="/structure/departments"]')
            form.locator('[name=name]').fill('İşletme ve İştirakler Müdürlüğü')
            form.get_by_role('button', name='Müdürlük oluştur').click()
            expect(page.get_by_role('region', name='Müdürlükler').get_by_label(
                'İşletme ve İştirakler Müdürlüğü yeni adı', exact=True
            )).to_have_value('İşletme ve İştirakler Müdürlüğü')
            form = page.locator('form[action="/structure/departments"]')
            form.locator('[name=name]').fill('Park Ve Bahçeler Müdürlüğü')
            form.get_by_role('button', name='Müdürlük oluştur').click()
            expect(page.get_by_role('alert')).to_contain_text('kaydıyla aynı')
            expect(page.locator('form[action="/structure/departments"] [name=name]')).to_have_value('Park Ve Bahçeler Müdürlüğü')
            screenshot(page, 'duplicate-name-error.png')
            page.goto('http://testserver/structure')
            details = page.locator('details').first; details.locator('summary').click()
            details.get_by_label('İşletme ve İştirakler Müdürlüğü', exact=True).check()
            details.get_by_role('button', name='Sorumlulukları kaydet').click()
            page.locator('details summary').first.click()
            expect(page.get_by_label('İşletme ve İştirakler Müdürlüğü', exact=True)).to_be_checked()
            screenshot(page, 'subprogramme-responsibility.png')
    finally: app.dependency_overrides.clear()


def test_first_period_browser_flow_and_values(browser, db):
    user = User(email='setup@example.invalid', full_name='Strateji', role='strategy', password_hash=hash_password('browser-test-only'))
    db.add_all([Organization(name='Yeni Belediyesi'), user]); db.commit()
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app, follow_redirects=False) as client, browser.new_context(viewport={'width': 1366, 'height': 900}) as context:
            login(client, user.email, 'browser-test-only'); route_to_client(context, client)
            page = context.new_page(); page.goto('http://testserver/dashboard')
            expect(page.get_by_role('button', name='İlk dönemi oluştur')).to_be_visible()
            screenshot(page, 'first-period.png')
            page.get_by_label('Dönem yılı', exact=True).fill('2019')
            page.get_by_role('button', name='İlk dönemi oluştur').click()
            expect(page.get_by_role('alert')).to_contain_text('2020–2100')
            expect(page.get_by_label('Dönem yılı', exact=True)).to_have_value('2019')
            page.get_by_label('Dönem yılı', exact=True).fill('2027')
            page.get_by_role('button', name='İlk dönemi oluştur').click()
            expect(page.get_by_role('heading', name='2027 Performans Programı', exact=True)).to_be_visible()
            page.get_by_role('link', name='Kurum Yapısı', exact=True).click()
            expect(page.get_by_role('heading', name='2027 · Programlar')).to_be_visible()
    finally: app.dependency_overrides.clear()
