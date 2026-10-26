"""009/010 frozen controls from phase5 after #132, plus actual browser layout."""
from collections import Counter
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path

import pytest

from app import activity_sections_service as sections
from test_activity_sections import section_client, login, ready_and_freeze
from test_ar_release_chain import reopen, freeze
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres
FROZEN = Path(__file__).parent / 'fixtures/section_index_009_010.html'


TEXT_PAIRS = r"""() => {
  const root = document.querySelector('.section-index-page');
  const background = el => {
    for (; el; el = el.parentElement) {
      const bg = getComputedStyle(el).backgroundColor;
      if (bg !== 'rgba(0, 0, 0, 0)') return bg;
    }
    return 'rgb(255, 255, 255)';
  };
  return [...root.querySelectorAll('*')].filter(el => el.checkVisibility() &&
    el.tagName !== 'OPTION' && (el.matches('select') ||
    [...el.childNodes].some(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim())))
    .map(el => [getComputedStyle(el).color, background(el)]);
}"""


def contrast(pair):
    import re
    def luminance(color):
        rgb = [int(v) / 255 for v in re.findall(r'\d+', color)[:3]]
        return sum(weight * (v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4)
            for weight, v in zip((.2126, .7152, .0722), rgb))
    values = sorted(map(luminance, pair))
    return (values[1] + .05) / (values[0] + .05)


class Contract(HTMLParser):
    """Include values, selected states and actual form nesting; redact only CSRF."""
    def __init__(self, html):
        super().__init__()
        self.main = False
        self.form = None
        self.controls = []
        self.bindings = []
        self.text_stack = []
        self.labels = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'main': self.main = True
        if not self.main: return
        if tag in {'a', 'button', 'label', 'option'}: self.text_stack.append([tag, []])
        if tag == 'form': self.form = (attrs.get('method', 'get'), attrs.get('action', ''))
        if tag not in {'form', 'input', 'button', 'select', 'option', 'textarea', 'a'}: return
        if attrs.get('name') == 'csrf_token': attrs['value'] = '<csrf>'
        control = (tag, tuple(sorted((k, v) for k, v in attrs.items() if k not in {'class', 'style'})))
        self.controls.append(control)
        if tag in {'input', 'button', 'select', 'option', 'textarea'}:
            self.bindings.append((control, self.form))

    def handle_data(self, data):
        if self.main:
            for _, parts in self.text_stack: parts.append(data)

    def handle_endtag(self, tag):
        if self.main and self.text_stack and self.text_stack[-1][0] == tag:
            kind, parts = self.text_stack.pop()
            self.labels.append((kind, ' '.join(''.join(parts).split())))
        if tag == 'main': self.main = False
        if tag == 'form': self.form = None


def assert_frozen(response):
    assert response.status_code == 200
    old = response.template.environment.from_string(FROZEN.read_text()).render(response.context)
    actual, expected = Contract(response.text), Contract(old)
    assert Counter(actual.controls) == Counter(expected.controls)
    assert actual.bindings == expected.bindings
    assert Counter(actual.labels) == Counter(expected.labels)


@pytest.fixture
def filled_index(section_client, db, sample):
    client, docs, _, _ = section_client
    own = docs['birim:' + str(sample['department'].id)]
    for code, status, reason in [('I.A', 'draft', ''), ('I.B', 'ready', ''),
                                  ('I.D', 'not_applicable', 'Sentetik kapsam açıklaması.')]:
        sections.save_section(db, sample['user'], own.id, code,
            [{'type': 'paragraph', 'text': 'Sentetik hizmet değerlendirmesi.'}], status, reason, own.revision)
    db.commit()
    return client, docs


