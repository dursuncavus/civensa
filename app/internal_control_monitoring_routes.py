"""CIV-079 Turkish monitoring screens; registered through existing IC routes."""
from io import BytesIO
from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .db import get_db
from .models import Department
from .internal_control_models import ICPlan, ICAction
from .internal_control_monitoring_models import ICMonitoringPeriod as Period, ICMonitoringBatch as Batch, ICMonitoringEvent as Event, ICMonitoringPeriodEvent as PeriodEvent
from . import internal_control_monitoring_service as m
from . import internal_control_monitoring_export as export
from .pp_errors import payload


def context():
    return dict(states=m.STATES, statuses=m.STATUSES, period_label=m.period_label, tsi=m.tsi)


def periods(db):
    return db.scalars(select(Period).order_by(Period.year.desc(), Period.half.desc(), Period.id.desc())).all()


def our_screen(request, db, user, period_id=None):
    from .main import templates
    user = m.require_access(db, user)
    if user.role != 'department':
        return RedirectResponse('/internal-control/monitoring', 303)
    available = periods(db)
    active_plan_id = db.scalar(select(ICPlan.id).where(ICPlan.status == 'active'))
    active_periods = [p for p in available if p.plan_id == active_plan_id]
    default_periods = active_periods or available
    period = m.get_period(db, user, m.number(period_id, 'period_id')) if period_id else next(
        (p for p in default_periods if not p.closed_at), default_periods[0] if default_periods else None)
    batches = db.scalars(select(Batch).where(Batch.period_id == period.id,
        Batch.department_id == user.department_id)).all() if period else []
    notes = m.visible_notes(db, user, period) if period else []
    details = [batch_context(db, user, b.id) for b in batches]
    return templates.TemplateResponse(request, 'internal_control/monitoring_ours.html', dict(
        user=user, monitoring_period=period, periods=available, details=details, notes=notes, note_codes={n.action_id: db.get(ICAction, n.action_id).action_code_raw for n in notes},
        note_editable=bool(period and not period.closed_at and m.today(db) <= period.deadline),
        cooperating=m.cooperating_actions(db, user, period) if period else [], **context()))


def batch_context(db, user, batch_id):
    user, period, batch, status, revision = m.get_batch(db, user, batch_id)
    return dict(batch=batch, rows=m.rows(db, batch), status=status, revision=revision,
        submission_open=m.today(db) <= period.deadline,
        editable=not period.closed_at and m.today(db) <= period.deadline and status in ('draft', 'returned') and (
            user.role == 'department' and batch.department_id == user.department_id or user.role == 'strategy' and batch.body_name is not None),
        events=db.scalars(select(Event).where(Event.batch_id == batch.id).order_by(Event.revision)).all())


def overview_screen(request, db, user, period_id=None):
    from .main import templates
    user = m.require_access(db, user, strategy=True)
    available = periods(db)
    period = m.get_period(db, user, m.number(period_id, 'period_id')) if period_id else (available[0] if available else None)
    details, counts = m.overview(db, user, period) if period else ([], {})
    return templates.TemplateResponse(request, 'internal_control/monitoring.html', dict(user=user,
        monitoring_period=period, periods=available, details=details, counts=counts,
        official_metrics=m.official_metrics(db, user, period) if period else None,
        unassigned=db.scalars(select(Department).where(Department.is_active.is_(True),
            Department.id.not_in([d['batch'].department_id for d in details if d['batch'].department_id])).order_by(Department.name)).all() if period else [],
        plans=db.scalars(select(ICPlan).where(ICPlan.status == 'active')).all(),
        period_events=db.scalars(select(PeriodEvent).where(PeriodEvent.period_id == period.id).order_by(PeriodEvent.id)).all() if period else [], **context()))


def detail_screen(request, db, user, batch_id):
    from .main import templates
    user, period, batch, status, revision = m.get_batch(db, user, batch_id)
    action_ids = {r['action'].id for r in m.rows(db, batch)}
    notes = [n for n in m.visible_notes(db, user, period) if n.action_id in action_ids]
    return templates.TemplateResponse(request, 'internal_control/monitoring_detail.html', dict(
        user=user, monitoring_period=period, detail=batch_context(db, user, batch_id),
        notes=notes, note_codes={n.action_id: db.get(ICAction, n.action_id).action_code_raw for n in notes}, **context()))


