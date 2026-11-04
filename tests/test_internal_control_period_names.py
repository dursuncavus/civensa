"""CIV-167: period-bound unit names, using synthetic data on local PostgreSQL."""
from datetime import date
from io import BytesIO

from docx import Document
from openpyxl import load_workbook
import pytest
from sqlalchemy import select
from starlette.datastructures import FormData

from app import internal_control_service as ic
from app import internal_control_monitoring_service as m
from app import internal_control_monitoring_export as export
from app import structure_service as structure
from app.internal_control_monitoring_models import ICMonitoringBatch as Batch
from app.models import Department, DepartmentScope, ReportingPeriod, User
from test_internal_control import action_row, workbook
from test_internal_control_monitoring import approve, monitoring

pytestmark = pytest.mark.postgres
OLD = 'Afet İşleri Müdürlüğü'
NEW = 'Afet İşleri ve Risk Yönetimi Müdürlüğü'
COOP_OLD = 'Destek Hizmetleri Müdürlüğü'
COOP_NEW = 'İdari Destek Müdürlüğü'


@pytest.fixture
def naming_plan(db, sample):
    sample['department'].name = OLD
    other = Department(organization_id=sample['department'].organization_id, name=COOP_OLD)
    db.add(other)
    db.flush()
    collaborator = User(email='coop@civ167.invalid', full_name='Katkı Personeli',
        role='department', department_id=other.id, password_hash='unused', can_submit=True)
    staff = User(email='staff@civ167.invalid', full_name='Strateji Personeli',
        role='strategy', department_id=sample['department'].id, password_hash='unused')
    db.add_all([collaborator, staff])
    db.commit()
    source = workbook([
        action_row(**{'7': OLD, '8': COOP_OLD, '10': '2026'}),
        action_row(**{'2': 'KOS1.2', '5': 'KOS1.2.1', '7': 'İç Kontrol Kurulu', '10': '2026'}),
    ], metadata=['Sentetik dönem adları planı', 2026, 2029, 'v1', '18.10.2026'])
    batch, _ = ic.create_import(db, sample['strategy'], source, 'civ167-sentetik.xlsx')
    ic.map_unit(db, sample['strategy'], batch, 'İç Kontrol Kurulu', body_name='İç Kontrol Kurulu')
    plan = ic.commit_import(db, sample['strategy'], batch.id)
    db.commit()
    ic.activate_plan(db, sample['strategy'], plan.id)
    db.commit()
    return {**sample, 'plan': plan, 'other': other, 'collaborator': collaborator, 'staff': staff}


def rename(db, data, department, name, effective='2027-01-01'):
    structure.save_change(db, data['strategy'], FormData([
        ('organization_id', department.organization_id), ('period_id', data['period'].id),
        ('change_type', 'RENAMED'), ('effective_date', effective),
        ('council_decision_no', '2026/167'), ('council_decision_date', '2026-12-01'),
        ('from_department_ids', department.id), ('new_name', name),
    ]))
    db.commit()


def assert_official_names(db, data, period, responsible, cooperating, *, draft=False):
    for fmt in ('docx', 'xlsx'):
        content = export.official_export(db, data['strategy'], period.id, fmt, draft=draft)
        if fmt == 'xlsx':
            rows = list(load_workbook(BytesIO(content))['Resmî İzleme'].values)[1:]
        else:
            rows = [[cell.text for cell in row.cells]
                    for row in Document(BytesIO(content)).tables[1].rows[1:]]
        assert [(row[5], row[6]) for row in rows] == [
            (responsible, cooperating), ('İç Kontrol Kurulu', None if fmt == 'xlsx' else '')]


