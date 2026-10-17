"""Keep the replaceable print fixture free of D-45 header-label indicators."""
from pathlib import Path

from app.data_importer import parse_performance_docx
from scripts.first_load_dryrun import scan_names


def test_print_book_has_no_header_label_indicators():
    fixture = Path(__file__).parent / 'fixtures/first_load/pp2027_print_d3.docx'
    parsed = parse_performance_docx(fixture.read_bytes())
    assert parsed['summary']['indicator_count'] > 0
    assert not [finding for finding in scan_names(parsed)
                if finding['cause'] == 'header_label_indicator']
