from datetime import datetime, UTC
from sqlalchemy import String, Integer, ForeignKey, Text, Float, Numeric, DateTime, UniqueConstraint, Boolean
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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


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
    card_id: Mapped[int | None] = mapped_column(ForeignKey("report_cards.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(80), default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    card: Mapped["ReportCard | None"] = relationship()
    name: Mapped[str] = mapped_column(String(300))
    unit: Mapped[str] = mapped_column(String(50))
    explanation: Mapped[str] = mapped_column(Text, default="")
    calculation_method: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    department: Mapped[Department] = relationship(back_populates="indicators")
    subprogram: Mapped[SubProgram] = relationship()
    values: Mapped[list["IndicatorValue"]] = relationship(back_populates="indicator", cascade="all, delete-orphan", order_by="IndicatorValue.year")


class IndicatorValue(Base):
    __tablename__ = "indicator_values"
    id: Mapped[int] = mapped_column(primary_key=True)
    indicator_id: Mapped[int] = mapped_column(ForeignKey("indicators.id"))
    year: Mapped[int] = mapped_column(Integer)
    value_kind: Mapped[str] = mapped_column(String(50))
    value: Mapped[float | None] = mapped_column(Numeric(26, 6), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    state: Mapped[str] = mapped_column(String(30), default="verified")
    indicator: Mapped[Indicator] = relationship(back_populates="values")
    __table_args__ = (UniqueConstraint("indicator_id", "year", "value_kind", name="uq_indicator_year_kind"),)


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    subprogram_id: Mapped[int | None] = mapped_column(ForeignKey("subprograms.id"), nullable=True)
    card_id: Mapped[int | None] = mapped_column(ForeignKey("report_cards.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(80), default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    card: Mapped["ReportCard | None"] = relationship()
    name: Mapped[str] = mapped_column(String(350))
    explanation: Mapped[str] = mapped_column(Text, default="")
    department: Mapped[Department] = relationship(back_populates="activities")
    subprogram: Mapped[SubProgram | None] = relationship()
    cost_values: Mapped[list["ActivityCostValue"]] = relationship(back_populates="activity", cascade="all, delete-orphan", order_by="ActivityCostValue.year")


class ActivityCostValue(Base):
    """Long-form activity budget value.

    value_kind supports budget, midyear_spend, year_end_estimate and forecast.
    funding_type supports total, inside and outside.
    This avoids year-specific database columns and survives annual template shifts.
    """
    __tablename__ = "activity_cost_values"
    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"))
    year: Mapped[int] = mapped_column(Integer)
    value_kind: Mapped[str] = mapped_column(String(50))
    funding_type: Mapped[str] = mapped_column(String(30), default="total")
    amount: Mapped[float | None] = mapped_column(Numeric(22, 2), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    state: Mapped[str] = mapped_column(String(30), default="verified")
    activity: Mapped[Activity] = relationship(back_populates="cost_values")
    __table_args__ = (UniqueConstraint("activity_id", "year", "value_kind", "funding_type", name="uq_activity_cost_value"),)


class DepartmentCostValue(Base):
    """Department-level non-activity cost values, e.g. Personnel and SGK."""
    __tablename__ = "department_cost_values"
    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    year: Mapped[int] = mapped_column(Integer)
    value_kind: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(50), default="personnel_sgk")
    amount: Mapped[float | None] = mapped_column(Numeric(22, 2), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    state: Mapped[str] = mapped_column(String(30), default="verified")
    __table_args__ = (UniqueConstraint("department_id", "period_id", "year", "value_kind", "category", name="uq_department_cost_value"),)


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    return_note: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    __table_args__ = (UniqueConstraint("department_id", "period_id", name="uq_submission_department_period"),)


class SubmissionEvent(Base):
    """Immutable workflow history for a department submission."""
    __tablename__ = "submission_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(30))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    note: Mapped[str] = mapped_column(Text, default="")
    snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))


class Notification(Base):
    """Role-scoped in-app notification generated by workflow transitions."""
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(30))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(String(500))
    link: Mapped[str] = mapped_column(String(300), default="")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))


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


class ImportBatch(Base):
    __tablename__ = "import_batches"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    filename: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="preview")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    # Snapshot of affected departments before applying the import. Used only for a
    # guarded rollback; never exposed to department users.
    snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    applied_hash: Mapped[str] = mapped_column(String(64), default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reverted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))


class ReportCard(Base):
    __tablename__ = "report_cards"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    subprogram_id: Mapped[int] = mapped_column(ForeignKey("subprograms.id"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    source_title: Mapped[str] = mapped_column(String(100), default="")
    administration: Mapped[str] = mapped_column(Text, default="")
    responsible: Mapped[str] = mapped_column(Text, default="")
    rationale: Mapped[str] = mapped_column(Text, default="")
    goal: Mapped[str] = mapped_column(Text, default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    calculation_method: Mapped[str] = mapped_column(Text, default="")
    data_source: Mapped[str] = mapped_column(Text, default="")
    footnote: Mapped[str] = mapped_column(Text, default="")
    source_page: Mapped[str] = mapped_column(String(100), default="")
    service_area: Mapped[str] = mapped_column(String(250), default="")
    strategic_link: Mapped[str] = mapped_column(Text, default="")
    subprogram: Mapped[SubProgram] = relationship()


class EconomicValue(Base):
    __tablename__ = "economic_values"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    year: Mapped[int] = mapped_column(Integer)
    value_kind: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(50))
    program_group: Mapped[str] = mapped_column(String(50))
    funding_type: Mapped[str] = mapped_column(String(30))
    amount: Mapped[float] = mapped_column(Numeric(22, 2))
    __table_args__ = (UniqueConstraint("period_id", "department_id", "year", "value_kind", "category", "program_group", "funding_type", name="uq_economic_cell"),)


class DepartmentScope(Base):
    __tablename__ = "department_scopes"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    display_name: Mapped[str] = mapped_column(String(250), default="")
    status: Mapped[str] = mapped_column(String(30), default="required")
    reason: Mapped[str] = mapped_column(Text, default="")
    __table_args__ = (UniqueConstraint("period_id", "department_id", name="uq_scope_department"),)


class ReportSection(Base):
    __tablename__ = "report_sections"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(300))
    kind: Mapped[str] = mapped_column(String(30), default="text")
    content_json: Mapped[str] = mapped_column(Text, default="{}")


class OfficialActivity(Base):
    __tablename__ = "official_activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    program_code: Mapped[str] = mapped_column(String(80), default="")
    program_name: Mapped[str] = mapped_column(String(300))
    subprogram_code: Mapped[str] = mapped_column(String(80), default="")
    subprogram_name: Mapped[str] = mapped_column(String(300))
    code: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(Text)


class ActivityResponsibility(Base):
    __tablename__ = "activity_responsibilities"
    id: Mapped[int] = mapped_column(primary_key=True)
    official_activity_id: Mapped[int] = mapped_column(ForeignKey("official_activities.id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    __table_args__ = (UniqueConstraint("official_activity_id", "department_id", name="uq_activity_department"),)


class ActivityCatalogueLink(Base):
    __tablename__ = "activity_catalogue_links"
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), primary_key=True)
    official_activity_id: Mapped[int] = mapped_column(ForeignKey("official_activities.id"), primary_key=True)


class Publication(Base):
    __tablename__ = "publications"
    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("reporting_periods.id"))
    version: Mapped[int] = mapped_column(Integer)
    snapshot_json: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    template_version: Mapped[str] = mapped_column(String(30), default="5.0")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    __table_args__ = (UniqueConstraint("period_id", "version", name="uq_publication_version"),)
