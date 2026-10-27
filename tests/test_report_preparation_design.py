"""CIV-118: frozen real-screen contract, status evidence and browser saves."""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect
from sqlalchemy import select

from app.main import app, require_user
from app.models import EconomicValue, IndicatorValue, Submission
from test_sidebar_ui import browser
from test_live_pilot_hardening import live_client, login
from test_section_index_design import TEXT_PAIRS, contrast

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/report_preparation_start.html'
SECTION_IDS = ['cards', 'assignments', 'catalogue', 'sources', 'finance', 'economics']


def route_application(context, client):
    """Exercise the real app with login cookies and the browser's content negotiation."""
    def serve(route):
        req = route.request
        response = client.request(req.method, req.url, content=req.post_data_buffer,
            headers={key: value for key, value in req.headers.items()
                     if key in ('content-type', 'x-csrf-token', 'accept')}, follow_redirects=False)
        headers = dict(response.headers)
        headers.pop('set-cookie', None)
        route.fulfill(status=response.status_code, headers=headers, body=response.content)
    context.route('http://testserver/**', serve)


@pytest.fixture
def report_http(live_client, sample):
    """Use loopback HTTP so Chromium follows native POST redirects itself.

    Playwright routing does not re-intercept a redirect chain. The serial HTTP
    bridge keeps every request inside the disposable TestClient database.
    """
    client = live_client()
    login(client, sample['user'].email)

    class Handler(BaseHTTPRequestHandler):
        def serve(self):
            body = self.rfile.read(int(self.headers.get('content-length', '0')))
            response = client.request(self.command, self.path, content=body,
                headers={k: self.headers[k] for k in ('content-type', 'x-csrf-token', 'accept')
                         if k in self.headers}, follow_redirects=False)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in {'content-length', 'transfer-encoding', 'connection', 'set-cookie'}:
                    self.send_header(key, value)
            self.send_header('Content-Length', str(len(response.content)))
            self.end_headers()
            self.wfile.write(response.content)
        do_GET = do_POST = serve

        def log_message(self, *args):
            pass

    server = HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    def walk(self, tag=None):
        for child in self.children:
            if isinstance(child, Node):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.walk(tag)

    def text(self):
        return ''.join(c.text() if isinstance(c, Node) else c for c in self.children)


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.root = self.current = Node()
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        child = Node(tag, attrs, self.current)
        self.current.children.append(child)
        if tag not in {'input', 'link', 'meta', 'br', 'hr', 'img', 'source', 'wbr'}:
            self.current = child

    def handle_endtag(self, tag):
        node = self.current
        while node.parent:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def normalized(text):
    return ' '.join(text.split())


def form_contract(html):
    """Compare form association, all control attributes, values and effective disabled state.

    Class/style and visible button/label text may change. CSRF values are compared
    exactly in memory. Whitespace around options without value is HTML-collapsed.
    """
    root = Document(html).root
    forms = []
    for form in root.walk('form'):
        fields = []
        for field in form.walk():
            if field.tag not in {'input', 'select', 'textarea', 'button', 'option', 'fieldset'}:
                continue
            attrs = {k: v for k, v in field.attrs.items() if k not in {'class', 'style'}}
            disabled = 'disabled' in attrs
            parent = field.parent
            while parent is not form:
                disabled |= parent.tag == 'fieldset' and 'disabled' in parent.attrs
                parent = parent.parent
            text = field.text() if field.tag == 'textarea' else (
                normalized(field.text()) if field.tag == 'option' else '')
            fields.append((field.tag, attrs, disabled, text))
        attrs = {k: v for k, v in form.attrs.items() if k not in {'class', 'style'}}
        forms.append(json.dumps([attrs, fields], sort_keys=True, ensure_ascii=False))
    return Counter(forms)


def links(html):
    return Counter(a.attrs['href'] for a in Document(html).root.walk('a'))


def removal_contract(html):
    root = Document(html).root
    def canonical(node):
        return [node.tag, node.attrs, [canonical(c) if isinstance(c, Node) else normalized(c)
                for c in node.children if isinstance(c, Node) or c.strip()]]
    return [canonical(n) for n in root.walk('details') if n.attrs.get('class') == 'draft-removal']


