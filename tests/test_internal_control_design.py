"""CIV-145: frozen content contracts and browser checks with disposable data."""
from collections import Counter
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from jinja2 import ChoiceLoader, DictLoader
import pytest

from app import internal_control_monitoring_service as monitoring
from app.main import templates
from test_activity_sections import login
from test_ic_our_actions_design import ic_client, VisibleText, ScreenContract, narrative_deltas
from test_internal_control import stage, saved, workbook, action_row
from test_internal_control_monitoring import monitoring as monitoring_data, fill
from test_section_index_design import TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
BASELINE = Path(__file__).parent / 'fixtures/civ145_internal_control'


class Hooks(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.main = False
        self.hooks = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'main': self.main = True
        if self.main:
            hooks = tuple((k, v) for k, v in attrs if k == 'id' or k.startswith(('data-', 'aria-')))
            if hooks: self.hooks.append((tag, hooks))

    def handle_endtag(self, tag):
        if tag == 'main': self.main = False


def frozen(response):
    """Render the starting templates using the identical real route context."""
    assert response.status_code in (200, 422)
    sources = {f'internal_control/{p.name}': p.read_text() for p in BASELINE.glob('*.html')}
    env = templates.env.overlay(loader=ChoiceLoader([DictLoader(sources), templates.env.loader]))
    request = response.context['request']
    request.state.pp_attempt_rendered = False
    actual = response.template.render(response.context)
    request.state.pp_attempt_rendered = False
    expected = env.get_template(response.template.name).render(response.context)
    expected = narrative_deltas(response.template.name, response.context, expected)
    if response.template.name == 'internal_control/monitoring.html':
        # Owner-approved display-only change in the standard column.
        for component, standard in response.context['counts']:
            before = f'<td>{escape(component)}</td><td>{escape(standard)}</td>'
            after = f'<td>{escape(component)}</td><td>{escape(standard.removeprefix(component))}</td>'
            assert expected.count(before) == 1
            expected = expected.replace(before, after, 1)
    new, old = ScreenContract(actual), ScreenContract(expected)
    assert new.controls == old.controls
    assert new.bindings == old.bindings
    assert Counter(new.labels) == Counter(old.labels)
    assert Hooks(actual).hooks == Hooks(expected).hooks
    assert VisibleText(actual).normalized() == VisibleText(expected).normalized()
    return actual


SCENES = ['index-empty', 'index-populated', 'index-file-required',
          'plan-populated', 'plan-empty', 'plan-active',
          'import-empty', 'import-populated', 'import-warning', 'import-error', 'import-committed',
          'monitoring-empty', 'monitoring-populated', 'monitoring-submitted', 'monitoring-returned', 'monitoring-error', 'monitoring-closed',
          'detail-empty', 'detail-populated', 'detail-department', 'detail-error', 'detail-submitted', 'detail-approved', 'detail-closed']


@pytest.fixture
def screen(request, ic_client, db, sample):
    scene = request.param
    login(ic_client, sample['strategy'].email)
    if scene.startswith('index') or scene == 'monitoring-empty':
        if scene == 'index-populated':
            saved(db, sample)
        path = '/internal-control/monitoring' if scene.startswith('monitoring') else '/internal-control'
        response = ic_client.get(path)
    elif scene.startswith('import'):
        rows = [] if scene == 'import-empty' else [action_row()]
        if scene == 'import-warning':
            rows = [action_row(**{'11': '2027 ikinci yarıyıl'})]
        if scene == 'import-error':
            rows = [action_row(**{'7': 'Sentetik Eşleşmeyen Müdürlük', '6': ''})]
        batch, _ = stage(db, sample, workbook(rows))
        if scene == 'import-committed':
            from app import internal_control_service as ic
            ic.commit_import(db, sample['strategy'], batch.id)
            db.commit()
        path = f'/internal-control/imports/{batch.id}'
        response = ic_client.get(path)
    elif scene.startswith('plan'):
        from app import internal_control_service as ic
        plan = saved(db, sample, workbook([action_row(**{'12': 'Sentetik plan açıklaması <korunur>.'})]))
        if scene == 'plan-active':
            ic.activate_plan(db, sample['strategy'], plan.id)
            db.commit()
        path = f'/internal-control/plans/{plan.id}' + ('?q=Bulunmayan' if scene == 'plan-empty' else '')
        response = ic_client.get(path)
    else:
        data = request.getfixturevalue('monitoring_data')
        period, batch = data['period'], data['body']
        if scene == 'detail-department':
            batch = data['owned']
            action = monitoring.rows(db, batch)[0]['action']
            monitoring.add_note(db, data['collaborator'], period.id, action.id, 'Sentetik işbirliği katkısı <korunur>.')
            db.commit()
            login(ic_client, sample['user'].email)
        if scene not in {'detail-empty', 'monitoring-populated', 'monitoring-error'}:
            fill(db, data, batch)
            if scene in {'detail-submitted', 'detail-approved', 'monitoring-submitted', 'monitoring-returned'}:
                monitoring.transition(db, sample['strategy'], batch.id, 'submit', monitoring.state(db, batch.id)[1])
                db.commit()
                if scene == 'detail-approved':
                    monitoring.transition(db, sample['strategy'], batch.id, 'approve', monitoring.state(db, batch.id)[1])
                    db.commit()
                if scene == 'monitoring-returned':
                    monitoring.transition(db, sample['strategy'], batch.id, 'return', monitoring.state(db, batch.id)[1], 'Sentetik açıklama tamamlanmalı.')
                    db.commit()
        if scene in {'monitoring-closed', 'detail-closed'}:
            monitoring.close_period(db, sample['strategy'], period.id, 1, 'Sentetik dönem tamamlandı.')
            db.commit()
        path = '/internal-control/monitoring' if scene.startswith('monitoring') else f'/internal-control/monitoring/batches/{batch.id}'
        if scene == 'monitoring-error':
            response = ic_client.post('/internal-control/monitoring/open', data={
                'csrf_token': ic_client.get(path).context['request'].session['csrf_token'],
                'plan_id': str(data['plan'].id), 'year': 'geçersiz', 'half': '1', 'deadline': '2029-12-31'})
        elif scene == 'detail-error':
            row = monitoring.rows(db, batch)[0]
            response = ic_client.post(path + '/entry', data={
                'csrf_token': ic_client.get(path).context['request'].session['csrf_token'],
                'id': row['target'].id, 'expected_revision': monitoring.state(db, batch.id)[1],
                'status': 'ongoing', 'percentage': '105', 'explanation': 'Sentetik açıklama <korunur>.',
                'reason': '', 'evidence': 'Sentetik EBYS 145'})
        else:
            response = ic_client.get(path)
    return scene, path, response, frozen(response)


def test_shared_sources_and_department_screen_unchanged():
    # Exact source hashes from phase5 69021f0 cover shared files and CIV-105.
    hashes = {'monitoring_shared': '7f855dc94b101377db64a6860dfa713606d3b117b3bc8e2514832ba73142dc82', 'monitoring_notes': '7122a66ff3c0dde77dc0b17c154203eaeb431a05f80aaaa7837d34768702fd07', 'monitoring_ours': 'ddd743a343c78a4a4b39ad3102b6d8e7265525cf8652958d014fe0b162545daf', 'our_actions': '57ed2f6df50e9ee2757fad56f44cf5faa731e0203e3cf8e0b56e8befe1c9c1f9'}
    for name in hashes:
        source = Path(f'app/templates/internal_control/{name}.html').read_bytes()
        if name == 'monitoring_ours':
            # D-342 permits only the state-dependent, read-only narrative include.
            delta = b"  {% include 'internal_control/narrative_ours.html' %}\n"
            assert source.count(delta) == 1
            source = source.replace(delta, b'', 1)
        assert sha256(source).hexdigest() == hashes[name]
    # The already-restyled screen is tested by its existing frozen suite.
    assert 'internal-control.css' not in Path('app/templates/internal_control/our_actions.html').read_text()


def test_css_uses_only_existing_tokens():
    import re
    css = Path('app/static/design/internal-control.css').read_text()
    tokens = Path('app/static/design/tokens.css').read_text()
    assert set(re.findall(r'var\((--[\w-]+)\)', css)) <= set(re.findall(r'(--[\w-]+):', tokens))
    assert not re.search(r'#[\da-fA-F]{3,8}\b|rgba?\(|hsla?\(', css)
    assert not re.search(r'--[\w-]+\s*:', css)
    for declaration in re.findall(r'(?:font-size|padding|gap|border-radius)\s*:\s*([^;}]+)', css):
        assert 'var(--' in declaration or declaration.strip() == '0'


@pytest.mark.parametrize(('screen', 'width'),
    [(scene, width) for scene in SCENES for width in (1440, 390)]
    + [('monitoring-populated', 1280), ('monitoring-populated', 1000)], indirect=['screen'])
def test_frozen_browser_layout_contrast_and_navigation(browser, screen, ic_client, width):
    from playwright.sync_api import expect
    scene, path, response, html = screen
    calls, errors = [], []
    with browser.new_context(viewport={'width': width, 'height': 900}, locale='tr-TR') as context:
        def serve(route):
            request = route.request
            if request.method == 'POST':
                calls.append((urlsplit(request.url).path, parse_qs(request.post_data, keep_blank_values=True)))
                route.fulfill(status=200, content_type='text/plain', body='Sentetik istek alındı.')
            elif urlsplit(request.url).path == urlsplit(path).path:
                calls.append((request.url, None))
                route.fulfill(status=200, content_type='text/html', body=html)
            elif urlsplit(request.url).path.startswith('/static/'):
                result = ic_client.get(request.url)
                route.fulfill(status=result.status_code, headers=dict(result.headers), body=result.content)
            else:
                calls.append((request.url, None))
                route.fulfill(status=200, content_type='text/plain', body='Sentetik bağlantı açıldı.')
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver' + path)
        page.evaluate('document.fonts.ready')
        root = page.locator('.internal-control-page')
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        monitoring_page = scene.startswith('monitoring-')
        root_width = root.bounding_box()['width']
        if monitoring_page:
            available = root.evaluate("el => { const p = el.parentElement; const s = getComputedStyle(p); return p.clientWidth - parseFloat(s.paddingLeft) - parseFloat(s.paddingRight); }")
            assert abs(root_width - available) <= 1
        else:
            assert root_width <= 704
        if monitoring_page:
            opening = root.locator('form[action="/internal-control/monitoring/open"]')
            if opening.count():
                grid = opening.locator('.ic-grid')
                fields = [field.bounding_box() for field in grid.locator(':scope > label').all()]
                columns = 3 if width >= 1100 else 2 if width > 700 else 1
                for i, field in enumerate(fields):
                    if i % columns:
                        previous = fields[i - 1]
                        assert abs(field['y'] - previous['y']) <= 1
                        assert field['x'] >= previous['x'] + previous['width']
                    elif i:
                        previous = fields[i - columns]
                        assert field['y'] >= previous['y'] + previous['height']
                plan = opening.locator(':scope > label').bounding_box()
                grid_box = grid.bounding_box()
                submit = opening.locator('button').bounding_box()
                assert plan['y'] + plan['height'] <= grid_box['y']
                assert abs(plan['width'] - grid_box['width']) <= 1
                assert submit['y'] >= grid_box['y'] + grid_box['height'] + 16
                assert abs(submit['x'] - grid_box['x']) <= 1
        for form in root.locator('form[method=post]').all():
            expect(form.locator('[name=csrf_token]')).to_have_value(response.context['request'].session['csrf_token'])
        for badge in root.locator('.status').all():
            assert badge.evaluate("el => getComputedStyle(el).position === 'static' && getComputedStyle(el).float === 'none'")
        panels = root.locator('section, .card')
        for panel in panels.all():
            box = panel.bounding_box()
            if box: assert box['width'] <= (root_width if monitoring_page else 704)
        top_panels = root.locator(':scope > section')
        boxes = [p.bounding_box() for p in top_panels.all()]
        assert all(a['y'] + a['height'] <= b['y'] + 1 and abs(a['x'] - b['x']) <= 1 for a, b in zip(boxes, boxes[1:]))
        assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
        assert page.locator('style').evaluate_all("els => els.every(el => !el.textContent.includes('.app:has(.ic-wrap)'))")
        script = TEXT_PAIRS.replace('.section-index-page', '.internal-control-page')
        pairs = set(map(tuple, page.evaluate(script)))
        # Include disclosure content and every new hover/focus text pair.
        for disclosure in root.locator('details').all():
            disclosure.locator('summary').focus()
            page.keyboard.press('Enter')
            expect(disclosure).to_have_attribute('open', '')
        pairs.update(map(tuple, page.evaluate(script)))
        for control in root.locator('a,button,summary,input:not([type=hidden]),select,textarea').all():
            if control.is_visible() and control.is_enabled():
                control.hover(); control.focus()
                assert control.evaluate("el => getComputedStyle(el).outlineStyle === 'solid'")
                pairs.update(map(tuple, page.evaluate(script)))
        assert all(contrast(pair) >= 4.5 for pair in pairs), [(p, contrast(p)) for p in pairs if contrast(p) < 4.5]
        for scroll in root.locator('.ic-scroll').all():
            table = scroll.locator('table')
            counts_table = table.locator('th').nth(1).inner_text() == 'Standart'
            if counts_table:
                expect(table).to_have_class('ic-counts-table')
                assert table.evaluate('el => getComputedStyle(el).tableLayout') == 'fixed'
                bottoms = table.locator('th').evaluate_all('''els => els.map(el => {
                    const range = document.createRange();
                    range.selectNodeContents(el);
                    return Math.max(...[...range.getClientRects()].map(rect => rect.bottom));
                })''')
                assert max(bottoms) - min(bottoms) <= 1
                for row in table.locator('tr').all():
                    widths = [cell.bounding_box()['width'] for cell in row.locator('th,td').all()]
                    assert max(widths) - min(widths) <= 1
            else:
                expected_layout = 'fixed' if 'ic-result-table' in (table.get_attribute('class') or '').split() else 'auto'
                assert table.evaluate('el => getComputedStyle(el).tableLayout') == expected_layout
            for cell in scroll.locator('th,td').all():
                assert cell.evaluate('el => el.scrollWidth <= el.clientWidth')
                assert cell.evaluate('el => getComputedStyle(el).fontSize') == '14px'
                alignment = 'bottom' if counts_table and cell.evaluate('el => el.tagName') == 'TH' else 'top'
                assert cell.evaluate('el => getComputedStyle(el).verticalAlign') == alignment
                assert cell.evaluate('el => getComputedStyle(el).overflowWrap') == 'normal'
                assert cell.evaluate('el => getComputedStyle(el).wordBreak') == 'normal'
                assert cell.evaluate('el => getComputedStyle(el).hyphens') == 'none'
                # Each word's rendered range must stay on one line, while spaces may wrap.
                assert cell.evaluate(r'''el => {
                    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
                    for (let node; node = walker.nextNode();) {
                        for (const word of node.textContent.matchAll(/\S+/gu)) {
                            const range = document.createRange();
                            range.setStart(node, word.index);
                            range.setEnd(node, word.index + word[0].length);
                            if (new Set([...range.getClientRects()].map(r => Math.round(r.y))).size > 1) return false;
                        }
                    }
                    return true;
                }''')
            if scroll.evaluate('el => el.scrollWidth <= el.clientWidth'):
                continue
            scroll.evaluate('el => el.scrollLeft = el.scrollWidth')
            assert scroll.evaluate('el => el.scrollLeft > 0')
            scroll.evaluate('el => el.scrollLeft = 0')
        if scene == 'detail-error':
            expect(root.locator('[name=percentage]')).to_have_value('105')
            expect(root.locator('[name=percentage]')).to_have_attribute('aria-invalid', 'true')
            expect(root.locator('[name=explanation]')).to_have_value('Sentetik açıklama <korunur>.')
        if scene == 'monitoring-error':
            expect(root.locator('[name=year]').first).to_have_value('geçersiz')
            expect(root.locator('[name=year]').first).to_have_attribute('aria-invalid', 'true')
        # Save the review state before navigation/form checks.
        for disclosure in root.locator('details').all():
            disclosure.locator('summary').click()
        if scene == 'index-file-required':
            root.get_by_role('button', name='Yükle ve doğrula').click()
            assert root.locator('[name=file]').evaluate('el => el.validity.valueMissing')
            assert not any(data is not None for _, data in calls)
        folder = os.getenv('CIVENSA_CIV145_SCREENSHOTS')
        if folder and width in (1440, 390):
            target = Path(folder); target.mkdir(parents=True, exist_ok=True)
            if scene != 'index-file-required':
                page.evaluate('document.activeElement.blur()')
                page.mouse.move(0, 0)
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=str(target / f'{scene}-{width}.png'), full_page=True)
            if scene == 'plan-populated':
                root.locator('details summary').first.click()
                page.evaluate('document.activeElement.blur(); window.scrollTo(0,0)')
                page.mouse.move(0, 0)
                page.screenshot(path=str(target / f'{scene}-expanded-{width}.png'), full_page=True)
        # Prove the existing forms still carry the exact route, values and CSRF.
        if scene in {'monitoring-populated', 'plan-populated'}:
            form = root.locator('form[method=get]').first
            values = form.evaluate('el => Object.fromEntries(new FormData(el))')
            form.locator('button').click()
            assert parse_qs(urlsplit(calls[-1][0]).query, keep_blank_values=True) == {k: [v] for k, v in values.items()}
        elif scene in {'detail-populated', 'import-populated', 'index-populated'}:
            form = root.locator('form[method=post]').first
            if scene == 'index-populated':
                form.locator('[name=file]').set_input_files({'name': 'sentetik.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'buffer': workbook()})
            else:
                expected = form.evaluate('el => Object.fromEntries(new FormData(el))')
                endpoint = form.get_attribute('action')
                form.locator('button').first.click()
                assert calls[-1] == (endpoint, {k: [v] for k, v in expected.items()})
        assert not errors


def test_standard_numbers_are_display_only(ic_client, db, sample):
    from lxml.html import fromstring
    from app import internal_control_service as ic

    login(ic_client, sample['strategy'].email)
    codes = [('KOS', 'KOS1', '1'), ('RDS', 'RDS5', '5'), ('BİS', 'BİS13', '13')]
    plan = saved(db, sample, workbook([action_row(**{
        '0': component, '1': standard, '2': standard + '.1', '5': standard + '.1.1',
    }) for component, standard, _ in codes]))
    ic.activate_plan(db, sample['strategy'], plan.id)
    db.commit()
    from datetime import timedelta
    period = monitoring.open_period(db, sample['strategy'], plan.id, 2027, 1,
                                    monitoring.today(db) + timedelta(days=1000))
    db.commit()
    response = ic_client.get('/internal-control/monitoring')
    before = list(response.context['counts'])
    markup = frozen(response)
    rows = fromstring(markup).xpath('//table')[-1].xpath('./tbody/tr')
    assert [(r[0].text_content(), r[1].text_content()) for r in rows] == [
        (component, number) for component, _, number in codes]
    assert list(monitoring.overview(db, sample['strategy'], period)[1]) == before
    assert before == [(component, standard) for component, standard, _ in codes]
