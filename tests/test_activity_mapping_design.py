"""CIV-150: frozen mapping contracts, unchanged JS flows and synthetic evidence."""
from collections import Counter
from datetime import datetime
from hashlib import sha256
import os
from pathlib import Path
import re
from types import SimpleNamespace as Record
from urllib.parse import urlsplit

from lxml.html import fromstring
from playwright.sync_api import expect
import pytest

from test_activity_mapping_gaps import strategy_client
from test_section_index_design import TEXT_PAIRS, contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/activity_mapping_start.html'
HOOKS = {'mapping-group', 'mapping-row', 'mapping-select', 'mapping-suggestion',
         'strong', 'muted-suggestion', 'choose-suggestion', 'revert-mapping-batch'}


def render(response, data, *, before=False):
    data['request'].state.pp_attempt_rendered = False
    env = response.template.environment
    source = FROZEN.read_bytes()
    assert sha256(source).hexdigest() == '8a4efb1aa191b39737529b0e5b45ea31b8b888be753c998043d10e98e1370c75'
    template = env.from_string(source.decode()) if before else response.template
    return template.render(data)


def contract(html):
    main = fromstring(html).get_element_by_id('main')
    controls, hooks = [], []
    for el in main.iter():
        classes = tuple(sorted(set(el.get('class', '').split()) & HOOKS))
        attributes = tuple(sorted((k, v) for k, v in el.attrib.items()
            if k == 'id' or k.startswith(('data-', 'aria-'))))
        if classes or attributes:
            # Retain the department/row association used by group.querySelectorAll.
            parents = tuple((p.tag, p.get('data-department'), p.get('data-activity'))
                for p in el.iterancestors() if set(p.get('class', '').split()) & {'mapping-group', 'mapping-row'})
            hooks.append((el.tag, classes, attributes, parents))
        if el.tag in {'a', 'button', 'input', 'select', 'option'}:
            controls.append((el.tag, tuple(sorted((k, v) for k, v in el.attrib.items()
                if k != 'class')), ' '.join(el.text_content().split()) if el.tag in {'a', 'button', 'option'} else ''))
    # Compare every visible text fragment, allowing only the requested reordering.
    texts = Counter(' '.join(t.split()) for t in main.xpath('.//text()[not(ancestor::script or ancestor::style)]') if t.strip())
    return controls, hooks, texts


@pytest.fixture
def queue(strategy_client, sample):
    response = strategy_client.get(f"/activity-mapping?period_id={sample['period'].id}")
    assert response.status_code == 200
    data = dict(response.context)
    choices = [Record(id=701, name='Park bakımı', program=Record(name='Çevre hizmetleri')),
               Record(id=702, name='Yeşil alan', program=Record(name='Çevre hizmetleri'))]
    activities = [Record(id=801, name='Sentetik park bakımı', explanation='Parkların mevsimlik bakımı.'),
                  Record(id=802, name='Sentetik fidan üretimi', explanation=''),
                  Record(id=803, name='Sentetik alan düzenlemesi', explanation='Kart bağlantısı tamamlanmalı.')]
    no_choices = Record(id=804, name='Sentetik yol bakımı', explanation='Gösterge yapısı kontrol edilmeli.')
    data.update(groups=[
        Record(department=Record(id=601), activities=activities, choices=choices, suggestions={
            801: Record(subprogram_id=701, score=.80), 802: Record(subprogram_id=702, score=.35),
            803: Record(subprogram_id=None, score=0)}),
        Record(department=Record(id=602), activities=[no_choices], choices=[], suggestions={
            804: Record(subprogram_id=None, score=0)}),
    ], department_names={601: 'Sentetik Park ve Bahçeler Müdürlüğü', 602: 'Sentetik Fen İşleri Müdürlüğü'},
        mapping_states={801: Record(subprogram=False, card=True, catalogue=True),
                        802: Record(subprogram=False, card=False, catalogue=True),
                        803: Record(subprogram=True, card=False, catalogue=False),
                        804: Record(subprogram=False, card=False, catalogue=False)},
        unresolved_count=4, mapping_counts=Record(subprogram=3, card=3, catalogue=2),
        suggestion_count=2, strong_suggestion_count=1,
        recent_batches=[Record(id='sentetik-150-a', count=2, created_at=datetime(2026, 10, 29, 10),
                               actor=sample['strategy'], status='applied', can_revert=True),
                        Record(id='sentetik-150-b', count=1, created_at=datetime(2026, 10, 28, 9),
                               actor=None, status='reverted', can_revert=False)])
    return response, data


