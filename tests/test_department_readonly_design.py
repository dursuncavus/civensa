"""CIV-114: real-route read-only states and frozen 024 HTML/CSS regression."""
from hashlib import sha256
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from test_department_design import configure
from test_section_index_design import contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/department_readonly'
CONTROLS = '.data-entry-page :is(input, textarea, select, button, a, summary)'
READONLY = ':is(input[readonly], textarea[readonly], select:disabled, input[type=checkbox]:disabled)'


@pytest.fixture
def frozen():
    assert sha256((FROZEN / 'department.html').read_bytes()).hexdigest() == '4361df1c4a578ff6e3a1c77e523ab5f245ae4b96ebe9a62a53084ce93620b225'
    assert sha256((FROZEN / 'data-entry.css').read_bytes()).hexdigest() == '9570f536fb1209614763f87d81105e177cb2e185a20453a60e084b4a8d195e33'
    return FROZEN


def before_html(response, frozen):
    context = dict(response.context)
    context['request'].state.pp_attempt_rendered = False
    return response.template.environment.from_string((frozen / 'department.html').read_text()).render(context)


def route_page(context, client, html=None, css=None):
    def serve(route):
        assert route.request.method == 'GET'
        if html is not None and '/department/' in route.request.url:
            route.fulfill(status=200, content_type='text/html', body=html)
        elif css is not None and route.request.url.endswith('/static/design/data-entry.css'):
            route.fulfill(status=200, content_type='text/css', body=css)
        else:
            response = client.get(route.request.url)
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
    context.route('http://testserver/**', serve)


def capture(page, name, width):
    destination = os.getenv('CIVENSA_CIV114_EVIDENCE_DIR')
    if destination:
        path = Path(destination)
        path.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path / f'{name}-{width}.png'), full_page=True)
        assert (path / f'{name}-{width}.png').stat().st_size <= 1_500_000


@pytest.mark.parametrize('actor', ['staff', 'strategy'])
@pytest.mark.parametrize('state', ['draft-clean', 'returned', 'submitted', 'approved', 'closed'])
def test_real_route_modifier_and_unchanged_html(client, db, sample, frozen, actor, state):
    configure(db, sample, state, actor)
    response = client.get('/department/1?period_id=1')
    assert response.status_code == 200
    readonly = actor == 'strategy' or state in {'submitted', 'approved', 'closed'}
    old = before_html(response, frozen)
    expected = old.replace('<div class="data-entry-page">', '<div class="data-entry-page is-readonly">', 1) if readonly else old
    # Entire response is byte-identical except the single authorized wrapper class.
    assert response.content == expected.encode()
    assert ('class="data-entry-page is-readonly"' in response.text) == readonly


@pytest.mark.parametrize('width', [1440, 390])
def test_draft_html_and_every_control_computed_style_unchanged(browser, client, frozen, width):
    response = client.get('/department/1?period_id=1')
    old = before_html(response, frozen)
    assert response.content == old.encode()
    snapshots = []
    for baseline in (True, False):
        with browser.new_context(viewport={'width': width, 'height': 900}) as context:
            route_page(context, client, html=old if baseline else response.text,
                css=(frozen / 'data-entry.css').read_text() if baseline else None)
            page = context.new_page()
            page.goto('http://testserver/department/1?period_id=1')
            page.evaluate('document.fonts.ready')
            tabs = []
            for tab in ('indicators', 'activities'):
                page.locator(f'[data-tab={tab}]').click()
                tabs.append(page.locator(CONTROLS).evaluate_all('''nodes => nodes.map(el => {
                    const style = getComputedStyle(el);
                    return Object.fromEntries(Array.from(style, name => [name, style.getPropertyValue(name)]));
                })'''))
                assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
                if not baseline and tab == 'indicators':
                    capture(page, 'department-draft', width)
            snapshots.append(tabs)
    assert snapshots[0] == snapshots[1]


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('state', ['strategy', 'submitted', 'approved', 'closed'])
def test_readonly_browser_fields_focus_contrast_and_layout(browser, client, db, sample, state, width):
    configure(db, sample, 'draft-clean' if state == 'strategy' else state,
        'strategy' if state == 'strategy' else 'staff')
    # Both checked and unchecked disabled checkboxes retain their meaning.
    sample['activity'].contract_bound = state in {'strategy', 'approved'}
    db.commit()
    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        route_page(context, client)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver/department/1?period_id=1')
        page.evaluate('document.fonts.ready')
        expect(page.locator('.data-entry-page')).to_have_class('data-entry-page is-readonly')
        for tab in ('indicators', 'activities'):
            page.locator(f'[data-tab={tab}]').click()
            fields = page.locator(f'#{tab}').locator(READONLY + ':visible')
            assert fields.count() > 0
            styles = fields.evaluate_all('''nodes => nodes.map(el => {
                const s = getComputedStyle(el);
                return {border: s.borderTopWidth, shadow: s.boxShadow, background: s.backgroundColor,
                    color: s.color, opacity: s.opacity, cursor: s.cursor};
            })''')
            for style in styles:
                assert style['border'] == '0px'
                assert style['shadow'] == 'none'
                assert style['background'] == 'rgb(239, 237, 232)'
                assert style['color'] == 'rgb(31, 35, 40)'
                assert style['opacity'] == '1' and style['cursor'] == 'default'
                assert contrast((style['color'], style['background'])) >= 4.5
            assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
            if state == 'strategy':
                capture(page, f'strategy-{tab}', width)
            # Keyboard navigation reaches read-only values; a dashed outline
            # distinguishes focus for reading/copying from editable controls.
            if tab == 'indicators':
                page.locator('[data-tab=activities]').focus()
                page.keyboard.press('Tab')
            else:
                page.locator('.activity-scroll').focus()
                page.keyboard.press('Tab')
            focused = page.locator(':focus')
            assert focused.evaluate('el => el.matches("input[readonly], textarea[readonly]")')
            outline = focused.evaluate('''el => { const s = getComputedStyle(el); return [
                s.outlineStyle, s.outlineWidth, s.outlineColor, s.backgroundColor, s.boxShadow]; }''')
            assert outline[0:2] == ['dashed', '2px']
            assert contrast((outline[2], outline[3])) >= 3
            assert outline[4] == 'none'
        checkbox = page.locator('.contract-bound')
        expect(checkbox).to_be_disabled()
        assert checkbox.is_checked() == (state in {'strategy', 'approved'})
        if checkbox.is_checked():
            assert checkbox.evaluate('el => getComputedStyle(el, "::before").maskImage') != 'none'
        assert not errors
