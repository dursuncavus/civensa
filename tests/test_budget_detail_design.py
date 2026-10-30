"""CIV-154: frozen detail contract and the real reversal flow on local PostgreSQL."""
from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
from collections import Counter
import os
from pathlib import Path
import re
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect
from sqlalchemy import select

from app.models import BudgetOperation
from tests.test_budget_reallocation import budget, preview, apply, reference
from tests.test_released_permissions import actors, http
from tests.test_section_index_design import TEXT_PAIRS, contrast
from tests.test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/budget_detail_start/budget_detail.html'
FROZEN_SHA256 = '16dcea388838089d966de4fbbaea171defaf219ad58f5fac0e3aeba3a1975a12'


class Contract(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.hooks, self.controls, self.text = [], [], []
        self.main = False
        self.suppressed = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'main':
            self.main = True
        hooks = {key: value for key, value in attrs.items()
                 if key in {'id', 'role', 'hidden'} or key.startswith(('data-', 'aria-'))}
        if hooks:
            self.hooks.append((tag, tuple(sorted(hooks.items()))))
        if tag in {'a', 'button', 'input', 'select', 'option', 'textarea', 'script'}:
            self.controls.append((tag, tuple(sorted(attrs.items()))))
        if tag in {'script', 'style'}:
            self.suppressed += 1

    def handle_endtag(self, tag):
        if tag == 'main':
            self.main = False
        if tag in {'script', 'style'}:
            self.suppressed -= 1

    def handle_data(self, data):
        if self.main and not self.suppressed and data.strip():
            self.text.append(' '.join(data.split()))

    @property
    def money(self):
        return re.findall(r'-?\d+(?:\.\d{3})*,\d{2}', ' '.join(self.text))

    @property
    def prose(self):
        # The list link moves above the panel. Only decorative summary separators
        # disappear when their label/value pairs become separate rows.
        return ' '.join(' '.join(self.text).replace('İşlem listesi', '').replace(' · ', ' ').split())


@pytest.fixture
def recorded(http, budget):
    client = http('strategy_director')
    response = apply(client, preview(client, budget))
    assert response.status_code == 200, response.text
    response = client.get(f"/budget-reallocations/{response.json()['id']}")
    assert response.status_code == 200
    return client, response


def scenario(response, phase='after_adoption', delegated=True, state='normal', results='shorter'):
    data = dict(response.context)
    operation = data['operation']
    data['operation'] = SimpleNamespace(**{
        key: getattr(operation, key) for key in
        ('id', 'year', 'reference_type', 'reference_date', 'reference_number', 'reason')
    }, phase=phase, delegation_id=73 if delegated else None,
        reverses_id=9000 if state == 'reversal' else None, created_at='2026-10-29 12:30:00')
    data['actor'] = SimpleNamespace(full_name='Sentetik Strateji Kullanıcısı', position='director')
    data['reference_request'] = deepcopy(data['reference_request'])
    data['reference_request'].update(change_total=delegated, change_outside=phase == 'after_adoption')
    # One leg with exclusions and one without the optional keys.
    data['reference_request']['legs'][0].update(excluded_categories=['capital'], excluded_activities=[91, 92])
    for key in ('excluded_categories', 'excluded_activities'):
        data['reference_request']['legs'][1].pop(key, None)
    data['preview'] = deepcopy(data['preview'])
    summaries = data['preview']['summaries']
    for summary, name in zip(summaries, ['Fen İşleri Müdürlüğü', 'Park ve Bahçeler Müdürlüğü']):
        summary['name'] = name
    data['department_names'] = dict(data['department_names'])
    data['department_names'].update({s['department_id']: s['name'] for s in summaries})
    summaries[0]['source_difference'] = '-12500.23'
    summaries[1]['outside_change'] = '12500.23'
    data['preview']['warnings'] = ['Sentetik uyarı: mevcut ekonomik/faaliyet farkı korunur.']
    data['preview']['department_results'] = [dict(name=s['name'], after='12345678.90', percent='3.25')
        for s in summaries[:1 if results == 'shorter' else len(summaries)]]
    if results == 'absent':
        data['preview'].pop('department_results')
    data['reversal'] = SimpleNamespace(id=9002) if state == 'reversed' else None
    return data


def frozen_html(response, data):
    source = FROZEN.read_bytes()
    assert sha256(source).hexdigest() == FROZEN_SHA256
    return response.template.environment.from_string(source.decode()).render(data)


def test_shared_styles_are_append_only_and_detail_scoped():
    css = Path('app/static/design/budget-reallocation.css').read_bytes()
    assert sha256(css[:6710]).hexdigest() == 'ed185906cc4de64090151230b038fe2a6eb91fb50d9881b6dc0e15ef55b01ca2'
    appended = re.sub(r'/\*.*?\*/', '', css[6710:].decode(), flags=re.S)
    selectors = re.findall(r'([^{}]+)\{', appended)
    assert selectors
    assert all(selector.strip().startswith('.budget-detail-page ') for selector in selectors)


@pytest.mark.parametrize('phase', ['before_adoption', 'after_adoption'])
@pytest.mark.parametrize('delegated', [False, True])
@pytest.mark.parametrize('state', ['normal', 'reversal', 'reversed'])
@pytest.mark.parametrize('results', ['absent', 'equal', 'shorter'])
def test_frozen_contract(recorded, phase, delegated, state, results):
    _, response = recorded
    data = scenario(response, phase, delegated, state, results)
    old = Contract(frozen_html(response, data))
    new = Contract(response.template.render(data))
    assert Counter(new.hooks) == Counter(old.hooks)
    assert Counter(new.controls) == Counter(old.controls)
    assert new.money == old.money
    assert new.prose == old.prose
    source = Path('app/templates/budget_detail.html').read_text()
    assert source.count("{% include 'budget_reference.html' %}") == 1
    assert FROZEN.read_text().count("{% include 'budget_reference.html' %}") == 1


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('version', ['before', 'after'])
def test_browser_reversal_evidence_and_layout(browser, recorded, db, width, version):
    client, response = recorded
    oid = response.context['operation'].id
    document = None
    errors, calls, pairs = [], [], set()
    minimum_contrast = 100.0
    with browser.new_context(viewport={'width': width, 'height': 1050}) as context:
        def serve(route):
            request = route.request
            path = urlsplit(request.url).path
            if request.method != 'GET':
                calls.append((path, request.post_data_json))
            result = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type': request.headers.get('content-type', ''),
                         'X-CSRF-Token': request.headers.get('x-csrf-token', '')}, follow_redirects=True)
            headers = dict(result.headers)
            headers.pop('set-cookie', None)
            body = document if document and path == f'/budget-reallocations/{oid}' else result.content
            route.fulfill(status=result.status_code, headers=headers, body=body)

        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))

        def render(state='normal'):
            nonlocal document
            data = scenario(response, state=state)
            document = frozen_html(response, data) if version == 'before' else response.template.render(data)
            page.goto(f'http://testserver/budget-reallocations/{oid}')
            page.evaluate('document.fonts.ready')

        def check():
            if version == 'before':
                return
            assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
            root = page.locator('.budget-detail-page')
            assert root.locator('*').evaluate_all(
                "els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
            for row in root.locator('p, label, .detail-facts, .department-summaries, .selection-disclosure').all():
                if row.is_visible():
                    assert row.bounding_box()['width'] <= 44 * 16 + 1
            pairs.update(map(tuple, page.evaluate(TEXT_PAIRS.replace('.section-index-page', '.budget-detail-page')
                .replace("el.matches('select')", "el.matches('select,input,textarea')"))))
            assert page.locator('.money-facts dd, td:nth-child(n+4)').evaluate_all(
                "els => els.every(el => getComputedStyle(el).textAlign === 'right' && getComputedStyle(el).fontVariantNumeric === 'tabular-nums')")
            if width == 390:
                assert page.locator('.budget-detail-page .table-wrap').evaluate('el => el.scrollWidth > el.clientWidth')
            boxes = page.locator('#reversal-section label').evaluate_all('els => els.map(el => el.getBoundingClientRect().x)')
            assert len(set(boxes)) <= 1

        def capture(state):
            folder = os.getenv('CIVENSA_CIV154_SCREENSHOTS')
            if folder:
                target = Path(folder)
                target.mkdir(parents=True, exist_ok=True)
                page.evaluate('document.activeElement.blur()')
                page.mouse.move(0, 0)
                path = target / f'{version}-{state}-{width}.png'
                page.screenshot(path=str(path), full_page=True)
                assert path.stat().st_size <= 1_500_000

        render()
        expect(page.locator('#budget-error')).to_be_hidden()
        expect(page.locator('#reverse-button')).to_have_class('button danger')
        expect(page.locator('#reference-label')).to_have_value('Meclis kararı')
        check()
        capture('operation')
        page.get_by_text('Kaydedilen uygun kayıt seçimleri', exact=True).click()
        expect(page.get_by_text('Çıkarılan faaliyet kimlikleri: 91, 92', exact=False)).to_be_visible()
        check()
        page.get_by_text('Kaydedilen uygun kayıt seçimleri', exact=True).click()
        # Exercise existing client validation before making the real request.
        page.locator('#reverse-button').click()
        expect(page.locator('#budget-error')).to_have_text(
            'Dayanak tarihi, sayısı ve gerekçe zorunlu. Eksik alanları tamamlayın.')
        assert calls == []
        page.locator('#phase').select_option('before_adoption')
        expect(page.locator('#reference-label')).to_have_value('Başkanlık talimatı')
        page.locator('#phase').select_option('after_adoption')
        expect(page.locator('#reference-label')).to_have_value('Meclis kararı')
        page.locator('#reference-date').fill('2026-10-29')
        page.locator('#reference-number').fill('SENTETIK/154')
        page.locator('#reason').fill('Sentetik test geri alma gerekçesi.')
        # Browser sends a valid form with an invalid enum: the unchanged server
        # returns the message which budget.js must show verbatim.
        page.locator('#phase').evaluate("el => el.add(new Option('Sentetik test', 'invalid'))")
        page.locator('#phase').select_option('invalid')
        expected_error = client.post(f'/api/budget-reallocations/{oid}/reverse', json=reference(
            phase='invalid', reference_type='council_decision', transfer_scope='other',
            reference_date='2026-10-29', reference_number='SENTETIK/154', reason='Sentetik test geri alma gerekçesi.'))
        assert expected_error.status_code == 422
        page.locator('#reverse-button').click()
        expect(page.locator('#budget-error')).to_have_text(expected_error.json()['detail'])
        expect(page.locator('#reverse-button')).to_be_enabled()
        check()
        # Return to a real option before collecting the evidence.
        page.locator('#phase').select_option('after_adoption')
        page.locator('#phase').evaluate("el => el.querySelector('option[value=invalid]').remove()")
        capture('error')
        if version == 'after':
            for control in page.locator('.budget-detail-page a, .budget-detail-page button, .budget-detail-page summary, .budget-detail-page input, .budget-detail-page select, .budget-detail-page textarea').all():
                if control.is_visible() and control.is_enabled():
                    control.hover()
                    check()
                    control.focus()
                    check()
            assert pairs
            minimum_contrast = min(contrast(pair) for pair in pairs)
            assert minimum_contrast >= 4.5, [(pair, contrast(pair)) for pair in pairs if contrast(pair) < 4.5]
        # Submit through budget.js and the real API; the new operation is loaded.
        page.locator('#reverse-button').click()
        expect(page).to_have_url(f'http://testserver/budget-reallocations/{oid + 1}')
        expect(page.get_by_role('heading', name=f'Bütçe Aktarması #{oid + 1}')).to_be_visible()
        expect(page.get_by_role('link', name=f'#{oid} numaralı işlemin geri alınması')).to_be_visible()
        assert db.scalar(select(BudgetOperation).where(BudgetOperation.reverses_id == oid)) is not None
        assert [path for path, _ in calls] == [f'/api/budget-reallocations/{oid}/reverse'] * 2
        assert calls[-1][1] == reference(phase='after_adoption', transfer_scope='other',
            reference_type='council_decision', reference_date='2026-10-29',
            reference_number='SENTETIK/154', reason='Sentetik test geri alma gerekçesi.')
        render('reversed')
        expect(page.get_by_text('Bu işlem geri alındı.', exact=False)).to_be_visible()
        expect(page.locator('#reversal-section')).to_have_count(0)
        expect(page.locator('#reverse-button')).to_have_count(0)
        check()
        capture('reversed')
        assert not errors, errors
        if version == 'after':
            print(f'CIV-154 {width}px minimum text contrast: {minimum_contrast:.2f}:1')
