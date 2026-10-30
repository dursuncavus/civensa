"""CIV-048 Turkish catalogue, import checklist and directorate read views."""
from collections import defaultdict
from io import BytesIO
import json

from fastapi import Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .file_security import read_upload_limited
from .internal_control_models import (COMPONENTS, STANDARD_COMPONENTS, ICPlan, ICCondition,
                                      ICAction, ICActionParty, ICImport)
from .models import Department, User
from . import internal_control_service as service

XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
STATUS_LABELS = {'draft': 'Taslak', 'active': 'Etkin', 'archived': 'Arşiv'}


def download(data, filename):
    return StreamingResponse(BytesIO(data), media_type=XLSX,
                             headers={'Content-Disposition': f'attachment; filename="{filename}"'})


def get_import(db, batch_id):
    batch = db.get(ICImport, batch_id)
    if not batch:
        raise HTTPException(404, 'Yükleme bulunamadı. Dosyayı yeniden yükleyin.')
    return batch


def commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'İşlem başka bir kullanıcı tarafından değiştirildi. Listeyi yenileyip yeniden deneyin.') from None


def catalogue(db, plan, *, component='', standard='', department_id=None, q=''):
    conditions = db.scalars(select(ICCondition).where(ICCondition.plan_id == plan.id)
                           .order_by(ICCondition.sort_order)).all()
    actions = db.scalars(select(ICAction).where(ICAction.plan_id == plan.id).order_by(ICAction.sort_order)).all()
    parties = db.scalars(select(ICActionParty).join(ICAction).where(ICAction.plan_id == plan.id)
                         .order_by(ICActionParty.sort_order)).all()
    departments = {d.id: d for d in db.scalars(select(Department).order_by(Department.name))}
    by_action, by_condition = defaultdict(list), defaultdict(list)
    for party in parties:
        label = 'Tüm Müdürlükler' if party.all_departments else (departments[party.department_id].name if party.department_id else party.body_name)
        by_action[party.action_id].append({'role': party.role, 'label': label})
    responsible = defaultdict(set)
    for party in parties:
        if party.role == 'responsible':
            for did in (list(departments) if party.all_departments else [party.department_id]):
                if did:
                    responsible[did].add(party.action_id)
    counts = {c: {'conditions': 0, 'actions': 0, 'departments': defaultdict(set)} for c in COMPONENTS}
    condition_index = {c.id: c for c in conditions}
    for condition in conditions:
        counts[STANDARD_COMPONENTS[condition.standard_code]]['conditions'] += 1
    for action in actions:
        c = STANDARD_COMPONENTS[condition_index[action.condition_id].standard_code]
        counts[c]['actions'] += 1
        for did, ids in responsible.items():
            if action.id in ids:
                counts[c]['departments'][departments[did].name].add(action.id)
        by_condition[action.condition_id].append(action)
    groups = {}
    key = service.department_key(q)
    for condition in conditions:
        comp = STANDARD_COMPONENTS[condition.standard_code]
        if component and component != comp or standard and standard != condition.standard_code:
            continue
        candidates = by_condition[condition.id]
        if department_id:
            candidates = [a for a in candidates if a.id in responsible[department_id]]
            if not candidates:
                continue
        if key:
            context = service.department_key(' '.join([condition.condition_code, condition.text, condition.current_state_text, condition.standard_title]))
            if key not in context:
                candidates = [a for a in candidates if key in service.department_key(' '.join(
                    [a.action_code, a.text, a.output_text, a.note] + [p['label'] for p in by_action[a.id]]))]
                if not candidates:
                    continue
        group = groups.setdefault(comp, {}).setdefault(condition.standard_code,
                    {'title': condition.standard_title, 'conditions': []})
        group['conditions'].append({'condition': condition, 'actions': candidates})
    return dict(groups=groups, counts=counts, parties=by_action, departments=list(departments.values()))