@pytest.mark.parametrize('role', ['strategy', 'department'])
@pytest.mark.parametrize('filters', ['all', 'period', 'section', 'status', 'combined', 'empty'])
def test_009_010_frozen_forms_links_filters_and_visibility(filled_index, sample, role, filters):
    client, docs = filled_index
    token = login(client, sample['strategy' if role == 'strategy' else 'user'].email)
    params = dict(period_id=str(sample['period'].id), section='I.A', status='draft')
    params = {'all': {}, 'period': {'period_id': params['period_id']},
        'section': {'section': 'I.B'}, 'status': {'status': 'ready'},
        'combined': params, 'empty': {**params, 'status': 'not_applicable'}}[filters]
    response = client.get('/activity-sections', params=params)
    assert_frozen(response)
    context = response.context
    assert context['selected_period'] == (int(params['period_id']) if 'period_id' in params else None)
    assert context['selected_section'] == params.get('section', '')
    assert context['selected_status'] == params.get('status', '')
    post = 'action="/activity-sections/years"' in response.text
    assert post == (role == 'strategy')
    if post:
        assert bool(f'name="csrf_token" value="{token}"' in response.text)
    own_id = docs['birim:' + str(sample['department'].id)].id
    links = [dict(attrs)['href'] for tag, attrs in Contract(response.text).controls if tag == 'a']
    exports = [url for url in links if '/export.' in url or '/typeset.json' in url]
    if role == 'department':
        assert all(f'/reports/{own_id}/' in url for url in exports)
    if filters != 'empty':
        assert exports
        for item in context['reports']:
            for section in item['matches']:
                assert f'/activity-sections/reports/{item["report"]["id"]}?code={section["code"]}' in links
                assert not params.get('section') or section['code'] == params['section']
                assert not params.get('status') or section['status'] == params['status']
    else:
        assert not context['reports']
        assert 'Bu filtrelerle rapor bulunamadı. Yıl raporlarını oluşturun veya filtreleri değiştirin.' in response.text


