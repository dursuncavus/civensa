"""CIV-135: frozen 007/008 behavior and synthetic browser acceptance."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from jinja2 import ChoiceLoader, DictLoader
import pytest
from starlette.requests import Request

from app.main import app, require_user, templates
from test_activity_contract import publish, new_report
from test_section_index_design import TEXT_PAIRS, contrast
from test_sidebar_ui import browser

FIXTURES = Path(__file__).parent / 'fixtures'
FROZEN = {
    'activity_contract_detail.html': ('activity_contract_detail_start.html', 'dc8869b5b5aafb5d77e1221d2555b49784f6fd359f02fc09b2197cec69f47f2e'),
    'activity_evidence_row.html': ('activity_evidence_row_start.html', 'ee11a620110307bbeee3b1c64c60bca482aa440010932d084c6fc62c635a7459'),
}
SCENARIOS = ['strategy-draft', 'department-draft', 'department-error', 'approved',
             'historical', 'previous-differences', 'newer-comparison']


class Behavior(HTMLParser):
    """All attributes of controls, hook attributes, form ownership and template contents.

    Only presentation classes/styles are excluded. CSRF, textarea whitespace,
    invalid/selected/required states, file accept and inert template fields are kept.
    """
    def __init__(self, html):
        super().__init__()
        self.main = False
        self.form = None
        self.in_template = False
        self.controls, self.hooks, self.inert, self.text = [], [], [], []
        self.stack = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'main': self.main = True
        if not self.main: return
        attrs = {k: v for k, v in attrs if k not in ('class', 'style')}
        item = (tag, tuple(sorted(attrs.items())))
        if tag == 'template': self.in_template = True
        if tag == 'form': self.form = item
        if tag in ('form', 'input', 'select', 'textarea', 'option', 'button', 'a'):
            self.controls.append((item, self.form))
        if any(k == 'id' or k.startswith(('data-', 'aria-')) for k in attrs):
            self.hooks.append(item)
        if self.in_template: self.inert.append(('start', item))
        if tag in ('textarea', 'option', 'button', 'a', 'label'):
            self.stack.append((tag, []))

    def handle_data(self, data):
        if not self.main: return
        for _, parts in self.stack: parts.append(data)
        if self.in_template and data.strip():
            self.inert.append(('text', ''.join(data.split())))

    def handle_endtag(self, tag):
        if self.in_template: self.inert.append(('end', tag))
        if self.stack and self.stack[-1][0] == tag:
            kind, parts = self.stack.pop()
            value = ''.join(parts)
            self.text.append((kind, value if kind == 'textarea' else ''.join(value.split())))
        if tag == 'template': self.in_template = False
        if tag == 'form': self.form = None
        if tag == 'main': self.main = False


def render_pair(ctx):
    sources = {}
    for name, (filename, digest) in FROZEN.items():
        raw = (FIXTURES / filename).read_bytes()
        assert sha256(raw).hexdigest() == digest
        sources[name] = raw.decode()
    frozen_env = templates.env.overlay(loader=ChoiceLoader([DictLoader(sources), templates.env.loader]))
    before = frozen_env.get_template('activity_contract_detail.html').render(ctx)
    after = templates.env.get_template('activity_contract_detail.html').render(ctx)
    old, new = Behavior(before), Behavior(after)
    assert new.controls == old.controls
    assert new.hooks == old.hooks
    assert new.inert == old.inert
    assert new.text == old.text
    # Moving the target into the compact actual summary changes reading order only.
    def visible_words(html):
        main = html.split('<main ', 1)[1].split('</main>', 1)[0]
        main = re.sub(r'<style>.*?</style>', '', main, flags=re.S)
        main = re.sub(r'<[^>]+>', ' ', main)
        return Counter(main.split())
    expected = visible_words(before)
    expected.subtract({'Raporu': 1, 'Performans': 1, 'Programı': 1})
    expected.update({'raporu': 1, 'performans': 1, 'programı': 1})
    assert visible_words(after) == +expected
    return before, after


def context(scenario, error_field='source_locator', error_source_index=1, long=False):
    now = datetime(2026, 10, 20, 9, tzinfo=timezone.utc)
    source = dict(source_id='synthetic-source', title='Sentetik hizmet kayıt defteri',
        locator='Sayfa 12', source_revision='2027/1', files=[dict(
            download_url='/api/activity-reports/indicators/101/evidence/synthetic-source/1',
            filename='sentetik-kanit.pdf', version=1, sha256='a' * 64)])
    sources = [source, dict(source_id='second', title='Sentetik izleme çizelgesi',
        locator='Satır 8', source_revision='2027/2', files=[])]
    indicators = []
    for i in range(2):
        definition = dict(name=['Tamamlanan hizmet sayısı', 'Değerlendirilen başvuru sayısı'][i],
            code=f'G.{i+1}', unit='Adet', explanation='Dönem içinde tamamlanan kayıtlar değerlendirilir.',
            calculation_method='Kayıtların toplamı', data_source='Hizmet kayıt defteri',
            targets=[dict(value=100, state='verified')], year=2027, department_id=1)
        if long: definition['name'] += 'UzunGöstergeAdı' * 30
        actuals = [dict(revision=r, value=80 if i == 0 else 100, state='verified' if i == 0 else 'needs_review',
            explanation='' if i == 0 else 'Dönem kayıtları kontrol ediliyor.', evidence=deepcopy(sources),
            entered_by_name='Örnek Kullanıcı', created_at=now,
            needs_deviation_explanation=i == 0, deviation=dict(delta=-20 if i == 0 else 0, corrective_action='İzleme'))
            for r in (1, 2)]
        indicators.append(dict(report_indicator_id=101+i, definition=definition,
            department='Örnek Hizmet Müdürlüğü', actuals=actuals))
    if scenario == 'approved':
        for row in indicators:
            row['actuals'][-1].update(state='verified', explanation='Kaynaklarla doğrulandı.', needs_deviation_explanation=False)
    if long:
        for row in indicators:
            for actual in row['actuals']:
                for evidence in actual['evidence']:
                    evidence['title'] += 'UzunKaynakAdı' * 30
                    if evidence['files']: evidence['files'][0]['filename'] = 'UzunDosyaAdı' * 30 + '.pdf'
    report = dict(year=2027, revision=2, current_revision=2, publication_version=1,
        revision_id=42, report_id=11, organization_id=1, approved=scenario == 'approved',
        returned_after_approval=False, revision_reason='Kaynak kayıtlarının kontrolü.',
        approval=dict(name='Örnek Strateji Müdürü', created_at=now) if scenario == 'approved' else None,
        newer_publication_available=scenario == 'newer-comparison', latest_publication_version=2,
        previous_revision_id=41 if scenario == 'previous-differences' else None,
        differences=[], closure_notes=[dict(department='Örnek Eski Müdürlük', message='Birim kapatıldı. Güncel birim kayıtlarını kontrol edin.')],
        indicators=indicators)
    differences = [dict(before=deepcopy(indicators[0]['definition']), after=deepcopy(indicators[0]['definition']))]
    differences[0]['after'].update(name='Güncellenen hizmet sayısı', targets=[dict(value=120, state='verified')])
    differences += [dict(before=None, after=deepcopy(indicators[1]['definition'])),
                    dict(before=deepcopy(indicators[1]['definition']), after=None)]
    if scenario == 'previous-differences': report['differences'] = differences
    if scenario == 'historical': report['current_revision'] = 3
    request = Request(dict(type='http', scheme='http', server=('testserver', 80),
        path='/activity-reports/revisions/42', headers=[], session={'csrf_token': 'synthetic-csrf'}))
    ctx = dict(request=request, report=report,
        user=dict(role='department' if scenario.startswith('department') else 'strategy',
            position='director', full_name='Örnek Kullanıcı', department_id=1),
        comparison=dict(version=2, differences=differences) if scenario == 'newer-comparison' else None,
        publications=[dict(id=21, version=2, created_at=now), dict(id=20, version=1, created_at=now)])
    if scenario == 'department-error':
        ctx.update(attempted_slot=101, attempted=dict(expected_revision='2', value='12,yanlış' if error_field == 'value' else '12,5', state='invalid' if error_field == 'state' else 'verified',
            explanation='  Denenen açıklama <örnek> & kayıt\nİkinci satır.  ', corrective_action='Denenen işlem'),
            attempted_sources=deepcopy(sources), form_error='İkinci kaynağın konumunu girip tekrar kaydedin.',
            error_field=error_field, error_source_index=error_source_index)
        ctx['attempted_sources'][1].update(locator='', attempted_filename='denenen.xlsx')
    return ctx


@pytest.mark.parametrize('scenario', SCENARIOS)
def test_frozen_contract(scenario):
    _, html = render_pair(context(scenario))
    assert '<style>' not in html
    assert '/static/design/activity-reports.css' in html
    assert '/static/design/activity-report-detail.css' in html
    assert 'details open' not in html


@pytest.mark.parametrize('field', ['value', 'state', 'source_title', 'source_locator',
    'source_revision', 'source_file', 'explanation', 'corrective_action'])
@pytest.mark.parametrize('source_index', [None, 0, 1])
def test_frozen_attempted_values_and_error_attributes(field, source_index):
    render_pair(context('department-error', field, source_index))


def test_frozen_empty_sources_missing_values_and_invalid_add_button():
    ctx = context('department-error', 'source_title')
    ctx['attempted_sources'] = []
    for row in ctx['report']['indicators']:
        row['actuals'] = []
        row['definition']['targets'] = []
    render_pair(ctx)
    ctx = context('department-draft')
    for i, state in enumerate(('missing', 'needs_review')):
        actual = ctx['report']['indicators'][i]['actuals'][-1]
        actual.update(value=None if i == 0 else 0, state=state, evidence=[])
        ctx['report']['indicators'][i]['definition']['targets'][0]['state'] = 'needs_review'
    render_pair(ctx)


@pytest.mark.postgres
def test_real_get_uses_frozen_contract_for_both_roles(client, db, sample):
    report = new_report(client, publish(client, db, sample), sample)
    for role in ('strategy', 'user'):
        app.dependency_overrides[require_user] = lambda: sample[role]
        response = client.get(f'/activity-reports/revisions/{report["revision_id"]}')
        assert response.status_code == 200
        render_pair(response.context)
    assert 'activity-report-detail.css' not in client.get('/dashboard').text


@pytest.mark.parametrize('scenario', SCENARIOS)
@pytest.mark.parametrize('width', [1440, 390])
def test_browser_layout_contrast_and_evidence(browser, client, tmp_path, scenario, width):
    before, after = render_pair(context(scenario))
    with browser.new_context(viewport={'width': width, 'height': 1000}, locale='tr-TR') as bc:
        html = before
        def serve(route):
            if route.request.method == 'POST' and '/actuals' in route.request.url:
                error_html = render_pair(context('department-error'))[1]
                route.fulfill(status=422, content_type='text/html', body=error_html)
            elif urlsplit(route.request.url).path == '/activity-reports/revisions/42':
                route.fulfill(status=200, content_type='text/html', body=html)
            else:
                response = client.get(route.request.url)
                headers = dict(response.headers)
                headers.pop('set-cookie', None)
                route.fulfill(status=response.status_code, headers=headers, body=response.content)
        bc.route('http://testserver/**', serve)
        page = bc.new_page()
        page.goto('http://testserver/activity-reports/revisions/42')
        folder = Path(os.getenv('CIVENSA_CIV135_SCREENSHOTS', str(tmp_path)))
        folder.mkdir(parents=True, exist_ok=True)
        capture = scenario in ('department-draft', 'department-error', 'approved')
        for phase in ('before', 'after'):
            if phase == 'after':
                html = after
                page.reload()
            page.wait_for_load_state('networkidle')
            page.evaluate('document.fonts.ready')
            page.evaluate('document.activeElement.blur()')
            page.mouse.move(0, 0)
            page.evaluate('window.scrollTo(0, 0)')
            if capture:
                path = folder / f'{scenario}-{width}-{phase}.png'
                page.screenshot(path=str(path), full_page=True)
                assert path.stat().st_size <= 1_500_000
        root = page.locator('.activity-report-detail-page')
        def layout():
            assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
            assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
            for selector in ('form', '.actual-summary', '.report-meta', 'details', '[data-latest-actual]', '[role=alert]'):
                for item in root.locator(selector).all():
                    if item.is_visible(): assert item.bounding_box()['width'] <= 44 * 16
        layout()
        assert root.locator('details[open]').count() == 0
        pairs_script = TEXT_PAIRS.replace('.section-index-page', '.activity-report-detail-page')
        pairs = set(map(tuple, page.evaluate(pairs_script)))
        for selector in ('a', '.button', '.primary', 'input', 'select', 'textarea', 'summary'):
            control = root.locator(selector).first
            if control.count() and control.is_visible():
                control.hover()
                control.focus()
                pairs.update(map(tuple, page.evaluate(pairs_script)))
        for details in root.locator('details').all(): details.locator('summary').click()
        pairs.update(map(tuple, page.evaluate(pairs_script)))
        assert pairs
        assert all(contrast(pair) >= 4.5 for pair in pairs), [(p, contrast(p)) for p in pairs if contrast(p) < 4.5]
        add = root.locator('[data-add-evidence]').first
        if add.count():
            rows = root.locator('[data-evidence-rows]').first
            count = rows.locator('[data-evidence-row]').count()
            add.click()
            assert rows.locator('[data-evidence-row]').count() == count + 1
            layout()
            rows.locator('[data-evidence-row]').last.locator('[data-remove-evidence]').click()
            assert rows.locator('[data-evidence-row]').count() == count
        if scenario == 'department-draft':
            # Exercise the real app.js error insertion and keep it above the actual form.
            record = root.locator('[data-draft-record]').first
            record.locator('[name=value]').fill('12,5')
            record.locator('button[type=submit]').click()
            error = record.locator('.draft-error')
            error.wait_for(state='visible')
            form_box, error_box = record.locator('[data-actual-form]').bounding_box(), error.bounding_box()
            assert error_box['y'] + error_box['height'] <= form_box['y']
            assert error.get_attribute('role') == 'alert'
            pairs = set(map(tuple, page.evaluate(pairs_script)))
            assert all(contrast(pair) >= 4.5 for pair in pairs)
            layout()
        # Long unbroken content must wrap in both summaries and source fields.
        html = render_pair(context(scenario, long=True))[1]
        page.goto('http://testserver/activity-reports/revisions/42')
        layout()
