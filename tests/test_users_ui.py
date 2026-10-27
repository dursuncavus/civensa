"""Strategy's six-step CSV walkthrough and personal first login in Chromium."""
import csv
import io
import os
from pathlib import Path
import secrets
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models import AuditLog, User
from tests.test_users_personal_accounts import accounts, csv_bytes, row

pytestmark = pytest.mark.postgres


@pytest.fixture
def local_accounts_http(accounts, db):
    # A loopback HTTP bridge lets Chromium follow the app's actual 303 redirects.
    client = accounts[0]()
    previous_database = app.dependency_overrides[get_db]
    def request_database():
        # Browser requests can overlap assertions on the fixture's Session.
        # Match production's per-request lifetime: rollback/close must never
        # close the assertion thread's in-use connection.
        with Session(db.get_bind(), expire_on_commit=False) as request_db:
            yield request_db
    app.dependency_overrides[get_db] = request_database
    class Handler(BaseHTTPRequestHandler):
        def serve(self):
            body = self.rfile.read(int(self.headers.get('content-length', '0')))
            response = client.request(self.command, self.path, content=body, headers={
                'content-type': self.headers.get('content-type', ''),
                'X-CSRF-Token': self.headers.get('X-CSRF-Token', '')}, follow_redirects=False)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in {'content-length', 'transfer-encoding', 'connection', 'set-cookie'}:
                    self.send_header(key, value)
            self.send_header('Content-Length', str(len(response.content)))
            self.end_headers(); self.wfile.write(response.content)
        do_GET = do_POST = serve
        def log_message(self, *args):
            pass
    server = HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        yield 'http://127.0.0.1:' + str(server.server_port)
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)
        app.dependency_overrides[get_db] = previous_database


@pytest.fixture
def policy_browser():
    with sync_playwright() as pw:
        options = {'headless': True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'):
            options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        with pw.chromium.launch(**options) as browser:
            yield browser


def test_account_change_policy_visible_by_table_and_in_new_user_form(policy_browser, local_accounts_http):
    policy = ('Rol veya müdürlük değişiminde hesap taşınmaz. '
              'Mevcut hesabı gerekçe yazarak kapatın, kişiye yeni hesap açın. '
              'Eski işlemler eski müdürlükte kalır.')
    with policy_browser.new_page() as page:
        page.goto(local_accounts_http + '/users')
        expect(page.locator('#accountChangePolicy')).to_have_text(policy)
        expect(page.locator('#accountChangePolicy')).to_be_visible()
        expect(page.locator('#accountChangePolicy + .table-wrap table')).to_be_visible()
        expect(page.locator('#newUserForm')).to_be_hidden()
        page.get_by_role('button', name='Kullanıcı ekle', exact=True).click()
        expect(page.locator('#newUserForm').get_by_text(policy, exact=True)).to_be_visible()


def test_strategy_six_step_import_retirement_and_first_login(db, sample, accounts, local_accounts_http):
    base = local_accounts_http
    with sync_playwright() as pw:
        options = {'headless': True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'):
            options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        with pw.chromium.launch(**options) as browser, browser.new_context(
            accept_downloads=True, viewport={'width': 1366, 'height': 1000}
        ) as context:
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('dialog', lambda dialog: dialog.accept())
            page.goto(base + '/users')
            # 1. Download the BOM template, including already served directorates.
            with page.expect_download() as event:
                page.get_by_role('link', name='Şablonu indir', exact=True).click()
            template = Path(event.value.path()).read_bytes().decode('utf-8-sig')
            assert list(csv.reader(io.StringIO(template)))[0][-1] == 'Görev'
            # 2. Fill personal rows in memory. The uploaded file has no passwords.
            rows = [row(sample, 1, 'Müdür'), row(sample, 2), row(sample, 3)]
            page.locator('#bulkUserFile').set_input_files({'name': 'kisisel-hesaplar.csv',
                'mimeType': 'text/csv', 'buffer': csv_bytes(rows)})
            # 3. Preview names, directorates and duties.
            page.get_by_role('button', name='Önizle', exact=True).click()
            expect(page.locator('#bulkUserResult')).to_contain_text('3 kişisel hesap oluşturulmaya hazır.')
            assert page.locator('#bulkUserResult tbody tr').count() == 3
            screenshots = os.getenv('CIVENSA_UI_SCREENSHOTS')
            def screenshot(name):
                if screenshots:
                    folder = Path(screenshots); folder.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(folder / name), full_page=True)
            screenshot('strategy-preview.png')
            # 4. Create, without persisting the response in browser storage.
            page.get_by_role('button', name='Hesapları oluştur', exact=True).click()
            expect(page.locator('#downloadBulkCredentials')).to_be_visible()
            assert page.evaluate('localStorage.length + sessionStorage.length') == 0
            # 5. Download once. Passwords never appear in the DOM or screenshots.
            with page.expect_download() as event:
                page.get_by_role('button', name='Parola dosyasını indir', exact=True).click()
            downloaded = Path(event.value.path())
            issued = list(csv.DictReader(io.StringIO(downloaded.read_bytes().decode('utf-8-sig'))))
            downloaded.unlink()
            expect(page.locator('#downloadBulkCredentials')).to_be_hidden()
            assert len(issued) == 3
            assert all(item['Geçici Parola'] not in page.content() for item in issued)
            page.get_by_role('link', name='Kullanıcı listesini yenile', exact=True).click()
            # 6. Select the former shared account and retire it with a reason.
            page.get_by_label(sample['user'].full_name + ' hesabını seç', exact=True).check()
            page.locator('#retireUsersReason').fill('Kişisel hesaplara geçildi; paylaşılan hesap kapatıldı.')
            screenshot('strategy-retirement.png')
            with page.expect_navigation():
                page.get_by_role('button', name='Seçilen hesapları pasifleştir', exact=True).click()
            db.refresh(sample['user']); assert not sample['user'].is_active
            assert db.scalar(select(AuditLog.id).where(AuditLog.action == 'user_deactivate', AuditLog.entity_id == sample['user'].id))
            # The new director logs in with their own temporary credential.
            page.get_by_role('button', name='Çıkış', exact=True).click()
            expect(page).to_have_url(base + '/login')
            assert page.locator('input[name="email"]').count(), page.locator('body').inner_text()
            page.locator('input[name="email"]').fill(issued[0]['E-posta'])
            page.locator('input[name="password"]').fill(issued[0]['Geçici Parola'])
            page.get_by_role('button', name='Giriş yap', exact=True).click()
            expect(page).to_have_url(base + '/change-password')
            expect(page.get_by_text('Devam etmek için kendi parolanızı belirleyin.', exact=True)).to_be_visible()
            screenshot('personal-first-login.png')
            page.goto(base + '/dashboard')
            expect(page).to_have_url(base + '/change-password')
            personal = secrets.token_urlsafe(20)
            page.locator('#firstCurrentPassword').fill(issued[0]['Geçici Parola'])
            page.locator('#firstNewPassword').fill(personal)
            page.locator('#firstConfirmPassword').fill(personal)
            page.get_by_role('button', name='Parolamı belirle ve devam et', exact=True).click()
            expect(page).to_have_url(base + '/modules')
            target = db.scalar(select(User).where(User.email == issued[0]['E-posta']))
            assert not target.must_change_password
            assert not errors