@pytest.mark.parametrize('role', ['strategy', 'department'])
def test_009_010_release_versions_and_reopen_names(section_client, sample, role):
    client, docs, _, _ = section_client
    token = login(client, sample['strategy'].email)
    doc = docs['idare']
    ready_and_freeze(client, token, doc)
    for version in (1, 2):
        login(client, sample['strategy' if role == 'strategy' else 'user'].email)
        response = client.get('/activity-sections')
        assert_frozen(response)
        if role == 'strategy':
            assert 'Onaylı kopya' in response.text
            for number in range(1, version + 1):
                for fmt in ('docx', 'pdf', 'json'):
                    assert f'/reports/{doc.id}/export.{fmt}?version={number}' in response.text
                assert f'/reports/{doc.id}/typeset.json?version={number}' in response.text
        else:
            assert f'/reports/{doc.id}/export.' not in response.text
        token = login(client, sample['strategy'].email)
        assert reopen(client, token, doc).status_code == 200
        response = client.get('/activity-sections')
        assert_frozen(response)
        assert f'Gerekçeyle açıldı · {sample["strategy"].full_name} ·' in response.text
        assert f'(Kullanıcı {sample["strategy"].id})' not in response.text
        context = {**response.context, 'reports': deepcopy(response.context['reports'])}
        report = next(item['report'] for item in context['reports'] if item['report']['id'] == doc.id)
        report['releases'][-1]['reopen']['actor_name'] = ''
        report['releases'][-1]['reopen']['actor_id'] = 999999
        html = response.template.render(context)
        assert 'Gerekçeyle açıldı · Kullanıcı 999999 ·' in html
        report['releases'][-1]['reopen']['actor_name'] = 'Sentetik <Deniz>'
        assert 'Gerekçeyle açıldı · Sentetik &lt;Deniz&gt; ·' in response.template.render(context)
        if version == 1: assert freeze(client, token, doc).status_code == 200


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('role', ['strategy', 'department'])
def test_009_010_grouping_warnings_disclosure_and_mobile(browser, filled_index, sample, width, role):
    from playwright.sync_api import expect
    client, docs = filled_index
    login(client, sample['strategy' if role == 'strategy' else 'user'].email)
    response = client.get('/activity-sections')
    # Legacy/error display contexts exercise both warning paths without corrupting DB data.
    context = deepcopy({k: v for k, v in response.context.items() if k in {'reports', 'report_errors'}})
    context['report_errors'] = [dict(year=2026, document_id=999999,
        message='Sentetik rapor doğrulanamadı. Kaynak kaydını kontrol edin.')]
    item = context['reports'][0]
    section = item['matches'][0]
    item['similarities'][section['code']] = dict(message='Sentetik önceki yıl kaynağı okunamadı.',
        source_url=f'/activity-sections/reports/{item["report"]["id"]}?code={section["code"]}', source_label='Önceki yıl')
    html = response.template.render({**response.context, **context})
    old = response.template.environment.from_string(FROZEN.read_text()).render({**response.context, **context})
    assert Counter(Contract(html).controls) == Counter(Contract(old).controls)
    with browser.new_context(viewport={'width': width, 'height': 900}) as browser_context:
        errors = []
        def serve(route):
            assert route.request.method == 'GET'
            result = client.get(route.request.url)
            headers = dict(result.headers); headers.pop('set-cookie', None)
            route.fulfill(status=result.status_code, headers=headers,
                body=html if route.request.url == 'http://testserver/activity-sections' else result.content)
        browser_context.route('http://testserver/**', serve)
        page = browser_context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://testserver/activity-sections')
        expect(page.get_by_role('status').first).to_contain_text('Sentetik rapor doğrulanamadı.')
        expect(page.locator('[data-ar-similarity]')).to_have_attribute('role', 'status')
        groups = page.locator('.report-group')
        assert groups.count() == len(context['reports'])
        for group, expected in zip(groups.all(), context['reports']):
            expect(group.locator('h3')).to_have_text(f'{expected["report"]["year"]} · {expected["report"]["department"]}')
            assert group.locator('tbody tr').count() == len(expected['matches'])
        summary = page.locator('.section-export > summary').first
        summary.focus(); page.keyboard.press('Enter')
        expect(page.locator('.section-export').first).to_have_attribute('open', '')
        page.keyboard.press('Tab')
        expect(page.get_by_role('link', name='Word olarak indir', exact=True).first).to_be_focused()
        summary.focus(); page.keyboard.press('Space')
        expect(page.locator('.section-export').first).not_to_have_attribute('open', '')
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        pairs = set(map(tuple, page.evaluate(TEXT_PAIRS)))
        for selector in ('.button', '.button.primary', 'summary', 'a', 'select'):
            control = page.locator('.section-index-page ' + selector).filter(visible=True).first
            if control.count():
                control.hover(); control.focus()
                pairs.update(map(tuple, page.evaluate(TEXT_PAIRS)))
        assert all(contrast(pair) >= 4.5 for pair in pairs), pairs
        selects = page.locator('form[method=get] select').all()
        boxes = [el.bounding_box() for el in selects]
        if width == 1440: assert len({round(box['y']) for box in boxes}) == 1
        else:
            assert boxes[0]['y'] < boxes[1]['y'] < boxes[2]['y']
            for table in page.locator('.index-table').all():
                assert table.bounding_box()['width'] <= groups.first.bounding_box()['width']
                assert table.locator('tr').last.bounding_box()['width'] <= table.bounding_box()['width']
            assert page.locator('.section-index-page .shell-table-scroll').evaluate_all('els => els.every(el => el.scrollWidth === el.clientWidth)')
        page.goto('http://testserver/activity-sections?section=I.A&status=not_applicable')
        expect(page.locator('.empty-state')).to_contain_text('Bu filtrelerle rapor bulunamadı.')
        expect(page.locator('form[method=get] [name=section]')).to_have_value('I.A')
        expect(page.locator('form[method=get] [name=status]')).to_have_value('not_applicable')
        assert all(contrast(pair) >= 4.5 for pair in page.evaluate(TEXT_PAIRS))
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        assert not errors


@pytest.mark.parametrize('width', [1440, 390])
def test_012_resource_save_header_does_not_wrap(browser, section_client, sample, width):
    client, docs, _, _ = section_client
    login(client, sample['user'].email)
    doc = docs['birim:' + str(sample['department'].id)]
    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        def serve(route):
            assert route.request.method == 'GET'
            response = client.get(route.request.url)
            headers = dict(response.headers); headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        for code in ('I.C.1', 'I.C.3', 'I.C.4'):
            page.goto(f'http://testserver/activity-sections/reports/{doc.id}?code={code}')
            for header in page.locator('[data-ar-resource-form] th:first-child').all():
                assert header.inner_text() == 'Kaydet'
                assert header.evaluate('el => getComputedStyle(el).whiteSpace') == 'nowrap'
                assert header.evaluate('el => {const r=document.createRange();r.selectNodeContents(el);return r.getClientRects().length}') == 1
            assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
