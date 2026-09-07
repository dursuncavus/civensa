from datetime import datetime, UTC
from sqlalchemy import String, Integer, ForeignKey, Text, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    departments: Mapped[list["Department"]] = relationship(back_populates="organization")

class ReportingPeriod(Base):
    __tablename__ = "reporting_periods"
    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer, unique=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    template_status: Mapped[str] = mapped_column(String(30), default="verified")

class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(200))
    organization: Mapped[Organization] = relationship(back_populates="departments")
    indicators: Mapped[list["Indicator"]] = relationship(back_populates="department", cascade="all, delete-orphan")
    activities: Mapped[list["Activity"]] = relationship(back_populates="department", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(30))
    password_hash: Mapped[str] = mapped_column(String(255))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)

class Program(Base):
    __tablename__ = "programs"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    name: Mapped[str] = mapped_column(String(250))
    __table_args__ = (UniqueConstraint("period_id", "name", name="uq_program_period_name"),)

class SubProgram(Base):
    __tablename__ = "subprograms"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    program_id: Mapped[int] = mapped_column(ForeignKey("programs.id"))
    name: Mapped[str] = mapped_column(String(250))
    rationale: Mapped[str] = mapped_column(Text, default="")
    goal: Mapped[str] = mapped_column(Text, default="")
    program: Mapped[Program] = relationship()
    __table_args__ = (UniqueConstraint("period_id", "program_id", "name", name="uq_subprogram_period_program_name"),)

class Indicator(Base):
    __tablename__ = "indicators"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    subprogram_id: Mapped[int] = mapped_column(ForeignKey("subprograms.id"))
    name: Mapped[str] = mapped_column(String(300))
    unit: Mapped[str] = mapped_column(String(50))
    explanation: Mapped[str] = mapped_column(Text, default="")
    calculation_method: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(String(250), default="")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    department: Mapped[Department] = relationship(back_populates="indicators")
    subprogram: Mapped[SubProgram] = relationship()
    values: Mapped[list["IndicatorValue"]] = relationship(back_populates="indicator", cascade="all, delete-orphan", order_by="IndicatorValue.year")

class IndicatorValue(Base):
    __tablename__ = "indicator_values"
    id: Mapped[int] = mapped_column(primary_key=True)
    indicator_id: Mapped[int] = mapped_column(ForeignKey("indicators.id"))
    year: Mapped[int] = mapped_column(Integer)
    value_kind: Mapped[str] = mapped_column(String(30))
    value: Mapped[float] = mapped_column(Float, default=0)
    indicator: Mapped[Indicator] = relationship(back_populates="values")
    __table_args__ = (UniqueConstraint("indicator_id", "year", "value_kind", name="uq_indicator_year_kind"),)

class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    subprogram_id: Mapped[int | None] = mapped_column(ForeignKey("subprograms.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(350))
    explanation: Mapped[str] = mapped_column(Text, default="")
    budget_2025: Mapped[float] = mapped_column(Float, default=0)
    budget_2026: Mapped[float] = mapped_column(Float, default=0)
    budget_2027: Mapped[float] = mapped_column(Float, default=0)
    budget_2028: Mapped[float] = mapped_column(Float, default=0)
    budget_inside: Mapped[float] = mapped_column(Float, default=0)
    budget_outside: Mapped[float] = mapped_column(Float, default=0)
    department: Mapped[Department] = relationship(back_populates="activities")
    subprogram: Mapped[SubProgram | None] = relationship()

class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    return_note: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    __table_args__ = (UniqueConstraint("department_id", "period_id", name="uq_submission_department_period"),)

class TemplateSnapshot(Base):
    __tablename__ = "template_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(20))
    fields_json: Mapped[str] = mapped_column(Text, default="[]")
    missing_json: Mapped[str] = mapped_column(Text, default="[]")
    extra_json: Mapped[str] = mapped_column(Text, default="[]")
    departments_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