@pytest.mark.parametrize('role', ['department', 'strategy'])
@pytest.mark.parametrize('editable', [True, False])
@pytest.mark.parametrize('group,fund', [('service', 'inside'), ('management', 'outside')])
def test_frozen_forms_links_values_disabled_removal(live_client, sample, role, editable, group, fund):
    client = live_client()
    login(client, sample['strategy' if role == 'strategy' else 'user'].email)
    app.dependency_overrides[require_user] = lambda: sample['strategy' if role == 'strategy' else 'user']
    response = client.get(f'/program/1?period_id=1&group={group}&fund={fund}')
    assert response.status_code == 200
    context = dict(response.context, editable=editable, removable=editable)
    assert context['request'].session.get('csrf_token')
    # Exercise every conditional source-verification form, including generic value,
    # non-default selected options and blank/zero distinctions.
    context['snapshot'] = deepcopy(context['snapshot'])
    context['snapshot']['indicators'][0]['values'][0].update(state='needs_review', value_kind='value', raw_text='1,75')
    context['snapshot']['activities'][0]['costs'][0].update(state='needs_review', raw_text='123,45')
    context['snapshot']['department_costs'][0].update(state='needs_review', amount=None, raw_text='—')
    context['snapshot']['economics'][0].update(state='needs_review', program_group='unallocated')
    source = FROZEN.read_bytes()
    assert sha256(source).hexdigest() == 'eff96facc6b8f8c7648978eb468d98b74000d0bceb94c6a0fc506e3c89f5da82'
    old = response.template.environment.from_string(source.decode()).render(context)
    new = response.template.render(context)
    assert form_contract(new) == form_contract(old)
    added = Counter({f'#rp-{key}': 2 for key in SECTION_IDS})
    assert links(new) == links(old) + added
    assert removal_contract(new) == removal_contract(old)
    for id in ['economicGridForm', 'economicGridErrors']:
        before = [n.attrs for n in Document(old).root.walk() if n.attrs.get('id') == id]
        after = [n.attrs for n in Document(new).root.walk() if n.attrs.get('id') == id]
        assert after == before and len(after) == 1


