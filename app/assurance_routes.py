"""Beyan variable forms and API, sharing real authentication and CSRF middleware."""
from contextlib import asynccontextmanager
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .db import get_db
from . import assurance_service as service
from . import activity_sections_service as sections
from .activity_sections_routes import transact, TurkishValidationRoute
from .assurance_guards import install_guards


def register(app):
    from .main import require_user, templates
    router = APIRouter(route_class=TurkishValidationRoute)
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application):
        application.state.assurance_integrity_error = service.check_startup()
        async with original_lifespan(application):
            yield

    app.router.lifespan_context = lifespan
    install_guards()
    templates.env.globals['assurance_view'] = service.view

    @router.post('/api/activity-sections/reports/{document_id}/assurances/{code}')
    def save(document_id: int, code: str, payload: dict,
             db: Session = Depends(get_db), user=Depends(require_user)):
        doc = transact(db, lambda: service.save(db, user, document_id, code, payload))
        return {'revision': doc.revision}

    def context(db, user, document_id, code):
        doc = sections.document(db, user, document_id)
        report = sections.report_data(db, user, document_id)
        slot = next(s for s in report['sections'] if s['code'] == 'EKLER')
        item = next((s for s in slot['assurances'] if s['code'] == code), None)
        if not item:
            sections.fail('Beyan bu raporda bulunamadı. EKLER listesinden bir beyan seçin.', 404)
        return {'user': user, 'report': report, 'statement': service.view(item), 'item': item,
                'editable': not report['frozen'] and report.get('workflow',{}).get('status')!='submitted' and service.can_edit(db, user, doc, code),
                'variables': item['variables']}

    @router.get('/activity-sections/reports/{document_id}/assurances/{code}')
    def editor(document_id: int, code: str, request: Request,
               db: Session = Depends(get_db), user=Depends(require_user)):
        return templates.TemplateResponse(request, 'assurance_editor.html', context(db, user, document_id, code))

    @router.post('/activity-sections/reports/{document_id}/assurances/{code}')
    async def form_save(document_id: int, code: str, request: Request,
                        db: Session = Depends(get_db), user=Depends(require_user)):
        form = await request.form()
        variables = {'place': str(form.get('place', '')), 'date': str(form.get('date', '')),
                     'signatories': [], 'reservations': []}
        try:
            allowed = {'csrf_token', 'expected_revision', 'place', 'date'}
            for i in range(101):
                person = {k: str(form.get(f'{k}_{i}', '')) for k in
                          ('person_ref', 'name', 'title', 'start_date', 'end_date')}
                reservation = {k: str(form.get(f'reservation_{k}_{i}', '')) for k in ('text', 'justification')}
                allowed.update(f'{k}_{i}' for k in person)
                allowed.update(f'reservation_{k}_{i}' for k in reservation)
                if any(person.values()): variables['signatories'].append(person)
                if any(reservation.values()): variables['reservations'].append(reservation)
            if set(form) - allowed or any(len(form.getlist(key)) != 1 for key in form):
                sections.fail(service.LOCK_ERROR)
            try:
                revision = int(str(form.get('expected_revision', '')))
            except ValueError:
                sections.fail('Rapor sürümü geçersiz. Sayfayı yenileyip yeniden kaydedin.')
            transact(db, lambda: service.save(db, user, document_id, code,
                     {'expected_revision': revision, 'variables': variables}))
            return RedirectResponse(f'/activity-sections/reports/{document_id}/assurances/{code}', 303)
        except HTTPException as error:
            # Preserve typed variable fields after validation/conflict errors.
            ctx = context(db, user, document_id, code)
            ctx.update(variables=variables, form_error=error.detail)
            return templates.TemplateResponse(request, 'assurance_editor.html', ctx, status_code=error.status_code)

    app.include_router(router)
