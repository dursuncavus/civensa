"""Integrity guards at existing approval/publication boundaries."""
from sqlalchemy import event, select
from .assurance_models import AssuranceStatement
from .activity_sections_models import ARDocument
from .models import ActivityReport, ActivityReportRevision, ActivityReportApproval
from .report_workflow_models import ReportCandidate, ReportRelease


def require_if_placed(connection, organization_id, period_id):
    from .assurance_service import integrity_error, require_integrity
    # A valid asset cannot block this transition. Avoid introducing a dependency
    # on EKLER tables while replaying pre-CIV-037 migration checkpoints.
    if not integrity_error():
        return
    placed = connection.execute(select(AssuranceStatement.id).join(
        ARDocument, ARDocument.id == AssuranceStatement.document_id).where(
        ARDocument.organization_id == organization_id,
        ARDocument.period_id == period_id).limit(1)).first()
    if placed:
        require_integrity()


def guard_publication(mapper, connection, release):
    candidate = connection.execute(select(ReportCandidate.resource_scope, ReportCandidate.organization_id,
        ReportCandidate.period_id).where(ReportCandidate.id == release.candidate_id)).one()
    if candidate.resource_scope == 'activity_report':
        require_if_placed(connection, candidate.organization_id, candidate.period_id)


def guard_approval(mapper, connection, approval):
    report = connection.execute(select(ActivityReport.organization_id, ActivityReport.period_id).join(
        ActivityReportRevision, ActivityReportRevision.report_id == ActivityReport.id).where(
        ActivityReportRevision.id == approval.report_revision_id)).one()
    require_if_placed(connection, report.organization_id, report.period_id)


def install_guards():
    for model, guard in ((ReportRelease, guard_publication), (ActivityReportApproval, guard_approval)):
        if not event.contains(model, 'before_insert', guard):
            event.listen(model, 'before_insert', guard)