def register(app):
    from .main import require_user

    async def mutate(request, db, user, operation, screen, destination):
        data = await request.form()
        try:
            result = operation(data)
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
        return RedirectResponse(destination(result), 303)

    @app.get('/internal-control/monitoring')
    def overview(request: Request, period_id: str = '', db: Session = Depends(get_db), user=Depends(require_user)):
        return overview_screen(request, db, user, period_id)

    @app.post('/internal-control/monitoring/open')
    async def open_period(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        return await mutate(request, db, user,
            lambda d: m.open_period(db, user, m.number(d.get('plan_id', ''), 'plan_id'), d.get('year', ''), d.get('half', ''), d.get('deadline', '')),
            lambda: overview_screen(request, db, user), lambda p: f'/internal-control/monitoring?period_id={p.id}')

    @app.post('/internal-control/monitoring/periods/{period_id}/close')
    async def close_period(period_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        period_id = m.number(period_id, 'period_id')
        return await mutate(request, db, user,
            lambda d: m.close_period(db, user, period_id, d.get('expected_revision', ''), d.get('reason', '')),
            lambda: overview_screen(request, db, user, period_id), lambda _: f'/internal-control/monitoring?period_id={period_id}')

    @app.get('/internal-control/monitoring/batches/{batch_id}')
    def detail(batch_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        batch_id = m.number(batch_id, 'batch_id')
        return detail_screen(request, db, user, batch_id)

    @app.post('/internal-control/monitoring/batches/{batch_id}/entry')
    async def save(batch_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        batch_id = m.number(batch_id, 'batch_id')
        return await mutate(request, db, user, lambda d: m.save_entry(db, user, batch_id,
            m.number(d.get('id', ''), 'id'), d.get('expected_revision', ''), d),
            lambda: detail_screen(request, db, user, batch_id), lambda _: f'/internal-control/monitoring/batches/{batch_id}')

    @app.post('/internal-control/monitoring/batches/{batch_id}/transition')
    async def transition(batch_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        batch_id = m.number(batch_id, 'batch_id')
        return await mutate(request, db, user, lambda d: m.transition(db, user, batch_id,
            d.get('action', ''), d.get('expected_revision', ''), d.get('reason', '')),
            lambda: detail_screen(request, db, user, batch_id), lambda _: f'/internal-control/monitoring/batches/{batch_id}')

    @app.post('/internal-control/monitoring/periods/{period_id}/notes')
    async def note(period_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        period_id = m.number(period_id, 'period_id')
        return await mutate(request, db, user, lambda d: m.add_note(db, user, period_id,
            m.number(d.get('id', ''), 'id'), d.get('content', '')),
            lambda: our_screen(request, db, user, period_id), lambda _: f'/internal-control/our-actions?period_id={period_id}')

    @app.get('/internal-control/monitoring/periods/{period_id}/official-report.{format}')
    @app.get('/internal-control/monitoring/periods/{period_id}/report.{format}')
    def report(request: Request, period_id: str, format: str, draft: str = 'false', db: Session = Depends(get_db), user=Depends(require_user)):
        period_id = m.number(period_id, 'period_id')
        if draft.lower() not in {'true', 'false', '1', '0'}:
            m.fail('Taslak seçimi geçersiz. Ekrandaki TASLAK veya onaylı rapor bağlantısını kullanın.', 'draft')
        draft = draft.lower() in {'true', '1'}
        official = '/official-report.' in request.url.path
        render = export.official_export if official else export.period_export
        data = render(db, user, period_id, format, draft=draft)
        prefix = ('TASLAK-' if draft else '') + ('resmi-' if official else '')
        media = 'application/vnd.openxmlformats-officedocument.' + ('wordprocessingml.document' if format == 'docx' else 'spreadsheetml.sheet')
        return StreamingResponse(BytesIO(data), media_type=media,
            headers={'Content-Disposition': f'attachment; filename="{prefix}ic-izleme-{period_id}.{format}"'})

    @app.get('/internal-control/monitoring/plans/{plan_id}/annual.xlsx')
    def annual(plan_id: str, year: str = '', db: Session = Depends(get_db), user=Depends(require_user)):
        plan_id = m.number(plan_id, 'plan_id')
        data = export.annual_export(db, user, plan_id, year)
        return StreamingResponse(BytesIO(data), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename="ic-yillik.xlsx"'})
