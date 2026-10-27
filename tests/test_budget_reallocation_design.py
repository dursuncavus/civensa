"""CIV-129: frozen templates, real budget APIs and synthetic browser evidence."""
from hashlib import sha256
from html.parser import HTMLParser
import os
from pathlib import Path
import re
from types import SimpleNamespace
from urllib.parse import urlsplit
from decimal import Decimal

import pytest
from playwright.sync_api import expect
from sqlalchemy import select
from app.models import BudgetOperation, BudgetOperationLine, Department, DepartmentScope

from tests.test_budget_reallocation import budget
from tests.test_released_permissions import actors, http
from tests.test_section_index_design import TEXT_PAIRS, contrast
from tests.test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/budget_reallocation_start'
HASHES = {
    'budget_index.html': '69104395a1e25fb9a6fdc89e903db1f9667e52dcf26e24401e89c1191a7b1bc6',
    'budget_wizard.html': 'd5973ff8ef37bd07858c078b1f64bda3fff05f2076772ad39f97cb68e7c012a4',
}
JS_CLASSES = {'leg', 'department', 'direction', 'input-mode', 'leg-amount', 'remove-leg',
              'category-choice', 'activity-choice', 'table-wrap'}
TITLE_CHANGES = {
    'Bütçe Aktarma': 'Bütçe aktarma',
    'Yeni Bütçe Aktarması': 'Yeni bütçe aktarması',
    '#9202 · İncele': 'Fen İşleri → Park ve Bahçeler ve 2 müdürlük daha · 5.000.000,00 TL',
    '#9201 · İncele': 'Fen İşleri → Park ve Bahçeler · 5.000.000,00 TL',
    '#9201 için telafi': 'Telafi: Başkanlık talimatı 01.10.2026 / 2026/123',
    '2026-10-01 / 2026/123': '01.10.2026 / 2026/123',
    '2026-10-02 / 2026/124': '02.10.2026 / 2026/124',
}


class Contract(HTMLParser):
    """Preserve hooks even inside template.content, field attributes and text order."""
    def __init__(self, html):
        super().__init__()
        self.hooks, self.controls, self.text = [], [], []
        self.suppressed = 0
        self.headers = []
        self.header = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'th':
            self.header = ''
        hooks = {k: v for k, v in attrs.items() if k == 'id' or k.startswith('data-')}
        classes = sorted(set(attrs.get('class', '').split()) & JS_CLASSES)
        # New table wrappers add accessibility/scroll containers, not JS bindings.
        if classes and classes != ['table-wrap']:
            hooks['js-classes'] = tuple(classes)
        if hooks:
            self.hooks.append((tag, tuple(sorted(hooks.items()))))
        if tag in {'a', 'input', 'select', 'option', 'textarea', 'button', 'script'}:
            self.controls.append((tag, tuple(sorted((k, v) for k, v in attrs.items()
                if k not in {'class', 'aria-label'}))))
        if tag in {'style', 'script'}:
            self.suppressed += 1

    def handle_endtag(self, tag):
        if tag == 'th':
            self.headers.append(' '.join(self.header.split()))
            self.header = None
        if tag in {'style', 'script'}:
            self.suppressed -= 1

    def handle_data(self, data):
        if self.header is not None:
            self.header += data
        if not self.suppressed and data.strip():
            text = ' '.join(data.split())
            self.text.append(TITLE_CHANGES.get(text, text))


def scenario(response, empty=False):
    context = dict(response.context)
    if response.template.name == 'budget_index.html':
        context['operations'] = [] if empty else [
            SimpleNamespace(id=9202, year=2027, reference_type='council_decision',
                reference_date='2026-10-02', reference_number='2026/124', reverses_id=9201),
            SimpleNamespace(id=9201, year=2027, reference_type='mayor_instruction',
                reference_date='2026-10-01', reference_number='2026/123', reverses_id=None),
        ]
        context['operation_labels'] = {
            9202: 'Fen İşleri → Park ve Bahçeler ve 2 müdürlük daha · 5.000.000,00 TL',
            9201: 'Fen İşleri → Park ve Bahçeler · 5.000.000,00 TL',
        }
        context['reversal_labels'] = {
            9202: 'Telafi: Başkanlık talimatı 01.10.2026 / 2026/123',
        }
    return context


