"""CIV-105: frozen department contracts and unchanged strategy rendering.

Fixtures are exact bytes from phase5 264c04b, including both shared partials.
All route and browser examples use disposable PostgreSQL and synthetic records.
"""
from collections import Counter
from datetime import date, datetime, timedelta
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from jinja2 import ChoiceLoader, DictLoader
import pytest
from starlette.datastructures import FormData

from app import internal_control_service as ic
from app import internal_control_monitoring_service as monitoring
from app.internal_control_monitoring_models import ICMonitoringBatch
from app.main import app, require_user, templates
from app.models import Department
from app.security import hash_password
from sqlalchemy import select
from test_activity_sections import login, PASSWORD
from test_internal_control import action_row, saved, workbook
from test_section_index_design import Contract, TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/ic_our_actions_start'
HASHES = {
    'our_actions': '8f145fb89ff0ed769fd4170f00a8455055101db6c7a4f6fc92657e537d2029ed',
    'monitoring_ours': 'd5640aca53de09429283077e72bdef36619278e873addd71634b6be560a30e90',
    'monitoring': '082e61029ab7bd3a48ad5e08a0f65644d89961ece64a10008963f5a1b2a3b90d',
    'monitoring_detail': '391a6253824fd36bab2a70608a6ba2526c5f39a734596e52bbcc156dce81794b',
    'monitoring_shared': '1f8118931a2aa0cc48da1b933d2f4d8982817fc7b7bc1169e00ce7c75e0dde23',
    'monitoring_notes': '7122a66ff3c0dde77dc0b17c154203eaeb431a05f80aaaa7837d34768702fd07',
}


class ScreenContract(Contract):
    def handle_data(self, data):
        super().handle_data(data + ' ')


class VisibleText(HTMLParser):
    """Freeze all content, including field values, help, notes and empty text."""
    def __init__(self, html):
        super().__init__()
        self.main = False
        self.style = False
        self.parts = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'main': self.main = True
        if tag == 'style': self.style = True

    def handle_endtag(self, tag):
        if tag == 'main': self.main = False
        if tag == 'style': self.style = False

    def handle_data(self, data):
        if self.main and not self.style: self.parts.append(data)

    def normalized(self):
        # Definition rows replace the old inline date separator. One copy edit.
        return ' '.join(' '.join(self.parts).replace(' · ', ' ').replace(
            'Çıktı / Sonuç:', 'Çıktı / sonuç:').split())


def synthetic_record(record):
    return SimpleNamespace(**{k: v for k, v in vars(record).items() if not k.startswith("_")})


def frozen_environment():
    sources = {}
    for name, digest in HASHES.items():
        data = (FROZEN / f'{name}.html').read_bytes()
        assert sha256(data).hexdigest() == digest
        sources[f'internal_control/{name}.html'] = data.decode()
    return templates.env.overlay(loader=ChoiceLoader([DictLoader(sources), templates.env.loader]))


def render_contract(response, context=None):
    assert response.status_code == 200
    context = dict(context or response.context)
    request = context['request']
    request.state.pp_attempt_rendered = False
    actual = response.template.render(context)
    request.state.pp_attempt_rendered = False
    expected = frozen_environment().get_template(response.template.name).render(context)
    new, old = ScreenContract(actual), ScreenContract(expected)
    assert new.controls == old.controls
    assert new.bindings == old.bindings
    assert Counter(new.labels) == Counter(old.labels)
    assert VisibleText(actual).normalized() == VisibleText(expected).normalized()
    # CSRF is not merely redacted: every rendered POST has the actual token.
    for html in (actual, expected):
        assert html.count('name="csrf_token"') == html.count('<form method="post"')
        if '<form method="post"' in html:
            assert f'name="csrf_token" value="{request.session["csrf_token"]}"' in html
    return actual


@pytest.fixture
def ic_client(client, db, sample):
    client.follow_redirects = False
    app.dependency_overrides.pop(require_user)
    for user in (sample['user'], sample['strategy']):
        user.password_hash = hash_password(PASSWORD)
    db.commit()
    login(client, sample['user'].email)
    return client


