"""Year-scoped photo management; authorization can be widened at rollout here."""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from .. import sunum_photos_service as photos
from ..db import get_db
from ..file_security import read_upload_limited
from ..models import ReportingPeriod


def register(app):
    from ..main import require_strategy, templates
    from ..activity_sections_routes import TurkishValidationRoute, transact

    # Department rollout changes this single dependency, after authorization.
    photo_access = require_strategy
    router = APIRouter(route_class=TurkishValidationRoute)
    prefix = '/activity-sections/reports/{document_id}/photos'

    def page(request, db, user, doc, *, error=None, status=200, form=None):
        rows = photos.list_photos(db, doc)
        return templates.TemplateResponse(request, 'sunum_photos.html', dict(
            user=user, doc=doc, period=db.get(ReportingPeriod, doc.period_id),
            departments=photos.departments(db, doc), photos=rows, consent_text=photos.CONSENT,
            selected_count=sum(p.selected for p in rows), error=error, form=form or {}), status_code=status)

    @router.get(prefix)
    def listing(document_id: int, request: Request, db: Session = Depends(get_db), user=Depends(photo_access)):
        return page(request, db, user, photos.scope(db, user, document_id))

    @router.post(prefix)
    async def upload(document_id: int, request: Request, db: Session = Depends(get_db), user=Depends(photo_access)):
        doc = photos.scope(db, user, document_id)
        form = await request.form()
        try:
            images = []
            for field in ('file', 'after_file') if form.get('kind') == 'pair' else ('file',):
                file = form.get(field)
                if not isinstance(file, UploadFile) and not hasattr(file, 'read'):
                    photos.fail('Fotoğraf dosyası eksik. Tek fotoğraf veya önce/sonra için iki dosya seçin.')
                raw = await read_upload_limited(file, photos.RAW_LIMIT, 'Fotoğraf')
                images.append((raw, file.filename or ''))
            def operation():
                locked = photos.scope(db, user, document_id, lock=True)
                return photos.upload(db, locked, user, department_id=form.get('department_id'),
                    caption=str(form.get('caption', '')), taken_on=str(form.get('taken_on', '')),
                    mahalle=str(form.get('mahalle', '')), kind=form.get('kind'),
                    consent=form.get('consent') == 'on', images=images)
            transact(db, operation)
            return RedirectResponse(request.url.path, 303)
        except HTTPException as error:
            db.rollback()
            return page(request, db, user, doc, error=error.detail, status=error.status_code, form=form)

    @router.post(prefix + '/{photo_id}/{action}')
    async def change(document_id: int, photo_id: int, action: str, request: Request,
                     db: Session = Depends(get_db), user=Depends(photo_access)):
        doc = photos.scope(db, user, document_id)
        form = await request.form()
        try:
            def operation():
                locked = photos.scope(db, user, document_id, lock=True)
                photos.change(db, locked, photo_id, action, form.get('value'))
            transact(db, operation)
            return RedirectResponse(f'/activity-sections/reports/{doc.id}/photos', 303)
        except HTTPException as error:
            db.rollback()
            return page(request, db, user, doc, error=error.detail, status=error.status_code)

    @router.get(prefix + '/{photo_id}/image')
    def image(document_id: int, photo_id: int, thumbnail: bool = False,
              db: Session = Depends(get_db), user=Depends(photo_access)):
        doc = photos.scope(db, user, document_id)
        return Response(photos.image_bytes(db, doc, photo_id, thumbnail), media_type='image/webp',
                        headers={'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})

    app.include_router(router)
