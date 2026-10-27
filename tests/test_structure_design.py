"""CIV-131: frozen form contracts, real browser flows and synthetic evidence."""
from datetime import date, datetime
from hashlib import sha256
import os
from pathlib import Path
from types import SimpleNamespace as Record

from jinja2 import ChoiceLoader, DictLoader
from playwright.sync_api import expect
import pytest

from app.models import Department, Organization, Program, ReportingPeriod, SubProgram
from test_ic_our_actions_design import VisibleText
from test_live_pilot_hardening import live_client, login
from test_master_data_ui import route_to_client
from test_section_index_design import Contract, TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FIXTURES = Path(__file__).parent / 'fixtures'
HASHES = {
    'structure': '3677cdd7e7598d9e156d1614e48f67b2fc5a49c519c87bb9803d07d8568b6ab5',
    'structure_wizard': '9331e00d8404d35c88c79af1486961bea3493049c8ca755a71d611a3677cb3cf',
}
TEXT_CHANGES = {
    'Kurum Yapısı': 'Kurum yapısı',
    'Döneme Ait Yapı': 'Döneme ait yapı',
    'Alt Program Oluştur': 'Alt program oluştur',
    'Müdürlük / Kayıt Adı düzenle Durum': 'Müdürlük Durum',
}


class StructureContract(Contract):
    """Order/bindings, every control attribute, raw textarea values and disclosure state."""
    def __init__(self, html):
        self.hidden_inputs = []
        self.disclosures = []
        self.textareas = []
        self.textarea = None
        self.hooks = []
        super().__init__(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'button':
            attrs = dict(attrs)
            if attrs.get('role') == 'switch':
                attrs = [(name, value) for name, value in attrs.items()
                    if name not in {'role', 'aria-checked', 'aria-label'}]
        super().handle_starttag(tag, attrs)
        if not self.main:
            return
        attrs = dict(attrs)
        if tag == 'input' and attrs.get('type') == 'hidden':
            self.hidden_inputs.append((self.form, tuple(sorted(attrs.items()))))
        if tag == 'details':
            self.disclosures.append(tuple(sorted((k, v) for k, v in attrs.items() if k != 'class')))
        hooks = {k: v for k, v in attrs.items() if k == 'id' or k.startswith('data-')}
        if tag == 'fieldset':
            hooks['hidden'] = 'hidden' in attrs
        if hooks:
            self.hooks.append((tag, tuple(sorted(hooks.items()))))
        if tag == 'textarea':
            self.textarea = []

    def handle_data(self, data):
        super().handle_data(data + ' ')
        if self.textarea is not None:
            self.textarea.append(data)

    def handle_endtag(self, tag):
        if tag == 'textarea':
            self.textareas.append(''.join(self.textarea))
            self.textarea = None
        super().handle_endtag(tag)


def frozen_environment(response):
    sources = {}
    for name, digest in HASHES.items():
        data = (FIXTURES / f'{name}_start.html').read_bytes()
        assert sha256(data).hexdigest() == digest
        sources[f'{name}.html'] = data.decode()
    env = response.template.environment
    return env.overlay(loader=ChoiceLoader([DictLoader(sources), env.loader]))


def render(response, context=None, *, before=False):
    context = context or response.context
    context['request'].state.pp_attempt_rendered = False
    template = frozen_environment(response).get_template('structure.html') if before else response.template
    return template.render(context)


def assert_frozen(response, context=None):
    context = context or response.context
    actual, old = render(response, context), render(response, context, before=True)
    current, starting = StructureContract(actual), StructureContract(old)
    assert current.controls == starting.controls
    assert current.bindings == starting.bindings
    assert current.hidden_inputs == starting.hidden_inputs
    expected_labels = [
        (kind, {'Pasifleştir': 'Etkin', 'Etkinleştir': 'Pasif'}.get(label, label)
            if kind == 'button' else label)
        for kind, label in starting.labels
    ]
    assert current.labels == expected_labels
    assert current.textareas == starting.textareas
    assert current.disclosures == starting.disclosures
    assert current.hooks == starting.hooks
    # Keep the frozen form content except for the approved table and status wording.
    expected = VisibleText(old).normalized()
    for a, b in TEXT_CHANGES.items():
        expected = expected.replace(a, b, 1)
    for d in context['departments']:
        state = 'Etkin' if d.is_active else 'Pasif'
        toggle = 'Pasifleştir' if d.is_active else 'Etkinleştir'
        name, organization = ' '.join(d.name.split()), ' '.join(d.organization.name.split())
        before = f'{name} #{d.id} · {organization} {name} yeni adı Adı kaydet {state} {toggle}'
        after = f'{name} yeni adı Adı kaydet #{d.id} · {organization} {state}'
        assert expected.count(before) == 1
        expected = expected.replace(before, after, 1)
    assert VisibleText(actual).normalized() == expected
    assert actual.count('name="csrf_token"') == actual.count('<form method="post"')
    return actual


@pytest.fixture
def structure_client(db, sample, live_client):
    org = Organization(name='İkinci Sentetik Belediyesi')
    db.add(org)
    db.flush()
    db.add_all([
        Department(organization_id=org.id, name='Park ve Bahçeler Müdürlüğü'),
        Department(organization_id=org.id, name='Park  ve Bahçeler Müdürlüğü', is_active=False),
        ReportingPeriod(year=2028, status='draft'),
        Program(period_id=sample['period'].id, name='İkinci Sentetik Program'),
    ])
    sample['subprogram'].rationale = 'Sentetik gerekçe\nİkinci satır'
    sample['subprogram'].goal = 'Sentetik hedef'
    db.add(SubProgram(period_id=sample['period'].id, program_id=sample['subprogram'].program_id,
        name='İkinci Sentetik Alt Program', rationale='Başka gerekçe', goal='Başka hedef'))
    db.commit()
    client = live_client()
    login(client, sample['strategy'].email)
    return client


def historical_context(response):
    context = dict(response.context)
    d = context['departments'][0]
    c = Record(id=901, change_type='RENAMED', effective_date=date(2027, 1, 1),
        council_decision_no='2026/48', note='Sentetik karar gerekçesi', created_by=1,
        created_at=datetime(2026, 12, 20, 9, 30))
    context.update(structure_changes=[c], copied_periods={901: [902]},
        change_links={901: [Record(from_department_id=d.id, to_department_id=d.id)]},
        change_transfers={901: [Record(indicator_id=None, activity_id=903, official_activity_id=None,
            from_department_id=d.id, to_department_id=d.id, note='Sentetik aktarım notu')]},
        account_warnings=[Record(department_id=d.id, full_name='Sentetik Kullanıcı', email='test@example.invalid')],
        untransferred=[Record(kind='activity', id=903, name='Sentetik aktarılmamış iş', department_id=d.id)])
    inactive = next(d for d in context['departments'] if not d.is_active)
    context['assigned'] = {sp.id: ([inactive.id] if index == 0 else [])
        for index, sp in enumerate(context['subprograms'])}
    return context


@pytest.mark.parametrize('state', ['no-period', 'empty-period', 'populated', 'duplicates', 'history', 'cancelled'])
def test_frozen_states_forms_links_and_disclosures(structure_client, state):
    response = structure_client.get('/structure')
    assert response.status_code == 200
    context = historical_context(response)
    if state == 'no-period':
        context.update(period=None, periods=[], programs=[], subprograms=[], scopes={}, profiles={}, work_items=[])
    elif state == 'empty-period':
        context.update(programs=[], subprograms=[])
    elif state != 'duplicates':
        context['duplicates'] = []
    if state == 'cancelled':
        context['cancellations'] = {901: Record(note='Sentetik iptal nedeni', created_by=1,
            created_at=datetime(2026, 12, 21, 10, 30))}
    assert_frozen(response, context)
    assert 'structure.css' not in structure_client.get('/dashboard').text


@pytest.mark.parametrize('kind', ['department-create', 'department-rename', 'active', 'program-create',
    'program-rename', 'subprogram-create', 'subprogram-rename', 'responsibilities', 'scope', 'wizard', 'cancel'])
def test_frozen_failed_save_attempts_selections_and_open_details(structure_client, kind):
    response = structure_client.get('/structure')
    context = historical_context(response)
    d, p, sp = context['departments'][0], context['programs'][0], context['subprograms'][0]
    action = {
        'department-create': '/structure/departments',
        'department-rename': f'/structure/departments/{d.id}/rename',
        'active': f'/structure/departments/{d.id}/active',
        'program-create': '/structure/programs', 'program-rename': f'/structure/programs/{p.id}',
        'subprogram-create': '/structure/subprograms', 'subprogram-rename': f'/structure/subprograms/{sp.id}',
        'responsibilities': f'/structure/subprograms/{sp.id}/responsibilities',
        'scope': '/structure/scopes', 'wizard': '/structure/changes', 'cancel': '/structure/changes/901/cancel',
    }[kind]
    context.update(attempted_action=action, error='Sentetik kayıt kaydedilemedi. İlgili alanı düzeltin.', attempted={
        'organization_id': str(context['organizations'][-1].id), 'name': '  Denenen <ad> & değer  ',
        'program_id': str(context['programs'][-1].id), 'rationale': '  İlk satır\nİkinci satır  ', 'goal': '  Hedef  ',
        'department_id': str(d.id), 'department_ids': [str(d.id)], 'status': 'excluded',
        'display_name': '  Dönemdeki ad  ', 'budget_code': '01.02', 'active_from': '2027-03-01',
        'active_to': '2027-12-31', 'reason': '  Kapsam gerekçesi\nİkinci satır  ', 'change_type': 'SPLIT',
        'effective_date': '2027-06-01', 'council_decision_no': '2027/48', 'council_decision_date': '2027-05-01',
        'note': '  Karar notu  ', 'from_department_ids': [str(d.id)], 'to_department_ids': [str(d.id)],
        'new_name': '  Yeni ad  ', 'new_names': 'İlk ad\nİkinci ad', 'transfer_note': '  Aktarım notu  ',
        **{f'transfer_{item["key"]}': str(d.id) for item in context['work_items']},
    })
    html = assert_frozen(response, context)
    assert 'role="alert"' in html
    if kind in {'subprogram-rename', 'responsibilities'}:
        assert sum('open' in dict(attrs) for attrs in StructureContract(html).disclosures) == 1


def test_department_table_has_two_columns_and_empty_state(structure_client):
    response = structure_client.get('/structure')
    context = dict(response.context)
    context['departments'] = []
    html = assert_frozen(response, context)
    assert '<th>Müdürlük</th>' in html
    assert '<th>Durum</th>' in html
    assert '<th>Adı düzenle</th>' not in html
    assert 'colspan="2">Henüz müdürlük yok.' in html


def capture(page, name, width):
    folder = os.getenv('CIVENSA_CIV131_SCREENSHOTS')
    if folder:
        target = Path(folder)
        target.mkdir(parents=True, exist_ok=True)
        page.evaluate('document.activeElement.blur(); window.scrollTo(0,0)')
        page.mouse.move(0, 0)
        page.screenshot(path=str(target / f'{name}-{width}.png'), full_page=True)


def assert_layout_and_contrast(page, root, width):
    assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
    assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
    assert root.locator('.structure-departments thead th').count() == 2
    pairs = set(map(tuple, page.evaluate(TEXT_PAIRS.replace('.section-index-page', '.structure-page'))))
    for control in root.locator('button, input:not([type=hidden]), select, textarea, summary, [tabindex]').all():
        if control.is_visible():
            control.hover()
            control.focus()
            pairs.update(map(tuple, page.evaluate(TEXT_PAIRS.replace('.section-index-page', '.structure-page'))))
    failures = [(pair, contrast(pair)) for pair in pairs if contrast(pair) < 4.5]
    assert not failures
    for locator in (root.locator('.section-head'), root.locator('.structure-program'), root.locator('details')):
        for item in locator.all():
            assert item.bounding_box()['width'] <= 704
    for form in root.locator('section > .structure-form').all():
        assert len(form.evaluate('el => getComputedStyle(el).gridTemplateColumns').split()) == (2 if width >= 1024 else 1)
    for form in root.locator('details[open] .structure-form').all():
        assert len(form.evaluate('el => getComputedStyle(el).gridTemplateColumns').split()) == 1
        for textarea in form.locator('textarea').all():
            assert abs(textarea.bounding_box()['width'] - textarea.locator('..').bounding_box()['width']) <= 1
    for row in root.locator('.structure-departments tbody tr').all():
        field, button = row.locator('input[name=name]'), row.get_by_role('button', name='Adı kaydet', exact=True)
        field_box, button_box = field.bounding_box(), button.bounding_box()
        assert abs(field_box['y'] + field_box['height'] - button_box['y'] - button_box['height']) <= 1
        assert row.locator('td').count() == 2
        assert row.locator('td').first.locator('b').count() == 0
        switch = row.get_by_role('switch')
        assert switch.count() == 1
        checked = switch.get_attribute('aria-checked')
        assert checked in {'true', 'false'}
        expect(switch).to_have_text('Etkin' if checked == 'true' else 'Pasif')
        assert switch.get_attribute('aria-label') == f'{field.input_value()} durumu'
        state_class = 'is-active' if checked == 'true' else 'is-inactive'
        assert switch.evaluate('(el, name) => el.classList.contains(name)', state_class)
    if width == 390:
        wrap = root.locator('.table-wrap').last
        assert wrap.evaluate('el => el.scrollWidth > el.clientWidth')
        wrap.focus()
        page.keyboard.press('ArrowRight')
        wrap.evaluate('el => el.scrollLeft = el.scrollWidth')
        assert wrap.evaluate('el => el.scrollLeft > 0')
        wrap.evaluate('el => el.scrollLeft = 0')


@pytest.mark.parametrize('width', [1440, 390])
def test_browser_layout_real_save_error_preservation_and_evidence(browser, structure_client, sample, width):
    client = structure_client
    sp = sample['subprogram']
    with browser.new_context(viewport={'width': width, 'height': 1000}) as context:
        context.set_default_timeout(5000)
        route_to_client(context, client)
        errors = []
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver/structure')
        page.evaluate('document.fonts.ready')
        root = page.locator('.structure-page')
        expect(root.locator('#structure-step-label')).to_have_text('1 / 6 · Değişiklik türü')
        details = root.locator(f'details:has(form[action="/structure/subprograms/{sp.id}"])')
        details.locator('summary').click()
        assert_layout_and_contrast(page, root, width)
        capture(page, 'after-structure', width)
        # Real duplicate save opens the affected disclosure and retains exact attempted textarea data.
        form = details.locator(f'form[action="/structure/subprograms/{sp.id}"]')
        form.get_by_label('Alt program adı', exact=True).fill('İkinci Sentetik Alt Program')
        form.locator('textarea[name=rationale]').fill('  Denenen gerekçe\nİkinci satır  ')
        form.locator('textarea[name=goal]').fill('  Denenen hedef  ')
        form.get_by_role('button', name='Alt programı kaydet', exact=True).click()
        expect(page.get_by_role('alert')).to_contain_text('kaydıyla aynı')
        expect(form.get_by_label('Alt program adı', exact=True)).to_have_value('İkinci Sentetik Alt Program')
        expect(form.locator('textarea[name=rationale]')).to_have_value('  Denenen gerekçe\nİkinci satır  ')
        expect(form.locator('textarea[name=goal]')).to_have_value('  Denenen hedef  ')
        assert details.get_attribute('open') is not None
        assert_layout_and_contrast(page, root, width)
        capture(page, 'after-error', width)
        # Before images render BOTH byte-identical starting templates with the same response context.
        response = client.get('/structure')
        start_context = dict(response.context)
        start_context.update(attempted_action=f'/structure/subprograms/{sp.id}', attempted={
            'name': 'İkinci Sentetik Alt Program', 'rationale': '  Denenen gerekçe\nİkinci satır  ',
            'goal': '  Denenen hedef  '})
        duplicate = client.post(f'/structure/subprograms/{sp.id}', data={
            'csrf_token': response.context['request'].session['csrf_token'], 'period_id': sample['period'].id,
            **start_context['attempted']})
        assert duplicate.status_code == 409
        assert_frozen(duplicate)
        before_html = render(duplicate, before=True)
        context.route('http://testserver/civ131-before-error', lambda route: route.fulfill(
            status=200, content_type='text/html; charset=utf-8', body=before_html))
        # Preserve /structure in request context so shared navigation and period links also match.
        page.goto('http://testserver/civ131-before-error')
        page.evaluate('document.fonts.ready')
        capture(page, 'before-error', width)
        before_html = render(response, before=True)
        context.route('http://testserver/civ131-before', lambda route: route.fulfill(
            status=200, content_type='text/html; charset=utf-8', body=before_html))
        page.goto('http://testserver/civ131-before')
        page.locator(f'details:has(form[action="/structure/subprograms/{sp.id}"]) summary').click()
        page.evaluate('document.fonts.ready')
        capture(page, 'before-structure', width)
        # A corrected save succeeds; department renaming, toggling and period selection use real handlers.
        page.goto('http://testserver/structure')
        details.locator('summary').click()
        form.get_by_label('Alt program adı', exact=True).fill('Düzeltilmiş sentetik alt program')
        form.get_by_role('button', name='Alt programı kaydet', exact=True).click()
        expect(root.locator('summary').filter(has_text='Düzeltilmiş sentetik alt program')).to_be_visible()
        row = root.locator(f'tr:has(input[id="dept-{sample["department"].id}"])')
        rename = row.locator('form').first
        rename.locator('[name=name]').fill('Yeni Sentetik Müdürlük')
        rename.get_by_role('button', name='Adı kaydet', exact=True).click()
        expect(row.locator('td').first.locator('input[name=name]')).to_have_value('Yeni Sentetik Müdürlük')
        toggle = row.get_by_role('switch')
        expect(toggle).to_have_attribute('aria-label', 'Yeni Sentetik Müdürlük durumu')
        toggle.click()
        expect(toggle).to_have_text('Pasif')
        expect(toggle).to_have_attribute('aria-checked', 'false')
        toggle.click()
        expect(toggle).to_have_text('Etkin')
        expect(toggle).to_have_attribute('aria-checked', 'true')
        select = root.locator('form[method=get]')
        select.locator('select[name=period_id]').select_option(label='2028')
        select.get_by_role('button', name='Göster', exact=True).click()
        expect(root.get_by_role('heading', name='2028 · Programlar')).to_be_visible()
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        assert not errors
