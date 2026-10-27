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
    if context['user'].role == 'department':
        target = f'/department/{context["department"].id}?period_id={context["period"].id}'
        # The legacy fixture predates clickable cards; only its entry link is exempt.
        old_links = [item for item in expected.controls if item[0] == 'a' and dict(item[1]).get('href') == target]
        assert len(old_links) == 1
        new_links = [item for item in actual.controls if item[0] == 'a' and dict(item[1]).get('href') == target]
        assert len(new_links) == 3
        assert Counter(item for item in actual.controls if item not in new_links) == Counter(
            item for item in expected.controls if item not in old_links)
        assert actual.bindings == expected.bindings
        new_labels = {'Veri girişi · ' + str(len(context['indicators'])) + ' gösterge', 'Civensa kontrolü', 'Gönderim'}
        old_labels = {'Veri girişini aç'}
        assert Counter(item for item in actual.labels if item[1] not in new_labels) == Counter(
            item for item in expected.labels if item[1] not in old_labels)
        assert [item for item in Hooks(html).items if not dict(item[1]).get('id', '').startswith('home-')] == Hooks(old).items
        return html
    new_card_labels = (
        'Dönemdeki müdürlük', 'Bakanlık şablonu', 'Eşleştirme bekleyen faaliyet',
        'Gösterge sayısı', 'Hatası olan gösterge', 'Gönderim durumu',
        'Onaylanan müdürlük', 'İnceleme bekleyen müdürlük', 'Veri girişi süren müdürlük',
        'Düzeltme gereken müdürlük', 'Veri girişine başlamayan müdürlük',
        'Kullanıcısı tanımlanmamış müdürlük',
    )

    def unchanged_controls(items):
        def is_dashboard_card(item):
            if item[0] != 'a':
                return False
            attrs = dict(item[1])
            return (
                'aria-label' in attrs or 'data-clear-progress-filter' in attrs or
                '/activity-mapping' in attrs.get('href', '')
            )

        return [item for item in items if not is_dashboard_card(item)]

    def unchanged_labels(items):
        return [item for item in items if not any(
            item[1].startswith(label) for label in (*new_card_labels, 'Faaliyet eşleştirme', 'Tümünü göster')
        )]

    def unchanged_hooks(items):
        ignored = {
            ('section', 'id', 'bakanlik-sablonu'),
            ('section', 'id', 'mudurluk-ilerleme'),
            ('p', 'id', 'progressFilterStatus'),
            ('span', 'data-filter-count', None),
            ('a', 'data-clear-progress-filter', None),
            ('a', 'data-filter-states', None),
            ('tr', 'data-state', None),
            ('script', 'src', '/static/design/dashboard.js'),
        }
        def is_dashboard_hook(item):
            attrs = dict(item[1])
            return any(
                item[0] == tag and name in attrs and (value is None or attrs[name] == value)
                for tag, name, value in ignored
            )

        return [item for item in items if not is_dashboard_hook(item)]

    assert Counter(unchanged_controls(actual.controls)) == Counter(unchanged_controls(expected.controls))
    assert actual.bindings == expected.bindings
    assert Counter(unchanged_labels(actual.labels)) == Counter(
        (tag, LABEL_CHANGES.get(text, text)) for tag, text in unchanged_labels(expected.labels)
    )
    assert unchanged_hooks(Hooks(html).items) == Hooks(old).items
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
    assert ('Bu dönem yapılacaklar' in html) == (role == 'department')
    if role == 'strategy':
        assert '<span>Dönem</span>' not in html
        controls = Contract(html).controls
        activate = [dict(attrs) for tag, attrs in controls if tag == 'button' and dict(attrs).get('data-id') == '9002'][-1]
        assert ('disabled' in activate) == (not verified)
        assert html.count('Görüntülenen dönem') == 1
        assert 'İşlem</span>' in html
        assert ('data-snapshot="9010"' in html) == filled
        assert ('data-import="9020"' in html) == filled
        summary_cards = html
        assert 'Dönemdeki müdürlük' in summary_cards
        assert 'Bakanlık şablonu' in summary_cards
        assert 'Eşleştirme bekleyen faaliyet' in summary_cards
        assert ('Bekleyen yok' in summary_cards) == (context['unresolved_count'] == 0)
        assert 'Onaylanan müdürlük' in summary_cards
        assert 'İnceleme bekleyen müdürlük' in summary_cards
        assert 'Veri girişi süren müdürlük' in summary_cards
        assert 'Düzeltme gereken müdürlük' in summary_cards
        assert 'Veri girişine başlamayan müdürlük' in summary_cards
        assert 'Kullanıcısı tanımlanmamış müdürlük' in summary_cards
        assert f'{context["progress_summary"]["submitted"]} incelemede olan müdürlük' in summary_cards
    else:
        assert all(label in html for label in ('Veri girişi · 1 gösterge', 'Civensa kontrolü', 'Gönderim'))
        assert 'dashboard-summary' not in html


