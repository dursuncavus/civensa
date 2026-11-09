"""PR #438 lead corrections: real header spellings, synthetic values only."""
import io
import json
from pathlib import Path
from decimal import Decimal
from zipfile import ZipFile
from xml.etree import ElementTree as ET

import pytest
from fastapi import HTTPException
from openpyxl import load_workbook
from sqlalchemy import select, func
from app import actual_import_service as imp
from app.models import ActualRevision
from tests.test_actual_import import db, scenario, workbook, confirmed, apply

pytestmark = pytest.mark.postgres
REAL_HEADERS = json.loads((Path(__file__).parent/'fixtures/civ192_headers.json').read_text())['headers']


def cached_formula(data, coordinate, value):
    """Supply a synthetic Excel cache; never calculate the formula in the test."""
    output = io.BytesIO()
    with ZipFile(io.BytesIO(data)) as source, ZipFile(output, 'w') as target:
        for item in source.infolist():
            payload = source.read(item.filename)
            if item.filename == 'xl/worksheets/sheet1.xml':
                root = ET.fromstring(payload)
                ns = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                cell = root.find(f'.//s:c[@r="{coordinate}"]', ns)
                assert cell.find('s:f', ns) is not None
                cell.find('s:v', ns).text = str(value)
                payload = ET.tostring(root)
            target.writestr(item, payload)
    return output.getvalue()


def stored(db, sample, scenario, data):
    record = imp.preview_import(db, sample['strategy'], scenario['revision_id'], data)
    db.commit()
    return record, json.loads(record.preview_json)


@pytest.mark.parametrize('reverse', [False, True])
def test_exact_lead_header_fixture_and_distinct_q4_total(client, db, sample, scenario, reverse):
    data = workbook([{'name':'Hizmet sayısı', 'q':[1,2,3,4], 'annual':10, 'strategy_ratio':.2}],
        headers=REAL_HEADERS, reverse=reverse)
    record, p = stored(db, sample, scenario, data)
    row = p['rows'][0]
    assert row['quarters'] == [1,2,3,4]
    assert row['raw_value'] == '10'
    assert row['strategy_ratio'] == .2
    assert len(row['readings']) == 1
    assert apply(db, sample, record, p)['counts'] == {'Yazıldı':1}


@pytest.mark.parametrize('cache', [None, 0])
def test_strategy_ratio_formula_with_missing_q4_never_writes(client, db, sample, scenario, cache):
    data = workbook([{'name':'Hizmet sayısı', 'q':[1,2,3,None], 'strategy_ratio':'=R2/M2'}])
    if cache is not None:
        data = cached_formula(data, 'S2', cache)
    before = db.scalar(select(func.count()).select_from(ActualRevision))
    record, p = stored(db, sample, scenario, data)
    row = p['rows'][0]
    assert row['status'] == 'Eksik'
    assert row['formulas']['strategy_ratio']['formula'] == '=R2/M2'
    assert row['formulas']['strategy_ratio']['cached_numeric'] is (cache is not None)
    assert apply(db, sample, record, p)['counts'] == {'Eksik':1}
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == before


@pytest.mark.parametrize('ratio', [0,1,2])
def test_handtyped_strategy_ratio_is_only_context(client, db, sample, scenario, ratio):
    record, p = stored(db, sample, scenario, workbook([
        {'name':'Hizmet sayısı', 'q':[1,2,3,None], 'strategy_ratio':ratio}]))
    assert p['rows'][0]['strategy_ratio'] == ratio
    assert apply(db, sample, record, p)['counts'] == {'Eksik':1}


@pytest.mark.parametrize('reading,expected', [('q4_total',20), ('method',10)])
def test_conflicting_totals_require_explicit_reading(client, db, sample, scenario, reading, expected):
    data = workbook([{'name':'Hizmet sayısı', 'q':[1,2,3,4], 'annual':20, 'strategy_ratio':2}])
    record, p = stored(db, sample, scenario, data)
    row = p['rows'][0]
    assert row['status'] == 'Onay gerekiyor'
    assert {Decimal(r['value']) for r in row['readings']} == {Decimal(10),Decimal(20)}
    response = client.get(f'/activity-reports/imports/{record.id}')
    assert response.status_code == 200
    assert 'Strateji oranı' in response.text and 'TOPLA: Q1 + Q2 + Q3 + Q4' in response.text
    before = db.scalar(select(func.count()).select_from(ActualRevision))
    choice = confirmed(p)
    choice['2'].pop('reading')
    with pytest.raises(HTTPException):
        imp.apply_import(db, sample['strategy'], record.id, p['expected_revision'], choice)
    db.rollback()
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == before
    choice = confirmed(p)
    choice['2']['reading'] = reading
    if reading == 'method':
        response = client.post(f'/activity-reports/imports/{record.id}/apply', data={
            'expected_revision':p['expected_revision'],
            'choice_2':f"{choice['2']['indicator_id']}:raw:method"})
        assert response.status_code == 200
        db.refresh(record)
        result = json.loads(record.result_json)
    else:
        result = apply(db, sample, record, p, choice)
    assert result['counts'] == {'Yazıldı':1}
    assert result['rows'][0]['annual_reading'] == reading
    assert db.scalar(select(ActualRevision).order_by(ActualRevision.id.desc())).value == expected


