"""024: frozen pre-CIV-097 field/action contract and native confirm keyboard flow."""
from html.parser import HTMLParser
import json
from pathlib import Path

import pytest
from playwright.sync_api import expect
from sqlalchemy import select

from app.models import Submission
from test_sidebar_ui import browser
from test_live_pilot_hardening import live_client

pytestmark = pytest.mark.postgres
CONTRACT = Path(__file__).parent / 'fixtures' / 'department_024_contract.json'


class Controls(HTMLParser):
    """Include hidden fields, both tabs and closed disclosures; never record CSRF values."""
    def __init__(self, html):
        super().__init__()
        self.controls = []
        self.in_main = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'main':
            self.in_main = True
        if not self.in_main or tag not in {'a', 'button', 'form', 'input', 'select', 'textarea', 'summary', 'option'}:
            return
        self.controls.append([tag, sorted([k, v] for k, v in attrs.items()
            if k not in {'value', 'style', 'aria-label', 'tabindex', 'role'} )])

    def handle_endtag(self, tag):
        if tag == 'main':
            self.in_main = False


def configure(db, sample, state, actor):
    sample['strategy'].position = 'staff'
    db.flush()
    user = sample['user']
    user.position = 'director' if actor == 'director' else 'staff'
    if actor == 'strategy':
        user.role = 'strategy'
    submission = db.scalar(select(Submission))
    submission.status = 'draft' if state in {'draft-issues', 'draft-clean', 'closed'} else state
    submission.return_note = 'Sentetik iade notu: açıklamayı kontrol edin.' if state == 'returned' else ''
    if state == 'closed':
        sample['period'].status = 'closed'
    if state == 'draft-issues':
        sample['card'].explanation = ''
        sample['indicator'].explanation = ''
    else:
        sample['indicator'].explanation = 'Sentetik açıklama'
    db.commit()


@pytest.mark.parametrize('actor', ['staff', 'director', 'strategy'])
@pytest.mark.parametrize('state', ['draft-issues', 'draft-clean', 'submitted', 'returned', 'approved', 'closed'])
def test_024_preserves_all_fields_and_action_targets(client, db, sample, state, actor):
    configure(db, sample, state, actor)
    response = client.get('/department/1?period_id=1')
    assert response.status_code == 200
    controls = Controls(response.text).controls
    frozen = json.loads(CONTRACT.read_text())
    expected = frozen['contracts'][frozen['cases'][f'{actor}/{state}']]
    # Exact attributes retain IDs, names, classes used by app.js, all data-*,
    # form actions/methods, hrefs and readonly/disabled/state conditions.
    assert controls == expected



@pytest.mark.parametrize('width', [1440, 390])
def test_024_confirm_focus_and_tab_order(browser, client, db, sample, width):
    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        writes, errors = [], []
        def serve(route):
            req = route.request
            if req.method != 'GET':
                writes.append(req.url)
            response = client.request(req.method, req.url, content=req.post_data_buffer,
                headers={'content-type': req.headers.get('content-type', '')}, follow_redirects=False)
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver/department/1?period_id=1')
        trigger = page.locator('.draft-removal summary').first
        trigger.focus()
        page.keyboard.press('Enter')
        dialog = page.locator('.removal-dialog[open]')
        cancel = dialog.locator('[data-cancel-removal]')
        confirm = dialog.locator('[type=submit]')
        expect(cancel).to_be_focused()
        page.keyboard.press('Tab')
        expect(confirm).to_be_focused()
        page.keyboard.press('Shift+Tab')
        expect(cancel).to_be_focused()
        page.keyboard.press('Escape')
        expect(dialog).to_have_count(0)
        expect(trigger).to_be_focused()
        page.keyboard.press('Enter')
        page.locator('.removal-dialog[open] [data-cancel-removal]').click()
        expect(trigger).to_be_focused()
        assert not writes and not errors
        fields = page.locator('.record').first.locator('[data-field]')
        fields.first.focus()
        for index in range(1, fields.count()):
            page.keyboard.press('Tab')
            expect(fields.nth(index)).to_be_focused()
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')


@pytest.mark.parametrize('width', [1440, 390])
def test_024_new_activity_preserves_cost_keys(browser, client, width):
    # app.js derives the write payload from the existing column labels.
    # Casing presentation must not turn budget/midyear fields into forecasts.
    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        def serve(route):
            assert route.request.method == 'GET'
            response = client.get(route.request.url)
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.goto('http://testserver/department/1?period_id=1')
        page.locator('[data-tab=activities]').click()
        page.locator('#addActivity').click()
        keys = page.locator('tr[data-new="1"] .activity-cost').evaluate_all(
            'nodes => nodes.map(el => [el.dataset.year, el.dataset.kind, el.dataset.funding])')
        assert keys == [[str(year), kind, funding] for year, kind in [
            (2026, 'budget'), (2026, 'midyear_spend'), (2026, 'year_end_estimate'),
            (2027, 'budget'), (2028, 'forecast'), (2029, 'forecast')]
            for funding in ['inside', 'outside']]
        page.locator('.cancel-new').click()
        expect(page.locator('tr[data-new="1"]')).to_have_count(0)