@pytest.mark.parametrize('width', [1440, 1280, 1200, 390])
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
        assert page.locator('script[src="/static/design/dashboard.js"]').count() == int(role == 'strategy')
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth'), page.evaluate("[...document.querySelectorAll('*')].filter(el => el.getBoundingClientRect().right > innerWidth).map(el => [el.tagName, el.className, el.getBoundingClientRect().width])")
        assert root.locator('label, th, .card span').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform === 'none')")
        if role == 'strategy':
            assert root.locator('.dashboard-summary .card').evaluate_all("els => els.every(el => getComputedStyle(el).borderRadius === '0px' && getComputedStyle(el).borderLeftWidth === '0px')")
        top_cards = root.locator('.dashboard-summary > .cards > *')

        def row_sizes(cards):
            rows = {}
            for card in cards.all():
                rows.setdefault(round(card.bounding_box()['y']), []).append(card)
            return sorted(map(len, rows.values()))

        if width >= 1280 and role == 'strategy':
            if role == 'strategy':
                assert top_cards.count() == 3
            assert len({round(card.bounding_box()['y']) for card in top_cards.all()}) == 3
            for card in top_cards.all():
                assert card.bounding_box()['height'] <= 44, (
                    card.inner_text(), card.bounding_box(),
                    card.evaluate("el => ({className: el.className, padding: getComputedStyle(el).padding, "
                                  "label: getComputedStyle(el.querySelector('span')).lineHeight, "
                                  "value: getComputedStyle(el.querySelector('b')).lineHeight})"))
            if role == 'strategy':
                progress_cards = root.locator('#mudurluk-ilerleme .cards > *')
                assert row_sizes(progress_cards) == [3, 3]
                assert progress_cards.count() == 6
                heights = [card.evaluate(
                    "el => ({label: el.innerText, height: el.getBoundingClientRect().height, "
                    "lineHeight: getComputedStyle(el.querySelector('span')).lineHeight, "
                    "labelHeight: el.querySelector('span').getBoundingClientRect().height})"
                    ) for card in progress_cards.all()]
                assert all(card['height'] <= 120 for card in heights), heights
            if width == 1440:
                summary, main = root.locator('.dashboard-summary'), root.locator('.dashboard-main')
                assert summary.bounding_box()['x'] >= main.bounding_box()['x'] + main.bounding_box()['width']
                assert abs(summary.bounding_box()['y'] - main.bounding_box()['y']) <= 8
                assert len({round(card.bounding_box()['x']) for card in top_cards.all()}) == 1
                first_panel = root.locator('.dashboard-main > .dashboard-panel').first
                title_bottom = page.locator('.page-header').bounding_box()['y'] + page.locator('.page-header').bounding_box()['height']
                assert first_panel.bounding_box()['y'] - title_bottom <= 120
        elif role == 'strategy':
            assert row_sizes(top_cards) == ([1, 2] if width == 1200 else [1, 1, 1])
            if role == 'strategy':
                assert row_sizes(root.locator('#mudurluk-ilerleme .cards > *')) == [2, 2, 2]
        for row in top_cards.all():
            label, value = row.locator('span').bounding_box(), row.locator('b').bounding_box()
            assert row.bounding_box()['height'] <= 44
            assert 0 <= value['x'] - label['x'] - label['width'] <= 13
            assert value['y'] < label['y'] + label['height']
            assert row.locator('b').evaluate("el => getComputedStyle(el).fontVariantNumeric.includes('tabular-nums')")
        assert root.locator('.card').evaluate_all('els => els.every(el => el.scrollWidth <= el.clientWidth)')
        pairs_script = TEXT_PAIRS.replace('.section-index-page', '.dashboard-page')
        pairs = set(map(tuple, page.evaluate(pairs_script)))
        for control in root.locator('a, button:not(:disabled), select').all():
            if control.is_visible():
                control.hover(); control.focus()
                pairs.update(map(tuple, page.evaluate(pairs_script)))
        if role == 'strategy':
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
            expect(root.locator('.home-task-list > li')).to_have_count(3)
            expect(root.locator('.dashboard-summary')).to_have_count(0)
        assert all(contrast(pair) >= 4.5 for pair in pairs), [(pair, contrast(pair)) for pair in pairs if contrast(pair) < 4.5]
        assert not errors


