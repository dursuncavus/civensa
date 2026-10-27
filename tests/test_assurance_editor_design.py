"""CIV-125: frozen form/legal contract and real-session browser acceptance."""
import hashlib
import os
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
from starlette.requests import Request
from playwright.sync_api import sync_playwright, expect
from app.main import templates
from app import assurance_service as service
from test_activity_sections import section_client, login
from test_assurance_helpers import variables, put

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / 'tests/fixtures/assurance_editor_before_civ125.html'


class Contract(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.forms, self.controls, self.links, self.rows = [], [], [], 0
        self.textarea = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.forms.append({key: attrs.get(key) for key in ('method', 'action')})
        if tag in ('input', 'textarea', 'button'):
            self.controls.append((tag, attrs, ''))
            if tag == 'textarea':
                self.textarea = len(self.controls) - 1
        if tag == 'a' and '?code=EKLER' in attrs.get('href', ''):
            self.links.append(attrs['href'])
        if tag == 'tr':
            self.rows += 1

    def handle_endtag(self, tag):
        if tag == 'textarea':
            self.textarea = None

    def handle_data(self, data):
        if self.textarea is not None:
            tag, attrs, value = self.controls[self.textarea]
            self.controls[self.textarea] = tag, attrs, value + data


def render_pair(code, editable, error, count):
    values = variables(two=True)
    values['signatories'] = (values['signatories'] * 50)[:count]
    values['reservations'] = [{'text': 'Çekince <örnek> & kayıt\nİkinci satır',
                               'justification': 'Gerekçe "örnek"\nDevam'} for _ in range(count)]
    item = dict(code=code, variables=values, version_id=None, file_sha256=None)
    request = Request({'type': 'http', 'scheme': 'http', 'server': ('testserver', 80),
                       'path': '/activity-sections/reports/7/assurances/' + code,
                       'headers': [], 'session': {'csrf_token': 'synthetic-csrf'}})
    ctx = dict(request=request, user={'role': 'strategy', 'full_name': 'Örnek Kullanıcı'},
               report=dict(id=7, year=2027, department='Örnek Müdürlüğü', revision=42),
               item=item, variables=values, editable=editable,
               statement=service.view(item), form_error=error)
    return (templates.env.from_string(FROZEN.read_text()).render(**ctx),
            templates.env.get_template('assurance_editor.html').render(**ctx))


@pytest.mark.parametrize('code', ['EK-1', 'EK-2', 'EK-3'])
@pytest.mark.parametrize('editable', [False, True])
@pytest.mark.parametrize('error', ['', 'Rapor sürümü geçersiz. Sayfayı yenileyip yeniden kaydedin.'])
@pytest.mark.parametrize('count', [0, 2, 99, 100])
def test_frozen_form_and_byte_identical_statement(code, editable, error, count):
    assert hashlib.sha256(FROZEN.read_bytes()).hexdigest() == '601104fbdeb21a49e86d789b70f845b0cdf49469d5ee0db013dc85f46b90fd8c'
    before, after = render_pair(code, editable, error, count)
    original, current = Contract(before), Contract(after)
    assert current.forms == original.forms
    assert current.controls == original.controls
    assert current.rows == original.rows
    assert current.links == original.links
    pattern = r'<div aria-label="Kilitli beyan metni">.*?</div>'
    assert re.search(pattern, after, re.S)[0].encode() == re.search(pattern, before, re.S)[0].encode()
    if not editable:
        assert 'Beyan alanlarını kaydet' not in after
        assert 'Bu beyan salt okunurdur.' in after
    if error:
        assert error + ' Girdiğiniz alanlar aşağıda korunmuştur.' in after


def luminance(rgb):
    channels = [float(v) / 255 for v in re.findall(r'[\d.]+', rgb)[:3]]
    return sum(weight * (v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4)
               for weight, v in zip((.2126, .7152, .0722), channels))


def assert_layout(page, width):
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    if page.locator('.ar-scroll').count():
        expect(page.locator('.assurance-scroll-hint')).to_be_visible()
        if width == 390:
            assert page.locator('.ar-scroll').evaluate('(e) => e.scrollWidth > e.clientWidth')
            page.locator('.ar-scroll').focus()
            page.keyboard.press('ArrowRight')
            page.wait_for_timeout(150)
            assert page.locator('.ar-scroll').evaluate('(e) => e.scrollLeft > 0')
            page.locator('.ar-scroll').evaluate('(e) => { e.scrollLeft = 0; }')
        if width >= 1024:
            boxes = [page.locator(f'[name={field}]').bounding_box() for field in ('place', 'date')]
            assert boxes[0]['y'] == boxes[1]['y']
    # Check the computed colours of every visible text node on the editor,
    # resolving the actual solid background through its ancestors.
    colours = page.locator('.assurance-editor-page').evaluate('''root => {
      const result = [];
      for (const el of [root, ...root.querySelectorAll('*')]) {
        const style = getComputedStyle(el);
        if (!el.getClientRects().length || style.visibility === 'hidden') continue;
        const text = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
        if (!text && !el.matches('input:not([type=hidden]),textarea')) continue;
        let bg = 'rgb(255, 255, 255)';
        for (let p = el; p; p = p.parentElement) {
          const colour = getComputedStyle(p).backgroundColor;
          if (colour !== 'rgba(0, 0, 0, 0)' && colour !== 'transparent') { bg = colour; break; }
        }
        result.push([style.color, bg]);
      }
      return result;
    }''')
    assert colours
    for fg, bg in colours:
        low, high = sorted((luminance(fg), luminance(bg)))
        assert (high + .05) / (low + .05) >= 4.5, (fg, bg)
    doc = page.locator('.assurance-document')
    assert doc.evaluate('(e) => e.clientWidth <= 72 * parseFloat(getComputedStyle(e).fontSize)')


@pytest.mark.postgres
@pytest.mark.parametrize('width', [1440, 390])
def test_browser_save_error_readonly_and_evidence(section_client, sample, width, tmp_path):
    client, docs, _, _ = section_client
    folder = Path(os.getenv('CIVENSA_UI_SCREENSHOTS', str(tmp_path)))
    folder.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        options = {'headless': True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'):
            options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        browser = p.chromium.launch(**options)
        context = browser.new_context(viewport={'width': width, 'height': 1060}, locale='tr-TR')
        def serve(route):
            req = route.request
            response = client.request(req.method, req.url, content=req.post_data_buffer,
                                      headers={'content-type': req.headers.get('content-type', '')},
                                      follow_redirects=True)
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        def capture(name):
            page.evaluate('document.fonts.ready')
            assert_layout(page, width)
            path = folder / f'{name}-{width}.png'
            page.screenshot(path=str(path), full_page=True)
            assert path.stat().st_size <= 1_500_000
        doc = docs['idare']
        login(client, 'strategy@example.invalid')
        url = f'http://testserver/activity-sections/reports/{doc.id}/assurances/EK-1'
        page.goto(url)
        page.locator('[name=place]').fill('Ankara')
        page.locator('[name=date]').fill('2028-02-15')
        for key, value in variables()['signatories'][0].items():
            page.locator(f'[name={key}_0]').fill(value)
        page.locator('[name=reservation_text_0]').fill('Örnek envanter kaydı eksik')
        page.get_by_role('button', name='Beyan alanlarını kaydet').click()
        expect(page.locator('.assurance-editor-page [role=alert]')).to_contain_text('Girdiğiniz alanlar aşağıda korunmuştur.')
        expect(page.locator('[name=place]')).to_have_value('Ankara')
        expect(page.locator('[name=date]')).to_have_value('2028-02-15')
        for key, value in variables()['signatories'][0].items():
            expect(page.locator(f'[name={key}_0]')).to_have_value(value)
        expect(page.locator('[name=reservation_text_0]')).to_have_value('Örnek envanter kaydı eksik')
        capture('error')
        page.locator('[name=reservation_justification_0]').fill('Örnek arşiv araştırması sürüyor.')
        page.get_by_role('button', name='Beyan alanlarını kaydet').click()
        expect(page.locator('.assurance-editor-page [role=alert]')).to_have_count(0)
        expect(page.locator('.assurance-document')).to_contain_text('Örnek arşiv araştırması sürüyor.')
        capture('ek1-editable')
        token = login(client, 'finance@example.invalid')
        assert put(client, token, doc, 'EK-3').status_code == 200
        page.goto(url.replace('EK-1', 'EK-3'))
        expect(page.get_by_role('button', name='Beyan alanlarını kaydet')).to_be_visible()
        capture('ek3-editable')
        login(client, 'strategy@example.invalid')
        page.reload()
        expect(page.locator('.assurance-readonly')).to_have_text('Bu beyan salt okunurdur.')
        expect(page.get_by_role('button', name='Beyan alanlarını kaydet')).to_have_count(0)
        capture('readonly')
        # Also exercise screen 014 through the actual department permission.
        login(client, 'test@example.invalid')
        unit = docs[f"birim:{sample['department'].id}"]
        page.goto(f'http://testserver/activity-sections/reports/{unit.id}/assurances/EK-2')
        assert_layout(page, width)
        context.close()
        browser.close()
