"""CIV-113: frozen GET/row contract and synthetic browser evidence."""
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import expect

from app.main import app, require_user
from app.models import ReportingPeriod
from test_section_index_design import Contract, TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/pp_manifest_start.html'


class Rows(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr' and 'data-key' in attrs:
            self.row = [attrs['data-key'], [], []]
        if self.row is not None:
            if tag == 'td': self.cell = []
            if tag == 'a': self.row[2].append(attrs['href'])

    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None:
            self.row[1].append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


@pytest.fixture
def manifest_response(client, db, sample):
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    db.add(ReportingPeriod(year=2028, status='active'))
    db.commit()
    return client.get('/report-builder/manifest', params={'period_id': sample['period'].id})


def synthetic_context(response, empty=False):
    rows = [dict(key=f'synthetic-{i}', name='Sentetik uzun bölüm adı ' + 'UzunAd' * 18,
                 kind='Bölüm' if i % 2 else 'Tablo', status=status, count=i,
                 href=f'/report-builder?period_id={response.context["period"].id}&section={i}#section-{i}')
            for i, status in enumerate(['Tamam', 'Boş', 'Eksik', 'Tamam'])]
    return dict(response.context, manifest=dict(rows=[] if empty else rows, source='Sentetik kapsam'))


def assert_contract(response, context):
    assert response.status_code == 200
    source = FROZEN.read_bytes()
    assert sha256(source).hexdigest() == '9f2296cc1214c9aba8090e9889be132409c5917afd8dabc5410936a3b50b86fe'
    old = response.template.environment.from_string(source.decode()).render(context)
    actual = response.template.render(context)
    before, after = Contract(old), Contract(actual)
    assert before.controls == after.controls
    assert before.bindings == after.bindings
    old_rows, new_rows = Rows(old).rows, Rows(actual).rows
    for row in old_rows: row[1][-1] = 'İçeriği aç'
    assert new_rows == old_rows
    assert len(new_rows) == len(context['manifest']['rows'])
    for row, expected in zip(new_rows, context['manifest']['rows']):
        assert row[0] == expected['key']
        assert row[1][2] == expected['status']
        assert row[2] == [expected['href']]
    return actual


@pytest.mark.parametrize('scenario', ['real', 'mixed', 'empty'])
def test_frozen_contract_and_summary(manifest_response, scenario):
    context = manifest_response.context if scenario == 'real' else synthetic_context(manifest_response, scenario == 'empty')
    html = assert_contract(manifest_response, context)
    counts = Counter(row['status'] for row in context['manifest']['rows'])
    assert f'{len(context["manifest"]["rows"])} bölüm/tablo · {counts["Tamam"]} tamam · {counts["Boş"]} boş · {counts["Eksik"]} eksik' in html


def test_department_response_and_page_only_css(client, sample):
    assert client.get('/report-builder/manifest', follow_redirects=False).status_code == 403
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    assert 'pp-manifest.css' not in client.get('/dashboard').text


@pytest.mark.parametrize('width', [1440, 390])
def test_browser_layout_contrast_and_period(browser, client, manifest_response, width):
    context = synthetic_context(manifest_response)
    html = assert_contract(manifest_response, context)
    calls = []
    with browser.new_context(viewport={'width': width, 'height': 1000}) as bc:
        def serve(route):
            path = urlsplit(route.request.url).path
            if path == '/report-builder/manifest':
                calls.append(route.request.url)
                route.fulfill(status=200, content_type='text/html', body=html)
            else:
                result = client.get(route.request.url)
                headers = dict(result.headers)
                headers.pop('set-cookie', None)
                route.fulfill(status=result.status_code, headers=headers, body=result.content)
        bc.route('http://testserver/**', serve)
        page = bc.new_page()
        page.goto('http://testserver/report-builder/manifest')
        page.evaluate('document.fonts.ready')
        root = page.locator('.pp-manifest-page')
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
        boxes = [el.bounding_box() for el in root.locator('.period-toolbar label, .period-toolbar select, .period-toolbar button').all()]
        if width == 1440:
            assert len({round(b['y'] + b['height'] / 2) for b in boxes}) == 1
        else:
            assert boxes[0]['y'] < boxes[1]['y'] < boxes[2]['y']
            expect(root.locator('.scroll-hint')).to_be_visible()
            wrap = root.locator('.table-wrap')
            assert wrap.evaluate('el => el.scrollWidth > el.clientWidth')
            wrap.evaluate('el => el.scrollLeft = el.scrollWidth')
            assert wrap.evaluate('el => el.scrollLeft > 0')
            wrap.evaluate('el => el.scrollLeft = 0')
        script = TEXT_PAIRS.replace('.section-index-page', '.pp-manifest-page')
        pairs = set(map(tuple, page.evaluate(script)))
        for control in root.locator('a, button, select, [tabindex]').all():
            control.hover()
            control.focus()
            pairs.update(map(tuple, page.evaluate(script)))
        assert all(contrast(pair) >= 4.5 for pair in pairs), [(p, contrast(p)) for p in pairs if contrast(p) < 4.5]
        screenshots = os.getenv('CIVENSA_CIV113_SCREENSHOTS')
        if screenshots:
            folder = Path(screenshots)
            folder.mkdir(parents=True, exist_ok=True)
            page.evaluate('document.activeElement.blur()')
            page.mouse.move(0, 0)
            if width == 390:
                root.locator('.table-wrap').screenshot(path=str(folder / 'manifest-table-status-390.png'))
            root.locator('.table-wrap').evaluate('el => el.scrollLeft = 0')
            page.evaluate('window.scrollTo(0, 0)')
            page.screenshot(path=str(folder / f'manifest-{width}.png'), full_page=True)
        other = next(p for p in context['periods'] if p.id != context['period'].id)
        root.locator('select').select_option(str(other.id))
        root.get_by_role('button', name='Dönemi Göster').click()
        assert parse_qs(urlsplit(calls[-1]).query) == {'period_id': [str(other.id)]}
