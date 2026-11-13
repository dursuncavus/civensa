"""Directorate guide tables and append-only activity photos (evidence DB storage)."""
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, LargeBinary, String, Text, UniqueConstraint, event, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .activity_sections_models import immutable


class ARUnitTable(Base):
    __tablename__ = 'ar_unit_tables'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'))
    kind: Mapped[str] = mapped_column(String(2))
    payload_json: Mapped[str] = mapped_column(Text)
    __table_args__ = (UniqueConstraint('document_id', 'kind'),
                      CheckConstraint("kind IN ('1','2','7','8')"))


class ARUnitPhoto(Base):
    __tablename__ = 'ar_unit_photos'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'))
    activity_key: Mapped[str] = mapped_column(String(80))
    caption: Mapped[str] = mapped_column(Text)
    filename: Mapped[str] = mapped_column(String(200))
    sha256: Mapped[str] = mapped_column(String(64))
    file_data: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))


class ARUnitPhotoRemoval(Base):
    __tablename__ = 'ar_unit_photo_removals'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'))
    photo_id: Mapped[int] = mapped_column(ForeignKey('ar_unit_photos.id'), unique=True)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


for model in (ARUnitPhoto, ARUnitPhotoRemoval):
    for action in ('before_update', 'before_delete'):
        event.listen(model, action, immutable)
