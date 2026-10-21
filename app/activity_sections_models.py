"""Yearly EK-1 content, kept separate from publication-bound indicator revisions."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (Boolean, CheckConstraint, DateTime, ForeignKey, Integer,
                        Numeric, String, Text, UniqueConstraint, event, func)
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class ARSectionDefinition(Base):
    __tablename__ = 'ar_section_definitions'
    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[int] = mapped_column(Integer)
    code: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey('ar_section_definitions.id'))
    position: Mapped[int] = mapped_column(Integer)
    applies_to: Mapped[str] = mapped_column(String(10), default='both')
    birim_owner: Mapped[str] = mapped_column(String(30), default='directorate')
    idare_owner: Mapped[str] = mapped_column(String(30), default='strategy')
    content_kind: Mapped[str] = mapped_column(String(30), default='text')
    __table_args__ = (UniqueConstraint('version', 'code'),
        CheckConstraint("applies_to IN ('birim','idare','both')"),
        CheckConstraint("birim_owner IN ('directorate','strategy','finance') AND idare_owner IN ('directorate','strategy','finance')"),
        CheckConstraint("content_kind IN ('text','text+tables','structured-from-PP','assurance','financial')"))


class ARDocument(Base):
    __tablename__ = 'ar_documents'
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    period_id: Mapped[int] = mapped_column(ForeignKey('reporting_periods.id'))
    department_id: Mapped[int | None] = mapped_column(ForeignKey('departments.id'))
    scope: Mapped[str] = mapped_column(String(40))
    definition_version: Mapped[int] = mapped_column(Integer)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    __table_args__ = (UniqueConstraint('organization_id','period_id','scope'),
        CheckConstraint("(scope = 'idare' AND department_id IS NULL) OR (scope <> 'idare' AND department_id IS NOT NULL)"))


class ARSectionContent(Base):
    __tablename__ = 'ar_section_contents'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'))
    definition_id: Mapped[int] = mapped_column(ForeignKey('ar_section_definitions.id'))
    blocks_json: Mapped[str] = mapped_column(Text, default='[]')
    status: Mapped[str] = mapped_column(String(20), default='empty')
    reason: Mapped[str] = mapped_column(Text, default='')
    copied_from_id: Mapped[int | None] = mapped_column(ForeignKey('ar_document_freezes.id'))
    copied_from_approval_id: Mapped[int | None] = mapped_column(ForeignKey('ar_unit_workflow_events.id'))
    copied_needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    edited_by: Mapped[int | None] = mapped_column(ForeignKey('users.id'))
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint('document_id','definition_id'),
        CheckConstraint("status IN ('empty','draft','ready','not_applicable')"),
        CheckConstraint("status <> 'not_applicable' OR length(trim(reason)) > 0"))


class ARResourceRow(Base):
    __tablename__ = 'ar_resource_rows'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'))
    table_kind: Mapped[str] = mapped_column(String(30))
    position: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(Text, default='')
    category: Mapped[str] = mapped_column(Text, default='')
    address: Mapped[str] = mapped_column(Text, default='')
    purpose: Mapped[str] = mapped_column(Text, default='')
    ownership: Mapped[str] = mapped_column(String(20), default='')
    count: Mapped[int | None] = mapped_column(Integer)
    area: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    __table_args__ = (CheckConstraint('count IS NULL OR count >= 0'),
        CheckConstraint('area IS NULL OR area >= 0'),
        CheckConstraint("table_kind IN ('employment','education','gender','buildings','vehicles','hardware','software')"))


class ARDocumentFreeze(Base):
    __tablename__ = 'ar_document_freezes'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'), unique=True)
    payload_json: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ARContentEvent(Base):
    __tablename__ = 'ar_content_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'))
    section_code: Mapped[str] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(String(30))
    before_json: Mapped[str] = mapped_column(Text)
    after_json: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ARUnitWorkflowEvent(Base):
    """Append-only decisions; submitted and approved bytes are retained per version."""
    __tablename__ = 'ar_unit_workflow_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(20))
    from_status: Mapped[str] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text, default='')
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    actor_name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    content_event_cursor: Mapped[int] = mapped_column(Integer, default=0)
    payload_json: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str | None] = mapped_column(String(64))
    __table_args__ = (
        UniqueConstraint('document_id', 'revision'),
        CheckConstraint("(action = 'submit' AND from_status IN ('draft','returned') AND to_status = 'submitted') OR "
                        "(action = 'return' AND from_status = 'submitted' AND to_status = 'returned') OR "
                        "(action = 'approve' AND from_status = 'submitted' AND to_status = 'approved') OR "
                        "(action = 'reopen' AND from_status = 'approved' AND to_status = 'draft')"),
        CheckConstraint("action NOT IN ('return','reopen') OR length(trim(reason)) > 0"),
        CheckConstraint('revision > 0 AND content_event_cursor >= 0'),
        CheckConstraint("(action IN ('submit','approve') AND payload_json IS NOT NULL AND sha256 IS NOT NULL AND length(sha256) = 64) OR "
                        "(action IN ('return','reopen') AND payload_json IS NULL AND sha256 IS NULL)"),
    )


def immutable(mapper, connection, target):
    raise ValueError('Onaylı faaliyet raporu veya denetim geçmişi değiştirilemez; yeni yıl raporunu açın.')


for model in (ARDocumentFreeze, ARContentEvent, ARUnitWorkflowEvent):
    event.listen(model, 'before_update', immutable)
    event.listen(model, 'before_delete', immutable)

# EKLER variable model must also participate in Alembic metadata discovery.
from .assurance_models import AssuranceStatement  # noqa: F401
