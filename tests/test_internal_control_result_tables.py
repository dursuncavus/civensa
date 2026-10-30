"""CIV-161: rendered text contract and Chromium geometry on disposable data."""
from hashlib import sha256
from html.parser import HTMLParser
import os
from pathlib import Path
import re

from jinja2 import ChoiceLoader, DictLoader
import pytest

from app import internal_control_questionnaire_service as q
from app.main import app, require_user, templates
from test_internal_control_monitoring import monitoring, approve
from test_internal_control_questionnaire import questionnaire
from test_sidebar_ui import browser
from test_section_index_design import contrast

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[1]
BASE_HASHES = {'monitoring.html': 'e0855fc6b48941ece746418038bbd629410578e4e9dc3fa9268bcceb2b104e3c', 'questionnaire_overview.html': '8a5df40acbb1e341c2fcb821c2d0092ad56f78812c45e26d5a181ea244301156'}


def original_source(name):
    source = (ROOT / 'app/templates/internal_control' / name).read_text()
    source = source.replace('class="card ic-results-card"', 'class="card"')
    source = re.sub(r' class="ic-result-table ic-result-table-(?:scores|summary)"', '', source)
    source = source.replace(' class="{{ \'ic-total-row\' if row == question_results.total else \'\' }}"', '')
    assert sha256(source.encode()).hexdigest() == BASE_HASHES[name], 'Only the authorized class attributes may change'
    return source


