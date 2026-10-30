"""Budget HTTP boundary: body awaits always precede synchronous locked work."""
import json
from collections import defaultdict
from decimal import Decimal
from datetime import datetime
from fastapi import Depends, Request, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.orm import Session
from .db import get_db
from .models import BudgetOperation, BudgetOperationLine, Department, ReportingPeriod, User, DepartmentScope
from . import budget_service as service
from . import authorization_service as auth


def register(app):
    from .main import require_pp_period, require_user, templates

    def context(db, user, period_id=None):
        org_id, _ = service.authorize(db, user)
        periods = db.scalars(select(ReportingPeriod).order_by(ReportingPeriod.year.desc())).all()
        departments = db.scalars(select(Department).where(Department.organization_id == org_id,
            or_(Department.is_active.is_(True), Department.id.in_(select(DepartmentScope.department_id).where(
                DepartmentScope.active_to.is_not(None))))).order_by(Department.id)).all()
        names_by_period = {period.id: {dep.id: service.structure.period_name(db, period.id, dep)
            for dep in departments} for period in periods}
        selected = period_id or (periods[0].id if periods else None)
        return {'user': user, 'references': service.REFERENCES, 'departments': departments, 'periods': periods,
            'department_names': names_by_period.get(selected, {}), 'department_names_by_period': names_by_period}

    def commit(db, work):
        try:
            result = work()
            db.commit()
            return {'ok': True, 'id': result.id}
        except (OperationalError, IntegrityError) as exc:
            db.rollback()
            if isinstance(exc, OperationalError) and getattr(exc.orig, 'sqlstate', None) not in {'40P01', '40001', '55P03'}:
                raise
            raise HTTPException(409, service.CONFLICT) from None
        except Exception:
            db.rollback()
            raise


    async def body(request):
        try:
            return await request.json()
        except (ValueError, UnicodeDecodeError):
            service.fail('Aktarma bilgileri okunamadı. Formu yeniden doldurup gönderin.')

    @app.post('/api/budget-reallocations/choices')
    async def choices(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        data = await body(request)
        ctx = service.scope(db, user, data)
        service.check_increases(db, ctx, ctx['legs'])
        return {'choices': [dict(index=i, name=ctx['names'][leg['department_id']],
            categories=[{'id': category, 'name': service.ECONOMIC_CATEGORIES.get(category, category)} for category in sorted({r.category for r in ctx['economic'] if r.department_id == leg['department_id'] and not service.protected(r.category)})],
            activities=[{'id': a.id, 'name': a.name} for a in ctx['activities'] if a.department_id == leg['department_id'] and not a.contract_bound]) for i, leg in enumerate(ctx['legs'])]}

    @app.get('/budget-reallocations')
    def index(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        ctx = context(db, user)
        org_id, _ = service.authorize(db, user)
        operations = db.scalars(select(BudgetOperation).where(
            BudgetOperation.organization_id == org_id).order_by(BudgetOperation.id.desc())).all()
        operation_ids = {item.id for item in operations}
        lines = db.scalars(select(BudgetOperationLine).where(
            BudgetOperationLine.operation_id.in_(operation_ids)).order_by(
                BudgetOperationLine.operation_id, BudgetOperationLine.id)).all() if operation_ids else []
        department_ids = {line.department_id for line in lines}
        departments = db.scalars(select(Department).where(Department.id.in_(department_ids))).all() if department_ids else []
        department_names = {item.id: item.name for item in departments}
        lines_by_operation = defaultdict(list)
        for line in lines:
            lines_by_operation[line.operation_id].append(line)

        operation_labels = {}
        for item in operations:
            changes = defaultdict(Decimal)
            for line in lines_by_operation[item.id]:
                changes[line.department_id] += Decimal(line.after) - Decimal(line.before)
            decreases = [(department_id, -change) for department_id, change in changes.items() if change < 0]
            increases = [(department_id, change) for department_id, change in changes.items() if change > 0]
            if decreases and increases:
                period_names = ctx['department_names_by_period'].get(item.period_id, {})
                name = lambda department_id: period_names.get(department_id) or department_names.get(department_id, '')
                text = f'{name(decreases[0][0])} → {name(increases[0][0])}'
                other_count = len(decreases) + len(increases) - 2
                if other_count:
                    text += f' ve {other_count} müdürlük daha'
                amount = sum((change for _, change in decreases), Decimal(0))
                operation_labels[item.id] = f'{text} · {service.money(amount)} TL'
            else:
                operation_labels[item.id] = 'Aktarma ayrıntısı bulunmuyor'

        operations_by_id = {item.id: item for item in operations}
        reversal_labels = {}
        for item in operations:
            reversed_operation = operations_by_id.get(item.reverses_id)
            if reversed_operation:
                reference = ctx['references'].get(reversed_operation.reference_type, 'Dayanak')
                reference_date = datetime.fromisoformat(reversed_operation.reference_date).strftime('%d.%m.%Y')
                reversal_labels[item.id] = (
                    f'Telafi: {reference} {reference_date} / {reversed_operation.reference_number}'
                )
        ctx.update(operations=operations, operation_labels=operation_labels, reversal_labels=reversal_labels)
        return templates.TemplateResponse(request, 'budget_index.html', ctx)

    @app.get('/budget-reallocations/new')
    def new(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        return templates.TemplateResponse(request, 'budget_wizard.html', context(db, user))

    @app.get('/budget-reallocations/{operation_id}')
    def detail(operation_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        org_id, _ = service.authorize(db, user)
        operation = db.get(BudgetOperation, operation_id)
        if not operation or operation.organization_id != org_id:
            raise HTTPException(404, 'Aktarma kaydı bulunamadı. İşlem listesini yenileyin.')
        ctx = context(db, user, operation.period_id)
        preview = json.loads(operation.preview_json)
        for summary in preview['summaries'] + preview.get('department_results', []):
            dep = db.get(Department, summary['department_id'])
            summary['name'] = service.structure.period_name(db, operation.period_id, dep)
        ctx.update(operation=operation, actor=db.get(User, operation.actor_id), preview=preview,
            reference_request=json.loads(operation.request_json),
            reversal=db.scalar(select(BudgetOperation).where(BudgetOperation.reverses_id == operation.id)),
            lines=db.scalars(select(BudgetOperationLine).where(BudgetOperationLine.operation_id == operation.id).order_by(BudgetOperationLine.id)).all())
        return templates.TemplateResponse(request, 'budget_detail.html', ctx)

    @app.post('/api/budget-reallocations/preview')
    async def preview(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        data = await body(request)
        return service.preview(db, user, data)

    @app.post('/api/budget-reallocations/apply')
    async def apply(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        data = await body(request)
        return commit(db, lambda: service.apply(db, user, data))

    @app.post('/api/budget-reallocations/{operation_id}/reverse')
    async def reverse(operation_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        data = await body(request)
        if not isinstance(data, dict):
            service.fail('Geri alma bilgileri geçersiz. Dayanağı ve gerekçeyi yeniden girin.')
        return commit(db, lambda: service.reverse(db, user, operation_id, data))

    @app.post('/api/activities/{activity_id}/contract-bound', dependencies=[Depends(require_pp_period)])
    async def flag(activity_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        data = await body(request)
        from .main import pp_period
        from .models import Activity
        activity = db.get(Activity, activity_id)
        if activity:
            pp_period(request, db, user, activity.department_id, data, activity.period_id)
        return commit(db, lambda: service.set_contract_bound(db, user, activity_id, data.get('contract_bound') if isinstance(data, dict) else None))

    @app.post('/api/budget-reallocations/delegations')
    async def delegate(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        data = await body(request)
        org_id, _ = service.authorize(db, user)
        if not isinstance(data, dict):
            service.fail('Yetki devri bilgileri geçersiz. Formu yeniden doldurun.')
        try:
            start, end = (datetime.fromisoformat(data.get(key, '')) for key in ('start_at', 'end_at'))
        except (TypeError, ValueError):
            service.fail('Yetki devri tarihleri geçersiz. Saat dilimi içeren başlangıç ve bitiş girin.')
        return commit(db, lambda: auth.create_delegation(db, user, org_id, user.department_id,
            service.identifier(data.get('delegate_user_id'), 'Vekil'), start, end, data.get('formal_basis'), authority_kind=service.AUTHORITY))

    @app.post('/api/budget-reallocations/delegations/{delegation_id}/revoke')
    async def revoke(delegation_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        data = await body(request)
        service.authorize(db, user)
        if not isinstance(data, dict):
            service.fail('İptal gerekçesi geçersiz. Gerekçeyi yeniden girin.')
        def work():
            auth.revoke_delegation(db, user, delegation_id, data.get('reason'))
            from .models import AuthorityDelegation
            return db.get(AuthorityDelegation, delegation_id)
        return commit(db, work)