@pytest.mark.parametrize('year,half,opened_before_change', [
    (2026, 2, False), (2027, 1, False), (2026, 2, True),
])
def test_period_open_official_exports_and_monitoring_names(
        db, naming_plan, client, monkeypatch, year, half, opened_before_change):
    from app.main import app, require_user
    d = naming_plan
    if not opened_before_change:
        rename(db, d, d['department'], NEW)
        rename(db, d, d['other'], COOP_NEW)
    monkeypatch.setattr(m, 'today', lambda db: date(2026, 12, 15) if opened_before_change else date(2027, 1, 15))
    period = m.open_period(db, d['strategy'], d['plan'].id, year, half, date(2027, 12, 31))
    db.commit()
    batches = db.scalars(select(Batch).where(Batch.period_id == period.id).order_by(Batch.id)).all()
    frozen = {batch.id: batch.label for batch in batches}
    if opened_before_change:
        assert_official_names(db, d, period, OLD, COOP_OLD, draft=True)
        rename(db, d, d['department'], NEW)
        rename(db, d, d['other'], COOP_NEW)
        monkeypatch.setattr(m, 'today', lambda db: date(2027, 1, 15))
    expected, coop_expected = (OLD, COOP_OLD) if year == 2026 else (NEW, COOP_NEW)
    assert batches[0].label == expected
    # Cooperating-only departments have no batch: their names use the year helper.
    assert all(batch.department_id != d['other'].id for batch in batches)
    assert_official_names(db, d, period, expected, coop_expected, draft=True)
    for batch in batches:
        approve(db, d, batch)
    assert_official_names(db, d, period, expected, coop_expected)
    app.dependency_overrides[require_user] = lambda: d['strategy']
    response = client.get(f'/internal-control/monitoring?period_id={period.id}')
    assert response.status_code == 200
    assert f'>{expected}</a>' in response.text
    assert f'{coop_expected} · Sorumlu eylem yok' in response.text
    db.expire_all()
    assert {batch.id: batch.label for batch in batches} == frozen
    assert d['department'].name == NEW and d['other'].name == COOP_NEW


def test_all_departments_and_body_names_stay_unchanged(db, monitoring, sample):
    d = monitoring
    before = {row[3]: row[5:7] for row in export.official_data(
        db, d['strategy'], d['period'].id, draft=True)[2]}
    rename(db, {**d, 'period': sample['period']}, d['department'], NEW, effective='2028-01-01')
    after = {row[3]: row[5:7] for row in export.official_data(
        db, d['strategy'], d['period'].id, draft=True)[2]}
    assert after == before
    assert after['KOS1.2.1'][0] == 'Tüm Müdürlükler'
    assert after['KOS1.3.1'][0] == 'İç Kontrol Kurulu'


def test_existing_frozen_labels_win_for_both_party_roles(db, naming_plan, client):
    from app.main import app, require_user
    d = naming_plan
    rename(db, d, d['department'], NEW)
    rename(db, d, d['other'], COOP_NEW)
    # Model an existing period whose labels differ from today's year resolution.
    from app.internal_control_monitoring_models import ICMonitoringPeriod as Period
    period = Period(plan_id=d['plan'].id, year=2026, half=2, deadline=date(2027, 12, 31))
    db.add(period)
    db.flush()
    labels = {d['department'].id: 'Dönemde görülen sorumlu adı',
              d['other'].id: 'Dönemde görülen işbirliği adı'}
    for did, label in labels.items():
        db.add(Batch(period_id=period.id, scope_key=f'd:{did}', department_id=did, label=label))
    db.commit()
    assert structure.name_for_year(db, 2026, d['department']) == OLD
    assert structure.name_for_year(db, 2026, d['other']) == COOP_OLD
    for _ in range(2):
        assert_official_names(db, d, period, labels[d['department'].id], labels[d['other'].id], draft=True)
    app.dependency_overrides[require_user] = lambda: d['strategy']
    response = client.get(f'/internal-control/monitoring?period_id={period.id}')
    assert response.status_code == 200
    assert all(f'>{label}</a>' in response.text for label in labels.values())
    db.expire_all()
    assert {b.department_id: b.label for b in db.scalars(select(Batch).where(Batch.period_id == period.id))} == labels


def test_year_helper_keeps_scope_precedence_chained_and_cancelled_changes(db, naming_plan):
    d = naming_plan
    rename(db, d, d['department'], NEW)
    rename(db, d, d['department'], 'Afet Yönetimi Müdürlüğü', effective='2028-07-01')
    periods = [ReportingPeriod(year=year) for year in (2026, 2028)]
    db.add_all(periods)
    db.flush()
    db.add(DepartmentScope(period_id=periods[0].id, department_id=d['department'].id,
                           display_name='Döneme özel ad', status='required'))
    db.commit()
    assert structure.name_for_year(db, 2026, d['department']) == OLD
    assert structure.name_for_year(db, 2027, d['department']) == NEW
    assert structure.name_for_year(db, 2028, d['department']) == 'Afet Yönetimi Müdürlüğü'
    assert structure.period_name(db, periods[0].id, d['department']) == 'Döneme özel ad'
    assert structure.period_name(db, periods[1].id, d['department']) == 'Afet Yönetimi Müdürlüğü'
    latest = structure.live_changes(db)[-1]
    structure.cancel_change(db, d['strategy'], latest.id, 'Meclis kararı düzeltildi')
    db.commit()
    assert structure.name_for_year(db, 2028, d['department']) == NEW
    assert structure.name_for_year(db, 2026, d['department']) == OLD
    assert structure.name_for_year(db, 2026, d['other']) == COOP_OLD