def empty(data):
    return dict(data, groups=[], unresolved_count=0, mapping_counts=Record(subprogram=0, card=0, catalogue=0),
                suggestion_count=0, strong_suggestion_count=0, recent_batches=[])


@pytest.mark.parametrize('state', ['populated', 'no-batches', 'empty', *range(8)])
def test_frozen_controls_hooks_attributes_links_and_all_visible_text(queue, state):
    response, data = queue
    if state == 'empty':
        data = empty(data)
    elif state == 'no-batches':
        data = dict(data, recent_batches=[])
    elif isinstance(state, int):
        data['mapping_states'][801] = Record(subprogram=bool(state & 1), card=bool(state & 2), catalogue=bool(state & 4))
    assert contract(render(response, data)) == contract(render(response, data, before=True))


def test_css_is_local_and_uses_only_existing_tokens(strategy_client):
    css = Path('app/static/design/activity-mapping.css').read_text()
    tokens = Path('app/static/design/tokens.css').read_text()
    assert set(re.findall(r'var\((--[\w-]+)\)', css)) <= set(re.findall(r'(--[\w-]+):', tokens))
    assert not re.search(r'#[\da-fA-F]{3,8}\b|rgba?\(|hsla?\(|--[\w-]+\s*:', css)
    assert 'uppercase' not in css
    for declaration in re.findall(r'(?:font-size|padding|gap|border-radius)\s*:\s*([^;}]+)', css):
        assert 'var(--' in declaration or declaration.strip() == '0'
    assert 'activity-mapping.css' not in strategy_client.get('/dashboard?period_id=1').text


def capture(page, name, width):
    folder = os.getenv('CIVENSA_CIV150_SCREENSHOTS')
    if folder:
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)
        page.evaluate('''() => {
            document.activeElement.blur();
            const content = document.querySelector('.activity-mapping-page') || document.querySelector('#main');
            window.scrollTo(0, Math.max(0, content.getBoundingClientRect().bottom + scrollY - innerHeight));
        }''')
        page.mouse.move(0, 0)
        target = path / f'{name}-{width}.png'
        page.screenshot(path=str(target), full_page=True)
        assert target.stat().st_size <= 1_500_000


