"""Directorate table forms/API; use the existing CSRF, scope and transactions."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel, Field, StrictBool, StrictInt
from sqlalchemy.orm import Session
from .db import get_db
from . import activity_sections_service as sections, ar_unit_tables_service as service
from .activity_sections_routes import TurkishValidationRoute, transact
from .models import ARUnitPhoto


class TableSave(BaseModel):
    model_config = {'extra': 'forbid'}
    expected_revision: StrictInt = Field(ge=0)
    rows: list[dict]
    no_projects: StrictBool | None = None


def register(app):
    from .main import require_user, templates
    router = APIRouter(route_class=TurkishValidationRoute)

    def context(db, user, document_id):
        doc = sections.document(db, user, document_id)
        if not doc.department_id and user.role != 'strategy':
            sections.fail('İdare tablolarını yalnız Strateji inceleyebilir. Kendi birim raporunuzu açın.', 403)
        report = service.with_photo_labels(db, sections.report_data(db, user, doc.id))
        from .ar_unit_workflow_service import state
        editable = bool(doc.department_id == user.department_id and user.role == 'department' and
                        not report['frozen'] and state(db, doc) in {'draft', 'returned'})
        return {'user': user, 'report': report, 'editable': editable,
                'data': report.get('unit_tables', {}), 'numbers': service.NUMBERS, 'money': service.MONEY,
                'staff': service.STAFF, 'project_states': service.PROJECT_STATES,
                'table_blockers': service.blockers(report) if doc.department_id else []}

    @router.get('/activity-sections/reports/{document_id}/unit-tables')
    def view(document_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        return templates.TemplateResponse(request, 'ar_unit_tables.html', context(db, user, document_id))

    @router.post('/api/activity-sections/reports/{document_id}/unit-tables/{kind}')
    def save(document_id: int, kind: str, data: TableSave,
             db: Session = Depends(get_db), user=Depends(require_user)):
        doc = transact(db, lambda: service.save(db, user, document_id, kind, **data.model_dump()))
        return {'revision': doc.revision}

    @router.post('/activity-sections/reports/{document_id}/unit-tables/{kind}')
    async def save_form(document_id: int, kind: str, request: Request,
                        db: Session = Depends(get_db), user=Depends(require_user)):
        form = await request.form(max_files=0, max_fields=22000)
        attempted = dict(form)
        try:
            if kind not in service.TABLES:
                sections.fail('Birim raporu tablosu bulunamadı. Tablo 1, 2, 7 veya 8 seçin.', 404)
            try:
                revision, count = int(form.get('expected_revision', '')), int(form.get('row_count', ''))
                if not 0 <= count <= 2000: raise ValueError()
            except (ValueError, TypeError):
                sections.fail(f'Tablo {kind}: Satır sayısı veya sürüm geçersiz. Sayfayı yenileyip yeniden deneyin.')
            fields = [key for key, _ in service.TABLES[kind][3] if key not in {'activity', 'total'}]
            rows = []
            for i in range(count):
                if kind in {'1', '8'} and form.get(f'include_{i}') != 'on': continue
                row = {key: str(form.get(f'{key}_{i}', '')) for key in fields}
                if kind in {'2', '7'}: row['key'] = str(form.get(f'key_{i}', ''))
                if kind == '7':
                    row.update(not_applied=form.get(f'not_applied_{i}') == 'on', reason=str(form.get(f'reason_{i}', '')))
                rows.append(row)
            choice = form.get('project_choice', '')
            no_projects = True if choice == 'none' else False if choice == 'rows' else None
            transact(db, lambda: service.save(db, user, document_id, kind, revision, rows, no_projects))
            return RedirectResponse(f'/activity-sections/reports/{document_id}/unit-tables#table-{kind}', 303)
        except HTTPException as error:
            if error.status_code not in {409, 422}: raise
            ctx = context(db, user, document_id)
            try: attempted_count = int(attempted.get('row_count', '1'))
            except (ValueError, TypeError): attempted_count = 1
            attempted['row_count'] = str(min(2000, max(1, attempted_count)))
            ctx.update(form_error=error.detail, attempted=attempted, attempted_kind=kind)
            return templates.TemplateResponse(request, 'ar_unit_tables.html', ctx, status_code=error.status_code)

    @router.post('/activity-sections/reports/{document_id}/unit-tables/photos/upload')
    async def upload(document_id: int, request: Request,
                     db: Session = Depends(get_db), user=Depends(require_user)):
        # Check scope before reading file bytes. Limit the multipart field as well
        # as the streamed file read; never allocate an unbounded upload.
        sections.document(db, user, document_id)
        form = await request.form(max_files=1, max_fields=10)
        try:
            try: revision = int(form.get('expected_revision', ''))
            except (ValueError, TypeError): sections.fail('Fotoğraf için rapor sürümü geçersiz. Sayfayı yenileyin.')
            file = form.get('file')
            if not hasattr(file, 'read'): sections.fail('Faaliyet fotoğrafı seçilmedi. JPG/PNG dosyası seçin.')
            raw = await file.read(service.MAX_FILE + 1)
            transact(db, lambda: service.upload(db, user, document_id, str(form.get('activity_key', '')),
                revision, str(form.get('caption', '')), raw, file.filename or ''))
            return RedirectResponse(f'/activity-sections/reports/{document_id}/unit-tables#photos', 303)
        except HTTPException as error:
            ctx = context(db, user, document_id)
            ctx.update(form_error=error.detail, photo_attempt=dict(form))
            return templates.TemplateResponse(request, 'ar_unit_tables.html', ctx, status_code=error.status_code)

    @router.post('/activity-sections/reports/{document_id}/unit-tables/photos/{photo_id}/remove')
    async def remove_photo(document_id: int, photo_id: int, request: Request,
                           db: Session = Depends(get_db), user=Depends(require_user)):
        sections.document(db, user, document_id)
        form = await request.form(max_files=0, max_fields=3)
        try:
            try: revision = int(form.get('expected_revision', ''))
            except (ValueError, TypeError): sections.fail('Fotoğraf için rapor sürümü geçersiz. Sayfayı yenileyin.')
            transact(db, lambda: service.remove_photo(db, user, document_id, photo_id, revision))
            return RedirectResponse(f'/activity-sections/reports/{document_id}/unit-tables#photos', 303)
        except HTTPException as error:
            ctx = context(db, user, document_id)
            ctx.update(form_error=error.detail)
            return templates.TemplateResponse(request, 'ar_unit_tables.html', ctx, status_code=error.status_code)

    @router.get('/activity-sections/reports/{document_id}/unit-tables/photos/{photo_id}')
    def photo(document_id: int, photo_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
        sections.document(db, user, document_id)
        photo = db.get(ARUnitPhoto, photo_id)
        if not photo or photo.document_id != document_id:
            sections.fail('Faaliyet fotoğrafı bulunamadı. Kendi raporunuzdaki fotoğrafı seçin.', 404)
        return Response(photo.file_data, media_type='image/png',
                        headers={'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})

    app.include_router(router)
