"""CIV-048 immutable plan versions and import history for future monitoring."""
from datetime import date, datetime
from sqlalchemy import (Boolean, CheckConstraint, Date, DateTime, ForeignKey,
                        ForeignKeyConstraint, Index, Integer, String, Text,
                        UniqueConstraint, event, func, text)
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .authorization_models import reject_history_change

COMPONENTS = {'KOS': 'Kontrol Ortamı', 'RDS': 'Risk Değerlendirme',
              'KFS': 'Kontrol Faaliyetleri', 'BİS': 'Bilgi ve İletişim', 'İS': 'İzleme'}
STANDARD_COMPONENTS = {f'{prefix}{n}': prefix for prefix, numbers in
                       [('KOS', range(1, 5)), ('RDS', range(5, 7)), ('KFS', range(7, 13)),
                        ('BİS', range(13, 17)), ('İS', range(17, 19))] for n in numbers}


class ICPlan(Base):
    __tablename__ = 'ic_plans'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    start_year: Mapped[int] = mapped_column(Integer)
    end_year: Mapped[int] = mapped_column(Integer)
    version_label: Mapped[str] = mapped_column(Text)
    approval_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default='draft')
    source_filename: Mapped[str] = mapped_column(Text)
    source_sha256: Mapped[str] = mapped_column(String(64))
    import_id: Mapped[int] = mapped_column(ForeignKey('ic_imports.id'), unique=True)
    supersedes_id: Mapped[int | None] = mapped_column(ForeignKey('ic_plans.id'))
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("status IN ('draft','active','archived')", name='ck_ic_plan_status'),
        CheckConstraint('start_year BETWEEN 1900 AND 2200 AND end_year BETWEEN start_year AND 2200', name='ck_ic_plan_years'),
        Index('uq_ic_one_active_plan', 'status', unique=True,
              postgresql_where=text("status = 'active'"), sqlite_where=text("status = 'active'")))


class ICStandard(Base):
    __tablename__ = 'ic_standards'
    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    component_code: Mapped[str] = mapped_column(String(5))
    title: Mapped[str | None] = mapped_column(Text)


class ICCondition(Base):
    __tablename__ = 'ic_conditions'
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey('ic_plans.id'), index=True)
    standard_code: Mapped[str] = mapped_column(ForeignKey('ic_standards.code'))
    standard_title: Mapped[str] = mapped_column(Text, default='')  # Version-local source title.
    condition_code: Mapped[str] = mapped_column(String(60))
    condition_code_raw: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    current_state_text: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint('plan_id', 'condition_code', name='uq_ic_condition_code'),
                      UniqueConstraint('id', 'plan_id', name='uq_ic_condition_plan'))


class ICAction(Base):
    __tablename__ = 'ic_actions'
    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey('ic_plans.id'), index=True)
    condition_id: Mapped[int] = mapped_column(Integer, index=True)
    action_code: Mapped[str] = mapped_column(String(60))
    action_code_raw: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    output_text: Mapped[str] = mapped_column(Text)
    start_raw: Mapped[str] = mapped_column(Text)
    due_raw: Mapped[str] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date)
    is_continuous: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint('plan_id', 'action_code', name='uq_ic_action_code'),
        ForeignKeyConstraint(['condition_id', 'plan_id'], ['ic_conditions.id', 'ic_conditions.plan_id']))


class ICActionParty(Base):
    __tablename__ = 'ic_action_parties'
    id: Mapped[int] = mapped_column(primary_key=True)
    action_id: Mapped[int] = mapped_column(ForeignKey('ic_actions.id'), index=True)
    role: Mapped[str] = mapped_column(String(20))
    department_id: Mapped[int | None] = mapped_column(ForeignKey('departments.id'), index=True)
    body_name: Mapped[str | None] = mapped_column(Text)
    all_departments: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_name: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        CheckConstraint("role IN ('responsible','cooperating')", name='ck_ic_party_role'),
        CheckConstraint('(CASE WHEN department_id IS NOT NULL THEN 1 ELSE 0 END + '
                        'CASE WHEN body_name IS NOT NULL THEN 1 ELSE 0 END + '
                        'CASE WHEN all_departments THEN 1 ELSE 0 END) = 1', name='ck_ic_party_target'))


class ICUnitAlias(Base):
    __tablename__ = 'ic_unit_aliases'
    id: Mapped[int] = mapped_column(primary_key=True)
    raw_name: Mapped[str] = mapped_column(Text, unique=True)  # Normalized matching key.
    department_id: Mapped[int | None] = mapped_column(ForeignKey('departments.id'))
    body_name: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint('(department_id IS NOT NULL AND body_name IS NULL) OR '
                                     '(department_id IS NULL AND body_name IS NOT NULL)', name='ck_ic_alias_target'),)


class ICImport(Base):
    __tablename__ = 'ic_imports'
    id: Mapped[int] = mapped_column(primary_key=True)
    source_filename: Mapped[str] = mapped_column(Text)
    source_sha256: Mapped[str] = mapped_column(String(64))
    source_json: Mapped[str] = mapped_column(Text)  # Parsed text only, no uploaded binary.
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ICImportAudit(Base):
    __tablename__ = 'ic_import_audits'
    id: Mapped[int] = mapped_column(primary_key=True)
    import_id: Mapped[int] = mapped_column(ForeignKey('ic_imports.id'), index=True)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey('ic_plans.id'))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    source_sha256: Mapped[str] = mapped_column(String(64))
    result: Mapped[str] = mapped_column(String(20))
    report_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint("result IN ('dry-run','commit','activation')", name='ck_ic_audit_result'),)


for model in (ICPlan, ICCondition, ICAction, ICActionParty, ICUnitAlias, ICImport, ICImportAudit):
    event.listen(model, 'before_update', reject_history_change)
    event.listen(model, 'before_delete', reject_history_change)

# Register monitoring metadata wherever the existing IC models are imported.
from . import internal_control_monitoring_models  # noqa: E402,F401
