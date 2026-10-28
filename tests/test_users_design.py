"""CIV-130: frozen users contract and real-route synthetic browser checks."""
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect

from app.models import Department, User
from test_section_index_design import TEXT_PAIRS, contrast
from test_sidebar_ui import browser
from tests.test_users_personal_accounts import accounts

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/users_start.html'

# personal_accounts.js: the first two IIFEs bind these users-page controls.
# Its firstPasswordForm/firstCurrentPassword/firstNewPassword/
# firstConfirmPassword/firstPasswordError belong to /change-password only.
# app.js additionally binds creation, position, activation and password reset;
# the included submit_authorization_control.html binds the last class/data attr.
JS_IDS = {
    'bulkUserFile', 'previewBulkUsers', 'applyBulkUsers', 'downloadBulkCredentials',
    'bulkUserResult', 'newUserBtn', 'newUserForm', 'userName', 'userEmail',
    'userRole', 'departmentLabel', 'userDepartment', 'userPosition', 'userPassword',
    'saveUser', 'cancelUser', 'accountChangePolicy', 'retireUsersReason',
    'retireSelectedUsers', 'retireUsersResult',
}
JS_CLASSES = {
    'create-department-user', 'retire-user', 'user-position', 'save-user-position',
    'toggle-user-active', 'show-password-reset', 'password-reset',
    'save-password-reset', 'toggle-submit-authorization',
}
JS_DATA = {'data-create-department', 'data-active', 'data-reset-user', 'data-user',
           'data-authorized'}
TEXT_CHANGES = {'Kullanıcı Ekle': 'Kullanıcı ekle', 'Ad Soyad': 'Ad soyad',
                'Geçici Parola': 'Geçici parola'}


class Contract(HTMLParser):
    """Preserve all control attrs, JS hooks, option texts, headers and copy.

    Only presentation classes/styles and the three permitted non-header labels
    differ. Missing-department names move outside their button; all page words
    are still compared as a multiset, allowing that presentation change.
    """
    def __init__(self, html):
        super().__init__()
        self.main = False
        self.controls, self.hooks, self.headers, self.options = [], [], [], []
        self.words = Counter()
        self.capture = None
        self.summary_depth = 0
        self.summary_parts = []
        self.summary = ''
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get('class', '').split())
        if tag == 'main':
            self.main = True
        if not self.main:
            return
        if self.summary_depth:
            self.summary_depth += 1
        elif 'users-summary' in classes or {'cards', 'strategy-cards'} <= classes:
            self.summary_depth = 1
        if tag in {'input', 'select', 'option', 'textarea', 'button', 'a', 'form'}:
            values = {k: v for k, v in attrs.items() if k not in {'class', 'style'}}
            if values.get('name') == 'csrf_token':
                values['value'] = '<csrf>'
            self.controls.append((tag, tuple(sorted(values.items()))))
        classes = tuple(sorted(classes & JS_CLASSES))
        data = tuple(sorted((k, v) for k, v in attrs.items() if k.startswith('data-')))
        if attrs.get('id') or classes or data:
            self.hooks.append((tag, attrs.get('id'), classes, data, 'hidden' in attrs))
        if tag in {'th', 'option'}:
            self.capture = [tag, tuple(sorted(attrs.items())), '']

    def handle_data(self, data):
        if not self.main:
            return
        if self.capture is not None:
            self.capture[2] += data
        if self.capture and self.capture[0] == 'th':
            return
        if self.summary_depth:
            self.summary_parts.append(data)
            return
        # Header copy is deliberately NOT sentence-cased.
        text = ' '.join(data.split())
        text = TEXT_CHANGES.get(text, text)
        text = text.replace('Kullanıcılar ve Yetkiler', 'Kullanıcılar ve yetkiler')
        self.words.update(text.split())

    def handle_endtag(self, tag):
        if self.capture and self.capture[0] == tag:
            kind, attrs, text = self.capture
            value = (attrs, ' '.join(text.split()))
            (self.headers if kind == 'th' else self.options).append(value)
            self.capture = None
        if self.summary_depth:
            self.summary_depth -= 1
            if not self.summary_depth:
                self.summary = ' '.join(' '.join(self.summary_parts).split())
        if tag == 'main':
            self.main = False


