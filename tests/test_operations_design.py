"""CIV-132: frozen 035 contract, synthetic browser states and real form flows."""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import expect

from app.main import app, require_user
from app.security import hash_password
from test_activity_sections import login, PASSWORD
from test_ic_our_actions_design import VisibleText
from test_release_readiness_migration_head import readiness, migrated_template
from test_section_index_design import Contract, TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/operations_035.html'
CHANGES = {'Sistem Durumu': 'Sistem durumu', 'Mantıksal Yedek İndir': 'Mantıksal yedek indir'}


class OperationsContract(Contract):
    def handle_data(self, data):
        super().handle_data(data + ' ')


class Hooks(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.items = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        hooks = tuple((k, v) for k, v in attrs if k in {'id', 'data-check-id'})
        if hooks:
            self.items.append((tag, hooks))
        if tag == 'input' and dict(attrs).get('type') == 'hidden':
            self.items.append((tag, tuple(attrs)))  # compare CSRF and context values without redaction


@pytest.fixture
def operations_response(readiness, client, db, sample):
    readiness()
    client.follow_redirects = False
    # Exercise the real signed session and CSRF dependency for browser submits.
    app.dependency_overrides.pop(require_user)
    sample['strategy'].password_hash = hash_password(PASSWORD)
    db.commit()
    login(client, sample['strategy'].email)
    response = client.get('/operations?period_id=1')
    assert response.status_code == 200
    return response


def scenario(response, technical='blocked', release='Engelli', decision='confirmed', populated=True):
    context = dict(response.context)
    context['readiness'] = deepcopy(context['readiness'])
    context['operations'] = deepcopy(context['operations'])
    ready = context['readiness']
    ready['status'] = technical
    ready['warnings'] = ['Sentetik uyarı: müdürlük hesabını kontrol edin.',
                         'Sentetik uyarı: dönem kayıtlarını yeniden inceleyin.'] if technical == 'blocked' else []
    checklist = ready['release']
    checklist['status'] = release
    for index, item in enumerate(checklist['automatic']):
        item['status'] = 'Engelli' if technical == 'blocked' and index == 0 else 'Geçti'
        item['next_step'] = 'Sentetik bağlantı kaydını inceleyin.' if item['status'] == 'Engelli' else ''
        item['evidence'] = {'result': item['status'] == 'Geçti', 'observed': 'SentetikUzunJSON' * 160}
    checklist['history'] = []
    for index, item in enumerate(checklist['manual']):
        item['status'] = 'Geçti' if release == 'Hazır' else ('Doğrulanmadı' if item['id'] == 'PP-19' else 'Elle onay bekliyor')
        item['evidence'] = None
        if populated and (index == 0 or release == 'Hazır'):
            event = dict(id=index + 1, item_id=item['id'], actor_name='Sentetik Deniz Yılmaz',
                created_at='2026-10-27T09:00:00+00:00', decision=decision,
                reason='Sentetik kabul kapsamı incelendi.', evidence='Sentetik tutanak 035 / sorumlu kişi onayı.',
                context_sha256=checklist['context_sha256'])
            item['evidence'] = event
            if decision == 'confirmed': item['status'] = 'Geçti'
            checklist['history'].append(event)
    if populated:
        checklist['history'].append({**checklist['history'][0], 'id': 100,
            'decision': 'revoked', 'context_sha256': 'f' * 64})
        context['operations']['latest_audit_at'] = '2026-10-27T09:00:00+00:00'
        context['operations']['submissions'] = {'draft': 1, 'submitted': 2, 'approved': 3, 'returned': 1}
        context['operations']['records']['unresolved_activities'] = 2
        context['operations']['records']['missing_department_accounts'] = 1
    else:
        context['operations']['submissions'] = {}
        context['operations']['latest_audit_at'] = None
    return context


def assert_frozen(response, context):
    assert sha256(FROZEN.read_bytes()).hexdigest() == 'e6e8623145c604159dd557d95ab8b63ff29a415d33d1f7213941bff1323e80dc'
    actual = response.template.render(context)
    old = response.template.environment.from_string(FROZEN.read_text()).render(context)
    new_contract, old_contract = OperationsContract(actual), OperationsContract(old)
    # Link order can change in the page actions; every attribute and form binding stays frozen.
    assert Counter(new_contract.controls) == Counter(old_contract.controls)
    assert new_contract.bindings == old_contract.bindings
    assert Counter(new_contract.labels) == Counter((tag, CHANGES.get(text, text)) for tag, text in old_contract.labels)
    assert Hooks(actual).items == Hooks(old).items
    new_text, old_text = VisibleText(actual).normalized(), VisibleText(old).normalized()
    for before, after in CHANGES.items(): old_text = old_text.replace(before, after)
    # This existing link moves from technical readiness into the page actions.
    for text in ('Kanıtları JSON olarak aç',):
        new_text, old_text = new_text.replace(text, '', 1), old_text.replace(text, '', 1)
    assert ' '.join(new_text.split()) == ' '.join(old_text.split())
    assert '<details open' not in actual and '<details class="pp-release-history" open' not in actual
    return actual, old


@pytest.mark.parametrize('technical,release', [('blocked', 'Engelli'), ('ready', 'Elle onay bekliyor'), ('ready', 'Hazır')])
@pytest.mark.parametrize('decision', ['confirmed', 'revoked'])
@pytest.mark.parametrize('populated', [False, True])
def test_frozen_ids_checks_forms_attributes_links_and_status_text(operations_response, technical, release, decision, populated):
    assert_frozen(operations_response, scenario(operations_response, technical, release, decision, populated))


def test_frozen_error_attempt_values_selection_and_history(operations_response):
    context = scenario(operations_response)
    context.update(confirmation_error='Sentetik hata: gerekçeyi tamamlayıp yeniden deneyin.',
        attempted={'item_id': 'D8', 'decision': 'revoked', 'reason': '  Girilen <gerekçe>  ',
                   'evidence': 'Korunacak kanıt & onay'})
    actual, _ = assert_frozen(operations_response, context)
    assert '  Girilen &lt;gerekçe&gt;  </textarea>' in actual
    assert 'Korunacak kanıt &amp; onay</textarea>' in actual


@pytest.mark.parametrize('width', [1440, 390])
def test_browser_panels_disclosures_contrast_and_evidence_flows(browser, operations_response, client, width):
    url = 'http://testserver/operations?period_id=1'
    html, before = assert_frozen(operations_response, scenario(operations_response))
    rendered = html
    calls, errors, pairs = [], [], set()
    folder = os.getenv('CIVENSA_OPERATIONS_SCREENSHOTS')
    def capture(page, name):
        if folder:
            path = Path(folder); path.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(path / f'{name}-{width}.png'), full_page=True)
    with browser.new_context(viewport={'width': width, 'height': 1000}) as context:
        def serve(route):
            request = route.request
            if request.method == 'POST': calls.append((request.url, parse_qs(request.post_data)))
            result = client.request(request.method, request.url, content=request.post_data_buffer,
                headers={'content-type': request.headers.get('content-type', '')},
                follow_redirects=request.method == 'POST')
            headers = dict(result.headers); headers.pop('set-cookie', None)
            route.fulfill(status=result.status_code, headers=headers,
                body=rendered if rendered is not None and urlsplit(request.url).path == '/operations' else result.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        # Identical synthetic blocked data, recorded D1 evidence and open long JSON before/after.
        rendered = before
        page.goto(url)
        page.locator('.pp-release-item details').first.locator('summary').click()
        capture(page, 'before-blocked')
        rendered = html
        page.goto(url)
        root = page.locator('.operations-page')
        expect(root.locator('details[open]')).to_have_count(0)
        def layout():
            assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
            assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
            assert root.locator('.release-checks,.pp-release-items,.pp-release-form,.table-wrap').evaluate_all(
                'els => els.every(el => el.getBoundingClientRect().width <= 704)')
        def colors():
            pairs.update(map(tuple, page.evaluate(TEXT_PAIRS.replace('.section-index-page', '.operations-page'))))
        layout(); colors()
        expect(root.locator('[data-check-id="D1"]')).to_contain_text('Sentetik Deniz Yılmaz')
        expect(root.locator('[data-check-id="D2"]')).to_contain_text('Kanıt ve kişi onayı henüz kaydedilmedi.')
        root.locator('.pp-release-item details').first.locator('summary').click()
        pre = root.locator('pre').first
        expect(pre).to_be_visible()
        assert pre.evaluate('el => el.scrollWidth > el.clientWidth')
        pre.focus(); page.keyboard.press('ArrowRight')
        page.wait_for_function('() => document.querySelector(".operations-page pre").scrollLeft > 0')
        layout(); colors(); capture(page, 'after-blocked')
        for control in root.locator('a,button,summary,select,textarea').all():
            if control.is_visible():
                control.hover(); control.focus(); colors()
        root.locator('.pp-release-history summary').click()
        layout(); colors()
        for technical, release, decision, populated in [('ready','Hazır','confirmed',True), ('ready','Elle onay bekliyor','revoked',True), ('blocked','Engelli','confirmed',False)]:
            rendered, _ = assert_frozen(operations_response, scenario(operations_response, technical, release, decision, populated))
            page.goto(url); layout(); colors()
        # Real form validation, retained fields, confirmation and withdrawal against local DB.
        rendered = None
        page.goto(url)
        form = root.locator('.pp-release-form')
        form.locator('[name=evidence]').fill('Sentetik kabul tutanağı / Deniz')
        form.locator('button').click()
        assert not calls  # native required validation
        form.locator('[name=reason]').fill('   ')
        form.locator('button').click()
        expect(root.locator('[role=alert]')).to_contain_text('Gerekçe alanı eksik')
        expect(form.locator('[name=evidence]')).to_have_value('Sentetik kabul tutanağı / Deniz')
        layout(); colors()
        form.locator('[name=reason]').fill('Sentetik tarayıcı teyidi')
        form.locator('button').click()
        expect(root.locator('[data-check-id="D1"]')).to_contain_text('Sentetik tarayıcı teyidi')
        expect(root.locator('[data-check-id="D1"] .status')).to_have_text('Geçti')
        form.locator('[name=decision]').select_option('revoked')
        form.locator('[name=reason]').fill('Sentetik teyit geri çekme')
        form.locator('[name=evidence]').fill('Sentetik yeni tutanak / Deniz')
        form.locator('button').click()
        expect(root.locator('[data-check-id="D1"]')).to_contain_text('Teyit geri çekildi')
        expect(root.locator('[data-check-id="D1"] .status')).to_have_text('Elle onay bekliyor')
        layout(); colors()
        assert len(calls) == 3
        assert all(call[0] == 'http://testserver/release/confirmations?period_id=1' for call in calls)
        for _, data in calls:
            assert set(data) == {'csrf_token', 'context_sha256', 'item_id', 'decision', 'reason', 'evidence'}
            assert data['csrf_token'] == [operations_response.context['request'].session['csrf_token']]
            assert data['item_id'] == ['D1']
        assert calls[-1][1]['decision'] == ['revoked']
        assert all(contrast(pair) >= 4.5 for pair in pairs), [(pair, contrast(pair)) for pair in pairs if contrast(pair) < 4.5]
        assert not errors
