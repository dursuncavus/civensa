"""CIV-104: frozen 021/022 contract and real shared-JS browser interactions."""
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.main import app, require_user
from test_section_index_design import Contract, TEXT_PAIRS, contrast
from test_sidebar_ui import browser
from test_activity_sections import login, PASSWORD
from app.security import hash_password

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/dashboard_021_022.html'
# The only approved-for-review control-label differences; every other label is frozen.
LABEL_CHANGES = {
    'Yeni Dönem': 'Yeni dönem', 'Şablonu Doğrula': 'Şablonu doğrula',
    'Aktif Et': 'Aktif et', 'Şablon Yükle': 'Şablon yükle',
    'Word Verisini Tara': 'Word verisini tara',
}
HOOK_CLASSES = {'verify-period', 'activate-period', 'snapshot-item', 'import-item'}


class DashboardContract(Contract):
    def handle_data(self, data):
        # Inline legacy markup has no whitespace between separate text nodes.
        super().handle_data(data + " ")


class Hooks(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.items = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hooks = {k: v for k, v in attrs.items() if k == 'id' or k.startswith('data-') or
                 (tag == 'script' and k == 'src')}
        classes = HOOK_CLASSES.intersection(attrs.get('class', '').split())
        if classes: hooks['class'] = ' '.join(sorted(classes))
        if hooks: self.items.append((tag, tuple(sorted(hooks.items()))))


@pytest.fixture
def dashboard_client(client, db, sample):
    client.follow_redirects = False
    app.dependency_overrides.pop(require_user)
    for user in (sample["user"], sample["strategy"]):
        user.password_hash = hash_password(PASSWORD)
    db.commit()
    return client


def assert_frozen(response, context=None):
    assert response.status_code == 200
    context = context or response.context
    html = response.template.render(context)
    old = response.template.environment.from_string(FROZEN.read_text()).render(context)
    actual, expected = DashboardContract(html), DashboardContract(old)
    assert Counter(actual.controls) == Counter(expected.controls)
    assert actual.bindings == expected.bindings
    assert Counter(actual.labels) == Counter((tag, LABEL_CHANGES.get(text, text)) for tag, text in expected.labels)
    assert Hooks(html).items == Hooks(old).items
    return html


def synthetic_context(response, filled):
    """Render-only examples include every account/progress state; no real files/data."""
    context = dict(response.context)
    period = context['period']
    context['periods'] = [SimpleNamespace(id=period.id, year=period.year, status='active', template_status='verified'),
        SimpleNamespace(id=9002, year=period.year + 1, status='draft', template_status='pending'),
        SimpleNamespace(id=9003, year=period.year + 2, status='draft', template_status='verified')]
    stamp = datetime(2026, 10, 21, 10, 30)
    context['snapshots'] = [dict(id=9010, filename='Sentetik bakanlık şablonu.docx', created_at=stamp)] if filled else []
    context['imports'] = [dict(id=9020, filename='Sentetik performans.docx', created_at=stamp, status='preview')] if filled else []
    states = [('approved', 'Tamamlandı'), ('submitted', 'İncelemede'), ('in_progress', 'Devam ediyor'),
              ('ready', 'Hazır'), ('needs_attention', 'Kontrol gerekli'), ('returned', 'İade edildi'), ('not_started', 'Başlamadı')]
    context['progress_rows'] = [dict(department_id=9100+i, department_name=f'Sentetik {name} Müdürlüğü',
        indicator_count=12, activity_count=4, is_active=i != 6, has_department_user=i != 4,
        state=state, label=name, progress_percent=[100, 80, 40, 90, 20, 30, 0][i], warning_count=i % 2,
        last_activity_at='2026-10-21T10:30:00' if i % 2 else None) for i, (state, name) in enumerate(states)]
    context['progress_summary'] = dict(approved=1, submitted=1, in_progress=1, ready=1,
        needs_attention=1, returned=1, not_started=1, missing_accounts=1)
    return context


@pytest.mark.parametrize('role', ['strategy', 'department'])
@pytest.mark.parametrize('filled', [False, True])
@pytest.mark.parametrize('verified', [False, True])
def test_021_022_frozen_forms_links_hooks_and_role_visibility(dashboard_client, sample, role, filled, verified):
    client = dashboard_client
    login(client, sample['strategy' if role == 'strategy' else 'user'].email)
    response = client.get(f'/dashboard?period_id={sample["period"].id}')
    assert_frozen(response)
    context = synthetic_context(response, filled) if role == 'strategy' else dict(response.context)
    if role == 'strategy':
        context['periods'][1].template_status = 'verified' if verified else 'pending'
    else:
        context['issues'] = 3 if filled else 0
    html = assert_frozen(response, context)
    assert ('id="newPeriodBtn"' in html) == (role == 'strategy')
    assert ('Veri girişini aç' in html) == (role == 'department')
    if role == 'strategy':
        controls = Contract(html).controls
        activate = [dict(attrs) for tag, attrs in controls if tag == 'button' and dict(attrs).get('data-id') == '9002'][-1]
        assert ('disabled' in activate) == (not verified)
        assert html.count('Görüntülenen dönem') == 1
        assert 'İşlem</span>' in html
        assert ('data-snapshot="9010"' in html) == filled
        assert ('data-import="9020"' in html) == filled


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('role', ['strategy', 'department'])
def test_021_022_browser_layout_contrast_and_period_actions(browser, dashboard_client, sample, width, role):
    client = dashboard_client
    from playwright.sync_api import expect
    login(client, sample['strategy' if role == 'strategy' else 'user'].email)
    url = f'http://testserver/dashboard?period_id={sample["period"].id}'
    response = client.get(url)
    render_context = synthetic_context(response, False) if role == 'strategy' else {**response.context, 'issues': 0}
    html = assert_frozen(response, render_context)
    calls, errors = [], []
    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        def serve(route):
            request = route.request
            if request.method == 'POST':
                calls.append((request.url, request.method, request.post_data_json,
                              request.headers.get('x-csrf-token')))
                # Exercise unchanged JS endpoint wiring without mutating fixture data/reloading.
                route.fulfill(status=400, json={'detail': 'Sentetik işlem yanıtı.'})
                return
            result = client.get(request.url)
            headers = dict(result.headers); headers.pop('set-cookie', None)
            route.fulfill(status=result.status_code, headers=headers, body=html if request.url == url else result.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        root = page.locator('.dashboard-page')
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth'), page.evaluate("[...document.querySelectorAll('*')].filter(el => el.getBoundingClientRect().right > innerWidth).map(el => [el.tagName, el.className, el.getBoundingClientRect().width])")
        assert root.locator('label, th, .card span').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform === 'none')")
        pairs_script = TEXT_PAIRS.replace('.section-index-page', '.dashboard-page')
        pairs = set(map(tuple, page.evaluate(pairs_script)))
        for control in root.locator('a, button:not(:disabled), select').all():
            if control.is_visible():
                control.hover(); control.focus()
                pairs.update(map(tuple, page.evaluate(pairs_script)))
        if role == 'strategy':
            if width == 1440:
                boxes = root.locator('.strategy-cards > *').all()
                assert len({round(el.bounding_box()['y']) for el in boxes}) == 1
            expect(page.locator('#newPeriodForm')).to_be_hidden()
            page.locator('#newPeriodBtn').click()
            expect(page.locator('#newPeriodForm')).to_be_visible()
            expect(page.locator('#newPeriodYear')).to_be_focused()
            assert page.evaluate('document.documentElement.scrollWidth === innerWidth'), page.evaluate("[...document.querySelectorAll('*')].filter(el => el.getBoundingClientRect().right > innerWidth).map(el => [el.tagName, el.className, el.getBoundingClientRect().width])")
            pairs.update(map(tuple, page.evaluate(pairs_script)))
            page.locator('#cancelPeriod').click()
            expect(page.locator('#newPeriodForm')).to_be_hidden()
            expect(page.locator('.activate-period[data-id="9002"]')).to_be_disabled()
            page.locator('.verify-period[data-id="9002"]').click()
            expect(page.locator('#toast')).to_have_text('Sentetik işlem yanıtı.')
            page.locator('#toast').evaluate("el => el.textContent = ''")
            page.locator('.activate-period[data-id="9003"]').click()
            expect(page.locator('#toast')).to_have_text('Sentetik işlem yanıtı.')
            page.locator('#newPeriodBtn').click()
            page.locator('#newPeriodYear').fill('2030')
            page.locator('#toast').evaluate("el => el.textContent = ''")
            page.locator('#createPeriod').click()
            expect(page.locator('#toast')).to_have_text('Sentetik işlem yanıtı.')
            assert [call[:2] for call in calls] == [
                ('http://testserver/api/periods/9002/verify-template', 'POST'),
                ('http://testserver/api/periods/9003/activate', 'POST'),
                ('http://testserver/api/periods', 'POST')]
            assert calls[-1][2] == {'year': '2030', 'base_period_id': str(sample['period'].id)}
            assert all(call[3] == response.context['request'].session['csrf_token'] for call in calls)
            region = root.get_by_role('region', name='Müdürlük ilerlemesi')
            if width == 390:
                assert region.evaluate('el => el.scrollWidth > el.clientWidth')
                region.focus(); page.keyboard.press('ArrowRight')
                page.wait_for_function('document.querySelector(".dashboard-page .table-wrap").scrollLeft > 0')
            expect(root.locator('.empty-state')).to_have_count(2)
            filled = synthetic_context(response, True)
            page.route(url, lambda route: route.fulfill(body=response.template.render(filled), content_type='text/html'))
            page.goto(url)
            expect(root.locator('[data-snapshot="9010"]')).to_be_visible()
            expect(root.locator('[data-import="9020"]')).to_be_visible()
            pairs.update(map(tuple, page.evaluate(pairs_script)))
        else:
            expect(root.locator('.button.primary')).to_have_count(1)
            assert root.locator('.dashboard-issues').evaluate('el => getComputedStyle(el).color') == 'rgb(31, 35, 40)'
            page.route(url, lambda route: route.fulfill(body=response.template.render({**response.context, 'issues': 3}), content_type='text/html'))
            page.goto(url)
            assert root.locator('.dashboard-issues').evaluate('el => getComputedStyle(el).color') == 'rgb(138, 90, 0)'
            pairs.update(map(tuple, page.evaluate(pairs_script)))
        assert all(contrast(pair) >= 4.5 for pair in pairs), [(pair, contrast(pair)) for pair in pairs if contrast(pair) < 4.5]
        assert not errors
