"""Presentation assets are independent of approved report facts."""
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class SunumPhoto(Base):
    __tablename__ = 'sunum_photos'

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    period_id: Mapped[int] = mapped_column(ForeignKey('reporting_periods.id'))
    year: Mapped[int] = mapped_column(Integer)
    department_id: Mapped[int] = mapped_column(ForeignKey('departments.id'))
    caption: Mapped[str] = mapped_column(String(140))
    taken_on: Mapped[date | None] = mapped_column(Date)
    mahalle: Mapped[str | None] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(6))
    pair_key: Mapped[str | None] = mapped_column(String(36))
    webp_data: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    thumb_data: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    byte_size: Mapped[int] = mapped_column(Integer)
    consent_confirmed: Mapped[bool] = mapped_column(Boolean)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    __table_args__ = (
        UniqueConstraint('organization_id', 'year', 'sha256', name='uq_sunum_photo_year_sha'),
        UniqueConstraint('pair_key', 'kind', name='uq_sunum_photo_pair_kind'),
        CheckConstraint("(kind = 'single' AND pair_key IS NULL) OR (kind IN ('before','after') AND pair_key IS NOT NULL)", name='ck_sunum_photo_kind'),
        CheckConstraint('length(trim(caption)) BETWEEN 1 AND 140', name='ck_sunum_photo_caption'),
        CheckConstraint('consent_confirmed', name='ck_sunum_photo_consent'),
        CheckConstraint('width > 0 AND height > 0 AND width <= 1600 AND height <= 1600 AND byte_size > 0', name='ck_sunum_photo_size'),
    )
