"""Phase 5A append-only correction requests/grants; rollout remains disabled."""
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, event, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .authorization_models import reject_history_change

class RevisionRequest(Base):
    __tablename__='revision_requests'
    id: Mapped[int]=mapped_column(primary_key=True)
    source_release_id: Mapped[int]=mapped_column(ForeignKey('report_releases.id'))
    organization_id: Mapped[int]=mapped_column(ForeignKey('organizations.id'))
    department_id: Mapped[int]=mapped_column(ForeignKey('departments.id'))
    requester_user_id: Mapped[int]=mapped_column(ForeignKey('users.id'))
    requester_membership_id: Mapped[int]=mapped_column(ForeignKey('directorate_memberships.id'))
    source_package_revision_id: Mapped[int]=mapped_column(ForeignKey('package_revisions.id'))
    patches_json: Mapped[str]=mapped_column(Text)
    reason: Mapped[str]=mapped_column(Text)
    evidence_json: Mapped[str]=mapped_column(Text,default='[]')
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    __table_args__=(CheckConstraint('length(trim(reason))>0',name='ck_revision_request_reason'),)

class RevisionRequestState(Base):
    __tablename__='revision_request_states'
    request_id: Mapped[int]=mapped_column(ForeignKey('revision_requests.id'),primary_key=True)
    state: Mapped[str]=mapped_column(String(20),default='requested')
    version: Mapped[int]=mapped_column(default=0)
    __table_args__=(CheckConstraint("state IN ('requested','accepted','rejected','cancelled','editing','stale','applied','closed_no_change')",name='ck_revision_request_state'),)

class RevisionRequestEvent(Base):
    __tablename__='revision_request_events'
    id: Mapped[int]=mapped_column(primary_key=True)
    request_id: Mapped[int]=mapped_column(ForeignKey('revision_requests.id'))
    workflow_event_id: Mapped[int]=mapped_column(ForeignKey('workflow_events.id'),unique=True)
    from_state: Mapped[str]=mapped_column(String(20))
    to_state: Mapped[str]=mapped_column(String(20))
    version: Mapped[int]=mapped_column()
    __table_args__=(UniqueConstraint('request_id','version',name='uq_revision_request_event_version'),)

class RevisionCorrectionCycle(Base):
    __tablename__='revision_correction_cycles'
    id: Mapped[int]=mapped_column(primary_key=True)
    source_release_id: Mapped[int]=mapped_column(ForeignKey('report_releases.id'))
    package_id: Mapped[int]=mapped_column(ForeignKey('directorate_packages.id'))
    source_package_revision_id: Mapped[int]=mapped_column(ForeignKey('package_revisions.id'))
    opening_revision_id: Mapped[int]=mapped_column(ForeignKey('package_revisions.id'))
    workflow_event_id: Mapped[int]=mapped_column(ForeignKey('workflow_events.id'),unique=True)
    __table_args__=(UniqueConstraint('source_release_id','package_id',name='uq_revision_cycle'),)

class RevisionEditGrant(Base):
    __tablename__='revision_edit_grants'
    id: Mapped[int]=mapped_column(primary_key=True)
    request_id: Mapped[int]=mapped_column(ForeignKey('revision_requests.id'),unique=True)
    source_release_id: Mapped[int]=mapped_column(ForeignKey('report_releases.id'))
    department_id: Mapped[int]=mapped_column(ForeignKey('departments.id'))
    cycle_id: Mapped[int]=mapped_column(ForeignKey('revision_correction_cycles.id'))
    membership_ids_json: Mapped[str]=mapped_column(Text)
    paths_json: Mapped[str]=mapped_column(Text)
    start_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    created_by: Mapped[int]=mapped_column(ForeignKey('users.id'))
    formal_basis: Mapped[str]=mapped_column(Text)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    __table_args__=(CheckConstraint('start_at<end_at',name='ck_revision_grant_time'),CheckConstraint('length(trim(formal_basis))>0',name='ck_revision_grant_basis'))

class RevisionEditGrantRenewal(Base):
    """Explicit append-only windows; the primary grant remains unique/immutable."""
    __tablename__='revision_edit_grant_renewals'
    id: Mapped[int]=mapped_column(primary_key=True)
    original_grant_id: Mapped[int]=mapped_column(ForeignKey('revision_edit_grants.id'))
    request_id: Mapped[int]=mapped_column(ForeignKey('revision_requests.id'))
    cycle_id: Mapped[int]=mapped_column(ForeignKey('revision_correction_cycles.id'))
    source_release_id: Mapped[int]=mapped_column(ForeignKey('report_releases.id'))
    paths_json: Mapped[str]=mapped_column(Text)
    start_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    created_by: Mapped[int]=mapped_column(ForeignKey('users.id'))
    reason: Mapped[str]=mapped_column(Text)
    workflow_event_id: Mapped[int]=mapped_column(ForeignKey('workflow_events.id'),unique=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    __table_args__=(CheckConstraint('start_at<end_at',name='ck_renewal_time'),CheckConstraint('length(trim(reason))>0',name='ck_renewal_reason'))

for model in (RevisionRequest,RevisionRequestState,RevisionRequestEvent,RevisionCorrectionCycle,RevisionEditGrant,RevisionEditGrantRenewal):
    event.listen(model,'before_update',reject_history_change)
    event.listen(model,'before_delete',reject_history_change)
