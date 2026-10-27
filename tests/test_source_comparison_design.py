"""CIV-120: frozen comparison contract and synthetic accessible filter evidence."""
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect

from app.main import app, require_user
from test_section_index_design import TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/source_comparison_start.html'
STATUSES = ['Eşleşiyor', 'Kararla değişti', 'Fark var', 'Kaynakta yok', 'Kayıtta yok']


class ComparisonContract(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.rows, self.links, self.notices, self.ids = [], [], [], []
        self.in_table = False
        self.row = self.cell = self.notice = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a': self.links.append(attrs['href'])
        if tag == 'table' and attrs.get('id') == 'source-comparison':
            self.in_table = True
            self.ids.append(attrs['id'])
        if self.in_table and tag == 'tr':
            self.row = [attrs.get('data-status'), attrs.get('data-model'), []]
        if self.in_table and tag == 'td': self.cell = []
        if tag == 'p' and 'return-note' in attrs.get('class', '').split(): self.notice = []

    def handle_data(self, data):
        if self.cell is not None: self.cell.extend(data.split())
        if self.notice is not None: self.notice.extend(data.split())

    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None:
            self.row[2].append(' '.join(self.cell))
            self.cell = None
        if tag == 'tr' and self.row is not None:
            if self.row[2]: self.rows.append(self.row)
            self.row = None
        if tag == 'table': self.in_table = False
        if tag == 'p' and self.notice is not None:
            self.notices.append(' '.join(self.notice))
            self.notice = None


@pytest.fixture(params=['strategy', 'department'])
def comparison_response(client, sample, request):
    app.dependency_overrides[require_user] = lambda: sample['strategy' if request.param == 'strategy' else 'user']
    return client.get('/source-comparison', params={'period_id': sample['period'].id,
                                                 'department_id': sample['department'].id})


def synthetic_context(response, empty=False):
    rows = [dict(status=status, model=model, department='Sentetik müdürlük',
                 record='Sentetik kayıt ' + 'UzunAd' * 12, year=2027, kind='Bütçe', funding='Toplam',
                 document='Sentetik kaynak.docx', batch_id=12, document_sha256='a' * 64,
                 table=2, row=i + 1, column=3, page='Bilinmiyor', source_amount='1.234,50',
                 stored_amount='1.244,50', difference='10,00', raw_text='1.234,50',
                 decision='Sentetik karar gerekçesi.' if status == 'Kararla değişti' else '',
                 note='Sentetik kayıt açıklaması.')
            for i, (status, model) in enumerate(zip(STATUSES + ['Fark var'],
                ['activity', 'indicator', 'total', 'economic', 'personnel', 'activity']))]
    return dict(response.context, comparison={'rows': [] if empty else rows,
                'notices': ['Sentetik kaynak uyarısı.']})


def assert_contract(response, context):
    assert response.status_code == 200
    source = FROZEN.read_bytes()
    assert sha256(source).hexdigest() == '7f7f56e95ecfc07de38e8feeb79db8f6b53d5cfcc9c4fd259e33beecebc7635d'
    old = response.template.environment.from_string(source.decode()).render(context)
    actual = response.template.render(context)
    before, after = ComparisonContract(old), ComparisonContract(actual)
    assert after.ids == before.ids == ['source-comparison']
    assert after.links == before.links
    assert after.rows == before.rows
    assert after.notices == before.notices == context['comparison']['notices']
    rows = [r for r in after.rows if r[0] is not None]
    assert len(rows) == len(context['comparison']['rows'])
    assert [(r[0], r[1]) for r in rows] == [(r['status'], r['model']) for r in context['comparison']['rows']]
    period = context['period'].id
    department = context['department_id']
    assert f'/source-comparison.csv?period_id={period}' + (f'&department_id={department}' if department else '') in after.links
    assert f'/dashboard?period_id={period}' in after.links
    return actual


@pytest.mark.parametrize('scenario', ['real', 'mixed', 'empty'])
@pytest.mark.parametrize('department_query', [True, False])
def test_frozen_contract_and_summary(comparison_response, scenario, department_query):
    context = dict(comparison_response.context) if scenario == 'real' else synthetic_context(comparison_response, scenario == 'empty')
    if not department_query: context['department_id'] = None
    html = assert_contract(comparison_response, context)
    counts = Counter(r['status'] for r in context['comparison']['rows'])
    assert (f'{len(context["comparison"]["rows"])} satır · {counts["Eşleşiyor"]} eşleşiyor · '
            f'{counts["Kararla değişti"]} kararla değişti · {counts["Fark var"]} fark var · '
            f'{counts["Kaynakta yok"]} kaynakta yok · {counts["Kayıtta yok"]} kayıtta yok') in html
    for status in STATUSES:
        assert (f'data-filter-status="{status}"' in html) == (counts[status] > 0)


def test_assets_only_on_comparison(client, comparison_response):
    assert '/static/design/source-comparison.css' in comparison_response.text
    assert '/static/design/source-comparison.js' in comparison_response.text
    dashboard = client.get('/dashboard').text
    assert '/static/design/source-comparison.css' not in dashboard
    assert '/static/design/source-comparison.js' not in dashboard


def route_page(bc, client, html):
    def serve(route):
        if urlsplit(route.request.url).path == '/source-comparison':
            route.fulfill(status=200, content_type='text/html', body=html)
        else:
            result = client.get(route.request.url)
            headers = dict(result.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=result.status_code, headers=headers, body=result.content)
    bc.route('http://testserver/**', serve)
    page = bc.new_page()
    page.goto('http://testserver/source-comparison')
    return page


@pytest.mark.parametrize('width', [1440, 390])
def test_browser_filter_keyboard_layout_contrast(browser, client, comparison_response, width):
    context = synthetic_context(comparison_response)
    html = assert_contract(comparison_response, context)
    folder = os.getenv('CIVENSA_CIV120_SCREENSHOTS')
    with browser.new_context(viewport={'width': width, 'height': 1000}) as bc:
        page = route_page(bc, client, html)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        root = page.locator('.source-comparison-page')
        rows = root.locator('#source-comparison tr[data-status]')
        buttons = root.locator('[data-filter-status]')
        all_button = buttons.first
        expect(rows.filter(visible=True)).to_have_count(6)
        expect(all_button).to_have_attribute('aria-pressed', 'true')
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
        if width == 390:
            expect(root.locator('.scroll-hint')).to_be_visible()
            wrap = root.locator('.table-wrap').first
            assert wrap.evaluate('el => el.scrollWidth > el.clientWidth')
            wrap.focus()
            page.keyboard.press('ArrowRight')
            expect(wrap).to_be_focused()
        script = TEXT_PAIRS.replace('.section-index-page', '.source-comparison-page')
        pairs = set(map(tuple, page.evaluate(script)))
        def screenshot(name):
            if folder:
                Path(folder).mkdir(parents=True, exist_ok=True)
                page.evaluate('document.activeElement.blur()')
                page.mouse.move(0, 0)
                root.locator('.table-wrap').first.evaluate('el => el.scrollLeft = 0')
                page.evaluate('window.scrollTo(0, 0)')
                # Keep the comparison evidence readable; the shared reconciliation
                # below this boundary has its own unchanged contract.
                boundary = root.locator('#pp-reconciliation')
                height = round(boundary.bounding_box()['y']) if boundary.count() else page.evaluate('document.documentElement.scrollHeight')
                page.screenshot(path=str(Path(folder) / f'{comparison_response.context["user"].role}-{name}-{width}.png'),
                                full_page=True, clip={'x': 0, 'y': 0, 'width': width, 'height': height})
        screenshot('all')
        for status in STATUSES:
            button = buttons.filter(has_text=status)
            button.click()
            expect(rows.filter(visible=True)).to_have_count(sum(r['status'] == status for r in context['comparison']['rows']))
            assert rows.filter(visible=True).evaluate_all('els => els.every(el => el.dataset.status === ' + repr(status) + ')')
            expect(button).to_have_attribute('aria-pressed', 'true')
            expect(root.locator('[aria-pressed="true"]')).to_have_count(1)
            pairs.update(map(tuple, page.evaluate(script)))
        all_button.click()
        expect(rows.filter(visible=True)).to_have_count(6)
        all_button.focus()
        for _ in range(3): page.keyboard.press('Tab')
        difference = buttons.filter(has_text='Fark var')
        expect(difference).to_be_focused()
        page.keyboard.press('Space')
        expect(rows.filter(visible=True)).to_have_count(2)
        expect(difference).to_have_attribute('aria-pressed', 'true')
        screenshot('difference')
        all_button.focus()
        page.keyboard.press('Enter')
        expect(rows.filter(visible=True)).to_have_count(6)
        expect(all_button).to_have_attribute('aria-pressed', 'true')
        for control in root.locator('a, button, summary, [tabindex]').all():
            control.hover()
            control.focus()
            pairs.update(map(tuple, page.evaluate(script)))
        root.locator('details').first.evaluate('el => el.open = true')
        expect(root.locator('details code').first).to_have_text('a' * 64)
        pairs.update(map(tuple, page.evaluate(script)))
        assert all(contrast(p) >= 4.5 for p in pairs), [(p, contrast(p)) for p in pairs if contrast(p) < 4.5]
        assert not errors
        page = route_page(bc, client, assert_contract(comparison_response, synthetic_context(comparison_response, empty=True)))
        expect(page.locator('.filter-empty')).to_have_text('Bu durumda satır yok.')
        expect(page.locator('.filter-empty')).to_be_visible()
        expect(page.get_by_text('Seçilen dönemde karşılaştırılacak kaynak veya kayıt bulunamadı.')).to_be_visible()
        root = page.locator('.source-comparison-page')
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        screenshot('empty')


@pytest.mark.parametrize('width', [1440, 390])
def test_without_javascript(browser, client, comparison_response, width):
    html = assert_contract(comparison_response, synthetic_context(comparison_response))
    with browser.new_context(java_script_enabled=False, viewport={'width': width, 'height': 1000}) as bc:
        page = route_page(bc, client, html)
        expect(page.locator('#source-comparison tr[data-status]').filter(visible=True)).to_have_count(6)
        expect(page.locator('.status-filter')).to_be_hidden()
        expect(page.locator('.filter-empty')).to_be_hidden()
