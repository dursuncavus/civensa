"""Turkish AR unit workflow endpoints; all transitions share one transaction."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field, StrictInt, StrictStr
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from .db import get_db
from . import ar_unit_workflow_service as service
from .pp_errors import payload, pp_error


class Transition(BaseModel):
    model_config = {'extra': 'forbid'}
    expected_revision: StrictInt = Field(ge=0)
    reason: StrictStr = ''


class WorkflowRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handler(request):
            try:
                return await original(request)
            except RequestValidationError as error:
                labels = {'document_id':'Birim faaliyet raporu', 'expected_revision':'Rapor sürümü', 'reason':'Gerekçe'}
                fields = list(dict.fromkeys(str(issue['loc'][-1]) for issue in error.errors()))
                errors = [{'field':field, 'message':f'{labels.get(field,"Birim faaliyet raporu")} alanı geçersiz. '
                           'Rapor ve sürüm için geçerli tam sayı, gerekçe için metin girin.'} for field in fields]
                return JSONResponse({'detail':'Birim faaliyet raporu işlenemedi. ' + ' '.join(e['message'] for e in errors),
                                     'errors':errors}, status_code=422)
            except HTTPException as error:
                return JSONResponse(payload(error), status_code=error.status_code, headers=error.headers)
        return handler


def transact(db, operation):
    try:
        result = operation()
        db.commit()
        return result
    except HTTPException:
        db.rollback()
        raise
    except (IntegrityError, OperationalError):
        db.rollback()
        raise pp_error(409, 'Birim faaliyet raporu kaydedilemedi; eşzamanlı işlem veya bağlantı sorunu oluştu. Sayfayı yenileyip son sürümü kontrol edin.', 'expected_revision') from None


def register(app):
    from .main import require_user, templates
    router = APIRouter(route_class=WorkflowRoute)

    @router.post('/api/activity-sections/reports/{document_id}/workflow/{action}')
    def transition(document_id: int, action: str, data: Transition,
                   db: Session = Depends(get_db), user=Depends(require_user)):
        result = transact(db, lambda: service.transition(db, user, document_id, action, **data.model_dump()))
        return {'event_id': result.id, 'revision': result.revision, 'status': result.to_status,
                'label': service.STATUSES[result.to_status], 'sha256': result.sha256}

    @router.post('/activity-sections/reports/{document_id}/workflow/{action}')
    async def transition_form(document_id: int, action: str, request: Request,
                              db: Session = Depends(get_db), user=Depends(require_user)):
        form = await request.form()
        back = f'/activity-sections/reports/{document_id}'
        try:
            try:
                revision = int(form.get('expected_revision', ''))
                if revision < 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise pp_error(422, 'Birim faaliyet raporu sürümü geçersiz. Sayfayı yenileyip yeniden deneyin.', 'expected_revision') from None
            await run_in_threadpool(transact, db, lambda: service.transition(
                db, user, document_id, action, revision, str(form.get('reason', ''))))
            return RedirectResponse(back, 303)
        except HTTPException as error:
            # The reason and revision remain visible for correction; no redirects
            # with audit reasons in the URL, and Jinja escapes attempted input.
            return templates.TemplateResponse(request, 'ar_unit_workflow_error.html',
                {'user': user, 'message': error.detail, 'back': back, 'action': action,
                 'reason': str(form.get('reason', '')), 'revision': str(form.get('expected_revision', ''))},
                status_code=error.status_code)

    app.include_router(router)
