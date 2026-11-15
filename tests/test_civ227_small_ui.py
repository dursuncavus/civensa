"""CIV-227: small screen fixes from the LOW backlog (D-268, D-251)."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES = Path(__file__).resolve().parents[1] / 'app' / 'templates'
STATIC = Path(__file__).resolve().parents[1] / 'app' / 'static'


def test_progress_table_has_a_narrow_screen_scroll_hint():
    dashboard = (TEMPLATES / 'dashboard.html').read_text(encoding='utf-8')
    hint = '<p class="muted table-scroll-hint">Tüm sütunları görmek için tabloyu yatay kaydırın.</p>'
    assert dashboard.index(hint) < dashboard.index('aria-label="Müdürlük ilerlemesi"')
    css = (STATIC / 'design' / 'dashboard.css').read_text(encoding='utf-8')
    assert '.dashboard-page .table-scroll-hint { display: none;' in css
    assert '@media (max-width: 760px) { .dashboard-page .table-scroll-hint { display: block; } }' in css


def test_resource_table_save_header_does_not_break():
    css = (STATIC / 'activity_sections.css').read_text(encoding='utf-8')
    assert '.ar-table thead th:first-child{white-space:nowrap}' in css
