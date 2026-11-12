"""CIV-220: the EK-1 listing builds report data for every directorate.

The pinned 2026 book must be verified, parsed and errata-projected once per
request, not once per directorate (33 s on the 33-directorate rehearsal).
"""
from decimal import Decimal
import json

import pytest

from app.data import pp_errata
from app import activity_sections_service as sections
from app import ar_unit_tables_service as tables
from test_approved_book_publication import approved_books, walk, period, publish  # noqa: F401
from test_pp_errata import create_fr

pytestmark = pytest.mark.postgres


def test_book_projection_reused_across_directorates(walk, monkeypatch):
    db, _, strategy, _, _, _ = walk
    docs = create_fr(walk)
    units = [d for d in docs if d.department_id]
    assert len(units) > 3
    calls = {'errata': 0, 'loads': 0}
    real_errata, real_loads = pp_errata.apply_pp_errata, tables.json.loads

    def errata(payload):
        calls['errata'] += 1
        return real_errata(payload)

    def loads(text, *args, **kwargs):
        if len(text) > 100000:
            calls['loads'] += 1
        return real_loads(text, *args, **kwargs)

    monkeypatch.setattr(pp_errata, 'apply_pp_errata', errata)
    monkeypatch.setattr(tables.json, 'loads', loads)
    data = [sections.report_data(db, strategy, d.id) for d in units]
    assert calls['errata'] == 1
    # One parse for the financial errata view, one for the unit-table book.
    assert calls['loads'] == 2
    # Each directorate still gets only its own planned figures and activities.
    for doc, item in zip(units, data):
        assert {r['department_id'] for r in item['financial']['pp_planned_figures']} <= {doc.department_id}
    # A caller changing its copy must not leak into another directorate's view.
    first = data[0]['financial']['pp_planned_figures']
    if first:
        first[0]['amount'] = Decimal('-1')
    again = sections.report_data(db, strategy, units[0].id)['financial']['pp_planned_figures']
    assert all(r['amount'] != Decimal('-1') for r in again)
    assert json.dumps(again, default=str) == json.dumps(
        sections.report_data(db, strategy, units[0].id)['financial']['pp_planned_figures'], default=str)