@pytest.mark.parametrize('scenario', ['empty', 'unassigned', 'unverified', 'incomplete_card', 'complete', 'submitted'])
def test_overview_statuses_and_exact_error_count(client, db, sample, scenario):
    if scenario == 'submitted':
        db.scalar(select(Submission)).status = 'submitted'
        db.commit()
    response = client.get('/program/1?period_id=1')
    context = dict(response.context)
    snap = context['snapshot'] = deepcopy(context['snapshot'])
    if scenario == 'empty':
        context.update(cards=[], errors=['Performans göstergesi yok.', 'Performans kartları hazırlanmalı.'])
        snap.update(indicators=[], activities=[], department_costs=[], economics=[])
        expected = ['Başlanmadı'] * 6
        expected_tones = ['neutral'] * 6
    elif scenario == 'unassigned':
        snap['indicators'][0]['card_id'] = None
        snap['activities'][0].update(card_id=None, official_ids=[])
        expected = ['1 kart', '2 kayıt kartsız', '1 faaliyet bağlanacak', 'Kaynak değerleri doğrulandı', 'Tutarlar doğrulandı', 'Kaynak hücreleri doğrulandı']
        expected_tones = ['neutral', 'warning', 'warning', 'success', 'success', 'success']
    elif scenario == 'unverified':
        snap['indicators'][0]['values'][0]['state'] = 'needs_review'
        snap['department_costs'][0]['state'] = 'needs_review'
        snap['activities'][0]['costs'][0]['state'] = 'needs_review'
        snap['economics'][0]['state'] = 'needs_review'
        snap['activities'][0]['costs'] = []
        expected = ['1 kart', 'Tamamlandı', 'Tamamlandı', '2 kayıt doğrulanacak', '1 faaliyet kontrol edilecek', '1 hücre doğrulanacak']
        expected_tones = ['neutral', 'success', 'success', 'warning', 'warning', 'warning']
    elif scenario == 'incomplete_card':
        context['cards'][0].rationale = ''
        expected = ['1 kart eksik', 'Tamamlandı', 'Tamamlandı', 'Kaynak değerleri doğrulandı', 'Tutarlar doğrulandı', 'Kaynak hücreleri doğrulandı']
        expected_tones = ['warning', 'success', 'success', 'success', 'success', 'success']
    else:
        expected = ['1 kart', 'Tamamlandı', 'Tamamlandı', 'Kaynak değerleri doğrulandı', 'Tutarlar doğrulandı', 'Kaynak hücreleri doğrulandı']
        expected_tones = ['neutral', 'success', 'success', 'success', 'success', 'success']
    root = Document(response.template.render(context)).root
    overview = next(n for n in root.walk('ul') if n.attrs.get('class') == 'rp-task-list')
    badges = [n for n in overview.walk('span') if 'rp-status' in n.attrs.get('class', '').split()]
    statuses = [normalized(n.text()) for n in badges]
    assert statuses == expected
    assert [n.attrs['class'].split()[-1] for n in badges] == expected_tones
    summary = next(n for n in root.walk('section') if n.attrs.get('class') == 'rp-panel rp-overview')
    errors = [n for n in summary.walk('details') if 'rp-errors' in n.attrs.get('class', '')]
    if context['errors']:
        assert len(errors) == 1
        assert len(list(errors[0].walk('li'))) == len(context['errors'])
        assert normalized(next(errors[0].walk('summary')).text()) == f'{len(context["errors"])} eksik / tutarsız kayıt'
    else:
        assert not errors
    if scenario == 'submitted':
        assert not context['editable']
        for form in root.walk('form'):
            if form.attrs.get('action', '').startswith('/program/') and form.attrs.get('method') == 'post':
                assert not list(form.walk('button'))


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('state', ['in-progress', 'complete', 'read-only', 'strategy'])
def test_browser_layout_anchors_contrast_and_evidence(browser, client, db, sample, width, state):
    if state == 'read-only':
        db.scalar(select(Submission)).status = 'submitted'
    if state in {'in-progress', 'strategy'}:
        sample['activity'].card_id = None
        db.scalar(select(IndicatorValue)).state = 'needs_review'
    if state == 'strategy':
        app.dependency_overrides[require_user] = lambda: sample['strategy']
        db.scalar(select(EconomicValue).where(EconomicValue.category == 'goods_services')).program_group = 'unallocated'
    db.commit()
    with browser.new_context(viewport={'width': width, 'height': 900}, locale='tr-TR', timezone_id='Europe/Istanbul', reduced_motion='reduce') as context:
        route_application(context, client)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver/program/1?period_id=1')
        page.evaluate('document.fonts.ready')
        root = page.locator('.report-preparation-page')
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        if width == 1440:
            task_list = root.locator('.rp-task-list')
            task_box = task_list.bounding_box()
            assert task_box['width'] <= 44 * 16
            for status in task_list.locator('.rp-status').all():
                status_box = status.bounding_box()
                assert task_box['x'] <= status_box['x']
                assert task_box['y'] <= status_box['y']
                assert status_box['x'] + status_box['width'] <= task_box['x'] + task_box['width']
                assert status_box['y'] + status_box['height'] <= task_box['y'] + task_box['height']
        contents = root.locator('.rp-contents')
        assert contents.is_visible() == (width >= 1280)
        if width >= 1280:
            assert contents.evaluate('el => getComputedStyle(el).position') == 'sticky'
        for key in SECTION_IDS:
            root.locator(f'.rp-overview a[href="#rp-{key}"]').click()
            expect(page).to_have_url(f'http://testserver/program/1?period_id=1#rp-{key}')
            box = root.locator(f'#rp-{key}').bounding_box()
            assert 0 <= box['y'] < 900
        if state == 'strategy':
            expect(root.get_by_role('link', name='Program Grubu Dağılımı', exact=True)).to_be_visible()
        assert not root.locator('#rp-finance > details[open]').count()
        # Closed and open records, focused fields and disabled controls are all measured.
        script = TEXT_PAIRS.replace('.section-index-page', '.report-preparation-page')
        pairs = set(map(tuple, page.evaluate(script)))
        root.locator('#rp-cards > details, #rp-finance > details').evaluate_all('els => els.forEach(el => el.open = true)')
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        pairs.update(map(tuple, page.evaluate(script)))
        for selector in ['.rp-overview a', '#rp-cards summary', '#rp-cards input[name=position]', '.rp-toolbar button']:
            control = root.locator(selector).first
            if control.is_enabled():
                control.hover()
                control.focus()
                pairs.update(map(tuple, page.evaluate(script)))
        pairs.update(map(tuple, root.locator('.rp-overview .rp-status').evaluate_all(
            'els => els.map(el => { const style = getComputedStyle(el); return [style.color, style.backgroundColor]; })')))
        assert all(contrast(pair) >= 4.5 for pair in pairs), [(p, contrast(p)) for p in pairs if contrast(p) < 4.5]
        reconciliation = root.locator('#pp-reconciliation')
        if reconciliation.count():
            headers = reconciliation.locator('thead th')
            numeric_cells = reconciliation.locator('tbody td:nth-child(3), tbody td:nth-child(4), tbody td:nth-child(5)')
            for cell in [*headers.all(), *numeric_cells.all()]:
                assert cell.evaluate('el => getComputedStyle(el).whiteSpace') == 'nowrap'
            for header in headers.all():
                assert header.evaluate('el => getComputedStyle(el).overflowWrap') == 'normal'
                assert header.evaluate('el => getComputedStyle(el).wordBreak') == 'normal'
            if width == 1440:
                assert reconciliation.locator('.table-wrap').evaluate('el => el.scrollWidth > el.clientWidth')
                assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        if width == 390:
            expect(root.locator('.rp-scroll-hint')).to_be_visible()
            table = root.locator('#economicGridForm .table-wrap')
            assert table.evaluate('el => el.scrollWidth > el.clientWidth')
            table.evaluate('el => el.scrollLeft = el.scrollWidth')
            assert table.evaluate('el => el.scrollLeft > 0')
            table.evaluate('el => el.scrollLeft = 0')
        if state in {'read-only', 'strategy'}:
            assert not root.locator('form[method=post]:not([data-draft-removal]) button').count()
            field = root.locator('#rp-cards input[name=position]').first
            assert field.is_disabled()
            assert field.evaluate('el => getComputedStyle(el).backgroundColor') == 'rgb(239, 237, 232)'
        # Capture default disclosures, so all six work sections remain scannable.
        root.locator('#rp-cards > details, #rp-finance > details').evaluate_all('els => els.forEach(el => el.open = !!el.querySelector("form[action$=cards]:not(:has(input[name=id]))"))')
        folder = os.getenv('CIVENSA_CIV118_SCREENSHOTS')
        if folder:
            Path(folder).mkdir(parents=True, exist_ok=True)
            page.evaluate('document.activeElement.blur(); window.scrollTo(0, 0)')
            page.mouse.move(0, 0)
            target = Path(folder) / f'{state}-{width}.png'
            page.screenshot(path=str(target), full_page=True)
            assert target.stat().st_size <= 1_500_000
        for boundary in [1279, 1280]:
            page.set_viewport_size({'width': boundary, 'height': 900})
            assert contents.is_visible() == (boundary == 1280)
        assert not errors