@pytest.mark.parametrize('width', [1440, 390])
def test_021_progress_card_filters_and_no_javascript_fallback(browser, dashboard_client, sample, width):
    from playwright.sync_api import expect

    client = dashboard_client
    login(client, sample['strategy'].email)
    url = f'http://testserver/dashboard?period_id={sample["period"].id}'
    response = client.get(url)
    render_context = synthetic_context(response, False)
    html = assert_frozen(response, render_context)
    errors = []

    def serve(route):
        result = client.get(route.request.url)
        headers = dict(result.headers)
        headers.pop('set-cookie', None)
        route.fulfill(status=result.status_code, headers=headers,
                      body=html if route.request.url == url else result.content)

    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)

        expected_cards = [
            ('Dönemdeki müdürlük', str(len(render_context['departments'])), '#mudurluk-ilerleme'),
            ('Bakanlık şablonu', 'Doğrulandı' if render_context['period'].template_status == 'verified' else 'Bekliyor',
             '#bakanlik-sablonu'),
            ('Eşleştirme bekleyen faaliyet', str(render_context['unresolved_count']),
             f'/activity-mapping?period_id={sample["period"].id}'),
        ]
        summary_cards = page.locator('.dashboard-summary .strategy-cards a.card')
        assert summary_cards.count() == len(expected_cards)
        for card, (label, value, href) in zip(summary_cards.all(), expected_cards):
            assert card.locator('span').inner_text() == label
            assert card.locator('b').inner_text() == value
            assert card.get_attribute('href') == href
            assert card.get_attribute('aria-label') == f'{label} {value}'
        mapping_card = summary_cards.nth(2)
        assert mapping_card.locator('small').inner_text() == (
            'Kontrol gerekli' if render_context['unresolved_count'] else 'Bekleyen yok'
        )

        progress_values = [1, 1, 2, 2, 1, 1]
        progress_labels = [
            'Onaylanan müdürlük', 'İnceleme bekleyen müdürlük',
            'Veri girişi süren müdürlük', 'Düzeltme gereken müdürlük',
            'Veri girişine başlamayan müdürlük', 'Kullanıcısı tanımlanmamış müdürlük',
        ]
        progress_cards = page.locator('#mudurluk-ilerleme .cards > a.card')
        assert progress_cards.count() == 6
        for card, label, value in zip(progress_cards.all(), progress_labels, progress_values):
            assert card.locator('span').inner_text() == label
            assert card.locator('b').inner_text() == str(value)
            assert card.get_attribute('aria-label') == f'{label} {value}'
        assert [card.get_attribute('data-filter-states') for card in progress_cards.all()[:5]] == [
            'approved', 'submitted', 'in_progress,ready', 'needs_attention,returned', 'not_started',
        ]
        assert [card.get_attribute('href') for card in progress_cards.all()[:5]] == ['#mudurluk-ilerleme'] * 5
        assert progress_cards.nth(5).get_attribute('href') == f'/users?period_id={sample["period"].id}'
        assert page.locator('#mudurluk-ilerleme').count() == 1
        assert page.locator('#bakanlik-sablonu').count() == 1

        rows = page.locator('#mudurluk-ilerleme tbody tr')
        assert rows.count() == 7
        assert rows.evaluate_all('els => els.map(el => el.dataset.state)') == [
            'approved', 'submitted', 'in_progress', 'ready', 'needs_attention', 'returned', 'not_started',
        ]
        filter_cards = page.locator('.progress-filter')
        assert all(card.get_attribute('role') == 'button' for card in filter_cards.all())
        assert all(card.get_attribute('aria-pressed') == 'false' for card in filter_cards.all())
        state_groups = [
            {'approved'}, {'submitted'}, {'in_progress', 'ready'},
            {'needs_attention', 'returned'}, {'not_started'},
        ]
        status = page.locator('#progressFilterStatus')
        for index, states in enumerate(state_groups):
            card = filter_cards.nth(index)
            card.click()
            visible_states = page.locator('#mudurluk-ilerleme tbody tr:visible').evaluate_all(
                'els => els.map(el => el.dataset.state)')
            assert visible_states and set(visible_states) == states
            expect(status).to_have_text(f'{len(visible_states)} müdürlük gösteriliyor · Tümünü göster')
            assert [filter_cards.nth(i).get_attribute('aria-pressed') for i in range(5)] == [
                str(i == index).lower() for i in range(5)
            ]
            expect(card).to_have_css('background-color', 'rgb(227, 240, 238)')
            status.get_by_text('Tümünü göster').click()
            assert page.locator('#mudurluk-ilerleme tbody tr:visible').count() == 7
            expect(status).to_be_hidden()
            assert all(filter_cards.nth(i).get_attribute('aria-pressed') == 'false' for i in range(5))

        filter_cards.nth(3).focus()
        page.keyboard.press('Enter')
        assert set(page.locator('#mudurluk-ilerleme tbody tr:visible').evaluate_all(
            'els => els.map(el => el.dataset.state)')) == {'needs_attention', 'returned'}
        assert filter_cards.nth(3).get_attribute('aria-pressed') == 'true'
        page.locator('[data-clear-progress-filter]').click()
        filter_cards.nth(4).focus()
        page.keyboard.press('Space')
        assert page.locator('#mudurluk-ilerleme tbody tr:visible').evaluate_all(
            'els => els.map(el => el.dataset.state)') == ['not_started']
        assert filter_cards.nth(4).get_attribute('aria-pressed') == 'true'
        page.locator('[data-clear-progress-filter]').click()
        assert page.locator('#mudurluk-ilerleme tbody tr:visible').count() == 7

        pairs_script = TEXT_PAIRS.replace('.section-index-page', '.dashboard-page')
        assert all(contrast(pair) >= 4.5 for pair in map(tuple, page.evaluate(pairs_script)))
        assert not errors

    with browser.new_context(viewport={'width': width, 'height': 900}, java_script_enabled=False) as context:
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.goto(url)
        assert all(page.locator('.progress-filter').nth(index).get_attribute('role') is None
                   for index in range(page.locator('.progress-filter').count()))
        assert all(page.locator('.progress-filter').nth(index).get_attribute('aria-pressed') is None
                   for index in range(page.locator('.progress-filter').count()))
        page.locator('.progress-filter').nth(3).click()
        assert page.url.endswith('#mudurluk-ilerleme')
        assert page.locator('#mudurluk-ilerleme tbody tr').count() == 7
        expect(page.locator('#progressFilterStatus')).to_be_hidden()