@pytest.fixture
def action_plan(db, sample):
    other = Department(organization_id=sample['department'].organization_id,
                       name='Sentetik Destek Müdürlüğü')
    db.add(other)
    db.commit()
    plan = saved(db, sample, workbook([
        action_row(**{'6': 'Sentetik etik eğitim programını değerlendirmek',
                      '12': 'Sentetik açıklama <korunur>.'}),
        action_row(**{'2': 'KOS1.2', '5': 'KOS1.2.1',
                      '6': 'Sentetik ortak eğitim için katkı sağlamak',
                      '7': other.name, '8': sample['department'].name}),
    ]))
    ic.activate_plan(db, sample['strategy'], plan.id)
    db.commit()
    return plan


@pytest.fixture
def open_period(db, sample, action_plan):
    period = monitoring.open_period(db, sample['strategy'], action_plan.id, 2027, 1,
                                    monitoring.today(db) + timedelta(days=1000))
    db.commit()
    return period


def test_no_plan_empty_and_department_visibility(ic_client, sample):
    response = ic_client.get('/internal-control/our-actions')
    assert response.template.name == 'internal_control/our_actions.html'
    html = render_contract(response)
    assert html.count('Bu bölümde eylem bulunmuyor.') == 2
    assert 'Henüz etkin bir İç Kontrol planı yok.' in html
    login(ic_client, sample['strategy'].email)
    assert ic_client.get('/internal-control/our-actions').status_code == 403


@pytest.mark.parametrize('filled', [True, False])
@pytest.mark.parametrize('history', [None, 9105])
def test_no_period_frozen_actions_counts_fallbacks_and_history(ic_client, action_plan, filled, history):
    response = ic_client.get('/internal-control/our-actions')
    context = dict(response.context, last_monitoring_period_id=history)
    if not filled:
        context.update(responsible=[], cooperating=[])
    else:
        action = synthetic_record(context['responsible'][0])
        action.start_raw = ''
        action.due_raw = ''
        context['responsible'] = [action]
    html = render_contract(response, context)
    assert ('?period_id=9105' in html) == bool(history)
    assert html.count('Bu bölümde eylem bulunmuyor.') == (0 if filled else 2)
    assert ('Belirtilmedi' in html) == filled
    assert ('&lt;korunur&gt;' in html) == filled


@pytest.mark.parametrize('status', ['draft', 'returned', 'submitted', 'approved', 'closed', 'expired', 'empty'])
@pytest.mark.parametrize('sender', ['staff', 'authorized', 'director'])
def test_monitoring_frozen_forms_fields_values_options_and_readonly(ic_client, open_period, status, sender):
    response = ic_client.get('/internal-control/our-actions')
    context = scenario_context(response, status)
    user = synthetic_record(context['user'])
    user.position = 'director' if sender == 'director' else 'staff'
    user.can_submit = sender == 'authorized'
    context['user'] = user
    html = render_contract(response, context)
    controls = ScreenContract(html).controls
    posts = [dict(attrs)['action'] for tag, attrs in controls
             if tag == 'form' and dict(attrs).get('method') == 'post']
    assert any(url.endswith('/entry') for url in posts) == (status in {'draft', 'returned'})
    # The starting macro still offers submission after the deadline; preserve
    # that control while keeping entry and note editing disabled.
    assert any(url.endswith('/transition') for url in posts) == (
        status in {'draft', 'returned', 'expired'} and sender != 'staff')
    assert any(url.endswith('/notes') for url in posts) == (status not in {'closed', 'expired', 'empty'})
    if status in {'closed', 'empty'}: assert not posts
    assert ('Bu dönemde sorumlu eyleminiz bulunmuyor.' in html) == (status == 'empty')
    assert ('İşbirliği görevi bulunmuyor.' in html) == (status == 'empty')
    options = [dict(attrs) for tag, attrs in controls if tag == 'option']
    assert options[0]['value'] == '9105' and 'selected' not in options[0]
    assert options[1]['value'] == str(open_period.id) and 'selected' in options[1]


