"""Keep the replaceable print fixture free of D-45 header-label indicators."""
from pathlib import Path

from app.data_importer import parse_performance_docx
from scripts.first_load_dryrun import scan_names

import pytest
from scripts.first_load_dryrun import inspect_import, parse_book, source_pages
from test_book_first_load import book


def test_print_book_has_no_header_label_indicators():
    fixture = Path(__file__).parent / 'fixtures/first_load/pp2027_print_d3.docx'
    parsed = parse_performance_docx(fixture.read_bytes())
    assert parsed['summary']['indicator_count'] > 0
    assert not [finding for finding in scan_names(parsed)
                if finding['cause'] == 'header_label_indicator']


@pytest.mark.postgres
def test_idml_rehearsal_loads_every_activity_link_and_keeps_source_issues(db):
    path = Path(__file__).parent / 'fixtures/first_load/source/pp2027_print_d3.idml'
    parsed, conversion = parse_book(path, exclude_source_tables=[195])
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
    assert parsed['excluded_source_tables'][0]['page'] == '243'
    assert not parsed['rejected_economic_tables']
    from scripts.first_load_audit import audit_results
    audit = audit_results(parsed, inspection['results'])
    assert audit['findings'] and all(f['side'] == 'SOURCE' for f in audit['findings'])
    assert len(audit['findings']) == sum(len(r['errors']) for r in inspection['results'])
    assert not audit['transfers']
    assert {f['group'] for f in audit['findings']} == {
        'activity_total', 'activity_value', 'cross_total', 'economic', 'explanation',
        'finance_missing', 'indicator', 'personnel', 'program_group'}
    halkla = next(r for r in inspection['results'] if r['name'] == 'Halkla İlişkiler Müdürlüğü')
    sixth = next(a for a in halkla['stored']['activities'] if a['name'].startswith('0006.'))
    assert sixth['explanation'].startswith('Çözüm Masası bünyesinde görev yapan personelin')
    assert all(a['explanation'] for a in halkla['stored']['activities'])
    kultur = next(r for r in inspection['results'] if r['name'].startswith('Kültür,'))
    assert all(not a['explanation'] for a in kultur['stored']['activities'] if a['name'].startswith(('0015.', '0016.', '0017.')))


def test_full_idml_still_rejects_p243_without_rehearsal_exclusion():
    path = Path(__file__).parent / 'fixtures/first_load/source/pp2027_print_d3.idml'
    parsed, _ = parse_book(path)
    assert 'membership_issues' in parsed and 'source_tables' in parsed
    assert parsed['rejected_economic_tables'][0]['table_number'] == 195
    assert parsed['excluded_source_tables'] == []
    assert parsed['source_tables']['195']['page'] == '243'


def test_repeatable_exclusions_use_original_word_numbers_and_are_reported(book):
    from scripts.first_load_dryrun import report
    _, _, word = book
    before = word.read_bytes()
    parsed, _ = parse_book(word, exclude_source_tables=[4, 2, 4])
    assert word.read_bytes() == before
    assert [t['table_number'] for t in parsed['excluded_source_tables']] == [2, 4]
    assert parsed['rehearsal_tables']['2']['original_number'] == 3
    inspection = dict(results=[], errors=[], plan={'conflicts': []}, unresolved=[], pending=[], applied=None)
    content = report(parsed, inspection, word, 'test')
    assert content.count('**Provada çıkarıldı — nihai kitapta düzeltilmeli:') == 2
    assert 'T2, kitap s.1; başlık: Alt Program Kapsamında' in content
    assert '--exclude-source-table 2 --exclude-source-table 4' in content
    assert content.index('Provada çıkarıldı') < content.index('Gönderime hazır')
    assert parse_book(word)[0]['excluded_source_tables'] == []
    for bad in [0, 6]:
        with pytest.raises(ValueError, match='tablo numarası bulunamadı'):
            parse_book(word, exclude_source_tables=[bad])
