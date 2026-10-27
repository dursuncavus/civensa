"""CIV-128: concise reconciliation statuses and on-demand row details."""
from decimal import Decimal
from html.parser import HTMLParser
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect
from sqlalchemy import select

from app.models import ActivityCostValue
from test_section_index_design import contrast
from test_sidebar_ui import browser

pytestmark = pytest.mark.postgres


class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    def walk(self, tag=None):
        for child in self.children:
            if isinstance(child, Node):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.walk(tag)

    def text(self):
        return ''.join(child.text() if isinstance(child, Node) else child
                       for child in self.children)

    def has_class(self, name):
        return name in self.attrs.get('class', '').split()


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.root = self.current = Node()
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        child = Node(tag, attrs, self.current)
        self.current.children.append(child)
        if tag not in {'input', 'link', 'meta', 'br', 'hr', 'img', 'source', 'wbr'}:
            self.current = child

    def handle_endtag(self, tag):
        node = self.current
        while node.parent:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def element_with_class(root, name):
    return next((node for node in root.walk() if node.has_class(name)), None)


def set_source_mismatch(db, sample):
    value = db.scalar(select(ActivityCostValue).where(
        ActivityCostValue.activity_id == sample['activity'].id,
        ActivityCostValue.year == 2027,
        ActivityCostValue.funding_type == 'total',
    ))
    value.source_amount = Decimal('130.00')
    db.commit()


@pytest.mark.parametrize('with_error', [False, True])
def test_reconciliation_status_counts_details_and_summary_panel(client, db, sample, with_error):
    if with_error:
        set_source_mismatch(db, sample)
    response = client.get(f"/program/{sample['department'].id}?period_id={sample['period'].id}")
    assert response.status_code == 200
    expected_rows = response.context['reconciliation']
    section = next(node for node in Document(response.text).root.walk()
                   if node.attrs.get('id') == 'pp-reconciliation')
    tbody = next(section.walk('tbody'))
    rows = list(tbody.walk('tr'))
    assert len(rows) == len(expected_rows)

    for row_node, row in zip(rows, expected_rows):
        status = element_with_class(row_node, 'pp-reconciliation-status')
        assert status and status.text().strip() == row['status']
        expected_status_class = {
            'Yayın engeli': 'pp-status-danger',
            'Uyarı': 'pp-status-warning',
            'Mutabık': 'pp-status-success',
        }[row['status']]
        assert status.has_class(expected_status_class)
        count = element_with_class(row_node, 'pp-reconciliation-count')
        expected_count = ' · '.join(
            value for value in (
                f"{len(row['errors'])} hata" if row['errors'] else '',
                f"{len(row['warnings'])} uyarı" if row['warnings'] else '',
            ) if value
        )
        assert (count.text().strip() if count else '') == expected_count

        details = list(row_node.walk('details'))
        assert len(details) == bool(row['errors'] or row['warnings'])
        if not details:
            continue
        detail = details[0]
        assert 'open' not in detail.attrs
        assert next(detail.walk('summary')).text().strip() == 'Ayrıntı'
        messages = [(node.attrs.get('class', ''), node.text().strip())
                    for node in detail.walk()
                    if node.tag == 'p' and (node.has_class('field-error') or node.has_class('muted'))]
        assert messages == [
            *[('field-error', message) for message in row['errors']],
            *[('muted', message) for message in row['warnings']],
        ]

    error_rows = sum(bool(row['errors']) for row in expected_rows)
    panel = element_with_class(section, 'pp-reconciliation-alert')
    if error_rows:
        assert panel and panel.text().strip() == (
            f'{error_rows} satırda yayın engeli var. Ayrıntıyı ilgili satırdaki '
            '“Ayrıntı” bağlantısından açın.'
        )
    else:
        assert panel is None


@pytest.mark.parametrize('width', [1440, 390])
def test_reconciliation_details_browser_layout_and_evidence(
    browser, client, db, sample, width
):
    set_source_mismatch(db, sample)

    def serve(route):
        request = route.request
        response = client.request(
            request.method, request.url, content=request.post_data_buffer,
            headers={key: request.headers[key] for key in ('content-type', 'accept')
                     if key in request.headers},
            follow_redirects=False,
        )
        headers = dict(response.headers)
        headers.pop('set-cookie', None)
        route.fulfill(status=response.status_code, headers=headers, body=response.content)

    with browser.new_context(viewport={'width': width, 'height': 900}) as context:
        context.route('http://testserver/**', serve)
        page = context.new_page()
        page.goto(f"http://testserver/program/{sample['department'].id}?period_id={sample['period'].id}")
        section = page.locator('#pp-reconciliation')
        expect(section).to_be_visible()
        details = section.locator('details')
        assert details.count() > 0
        assert details.evaluate_all('els => els.every(el => !el.open)')
        assert page.evaluate('document.documentElement.scrollWidth === window.innerWidth')
        table_wrap = section.locator('.table-wrap')
        if width == 1440:
            assert table_wrap.evaluate('el => el.scrollWidth <= el.clientWidth')
        else:
            assert table_wrap.evaluate('el => el.scrollWidth > el.clientWidth')

        details.first.locator('summary').click()
        expect(details.first.locator('p.field-error, p.muted').first).to_be_visible()
        assert page.evaluate('document.documentElement.scrollWidth === window.innerWidth')
        color_pairs = section.locator(
            '.pp-reconciliation-status, .pp-reconciliation-count, .pp-reconciliation-alert, '
            'details summary, .field-error, .muted'
        ).evaluate_all(
            '''els => {
              const background = el => {
                for (; el; el = el.parentElement) {
                  const color = getComputedStyle(el).backgroundColor;
                  if (color !== 'rgba(0, 0, 0, 0)') return color;
                }
                return 'rgb(255, 255, 255)';
              };
              return els.map(el => [getComputedStyle(el).color, background(el)]);
            }'''
        )
        assert all(contrast(pair) >= 4.5 for pair in color_pairs), [
            (pair, contrast(pair)) for pair in color_pairs if contrast(pair) < 4.5
        ]

        screenshot_dir = os.getenv('CIVENSA_CIV128_SCREENSHOTS')
        if screenshot_dir:
            folder = Path(screenshot_dir)
            folder.mkdir(parents=True, exist_ok=True)
            details.first.locator('summary').click()
            page.evaluate('window.scrollTo(0, 0)')
            closed = folder / f'in-progress-{width}-closed.png'
            page.screenshot(path=str(closed), full_page=True)
            details.first.locator('summary').click()
            opened = folder / f'in-progress-{width}-open.png'
            page.screenshot(path=str(opened), full_page=True)
            assert closed.stat().st_size <= 1_500_000
            assert opened.stat().st_size <= 1_500_000
