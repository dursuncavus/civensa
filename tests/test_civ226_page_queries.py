"""CIV-226: pages that list every directorate read shared rows once.

On the hosted database every query is a network round trip (~6-10 ms). Live
on 15 Nov: Genel Bakış 6-7 s (~460 queries), Rapor Oluşturucu 6-11 s (~1900),
Faaliyet Raporu 2-3.5 s (~410), Kurum Yapısı ~2 s (~350), Kullanıcılar 1-2 s.
"""
import pytest
from sqlalchemy import event, select

from app.main import department_progress_overview
from app.models import Department
from app.program_service import period_departments, validate_department, validate_departments
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


def test_bulk_validation_and_single_row_match_per_department(walk):
    db, _, _, user, _, _ = walk
    p = period(db)
    ids = [d.id for d in period_departments(db, p.id)]
    assert len(ids) > 30
    bulk = validate_departments(db, p.id, ids)
    assert bulk == {did: validate_department(db, p.id, did) for did in ids}
    assert any(errors for errors, _ in bulk.values())
    full = department_progress_overview(db, p)
    row = next(r for r in full['rows'] if r['department_id'] == user.department_id)
    assert department_progress_overview(db, p, user.department_id)['rows'] == [row]


@pytest.mark.parametrize('path,budget', [
    ('/dashboard', 60), ('/api/progress', 50), ('/activity-report', 30), ('/users', 30),
    ('/structure', 50), ('/report-builder', 600)])
def test_strategy_pages_query_budget(walk, path, budget):
    db, client, _, _, _, _ = walk
    create_fr(walk)
    db.flush()
    assert client.get(path).status_code == 200
    response, count = _count(db, lambda: client.get(path))
    assert response.status_code == 200
    # Before CIV-226 on this fixture: 458 / 444 / 409 / 214 / 353 / 1927.
    assert count <= budget, (path, count)


def test_department_dashboard_query_budget(walk):
    db, client, _, user, login, _ = walk
    create_fr(walk)
    db.flush()
    login(user)
    assert client.get('/dashboard').status_code == 200
    response, count = _count(db, lambda: client.get('/dashboard'))
    assert response.status_code == 200
    assert count <= 60, count  # was 463
