"""024: frozen pre-CIV-097 field/action contract and native confirm keyboard flow."""
from html.parser import HTMLParser
import json
from pathlib import Path

import pytest
from playwright.sync_api import expect
from sqlalchemy import select

from app.models import Submission
from test_sidebar_ui import browser

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
