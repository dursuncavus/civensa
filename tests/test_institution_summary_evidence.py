"""Lead review regressions: arithmetic evidence is distinct from scope evidence."""
from copy import deepcopy
from decimal import Decimal
from collections import Counter

import pytest

from scripts.first_load_dryrun import institution_report
from scripts.institution_summary import (
    audit_institution_tables, detail_checks, economic_checks, row_checks, year_groups,
)
from test_institution_summary import detail, directorates, economic, printed, programme_source


def single_activity_source():
    parsed = programme_source()
    parsed['departments'][0]['blocks'][0]['activity_memberships'].pop()
    parsed['rehearsal_tables']['1']['book'].pop()
    return parsed


def test_equal_programme_sum_cannot_pass_with_different_activity_coverage():
    source = detail()
    parsed = single_activity_source()  # One source activity; the summary contains two.
    result = next(f for f in detail_checks(source, year_groups(source), parsed)
                  if f['check'] == 'Müdürlük program çapraz toplamı')
    assert result['computed'] == Decimal(3)
    assert result['status'] == 'FAIL'
    assert result['classification'] == 'CHECK'
    assert result['coverage']['summary_only']


def test_repeated_reference_to_same_membership_cell_is_counted_once():
    source = detail()
    source['rows'][4][1] = source['rows'][4][3] = '3,00'
    source['rows'][5][1] = source['rows'][5][3] = '0,00'
    source['rows'].pop(5)  # One activity in both scopes.
    parsed = single_activity_source()
    parsed['departments'][0]['blocks'].append(deepcopy(parsed['departments'][0]['blocks'][0]))
    result = next(f for f in detail_checks(source, year_groups(source), parsed)
                  if f['check'] == 'Müdürlük program çapraz toplamı')
    assert result['computed'] == Decimal(3)
    assert result['status'] == 'PASS'
    assert len(result['contributors']) == 1


def test_same_cell_referenced_by_different_programmes_requires_allocation():
    source = detail()
    source['rows'].pop(5)
    source['rows'][4][1] = source['rows'][4][3] = '3,00'
    parsed = single_activity_source()
    other = deepcopy(parsed['departments'][0]['blocks'][0])
    other['program'] = 'Ormanlar'
    parsed['departments'][0]['blocks'].append(other)
    result = next(f for f in detail_checks(source, year_groups(source), parsed)
                  if f['check'] == 'Müdürlük program çapraz toplamı')
    assert result['computed'] == Decimal(3)
    assert result['classification'] == 'CHECK' and result['status'] == 'FAIL'


def test_in_table_arithmetic_has_cell_evidence_and_missing_numbers_are_unknown():
    source = economic()
    source['rows'][2][4] = '29,00'
    result = row_checks(source, year_groups(source))[0]
    assert result['classification'] == 'BOOK'
    assert [(r['row'], r['column'], r['amount']) for r in result['contributors']] == [
        (3, 2, Decimal(10)), (3, 3, Decimal(20)), (3, 4, Decimal(0))]
    source['rows'][2][2] = ''
    result = row_checks(source, year_groups(source))[0]
    assert result['classification'] == 'UNKNOWN' and result['computed'] is None


def test_two_printed_economic_sources_disagree_without_attributing_book_error():
    source = economic()
    parsed = directorates('29.99')
    result = next(f for f in economic_checks(source, year_groups(source), parsed)
                  if f['check'] == 'Müdürlük ekonomik çapraz toplamı')
    assert result['classification'] == 'UNKNOWN'
    assert result['computed'] == Decimal('29.99')
    assert [(r['table'], r['row'], r['column']) for r in result['contributors']] == [('economic1', 2, 2)]
    # The check must not silently substitute raw text for a conflicting parsed amount.
    parsed['rehearsal_tables']['1']['book'][1][1] = '31,00'
    result = next(f for f in economic_checks(source, year_groups(source), parsed)
                  if f['check'] == 'Müdürlük ekonomik çapraz toplamı')
    assert result['classification'] == 'CHECK' and result['computed'] is None