def frozen_html(response, context):
    source = (FROZEN / response.template.name).read_bytes()
    assert sha256(source).hexdigest() == HASHES[response.template.name]
    return response.template.environment.from_string(source.decode()).render(context)


@pytest.mark.parametrize('screen,empty', [('budget_index.html', False), ('budget_index.html', True),
                                         ('budget_wizard.html', False)])
def test_frozen_contract(http, budget, screen, empty):
    client = http('strategy_director')
    response = client.get('/budget-reallocations' + ('/new' if 'wizard' in screen else ''))
    assert response.status_code == 200
    context = scenario(response, empty)
    old, new = Contract(frozen_html(response, context)), Contract(response.template.render(context))
    assert new.hooks == old.hooks
    assert new.controls == old.controls
    assert new.headers == old.headers
    # Includes every header (also the blank remove header), option, link and label.
    assert new.text == old.text
    assert 'budget-reallocation.css' not in client.get('/dashboard').text


def test_list_summaries_use_operation_lines_and_reference_not_ids(db, http, budget, actors):
    strategy_department = db.get(Department, actors['strategy_director'].department_id)
    departments = db.scalars(select(Department).where(
        Department.organization_id == strategy_department.organization_id).order_by(Department.id)).all()
    departments = departments[:3]
    names = ['Fen İşleri', 'Park ve Bahçeler', 'Temizlik İşleri']
    for department, name in zip(departments, names):
        department.name = name
        scope = db.scalar(select(DepartmentScope).where(
            DepartmentScope.period_id == budget['period_id'],
            DepartmentScope.department_id == department.id))
        if scope:
            scope.display_name = name
        else:
            db.add(DepartmentScope(period_id=budget['period_id'], department_id=department.id,
                display_name=name, status='required'))
    fourth = Department(organization_id=strategy_department.organization_id, name='Ulaşım Müdürlüğü')
    db.add(fourth)
    db.flush()
    participants = [*departments, fourth]

    def operation(reference_number, reverses_id=None):
        item = BudgetOperation(organization_id=strategy_department.organization_id,
            period_id=budget['period_id'], actor_id=actors['strategy_director'].id,
            reverses_id=reverses_id, year=budget['year'], value_kind='budget', phase='before_adoption',
            reference_type='mayor_instruction', reference_date='2026-10-01',
            reference_number=reference_number, reason='Sentetik test aktarımı.',
            request_json='{}', preview_json='{}')
        db.add(item)
        db.flush()
        return item

    def line(operation_id, department_id, before, after, index):
        db.add(BudgetOperationLine(operation_id=operation_id, department_id=department_id,
            value_table='economic_values', value_id=index, label='Test değeri', funding_type='inside',
            before=Decimal(before), after=Decimal(after), before_json='{}', after_json='{}'))

    two_leg = operation('2026/123')
    line(two_leg.id, departments[0].id, '5000000', '0', 1)
    line(two_leg.id, departments[1].id, '0', '5000000', 2)
    four_leg = operation('2026/124', two_leg.id)
    line(four_leg.id, participants[0].id, '2500000', '0', 3)
    line(four_leg.id, participants[1].id, '2500000', '0', 4)
    line(four_leg.id, participants[2].id, '0', '2500000', 5)
    line(four_leg.id, participants[3].id, '0', '2500000', 6)
    db.commit()

    client = http('strategy_director')
    response = client.get('/budget-reallocations')
    assert response.status_code == 200
    visible = ' '.join(Contract(response.text).text)
    assert 'Fen İşleri → Park ve Bahçeler · 5.000.000,00 TL' in visible
    assert 'Fen İşleri → Temizlik İşleri ve 2 müdürlük daha · 5.000.000,00 TL' in visible
    assert '02.10.2026 / 2026/124' in visible
    assert 'Telafi: Başkanlık talimatı 01.10.2026 / 2026/123' in visible
    assert not re.search(r'#\d+', visible)


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('version', ['before', 'after'])
def test_browser_evidence_and_contract(browser, http, budget, width, version):
    client = http('strategy_director')
    errors, calls, pairs = [], [], set()
    document = None
    with browser.new_context(viewport={'width': width, 'height': 1050}) as context:
        def serve(route):
            request = route.request
            path = urlsplit(request.url).path
            if request.method != 'GET':
                calls.append((path, request.post_data_json))
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type': request.headers.get('content-type', ''),
                         'X-CSRF-Token': request.headers.get('x-csrf-token', '')}, follow_redirects=True)
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers,
                body=document if document and path in {'/budget-reallocations', '/budget-reallocations/new'} else response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))

        def render(path, empty=False):
            nonlocal document
            response = client.get(path)
            assert response.status_code == 200
            data = scenario(response, empty)
            document = frozen_html(response, data) if version == 'before' else response.template.render(data)
            page.goto('http://testserver' + path)
            page.evaluate('document.fonts.ready')

        def check():
            if version == 'before':
                return
            assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
            if (width == 1440 and page.url.endswith('/budget-reallocations')
                    and page.locator('.budget-operation-list tbody tr').count() == 2):
                headers = page.locator('.budget-operation-list th').evaluate_all(
                    'els => els.map(el => el.getBoundingClientRect().width)')
                assert headers[0] > max(headers[1:])
                expect(page.locator('.budget-operation-list tbody tr:not(:last-child) td:nth-child(2)')).to_have_css(
                    'white-space', 'nowrap')
            root = page.locator('.budget-reallocation-page')
            assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
            pairs.update(map(tuple, page.evaluate(TEXT_PAIRS.replace('.section-index-page', '.budget-reallocation-page').replace("el.matches('select')", "el.matches('select,input,textarea')"))))
            # D-292: all prose, checkbox rows and summary blocks stay compact.
            for row in root.locator('p, label, #preview-result > div:not(.table-wrap)').all():
                if row.is_visible() and not row.locator('xpath=ancestor::table').count():
                    assert row.bounding_box()['width'] <= 44 * 16 + 1

        def capture(name):
            folder = os.getenv('CIVENSA_CIV138_SCREENSHOTS')
            if not name.startswith('017-rows'):
                return
            if folder:
                target = Path(folder)
                target.mkdir(parents=True, exist_ok=True)
                page.evaluate('document.activeElement.blur()')
                page.mouse.move(0, 0)
                page.screenshot(path=str(target / f'{version}-{name}-{width}.png'), full_page=True)

        for empty in (False, True):
            render('/budget-reallocations', empty)
            check()
            expect(page.locator('tbody tr')).to_have_count(1 if empty else 2)
            if version == 'after' and width == 390:
                wrap = page.locator('.budget-reallocation-page .table-wrap')
                assert wrap.evaluate('el => el.scrollWidth > el.clientWidth')
                wrap.focus()
                page.keyboard.press('ArrowRight')
                expect(wrap).to_be_visible()
                wrap.evaluate('el => el.scrollLeft = 0')
            if not empty:
                if version == 'after':
                    listing = page.locator('.budget-reallocation-page')
                    expect(listing.get_by_role('link', name='Fen İşleri → Park ve Bahçeler · 5.000.000,00 TL')).to_be_visible()
                    expect(listing.get_by_role('link', name='Fen İşleri → Park ve Bahçeler ve 2 müdürlük daha · 5.000.000,00 TL')).to_be_visible()
                    expect(listing.get_by_role('link', name='Telafi: Başkanlık talimatı 01.10.2026 / 2026/123')).to_have_attribute(
                        'href', '/budget-reallocations/9201')
                    assert '#9201' not in listing.inner_text() and '#9202' not in listing.inner_text()
                else:
                    expect(page.get_by_role('link', name='#9201 için telafi')).to_have_attribute(
                        'href', '/budget-reallocations/9201')
            capture('017-empty' if empty else '017-rows')
        render('/budget-reallocations/new')
        expect(page.locator('#budget-error')).to_be_hidden()
        expect(page.locator('.leg')).to_have_count(2)
        if version == 'after':
            fields = page.locator('.form-grid').first.locator('label').all()
            boxes = [field.bounding_box() for field in fields]
            if width == 1440:
                assert len({box['y'] for box in boxes}) == 1
            else:
                assert len({box['x'] for box in boxes}) == 1
                assert len({box['y'] for box in boxes}) == 3
        check()
        capture('018-step1')
        if version == 'after':
            page.locator('#preview-button').click()
            expect(page.locator('#budget-error')).to_be_visible()
            expect(page.locator('#budget-error')).to_have_attribute('role', 'alert')
            check()
            for _ in range(3):
                page.locator('#add-leg').click()
            expect(page.locator('.leg')).to_have_count(5)
            check()
            assert page.locator('.leg .leg-amount').evaluate_all(
                'els => new Set(els.map(el => getComputedStyle(el).borderColor)).size === 1')
            for _ in range(3):
                page.locator('.remove-leg').last.click()
        for index, leg in enumerate(budget['legs']):
            row = page.locator('.leg').nth(index)
            row.locator('.department').select_option(str(leg['department_id']))
            row.locator('.direction').select_option(leg['direction'])
            row.locator('.leg-amount').fill('5.000.000,00')
        page.locator('#preview-button').click()
        expect(page.locator('#preview-result')).to_contain_text('5.000.000,00')
        expect(page.locator('#budget-error')).to_be_hidden()
        check()
        page.locator('#preview-section').scroll_into_view_if_needed()
        capture('018-preview')
        page.locator('#eligible-choices summary').first.click()
        check()
        choice = page.locator('.category-choice').first
        choice.uncheck()
        page.locator('#refresh-preview').click()
        expect(page.locator('#preview-result table')).to_be_visible()
        assert calls[-1][1]['legs'][0]['excluded_categories'] == [choice.get_attribute('value')]
        page.locator('#continue-reference').click()
        expect(page.locator('#reference-section')).to_be_visible()
        check()
        page.locator('#phase').select_option('after_adoption')
        expect(page.locator('#reference-label')).to_have_value('Meclis kararı')
        page.locator('#reference-date').fill('2026-10-01')
        page.locator('#reference-number').fill('2026/123')
        page.locator('#reason').fill('Sentetik yatırım öncelikleri doğrultusunda ödenek aktarımı.')
        if version == 'after':
            for control in page.locator('.budget-reallocation-page a, .budget-reallocation-page button, .budget-reallocation-page summary, .budget-reallocation-page input, .budget-reallocation-page select, .budget-reallocation-page textarea').all():
                if control.is_visible() and control.is_enabled():
                    control.hover()
                    control.focus()
                    check()
            assert pairs
            assert all(contrast(pair) >= 4.5 for pair in pairs), [(p, contrast(p)) for p in pairs if contrast(p) < 4.5]
        page.locator('#apply-button').click()
        expect(page).to_have_url('http://testserver/budget-reallocations/1')
        expect(page.get_by_role('heading', name='Bütçe Aktarması #1')).to_be_visible()
        assert [path for path, _ in calls] == [
            '/api/budget-reallocations/choices', '/api/budget-reallocations/preview',
            '/api/budget-reallocations/choices', '/api/budget-reallocations/preview',
            '/api/budget-reallocations/apply']
        assert not errors
