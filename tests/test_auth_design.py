"""CIV-102: contracts frozen from b8e063f before the presentation change."""
from html.parser import HTMLParser
import json
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from test_sidebar_ui import browser
from test_live_pilot_hardening import live_client, PASSWORD

pytestmark = pytest.mark.postgres


class Contract(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.rows = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag not in ('form', 'input'):
            return
        attrs = dict(attrs)
        self.rows.append([tag, {k: attrs[k] for k in (
            'name', 'id', 'type', 'autocomplete', 'required', 'minlength', 'method', 'action'
        ) if k in attrs}])


def assert_contract(html, name):
    frozen = json.loads((Path(__file__).parent / 'fixtures/auth_contract.json').read_text())
    actual = Contract(html).rows
    if name == 'login':
        # Login had no IDs on the base; only these label associations are added.
        assert [row[1].get('id') for row in actual if row[0] == 'input'] == ['loginEmail', 'loginPassword']
        for tag, attrs in actual:
            attrs.pop('id', None)
    assert actual == frozen[name]


def route_client(context, client, writes):
    def serve(route):
        req = route.request
        if req.method != 'GET':
            writes.append((req.method, req.url, req.post_data_json if 'application/json' in req.headers.get('content-type', '') else None))
        response = client.request(req.method, req.url, content=req.post_data_buffer,
            headers={k: v for k, v in req.headers.items() if k in ('content-type', 'x-csrf-token')},
            follow_redirects=False)
        headers = dict(response.headers)
        headers.pop('set-cookie', None)
        route.fulfill(status=response.status_code, headers=headers, body=response.content)
    context.route('http://testserver/**', serve)


def screenshot(page, name, width):
    folder = os.getenv('CIV102_SCREENSHOTS')
    if folder:
        Path(folder).mkdir(parents=True, exist_ok=True)
        page.evaluate('document.fonts.ready')
        if name.startswith('024-'):
            page.evaluate('window.scrollTo(0, 0)')
        page.screenshot(path=str(Path(folder) / f'{name}-{width}.png'),
                        full_page=not name.startswith('024-'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')


@pytest.mark.parametrize('width', [1440, 390])
def test_login_contract_error_and_keyboard(browser, live_client, width):
    client = live_client()
    assert_contract(client.get('/login').text, 'login')
    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        route_client(context, client, [])
        page = context.new_page()
        page.goto('http://testserver/login')
        screenshot(page, '032-login-empty', width)
        expect(page.get_by_label('E-posta', exact=True)).to_have_attribute('id', 'loginEmail')
        expect(page.get_by_label('Parola', exact=True)).to_have_attribute('id', 'loginPassword')
        assert page.locator('.auth-page').evaluate("el => getComputedStyle(el).backgroundImage") == 'none'
        assert page.locator('.auth-card').evaluate("el => getComputedStyle(el).boxShadow") == 'none'
        for target in ('#loginEmail', '#loginPassword', 'button[type=submit], form button'):
            page.keyboard.press('Tab')
            expect(page.locator(target)).to_be_focused()
        page.locator('#loginEmail').fill('unknown@example.invalid')
        page.locator('#loginPassword').fill('Invalid-synthetic-password')
        page.locator('form button').click()
        expect(page.get_by_role('alert')).to_have_text('Giriş formundaki e-posta veya parola doğrulanamadı. Bilgilerinizi kontrol edip yeniden giriş yapın.')
        expect(page.locator('#loginEmail')).to_have_value('unknown@example.invalid')
        screenshot(page, '032-login-error', width)


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('role', ['strategy', 'department'])
def test_first_password_contract_server_error_and_success(browser, live_client, db, sample, role, width):
    user = sample['strategy' if role == 'strategy' else 'user']
    user.must_change_password = True
    db.commit()
    client = live_client()
    response = client.post('/login', data={'email': user.email, 'password': PASSWORD})
    assert response.headers['location'] == '/change-password'
    html = client.get('/change-password').text
    assert_contract(html, 'change_password')
    assert 'name="csrf_token" value="None"' not in html
    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        writes = []
        route_client(context, client, writes)
        page = context.new_page()
        page.goto('http://testserver/change-password')
        token = page.locator('meta[name="csrf-token"]').get_attribute('content')
        assert token and token != 'None'
        expect(page.locator('input[name="csrf_token"]')).to_have_value(token)
        for label, target in [('Mevcut geçici parola', 'firstCurrentPassword'),
                              ('Yeni parola', 'firstNewPassword'),
                              ('Yeni parola tekrar', 'firstConfirmPassword')]:
            expect(page.get_by_label(label, exact=True)).to_have_attribute('id', target)
        expect(page.locator('#firstPasswordError')).to_be_hidden()
        prefix = '019' if role == 'strategy' else '020'
        screenshot(page, prefix + '-first-password-empty', width)
        targets = ['#firstCurrentPassword', '#firstNewPassword', '#firstConfirmPassword', '#firstPasswordForm button', 'form[action="/logout"] button']
        for target in targets:
            page.keyboard.press('Tab')
            expect(page.locator(target)).to_be_focused()
        page.locator('#firstCurrentPassword').fill('wrong-synthetic-password')
        page.locator('#firstNewPassword').fill('New-synthetic-password')
        page.locator('#firstConfirmPassword').fill('New-synthetic-password')
        page.locator('#firstPasswordForm button').click()
        expect(page.get_by_role('alert')).to_have_text('Mevcut parola hatalı.')
        assert writes == [('POST', 'http://testserver/api/me/change-password', {
            'current_password': 'wrong-synthetic-password', 'new_password': 'New-synthetic-password',
            'confirmation': 'New-synthetic-password'})]
        screenshot(page, prefix + '-first-password-error', width)
        page.locator('#firstCurrentPassword').fill(PASSWORD)
        page.locator('#firstPasswordForm button').click()
        page.wait_for_url('http://testserver/modules', wait_until='networkidle')
        db.refresh(user)
        assert not user.must_change_password


@pytest.mark.parametrize('width', [1440, 390])
def test_password_dialog_keyboard_help_and_focus(browser, live_client, sample, width):
    client = live_client()
    client.post('/login', data={'email': sample['user'].email, 'password': PASSWORD})
    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        route_client(context, client, [])
        page = context.new_page()
        page.goto('http://testserver/department/1?period_id=1')
        opener = page.locator('#changePasswordButton')
        opener.focus()
        page.keyboard.press('Enter')
        dialog = page.get_by_role('dialog')
        expect(dialog).to_be_visible()
        expect(page.locator('#passwordHelp')).to_have_text('Yeni parolanız en az 12 karakter olmalıdır.')
        expect(page.locator('#currentPassword')).to_be_focused()
        screenshot(page, '024-password-dialog', width)
        for target in ('#newPassword', '#confirmPassword', '#cancelPasswordChange', '#savePasswordChange', '#currentPassword'):
            page.keyboard.press('Tab')
            expect(page.locator(target)).to_be_focused()
        page.keyboard.press('Shift+Tab')
        expect(page.locator('#savePasswordChange')).to_be_focused()
        page.keyboard.press('Escape')
        expect(dialog).to_be_hidden()
        expect(opener).to_be_focused()
        page.keyboard.press('Enter')
        page.locator('#cancelPasswordChange').click()
        expect(dialog).to_be_hidden()
        expect(opener).to_be_focused()
