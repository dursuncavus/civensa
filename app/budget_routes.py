"""Budget HTTP boundary: body awaits always precede synchronous locked work."""
import json
from datetime import datetime
from fastapi import Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.orm import Session
from .db import get_db
from .models import BudgetOperation, BudgetOperationLine, Department, ReportingPeriod, User
from . import budget_service as service
from . import authorization_service as auth


def register(app):
    from .main import require_user, templates

    def context(db, user):
        org_id, _ = service.authorize(db, user)
        return {'user': user, 'references': service.REFERENCES,
            'departments': db.scalars(select(Department).where(Department.organization_id == org_id, Department.is_active.is_(True)).order_by(Department.name)).all(),
            'periods': db.scalars(select(ReportingPeriod).order_by(ReportingPeriod.year.desc())).all()}

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
        return {'choices': [dict(index=i, name=next(d.name for d in ctx['deps'] if d.id == leg['department_id']),
            categories=[{'id': category, 'name': service.ECONOMIC_CATEGORIES.get(category, category)} for category in sorted({r.category for r in ctx['economic'] if r.department_id == leg['department_id'] and not service.protected(r.category)})],
            activities=[{'id': a.id, 'name': a.name} for a in ctx['activities'] if a.department_id == leg['department_id'] and not a.contract_bound]) for i, leg in enumerate(ctx['legs'])]}

    @app.get('/budget-reallocations')
    def index(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        ctx = context(db, user)
        org_id, _ = service.authorize(db, user)
        ctx['operations'] = db.scalars(select(BudgetOperation).where(BudgetOperation.organization_id == org_id).order_by(BudgetOperation.id.desc())).all()
        return templates.TemplateResponse(request, 'budget_index.html', ctx)

    @app.get('/budget-reallocations/new')
    def new(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        return templates.TemplateResponse(request, 'budget_wizard.html', context(db, user))

    @app.get('/budget-reallocations/{operation_id}')
    def detail(operation_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        ctx = context(db, user)
        org_id, _ = service.authorize(db, user)
        operation = db.get(BudgetOperation, operation_id)
        if not operation or operation.organization_id != org_id:
            raise HTTPException(404, 'Aktarma kaydı bulunamadı. İşlem listesini yenileyin.')
        ctx.update(operation=operation, actor=db.get(User, operation.actor_id), preview=json.loads(operation.preview_json),
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

    @app.post('/api/activities/{activity_id}/contract-bound')
    async def flag(activity_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        data = await body(request)
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
