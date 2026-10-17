"""Existing service-only publication boundary rejects corrupt legal assets atomically."""
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from app import activity_sections_service as sections, assurance_service as assurance
from app.models import ReportRelease, ReportCandidateState
from tests.test_report_workflow import foundation_db, people, package, approved, candidate, review, approve, publish
from test_assurance_helpers import variables

pytestmark = pytest.mark.postgres


def test_publication_integrity_guard(foundation_db, people, candidate, tmp_path, monkeypatch):
    db, x, c = foundation_db, people, candidate
    docs = sections.create_year(db, x['strategy'], c.organization_id, c.period_id)
    doc = next(d for d in docs if not d.department_id)
    assurance.save(db, x['strategy'], doc.id, 'EK-1', {'expected_revision': 0, 'variables': variables()})
    db.commit()
    review(db, x, c); approve(db, x, c)
    missing = tmp_path / 'missing.json'
    monkeypatch.setattr(assurance, 'ASSET_PATH', missing)
    if c.resource_scope == 'performance_program':
        assert publish(db, x, c).id
    else:
        with pytest.raises(HTTPException) as caught:
            publish(db, x, c)
        assert caught.value.status_code == 409 and 'assurance_statements_2025.json' in caught.value.detail
        db.rollback()
        assert db.scalar(select(func.count()).select_from(ReportRelease).where(ReportRelease.candidate_id == c.id)) == 0
        assert db.get(ReportCandidateState, c.id).state == 'final_approved'


@pytest.mark.parametrize('package', ['activity_report'], indirect=True)
def test_approval_freeze_integrity_guard(foundation_db, people, candidate, tmp_path, monkeypatch):
    from app.models import ActivityReportApproval
    db, x, c = foundation_db, people, candidate
    docs = sections.create_year(db, x['strategy'], c.organization_id, c.period_id)
    doc = next(d for d in docs if not d.department_id)
    assurance.save(db, x['strategy'], doc.id, 'EK-1', {'expected_revision': 0, 'variables': variables()})
    db.commit(); review(db, x, c)
    monkeypatch.setattr(assurance, 'ASSET_PATH', tmp_path / 'missing.json')
    with pytest.raises(HTTPException) as caught:
        approve(db, x, c)
    assert caught.value.status_code == 409
    db.rollback()
    assert db.scalar(select(ActivityReportApproval).where(ActivityReportApproval.report_revision_id == c.activity_revision_id)) is None
    assert db.get(ReportCandidateState, c.id).state == 'final_review'
