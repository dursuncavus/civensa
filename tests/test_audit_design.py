"""CIV-127: frozen audit-history contracts and responsive design checks."""
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
import os
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import expect

from app.main import app, require_user, safe_audit_details
from app.models import AuditLog
from test_section_index_design import TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/audit_016_start.html'
FROZEN_HASH = 'cae9097470488fb8b11616943b8259cda77ab427cfe0eccead25370db94d26ed'


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


def frozen_context(context):
    context = dict(context)
    context['actions'] = [code for code, _ in context['actions']]
    context['safe_details'] = safe_audit_details
    return context


def assert_frozen(response, **options):
    original = FROZEN.read_bytes()
    assert sha256(original).hexdigest() == FROZEN_HASH
    context = render_context(response, **options)
    old = response.template.environment.from_string(original.decode()).render(frozen_context(context))
    actual = response.template.render(context)
    before, after = AuditContract(old), AuditContract(actual)
    assert before.controls == after.controls
    assert before.links == after.links
    assert before.headers == after.headers == ['Tarih', 'Kullanıcı', 'İşlem', 'Varlık', 'Ayrıntı']
    if options.get('rows') == []:
        assert after.cells[-1] == 'Filtreye uygun kayıt bulunamadı.'
    else:
        assert len(before.cells) == len(after.cells)
        assert all(before.cells[index:index + 2] == after.cells[index:index + 2]
                   for index in range(0, len(before.cells), 5))
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
    assert with_period.cells[2:4] == ['Diğer işlem', 'Diğer kayıt']
    assert 'Teknik ayrıntı' in with_period.data
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


def test_known_action_filter_keeps_raw_value_and_displays_turkish_label(audit_client, db, sample):
    db.add(AuditLog(user_id=sample['strategy'].id, action='activity_update',
        entity_type='activity', entity_id=sample['activity'].id,
        created_at=datetime(2026, 10, 26, 9, 30), details='revision=3'))
    db.commit()
    response = audit_client.get(
        f'/audit?period_id={sample["period"].id}&action=activity_update')
    assert response.status_code == 200
    page = AuditContract(response.text)
    assert any(tag == 'option' and dict(attrs).get('value') == 'activity_update'
        and 'selected' in dict(attrs) for tag, attrs in page.controls)
    assert 'Faaliyet güncellendi' in page.data
    assert 'activity_update' not in page.data
    assert page.cells[2:] == ['Faaliyet güncellendi', 'Faaliyet: Ortak faaliyet', 'Revizyon 3']


def test_csv_export_preserves_original_codes_and_raw_details(audit_client, db, sample):
    db.add(AuditLog(user_id=sample['strategy'].id, action='activity_update',
        entity_type='activity', entity_id=sample['activity'].id,
        created_at=datetime(2026, 10, 26, 9, 30), details='revision=3;subprogram_id=15'))
    db.commit()
    response = audit_client.get(
        f'/api/audit/export.csv?period_id={sample["period"].id}&action=activity_update')
    assert response.status_code == 200
    assert response.content == (
        '\ufeffTarih,Kullanıcı,İşlem,Varlık,Varlık ID,Ayrıntı\r\n'
        f'2026-10-26 09:30:00,{sample["strategy"].email},activity_update,activity,'
        f'{sample["activity"].id},revision=3;subprogram_id=15\r\n'
    ).encode('utf-8')


