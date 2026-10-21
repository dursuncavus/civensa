"""Evidence uses the same database binary storage as financial statements."""
from datetime import datetime, UTC
from sqlalchemy import ForeignKey, String, Integer, Text, LargeBinary, DateTime, UniqueConstraint, CheckConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class ActivityEvidenceFile(Base):
    __tablename__ = 'activity_evidence_files'
    id: Mapped[int] = mapped_column(primary_key=True)
    actual_revision_id: Mapped[int] = mapped_column(ForeignKey('actual_revisions.id'), index=True)
    actual_revision: Mapped['ActualRevision'] = relationship()
    report_indicator_id: Mapped[int] = mapped_column(ForeignKey('report_indicators.id'))
    source_id: Mapped[str] = mapped_column(String(36))
    version: Mapped[int] = mapped_column(Integer)
    filename: Mapped[str] = mapped_column(String(200))
    sha256: Mapped[str] = mapped_column(String(64))
    file_data: Mapped[bytes] = mapped_column(LargeBinary)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    __table_args__ = (UniqueConstraint('report_indicator_id', 'source_id', 'version', name='uq_activity_evidence_version'),
                      CheckConstraint('version > 0', name='ck_activity_evidence_version'))


class ActivityEvidenceFreeze(Base):
    __tablename__ = 'activity_evidence_freezes'
    id: Mapped[int] = mapped_column(primary_key=True)
    report_revision_id: Mapped[int] = mapped_column(ForeignKey('activity_report_revisions.id'), unique=True)
    manifest_json: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))


def immutable(mapper, connection, target):
    raise ValueError('Kanıt dosyası veya dondurulmuş ek listesi değiştirilemez; yeni dosya sürümü oluşturun.')


for model in (ActivityEvidenceFile, ActivityEvidenceFreeze):
    event.listen(model, 'before_update', immutable)
    event.listen(model, 'before_delete', immutable)