class Cells(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.cells = []
        self.current = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag in ('th', 'td'):
            self.current = []

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag in ('th', 'td') and self.current is not None:
            self.cells.append((tag, ' '.join(''.join(self.current).split())))
            self.current = None


@pytest.fixture
def result_screen(db, questionnaire, client):
    d = questionnaire
    # Read official wording at test time; no workbook or question copy is committed.
    workbook = (ROOT / 'docs/internal-control/ic-kontrol-soru-formu-70.xlsx').read_bytes()
    assert len(q.parse_questions(workbook)) == 70
    catalogue = q.save_list(db, d['strategy'], 'Sentetik görünüm denemesi', workbook)
    q.attach(db, d['strategy'], d['period'].id, catalogue.id,
             [batch.department_id for batch in d['question_batches']], 1)
    db.commit()
    app.dependency_overrides[require_user] = lambda: d['strategy']
    return d, f'/internal-control/monitoring?period_id={d["period"].id}'


def approve_synthetic(db, d):
    questions = q.questions(db, d['period'].id)
    for batch, actor, offset in ((d['question_owned'], d['user'], 0),
                                  (d['question_other'], d['collaborator'], 1)):
        data = {f'answer_{row["code"]}': ('yes', 'no', 'developing')[(i + offset) % 3]
                for i, row in enumerate(questions)}
        q.save_answers(db, actor, batch.id, 0, data, submit=True)
        q.transition(db, d['strategy'], batch.id, 'approve', 2)
    db.commit()
    approve(db, d, d['owned'], status='completed', percentage='100')


def test_rendered_cells_and_class_contract(db, result_screen, client):
    d, path = result_screen
    sources = {f'internal_control/{name}': original_source(name) for name in BASE_HASHES}
    old_env = templates.env.overlay(loader=ChoiceLoader([DictLoader(sources), templates.env.loader]))
    for approved in (False, True):
        if approved:
            approve_synthetic(db, d)
        response = client.get(path)
        assert response.status_code == 200
        response.context['request'].state.pp_attempt_rendered = False
        before = old_env.get_template(response.template.name).render(response.context)
        assert Cells(before).cells == Cells(response.text).cells
        assert response.text.count('class="ic-result-table ') == 4
        assert response.text.count('class="ic-total-row"') == 2
        assert len(response.context['question_results']['pending']) == (1 if approved else 3)


def test_result_geometry_and_contrast(db, result_screen, client, browser):
    d, path = result_screen
    evidence = os.getenv('CIVENSA_CIV161_EVIDENCE')
    sources = {f'internal_control/{name}': original_source(name) for name in BASE_HASHES}
    old_env = templates.env.overlay(loader=ChoiceLoader([DictLoader(sources), templates.env.loader]))
    mode = {'before': False}
    with browser.new_context() as context:
        def serve(route):
            response = client.get(route.request.url)
            body = response.content
            if mode['before']:
                if hasattr(response, 'template'):
                    response.context['request'].state.pp_attempt_rendered = False
                    body = old_env.get_template(response.template.name).render(response.context).encode()
                elif route.request.url.endswith('/internal-control.css'):
                    body = body.split(b'/* CIV-161:')[0]
            headers = dict(response.headers)
            headers.pop('set-cookie', None)
            headers.pop('content-length', None)
            route.fulfill(status=response.status_code, headers=headers, body=body)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        for approved in (False, True):
            if approved:
                approve_synthetic(db, d)
            for width in (1440, 390):
                page.set_viewport_size({'width': width, 'height': 1000 if width == 1440 else 844})
                for before in ((True, False) if evidence else (False,)):
                    mode['before'] = before
                    page.goto('http://testserver' + path)
                    page.evaluate('document.fonts.ready')
                    if not before:
                        tables = page.locator('.ic-result-table')
                        assert tables.count() == 4
                        component = page.get_by_role('region', name='Bileşen özeti', exact=True)
                        question = page.get_by_role('region', name='Soru özeti', exact=True)
                        for index in (2, 3, 4):
                            a = component.locator(f'thead th:nth-child({index})').bounding_box()
                            b = question.locator(f'thead th:nth-child({index})').bounding_box()
                            assert abs(a['x'] - b['x']) <= 1
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        for table in tables.all():
                            assert table.evaluate("e => getComputedStyle(e).tableLayout") == 'fixed'
                            for cell in table.locator('tr > :not(:first-child)').all():
                                style = cell.evaluate("e => { const s = getComputedStyle(e); return [s.textAlign,s.fontVariantNumeric,s.whiteSpace,s.color,s.backgroundColor] }")
                                assert style[:2] == ['right', 'tabular-nums']
                                if cell.evaluate('e => e.tagName') == 'TD':
                                    assert style[2] == 'nowrap'
                                assert contrast((style[3], 'rgb(255, 255, 255)' if style[4] == 'rgba(0, 0, 0, 0)' else style[4])) >= 4.5
                            for cell in table.locator('tbody th[scope=row]').all():
                                style = cell.evaluate("e => {const s=getComputedStyle(e); return [s.color,s.backgroundColor,s.textAlign,s.fontWeight]}")
                                assert contrast((style[0], style[1])) >= 4.5
                                assert style[2] == 'left'
                                assert style[3] == ('500' if cell.locator('..').get_attribute('class') == 'ic-total-row' else '400')
                            for header in table.locator('thead th').all():
                                assert header.evaluate("""e => {
                                    const s = getComputedStyle(e);
                                    const canvas = document.createElement('canvas');
                                    const ctx = canvas.getContext('2d'); ctx.font = s.font;
                                    const available = e.clientWidth - parseFloat(s.paddingLeft) - parseFloat(s.paddingRight);
                                    return e.textContent.trim().split(/\\s+/).every(word => ctx.measureText(word).width <= available + 1)
                                        && e.clientHeight <= 2 * parseFloat(s.lineHeight) + parseFloat(s.paddingTop) + parseFloat(s.paddingBottom) + 1;
                                }"""), header.inner_text()
                            if width == 1440:
                                assert table.locator('..').evaluate('e => e.scrollWidth <= e.clientWidth')
                            if width == 390:
                                assert table.locator('..').evaluate('e => e.scrollWidth > e.clientWidth')
                                table.locator('..').evaluate('e => e.scrollLeft = e.scrollWidth')
                                assert table.locator('thead th').last.bounding_box()['x'] < width
                                table.locator('..').evaluate('e => e.scrollLeft = 0')
                        for heading in page.locator('.ic-results-card h3').all():
                            assert heading.evaluate('e => [getComputedStyle(e).marginTop,getComputedStyle(e).marginBottom]') == ['24px', '12px']
                    if evidence:
                        target = Path(evidence)
                        target.mkdir(parents=True, exist_ok=True)
                        for label, locator in (
                            ('sonuclar', page.locator('section').filter(has=page.get_by_role('heading', name='Soru formu sonuçları', exact=True))),
                            ('resmi-ozet', page.locator('section').filter(has=page.get_by_role('heading', name='Eylem bazında resmî rapor özeti', exact=True))),
                        ):
                            image = target / f'{"once" if before else "sonra"}-{label}-{"onayli" if approved else "bos"}-{width}.png'
                            locator.screenshot(path=str(image))
                            assert image.stat().st_size <= 1_500_000
