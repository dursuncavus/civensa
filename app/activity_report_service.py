"""Read-only annual indicator pilot; no retrospective programme mapping."""
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from .models import ReportingPeriod, Indicator
from .numbers import format_number


def indicator_cell(row):
    if row is None:
        return 'Kayıt yok'
    if row.state != 'verified' or row.value is None:
        return f'Doğrulanmalı: {row.raw_text}' if row.raw_text else 'Doğrulanmalı'
    return format_number(row.value)


def annual_indicators(db, user, year):
    if user.role not in {'strategy', 'department'} or (user.role == 'department' and not user.department_id):
        raise HTTPException(403, 'Müdürlük atamanız bulunmuyor. Strateji biriminden yetkinizi kontrol etmesini isteyin.')
    period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == year))
    if period is None:
        return []
    query = select(Indicator).where(Indicator.period_id == period.id).options(
        selectinload(Indicator.values), selectinload(Indicator.department))
    if user.role == 'department':
        query = query.where(Indicator.department_id == user.department_id)
    from .structure_service import period_name
    result = []
    for indicator in db.scalars(query.order_by(Indicator.department_id, Indicator.position, Indicator.id)):
        values = {v.value_kind: v for v in indicator.values if v.year == year and v.value_kind in {'target', 'actual'}}
        result.append(dict(name=indicator.name, department=period_name(db, period.id, indicator.department),
                           unit=indicator.unit, source=indicator.data_source,
                           target=indicator_cell(values.get('target')),
                           actual=indicator_cell(values.get('actual'))))
    return result