def test_economic_cell_is_not_multiplied_by_repeated_table_reference():
    source = economic()
    parsed = directorates()
    parsed['departments'][0]['economic_tables'].append(deepcopy(parsed['departments'][0]['economic_tables'][0]))
    result = next(f for f in economic_checks(source, year_groups(source), parsed)
                  if f['check'] == 'Müdürlük ekonomik çapraz toplamı')
    assert result['status'] == 'PASS' and result['computed'] == Decimal(30)
    assert len(result['contributors']) == 1


def test_subtotal_stops_at_its_printed_boundary_and_excludes_annex_programme():
    source = detail()
    source['rows'].append(['(2) Separate annex', '99,00', '0,00', '99,00'])
    result = next(f for f in detail_checks(source, year_groups(source), programme_source())
                  if f['check'] == 'Sütun toplamı' and f['row'] == 7 and f['column'] == 2)
    assert result['computed'] == Decimal(3) and result['status'] == 'PASS'
    assert [r['row'] for r in result['contributors']] == [3]


def test_ambiguous_hierarchy_is_a_check_limit_not_a_book_accusation():
    source = detail()
    source['rows'][3][0] = '(1.1.1) Orphan'
    results = detail_checks(source, year_groups(source), programme_source())
    assert all(f['classification'] == 'CHECK' for f in results if f['check'] == 'Sütun toplamı')


def test_unknown_economic_row_cannot_certify_total_coverage():
    source = economic()
    source['rows'][2][0] = 'Unidentified numeric row'
    results = economic_checks(source, year_groups(source), directorates())
    assert all(f['classification'] == 'CHECK' and f['status'] == 'FAIL'
               for f in results if f['check'] == 'Sütun toplamı')


def test_every_printed_failure_has_a_class_and_all_nine_requested_breakdowns(printed):
    audit = audit_institution_tables(printed)
    failed = [f for f in audit['findings'] if f['status'] == 'FAIL']
    counts = Counter(f['classification'] for f in failed)
    assert counts == audit['classes'] == {'BOOK': 53, 'CHECK': 104, 'UNKNOWN': 27}
    assert len(failed) == sum(counts.values())
    expected = {('u444di4775', 3, c): 'CHECK' for c in (4, 7, 10)}
    expected.update({('u40c3i5faa', 5, c): 'UNKNOWN' for c in (9, 13)})
    expected[('u40c3i5faa', 8, 9)] = 'UNKNOWN'
    expected.update({('u444di4775', 193, c): 'BOOK' for c in (2, 5, 8)})
    assert {(f['table'], f['row'], f['column']): f['classification'] for f in audit['evidence']} == expected
    for f in audit['evidence']:
        refs = f['contributors']
        assert len({(r['table'], r['row'], r['column']) for r in refs}) == len(refs)
        assert sum((r['amount'] for r in refs), Decimal(0)) == f['computed']
        assert all(isinstance(r['row'], int) and isinstance(r['column'], int) and r['page'] != '?' for r in refs)
        if f['check'] == 'Sütun toplamı':
            assert [r['row'] for r in refs] == [3, 30, 35, 95, 99, 107, 114, 117, 123, 135, 146, 153, 173, 184, 188]
        elif f['check'] == 'Müdürlük program çapraz toplamı':
            assert [r['row'] for r in f['printed_components']] == [4, 14, 27]
            assert len(refs) == 77 and len(f['printed_leaves']) == 23
        else:
            assert len(refs) == (13 if f['row'] == 8 else 34)
            assert all(r['cards'] for r in refs)
    report = '\n'.join(institution_report(audit))
    assert '| Durum | Sınıf |' in report
    assert 'BOOK 53 / CHECK 104 / UNKNOWN 27' in report
    assert report.count('#### Kanıt ') == 9
    assert len([line for line in report.splitlines() if line.startswith('| FAIL |')]) == len(failed)
    assert all(line.startswith(('| FAIL | BOOK |', '| FAIL | CHECK |', '| FAIL | UNKNOWN |'))
               for line in report.splitlines() if line.startswith('| FAIL |'))


def test_unclassified_fail_cannot_be_rendered():
    with pytest.raises((KeyError, ValueError)):
        institution_report(dict(findings=[dict(status='FAIL')], tables=[]))
