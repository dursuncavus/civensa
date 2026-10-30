"""CIV-160 period narrative: immutable full snapshots and workflow events."""
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint, event, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .authorization_models import reject_history_change


class ICNarrativeEvent(Base):
    __tablename__ = 'ic_narrative_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey('ic_monitoring_periods.id'), index=True)
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
        UniqueConstraint('period_id', 'revision'),
        CheckConstraint('revision > 0', name='ck_ic_narrative_revision'),
        CheckConstraint("(action='save' AND from_status IN ('draft','returned') AND to_status=from_status) OR "
                        "(action='submit' AND from_status IN ('draft','returned') AND to_status='submitted') OR "
                        "(action='return' AND from_status='submitted' AND to_status='returned') OR "
                        "(action='approve' AND from_status='submitted' AND to_status='approved') OR "
                        "(action='reopen' AND from_status='approved' AND to_status='draft')", name='ck_ic_narrative_transition'),
        CheckConstraint("action NOT IN ('return','reopen') OR length(trim(reason)) > 0", name='ck_ic_narrative_reason'))


event.listen(ICNarrativeEvent, 'before_update', reject_history_change)
event.listen(ICNarrativeEvent, 'before_delete', reject_history_change)
from .internal_control_narrative_guards import metadata_guards  # noqa: E402
event.listen(Base.metadata, 'after_create', metadata_guards)