@pytest.mark.parametrize('width', [1440, 390])
def test_real_card_grid_saves_and_rejected_form_reopens(browser, db, sample, report_http, width):
    base = report_http
    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        page = context.new_page()
        page.goto(base + '/program/1?period_id=1')
        record = page.locator('#rp-cards > details').first
        assert not record.evaluate('el => el.open')
        record.locator('summary').first.click()
        title = record.locator('textarea[name=source_title]')
        title.fill('Sentetik kayıt testi')
        record.get_by_role('button', name='Kartı kaydet', exact=True).click()
        expect(page).to_have_url(base + '/program/1?period_id=1')
        expect(page.locator('#rp-cards')).to_be_visible()
        db.refresh(sample['card'])
        assert sample['card'].source_title == 'Sentetik kayıt testi'
        # A rejected POST must retain the attempted field and reopen records.
        record = page.locator('#rp-cards > details').first
        record.locator('summary').first.click()
        record.locator('textarea[name=rationale]').fill('Gönderilemeyen sentetik açıklama')
        record.locator('select[name=subprogram_id]').evaluate('el => { const o = new Option("Geçersiz dönem", "999999"); el.add(o); el.value = o.value; }')
        record.get_by_role('button', name='Kartı kaydet', exact=True).click()
        expect(page.locator('#rp-cards > details').first).to_have_attribute('open', '')
        expect(page.locator('#rp-finance > details').first).to_have_attribute('open', '')
        expect(page.locator('#rp-cards textarea[name=rationale]').first).to_have_value('Gönderilemeyen sentetik açıklama')
        page.goto(base + '/program/1?period_id=1')
        grid = page.locator('#economicGridForm')
        field = grid.locator('input[name="goods_services:2027:budget"]')
        field.fill('140,00')
        grid.get_by_role('button', name='Tabloyu kaydet', exact=True).click()
        expect(page).to_have_url(base + '/program/1?period_id=1&group=service&fund=inside')
        db.expire_all()
        value = db.scalar(select(EconomicValue).where(EconomicValue.category == 'goods_services', EconomicValue.year == 2027, EconomicValue.funding_type == 'inside'))
        assert str(value.amount) == '140.00'


def test_stylesheet_is_loaded_only_for_program(client):
    assert '/static/design/report-preparation.css' in client.get('/program/1?period_id=1').text
    assert '/static/design/report-preparation.css' not in client.get('/department/1?period_id=1').text
