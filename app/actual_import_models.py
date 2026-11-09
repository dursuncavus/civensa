"""Stored annual-actual previews; uploaded workbook bytes are never retained."""
from datetime import datetime, UTC
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class ActualImport(Base):
    __tablename__ = 'actual_imports'
    id: Mapped[int] = mapped_column(primary_key=True)
    report_revision_id: Mapped[int] = mapped_column(ForeignKey('activity_report_revisions.id'), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    source_sha256: Mapped[str] = mapped_column(String(64))
    preview_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