def scenario_context(response, scenario):
    """Presentation states use the real route context, without changing database rows."""
    context = dict(response.context)
    if scenario in {'no-period-actions', 'no-period-empty'}:
        if scenario.endswith('empty'): context.update(responsible=[], cooperating=[], plan=None)
        return context
    period = synthetic_record(context['monitoring_period'])
    detail = dict(context['details'][0])
    detail['rows'] = [dict(detail['rows'][0])]
    detail['rows'][0]['entry'] = SimpleNamespace(status='ongoing', percentage=0,
        explanation='Sentetik eğitim hazırlığı sürüyor.', reason='', evidence='Sentetik EBYS 2027/105')
    detail['status'] = scenario if scenario in {'draft', 'returned', 'submitted', 'approved'} else 'draft'
    detail['editable'] = scenario in {'draft', 'returned', 'open-error'}
    if scenario == 'closed': period.closed_at = datetime(2026, 10, 26, 9)
    if scenario == 'expired': period.deadline = date(2000, 1, 1)
    context.update(monitoring_period=period, details=[detail],
                   note_editable=scenario not in {'closed', 'expired', 'empty'},
                   periods=[SimpleNamespace(id=9105, year=2026, half=2, closed_at=datetime(2026, 10, 26)), period])
    context['notes'] = [SimpleNamespace(action_id=context['cooperating'][0].id,
        content='Sentetik işbirliği katkısı <korunur>.', actor_name='Sentetik Katkı Personeli',
        created_at=datetime(2026, 10, 26, 9))]
    context['note_codes'] = {context['cooperating'][0].id: context['cooperating'][0].action_code_raw}
    if scenario == 'empty': context.update(details=[], cooperating=[], notes=[])
    if scenario == 'open-error':
        row = detail['rows'][0]
        context['request'].state.pp_attempt = (
            f'/internal-control/monitoring/batches/{detail["batch"].id}/entry',
            FormData({'id': str(row['target'].id), 'expected_revision': str(detail['revision']),
                      'status': 'ongoing', 'percentage': '105', 'explanation': '<Korunan açıklama>',
                      'reason': '', 'evidence': ''}),
            {'detail': 'Sentetik gerçekleşme oranı geçersiz. Alanı düzeltip yeniden kaydedin.',
             'errors': [{'field': 'percentage', 'message': 'Gerçekleşme oranı için 0–100 girin.'}]})
    return context


