"""CIV-031 append-only budget instructions and exact value changes."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, event, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .authorization_models import reject_history_change


class BudgetOperation(Base):
    __tablename__ = 'budget_operations'
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'))
    period_id: Mapped[int] = mapped_column(ForeignKey('reporting_periods.id'))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    delegation_id: Mapped[int | None] = mapped_column(ForeignKey('authority_delegations.id'), nullable=True)
    reverses_id: Mapped[int | None] = mapped_column(ForeignKey('budget_operations.id'), unique=True, nullable=True)
    year: Mapped[int] = mapped_column(Integer)
    value_kind: Mapped[str] = mapped_column(String(50))
    phase: Mapped[str] = mapped_column(String(30))
    reference_type: Mapped[str] = mapped_column(String(50))
    reference_date: Mapped[str] = mapped_column(String(10))
    reference_number: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str] = mapped_column(Text)
    request_json: Mapped[str] = mapped_column(Text)
    preview_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BudgetOperationLine(Base):
    __tablename__ = 'budget_operation_lines'
    id: Mapped[int] = mapped_column(primary_key=True)
    operation_id: Mapped[int] = mapped_column(ForeignKey('budget_operations.id'), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey('departments.id'))
    value_table: Mapped[str] = mapped_column(String(30))
    value_id: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(Text)
    funding_type: Mapped[str] = mapped_column(String(30))
    before: Mapped[Decimal] = mapped_column(Numeric(22, 2))
    after: Mapped[Decimal] = mapped_column(Numeric(22, 2))
    before_json: Mapped[str] = mapped_column(Text)
    after_json: Mapped[str] = mapped_column(Text)


for model in (BudgetOperation, BudgetOperationLine):
    event.listen(model, 'before_update', reject_history_change)
    event.listen(model, 'before_delete', reject_history_change)