def register(app):
    from .main import require_user, templates

    def strategy(db: Session = Depends(get_db), user=Depends(require_user)):
        return service.require_access(db, user, strategy=True)

    @app.get('/internal-control')
    def index(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        service.require_access(db, user)
        if user.role == 'department':
            return RedirectResponse('/internal-control/our-actions', 303)
        plans = db.scalars(select(ICPlan).order_by(ICPlan.id.desc())).all()
        return templates.TemplateResponse(request, 'internal_control/index.html',
            dict(user=user, plans=plans, status_labels=STATUS_LABELS))

    @app.get('/internal-control/template.xlsx')
    def template(user=Depends(strategy)):
        return download(service.template_bytes(), 'ic-plan-sablonu.xlsx')

    @app.post('/internal-control/imports')
    async def upload(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(strategy)):
        data = await read_upload_limited(file, service.MAX_UPLOAD, 'İç Kontrol plan dosyası')
        batch, _ = service.create_import(db, user, data, file.filename or '')
        commit(db)
        return RedirectResponse(f'/internal-control/imports/{batch.id}', 303)

    @app.get('/internal-control/imports/{batch_id}')
    def preview(batch_id: int, request: Request, db: Session = Depends(get_db), user=Depends(strategy)):
        batch = get_import(db, batch_id)
        report = service.validate_source(db, json.loads(batch.source_json))
        return templates.TemplateResponse(request, 'internal_control/import.html', dict(user=user, batch=batch,
            report=report, departments=db.scalars(select(Department).order_by(Department.name)).all(),
            plans=db.scalars(select(ICPlan).where(ICPlan.status != 'archived').order_by(ICPlan.id.desc())).all(),
            committed_plan=db.scalar(select(ICPlan).where(ICPlan.import_id == batch.id))))

    @app.get('/internal-control/imports/{batch_id}/validation.xlsx')
    def validation(batch_id: int, db: Session = Depends(get_db), user=Depends(strategy)):
        report = service.validate_source(db, json.loads(get_import(db, batch_id).source_json))
        return download(service.validation_bytes(report), 'ic-plan-dogrulama.xlsx')

    @app.post('/internal-control/imports/{batch_id}/validate')
    def revalidate(batch_id: int, db: Session = Depends(get_db), user=Depends(strategy)):
        service.dry_run(db, user, get_import(db, batch_id))
        commit(db)
        return RedirectResponse(f'/internal-control/imports/{batch_id}', 303)

    @app.post('/internal-control/imports/{batch_id}/mappings')
    def mapping(batch_id: int, raw_name: str = Form(...), department_id: str = Form(''), body_name: str = Form(''),
                db: Session = Depends(get_db), user=Depends(strategy)):
        if department_id and not department_id.isdecimal():
            raise HTTPException(422, 'Müdürlük seçimi geçersiz. Listeden bir müdürlük seçin.')
        try:
            service.map_unit(db, user, get_import(db, batch_id), raw_name, int(department_id) if department_id else None, body_name)
            service.dry_run(db, user, get_import(db, batch_id))
            commit(db)
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Birim başka bir kullanıcı tarafından eşleştirildi. Doğrulama listesini yenileyin.') from None
        return RedirectResponse(f'/internal-control/imports/{batch_id}', 303)

    @app.post('/internal-control/imports/{batch_id}/commit')
    def save(batch_id: int, supersedes_id: str = Form(''), db: Session = Depends(get_db), user=Depends(strategy)):
        if supersedes_id and not supersedes_id.isdecimal():
            raise HTTPException(422, 'Önceki plan seçimi geçersiz. Planı listeden seçin.')
        try:
            plan = service.commit_import(db, user, batch_id, supersedes_id=int(supersedes_id) if supersedes_id else None)
            commit(db)
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Plan eşzamanlı olarak kaydedildi veya değişti. Plan listesini yenileyin.') from None
        return RedirectResponse(f'/internal-control/plans/{plan.id}', 303)

    @app.post('/internal-control/plans/{plan_id}/activate')
    def activate(plan_id: int, db: Session = Depends(get_db), user=Depends(strategy)):
        try:
            service.activate_plan(db, user, plan_id)
            commit(db)
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Etkin plan değişti. Plan listesini yenileyip yeniden deneyin.') from None
        return RedirectResponse(f'/internal-control/plans/{plan_id}', 303)

    @app.get('/internal-control/plans/{plan_id}')
    def view(plan_id: int, request: Request, component: str = '', standard: str = '', department_id: str = '',
             q: str = '', db: Session = Depends(get_db), user=Depends(strategy)):
        if department_id and not department_id.isdecimal():
            raise HTTPException(422, 'Müdürlük seçimi geçersiz. Listeden seçin.')
        department_id = int(department_id) if department_id else None
        plan = db.get(ICPlan, plan_id)
        if not plan:
            raise HTTPException(404, 'Plan bulunamadı. Plan listesini yenileyin.')
        return templates.TemplateResponse(request, 'internal_control/plan.html', dict(user=user, plan=plan,
            components=COMPONENTS, standards=STANDARD_COMPONENTS, status_labels=STATUS_LABELS,
            creator=db.get(User, plan.created_by),
            component=component, standard=standard, department_id=department_id, q=q,
            **catalogue(db, plan, component=component, standard=standard, department_id=department_id, q=q)))

    @app.get('/internal-control/our-actions')
    def ours(request: Request, period_id: str = '', db: Session = Depends(get_db), user=Depends(require_user)):
        from .internal_control_monitoring_routes import our_screen
        from .internal_control_monitoring_models import ICMonitoringPeriod
        if period_id or db.scalar(select(ICMonitoringPeriod.id).join(ICPlan).where(ICPlan.status == 'active').limit(1)):
            return our_screen(request, db, user, period_id)
        responsible = service.directorate_actions(db, user, 'responsible')
        cooperating = service.directorate_actions(db, user, 'cooperating')
        plan = db.scalar(select(ICPlan).where(ICPlan.status == 'active'))
        return templates.TemplateResponse(request, 'internal_control/our_actions.html',
            dict(user=user, plan=plan, responsible=responsible, cooperating=cooperating,
                 last_monitoring_period_id=db.scalar(select(ICMonitoringPeriod.id).order_by(ICMonitoringPeriod.id.desc()).limit(1))))

    from .internal_control_monitoring_routes import register as register_monitoring
    register_monitoring(app)
