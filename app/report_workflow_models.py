"""Phase 4 immutable report content and separate audited state projection."""
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, event, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .authorization_models import reject_history_change

class ReportCandidate(Base):
    __tablename__='report_candidates'
    id: Mapped[int]=mapped_column(primary_key=True)
    organization_id: Mapped[int]=mapped_column(ForeignKey('organizations.id'))
    period_id: Mapped[int]=mapped_column(ForeignKey('reporting_periods.id'))
    resource_scope: Mapped[str]=mapped_column(String(30))
    report_key: Mapped[str]=mapped_column(String(100))
    sequence: Mapped[int]=mapped_column(Integer)
    predecessor_candidate_id: Mapped[int|None]=mapped_column(ForeignKey('report_candidates.id'),nullable=True)
    activity_revision_id: Mapped[int|None]=mapped_column(ForeignKey('activity_report_revisions.id'),nullable=True)
    payload_json: Mapped[str]=mapped_column(Text)
    payload_sha256: Mapped[str]=mapped_column(String(64))
    manifest_json: Mapped[str]=mapped_column(Text)
    sha256: Mapped[str]=mapped_column(String(64))
    created_by: Mapped[int]=mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    __table_args__=(UniqueConstraint('organization_id','resource_scope','report_key','sequence',name='uq_candidate_sequence'),CheckConstraint("resource_scope IN ('performance_program','activity_report')",name='ck_candidate_scope'),CheckConstraint("(resource_scope='performance_program' AND activity_revision_id IS NULL) OR (resource_scope='activity_report' AND activity_revision_id IS NOT NULL)",name='ck_candidate_materialization'))

class ReportCandidateState(Base):
    __tablename__='report_candidate_states'
    candidate_id: Mapped[int]=mapped_column(ForeignKey('report_candidates.id'),primary_key=True)
    state: Mapped[str]=mapped_column(String(30),default='assembling')
    version: Mapped[int]=mapped_column(Integer,default=0)
    __table_args__=(CheckConstraint("state IN ('assembling','final_review','returned_to_strategy','final_approved','published')",name='ck_candidate_state'),)

class CandidatePackage(Base):
    __tablename__='candidate_packages'
    id: Mapped[int]=mapped_column(primary_key=True)
    candidate_id: Mapped[int]=mapped_column(ForeignKey('report_candidates.id'))
    package_revision_id: Mapped[int]=mapped_column(ForeignKey('package_revisions.id'))
    strategy_decision_id: Mapped[int]=mapped_column(ForeignKey('package_decisions.id'))
    sha256: Mapped[str]=mapped_column(String(64))
    __table_args__=(UniqueConstraint('candidate_id','package_revision_id',name='uq_candidate_package'),)

class ReportDecision(Base):
    __tablename__='report_decisions'
    id: Mapped[int]=mapped_column(primary_key=True)
    candidate_id: Mapped[int]=mapped_column(ForeignKey('report_candidates.id'))
    action: Mapped[str]=mapped_column(String(30))
    candidate_sha256: Mapped[str]=mapped_column(String(64))
    assignment_id: Mapped[int]=mapped_column(ForeignKey('final_authority_assignments.id'))
    workflow_event_id: Mapped[int]=mapped_column(ForeignKey('workflow_events.id'),unique=True)
    activity_approval_id: Mapped[int|None]=mapped_column(ForeignKey('activity_report_approvals.id'),nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    __table_args__=(CheckConstraint("action IN ('final_approve','final_return')",name='ck_report_decision_action'),)

class ReportRelease(Base):
    __tablename__='report_releases'
    id: Mapped[int]=mapped_column(primary_key=True)
    candidate_id: Mapped[int]=mapped_column(ForeignKey('report_candidates.id'),unique=True)
    final_decision_id: Mapped[int]=mapped_column(ForeignKey('report_decisions.id'))
    organization_id: Mapped[int]=mapped_column(ForeignKey('organizations.id'))
    resource_scope: Mapped[str]=mapped_column(String(30))
    report_key: Mapped[str]=mapped_column(String(100))
    major: Mapped[int]=mapped_column(Integer,default=1)
    minor: Mapped[int]=mapped_column(Integer,default=0)
    publication_id: Mapped[int|None]=mapped_column(ForeignKey('publications.id'),nullable=True,unique=True)
    activity_approval_id: Mapped[int|None]=mapped_column(ForeignKey('activity_report_approvals.id'),nullable=True,unique=True)
    workflow_event_id: Mapped[int]=mapped_column(ForeignKey('workflow_events.id'),unique=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    __table_args__=(UniqueConstraint('organization_id','resource_scope','report_key','major','minor',name='uq_report_release_version'),CheckConstraint("(resource_scope='performance_program' AND publication_id IS NOT NULL AND activity_approval_id IS NULL) OR (resource_scope='activity_report' AND publication_id IS NULL AND activity_approval_id IS NOT NULL)",name='ck_release_one_target'),CheckConstraint('major>=1 AND minor>=0',name='ck_release_version'))

class ReportReleaseSuccession(Base):
    """Append-only release edges; populated only by a future publication slice."""
    __tablename__='report_release_successions'
    id: Mapped[int]=mapped_column(primary_key=True)
    predecessor_release_id: Mapped[int]=mapped_column(ForeignKey('report_releases.id'),unique=True)
    successor_release_id: Mapped[int]=mapped_column(ForeignKey('report_releases.id'),unique=True)
    predecessor_candidate_sha256: Mapped[str]=mapped_column(String(64))
    successor_candidate_sha256: Mapped[str]=mapped_column(String(64))
    workflow_event_id: Mapped[int]=mapped_column(ForeignKey('workflow_events.id'),unique=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    __table_args__=(CheckConstraint('predecessor_release_id<>successor_release_id',name='ck_release_succession_distinct'),)

class ReportArtifact(Base):
    __tablename__='report_artifacts'
    id: Mapped[int]=mapped_column(primary_key=True)
    release_id: Mapped[int]=mapped_column(ForeignKey('report_releases.id'))
    artifact_type: Mapped[str]=mapped_column(String(30))
    object_version: Mapped[str]=mapped_column(String(30))
    serialization_version: Mapped[str]=mapped_column(String(50))
    content_json: Mapped[str]=mapped_column(Text)
    sha256: Mapped[str]=mapped_column(String(64))
    byte_size: Mapped[int]=mapped_column(Integer)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    __table_args__=(UniqueConstraint('release_id','artifact_type','object_version',name='uq_release_artifact'),CheckConstraint('byte_size>=0',name='ck_artifact_size'))

IMMUTABLE_REPORT_MODELS=(ReportCandidate,CandidatePackage,ReportDecision,ReportRelease,ReportReleaseSuccession,ReportArtifact)
for model in IMMUTABLE_REPORT_MODELS+(ReportCandidateState,):
    event.listen(model,'before_update',reject_history_change)
    event.listen(model,'before_delete',reject_history_change)
