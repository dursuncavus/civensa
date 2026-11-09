"""CIV-198: byte-for-byte legacy snapshots and call-scoped structure reads."""
import json
from decimal import Decimal

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session
from starlette.datastructures import FormData

from app import program_service as program, structure_service as structure
from app.models import (Activity, ActivityCatalogueLink, ActivityCostValue,
    ActivityResponsibility, Department, DepartmentScope, Indicator, IndicatorValue, OfficialActivity, ReportCard,
    ReportingPeriod, StructureChangeCancellation)
from tests.reference import civ198_snapshots as before

pytestmark = pytest.mark.parametrize('backend', [
    'sqlite', pytest.param('postgres', marks=pytest.mark.postgres),
])


@pytest.fixture
def shaped_periods(db, sample):
    """The first-load shape, reduced to two cards plus excluded/history cases."""
    period, department = sample['period'], sample['department']
    history = ReportingPeriod(year=2026)
    excluded = Department(organization_id=department.organization_id, name='Kapsam Dışı Birim')
    db.add_all([history, excluded])
    db.flush()
    db.add(DepartmentScope(period_id=period.id, department_id=excluded.id,
        status='excluded', reason='Sentetik kapsam istisnası', position=-1))
    # Reverse card positions and use two indicators/activities so collection
    # order, null versus zero, and historical years are all observable.
    card = ReportCard(period_id=period.id, department_id=department.id,
        subprogram_id=sample['subprogram'].id, position=-1, source_title='İkinci kart')
    db.add(card)
    db.flush()
    indicator = Indicator(period_id=period.id, department_id=department.id,
        subprogram_id=sample['subprogram'].id, card_id=card.id, name='İkinci gösterge', unit='Adet')
    activity = Activity(period_id=period.id, department_id=department.id,
        subprogram_id=sample['subprogram'].id, card_id=card.id, name='İkinci faaliyet')
    db.add_all([indicator, activity])
    db.flush()
    db.add_all([
        IndicatorValue(indicator_id=indicator.id, year=2028, value_kind='forecast', value=None,
            raw_text='—', state='not_applicable'),
        IndicatorValue(indicator_id=indicator.id, year=2026, value_kind='actual', value=Decimal('0')),
        IndicatorValue(indicator_id=indicator.id, year=2027, value_kind='target', value=Decimal('2.50')),
        IndicatorValue(indicator_id=indicator.id, year=2027, value_kind='actual', value=Decimal('0')),
        ActivityCostValue(activity_id=activity.id, year=2026, value_kind='budget', funding_type='total',
            amount=None, raw_text='—', state='not_applicable'),
        ActivityCatalogueLink(activity_id=activity.id, official_activity_id=sample['official'].id),
    ])
    for funding, amount in [('total', '0'), ('outside', '0'), ('inside', '0')]:
        db.add(ActivityCostValue(activity_id=activity.id, year=2027, value_kind='budget',
            funding_type=funding, amount=Decimal(amount), source_amount=Decimal(amount)))
    second_official = OfficialActivity(period_id=period.id, program_code='2', program_name='İkinci program',
        subprogram_code='2.1', subprogram_name='İkinci alt program', code='2.1.1', name='İkinci katalog kaydı')
    db.add(second_official)
    db.flush()
    # Multiple memberships in non-ID insertion order expose accidental sorting.
    db.add_all([
        ActivityResponsibility(official_activity_id=second_official.id, department_id=excluded.id),
        ActivityResponsibility(official_activity_id=second_official.id, department_id=department.id),
        ActivityCatalogueLink(activity_id=activity.id, official_activity_id=second_official.id),
        ActivityCatalogueLink(activity_id=sample['activity'].id, official_activity_id=second_official.id),
    ])
    db.commit()
    change = structure.save_change(db, sample['strategy'], FormData(dict(
        organization_id=department.organization_id, period_id=period.id,
        change_type='RENAMED', effective_date='2028-01-01', council_decision_no='SENTETİK-198',
        council_decision_date='2027-12-15', from_department_ids=str(department.id),
        new_name='Yeni Sentetik Müdürlük')))
    db.commit()
    return [history.id, period.id], change.id


