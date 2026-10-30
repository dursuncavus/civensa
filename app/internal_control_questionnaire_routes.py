"""CIV-085 screens registered by the monitoring router."""
import base64
import json
from io import BytesIO
from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from itsdangerous import URLSafeTimedSerializer, BadSignature
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .db import get_db
from .config import session_secret
from .models import Department
from . import internal_control_monitoring_service as m
from . import internal_control_questionnaire_service as q
from .pp_errors import payload


def context():
    return dict(states=m.STATES, answer_labels=q.ANSWERS, components=q.COMPONENTS,
                period_label=m.period_label, tsi=m.tsi)


def batch_context(db, user, batch_id):
    user, period, batch, status, revision = q.get_batch(db, user, batch_id)
    rows = q.rows(db, batch)
    return dict(batch=batch, status=status, revision=revision, rows=rows,
        list_id=q.attachment(db, period.id).list_id,
        answered=sum(r['answer'] is not None for r in rows),
        editable=user.role == 'department' and not period.closed_at and m.today(db) <= period.deadline and status in ('draft', 'returned'),
        events=db.scalars(select(q.Event).where(q.Event.batch_id == batch.id).order_by(q.Event.revision)).all())


def overview_context(db, user, period):
    m.require_access(db, user, strategy=True)
    attached = q.attachment(db, period.id)
    return dict(question_attachment=attached,
        question_lists=db.scalars(select(q.QuestionList).order_by(q.QuestionList.id.desc())).all(),
        question_departments=db.scalars(select(Department).where(Department.is_active.is_(True) |
            Department.id.in_(json.loads(attached.departments_json) if attached else [])).order_by(Department.name)).all(),
        question_selected=json.loads(attached.departments_json) if attached else None,
        question_details=[batch_context(db, user, b.id) for b in q.batches(db, period.id)],
        question_results=q.results(db, user, period), **context())


def detail_screen(request, db, user, batch_id):
    from .main import templates
    user, period, batch, status, revision = q.get_batch(db, user, batch_id)
    return templates.TemplateResponse(request, 'internal_control/questionnaire_detail.html', dict(
        user=user, monitoring_period=period, detail=batch_context(db, user, batch_id), **context()))


def upload_screen(request, db, user, **extra):
    from .main import templates
    user = m.require_access(db, user, strategy=True)
    saved = db.scalars(select(q.QuestionList).order_by(q.QuestionList.id.desc())).all()
    return templates.TemplateResponse(request, 'internal_control/questionnaire_upload.html', dict(user=user,
        saved_questions={item.id: json.loads(item.questions_json) for item in saved},
        lists=saved, **context(), **extra))


def signer():
    return URLSafeTimedSerializer(session_secret(), salt='civ085-question-preview')


def register(app):
    from .main import require_user
    from .internal_control_monitoring_routes import overview_screen
    from .internal_control_questionnaire_export import questionnaire_export

    @app.get('/internal-control/questionnaires')
    def upload(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        return upload_screen(request, db, user)

    @app.get('/internal-control/questionnaires/template.xlsx')
    def template(db: Session = Depends(get_db), user=Depends(require_user)):
        m.require_access(db, user, strategy=True)
        return StreamingResponse(BytesIO(q.template()), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename="ic-soru-sablonu.xlsx"'})

    @app.post('/internal-control/questionnaires/preview')
    async def preview(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        user = m.require_access(db, user, strategy=True)
        data = await request.form()
        file = data.get('file')
        content = await file.read(5 * 1024 * 1024 + 1) if hasattr(file, 'read') else b''
        name = str(data.get('name', '')).strip()
        try:
            if not 1 <= len(name) <= 200:
                m.fail('Soru listesi adı boş veya uzun. 1–200 karakterlik ad girin.', 'name')
            parsed = q.parse_questions(content)
        except HTTPException as exc:
            response = upload_screen(request, db, user, errors=payload(exc)['errors'], attempted_name=name)
            response.status_code = 422
            return response
        token = signer().dumps(dict(actor_id=user.id, name=name, content=base64.b64encode(content).decode('ascii')))
        return upload_screen(request, db, user, preview=parsed, preview_token=token, attempted_name=name)

    @app.post('/internal-control/questionnaires/save')
    async def save_list(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        m.require_access(db, user, strategy=True)
        data = await request.form()
        try:
            staged = signer().loads(str(data.get('preview_token', '')), max_age=3600)
            if staged['actor_id'] != user.id:
                raise BadSignature('actor')
        except (BadSignature, KeyError, ValueError):
            m.fail('Soru önizlemesi geçersiz veya süresi dolmuş. Dosyayı yeniden yükleyip inceleyin.', 'preview_token')
        q.save_list(db, user, staged['name'], base64.b64decode(staged['content']))
        db.commit()
        return RedirectResponse('/internal-control/questionnaires', 303)

    async def mutate(request, db, operation, screen, destination):
        data = await request.form()
        try:
            operation(data)
            db.commit()
        except HTTPException as exc:
            db.rollback()
            if exc.status_code != 422:
                raise
            request.state.pp_attempt = (request.url.path, data, payload(exc))
            response = screen()
            response.status_code = 422
            return response
        except IntegrityError:
            db.rollback()
            m.conflict()
        return RedirectResponse(destination, 303)

    @app.post('/internal-control/monitoring/periods/{period_id}/questionnaire')
    async def attach(period_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        period_id = m.number(period_id, 'period_id')
        return await mutate(request, db, lambda d: q.attach(db, user, period_id,
            m.number(d.get('list_id', ''), 'list_id'), d.getlist('department_ids'), d.get('expected_revision', '')),
            lambda: overview_screen(request, db, user, period_id), f'/internal-control/monitoring?period_id={period_id}#soru-formu')

    @app.get('/internal-control/questionnaires/batches/{batch_id}')
    def detail(batch_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        return detail_screen(request, db, user, m.number(batch_id, 'batch_id'))

    @app.post('/internal-control/questionnaires/batches/{batch_id}/answers')
    async def answers(batch_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        batch_id = m.number(batch_id, 'batch_id')
        return await mutate(request, db, lambda d: q.save_answers(db, user, batch_id,
            d.get('expected_revision', ''), d, submit=d.get('operation') == 'submit', expected_list_id=d.get('list_id', '')),
            lambda: detail_screen(request, db, user, batch_id), f'/internal-control/questionnaires/batches/{batch_id}')

    @app.post('/internal-control/questionnaires/batches/{batch_id}/transition')
    async def transition(batch_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        batch_id = m.number(batch_id, 'batch_id')
        return await mutate(request, db, lambda d: q.transition(db, user, batch_id,
            d.get('action', ''), d.get('expected_revision', ''), d.get('reason', '')),
            lambda: detail_screen(request, db, user, batch_id), f'/internal-control/questionnaires/batches/{batch_id}')

    @app.get('/internal-control/monitoring/periods/{period_id}/questionnaire.xlsx')
    def export(period_id: str, draft: str = 'false', db: Session = Depends(get_db), user=Depends(require_user)):
        if draft.lower() not in {'true', 'false', '1', '0'}:
            m.fail('Taslak seçimi geçersiz. Ekrandaki indirme bağlantısını kullanın.', 'draft')
        is_draft = draft.lower() in {'true', '1'}
        content = questionnaire_export(db, user, m.number(period_id, 'period_id'), draft=is_draft)
        return StreamingResponse(BytesIO(content), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename="' + ('TASLAK-' if is_draft else '') + 'ic-soru-sonuclari.xlsx"'})
