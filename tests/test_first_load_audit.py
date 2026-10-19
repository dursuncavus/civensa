from copy import deepcopy

import pytest
from sqlalchemy import select

from app.models import Activity
from app.program_service import department_snapshot
from scripts.first_load_audit import audit_results
from scripts.first_load_dryrun import parse_book
from test_book_first_load import book, import_book
from test_word_import import import_context

pytestmark = pytest.mark.postgres


@pytest.fixture
def traced(db, import_context, book):
    _, _, word = book
    parsed, _ = parse_book(word)
    # The synthetic book fixture's original grid is equal to its Word grid.
    for table in parsed['rehearsal_tables'].values():
        table['book'] = deepcopy(table['word'])
    import_book(db, import_context, parsed)
    department_id = db.scalar(select(Activity.department_id))
    stored = department_snapshot(db, import_context.period.id, department_id)
    result = dict(name=parsed['departments'][0]['name'], stored=stored,
                  errors=['0001.Park yapımı: 2029 Tahmin finansman bilgisi eksik.'])
    return parsed, result


def test_source_blank_has_book_word_and_stored_proof(traced):
    parsed, result = traced
    audit = audit_results(parsed, [result])
    assert not audit['transfers']
    finding = audit['findings'][0]
    assert (finding['side'], finding['group']) == ('SOURCE', 'finance_missing')
    assert all(cell['book'] == cell['word'] == '' for cell in finding['cells'])
    assert all(value['amount'] is None for value in finding['stored'])


def test_changed_generated_cell_is_system_not_source(traced):
    parsed, result = traced
    # Change 2027 even though the validation message concerns 2029: the complete
    # transfer audit must catch corruption outside the displayed error cells.
    parsed['rehearsal_tables']['5']['word'][1][1] = '123,00'
    audit = audit_results(parsed, [result])
    finding = audit['findings'][0]
    assert finding['side'] == 'SYSTEM'
    assert audit['transfers'] and 'kitap–Word aktarımı' in finding['details']


def test_wrong_stored_value_and_unknown_rule_are_never_called_source(traced):
    parsed, result = traced
    result['stored']['activities'][0]['costs'][0]['amount'] = '999'
    audit = audit_results(parsed, [result])
    assert audit['transfers']
    assert audit['findings'][0]['side'] == 'SYSTEM'
    result['errors'] = ['Yeni ve sınıflandırılmamış bir doğrulama hatası.']
    finding = audit_results(parsed, [result])['findings'][0]
    assert finding['side'] == 'SYSTEM' and finding['group'] == 'unknown'
