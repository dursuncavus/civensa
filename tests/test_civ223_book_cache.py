"""CIV-223: the pinned book is parsed once per process, not once per request,
and a changed stored snapshot is still refused (digest re-checked per session)."""
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import activity_sections_service as sections
from app import ar_unit_tables_service as tables
from app.data import pp_errata
from test_approved_book_publication import approved_books, walk, period, publish  # noqa: F401
from test_pp_errata import create_fr

pytestmark = pytest.mark.postgres


def test_book_parsed_once_across_requests_and_tamper_refused(walk, monkeypatch):
    db, _, strategy, _, _, _ = walk
    docs = create_fr(walk)
    db.commit()
    unit = next(d for d in docs if d.department_id)
    calls = {'errata': 0, 'loads': 0}
    real_errata, real_loads = pp_errata.apply_pp_errata, tables.json.loads

    def errata(payload):
        calls['errata'] += 1
        return real_errata(payload)

    def loads(raw, *args, **kwargs):
        if len(raw) > 100000:
            calls['loads'] += 1
        return real_loads(raw, *args, **kwargs)

    monkeypatch.setattr(pp_errata, 'apply_pp_errata', errata)
    monkeypatch.setattr(tables.json, 'loads', loads)
    first = sections.report_data(db, strategy, unit.id)
    # A second request = a new DB session: no re-parse, same result.
    with Session(db.bind) as other:
        second = sections.report_data(other, other.merge(strategy), unit.id)
    assert calls == {'errata': 1, 'loads': 2}
    assert first['financial']['pp_planned_figures'] == second['financial']['pp_planned_figures']
    assert first['unit_tables'] == second['unit_tables']

    # Tampering with the stored snapshot (the immutability trigger bypassed)
    # is caught in the next session even though a parsed copy is cached.
    db.execute(text('ALTER TABLE publications DISABLE TRIGGER USER'))
    db.execute(text("UPDATE publications SET snapshot_json = snapshot_json || ' '"))
    db.execute(text('ALTER TABLE publications ENABLE TRIGGER USER'))
    db.commit()
    with Session(db.bind) as other:
        with pytest.raises(Exception) as error:
            sections.report_data(other, other.merge(strategy), unit.id)
    assert getattr(error.value, 'status_code', None) == 409