@pytest.mark.parametrize('width', [1440, 390])
def test_024_source_disclosure_contract_height_and_confirm(browser, db, sample, live_client, width):
    from test_source_conflicts import source_total
    from test_source_conflicts_ui import route_application
    from test_live_pilot_hardening import login

    total = source_total(db, sample)
    client = live_client()
    login(client, sample['user'].email)
    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        route_application(context, client)
        page = context.new_page()
        writes, errors = [], []
        page.on('request', lambda request: writes.append((request.method, request.url, request.post_data_json))
            if request.method != 'GET' else None)
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver/department/1?period_id=1')
        page.locator('[data-tab=activities]').click()
        page.evaluate('document.fonts.ready')
        row = page.locator('tr[data-activity="1"]')
        box = row.locator('.source-disagreement')
        panel = box.locator('details')
        trigger = panel.locator('summary')
        expect(trigger).to_have_text('Kaynak toplamı farklı · 2027 Bütçe')
        assert not panel.evaluate('el => el.open')
        expect(box.locator('.source-total-reason')).to_be_hidden()
        expect(box.locator('.confirm-source-total')).to_be_hidden()
        # All original data and controls remain in the original cost cell.
        assert box.evaluate('el => [el.className, el.dataset.year, el.dataset.kind, el.dataset.source, el.parentElement.dataset.costKey]') == [
            'source-disagreement issue-list', '2027', 'budget', '140.00', '2027:budget']
        controls = Controls(client.get('/department/1?period_id=1').text).controls
        field = ['input', [['class', 'source-total-reason'], ['data-field', 'cost_2027_budget_reason'],
            ['minlength', '10'], ['placeholder', 'En az 10 karakter']]]
        button = ['button', [['class', 'button small confirm-source-total'], ['type', 'button']]]
        # Reconcile the mismatch draft against the frozen, unchanged field/target contract.
        frozen = json.loads(CONTRACT.read_text())
        original = frozen['contracts'][frozen['cases']['staff/draft-clean']]
        additions = [['summary', []], field, button]
        assert Controls('<main>' + box.evaluate('el => el.outerHTML') + '</main>').controls == additions
        assert box.locator('b').count() == 1 and box.locator('p').count() == 2
        outside = next(i for i, control in enumerate(original) if control[0] == 'input'
            and ['data-year', '2027'] in control[1] and ['data-kind', 'budget'] in control[1]
            and ['data-funding', 'outside'] in control[1])
        assert controls == original[:outside + 1] + additions + original[outside + 1:]
        closed_height = row.bounding_box()['height']
        box.evaluate('el => el.hidden = true')
        clean_height = row.bounding_box()['height']
        box.evaluate('el => el.hidden = false')
        if width == 1440:
            assert closed_height <= clean_height + 16
        trigger.focus()
        page.keyboard.press('Enter')
        expect(box.locator('.source-total-reason')).to_be_visible()
        assert row.bounding_box()['height'] > closed_height
        expect(box).to_contain_text('Kaynak: 140,00 · Hesaplanan: 133,50')
        expect(box).to_contain_text('Kaynak toplamı korunur. Bütçe içi ve dışını kontrol edin veya gerekçeyle karar verin.')
        reason = box.locator('.source-total-reason')
        reason.fill('123456789')
        box.locator('.confirm-source-total').click()
        expect(reason).to_be_focused()
        expect(page.locator('#toast')).to_contain_text('Karar gerekçesi en az 10 karakter olmalı.')
        assert writes == []
        page.keyboard.press('Escape')
        assert not panel.evaluate('el => el.open')
        expect(trigger).to_be_focused()
        page.keyboard.press('Space')
        expect(reason).to_be_visible()
        # The unchanged input handler still updates computed totals and box.hidden.
        row.locator('.edit-activity').click()
        inside = row.locator('.activity-cost[data-year="2027"][data-funding="inside"]')
        inside.fill('106,50')
        expect(box).to_be_hidden()
        inside.fill('100,00')
        expect(box).to_be_visible()
        expect(box.locator('.computed-total')).to_have_text('133,50')
        reason.fill('Finansman dağılımı kontrol edilerek doğrulandı.')
        box.locator('.confirm-source-total').click()
        expect(box).to_have_count(0)
        assert writes == [('PUT', 'http://testserver/api/activities/1?period_id=1', {
            'cost_2027_budget_use_computed': True,
            'cost_2027_budget_reason': 'Finansman dağılımı kontrol edilerek doğrulandı.',
            'cost_2027_budget_inside': '100,00', 'cost_2027_budget_outside': '33,50'})]
        expect(page.locator('[data-activity-total="2027:budget"]')).to_have_text('133,50')
        db.refresh(total)
        assert str(total.amount) == '133.50' and str(total.source_amount) == '140.00'
        assert not errors
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
