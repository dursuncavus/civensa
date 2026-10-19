"""CIV-038: actual financial facts, independent of PP budget references."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, LargeBinary, Numeric, String, Text, UniqueConstraint, event, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .activity_sections_models import immutable


class ARBudgetRow(Base):
    __tablename__ = 'ar_budget_rows'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    row_key: Mapped[str] = mapped_column(String(150))
    department_id: Mapped[int | None] = mapped_column(ForeignKey('departments.id'))
    economic_code: Mapped[str] = mapped_column(String(5), default='')
    program_id: Mapped[int | None] = mapped_column(ForeignKey('programs.id'))
    subprogram_id: Mapped[int | None] = mapped_column(ForeignKey('subprograms.id'))
    initial: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    added: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    deducted: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    entered_final: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    actual: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    cancelled: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    carried: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    estimate: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    refunds: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    explanation: Mapped[str] = mapped_column(Text, default='')
    import_id: Mapped[int | None] = mapped_column(ForeignKey('ar_financial_imports.id'))
    __table_args__ = (UniqueConstraint('document_id', 'kind', 'row_key'),
        CheckConstraint("kind IN ('expenditure','programme','revenue')"),
        CheckConstraint("(kind = 'revenue' AND department_id IS NULL AND program_id IS NULL AND subprogram_id IS NULL) OR (kind = 'expenditure' AND department_id IS NOT NULL AND program_id IS NULL AND subprogram_id IS NULL) OR (kind = 'programme' AND department_id IS NOT NULL AND program_id IS NOT NULL)"),
        *[CheckConstraint(f'{field} IS NULL OR {field} >= 0') for field in ('initial','added','deducted','entered_final','actual','cancelled','carried','estimate','refunds')])


class ARFinancialPolicy(Base):
    __tablename__ = 'ar_financial_policies'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'), unique=True)
    lower_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    upper_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    __table_args__ = (CheckConstraint('lower_rate IS NULL OR lower_rate >= 0'),
        CheckConstraint('upper_rate IS NULL OR upper_rate >= 0'),
        CheckConstraint('lower_rate IS NULL OR upper_rate IS NULL OR lower_rate <= upper_rate'))


class ARFinancialEntry(Base):
    __tablename__ = 'ar_financial_entries'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    position: Mapped[int] = mapped_column()
    payload_json: Mapped[str] = mapped_column(Text)
    __table_args__ = (CheckConstraint("kind IN ('assets','aid','audit','explanations')"),)


class ARFinancialStatement(Base):
    __tablename__ = 'ar_financial_statements'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'), index=True)
    name: Mapped[str] = mapped_column(String(200))
    period: Mapped[str] = mapped_column(String(200), default='')
    statement_date: Mapped[str] = mapped_column(String(10), default='')
    explanation: Mapped[str] = mapped_column(Text, default='')
    figures_json: Mapped[str] = mapped_column(Text, default='[]')
    filename: Mapped[str] = mapped_column(String(200), default='')
    sha256: Mapped[str] = mapped_column(String(64), default='')
    file_data: Mapped[bytes | None] = mapped_column(LargeBinary)
    __table_args__ = (UniqueConstraint('document_id', 'name'),)


class ARFinancialImport(Base):
    __tablename__ = 'ar_financial_imports'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('ar_documents.id'), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    revision: Mapped[int] = mapped_column()
    source_sha256: Mapped[str] = mapped_column(String(64))
    preview_json: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


for action in ('before_update', 'before_delete'):
    event.listen(ARFinancialImport, action, immutable)
