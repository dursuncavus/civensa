"""Additional PR review regressions: time, row isolation, query budget and labels."""
import html
import json
import re

import pytest
from sqlalchemy import event, select
from starlette.datastructures import FormData
from app import activity_contract_service as contract, actual_import_service as imp, structure_service
from app.main import app, require_user
from app.models import (Department, DepartmentScope, Indicator, IndicatorValue, Publication, ReportCard)
from tests.test_activity_contract import new_report
from tests.test_actual_import import db, scenario, workbook, preview, apply

pytestmark = pytest.mark.postgres


def merge_form(sample, old, receiver, year):
    return FormData({'organization_id':str(old.organization_id), 'period_id':str(sample['period'].id),
        'change_type':'MERGED', 'effective_date':f'{year}-03-01', 'council_decision_date':f'{year}-01-01',
        'council_decision_no':f'SENTETIK-{year}', 'from_department_ids':str(old.id),
        'to_department_ids':str(receiver.id)})


def test_future_merge_cannot_route_a_2026_actual(client, db, sample, scenario):
    old = Department(organization_id=sample['department'].organization_id, name='Gelecekte Birleşen Test')
    db.add(old); db.flush()
    structure_service.save_change(db, sample['strategy'], merge_form(sample, old, sample['department'], 2027))
    db.commit()
    record, p = preview(db, sample, scenario, [{'name':'Hizmet sayısı', 'department':old.name, 'annual':19}])
    assert p['rows'][0]['status'] == 'Eşleşmedi'
    assert apply(db, sample, record, p)['counts'] == {'Eşleşmedi':1}
    assert sample['department'].id in structure_service.import_department_ids(
        db, old.organization_id, 2027, old.name, imp.normalized)


def test_rejected_row_does_not_poison_next_row_lock(client, db, sample, scenario):
    record, p = preview(db, sample, scenario, [{'name':'Kanıtsız sayı', 'annual':13},
        {'name':'Hizmet sayısı', 'annual':19}])
    result = apply(db, sample, record, p)
    assert [row['status'] for row in result['rows']] == ['Hata','Yazıldı']
    assert 'kaynak bulunmuyor' in result['rows'][0]['message']


def test_structure_directory_select_budget_is_constant(client, db, sample, scenario, monkeypatch):
    departments = [Department(organization_id=sample['department'].organization_id,
        name=f'Sentetik Müdürlük {i}') for i in range(50)]
    db.add_all(departments); db.flush()
    db.add_all([DepartmentScope(period_id=sample['period'].id, department_id=d.id,
        display_name=d.name, status='required') for d in departments])
    db.commit()
    # Isolate import's directory/context queries from the pre-existing report
    # validation API, which is exercised normally in all other scenarios.
    report = contract.report_data(db, sample['strategy'], scenario['revision_id'])
    monkeypatch.setattr(contract, 'report_data', lambda *args:report)
    statements = []
    engine = db.get_bind()
    def count(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith('SELECT'):
            statements.append(statement)
    event.listen(engine, 'before_cursor_execute', count)
    try:
        imp.preview_import(db, sample['strategy'], scenario['revision_id'], workbook([
            {'name':'Hizmet sayısı', 'department':d.name, 'annual':19} for d in departments]))
    finally:
        event.remove(engine, 'before_cursor_execute', count)
    assert len(statements) <= 6, len(statements)


@pytest.mark.parametrize('merged', [False, True])
def test_same_named_options_show_pinned_book_context(client, db, sample, merged):
    sample['period'].year = 2026
    db.scalar(select(IndicatorValue).where(IndicatorValue.indicator_id==sample['indicator'].id)).year = 2026
    sample['indicator'].code = 'PG1'
    sample['card'].source_title = '2026/Kart A'
    receiver = sample['department']
    if merged:
        receiver = Department(organization_id=receiver.organization_id, name='Devralan Test Müdürlüğü')
        db.add(receiver); db.flush()
        db.add(DepartmentScope(period_id=sample['period'].id, department_id=receiver.id, status='required'))
    card = ReportCard(period_id=sample['period'].id, department_id=receiver.id,
        subprogram_id=sample['subprogram'].id, source_title='2026/Kart B', goal='Diğer kitap hedefi')
    db.add(card); db.flush()
    other = Indicator(period_id=sample['period'].id, department_id=receiver.id,
        subprogram_id=sample['subprogram'].id, card_id=card.id, code='PG1', name='Hizmet sayısı', unit='Adet')
    db.add(other); db.flush()
    db.add(IndicatorValue(indicator_id=other.id, year=2026, value_kind='target', value=10)); db.commit()
    from app.program_service import book_snapshot
    raw = contract.canonical(book_snapshot(db, sample['period'].id))
    pub = Publication(period_id=sample['period'].id, version=1, snapshot_json=raw,
        sha256=contract.digest(raw), created_by=sample['strategy'].id)
    db.add(pub); db.flush()
    for indicator in (sample['indicator'], other):
        contract.bind_legacy_indicator(db, sample['strategy'], pub.id, indicator.id, None, 'Sentetik kitap bağlamı')
    db.commit()
    app.dependency_overrides[require_user] = lambda:sample['strategy']
    report = new_report(client, pub, sample)
    if merged:
        structure_service.save_change(db, sample['strategy'], merge_form(sample, sample['department'], receiver, 2026))
    # Labels must come from the pinned publication, not today's mutable PP card.
    sample['card'].source_title = 'Sonradan değişen canlı kart adı'; db.commit()
    record = imp.preview_import(db, sample['strategy'], report['revision_id'], workbook([
        {'name':'Hizmet sayısı', 'department':sample['department'].name, 'annual':19}]))
    db.commit()
    response = client.get(f'/activity-reports/imports/{record.id}')
    assert response.status_code == 200
    labels = [html.unescape(text) for _,text in re.findall(
        r'<option value="(\d+:raw:q4_total)">([^<]*)</option>', response.text)]
    assert len(labels) == len(set(labels)) == 2
    assert all('PG1' in label for label in labels)
    assert any('2026/Kart A' in label for label in labels)
    assert any('2026/Kart B' in label for label in labels)
    assert 'Sonradan değişen canlı kart adı' not in ' '.join(labels)
    assert any(sample['department'].name in label for label in labels)
    assert any(receiver.name in label for label in labels)