def normalized_summary(summary):
    match = re.fullmatch(
        r'Müdürlük (\d+) Etkin müdürlük hesabı (\d+) Hesap bekliyor (\d+)', summary)
    if not match:
        return summary
    departments, accounts, missing = match.groups()
    return (f'{departments} müdürlük · {accounts} etkin müdürlük hesabı · '
            f'{missing} hesap bekliyor')


def normalized_headers(headers):
    combined = {'Ad Soyad', 'E-posta', 'Rol'}
    result = [header for header in headers if header[1] not in combined]
    index = next((i for i, header in enumerate(headers) if header[1] in combined), None)
    if index is not None:
        result.insert(sum(header[1] not in combined for header in headers[:index]),
                      ((), 'Kullanıcı'))
    return result


@pytest.fixture
def users_data(db, sample, accounts):
    sample['strategy'].full_name = 'Derya Sentetik'
    sample['user'].full_name = 'Ada Sentetik'
    missing = [Department(organization_id=sample['department'].organization_id,
        name=name) for name in ['Bilgi İşlem Müdürlüğü',
                               'Uzun adlı sentetik Kültür ve Sosyal İşler Müdürlüğü']]
    db.add_all(missing)
    db.add_all([
        User(email='test.layout@example.invalid', full_name='Bora Sentetik',
             role='department', position='staff', can_submit=False,
             department_id=sample['strategy'].department_id, password_hash='unused'),
        User(email='test.longer.layout@example.invalid', full_name='Ceren Sentetik devre dışı hesap',
             role='department', position='staff', is_active=False, can_submit=False,
             department_id=sample['department'].id, password_hash='unused'),
        User(email='deniz@example.invalid', full_name='Deniz Sentetik',
             role='department', position='director',
             department_id=sample['department'].id, password_hash='unused'),
        User(email='ekin@example.invalid', full_name='Ekin Sentetik',
             role='strategy', position='staff', password_hash='unused'),
    ])
    db.commit()
    return missing


