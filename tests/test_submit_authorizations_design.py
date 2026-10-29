"""CIV-119: frozen row contract, real HTTP controls and synthetic evidence."""
from hashlib import sha256
import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from html.parser import HTMLParser
from playwright.sync_api import expect

from app.models import User
from test_released_permissions import actors, http
from test_section_index_design import TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/submit_authorizations_start.html'


@pytest.fixture
def staff(db, actors):
    actors['staff'].full_name = 'Ada Sentetik'
    actors['authorized'].full_name = 'Bora Sentetik'
    inactive = User(email='inactive@example.invalid', full_name='Ceren Sentetik uzun personel adı',
        role='department', position='staff', department_id=actors['staff'].department_id,
        password_hash='unused', is_active=False, can_submit=False)
    db.add(inactive)
    db.commit()
    return [actors['staff'], actors['authorized'], inactive]


class Rows(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.rows = []
        self.row = None
        self.control = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr':
            self.row = []
        if self.row is not None and (tag == 'button' or
                (tag == 'span' and 'status' in attrs.get('class', '').split())):
            self.control = [tag, sorted(attrs.items()), '']

    def handle_data(self, data):
        if self.control is not None:
            self.control[2] += data

    def handle_endtag(self, tag):
        if self.control is not None and tag == self.control[0]:
            self.row.append(self.control)
            self.control = None
        if tag == 'tr' and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None


def row_contract(html):
    return Rows(html).rows


def test_frozen_rows_and_summary(http, staff):
    response = http('director').get('/submit-authorizations')
    assert response.status_code == 200
    source = FROZEN.read_bytes()
    assert sha256(source).hexdigest() == 'be49aca4526e1aa7299c0f64f1e69d9dc2c008ae5b0c046a26f43a82ca565b9a'
    old = response.template.environment.from_string(source.decode()).render(response.context)
    assert row_contract(response.text) == row_contract(old)
    assert len(row_contract(response.text)) == len(staff)
    for user in staff:
        assert user.full_name in response.text
        assert user.email in response.text
    assert 'Etkin' in response.text and 'Devre dışı' in response.text
    assert '3 personel · 1 yetkili · 2 yetkisiz' in response.text
    assert 'submit-authorizations.css' not in http('director').get('/dashboard').text


@pytest.mark.parametrize('actor', ['staff', 'authorized', 'strategy_staff', 'strategy_director'])
def test_same_non_director_403(http, actor):
    response = http(actor).get('/submit-authorizations')
    assert response.status_code == 403
    assert response.json()['detail'] == 'Gönderim Yetkileri ekranını yalnızca müdürlüğün Müdürü açabilir. Yetki için Müdürünüze başvurun.'


@pytest.mark.parametrize('empty', [False, True])
@pytest.mark.parametrize('width', [1440, 390])
def test_browser_layout_contrast_and_toggle(browser, http, db, staff, width, empty):
    if empty:
        for user in staff:
            user.department_id = None
        db.commit()
    client = http('director')
    writes, errors = [], []
    with browser.new_context(viewport={'width': width, 'height': 1000}) as context:
        def serve(route):
            request = route.request
            if request.method != 'GET':
                writes.append((request.method, urlsplit(request.url).path, request.post_data_json))
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type': request.headers.get('content-type', '')}, follow_redirects=False)
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver/submit-authorizations')
        page.evaluate('document.fonts.ready')
        root = page.locator('.submit-authorizations-page')
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
        if empty:
            expect(root.locator('.authorization-summary')).to_have_text('0 personel · 0 yetkili · 0 yetkisiz')
            expect(root.locator('tbody tr')).to_have_count(0)
            expect(root.locator('.empty-state')).to_have_text('Müdürlüğünüzde Personel hesabı yok. Hesap oluşturulması için Strateji birimine başvurun.')
        elif width == 390:
            expect(root.locator('.scroll-hint')).to_be_visible()
            wrap = root.locator('.table-wrap')
            assert wrap.evaluate('el => el.scrollWidth > el.clientWidth')
            wrap.focus()
            page.keyboard.press('ArrowRight')
            wrap.evaluate('el => el.scrollLeft = el.scrollWidth')
            assert wrap.evaluate('el => el.scrollLeft > 0')
        script = TEXT_PAIRS.replace('.section-index-page', '.submit-authorizations-page')
        pairs = set(map(tuple, page.evaluate(script)))
        for control in root.locator('button, [tabindex]').all():
            control.hover()
            control.focus()
            pairs.update(map(tuple, page.evaluate(script)))
        assert all(contrast(pair) >= 4.5 for pair in pairs), [(p, contrast(p)) for p in pairs if contrast(p) < 4.5]
        def colors(button):
            return button.evaluate("""el => {
                const style = getComputedStyle(el);
                const token = (property, name) => {
                    const probe = document.createElement('span');
                    probe.style[property] = `var(${name})`;
                    document.body.append(probe);
                    const value = getComputedStyle(probe)[property];
                    probe.remove();
                    return value;
                };
                return {
                    color: style.color,
                    background: style.backgroundColor,
                    border: style.borderColor,
                    success: token('color', '--success'),
                    successBackground: token('backgroundColor', '--success-bg'),
                    defaultColor: token('color', '--text'),
                    defaultBackground: token('backgroundColor', '--surface'),
                    defaultBorder: token('borderColor', '--text-secondary')
                };
            }""")

        if not empty:
            authorized = root.locator(f'button[data-user="{staff[1].id}"]')
            unauthorized = root.locator(f'button[data-user="{staff[0].id}"]')
            authorized_colors = colors(authorized)
            assert authorized_colors['color'] == authorized_colors['success']
            assert authorized_colors['background'] == authorized_colors['successBackground']
            unauthorized_colors = colors(unauthorized)
            assert unauthorized_colors['color'] == unauthorized_colors['defaultColor']
            assert unauthorized_colors['background'] == unauthorized_colors['defaultBackground']
            assert unauthorized_colors['border'] == unauthorized_colors['defaultBorder']

        folder = os.getenv('CIVENSA_CIV149_SCREENSHOTS')
        if folder:
            target = Path(folder)
            target.mkdir(parents=True, exist_ok=True)
            page.evaluate('document.activeElement.blur()')
            page.mouse.move(0, 0)
            if not empty and width == 390:
                root.locator('.table-wrap').evaluate('el => el.scrollLeft = 0')
            if not empty:
                page.screenshot(path=str(target / f'submit-authorizations-{width}.png'), full_page=True)
        if not empty:
            button = root.locator(f'button[data-user="{staff[0].id}"]')
            expect(button).to_have_text('Yetki ver')
            button.click()
            expect(button).to_have_attribute('data-authorized', '1')
            expect(button).to_have_text('Yetkiyi kaldır')
            toggled_colors = colors(button)
            assert toggled_colors['color'] == toggled_colors['success']
            assert toggled_colors['background'] == toggled_colors['successBackground']
            expect(button.locator('..').locator('.status')).to_have_count(0)
            expect(root.locator('.authorization-summary')).to_have_text('3 personel · 2 yetkili · 1 yetkisiz')
            button.click()
            expect(button).to_have_attribute('data-authorized', '0')
            reverted_colors = colors(button)
            assert reverted_colors['color'] == reverted_colors['defaultColor']
            assert reverted_colors['background'] == reverted_colors['defaultBackground']
            assert reverted_colors['border'] == reverted_colors['defaultBorder']
            expect(button.locator('..').locator('.status')).to_have_count(0)
            assert writes == [('POST', f'/api/users/{staff[0].id}/submit-authorization', {'can_submit': True}),
                              ('POST', f'/api/users/{staff[0].id}/submit-authorization', {'can_submit': False})]
        assert not errors
