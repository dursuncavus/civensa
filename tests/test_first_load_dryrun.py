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
    assert parsed['excluded_source_tables'] == []
    assert next(t for t in conversion['non_printed'] if t['story'] == 'u4258')['spread_pages'] == ['242', '243']
    assert not parsed['rejected_economic_tables']
    from scripts.first_load_audit import audit_results, checklist
    audit = audit_results(parsed, inspection['results'])
    assert audit['findings'] and all(f['side'] == 'SOURCE' for f in audit['findings'])
    assert len(audit['findings']) == sum(len(r['errors']) for r in inspection['results'])
    assert not audit['transfers']
    presentation = checklist(parsed, inspection['results'], audit)
    assert (presentation['book_messages'], presentation['allocation_messages'], presentation['mixed_messages']) == (370, 112, 28)
    assert presentation['book_messages'] + presentation['allocation_messages'] == len(audit['findings']) == 482
    assert len(presentation['items']) == 158
    assert presentation['only_allocation'] == []
    assert all(item['action'] for item in presentation['items'])
    assert sum(allocation['messages'] for allocation in presentation['allocations'].values()) == 140
    assert set(presentation['allocations']) == {
        'Fen İşleri Müdürlüğü', 'İnsan Kaynakları ve Eğitim Müdürlüğü', 'Yazı İşleri Müdürlüğü'}
    mixed_personnel = next(f for f in audit['findings'] if {
        'program_group_unallocated', 'personnel_total_mismatch'} <= {c['cause'] for c in f.get('causes', [])})
    book_item = next(i for i in presentation['items'] if i['department'] == mixed_personnel['department']
                     and mixed_personnel['error'] in i['messages'])
    assert len({c['table'] for c in book_item['cells']}) == 2  # Economic and common personnel tables, not programme cards.
    from scripts.first_load_dryrun import report
    content = report(parsed, inspection, path, 'test')
    book_list = content.split('## Pazartesi — müdürlük bazında yalnız kitap düzeltme listesi')[1]
    assert book_list.count('- [ ] ') == book_list.count('  Yapılacak: ') == 158
    assert 'program grubu' not in book_list.lower()
    assert 'Program Grubu Belirlenmeli' not in book_list
    assert '45.333.709,00 + 0,00 = 45.333.709,00, kitapta 44.333.709,00 yazıyor (fark -1.000.000,00)' in book_list
    assert {f['group'] for f in audit['findings']} == {
        'activity_total', 'activity_value', 'cross_total', 'economic', 'explanation',
        'finance_missing', 'indicator', 'personnel', 'program_group'}
    halkla = next(r for r in inspection['results'] if r['name'] == 'Halkla İlişkiler Müdürlüğü')
    sixth = next(a for a in halkla['stored']['activities'] if a['name'].startswith('0006.'))
    assert sixth['explanation'].startswith('Çözüm Masası bünyesinde görev yapan personelin')
    assert all(a['explanation'] for a in halkla['stored']['activities'])
    kultur = next(r for r in inspection['results'] if r['name'].startswith('Kültür,'))
    assert all(not a['explanation'] for a in kultur['stored']['activities'] if a['name'].startswith(('0015.', '0016.', '0017.')))


def test_pasteboard_p243_is_excluded_without_rehearsal_exclusion():
    path = Path(__file__).parent / 'fixtures/first_load/source/pp2027_print_d3.idml'
    parsed, _ = parse_book(path)
    assert 'membership_issues' in parsed and 'source_tables' in parsed
    assert parsed['rejected_economic_tables'] == []
    assert parsed['excluded_source_tables'] == []
    assert all(t['page'] != '243' for t in parsed['source_tables'].values())


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
    headings = ['Kitap temiz mi:', 'Kitap kontrol maddesi:',
                'Yalnız program grubu dağılımı bekleyen müdürlük:', 'Gönderime hazır:', 'Provada çıkarıldı']
    assert [content.index(text) for text in headings] == sorted(content.index(text) for text in headings)
    assert parse_book(word)[0]['excluded_source_tables'] == []
    for bad in [0, 6]:
        with pytest.raises(ValueError, match='tablo numarası bulunamadı'):
            parse_book(word, exclude_source_tables=[bad])


def test_amount_comparison_aligns_insertions_and_preserves_missing_states():
    from scripts.first_load_dryrun import amount_changes
    old = dict(id='old-export-id', page='1', department='Örnek', label='T1', rows=[
        ['Faaliyetler', '2027 Bütçe', '2028 Tahmin'],
        ['A', '', '-'], ['B', '0,00', '1.000,00'], ['Toplam', '0,00', '1.000,00']])
    new = dict(old, id='new-export-id', rows=[
        old['rows'][0], ['A', '-', '0,00'], ['B', '0,00', '1.250,50'],
        ['Yeni faaliyet', '50,00', ''], ['Toplam', '50,00', '1.250,50']])
    changes = amount_changes({('other',): old}, {('other',): new})
    assert len(changes) == 7
    blank = next(c for c in changes if c['old'] == 'BOŞ' and c['new'] == '-')
    assert blank['difference'] == 'Hesaplanamaz'
    assert next(c for c in changes if c['old'] == '-' and c['new'] == '0,00')['difference'] == 'Hesaplanamaz'
    assert next(c for c in changes if c['old'] == '1.000,00' and c['new'] == '1.250,50')['difference'] == '250,5'
    assert sum(c['old'] == 'YOK (satır/hücre yok)' for c in changes) == 2
    assert next(c for c in changes if 'Toplam' in c['row'])['row'].startswith('r4 → r5')
