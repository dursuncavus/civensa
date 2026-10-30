"""CIV-085 immutable question catalogues, participation revisions and answers."""
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint, event, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .authorization_models import reject_history_change


class ICQuestionList(Base):
    __tablename__ = 'ic_question_lists'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    questions_json: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    actor_name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint('length(trim(name)) BETWEEN 1 AND 200', name='ck_ic_question_list_name'),)


class ICQuestionAttachment(Base):
    __tablename__ = 'ic_question_attachments'
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey('ic_monitoring_periods.id'), index=True)
    list_id: Mapped[int] = mapped_column(ForeignKey('ic_question_lists.id'))
    revision: Mapped[int] = mapped_column(Integer)
    departments_json: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    actor_name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint('period_id', 'revision'), CheckConstraint('revision > 0', name='ck_ic_question_attachment_revision'))


class ICQuestionBatch(Base):
    __tablename__ = 'ic_question_batches'
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey('ic_monitoring_periods.id'), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey('departments.id'))
    label: Mapped[str] = mapped_column(Text)
    __table_args__ = (UniqueConstraint('period_id', 'department_id'),)


class ICQuestionEvent(Base):
    __tablename__ = 'ic_question_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey('ic_question_batches.id'), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(Text)
    from_status: Mapped[str] = mapped_column(Text)
    to_status: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    actor_name: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    snapshot_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint('batch_id', 'revision'),
        CheckConstraint('revision > 0', name='ck_ic_question_revision'),
        CheckConstraint("(action='save' AND from_status IN ('draft','returned') AND to_status=from_status) OR "
                        "(action='submit' AND from_status IN ('draft','returned') AND to_status='submitted') OR "
                        "(action='return' AND from_status='submitted' AND to_status='returned') OR "
                        "(action='approve' AND from_status='submitted' AND to_status='approved') OR "
                        "(action='reopen' AND from_status='approved' AND to_status='draft')", name='ck_ic_question_transition'),
        CheckConstraint("action NOT IN ('return','reopen') OR length(trim(reason)) > 0", name='ck_ic_question_reason'))


IMMUTABLE_MODELS = (ICQuestionList, ICQuestionAttachment, ICQuestionBatch, ICQuestionEvent)
for model in IMMUTABLE_MODELS:
    event.listen(model, 'before_update', reject_history_change)
    event.listen(model, 'before_delete', reject_history_change)

from .internal_control_questionnaire_guards import metadata_guards  # noqa: E402
event.listen(Base.metadata, 'after_create', metadata_guards)
