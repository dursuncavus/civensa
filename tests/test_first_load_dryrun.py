"""Keep the replaceable print fixture free of D-45 header-label indicators."""
from pathlib import Path

from app.data_importer import parse_performance_docx
from scripts.first_load_dryrun import scan_names

import pytest
from scripts.first_load_dryrun import inspect_import, parse_book, source_pages


def test_print_book_has_no_header_label_indicators():
    fixture = Path(__file__).parent / 'fixtures/first_load/pp2027_print_d3.docx'
    parsed = parse_performance_docx(fixture.read_bytes())
    assert parsed['summary']['indicator_count'] > 0
    assert not [finding for finding in scan_names(parsed)
                if finding['cause'] == 'header_label_indicator']


@pytest.mark.postgres
def test_idml_rehearsal_loads_every_activity_link_and_keeps_source_issues(db):
    path = Path(__file__).parent / 'fixtures/first_load/source/pp2027_print_d3.idml'
    parsed, conversion = parse_book(path)
    assert conversion['counts']['card'] == conversion['counts']['membership']
    assert all(len(a['source_memberships']) == 1 for d in parsed['departments'] for a in d['activities'])
    assert any('Özel Kalem' in issue and '0006.' in issue for issue in parsed['membership_issues'])
    inspection = inspect_import(db, parsed, path.name)
    assert inspection['apply_error'] is None
    assert inspection['applied']['unlinked_activities'] == 0
    assert inspection['catalogue']['links'] == parsed['summary']['activity_count']
    assert any(result['ready'] for result in inspection['results'])
    assert not any('kataloğu bağlantısı eksik' in error or 'kart bağlantısı eksik' in error
                   for result in inspection['results'] for error in result['errors'])
    park = next(d for d in parsed['departments'] if d['name'] == 'Park ve Bahçeler Müdürlüğü')
    activity = next(a for a in park['activities'] if a['name'].startswith('0007.'))
    costs = {v['funding_type']: v['amount'] for v in activity['costs'] if (v['year'], v['kind']) == (2027, 'budget')}
    assert costs == {'total': '44333709.00', 'inside': '45333709.00', 'outside': '0.00'}
    assert source_pages(parsed, park['name'], activity['name'] + ': toplam farklı') == ['128']
    assert any(t['page'] == '243' for t in parsed['source_tables'].values())
