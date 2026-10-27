"""CIV-126: frozen list/form contract and synthetic browser acceptance."""
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from starlette.requests import Request

from app.main import app, require_user, templates
from test_section_index_design import Contract, TEXT_PAIRS, contrast
from test_sidebar_ui import browser

FROZEN = Path(__file__).parent / 'fixtures/activity_contract_index_start.html'


class HiddenInputs(HTMLParser):
    """Compare actual CSRF values as well as the shared contract's redacted view."""
    def __init__(self, html):
        super().__init__()
        self.inputs = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'input' and values.get('type') == 'hidden':
            self.inputs.append(values)


class RevisionRows(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.rows = []
        self.row = None
        self.badge = None
        self.reason = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and attrs.get('href', '').startswith('/activity-reports/revisions/'):
            self.row = [attrs['href'], [], '']
        if self.row is not None:
            if tag == 'span' and {'badge', 'status'} & set(attrs.get('class', '').split()):
                self.badge = []
            if tag == 'p': self.reason = []

    def handle_data(self, text):
        if self.badge is not None: self.badge.append(text)
        if self.reason is not None: self.reason.append(text)

    def handle_endtag(self, tag):
        if tag == 'span' and self.badge is not None:
            self.row[1].append(' '.join(''.join(self.badge).split()))
            self.badge = None
        if tag == 'p' and self.reason is not None:
            self.row[2] = ' '.join(''.join(self.reason).split())
            self.reason = None
        if tag == 'li' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def context(scenario, long=False):
    role = 'department' if scenario == 'department' else 'strategy'
    request = Request({'type': 'http', 'scheme': 'http', 'server': ('testserver', 80),
                       'path': '/activity-reports', 'headers': [],
                       'session': {'csrf_token': 'synthetic-csrf'}})
    statuses = [['Onaylı'], ['Nihai onay sonrası iade edildi', 'Taslak'], ['İncelemede']]
    return dict(request=request, user=dict(role=role, full_name='Örnek Kullanıcı', department_id=1),
        revisions=[] if scenario == 'empty' else [dict(id=i + 1, year=2027, revision=3 - i,
            publication_version=2, organization='Örnek Belediyesi' + (' UzunKurumAdı' * 20 if long else ''),
            status_badges=badges, revision_reason='Kaynak kayıt düzeltmesi <örnek> & açıklama.' if i != 2 else '')
            for i, badges in enumerate(statuses)],
        organizations=[dict(id=11, name='Örnek Belediyesi'), dict(id=12, name='İkinci Kurum')],
        publications=[] if scenario in ('no-publications', 'empty', 'department') else [dict(id=i + 21,
            year=2027, version=2 - i, created_at=datetime(2026, 10, 20, 9, tzinfo=timezone.utc), valid=i == 0)
            for i in range(2)])


def assert_contract(ctx):
    source = FROZEN.read_bytes()
    assert sha256(source).hexdigest() == 'ba26b6a53cb7000bb123174bdd35668c7b26d1f7a8c30e4fe605def1053305ab'
    old = templates.env.from_string(source.decode()).render(ctx)
    new = templates.env.get_template('activity_contract_index.html').render(ctx)
    before, after = Contract(old), Contract(new)
    assert after.controls == before.controls
    assert after.bindings == before.bindings
    assert HiddenInputs(new).inputs == HiddenInputs(old).inputs
    # Line-per-element formatting adds whitespace between nested select options.
    def labels(contract):
        return [(tag, ''.join(value.split()) if tag == 'label' else value)
                for tag, value in contract.labels]
    assert labels(after) == labels(before)
    assert RevisionRows(new).rows == RevisionRows(old).rows
    for row, revision in zip(RevisionRows(new).rows, ctx['revisions'], strict=True):
        assert row[0] == f'/activity-reports/revisions/{revision["id"]}'
        assert row[1] == revision.get('status_badges', [])
    return old, new


@pytest.mark.parametrize('scenario', ['strategy', 'no-publications', 'department', 'empty'])
def test_frozen_links_form_options_required_and_revision_badges(scenario):
    old, new = assert_contract(context(scenario))
    assert '<style>' not in new
    assert 'Faaliyet raporları</h1>' in new
    assert 'activity-reports.css' in new
    # The title is the only wording change, including all explanatory prose.
    def text(html):
        import re
        main = html.split('<main ', 1)[1].split('</main>', 1)[0]
        main = re.sub(r'<style>.*?</style>', '', main, flags=re.S)
        return ''.join(re.sub(r'<[^>]*>', '', main).split())
    assert text(new) == text(old).replace('FaaliyetRaporları', 'Faaliyetraporları', 1)


@pytest.mark.postgres
def test_actual_get_contract_and_page_local_css(client, sample):
    for role in ('strategy', 'user'):
        app.dependency_overrides[require_user] = lambda: sample[role]
        response = client.get('/activity-reports')
        assert response.status_code == 200
        assert_contract(response.context)
        assert 'activity-reports.css' not in client.get('/dashboard').text


@pytest.mark.parametrize('scenario', ['strategy', 'no-publications', 'department', 'empty'])
@pytest.mark.parametrize('width', [1440, 1024, 620, 390])
def test_browser_layout_header_contrast_and_evidence(browser, client, scenario, width, tmp_path):
    old, new = assert_contract(context(scenario))
    with browser.new_context(viewport={'width': width, 'height': 1000}, locale='tr-TR') as bc:
        html = old
        def serve(route):
            if urlsplit(route.request.url).path == '/activity-reports':
                route.fulfill(status=200, content_type='text/html', body=html)
            else:
                result = client.get(route.request.url)
                headers = dict(result.headers)
                headers.pop('set-cookie', None)
                route.fulfill(status=result.status_code, headers=headers, body=result.content)
        bc.route('http://testserver/**', serve)
        page = bc.new_page()
        page.goto('http://testserver/activity-reports')
        page.wait_for_load_state('networkidle')
        page.evaluate('document.fonts.ready')
        header_before = page.locator('.page-header').bounding_box()
        html = new
        page.reload()
        page.wait_for_load_state('networkidle')
        page.evaluate('document.fonts.ready')
        page.evaluate('window.scrollTo(0, 0)')
        header = page.locator('.page-header')
        assert header.bounding_box() == header_before
        assert header.evaluate('el => getComputedStyle(el).flexWrap') == ('wrap' if width <= 1100 else 'nowrap')
        root = page.locator('.activity-reports-page')
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
        assert root.locator('*').evaluate_all("els => els.every(el => getComputedStyle(el).textTransform !== 'uppercase')")
        for row in root.locator('.revision-row').all():
            box = row.bounding_box()
            assert box['width'] <= 44 * 16
            link = row.locator('.revision-heading > a')
            link_box = link.bounding_box()
            first_badge = row.locator('.status').first.bounding_box()
            reason = row.locator('.revision-reason')
            if reason.count():
                reason_box = reason.bounding_box()
                heading_box = row.locator('.revision-heading').bounding_box()
                assert reason_box['y'] >= heading_box['y'] + heading_box['height']
            if width == 1440:
                badge_center = first_badge['y'] + first_badge['height'] / 2
                badge_gap = first_badge['x'] - (link_box['x'] + link_box['width'])
                assert link_box['y'] <= badge_center <= link_box['y'] + link_box['height']
                assert 0 < badge_gap <= 16
                meta = link.locator('.revision-meta')
                assert meta.evaluate('el => getComputedStyle(el).display') == 'inline'
                text_rects = link.evaluate("""el => {
                    const meta = el.querySelector('.revision-meta');
                    const rect = node => {
                        const range = document.createRange();
                        range.selectNodeContents(node);
                        const box = range.getBoundingClientRect();
                        return {top: box.top, bottom: box.bottom};
                    };
                    for (const node of el.childNodes) {
                        if (node === meta) break;
                        if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
                            return {organization: rect(node), metadata: rect(meta)};
                        }
                    }
                }""")
                assert text_rects['metadata']['top'] < text_rects['organization']['bottom']
                assert text_rects['metadata']['bottom'] > text_rects['organization']['top']
            for badge in row.locator('.status').all():
                b = badge.bounding_box()
                assert 0 <= b['x'] - box['x'] < 44 * 16
                assert b['x'] + b['width'] <= box['x'] + box['width'] + 1
        if scenario == 'strategy':
            fields = [root.locator(f'[name={name}]').bounding_box() for name in ('organization_id', 'publication_id')]
            assert (fields[0]['y'] == fields[1]['y']) == (width >= 1024)
        script = TEXT_PAIRS.replace('.section-index-page', '.activity-reports-page')
        pairs = set(map(tuple, page.evaluate(script)))
        for control in root.locator('a, button, select').all():
            control.hover()
            control.focus()
            pairs.update(map(tuple, page.evaluate(script)))
        assert pairs
        assert all(contrast(pair) >= 4.5 for pair in pairs), [(p, contrast(p)) for p in pairs if contrast(p) < 4.5]
        if width in (1440, 390):
            folder = Path(os.getenv('CIVENSA_CIV126_SCREENSHOTS', str(tmp_path)))
            folder.mkdir(parents=True, exist_ok=True)
            page.evaluate('document.activeElement.blur()')
            page.mouse.move(0, 0)
            page.evaluate('window.scrollTo(0, 0)')
            path = folder / f'{scenario}-{width}.png'
            page.screenshot(path=str(path), full_page=True)
            assert path.stat().st_size <= 1_500_000
        # Stress wrapping separately from the readable evidence data.
        html = assert_contract(context(scenario, long=True))[1]
        page.reload()
        assert page.evaluate('document.documentElement.scrollWidth === innerWidth')