@pytest.mark.parametrize('filled', [False, True])
def test_021_html_byte_identical_before_civ112(dashboard_client, sample, filled):
    login(dashboard_client, sample['strategy'].email)
    response = dashboard_client.get(f'/dashboard?period_id={sample["period"].id}')
    context = synthetic_context(response, filled)
    before = response.template.environment.from_string(
        (Path(__file__).parent / 'fixtures/dashboard_pre_civ112.html').read_text()).render(context)
    assert response.template.render(context).encode() == before.encode()


HOME_STATES = {
    'a': ('not_started', 'Başlanmadı', 'Bekliyor', 'Gönderilmedi'),
    'b': ('needs_attention', 'Devam ediyor', 'Düzeltme gerekli · 3 gösterge', 'Gönderilmedi'),
    'c': ('ready', 'Tamamlandı', 'Sorun yok', 'Gönderilmedi'),
    'd': ('submitted', 'Tamamlandı', 'Sorun yok', 'Gönderildi'),
    'e': ('returned', 'Devam ediyor', 'Düzeltme gerekli · 3 gösterge', 'İade edildi — düzeltip yeniden gönderin'),
    'approved': ('approved', 'Tamamlandı', 'Sorun yok', 'Onaylandı'),
}


def seed_home_state(db, sample, state):
    """Real persisted synthetic progress; no replacement route context or state mock."""
    from sqlalchemy import select
    from app.models import AuditLog, Indicator, IndicatorValue, Submission
    indicator = sample['indicator']
    # Three indicators makes issue count distinct from the number of field errors.
    for number in (2, 3):
        row = Indicator(period_id=sample['period'].id, department_id=sample['department'].id,
            subprogram_id=sample['subprogram'].id, card_id=sample['card'].id,
            name=f'Sentetik gösterge {number}', unit='Adet')
        db.add(row); db.flush()
        db.add(IndicatorValue(indicator_id=row.id, year=sample['period'].year,
            value_kind='target', value='2'))
    db.flush()
    if state in ('b', 'e'):
        for row in db.scalars(select(Indicator)).all():
            row.name = ''
            row.unit = ''
    if state != 'a':
        db.add(AuditLog(user_id=sample['user'].id, action='indicator_update',
            entity_type='indicator', entity_id=indicator.id))
    db.scalar(select(Submission)).status = {
        'd': 'submitted', 'e': 'returned', 'approved': 'approved'}.get(state, 'draft')
    db.commit(); db.expire_all()