@pytest.mark.parametrize('cache', [None, 0, 19])
def test_formula_total_needs_numeric_cache(client, db, sample, scenario, cache):
    data = workbook([{'name':'Hizmet sayısı', 'q':[1,2,3,None], 'annual':'=SUM(N2:Q2)'}])
    if cache is not None:
        data = cached_formula(data, 'R2', cache)
    record, p = stored(db, sample, scenario, data)
    assert p['rows'][0]['formulas']['q4_total']['cached_numeric'] is (cache is not None)
    result = apply(db, sample, record, p)
    assert result['counts'] == ({'Eksik':1} if cache is None else {'Yazıldı':1})
    if cache is not None:
        assert db.scalar(select(ActualRevision).order_by(ActualRevision.id.desc())).value == cache


@pytest.mark.parametrize('explanation', [None, '', '   '])
def test_blank_workbook_explanation_keeps_directorate_text(client, db, sample, scenario, explanation):
    previous = db.scalar(select(ActualRevision).order_by(ActualRevision.id))
    original = previous.explanation
    record, p = stored(db, sample, scenario, workbook([
        {'name':'Hizmet sayısı', 'annual':19, 'explanation':explanation}]))
    assert apply(db, sample, record, p)['counts'] == {'Yazıldı':1}
    latest = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id==previous.report_indicator_id)
        .order_by(ActualRevision.revision.desc()))
    assert latest.value == 19 and latest.explanation == original
    assert latest.evidence_json == previous.evidence_json


@pytest.mark.parametrize('version', [None,2])
def test_obsolete_ratio_based_preview_is_rejected(client, db, sample, scenario, version):
    record, p = stored(db, sample, scenario, workbook([{'name':'Hizmet sayısı', 'annual':19}]))
    p.pop('schema_version', None)
    if version is not None:
        p['schema_version'] = version
    record.preview_json = json.dumps(p); db.commit()
    before = db.scalar(select(func.count()).select_from(ActualRevision))
    with pytest.raises(HTTPException) as error:
        imp.apply_import(db, sample['strategy'], record.id, p['expected_revision'], confirmed(p))
    assert error.value.status_code == 409
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == before


def test_absent_explanation_column_keeps_previous_text(client, db, sample, scenario):
    data = workbook([{'name':'Hizmet sayısı', 'annual':19}])
    book = load_workbook(io.BytesIO(data))
    book['veriler'].delete_cols(24)
    output = io.BytesIO(); book.save(output); book.close()
    record, p = stored(db, sample, scenario, output.getvalue())
    assert 'explanation' not in p['rows'][0]['source']
    previous = db.scalar(select(ActualRevision).order_by(ActualRevision.id))
    assert apply(db, sample, record, p)['counts'] == {'Yazıldı':1}
    latest = db.scalar(select(ActualRevision).order_by(ActualRevision.id.desc()))
    assert latest.explanation == previous.explanation


@pytest.mark.parametrize('cache', [None,4])
def test_quarter_formula_needs_numeric_cache(client, db, sample, scenario, cache):
    data = workbook([{'name':'Hizmet sayısı', 'q':[1,2,3,'=2+2']}])
    if cache is not None:
        data = cached_formula(data, 'Q2', cache)
    record, p = stored(db, sample, scenario, data)
    assert p['rows'][0]['formulas']['q4']['cached_numeric'] is (cache is not None)
    assert apply(db, sample, record, p)['counts'] == ({'Eksik':1} if cache is None else {'Yazıldı':1})
    if cache is not None:
        assert db.scalar(select(ActualRevision).order_by(ActualRevision.id.desc())).value == 10


def test_cumulative_conflict_keeps_value_and_scale_choices_together(client, db, sample, scenario):
    record, p = stored(db, sample, scenario, workbook([{'name':'Memnuniyet oranı', 'unit':'Oran',
        'method':'T.KÜMÜLATİF', 'q':[None,None,None,.25], 'annual':.8}]))
    assert p['rows'][0]['status'] == 'Onay gerekiyor'
    choice = confirmed(p)
    choice['2'].update(reading='method', scale='percent')
    assert apply(db, sample, record, p, choice)['counts'] == {'Yazıldı':1}
    assert db.scalar(select(ActualRevision).order_by(ActualRevision.id.desc())).value == 25


def test_uncached_total_formula_can_only_fall_back_to_complete_quarters(client, db, sample, scenario):
    record, p = stored(db, sample, scenario, workbook([
        {'name':'Hizmet sayısı', 'q':[1,2,3,4], 'annual':'=SUM(N2:Q2)'}]))
    assert [r['key'] for r in p['rows'][0]['readings']] == ['method']
    assert apply(db, sample, record, p)['counts'] == {'Yazıldı':1}
    assert db.scalar(select(ActualRevision).order_by(ActualRevision.id.desc())).value == 10