@pytest.mark.parametrize('historical', [False, True])
def test_snapshots_are_byte_identical_to_parent_readers(db, sample, shaped_periods, historical, backend):
    period_ids, _ = shaped_periods
    # Independent fresh identity maps exercise the real lazy/eager SQL ordering.
    for pid in period_ids:
        with Session(db.get_bind()) as old_db, Session(db.get_bind()) as new_db:
            ids = [d.id for d in before.period_departments(old_db, pid)]
            old_book = before.book_snapshot(old_db, pid)
            new_book = program.book_snapshot(new_db, pid)
            assert json.dumps(new_book, sort_keys=False) == json.dumps(old_book, sort_keys=False)
            for did in ids:
                assert json.dumps(program.department_snapshot(new_db, pid, did), sort_keys=False) == json.dumps(
                    before.department_snapshot(old_db, pid, did), sort_keys=False)
                assert json.dumps(program.department_package_snapshot(new_db, pid, did), sort_keys=False) == json.dumps(
                    before.department_package_snapshot(old_db, pid, did), sort_keys=False)
            assert json.dumps(program.cost_reconciliation(new_db, pid, include_historical=historical), sort_keys=False) == json.dumps(
                before.cost_reconciliation(old_db, pid, include_historical=historical), sort_keys=False)
            assert 'structure_read_context' not in new_db.info


def test_structure_write_is_visible_within_the_same_read_scope(db, sample, backend):
    department = sample['department']
    period = sample['period']
    with structure.structure_read_context(db):
        assert structure.period_name(db, period.id, department) == 'Test Müdürlüğü'
        change = structure.save_change(db, sample['strategy'], FormData(dict(
            organization_id=department.organization_id, period_id=period.id,
            change_type='RENAMED', effective_date='2027-01-01', council_decision_no='SENTETİK-198',
            council_decision_date='2026-12-15', from_department_ids=str(department.id),
            new_name='Aynı Çağrıda Yeni Müdürlük')))
        assert structure.period_name(db, period.id, department) == 'Aynı Çağrıda Yeni Müdürlük'
        assert structure.name_for_year(db, 2026, department) == 'Test Müdürlüğü'
        assert structure.live_changes(db) == [change]
        db.add(StructureChangeCancellation(change_id=change.id, note='Sentetik iptal gerekçesi',
            created_by=sample['strategy'].id))
        # The next read flushes the pending cancellation and invalidates both
        # the live-change list and decoded before-state in this same call.
        assert structure.live_changes(db) == []
        assert structure.name_for_year(db, 2026, department) == department.name
    assert 'structure_read_context' not in db.info


def test_name_cache_is_discarded_on_error_and_after_each_call(db, sample, backend):
    with pytest.raises(RuntimeError):
        with structure.structure_read_context(db):
            structure.period_name(db, sample['period'].id, sample['department'])
            raise RuntimeError('synthetic read failure')
    assert 'structure_read_context' not in db.info
    with structure.structure_read_context(db):
        structure.period_name(db, sample['period'].id, sample['department'])
    assert 'structure_read_context' not in db.info


def test_period_snapshot_reads_do_not_scale_per_indicator_or_activity(db, sample, backend):
    statements = []
    def count(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    # Compare a period snapshot with one card to the same period with 20 extra
    # rows. This guards actual DB round trips rather than a helper call count.
    def reads():
        with Session(db.get_bind()) as session:
            event.listen(session.bind, 'before_cursor_execute', count)
            try:
                program.book_snapshot(session, sample['period'].id)
            finally:
                event.remove(session.bind, 'before_cursor_execute', count)
        result = len(statements)
        statements.clear()
        return result
    baseline = reads()
    for number in range(20):
        db.add(Indicator(period_id=sample['period'].id, department_id=sample['department'].id,
            subprogram_id=sample['subprogram'].id, card_id=sample['card'].id,
            name=f'Sentetik gösterge {number}', unit='Adet'))
        db.add(Activity(period_id=sample['period'].id, department_id=sample['department'].id,
            subprogram_id=sample['subprogram'].id, card_id=sample['card'].id,
            name=f'Sentetik faaliyet {number}'))
    db.commit()
    assert reads() <= baseline + 2


def test_name_reads_respect_no_autoflush(db, sample, backend):
    pending = Department(organization_id=sample['department'].organization_id, name='Bekleyen Birim')
    db.add(pending)
    with db.no_autoflush:
        assert structure.period_name(db, sample['period'].id, sample['department']) == 'Test Müdürlüğü'
        assert pending.id is None
        with structure.structure_read_context(db):
            assert structure.period_name(db, sample['period'].id, sample['department']) == 'Test Müdürlüğü'
            assert pending.id is None
    assert 'structure_read_context' not in db.info