@pytest.mark.parametrize('state', HOME_STATES)
@pytest.mark.parametrize('width', [1440, 390])
def test_022_real_task_list_states(browser, dashboard_client, db, sample, state, width):
    import os
    from playwright.sync_api import expect
    seed_home_state(db, sample, state)
    login(dashboard_client, sample['user'].email)
    url = f'http://testserver/dashboard?period_id={sample["period"].id}'
    response = dashboard_client.get(url)
    assert response.status_code == 200
    expected = HOME_STATES[state]
    assert response.context['department_state'] == expected[0]
    assert response.context['issues'] == (3 if state in ('b', 'e') else 0)
    with browser.new_context(viewport={'width': width, 'height': 900}, locale='tr-TR',
                             timezone_id='Europe/Istanbul', reduced_motion='reduce') as context:
        def serve(route):
            assert route.request.method == 'GET'
            result = dashboard_client.get(route.request.url)
            headers = dict(result.headers); headers.pop('set-cookie', None)
            route.fulfill(status=result.status_code, headers=headers, body=result.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        page.evaluate('document.fonts.ready')
        root = page.locator('.department-dashboard')
        tasks = root.locator('ol.home-task-list')
        expect(tasks.locator(':scope > li')).to_have_count(3)
        assert tasks.locator('.badge').all_text_contents() == list(expected[1:])
        assert tasks.locator('a').all_text_contents() == ['Veri girişi · 3 gösterge', 'Civensa kontrolü', 'Gönderim']
        target = f'/department/{sample["department"].id}?period_id={sample["period"].id}'
        for link in tasks.locator('a').all():
            assert link.get_attribute('href') == target
            assert link.get_attribute('aria-describedby')
        expect(root.locator('form, button, .dashboard-summary')).to_have_count(0)
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
        pairs_script = TEXT_PAIRS.replace('.section-index-page', '.department-dashboard')
        pairs = set(map(tuple, page.evaluate(pairs_script)))
        for link in tasks.locator('a').all():
            link.hover(); link.focus()
            pairs.update(map(tuple, page.evaluate(pairs_script)))
        assert all(contrast(pair) >= 4.5 for pair in pairs), [(p, contrast(p)) for p in pairs]
        if width == 390:
            for item in tasks.locator('li').all():
                link, badge = item.locator('a').bounding_box(), item.locator('.badge').bounding_box()
                assert badge['y'] >= link['y'] + link['height']
        else:
            # CIV-122: the status stays near its step instead of the far edge of a wide panel.
            box = tasks.bounding_box()
            assert box['width'] <= 44 * 16 + 1, box
            for item in tasks.locator('li').all():
                badge = item.locator('.badge').bounding_box()
                assert badge['x'] + badge['width'] <= box['x'] + box['width'] + 1
        assert not errors
        # Opt-in capture uses these exact real-route scenarios; no capture script is committed.
        if os.getenv('CIVENSA_CAPTURE_CIV112') == '1' and state in ('a', 'b', 'd', 'e'):
            from PIL import Image
            page.locator('h1').click()
            target_png = Path('docs/design/rollout/civ-112') / f'022-{state}-{width}.png'
            page.screenshot(path=str(target_png), full_page=True, animations='disabled', caret='hide')
            with Image.open(target_png) as png:
                png.save(target_png, optimize=True)
            assert target_png.stat().st_size <= 1_500_000


@pytest.mark.parametrize('state,entry', [
    ('not_started', 'Başlanmadı'), ('in_progress', 'Devam ediyor'),
    ('needs_attention', 'Devam ediyor'), ('returned', 'Devam ediyor'),
    ('ready', 'Tamamlandı'), ('submitted', 'Tamamlandı'), ('approved', 'Tamamlandı'),
])
def test_022_entry_mapping_and_pending_check(dashboard_client, sample, state, entry):
    login(dashboard_client, sample['user'].email)
    response = dashboard_client.get(f'/dashboard?period_id={sample["period"].id}')
    html = response.template.render({**response.context, 'department_state': state, 'issues': 0})
    assert f'id="home-entry-status">{entry}</span>' in html
    check = 'Sorun yok' if entry == 'Tamamlandı' else 'Bekliyor'
    assert f'id="home-check-status">{check}</span>' in html