@pytest.mark.parametrize('width', [1440, 1024, 390])
def test_browser_layout_contrast_and_screenshots(browser, audit_client, db, sample, width):
    db.add_all([
        AuditLog(user_id=sample['strategy'].id, action='activity_update', entity_type='activity',
            entity_id=127, created_at=datetime(2026, 10, 26, 9, 30), details='revision=3;note=sentetik'),
        AuditLog(user_id=sample['strategy'].id, action='user_create', entity_type='user',
            entity_id=sample['strategy'].id, created_at=datetime(2026, 10, 26, 9, 30), details='role=strategy'),
        AuditLog(user_id=sample['strategy'].id, action='budget_reallocation', entity_type='budget_operation',
            entity_id=9201, created_at=datetime(2026, 10, 26, 9, 30),
            details='{"count": 12, "bytes": 1200000}'),
    ])
    db.commit()
    filtered_url = f'http://testserver/audit?period_id={sample["period"].id}&user=strategy%40example.invalid'
    empty_url = filtered_url.replace('strategy%40example.invalid', 'missing%40example.invalid')
    filtered = audit_client.get(filtered_url)
    empty = audit_client.get(empty_url)
    assert filtered.status_code == empty.status_code == 200
    page_html = {
        'filtered': filtered.template.environment.from_string(FROZEN.read_text()).render(
            frozen_context(filtered.context)),
        'empty': empty.template.environment.from_string(FROZEN.read_text()).render(frozen_context(empty.context)),
    }
    target = os.getenv('CIVENSA_CIV138_SCREENSHOTS')
    errors = []
    with browser.new_context(viewport={'width': width, 'height': 1000}) as context:
        def serve(route):
            request = route.request
            if urlsplit(request.url).path == '/audit':
                user_filter = parse_qs(urlsplit(request.url).query).get('user', [''])[0]
                state = 'empty' if user_filter == 'missing@example.invalid' else 'filtered'
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
                filtered.template.environment.from_string(FROZEN.read_text()).render(
                    frozen_context(filtered.context))
                if stage == 'before' else filtered.text)
            page_html['empty'] = (
                empty.template.environment.from_string(FROZEN.read_text()).render(frozen_context(empty.context))
                if stage == 'before' else empty.text)
            for state, url, expected in [
                ('filtered', filtered_url, 'Faaliyet güncellendi'),
                ('empty', empty_url, 'Filtreye uygun kayıt bulunamadı.'),
            ]:
                page.goto(url)
                root = page.locator('.audit-page')
                if stage == 'after':
                    assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
                    assert page.locator('main *').evaluate_all(
                        "els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
                    filter_form = root.locator('.audit-filters')
                    if width >= 1024:
                        assert filter_form.evaluate(
                            'el => getComputedStyle(el).gridTemplateColumns.split(" ").length === 5')
                        layout = filter_form.evaluate("""el => [...el.children].map(child => ({
                            tag: child.tagName, type: child.type || '', top: child.getBoundingClientRect().top,
                            height: child.getBoundingClientRect().height, row: getComputedStyle(child).gridRow
                        }))""")
                        rows = filter_form.locator('label select, label input, button, a').evaluate_all(
                            'els => els.map(el => el.getBoundingClientRect().y)')
                        assert max(rows) - min(rows) <= 2, layout
                    elif width == 390:
                        assert filter_form.evaluate(
                            'el => getComputedStyle(el).gridTemplateColumns.split(" ").length === 1')
                    if state == 'filtered':
                        expect(root).to_contain_text(expected)
                        visible_text = root.inner_text()
                        assert 'activity_update' not in visible_text
                        assert not re.search(r'#\d+', visible_text)
                        detail_row = root.locator('tr').filter(has_text='Faaliyet güncellendi')
                        expect(detail_row.get_by_text('Revizyon 3', exact=False)).to_be_visible()
                        expect(detail_row.get_by_text('Teknik ayrıntı')).to_be_visible()
                        cell = root.locator('.audit-details').first
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
                if target and state == 'filtered' and width in {1440, 390}:
                    folder = Path(target)
                    folder.mkdir(parents=True, exist_ok=True)
                    page.evaluate('document.activeElement.blur(); window.scrollTo(0, 0)')
                    page.mouse.move(0, 0)
                    image = folder / f'{stage}-{state}-{width}.png'
                    page.screenshot(path=str(image), full_page=True)
                    assert image.stat().st_size <= 1_500_000
        assert not errors
