"""CIV-051: independent arithmetic evidence, including incomplete source data."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from scripts.first_load_audit import audit_results
from scripts.first_load_dryrun import institution_report, parse_book
from scripts.institution_summary import (
    audit_institution_tables, column_checks, detail_checks, economic_checks,
    row_checks, share_checks, table_kind, year_groups,
)


def table(kind, rows):
    return dict(kind=kind, id='synthetic', page='731', rows=rows)


def economic():
    return table('economic', [
        ['EKONOMİK KOD', '2027', '→', '→', '→'],
        ['↓', 'HİZMET PROGRAMLARI TOPLAM', 'YÖNETİM VE DESTEK PROGRAMI', 'PROGRAM DIŞI GİDERLER', 'TOPLAM'],
        ['Personel Giderleri', '10,00', '20,00', '0,00', '30,00'],
        ['Yedek Ödenekler', '0,00', '0,00', '5,00', '5,00'],
        ['BÜTÇE İÇİ TOPLAM KAYNAK', '10,00', '20,00', '5,00', '35,00'],
    ])


def directorates(amount='30.00'):
    return dict(departments=[dict(blocks=[], economic_tables=[dict(
        categories=['personnel'], values=[
            dict(category='personnel', year=2027, kind='budget', funding_type='inside',
                 amount=amount, state='needs_review'),
            dict(category='personnel', year=2027, kind='budget', funding_type='outside', amount='0.00'),
        ])])])


@pytest.mark.parametrize('value,status,difference', [('30,00', 'PASS', '0'), ('29,00', 'FAIL', '-1')])
def test_row_total_uses_components_and_signed_difference(value, status, difference):
    source = economic()
    source['rows'][2][4] = value
    result = row_checks(source, year_groups(source))[0]
    assert (result['status'], result['difference']) == (status, Decimal(difference))
    assert (result['page'], result['row'], result['column']) == ('731', 3, 5)


@pytest.mark.parametrize('value', ['', '-', None, 'bad', '↓', '-1,00', '0,0001'])
def test_unknown_component_is_never_zero(value):
    source = economic()
    source['rows'][2][3] = value
    result = row_checks(source, year_groups(source))[0]
    assert result['status'] == 'FAIL'
    assert result['computed'] is result['difference'] is None


def test_column_total_includes_reserve_without_double_counting_subtotals():
    source = economic()
    checks = column_checks(source, {4: [2, 3]}, [1, 2, 3, 4])
    assert all(c['status'] == 'PASS' for c in checks)
    source['rows'][4][4] = '30,00'
    result = column_checks(source, {4: [2, 3]}, [4])[0]
    assert result['computed'] == Decimal(35)
    assert result['difference'] == Decimal(-5)
    assert result['status'] == 'FAIL'


def test_missing_or_duplicate_total_is_a_named_failure():
    source = economic()
    source['rows'].pop()
    results = economic_checks(source, year_groups(source), directorates())
    assert any(r['status'] == 'FAIL' and 'toplam' in r['label'] and 'bulunamadı' in r['note'] for r in results)
    source = economic()
    source['rows'].append(source['rows'][-1][:])
    assert any(r['check'] == 'Okuma / kapsam' for r in economic_checks(source, year_groups(source), directorates()))


@pytest.mark.parametrize('amount,status', [('30.00', 'PASS'), ('29.99', 'FAIL'), (None, 'FAIL')])
def test_economic_cross_check_uses_source_amounts_and_all_directorates(amount, status):
    source = economic()
    parsed = directorates(amount)
    before = deepcopy(parsed)
    checks = economic_checks(source, year_groups(source), parsed)
    cross = [c for c in checks if c['check'] == 'Müdürlük ekonomik çapraz toplamı']
    assert len(cross) == 1
    assert cross[0]['status'] == status
    assert all(c['label'] != 'Yedek Ödenekler' for c in cross)
    assert parsed == before  # Source review state is not changed by arithmetic.


def test_absent_economic_table_does_not_pass_partial_sum():
    source = economic()
    parsed = directorates()
    parsed['departments'].append(dict(blocks=[], economic_tables=[]))
    cross = next(c for c in economic_checks(source, year_groups(source), parsed)
                 if c['check'] == 'Müdürlük ekonomik çapraz toplamı')
    assert cross['status'] == 'FAIL' and cross['computed'] is None


def test_programme_group_category_totals_require_source_allocation():
    source = economic()
    parsed = directorates('10.00')
    values = parsed['departments'][0]['economic_tables'][0]['values']
    for v in values:
        v['program_group'] = 'service'
    other = deepcopy(parsed['departments'][0])
    for v in other['economic_tables'][0]['values']:
        v['program_group'] = 'management'
        if v['funding_type'] == 'inside':
            v['amount'] = '20.00'
    parsed['departments'].append(other)
    checks = economic_checks(source, year_groups(source), parsed)
    groups = [c for c in checks if c['check'] == 'Müdürlük program grubu çapraz toplamı']
    assert len(groups) == 3 and all(c['status'] == 'PASS' for c in groups)
    other['economic_tables'][0]['values'][0]['program_group'] = 'unallocated'
    checks = economic_checks(source, year_groups(source), parsed)
    groups = [c for c in checks if c['check'] == 'Müdürlük program grubu çapraz toplamı']
    assert all(c['status'] == 'FAIL' and c['computed'] is None for c in groups)


def share():
    return table('share', [
        ['MÜDÜRLÜK ADI', '2027 YILI MÜDÜRLÜK BÜTÇESİ', 'TOPLAM BÜTÇEYE ORANI (%)'],
        ['A', '1,00', '33,33'], ['B', '1,00', '33,33'], ['C', '1,00', '33,33'],
        ['TOPLAM', '3,00', '100'],
    ])


def test_share_rounding_and_sum_allow_printed_precision_only():
    source = share()
    assert all(c['status'] == 'PASS' for c in share_checks(source))
    source['rows'][1][2] = '33,34'
    results = share_checks(source)
    assert next(c for c in results if c['row'] == 2 and c['check'] == 'Yüzde oranı')['status'] == 'FAIL'
    source['rows'][1][2] = '31,00'
    assert next(c for c in share_checks(source) if c['check'] == 'Yüzdeler toplamı')['status'] == 'FAIL'


@pytest.mark.parametrize('percentage,status', [('0,01', 'PASS'), ('0,00', 'FAIL')])
def test_exact_half_rounds_up(percentage, status):
    source = table('share', [share()['rows'][0], ['A', '1,00', percentage],
                             ['B', '19.999,00', '100,00'], ['TOPLAM', '20.000,00', '100']])
    result = next(c for c in share_checks(source) if c['row'] == 2 and c['check'] == 'Yüzde oranı')
    assert result['computed'] == Decimal('0.005')
    assert result['status'] == status


def test_share_missing_total_zero_denominator_and_bad_amount_are_failures():
    source = share()
    source['rows'].pop()
    assert share_checks(source)[0]['status'] == 'FAIL'
    source = share()
    source['rows'][-1][1] = '0,00'
    assert all(c['status'] == 'FAIL' for c in share_checks(source) if c['check'] == 'Yüzde oranı')
    source = share()
    source['rows'][1][1] = ''
    assert next(c for c in share_checks(source) if c['check'] == 'Sütun toplamı')['computed'] is None


def detail():
    return table('detail', [
        ['EKONOMİK KOD', '2027', '→', '→'],
        ['↓', 'BÜTÇE İÇİ (TL)', 'BÜTÇE DIŞI (TL)', 'TOPLAM (TL)'],
        ['(1) Parklar', '3,00', '0,00', '3,00'],
        ['(1.1) Ağaçlar', '3,00', '0,00', '3,00'],
        ['Dikim', '1,00', '0,00', '1,00'], ['Bakım', '2,00', '0,00', '2,00'],
        ['FAALİYET MALİYETLERİ ARA TOPLAMI', '3,00', '0,00', '3,00'],
        ['KURUMSAL GENEL YÖNETİM GİDERLERİ', '4,00', '0,00', '4,00'],
        ['Personel', '4,00', '0,00', '4,00'], ['GENEL TOPLAM', '7,00', '0,00', '7,00'],
    ])


def programme_source(value='3,00'):
    return dict(departments=[dict(blocks=[dict(program='Parklar', activity_memberships=[dict(
        table_number=1, row_number=3)])])], rehearsal_tables={'1': dict(book=[
            ['Alt Program Kapsamında Yürütülecek Faaliyet Maliyetleri', '→'],
            ['Faaliyetler', '2027 Bütçe'], ['0001.Dikim', value]])})


def test_hierarchical_subtotals_cover_direct_children():
    source = detail()
    results = detail_checks(source, year_groups(source), programme_source())
    assert all(r['status'] == 'PASS' for r in results)
    source['rows'][4][1] = source['rows'][4][3] = '2,00'
    results = detail_checks(source, year_groups(source), programme_source())
    bad = [r for r in results if r['check'] == 'Sütun toplamı' and r['status'] == 'FAIL']
    assert {(r['row'], r['column']) for r in bad} == {(4, 2), (4, 4)}
    assert all(r['difference'] == -1 for r in bad)


@pytest.mark.parametrize('value,status', [('3,00', 'PASS'), ('2,00', 'FAIL'), ('', 'FAIL')])
def test_programme_cross_check_uses_membership_amount_cells(value, status):
    source = detail()
    results = detail_checks(source, year_groups(source), programme_source(value))
    cross = next(c for c in results if c['check'] == 'Müdürlük program çapraz toplamı')
    assert cross['status'] == status


def test_programme_suffix_normalization_and_distinct_taxonomy_are_explicit():
    source = detail()
    source['rows'][2][0] = '(1) Parklar Programı'
    parsed = programme_source()
    parsed['departments'][0]['blocks'][0]['program'] = 'Parklar Program'
    results = detail_checks(source, year_groups(source), parsed)
    assert all(r['status'] == 'PASS' for r in results)
    parsed['departments'][0]['blocks'][0]['program'] = 'Ormanlar'
    results = detail_checks(source, year_groups(source), parsed)
    assert any(r['check'] == 'Program adı eşlemesi' and r['label'] == 'Ormanlar' and r['status'] == 'FAIL'
               for r in results)
    assert next(r for r in results if r['check'] == 'Müdürlük program çapraz toplamı')['computed'] is None


def test_missing_programme_column_does_not_allow_a_partial_total():
    source = detail()
    parsed = programme_source()
    block = deepcopy(parsed['departments'][0]['blocks'][0])
    block['activity_memberships'][0]['table_number'] = 2
    parsed['departments'][0]['blocks'].append(block)
    parsed['rehearsal_tables']['2'] = dict(book=[['Title', '→'], ['Faaliyetler', '???'], ['Activity', '1,00']])
    results = detail_checks(source, year_groups(source), parsed)
    cross = next(r for r in results if r['check'] == 'Müdürlük program çapraz toplamı')
    assert cross['status'] == 'FAIL' and cross['computed'] is None


def test_all_printed_years_are_checked_and_missing_detail_total_fails():
    source = economic()
    for row in source['rows']:
        row.extend(row[1:])
    source['rows'][0][5] = '2028'
    source['rows'][2][8] = '31,00'
    checks = row_checks(source, year_groups(source))
    assert len(checks) == 6
    assert next(c for c in checks if c['row'] == 3 and c['column'] == 9)['difference'] == 1
    source = detail()
    source['rows'].pop()
    assert any(r['check'] == 'Okuma / kapsam' and 'geneltoplam' in r['label']
               for r in detail_checks(source, year_groups(source), programme_source()))


def test_heading_discovery_missing_tables_and_unreadable_layout_are_explicit():
    source = economic()
    assert table_kind(source) == 'economic'
    assert table_kind(share()) == 'share'
    assert table_kind(detail()) == 'detail'
    source['rows'][1][4] = '???'
    parsed = directorates()
    parsed['institution_tables'] = [source]
    audit = audit_institution_tables(parsed)
    assert len(audit['findings']) == 3
    assert all(f['status'] == 'FAIL' for f in audit['findings'])
    assert {f['name'] for f in audit['findings']} == {
        'Ekonomik kod / program grupları', 'Müdürlük bütçeleri ve toplam bütçeye oranı',
        'Ekonomik kod / program ve faaliyet ayrıntısı'}
    assert audit['findings'][0]['page'] == '731'


FIXTURES = Path(__file__).parent / 'fixtures/first_load'
PRINTED = FIXTURES / 'source/2027-performans-programi_16102026_duzeltilmis 2.idml'


@pytest.fixture(scope='module')
def printed():
    return parse_book(PRINTED)[0]


def test_printed_book_summary_defects_and_separate_directorate_counts(printed):
    assert hashlib.sha256(PRINTED.read_bytes()).hexdigest() == '261cd17fd0be13dead1c573966bb3cc17b63664adc867b2e6fc4e156df28f36e'
    audit = audit_results(printed, [])
    assert audit['findings'] == audit['counts'] == audit['transfers'] == []
    institution = audit['institution']
    assert len(institution['tables']) == 3
    assert not [f for f in institution['findings'] if f['check'] == 'Okuma / kapsam']
    reserve = [f for f in institution['findings'] if f['page'] == '244'
               and f['check'] == 'Satır toplamı' and f['label'] == 'Yedek Ödenekler']
    assert [(f['column'], f['printed'], f['computed'], f['difference']) for f in reserve] == [
        (5, Decimal('600000000'), Decimal('600500000'), Decimal('-500000')),
        (9, Decimal('610000000'), Decimal('1220000000'), Decimal('-610000000')),
        (13, Decimal('0'), Decimal('1488400000'), Decimal('-1488400000')),
    ]
    assert all(f['status'] == 'FAIL' for f in reserve)
    totals = [f for f in institution['findings'] if f['page'] == '244' and f['row'] == 12 and f['status'] == 'FAIL']
    assert any(f['column'] == 5 and f['check'] == 'Satır toplamı' and f['difference'] == Decimal('-499500000') for f in totals)
    assert any(f['column'] == 3 and f['check'] == 'Sütun toplamı' and f['difference'] == Decimal('499000000') for f in totals)
    assert len(institution['reserves']) == 3
    assert institution['reserves'][0]['values'] == ['0,00', '500.000,00', '600.000.000,00', '600.000.000,00']
    report = '\n'.join(institution_report(institution))
    assert '## Kurum özet tabloları' in report and 'Fark' in report
    assert '600.500.000,00' in report and '-1.488.400.000,00' in report
    assert all(f['status'] == 'PASS' for f in institution['findings'] if f['page'] == '246')


def test_owner_confirmed_name_map_preserves_values_and_checksums():
    mapping = json.loads((FIXTURES / 'name_map.json').read_text())
    assert mapping['pending_ali'] == []
    assert '19 Ekim 2026' in mapping['note'] and 'D-94' in mapping['note']
    assert mapping['map']['Harita ve Planlama Müdürlüğü'] == 'Plan Proje Müdürlüğü'
    for line in (FIXTURES / 'SHA256SUMS').read_text().splitlines():
        if line.startswith('#'):
            continue
        digest, name = line.split('  ', 1)
        path = FIXTURES.parents[2] / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
