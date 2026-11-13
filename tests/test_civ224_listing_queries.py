"""CIV-224: the EK-1 listing reads period-wide rows once per page.

On the hosted database every query is a network round trip (~6 ms). The
33-directorate listing issued ~1500 queries (13-15 s live). Inside the listing
memo the same report data must come back with far fewer queries.
"""
import json

import pytest
from sqlalchemy import event, select

from app import activity_sections_service as sections
from app.listing_memo import listing_memo, memo
from app.models import Department, Organization, ReportingPeriod, User
from app.structure_service import structure_read_context
from test_approved_book_publication import approved_books, walk, period, publish  # noqa: F401
from test_pp_errata import create_fr

pytestmark = pytest.mark.postgres


def _count(db, run):
    statements = []
    engine = db.get_bind()

    def hook(conn, cursor, statement, params, context, executemany):
        statements.append(statement)
    event.listen(engine, 'before_cursor_execute', hook)
    try:
        result = run()
    finally:
        event.remove(engine, 'before_cursor_execute', hook)
    return result, len(statements)


def _all(db, strategy, docs):
    return json.dumps([sections.report_data(db, strategy, d.id) for d in docs], default=str, sort_keys=True)


def _listed(db, strategy, docs):
    with listing_memo(db), structure_read_context(db):
        keep = [db.scalars(select(m)).all() for m in (Department, ReportingPeriod, Organization, User)]
        result = _all(db, strategy, docs)
        assert keep
        return result


def test_listing_memo_same_data_fewer_queries(walk):
    db, _, strategy, _, _, _ = walk
    docs = create_fr(walk)
    assert len([d for d in docs if d.department_id]) > 3
    _all(db, strategy, docs)  # warm the process book cache for a fair count
    db.expunge_all()
    plain, plain_count = _count(db, lambda: _all(db, strategy, docs))
    db.expunge_all()
    listed, listed_count = _count(db, lambda: _listed(db, strategy, docs))
    assert listed == plain
    # Measured: 1514 → 374 for 34 documents. Keep a margin, catch regressions.
    assert listed_count * 3 < plain_count, (listed_count, plain_count)
    assert listed_count <= 16 * len(docs), (listed_count, len(docs))


def test_memo_off_outside_listing_and_stops_on_writes(walk):
    db, _, strategy, _, _, _ = walk
    calls = []

    def load():
        calls.append(1)
        return len(calls)
    assert memo(db, 'k', load) == 1 and memo(db, 'k', load) == 2  # no listing: always loads
    with listing_memo(db):
        assert memo(db, 'k', load) == 3 and memo(db, 'k', load) == 3
        db.get(User, strategy.id).full_name = 'Değişti'
        assert memo(db, 'k', load) == 4  # pending write: never serve cached rows
    db.rollback()