@pytest.mark.parametrize('missing', [True, False])
def test_frozen_controls_hooks_copy_options_and_headers(accounts, users_data, db, sample, missing):
    if not missing:
        for department in users_data:
            department.is_active = False
        db.commit()
    client = accounts[0]()
    response = client.get('/users')
    assert response.status_code == 200
    source = FROZEN.read_bytes()
    assert sha256(source).hexdigest() == '53e0086d52cc338dbd8603a87afa0bee1ea11ea19c46b7791c8ff2e83105c924'
    old = response.template.environment.from_string(source.decode()).render(response.context)
    actual, expected = Contract(response.text), Contract(old)
    assert Counter(actual.controls) == Counter(expected.controls)
    assert Counter(actual.hooks) == Counter(expected.hooks)
    assert actual.options == expected.options
    assert actual.headers == normalized_headers(expected.headers)
    assert actual.summary == normalized_summary(expected.summary)
    assert actual.words == expected.words - Counter({'Yetkili': expected.words['Yetkili'], 'Yetkisiz': expected.words['Yetkisiz']})
    assert 'Yetkili' not in actual.words and 'Yetkisiz' not in actual.words
    soup_buttons = re.findall(r'<button[^>]*toggle-submit-authorization[^>]*>', response.text)
    assert soup_buttons
    for tag in soup_buttons:
        assert ('authorized' in re.search(r'class="([^"]*)"', tag).group(1).split()) == ('data-authorized="1"' in tag)
    assert JS_IDS <= {item[1] for item in actual.hooks}
    assert JS_CLASSES - ({'create-department-user'} if not missing else set()) <= {
        name for _, _, classes, _, _ in actual.hooks for name in classes}
    assert JS_DATA - ({'data-create-department'} if not missing else set()) <= {
        name for _, _, _, data, _ in actual.hooks for name, _ in data}
    assert bool(response.context['missing_departments']) == missing
    assert 'users.css' not in client.get('/dashboard').text
    assert len(response.context['users']) == 6
    assert sample['strategy'].id in [u.id for u in response.context['users']]
    assert any(not u.is_active for u in response.context['users'])
    assert any(u.can_submit for u in response.context['users'])


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('phase', ['before', 'after'])
@pytest.mark.parametrize('missing', [True, False])
def test_browser_layout_contrast_and_existing_controls(browser, accounts, users_data, db, width, phase, missing):
    if not missing:
        for department in users_data:
            department.is_active = False
        db.commit()
    client = accounts[0]()
    summary_context = client.get('/users').context
    errors, writes = [], []
    with browser.new_context(viewport={'width': width, 'height': 1000},
                             locale='tr-TR', timezone_id='Europe/Istanbul') as context:
        def serve(route):
            request = route.request
            path = urlsplit(request.url).path
            if request.method != 'GET':
                writes.append((request.method, path, request.post_data_json))
            response = client.request(request.method, request.url,
                content=request.post_data_buffer,
                headers={'content-type': request.headers.get('content-type', ''),
                         'X-CSRF-Token': request.headers.get('x-csrf-token', '')},
                follow_redirects=False)
            body = response.content
            if phase == 'before' and path == '/users':
                body = response.template.environment.from_string(FROZEN.read_text()).render(response.context).encode()
            headers = {k: v for k, v in response.headers.items()
                       if k not in {'set-cookie', 'content-length'}}
            route.fulfill(status=response.status_code, headers=headers, body=body)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver/users')
        page.evaluate('document.fonts.ready')
        if missing:
            page.locator('details summary').click()
        else:
            expect(page.locator('main details')).to_have_count(0)
        page.locator('#newUserBtn').click()
        expect(page.locator('#newUserForm')).to_be_visible()
        expect(page.locator('#userName')).to_be_focused()
        row = page.locator('tr[data-user]').filter(has_text='Ada Sentetik')
        folder = os.getenv('CIVENSA_CIV130_SCREENSHOTS')
        if phase == 'after' and width == 1440:
            assert page.locator('.users-table th').evaluate_all("""headers => headers.every(header => {
              const range = document.createRange();
              range.selectNodeContents(header);
              return new Set([...range.getClientRects()].map(rect => Math.round(rect.top))).size === 1;
            })""")
            assert page.locator('.users-table select.user-position').evaluate_all("""selects => selects.every(select => {
              const option = select.selectedOptions[0];
              const style = getComputedStyle(select);
              const canvas = document.createElement('canvas');
              const context = canvas.getContext('2d');
              context.font = style.font;
              const textWidth = context.measureText(option.textContent.trim()).width;
              const arrowWidth = parseFloat(style.fontSize) + 2;
              const padding = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
              return select.clientWidth >= Math.ceil(textWidth + arrowWidth + padding);
            })""")
            assert page.locator('.users-table td:nth-child(3)').evaluate_all("""cells => {
              const cell = cells.find(cell => cell.textContent.includes('Strateji Geliştirme Müdürlüğü'));
              if (!cell) return false;
              const range = document.createRange();
              range.selectNodeContents(cell);
              return new Set([...range.getClientRects()].map(rect => Math.round(rect.top))).size <= 2;
            }""")
            assert page.locator('.users-table tbody tr').evaluate_all("""rows => {
              const unwrapped = rows.filter(row => {
                const identity = row.querySelector('.user-identity');
                return [...identity.querySelectorAll('b, .user-email')].every(el => {
                  const range = document.createRange();
                  range.selectNodeContents(el);
                  return new Set([...range.getClientRects()].map(rect => Math.round(rect.top))).size <= 1;
                });
              });
              return new Set(unwrapped.map(row => Math.round(row.getBoundingClientRect().height))).size <= 1;
            }""") or width == 1440
            button_layout = page.locator('.users-table .button.small').evaluate_all("""buttons => {
              const heights = buttons.filter(button => button.getClientRects().length)
                .map(button => button.getBoundingClientRect().height);
              const paddings = buttons.map(button => getComputedStyle(button).padding);
              const lines = buttons.map(button => {
                const range = document.createRange();
                range.selectNodeContents(button);
                return new Set([...range.getClientRects()].map(rect => Math.round(rect.top))).size <= 1;
              });
              return {heights, paddings, lines};
            }""")
            assert (len(set(button_layout['heights'])) == 1 and
                    len(set(button_layout['paddings'])) == 1 and
                    all(button_layout['lines'])), button_layout
            alignment = page.locator('.users-table tbody tr').evaluate_all("""rows => {
              const pairs = rows.flatMap(row => {
                const active = row.querySelector('.toggle-user-active');
                const activeBadge = row.querySelector('td:last-child .status');
                return [[activeBadge, active]].filter(([badge, action]) => badge && action);
              });
              return pairs.map(([badge, action]) => [
                badge.getBoundingClientRect().top + badge.getBoundingClientRect().height / 2,
                action.getBoundingClientRect().top + action.getBoundingClientRect().height / 2
              ]);
            }""")
            assert all(abs(badge_top - action_top) <= 2 or action_top > badge_top
                       for badge_top, action_top in alignment), alignment
            assert page.locator('.users-table td:nth-child(5) .status').count() == 0
            assert page.locator('.users-table td:last-child').evaluate_all(
                "cells => cells.every(c => c.getBoundingClientRect().right <= c.closest('.table-wrap').getBoundingClientRect().right + 1)") or width == 390
        if folder and phase == 'after' and missing and width == 1440:
            target = Path(folder)
            target.mkdir(parents=True, exist_ok=True)
            page.evaluate('document.activeElement.blur()')
            page.mouse.move(0, 0)
            page.evaluate('scrollTo(0, 0)')
            page.screenshot(path=str(target / 'users-after-1440.png'), full_page=True)
        row.locator('.show-password-reset').click()
        expect(row.locator('.password-reset')).to_be_visible()
        expect(row.locator('.password-reset input')).to_be_focused()
        assert not page.locator('input[type=password]').evaluate_all('els => els.some(el => el.value)')
        if phase == 'after':
            root = page.locator('.users-page')
            assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
            expect(page.locator('.users-table th')).to_have_count(6)
            assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
            summary = root.locator('.users-summary')
            assert summary.evaluate('el => el.getBoundingClientRect().width <= 704')
            expect(summary).to_have_text(
                f'{len(summary_context["departments"])} müdürlük · '
                f'{summary_context["department_account_count"]} etkin müdürlük hesabı · '
                f'{len(summary_context["missing_departments"])} hesap bekliyor')
            expect(summary.locator('.status.warning')).to_have_count(
                1 if summary_context['missing_departments'] else 0)
            if summary_context['missing_departments']:
                expect(summary.locator('.status.warning')).to_have_text(
                    f'{len(summary_context["missing_departments"])} hesap bekliyor')
            if missing:
                assert root.locator('.missing-departments').evaluate('el => el.getBoundingClientRect().width <= 704')
            columns = page.locator('#newUserForm').evaluate('el => getComputedStyle(el).gridTemplateColumns.split(" ").length')
            assert columns == (3 if width >= 1024 else 1)
            if width == 1440:
                overflow = page.locator('.users-table td').evaluate_all("""cells => cells.flatMap(cell => {
                  const paddingRight = parseFloat(getComputedStyle(cell).paddingRight);
                  const right = cell.getBoundingClientRect().right - paddingRight + 1;
                  return [...cell.querySelectorAll('*')].filter(el => el.getClientRects().length &&
                    !el.classList.contains('sr-only') && el.getBoundingClientRect().right > right)
                    .map(el => [cell.cellIndex, el.className, el.getBoundingClientRect().right, right]);
                })""")
                assert not overflow, overflow
                assert page.locator('.users-table .user-email').evaluate_all("""emails => emails.every(el => {
                  const text = el.textContent;
                  for (let index = 0; index < text.length - 1; index += 1) {
                    if (!/[a-z\\d]/i.test(text[index]) || !/[a-z\\d]/i.test(text[index + 1])) continue;
                    const first = document.createRange();
                    const second = document.createRange();
                    first.setStart(el.firstChild, index);
                    first.setEnd(el.firstChild, index + 1);
                    second.setStart(el.firstChild, index + 1);
                    second.setEnd(el.firstChild, index + 2);
                    if (Math.round(first.getBoundingClientRect().top) !==
                        Math.round(second.getBoundingClientRect().top)) return false;
                  }
                  return true;
                })""")
                assert page.locator('.users-table td').evaluate_all(
                    "cells => cells.every(cell => getComputedStyle(cell).verticalAlign === 'middle')")
                assert page.locator('.bulk-user-import .actions .button:not([hidden])').evaluate_all(
                    'els => new Set(els.map(el => el.getBoundingClientRect().top)).size === 1')
            expect(row.locator('td:last-child .status')).to_have_text('Etkin')
            inactive = page.locator('tr[data-user]').filter(has_text='Ceren Sentetik')
            expect(inactive.locator('td:last-child .status')).to_have_text('Devre dışı')
            assert inactive.locator('td:last-child .status').evaluate(
                'el => getComputedStyle(el).color === getComputedStyle(document.querySelector(".users-page .muted")).color')
            wrap = page.locator('.users-table')
            if width == 1440:
                assert wrap.evaluate('el => el.scrollWidth <= el.clientWidth')
            else:
                assert wrap.evaluate('el => el.scrollWidth > el.clientWidth')
                wrap.focus()
                page.keyboard.press('ArrowRight')
                assert wrap.evaluate('el => el.scrollLeft > 0')
            if width == 1440:
                assert page.locator('.users-table td:last-child .user-status-controls').evaluate_all("""controls => controls.every(el => {
                  const cell = el.closest('td');
                  const style = getComputedStyle(cell);
                  return el.getBoundingClientRect().right <=
                    cell.getBoundingClientRect().right - parseFloat(style.paddingRight) + 1;
                })""")
                assert row.locator('.password-reset').evaluate("""el => {
                  const input = el.querySelector('input').getBoundingClientRect();
                  const button = el.querySelector('button').getBoundingClientRect();
                  return Math.abs(input.top - button.top) <= 2 && input.right <= button.left + 1;
                }""")
                assert root.locator('.user-email').evaluate_all(
                    "els => els.every(el => getComputedStyle(el).overflowWrap === 'normal')")
                position_select = page.get_by_role('combobox', name='Bora Sentetik unvanı')
                expect(position_select).to_have_count(1)
                assert position_select.locator('xpath=..').locator('.sr-only').evaluate(
                    "el => getComputedStyle(el).clip === 'rect(0px, 0px, 0px, 0px)'")
                position_controls = position_select.locator('xpath=../..')
                assert position_controls.evaluate("""el => {
                  const select = el.querySelector('select').getBoundingClientRect();
                  const button = el.querySelector('button').getBoundingClientRect();
                  return Math.abs(select.top - button.top) <= 2 && select.right <= button.left + 1;
                }""")
            script = TEXT_PAIRS.replace('.section-index-page', '.users-page')
            pairs = set(map(tuple, page.evaluate(script)))
            selectors = ['#newUserBtn', '#previewBulkUsers', '#userName', '#userRole',
                             '.toggle-user-active',
                             '.toggle-submit-authorization', '#retireUsersReason']
            if missing:
                selectors.append('.create-department-user')
            for selector in selectors:
                control = page.locator(selector).first
                control.hover()
                control.focus()
                pairs.update(map(tuple, page.evaluate(script)))
            for control in root.locator('input[placeholder], textarea[placeholder]').all():
                pairs.add(tuple(control.evaluate('el => [getComputedStyle(el, "::placeholder").color, getComputedStyle(el).backgroundColor]')))
            assert all(contrast(p) >= 4.5 for p in pairs), [(p, contrast(p)) for p in pairs if contrast(p) < 4.5]
        if folder and missing:
            target = Path(folder)
            target.mkdir(parents=True, exist_ok=True)
            page.evaluate('document.activeElement.blur()')
            page.mouse.move(0, 0)
            page.locator('.table-wrap.section').evaluate('el => el.scrollLeft = 0')
            page.evaluate('scrollTo(0, 0)')
            screenshot_name = 'users-after-1440-password-open.png' if phase == 'after' and width == 1440 else f'users-{phase}-{width}.png'
            page.screenshot(path=str(target / screenshot_name), full_page=True)
            if width == 390:
                page.locator('.table-wrap.section').evaluate('el => el.scrollLeft = el.scrollWidth')
                page.screenshot(path=str(target / f'users-{phase}-status-390.png'), full_page=True)
        # Disclosure and form bindings keep operating after the visual migration.
        row.locator('.show-password-reset').click()
        expect(row.locator('.password-reset')).to_be_hidden()
        page.locator('#cancelUser').click()
        expect(page.locator('#newUserForm')).to_be_hidden()
        if missing:
            page.locator('.create-department-user').first.click()
            expect(page.locator('#userDepartment')).to_have_value(str(users_data[0].id))
        else:
            page.locator('#newUserBtn').click()
        page.locator('#userRole').select_option('strategy')
        expect(page.locator('#departmentLabel')).to_be_hidden()
        page.locator('#userRole').select_option('department')
        expect(page.locator('#departmentLabel')).to_be_visible()
        if phase == 'after':
            authorization = row.locator('.toggle-submit-authorization')
            authorization.click()
            expect(authorization).to_have_text('Yetki ver')
            authorization.click()
            expect(authorization).to_have_text('Yetkiyi kaldır')
            uid = row.get_attribute('data-user')
            assert writes == [('POST', f'/api/users/{uid}/submit-authorization', {'can_submit': False}),
                              ('POST', f'/api/users/{uid}/submit-authorization', {'can_submit': True})]
        assert not errors
