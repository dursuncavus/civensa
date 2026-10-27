"""CIV-127: frozen audit-history contracts and responsive design checks."""
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect

from app.main import app, require_user
from app.models import AuditLog
from test_section_index_design import TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/audit_016_start.html'
FROZEN_HASH = 'cae9097470488fb8b11616943b8259cda77ab427cfe0eccead25370db94d26ed'
SCROLL_HINT = 'Tablonun tamamını görmek için yatay kaydırın.'


class AuditContract(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.in_main = False
        self.data = []
        self.controls = []
        self.links = []
        self.headers = []
        self.cells = []
        self.current_link = None
        self.current_cell = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'main':
            self.in_main = True
        if not self.in_main:
            return
        if tag in {'form', 'input', 'select', 'option', 'button'}:
            self.controls.append((tag, tuple(sorted((k, v) for k, v in attrs.items()
                if k not in {'class', 'style'}))))
        if tag == 'a':
            self.current_link = [attrs.get('href'), []]
        if tag in {'th', 'td'}:
            self.current_cell = [tag, []]

    def handle_data(self, data):
        if not self.in_main:
            return
        if data.strip():
            self.data.append(data.strip())
        if self.current_link is not None:
            self.current_link[1].append(data)
        if self.current_cell is not None:
            self.current_cell[1].append(data)

    def handle_endtag(self, tag):
        if not self.in_main:
            return
        if tag == 'a' and self.current_link is not None:
            self.links.append((self.current_link[0], ' '.join(''.join(self.current_link[1]).split())))
            self.current_link = None
        if tag in {'th', 'td'} and self.current_cell is not None:
            cell_tag, text = self.current_cell
            value = ' '.join(''.join(text).split())
            (self.headers if cell_tag == 'th' else self.cells).append(value)
            self.current_cell = None
        if tag == 'main':
            self.in_main = False


def render_context(response, *, period=True, rows=None, page=1, has_next=False):
    context = dict(response.context)
    if not period:
        context['period'] = None
        context['period_query'] = ''
    if rows is not None:
        context['rows'] = rows
    context['page'] = page
    context['has_next'] = has_next
    context['request'].state.pp_attempt_rendered = False
    return context


def assert_frozen(response, **options):
    original = FROZEN.read_bytes()
    assert sha256(original).hexdigest() == FROZEN_HASH
    context = render_context(response, **options)
    old = response.template.environment.from_string(original.decode()).render(context)
    actual = response.template.render(context)
    before, after = AuditContract(old), AuditContract(actual)
    assert before.controls == after.controls
    assert before.links == after.links
    assert before.headers == after.headers == ['Tarih', 'Kullanıcı', 'İşlem', 'Varlık', 'Ayrıntı']
    if options.get('rows') == []:
        assert after.cells[-1] == 'Filtreye uygun kayıt bulunamadı.'
    else:
        assert before.cells == after.cells
    old_text = ' '.join(' '.join(before.data).split())
    new_text = ' '.join(' '.join(after.data).split())
    old_text = old_text.replace('Denetim Geçmişi', 'Denetim geçmişi')
    new_text = ' '.join(new_text.replace(SCROLL_HINT, '').split())
    assert new_text == old_text
    return actual


@pytest.fixture
def audit_client(client, sample):
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    return client


def test_frozen_forms_links_table_and_visible_text(audit_client, db, sample):
    db.add(AuditLog(user_id=sample['strategy'].id, action='contract_action',
        entity_type='synthetic', entity_id=127, created_at=datetime(2026, 10, 26, 9, 30),
        details='Sentetik sözleşme ayrıntısı'))
    db.commit()
    base_url = f'/audit?period_id={sample["period"].id}&action=contract_action&user=strategy%40example.invalid'
    response = audit_client.get(base_url)
    assert response.status_code == 200
    with_period = AuditContract(assert_frozen(response))
    assert ('input', (('name', 'period_id'), ('type', 'hidden'), ('value', str(sample['period'].id)))) in with_period.controls
    assert any(tag == 'option' and 'selected' in dict(attrs) and
        dict(attrs).get('value') == 'contract_action' for tag, attrs in with_period.controls)
    assert ('/audit?period_id=' + str(sample['period'].id), 'Temizle') in with_period.links
    assert ('/api/audit/export.csv?period_id=' + str(sample['period'].id) +
        '&action=contract_action&user=strategy%40example.invalid', 'CSV indir') in with_period.links
    no_period = AuditContract(assert_frozen(response, period=False))
    assert not any(tag == 'input' and dict(attrs).get('name') == 'period_id' for tag, attrs in no_period.controls)
    next_page = AuditContract(assert_frozen(response, page=2, has_next=True))
    expected_page_query = f'?period_id={sample["period"].id}&page='
    assert (expected_page_query + '1&action=contract_action&user=strategy%40example.invalid', 'Önceki') in next_page.links
    assert (expected_page_query + '3&action=contract_action&user=strategy%40example.invalid', 'Sonraki') in next_page.links
    empty_response = audit_client.get(base_url.replace('strategy%40example.invalid', 'missing%40example.invalid'))
    empty = AuditContract(assert_frozen(empty_response))
    assert 'Filtreye uygun kayıt bulunamadı.' in empty.cells


@pytest.mark.parametrize('width', [1440, 390])
def test_browser_layout_contrast_and_screenshots(browser, audit_client, db, sample, width):
    detail = 'Sentetik ayrıntı ' * 20
    record = AuditLog(user_id=sample['strategy'].id, action='civ127_synthetic',
        entity_type='synthetic', entity_id=127, created_at=datetime(2026, 10, 26, 9, 30),
        details=detail[:300])
    db.add(record)
    db.commit()
    filtered_url = f'http://testserver/audit?period_id={sample["period"].id}&action=civ127_synthetic&user=strategy%40example.invalid'
    empty_url = filtered_url.replace('strategy%40example.invalid', 'missing%40example.invalid')
    filtered = audit_client.get(filtered_url)
    empty = audit_client.get(empty_url)
    assert filtered.status_code == empty.status_code == 200
    page_html = {
        'filtered': filtered.template.environment.from_string(FROZEN.read_text()).render(filtered.context),
        'empty': empty.template.environment.from_string(FROZEN.read_text()).render(empty.context),
    }
    target = os.getenv('CIVENSA_CIV127_SCREENSHOTS')
    errors = []
    with browser.new_context(viewport={'width': width, 'height': 1000}) as context:
        def serve(route):
            request = route.request
            if urlsplit(request.url).path == '/audit':
                state = 'empty' if 'missing%40example.invalid' in request.url else 'filtered'
                route.fulfill(status=200, content_type='text/html; charset=utf-8',
                              body=page_html[state])
                return
            response = audit_client.get(request.url)
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)

        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        for stage in ('before', 'after'):
            page_html['filtered'] = (
                filtered.template.environment.from_string(FROZEN.read_text()).render(filtered.context)
                if stage == 'before' else filtered.text)
            page_html['empty'] = (
                empty.template.environment.from_string(FROZEN.read_text()).render(empty.context)
                if stage == 'before' else empty.text)
            for state, url, expected in [
                ('filtered', filtered_url, detail[:300]),
                ('empty', empty_url, 'Filtreye uygun kayıt bulunamadı.'),
            ]:
                page.goto(url)
                root = page.locator('.audit-page')
                if stage == 'after':
                    assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
                    assert page.locator('main *').evaluate_all(
                        "els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
                    if state == 'filtered':
                        cell = root.locator('.audit-details')
                        expect(cell).to_contain_text(expected)
                        assert cell.evaluate("el => getComputedStyle(el).overflowWrap === 'anywhere'")
                        assert cell.evaluate('el => el.scrollWidth <= el.clientWidth')
                    else:
                        expect(root.get_by_text(expected, exact=True)).to_be_visible()
                    if width == 390:
                        expect(root.locator('.audit-scroll-hint')).to_be_visible()
                        assert root.locator('.table-wrap').evaluate('el => el.scrollWidth > el.clientWidth')
                    pairs = set(map(tuple, page.evaluate(
                        TEXT_PAIRS.replace('.section-index-page', '.audit-page'))))
                    assert all(contrast(pair) >= 4.5 for pair in pairs), [
                        (pair, contrast(pair)) for pair in pairs if contrast(pair) < 4.5]
                if target:
                    folder = Path(target)
                    folder.mkdir(parents=True, exist_ok=True)
                    page.evaluate('document.activeElement.blur(); window.scrollTo(0, 0)')
                    page.mouse.move(0, 0)
                    image = folder / f'{stage}-{state}-{width}.png'
                    page.screenshot(path=str(image), full_page=True)
                    assert image.stat().st_size <= 1_500_000
        assert not errors
