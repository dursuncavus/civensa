"""CIV-079 monitoring streams. Content and decisions are immutable versions."""
from datetime import date, datetime
from sqlalchemy import (CheckConstraint, Date, DateTime, ForeignKey, Index, Integer,
                        String, Text, UniqueConstraint, event, func, text)
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .authorization_models import reject_history_change


class ICMonitoringPeriod(Base):
    __tablename__ = 'ic_monitoring_periods'
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey('ic_plans.id'))
    year: Mapped[int] = mapped_column(Integer)
    half: Mapped[int] = mapped_column(Integer)
    deadline: Mapped[date] = mapped_column(Date)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint('plan_id', 'year', 'half', name='uq_ic_monitoring_period'),
        CheckConstraint('half IN (1,2) AND year BETWEEN 1900 AND 2200', name='ck_ic_monitoring_period'),
        Index('uq_ic_monitoring_open', 'plan_id', unique=True,
              postgresql_where=text('closed_at IS NULL'), sqlite_where=text('closed_at IS NULL')))


class ICMonitoringPeriodEvent(Base):
    __tablename__ = 'ic_monitoring_period_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey('ic_monitoring_periods.id'))
    action: Mapped[str] = mapped_column(String(10))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    actor_name: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('period_id', 'action'),
                      CheckConstraint("action IN ('open','close')", name='ck_ic_monitoring_period_event'))


class ICMonitoringBatch(Base):
    __tablename__ = 'ic_monitoring_batches'
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey('ic_monitoring_periods.id'), index=True)
    scope_key: Mapped[str] = mapped_column(Text)
    department_id: Mapped[int | None] = mapped_column(ForeignKey('departments.id'))
    body_name: Mapped[str | None] = mapped_column(Text)
    label: Mapped[str] = mapped_column(Text)
    __table_args__ = (UniqueConstraint('period_id', 'scope_key'),
                      CheckConstraint('(department_id IS NOT NULL AND body_name IS NULL) OR '
                                      '(department_id IS NULL AND body_name IS NOT NULL)', name='ck_ic_monitoring_owner'))


class ICMonitoringTarget(Base):
    __tablename__ = 'ic_monitoring_targets'
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey('ic_monitoring_batches.id'), index=True)
    action_id: Mapped[int] = mapped_column(ForeignKey('ic_actions.id'))
    __table_args__ = (UniqueConstraint('batch_id', 'action_id'),)


class ICMonitoringEvent(Base):
    __tablename__ = 'ic_monitoring_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey('ic_monitoring_batches.id'), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(10))
    from_status: Mapped[str] = mapped_column(String(12))
    to_status: Mapped[str] = mapped_column(String(12))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    actor_name: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    snapshot_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint('batch_id', 'revision'),
        CheckConstraint('revision > 0', name='ck_ic_monitoring_revision'),
        CheckConstraint("(action='save' AND from_status IN ('draft','returned') AND to_status=from_status) OR "
                        "(action='submit' AND from_status IN ('draft','returned') AND to_status='submitted') OR "
                        "(action='return' AND from_status='submitted' AND to_status='returned') OR "
                        "(action='approve' AND from_status='submitted' AND to_status='approved') OR "
                        "(action='reopen' AND from_status='approved' AND to_status='draft')", name='ck_ic_monitoring_transition'),
        CheckConstraint("action NOT IN ('return','reopen') OR length(trim(reason)) > 0", name='ck_ic_monitoring_reason'))


class ICMonitoringEntry(Base):
    __tablename__ = 'ic_monitoring_entries'
    id: Mapped[int] = mapped_column(primary_key=True)
    target_id: Mapped[int] = mapped_column(ForeignKey('ic_monitoring_targets.id'), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey('ic_monitoring_events.id'), unique=True)
    status: Mapped[str] = mapped_column(String(15))
    percentage: Mapped[int | None] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    evidence: Mapped[str] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint("status IN ('completed','ongoing','not_started','delayed','partial','not_approved') AND (status != 'partial' OR (percentage IS NOT NULL AND percentage BETWEEN 1 AND 99)) AND (status != 'not_approved' OR length(trim(explanation)) > 0)", name='ck_ic_monitoring_entry_status'),
        CheckConstraint('(percentage BETWEEN 0 AND 100) AND (percentage IS NOT NULL OR status IN (\'not_started\',\'not_approved\'))', name='ck_ic_monitoring_percentage'),
        CheckConstraint("status != 'delayed' OR length(trim(reason)) > 0", name='ck_ic_monitoring_delay_reason'))


class ICMonitoringNote(Base):
    __tablename__ = 'ic_monitoring_notes'
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey('ic_monitoring_periods.id'), index=True)
    action_id: Mapped[int] = mapped_column(ForeignKey('ic_actions.id'))
    department_id: Mapped[int] = mapped_column(ForeignKey('departments.id'))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    actor_name: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint('length(trim(content)) BETWEEN 1 AND 2000', name='ck_ic_monitoring_note'),)


IMMUTABLE_MODELS = (ICMonitoringPeriodEvent, ICMonitoringBatch, ICMonitoringTarget,
                    ICMonitoringEvent, ICMonitoringEntry, ICMonitoringNote)
for model in IMMUTABLE_MODELS:
    event.listen(model, 'before_update', reject_history_change)
    event.listen(model, 'before_delete', reject_history_change)
event.listen(ICMonitoringPeriod, 'before_update', reject_history_change)
event.listen(ICMonitoringPeriod, 'before_delete', reject_history_change)

from .internal_control_monitoring_guards import metadata_guards  # noqa: E402
event.listen(Base.metadata, 'after_create', metadata_guards)

from . import internal_control_questionnaire_models  # noqa: E402,F401
