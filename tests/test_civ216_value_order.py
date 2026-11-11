"""CIV-216: value lists have a total order, so book/release digests are stable.

Ordering by year alone left rows of the same year (value kinds, funding types)
in database order. On PostgreSQL an UPDATE moves a row to the end of the heap,
so two reads of the same period could serialise the PP book differently and
the release context digest failed spuriously (409 on the /operations
confirmation form)."""
import pytest
from sqlalchemy import select

from app.models import Activity, ActivityCostValue, Indicator, IndicatorValue
from app.program_service import book_snapshot


def test_value_relationships_break_year_ties_by_id():
    for relationship, table in ((Activity.cost_values, 'activity_cost_values'),
                                (Indicator.values, 'indicator_values')):
        order = relationship.property.order_by
        assert [(c.table.name, c.name) for c in order] == [(table, 'year'), (table, 'id')]


def _values(book):
    for department in book['departments']:
        for activity in department['activities']:
            yield [(v['year'], v['id']) for v in activity['costs']]
        for indicator in department['indicators']:
            yield [(v['year'], v['id']) for v in indicator['values']]


def _check_snapshot_order_after_update(db, sample):
    first = db.scalar(select(ActivityCostValue).where(ActivityCostValue.activity_id == sample['activity'].id)
                      .order_by(ActivityCostValue.id))
    db.add(IndicatorValue(indicator_id=sample['indicator'].id, year=2027, value_kind='actual', value='2'))
    db.commit()
    first.raw_text = 'güncellendi'  # moves the tuple on PostgreSQL
    db.commit()
    db.expire_all()
    book = book_snapshot(db, sample['period'].id)
    lists = list(_values(book))
    assert any(len(set(year for year, _ in values)) < len(values) for values in lists)
    assert all(values == sorted(values) for values in lists)
    db.expire_all()
    assert book_snapshot(db, sample['period'].id) == book


def test_snapshot_values_follow_year_then_id(db, sample):
    _check_snapshot_order_after_update(db, sample)


@pytest.mark.postgres
def test_snapshot_values_follow_year_then_id_on_postgres(db, sample):
    _check_snapshot_order_after_update(db, sample)
