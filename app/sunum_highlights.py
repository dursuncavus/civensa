"""Year-scoped editorial highlights: service and Strateji routes."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import activity_sections_service as reports, sunum_photos_service as photos
from .db import get_db
from .models import Department, ReportingPeriod
from .sunum.facts import facts
from .sunum.models import SunumHighlight

EDIT_ROLES = {'strategy'}  # Widen here only at an authorized rollout.
DIGIT_ERROR = 'Cümleye rakam yazmayın; rakam rapordan otomatik gelir. Rakamı listeden seçin.'
MISSING = 'Bu rakam raporda artık yok; başka bir rakam seçin.'


def scope(db, user, document_id, *, lock=False):
    doc = reports.document(db, user, document_id)
    if doc.department_id is not None:
        reports.fail('Meclis sunumu öne çıkanları için idare faaliyet raporunu açın.')
    if lock:
        # Lock the year itself, including when more than one document points to it.
        db.execute(select(ReportingPeriod.id).where(ReportingPeriod.id == doc.period_id).with_for_update()).scalar_one()
    return doc


def rows(db, doc):
    year = db.get(ReportingPeriod, doc.period_id).year
    return list(db.scalars(select(SunumHighlight).where(SunumHighlight.organization_id == doc.organization_id,
        SunumHighlight.year == year).order_by(SunumHighlight.sort_order, SunumHighlight.id)))


def current_facts(db, user, doc):
    payload = reports.report_data(db, user, doc.id, use_freeze=False)
    from .ar_unit_workflow_service import approved_sources
    # The current İdare report aggregates the latest approved units. Ignore a
    # historical İdare freeze here, but never offer unfinished unit draft facts.
    sources = [snapshot for _, snapshot in approved_sources(db, doc)[0]]
    return facts(payload, sources)


def save(db, doc, user, form, catalogue, row=None):
    kind = str(form.get('kind', ''))
    if kind not in {'spot', 'feature'} or (row and row.kind != kind):
        reports.fail('Öne çıkan türü geçersiz. Spot veya müdürlük işi seçin.')
    label = str(form.get('label', '')).strip()
    sentence = str(form.get('sentence', '')).strip()
    context = str(form.get('context', '')).strip()
    if any(c.isdigit() for c in label + sentence):
        reports.fail(DIGIT_ERROR)
    if not sentence or len(sentence) > 180 or len(label) > 40 or len(context) > 80:
        reports.fail('Öne çıkan kaydedilemedi. Cümleyi en fazla 180, rakam altı yazısını 40, bağlamı 80 karakterle yazın; cümle zorunludur.')
    fact = next((f for f in catalogue if f['key'] == form.get('fact_key')), None)
    if fact is None:
        reports.fail(MISSING)
    dep = fact['department_id']
    if kind == 'feature' and (dep is None or str(dep) != str(form.get('department_id'))):
        reports.fail('Öne çıkan iş için aynı müdürlüğün rakamını seçin.')
    if dep is not None and dep not in {d.id for d in photos.departments(db, doc)}:
        reports.fail('Müdürlük bu rapor yılı kapsamında değil. Listeden bir müdürlük seçin.')
    existing = [r for r in rows(db, doc) if row is None or r.id != row.id]
    selected = form.get('selected') == 'on'
    if selected and kind == 'spot' and sum(r.kind == 'spot' and r.selected for r in existing) >= 5:
        reports.fail('Sunumda en fazla 5 spot gösterilebilir. Başka bir spotun seçimini kaldırın.')
    if kind == 'feature' and any(r.kind == 'feature' and r.department_id == dep for r in existing):
        reports.fail('Bu müdürlük için bu yılda yalnız bir öne çıkan iş olabilir. Mevcut işi düzenleyin.')
    photo_id = None
    if form.get('photo_id'):
        try:
            photo_id = int(form['photo_id'])
        except (TypeError, ValueError):
            reports.fail('Fotoğraf seçimi geçersiz. Listeden bir fotoğraf seçin.')
        photo = photos.photo(db, doc, photo_id)
        if kind != 'feature' or photo.kind != 'single' or photo.department_id != dep or photo.year != db.get(ReportingPeriod, doc.period_id).year:
            reports.fail('Öne çıkan işin fotoğrafı aynı müdürlük ve yıldan tek fotoğraf olmalıdır. Fotoğraf seçimini düzeltin.')
    if row is None:
        row = SunumHighlight(organization_id=doc.organization_id, period_id=doc.period_id,
            year=db.get(ReportingPeriod, doc.period_id).year, created_by=user.id,
            sort_order=max((r.sort_order for r in existing), default=-1) + 1)
        db.add(row)
    row.kind, row.department_id, row.fact_key = kind, dep, fact['key']
    row.label, row.sentence, row.context = label or None, sentence, context or None
    row.photo_id, row.selected = photo_id, selected
    db.flush()
    return row


def change(db, doc, highlight_id, action, form):
    items = rows(db, doc)
    row = next((r for r in items if r.id == highlight_id), None)
    if row is None:
        reports.fail('Öne çıkan bu rapor yılında bulunamadı. Listeyi yenileyin.', 404)
    if action == 'delete':
        if form.get('value') != 'yes':
            reports.fail('Öne çıkan silinmedi. Silme onayını işaretleyin.')
        db.delete(row)
    elif action == 'order':
        value = form.get('value')
        if value not in {'up', 'down'}:
            reports.fail('Öne çıkan sırası değiştirilemedi. Yukarı veya aşağı düğmesini kullanın.')
        items = [r for r in items if r.kind == row.kind]
        index = items.index(row)
        other = index + (-1 if value == 'up' else 1)
        if 0 <= other < len(items):
            items[index], items[other] = items[other], items[index]
        for i, item in enumerate(items):
            item.sort_order = i
    else:
        reports.fail('Öne çıkan işlemi bulunamadı. Listedeki düğmeleri kullanın.', 404)
    db.flush()


def deck_items(db, doc):
    import base64
    names = {d.id: d.name for d in db.scalars(select(Department).where(Department.organization_id == doc.organization_id))}
    result = []
    for row in rows(db, doc):
        if not row.selected:
            continue
        image = None
        if row.photo_id:
            photo = photos.photo(db, doc, row.photo_id)
            if photo.kind == 'single' and photo.department_id == row.department_id and photo.year == row.year:
                image = 'data:image/webp;base64,' + base64.b64encode(photo.webp_data).decode('ascii')
        result.append(dict(id=row.id, kind=row.kind, fact_key=row.fact_key, department_id=row.department_id,
            department=names.get(row.department_id), label=row.label, sentence=row.sentence, context=row.context,
            sort_order=row.sort_order, image=image))
    return result


def register(app):
    from .main import require_strategy, require_user, templates
    from .activity_sections_routes import TurkishValidationRoute, transact
    router = APIRouter(route_class=TurkishValidationRoute)
    prefix = '/activity-sections/reports/{document_id}/highlights'

    def access(user=Depends(require_user)):
        if user.role not in EDIT_ROLES:
            require_strategy(user)
        return user

    def page(request, db, user, doc, *, error=None, status=200, form=None):
        catalogue = current_facts(db, user, doc)
        items = rows(db, doc)
        return templates.TemplateResponse(request, 'sunum_highlights.html', dict(user=user, doc=doc,
            period=db.get(ReportingPeriod, doc.period_id), departments=photos.departments(db, doc),
            photos=[p for p in photos.list_photos(db, doc) if p.kind == 'single'], catalogue=catalogue,
            fact_map={f['key']: f for f in catalogue}, highlights=items,
            selected_count=sum(r.kind == 'spot' and r.selected for r in items), error=error,
            form=form or {}, missing_message=MISSING), status_code=status)

    @router.get(prefix)
    def listing(document_id: int, request: Request, db: Session = Depends(get_db), user=Depends(access)):
        return page(request, db, user, scope(db, user, document_id))

    @router.post(prefix)
    async def create(document_id: int, request: Request, db: Session = Depends(get_db), user=Depends(access)):
        doc = scope(db, user, document_id)
        form = await request.form()
        try:
            def operation():
                locked = scope(db, user, document_id, lock=True)
                save(db, locked, user, form, current_facts(db, user, locked))
            transact(db, operation)
            return RedirectResponse(request.url.path, 303)
        except HTTPException as error:
            db.rollback()
            return page(request, db, user, doc, error=error.detail, status=error.status_code, form=form)

    @router.post(prefix + '/{highlight_id}/{action}')
    async def update(document_id: int, highlight_id: int, action: str, request: Request,
                     db: Session = Depends(get_db), user=Depends(access)):
        doc = scope(db, user, document_id)
        form = await request.form()
        try:
            def operation():
                locked = scope(db, user, document_id, lock=True)
                if action == 'edit':
                    row = next((r for r in rows(db, locked) if r.id == highlight_id), None)
                    if row is None:
                        reports.fail('Öne çıkan bulunamadı. Listeyi yenileyin.', 404)
                    save(db, locked, user, form, current_facts(db, user, locked), row)
                else:
                    change(db, locked, highlight_id, action, form)
            transact(db, operation)
            return RedirectResponse(f'/activity-sections/reports/{doc.id}/highlights', 303)
        except HTTPException as error:
            db.rollback()
            return page(request, db, user, doc, error=error.detail, status=error.status_code)
    app.include_router(router)