def assert_design(page, width, populated):
    root = page.locator('.activity-mapping-page')
    assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
    assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
    script = TEXT_PAIRS.replace('.section-index-page', '.activity-mapping-page')
    pairs = set(map(tuple, page.evaluate(script)))
    for control in root.locator('a,button,input,select').all():
        if control.is_visible() and control.is_enabled():
            control.hover()
            control.focus()
            assert control.evaluate("el => getComputedStyle(el).outlineStyle === 'solid'")
            pairs.update(map(tuple, page.evaluate(script)))
    assert all(contrast(pair) >= 4.5 for pair in pairs), [(p, contrast(p)) for p in pairs if contrast(p) < 4.5]
    for item in root.locator('.mapping-counts > div,.mapping-states,.mapping-choice,.mapping-info,.mapping-csv-import,.snapshot-item,.mapping-filterbar,.section-head').all():
        assert item.bounding_box()['width'] <= 704
    status = root.locator('.mapping-summary .status')
    expect(status).to_have_text('Kontrol gerekli' if populated else 'Hazır')
    if not populated:
        return
    assert root.locator('.mapping-info p').count() == 3
    if width >= 1024:
        file = root.locator('#mappingCsvFile').bounding_box()
        for control in root.locator('.mapping-csv-fields .button').all():
            box = control.bounding_box()
            assert abs(file['y'] + file['height'] - box['y'] - box['height']) <= 1
    filters = root.locator('.mapping-filterbar')
    assert len(filters.evaluate('el => getComputedStyle(el).gridTemplateColumns').split()) == (2 if width >= 1024 else 1)
    for row in root.locator('.mapping-row').all():
        activity, choice = row.locator('.mapping-activity').bounding_box(), row.locator('.mapping-choice').bounding_box()
        if width >= 1024:
            assert abs(activity['y'] - choice['y']) <= 1
            assert choice['x'] >= activity['x'] + activity['width']
        else:
            assert choice['y'] >= activity['y'] + activity['height']
        assert row.locator('.mapping-states > .status').count() == 3
        for badge in row.locator('.mapping-states > .status').all():
            expected = 'success' if 'Tamam' in badge.inner_text() else 'warning'
            assert expected in badge.get_attribute('class').split()
        for text, field in [('Alt program seçilmedi:', 'Alt program:'), ('Kart seçilmedi:', 'Kart:'),
                            ('Resmî katalog bağlantısı yok:', 'Resmî katalog:')]:
            assert row.locator('.mapping-fixes').get_by_text(text, exact=False).count() == int(
                'Eksik' in row.locator('.mapping-states').get_by_text(field, exact=False).inner_text())
    # Suggestions stay compact with their confidence and action on the same line.
    for suggestion in root.locator('.mapping-suggestion:has(button)').all():
        box, button = suggestion.bounding_box(), suggestion.locator('button').bounding_box()
        assert abs(box['height'] - button['height']) <= 1
    bar = root.locator('.sticky-save')
    assert bar.evaluate("el => getComputedStyle(el).position") == 'sticky'
    # The mobile navigation follows the workspace; measure scrolling within this
    # page's content, before the separate navigation region below it.
    end = root.evaluate('el => el.getBoundingClientRect().bottom + scrollY - innerHeight')
    for offset in (0, max(0, end / 2), max(0, end)):
        page.evaluate('(offset) => window.scrollTo(0, offset)', offset)
        expect(bar).to_be_in_viewport(ratio=1)
    expect(root.locator('.mapping-select[data-activity="804"]')).to_be_disabled()


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('before', [True, False], ids=['before', 'after'])
@pytest.mark.parametrize('scene', ['populated', 'empty'])
def test_browser_contract_layout_flows_and_evidence(browser, queue, strategy_client, width, before, scene):
    response, data = queue
    if scene == 'empty':
        data = empty(data)
    html = render(response, data, before=before)
    with browser.new_context(viewport={'width': width, 'height': 900}, locale='tr-TR') as context:
        context.set_default_timeout(5000)
        pending, calls, errors = [], [], []

        def serve(route):
            request = route.request
            path = urlsplit(request.url).path
            if path.startswith('/static/'):
                result = strategy_client.get(request.url)
                route.fulfill(status=result.status_code, headers=dict(result.headers), body=result.content)
            elif path == '/activity-mapping':
                route.fulfill(status=200, content_type='text/html; charset=utf-8', body=html)
            elif path.endswith('/import-preview'):
                calls.append(request)
                pending.append(route)
            elif request.method == 'GET':
                result = strategy_client.get(request.url)
                route.fulfill(status=result.status_code, headers=dict(result.headers), body=result.content)
            else:
                raise AssertionError(f'Unexpected request: {request.method} {path}')

        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f"http://testserver/activity-mapping?period_id={data['period'].id}")
        page.evaluate('document.fonts.ready')
        if not before:
            assert_design(page, width, scene == 'populated')
        capture(page, f"{'before' if before else 'after'}-{scene}", width)
        if scene == 'empty':
            expect(page.get_by_text('Eşleştirme kuyruğu temiz', exact=True)).to_be_visible()
            assert not errors
            return
        group1 = page.locator('.mapping-group[data-department="601"]')
        group2 = page.locator('.mapping-group[data-department="602"]')
        department, search = page.locator('#mappingDepartmentFilter'), page.locator('#mappingSearch')
        department.select_option('602')
        expect(group1).to_be_hidden()
        expect(group2).to_be_visible()
        search.fill('park')
        expect(group2).to_be_hidden()
        department.select_option('')
        expect(group1).to_be_visible()
        expect(group1.locator('.mapping-row:visible')).to_have_count(1)
        search.fill('fidan')
        expect(group1.locator('.mapping-row:visible')).to_have_count(1)
        search.fill('bulunmayan')
        expect(page.locator('.mapping-group:visible')).to_have_count(0)
        search.fill('')
        expect(page.locator('.mapping-group:visible')).to_have_count(2)
        strong = page.locator('.mapping-row[data-activity="801"]')
        weak = page.locator('.mapping-row[data-activity="802"]')
        expect(page.locator('#saveMappingsBottom')).to_be_disabled()
        strong.locator('.choose-suggestion').click()
        expect(strong.locator('select')).to_have_value('701')
        expect(page.locator('#selectedMappingCount')).to_have_text('1')
        expect(page.locator('#saveMappingsBottom')).to_be_enabled()
        weak.locator('.choose-suggestion').click()
        expect(weak.locator('select')).to_have_value('702')
        expect(page.locator('#selectedMappingCount')).to_have_text('2')
        for row in (strong, weak):
            row.locator('select').select_option('')
        page.locator('#selectStrongSuggestions').click()
        expect(strong.locator('select')).to_have_value('701')
        expect(weak.locator('select')).to_have_value('')
        expect(page.locator('#selectedMappingCount')).to_have_text('1')
        strong.locator('select').select_option('')
        expect(page.locator('#saveAllMappings')).to_be_disabled()
        preview, apply = page.locator('#previewMappingCsv'), page.locator('#applyMappingCsv')
        expect(apply).to_be_disabled()
        preview.click()
        assert not calls
        upload = page.locator('#mappingCsvFile')
        upload.set_input_files({'name': 'sentetik.csv', 'mimeType': 'text/csv', 'buffer': b'Faaliyet ID\n801\n'})
        expect(apply).to_be_disabled()
        preview.click()
        expect(preview).to_be_disabled()
        assert len(pending) == 1
        pending.pop().fulfill(status=200, json={'ok': True, 'count': 1})
        expect(preview).to_be_enabled()
        expect(apply).to_be_enabled()
        expect(page.locator('#mappingCsvResult')).to_contain_text('1 faaliyet eşleştirilmeye hazır.')
        if not before:
            assert_design(page, width, True)
        upload.set_input_files({'name': 'duzeltilmis.csv', 'mimeType': 'text/csv', 'buffer': b'Faaliyet ID\n802\n'})
        expect(apply).to_be_disabled()
        preview.click()
        expect(preview).to_be_disabled()
        pending.pop().fulfill(status=200, json={'ok': False, 'errors': ['Sentetik satır 2: alt programı düzeltin.']})
        expect(preview).to_be_enabled()
        expect(apply).to_be_disabled()
        expect(page.locator('#mappingCsvResult')).to_contain_text('Dosya uygulanamaz.')
        preview.click()
        expect(preview).to_be_disabled()
        pending.pop().fulfill(status=422, json={'detail': 'Sentetik CSV kontrol edilemedi.'})
        expect(preview).to_be_enabled()
        expect(apply).to_be_disabled()
        expect(page.locator('#mappingCsvResult')).to_have_text('Sentetik CSV kontrol edilemedi.')
        assert all('period_id=' in request.url for request in calls)
        assert not errors
