"""Additive Phases 1–2 projections and immutable authority/change history."""
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, event, func, text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class AuthorizationConfiguration(Base):
    __tablename__ = 'authorization_configurations'
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), primary_key=True)
    workflow_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text('false'))
    # Activation needs a later reviewed migration, not an environment toggle.
    __table_args__ = (CheckConstraint('workflow_enabled = false', name='ck_auth_foundation_disabled'),)


class DirectorateMembership(Base):
    __tablename__ = 'directorate_memberships'
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    department_id: Mapped[int] = mapped_column(ForeignKey('departments.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    role_code: Mapped[str] = mapped_column(String(40))
    slot: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text('true'))
    formal_basis: Mapped[str] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    __table_args__ = (
        CheckConstraint("(role_code = 'department_editor' AND slot IN (1,2)) OR (role_code = 'department_director' AND slot = 3)", name='ck_directorate_role_slot'),
        CheckConstraint('length(trim(formal_basis)) > 0', name='ck_membership_basis'),
        Index('uq_active_directorate_slot', 'department_id', 'slot', unique=True, postgresql_where=text('active'), sqlite_where=text('active = 1')),
        Index('uq_active_directorate_person', 'user_id', unique=True, postgresql_where=text('active'), sqlite_where=text('active = 1')),
    )


class MembershipEvent(Base):
    __tablename__ = 'membership_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    membership_id: Mapped[int] = mapped_column(ForeignKey('directorate_memberships.id'))
    actor_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    actor_snapshot_json: Mapped[str] = mapped_column(Text)
    event_type: Mapped[str] = mapped_column(String(40))
    previous_json: Mapped[str] = mapped_column(Text)
    new_json: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuthorityDelegation(Base):
    __tablename__ = 'authority_delegations'
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    department_id: Mapped[int] = mapped_column(ForeignKey('departments.id'))
    authority_kind: Mapped[str] = mapped_column(String(40), default='director_approval', server_default='director_approval')
    director_membership_id: Mapped[int] = mapped_column(ForeignKey('directorate_memberships.id'))
    delegate_membership_id: Mapped[int] = mapped_column(ForeignKey('directorate_memberships.id'))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text('true'))
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    formal_basis: Mapped[str] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint('start_at < end_at', name='ck_delegation_interval'), CheckConstraint('director_membership_id <> delegate_membership_id', name='ck_delegation_distinct'), CheckConstraint('length(trim(formal_basis)) > 0', name='ck_delegation_basis'))


class DelegationRevocation(Base):
    __tablename__ = 'delegation_revocations'
    id: Mapped[int] = mapped_column(primary_key=True)
    delegation_id: Mapped[int] = mapped_column(ForeignKey('authority_delegations.id'), unique=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint('length(trim(reason)) > 0', name='ck_delegation_revoke_reason'),)


class DelegationEvent(Base):
    __tablename__ = 'delegation_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    delegation_id: Mapped[int] = mapped_column(ForeignKey('authority_delegations.id'))
    actor_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    actor_snapshot_json: Mapped[str] = mapped_column(Text)
    event_type: Mapped[str] = mapped_column(String(40))
    context_json: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FinalAuthorityAssignment(Base):
    __tablename__ = 'final_authority_assignments'
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    formal_basis: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text('true'))
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    __table_args__ = (CheckConstraint('length(trim(formal_basis)) > 0', name='ck_final_authority_basis'), Index('uq_active_final_authority', 'organization_id', unique=True, postgresql_where=text('active'), sqlite_where=text('active = 1')))


class FinalAuthorityEvent(Base):
    __tablename__ = 'final_authority_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey('final_authority_assignments.id'))
    actor_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    actor_snapshot_json: Mapped[str] = mapped_column(Text)
    previous_json: Mapped[str] = mapped_column(Text)
    new_json: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkflowEvent(Base):
    __tablename__ = 'workflow_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    actor_snapshot_json: Mapped[str] = mapped_column(Text)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    department_id: Mapped[int | None] = mapped_column(ForeignKey('departments.id'), nullable=True)
    event_type: Mapped[str] = mapped_column(String(80))
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(100))
    context_json: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30))
    correlation_id: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint("source IN ('manual','import','ex_officio','administrative')", name='ck_workflow_event_source'), CheckConstraint("source <> 'ex_officio' OR length(trim(reason)) > 0", name='ck_ex_officio_reason'))


class FieldChangeEvent(Base):
    __tablename__ = 'field_change_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_event_id: Mapped[int] = mapped_column(ForeignKey('workflow_events.id'), index=True)
    field_key: Mapped[str] = mapped_column(String(200))
    field_type: Mapped[str] = mapped_column(String(40))
    previous_json: Mapped[str] = mapped_column(Text)
    new_json: Mapped[str] = mapped_column(Text)
    revision_request_id: Mapped[int | None] = mapped_column(ForeignKey('revision_requests.id'), nullable=True)


class NotificationRecipient(Base):
    __tablename__ = 'notification_recipients'
    id: Mapped[int] = mapped_column(primary_key=True)
    notification_id: Mapped[int] = mapped_column(ForeignKey('notifications.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (UniqueConstraint('notification_id', 'user_id', name='uq_notification_recipient'),)


IMMUTABLE_AUTH_MODELS = (MembershipEvent, AuthorityDelegation, DelegationRevocation,
                         DelegationEvent, FinalAuthorityEvent, WorkflowEvent, FieldChangeEvent)


def reject_history_change(mapper, connection, target):
    raise ValueError('Yetki ve değişiklik geçmişi değiştirilemez; yeni olay kaydedin.')


for model in IMMUTABLE_AUTH_MODELS:
    event.listen(model, 'before_update', reject_history_change)
    event.listen(model, 'before_delete', reject_history_change)

# State projections change only through audited Core operations in the service.
for model in (DirectorateMembership, FinalAuthorityAssignment):
    event.listen(model, 'before_update', reject_history_change)
    event.listen(model, 'before_delete', reject_history_change)
