"""Phase 3 package projections and append-only content/decisions; no rollout switch."""
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, event, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .authorization_models import reject_history_change


class DirectoratePackage(Base):
    __tablename__ = 'directorate_packages'
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    department_id: Mapped[int] = mapped_column(ForeignKey('departments.id'))
    resource_scope: Mapped[str] = mapped_column(String(30))
    period_id: Mapped[int] = mapped_column(ForeignKey('reporting_periods.id'))
    report_revision_id: Mapped[int | None] = mapped_column(ForeignKey('activity_report_revisions.id'), nullable=True)
    source_key: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(30), default='draft')
    version: Mapped[int] = mapped_column(Integer, default=0)
    current_revision: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (
        UniqueConstraint('department_id', 'resource_scope', 'source_key', name='uq_directorate_package_source'),
        CheckConstraint("resource_scope IN ('performance_program','activity_report')", name='ck_package_scope'),
        CheckConstraint("state IN ('draft','returned','director_review','strategy_review','strategy_approved')", name='ck_package_state'),
        CheckConstraint("(resource_scope='performance_program' AND report_revision_id IS NULL) OR (resource_scope='activity_report' AND report_revision_id IS NOT NULL)", name='ck_package_source'),
    )


class PackageRevision(Base):
    __tablename__ = 'package_revisions'
    id: Mapped[int] = mapped_column(primary_key=True)
    package_id: Mapped[int] = mapped_column(ForeignKey('directorate_packages.id'))
    revision: Mapped[int] = mapped_column(Integer)
    previous_revision_id: Mapped[int | None] = mapped_column(ForeignKey('package_revisions.id'), nullable=True)
    content_json: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    reason: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('package_id','revision',name='uq_package_revision'),)


class PackageDecision(Base):
    __tablename__ = 'package_decisions'
    id: Mapped[int] = mapped_column(primary_key=True)
    package_revision_id: Mapped[int] = mapped_column(ForeignKey('package_revisions.id'))
    snapshot_sha256: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(40))
    from_state: Mapped[str] = mapped_column(String(30))
    to_state: Mapped[str] = mapped_column(String(30))
    workflow_event_id: Mapped[int] = mapped_column(ForeignKey('workflow_events.id'), unique=True)
    delegation_id: Mapped[int | None] = mapped_column(ForeignKey('authority_delegations.id'), nullable=True)
    # Actor, reason and DB timestamp belong to the immutable linked WorkflowEvent.
    __table_args__ = (CheckConstraint("action IN ('submit_to_director','director_approve','director_return','director_reopen','strategy_approve','strategy_return')", name='ck_package_decision_action'),)


for model in (PackageRevision, PackageDecision):
    event.listen(model, 'before_update', reject_history_change)
    event.listen(model, 'before_delete', reject_history_change)
