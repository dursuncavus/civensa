"""CIV-111: frozen 042 contracts and real app.js browser interactions.

Only synthetic presentation records and disposable PostgreSQL are used.
"""
from collections import Counter
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
import os
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect
import pytest

from app.main import app, require_user
from app.security import hash_password
from test_activity_sections import login, PASSWORD
from test_ic_our_actions_design import VisibleText
from test_section_index_design import Contract, TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/review_042.html'
CHANGES = {'İnceleme Kuyruğu': 'İnceleme kuyruğu', 'Durum / Revizyon': 'Durum / revizyon',
           'İade Et': 'İade et', 'Word Raporu': 'Word raporu'}
ADDITIONS = {'Düzeltme için aç', 'Tablonun tamamını görmek için yatay kaydırın.',
             'Bu dönem için incelenecek paket yok.'}


class ReviewContract(Contract):
    def handle_data(self, data):
        super().handle_data(data + ' ')


class ReviewHooks(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.items = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hooks = {k: v for k, v in attrs.items() if k == 'id' or k.startswith('data-')}
        if 'review-action' in attrs.get('class', '').split():
            hooks['class'] = 'review-action'
        if hooks: self.items.append((tag, tuple(sorted(hooks.items()))))


@pytest.fixture
def review_client(client, db, sample):
    client.follow_redirects = False
    app.dependency_overrides.pop(require_user)
    for user in (sample['user'], sample['strategy']):
        user.password_hash = hash_password(PASSWORD)
    db.commit()
    login(client, sample['strategy'].email)
    return client


def scenario(response, statuses=('draft', 'submitted', 'returned', 'approved')):
    context = dict(response.context)
    context['rows'] = []
    context['department_names'] = {}
    context['event_map'] = {}
    for i, status in enumerate(statuses, 9100):
        submission = SimpleNamespace(id=i, status=status, revision=2,
            return_note=('Kaynak belgeye göre düzeltin. ' * 8 + 'UzunNot' * 24) if status == 'returned' else '')
        department = SimpleNamespace(id=i + 100)
        context['rows'].append((submission, department))
        context['department_names'][department.id] = f'Sentetik {status} Müdürlüğü'
        if status != 'draft':
            context['event_map'][i] = [SimpleNamespace(event_type='approve' if status == 'approved' else status,
                created_at=datetime(2026, 10, 26, 9, 30), actor=None, note='Sentetik işlem açıklaması.')]
    return context


def assert_frozen(response, context):
    assert sha256(FROZEN.read_bytes()).hexdigest() == 'b5b9220a49f7d98e5e560cd8c1e7feb3fc7201395dd0fbdc86b74112ebe9484e'
    request = context['request']
    request.state.pp_attempt_rendered = False
    actual = response.template.render(context)
    request.state.pp_attempt_rendered = False
    old = response.template.environment.from_string(FROZEN.read_text()).render(context)
    new_contract, old_contract = ReviewContract(actual), ReviewContract(old)
    assert new_contract.controls == old_contract.controls
    assert new_contract.bindings == old_contract.bindings
    assert Counter(new_contract.labels) == Counter((tag, CHANGES.get(text, text)) for tag, text in old_contract.labels)
    assert ReviewHooks(actual).items == ReviewHooks(old).items
    new_text, old_text = VisibleText(actual).normalized(), VisibleText(old).normalized()
    for before, after in CHANGES.items(): old_text = old_text.replace(before, after)
    if not context['rows']:
        old_text = old_text.replace('Müdürlük Durum / revizyon Son işlem İşlem ', '', 1)
    for addition in ADDITIONS: new_text = new_text.replace(addition, '')
    assert ' '.join(new_text.split()) == old_text
    assert actual.count('name="csrf_token"') == actual.count('<form method="post"')
    if '<form method="post"' in actual:
        assert f'name="csrf_token" value="{request.session["csrf_token"]}"' in actual
    return actual


@pytest.mark.parametrize('status', ['draft', 'submitted', 'returned', 'approved'])
@pytest.mark.parametrize('position', ['director', 'staff'])
@pytest.mark.parametrize('closed', [False, True])
def test_frozen_forms_links_fields_hooks_and_visibility(review_client, sample, status, position, closed):
    response = review_client.get(f'/review?period_id={sample["period"].id}')
    context = scenario(response, (status,))
    context['user'] = SimpleNamespace(**{k: v for k, v in vars(context['user']).items() if not k.startswith('_')})
    context['user'].position = position
    context['period'] = SimpleNamespace(id=sample['period'].id, year=2027, status='closed' if closed else 'active')
    html = assert_frozen(response, context)
    assert ('data-reopen-form' in html) == (status == 'approved' and position == 'director' and not closed)
    assert ('data-decision="approve"' in html) == (status == 'submitted' and position == 'director')
    assert ('Word raporu' in html) == (status == 'approved')
    assert ('Strateji Geliştirme Müdürüne başvurun.' in html) == (position == 'staff')


def test_real_role_visibility_empty_and_inactive_contract(review_client, db, sample):
    response = review_client.get('/review')
    assert response.status_code == 200
    assert_frozen(response, scenario(response, ()))
    context = scenario(response, ('approved',))
    context['user'] = SimpleNamespace(role='strategy', position='director', is_active=False)
    assert 'data-reopen-form' not in assert_frozen(response, context)
    sample['strategy'].position = 'staff'
    db.commit()
    assert 'Strateji Geliştirme Müdürüne başvurun.' in review_client.get('/review').text
    login(review_client, sample['user'].email)
    assert review_client.get('/review').status_code == 403


def test_reopen_error_retains_values_and_opens_only_affected_disclosure(review_client):
    from starlette.datastructures import FormData
    response = review_client.get('/review')
    context = scenario(response, ('approved', 'approved'))
    context['request'].state.pp_attempt = (
        '/review/submissions/9100/reopen', FormData({'reason': '   ', 'period_id': str(context['period'].id)}),
        {'detail': 'Gerekçe zorunlu.', 'errors': [{'field': 'reason', 'message': 'Gerekçe zorunlu.'}]})
    html = assert_frozen(response, context)
    import re
    details = re.findall(r'<details class="review-reopen"([^>]*)>(.*?)</details>', html, re.S)
    assert details[0][0].strip() == 'open'
    assert not details[1][0].strip()
    assert '>\n   </textarea>' in details[0][1]
    assert 'Gerekçe zorunlu.' in details[0][1]


@pytest.mark.parametrize('width', [1440, 390])
def test_browser_layout_contrast_decisions_and_reopen(browser, review_client, sample, width):
    url = f'http://testserver/review?period_id={sample["period"].id}'
    response = review_client.get(url)
    render_context = scenario(response)
    html = assert_frozen(response, render_context)
    calls, errors = [], []
    folder = os.getenv('CIVENSA_REVIEW_SCREENSHOTS')
    def capture(page, name):
        if folder:
            path = Path(folder); path.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(path / f'{name}-{width}.png'), full_page=True)
    with browser.new_context(viewport={'width': width, 'height': 1000}) as context:
        def serve(route):
            request = route.request
            if request.method == 'POST':
                calls.append((request.url, request.post_data, request.headers))
                if '/api/' in request.url:
                    route.fulfill(status=409, json={'detail': 'Sentetik sunucu hatası. Paketi kontrol edip yeniden deneyin.'})
                else:
                    route.fulfill(status=200, content_type='text/plain; charset=utf-8', body='Sentetik düzeltme isteği alındı.')
                return
            result = review_client.get(request.url)
            headers = dict(result.headers); headers.pop('set-cookie', None)
            route.fulfill(status=result.status_code, headers=headers,
                          body=html if urlsplit(request.url).path == '/review' else result.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        root = page.locator('.review-page')
        def layout():
            assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
            assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
        pairs = set()
        def colors():
            pairs.update(map(tuple, page.evaluate(TEXT_PAIRS.replace('.section-index-page', '.review-page'))))
        layout(); colors(); capture(page, 'director')
        region = root.get_by_role('region', name='İnceleme kuyruğu')
        if width == 390:
            expect(root.locator('.review-scroll-hint')).to_be_visible()
            assert region.evaluate('el => el.scrollWidth > el.clientWidth')
            region.focus(); page.keyboard.press('ArrowRight')
            page.wait_for_function('() => document.querySelector(".review-page .table-wrap").scrollLeft > 0')
        for control in root.locator('a,button,summary').all():
            if control.is_visible():
                control.hover(); control.focus(); colors()
        dialogs = []
        def confirm(dialog):
            dialogs.append(dialog.message); dialog.accept()
        page.on('dialog', confirm)
        root.locator('[data-decision=approve]').click()
        expect(root.locator('#reviewErrors-9101')).to_contain_text('Sentetik sunucu hatası.')
        expect(root.locator('#reviewErrors-9101')).to_be_focused()
        colors()
        assert dialogs == ['Bu müdürlük paketi onaylanacak ve veri girişi kilitlenecek. Devam edilsin mi?']
        root.locator('[data-decision=return]').click()
        expect(root.locator('#returnNote')).to_be_focused()
        layout(); colors(); capture(page, 'return-modal')
        root.locator('#cancelReturn').click()
        expect(root.locator('#reviewModal')).to_be_hidden()
        root.locator('[data-decision=return]').click()
        root.locator('#returnNote').fill('  Sentetik iade gerekçesi.  ')
        root.locator('#confirmReturn').click()
        expect(page.locator('#toast')).to_contain_text('Sentetik sunucu hatası.')
        root.locator('#cancelReturn').click()
        import json
        assert [json.loads(call[1]) for call in calls] == [
            {'decision': 'approve', 'note': ''}, {'decision': 'return', 'note': 'Sentetik iade gerekçesi.'}]
        assert all(call[0] == f'http://testserver/api/submissions/9101/decision?period_id={sample["period"].id}' for call in calls)
        assert all(call[2]['x-csrf-token'] == response.context['request'].session['csrf_token'] for call in calls)
        expect(root.locator('[data-reopen-form]')).to_be_hidden()
        root.locator('summary').click()
        expect(root.locator('[data-reopen-form]')).to_be_visible()
        layout(); colors(); capture(page, 'reopen')
        root.locator('[name=reason]').fill('Sentetik düzeltme gerekçesi.')
        root.locator('[data-reopen-form] button').click()
        expect(page.get_by_text('Sentetik düzeltme isteği alındı.')).to_be_visible()
        assert calls[-1][0] == 'http://testserver/review/submissions/9103/reopen'
        assert parse_qs(calls[-1][1]) == {'reason': ['Sentetik düzeltme gerekçesi.'],
            'csrf_token': [response.context['request'].session['csrf_token']], 'period_id': [str(sample['period'].id)]}
        for view in ('empty', 'staff'):
            render_context = scenario(response, () if view == 'empty' else ('draft', 'submitted', 'returned', 'approved'))
            if view == 'staff':
                render_context['user'] = SimpleNamespace(**{k: v for k, v in vars(render_context['user']).items() if not k.startswith('_')})
                render_context['user'].position = 'staff'
            html = assert_frozen(response, render_context)
            page.goto(url); layout(); colors(); capture(page, view)
            if view == 'empty': expect(root.get_by_text('Bu dönem için incelenecek paket yok.')).to_be_visible()
            else: expect(root.locator('[data-reopen-form],.review-action')).to_have_count(0)
        assert all(contrast(pair) >= 4.5 for pair in pairs), [(p, contrast(p)) for p in pairs if contrast(p) < 4.5]
        assert not errors