@pytest.mark.parametrize('closed', [False, True])
def test_real_closed_period_and_strategy_byte_identical(ic_client, db, sample, open_period, closed):
    if closed:
        monitoring.close_period(db, sample['strategy'], open_period.id, 1, 'Sentetik dönem kapatıldı.')
        db.commit()
    response = ic_client.get('/internal-control/our-actions')
    html = render_contract(response)
    if closed:
        assert not [attrs for tag, attrs in ScreenContract(html).controls
                    if tag == 'form' and dict(attrs).get('method') == 'post']
    login(ic_client, sample['strategy'].email)
    redirect = ic_client.get('/internal-control/our-actions')
    assert redirect.status_code == 303
    assert redirect.headers['location'] == '/internal-control/monitoring'
    batch = db.scalar(select(ICMonitoringBatch).where(ICMonitoringBatch.period_id == open_period.id))
    for path in ['/internal-control/monitoring', f'/internal-control/monitoring/batches/{batch.id}']:
        response = ic_client.get(path)
        assert response.status_code == 200
        expected = frozen_environment().get_template(response.template.name).render(response.context)
        assert response.content == expected.encode()
        assert 'ic-our-actions.css' not in response.text
        assert 'ic-our-actions-page' not in response.text


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('scenario', ['no-period-actions', 'no-period-empty', 'open-error', 'submitted', 'closed', 'empty', 'returned', 'approved'])
def test_browser_layout_contrast_and_form_navigation(browser, ic_client, db, sample, action_plan, width, scenario):
    from playwright.sync_api import expect
    if not scenario.startswith('no-period'):
        monitoring.open_period(db, sample['strategy'], action_plan.id, 2027, 1,
                               monitoring.today(db) + timedelta(days=1000))
        db.commit()
    response = ic_client.get('/internal-control/our-actions')
    context = scenario_context(response, scenario)
    # Unbroken long codes and action text exercise wrapping in both templates.
    key = 'responsible' if scenario.startswith('no-period') else 'cooperating'
    if context[key]:
        action = synthetic_record(context[key][0])
        action.action_code_raw = 'KOS.' + '105' * 32
        action.text += ' ' + 'SentetikUzunEylem' * 12
        context[key] = [action]
    html = render_contract(response, context)
    calls, errors = [], []
    url = 'http://testserver/internal-control/our-actions'
    with browser.new_context(viewport={'width': width, 'height': 900}) as browser_context:
        def serve(route):
            request = route.request
            if request.method == 'POST':
                calls.append((request.url, parse_qs(request.post_data)))
                route.fulfill(status=200, content_type='text/plain', body='Sentetik katkı alındı.')
                return
            if urlsplit(request.url).path == '/internal-control/our-actions':
                calls.append((request.url, None))
                route.fulfill(status=200, content_type='text/html', body=html)
                return
            result = ic_client.get(request.url)
            headers = dict(result.headers); headers.pop('set-cookie', None)
            route.fulfill(status=result.status_code, headers=headers, body=result.content)
        browser_context.route('http://testserver/**', serve)
        page = browser_context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        root = page.locator('.ic-our-actions-page')
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
        # No shared inline shell overrides are emitted by this screen.
        assert page.locator('style').count() == 0
        pairs_script = TEXT_PAIRS.replace('.section-index-page', '.ic-our-actions-page')
        pairs = set(map(tuple, page.evaluate(pairs_script)))
        for control in root.locator('a, button, select, textarea, input:not([type=hidden])').all():
            if control.is_visible():
                control.hover(); control.focus()
                pairs.update(map(tuple, page.evaluate(pairs_script)))
        assert all(contrast(pair) >= 4.5 for pair in pairs), [(pair, contrast(pair)) for pair in pairs if contrast(pair) < 4.5]
        if not scenario.startswith('no-period'):
            toolbar = root.locator('.period-toolbar')
            boxes = [el.bounding_box() for el in toolbar.locator('label, select, button').all()]
            if width == 1440:
                assert len({round(b['y'] + b['height'] / 2) for b in boxes}) == 1
            else:
                assert boxes[0]['y'] < boxes[1]['y'] < boxes[2]['y']
            if scenario == 'open-error':
                expect(root.locator('[name=percentage]')).to_have_value('105')
                expect(root.locator('[name=percentage]')).to_have_attribute('aria-invalid', 'true')
                error = root.locator('#pp-error-percentage')
                expect(error).to_have_text('Gerçekleşme oranı için 0–100 girin.')
                assert error.evaluate('el => el.previousElementSibling.name') == 'percentage'
                expect(root.locator('[name=explanation]')).to_have_value('<Korunan açıklama>')
            if scenario in {'submitted', 'closed'}:
                expect(root.locator('.batch-content > .card > p:nth-of-type(2)')).to_contain_text('salt okunur')
            toolbar.locator('select').select_option('9105')
            toolbar.get_by_role('button', name='Dönemi göster').click()
            assert parse_qs(urlsplit(calls[-1][0]).query) == {'period_id': ['9105']}
            note_form = root.locator('form[action$="/notes"]')
            if note_form.count():
                action_id = note_form.locator('[name=id]').input_value()
                endpoint = note_form.get_attribute('action')
                note_form.locator('textarea').fill('Sentetik işbirliği katkısı.')
                note_form.get_by_role('button', name='Katkı notu ekle').click()
                assert calls[-1] == ('http://testserver' + endpoint, {
                    'csrf_token': [context['request'].session['csrf_token']],
                    'id': [action_id], 'content': ['Sentetik işbirliği katkısı.']})
        assert not errors
