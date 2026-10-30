"""CIV-160 editor and decisions, restricted to Strateji on every route."""
from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .db import get_db
from . import internal_control_monitoring_service as m
from . import internal_control_narrative_service as n
from . import internal_control_questionnaire_service as q
from .pp_errors import payload


def screen(request, db, user, period_id):
    from .main import templates
    user = m.require_access(db, user, strategy=True)
    period = m.get_period(db, user, period_id)
    status, revision = n.state(db, period.id)
    return templates.TemplateResponse(request, 'internal_control/narrative_editor.html', dict(
        user=user, monitoring_period=period, status=status, revision=revision, states=m.STATES,
        fields=n.fields(db, period), values=n.content(db, period), actions=n.ACTIONS,
        editable=not period.closed_at and status in ('draft', 'returned'),
        events=db.scalars(select(n.Event).where(n.Event.period_id == period.id).order_by(n.Event.revision)).all(),
        reference=q.results(db, user, period), period_label=m.period_label, tsi=m.tsi))


def register(app):
    from .main import require_user

    @app.get('/internal-control/monitoring/narrative-editor.js')
    def editor_script(db: Session = Depends(get_db), user=Depends(require_user)):
        m.require_access(db, user, strategy=True)
        return Response(EDITOR_SCRIPT, media_type='application/javascript')

    path = '/internal-control/monitoring/periods/{period_id}/narrative'

    @app.get(path)
    def editor(period_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        m.require_access(db, user, strategy=True)
        return screen(request, db, user, m.number(period_id, 'period_id'))

    async def mutate(period_id, request, db, user, operation):
        m.require_access(db, user, strategy=True)
        period_id = m.number(period_id, 'period_id')
        data = await request.form()
        try:
            operation(period_id, data)
            db.commit()
        except HTTPException as exc:
            db.rollback()
            if exc.status_code != 422:
                raise
            request.state.pp_attempt = (request.url.path, data, payload(exc))
            response = screen(request, db, user, period_id)
            response.status_code = 422
            return response
        except IntegrityError:
            db.rollback()
            m.conflict()
        return RedirectResponse(f'/internal-control/monitoring/periods/{period_id}/narrative?saved=1', 303)

    @app.post(path + '/save')
    async def save(period_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        return await mutate(period_id, request, db, user, lambda pid, d: n.save(db, user, pid,
            d.get('expected_revision', ''), d, submit=d.get('operation') == 'submit'))

    @app.post(path + '/copy')
    async def copy(period_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        return await mutate(period_id, request, db, user, lambda pid, d: n.copy_previous(db, user, pid, d.get('expected_revision', '')))

    @app.post(path + '/transition')
    async def transition(period_id: str, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        return await mutate(period_id, request, db, user, lambda pid, d: n.transition(db, user, pid,
            d.get('action', ''), d.get('expected_revision', ''), d.get('reason', '')))


# Same-origin script preserves the application CSP without inline handlers.
EDITOR_SCRIPT = r"""(()=> {

const form = document.querySelector('[data-narrative-form]');
if (form) {
  const state = form.querySelector('[data-save-state]');
  function update(field) {
    const count = [...field.value].length;
    form.querySelector('[data-counter="' + field.name + '"]').textContent = count.toLocaleString('tr-TR') + ' / ' + Number(field.dataset.limit).toLocaleString('tr-TR') + ' karakter';
  }
  form.querySelectorAll('textarea[data-limit]').forEach(field => {
    update(field);
    field.addEventListener('input', () => { update(field); state.textContent = 'Kaydedilmemiş değişiklikler var'; });
  });
  if (form.querySelector('[aria-invalid="true"]') || form.querySelector('[role="alert"]')) state.textContent = 'Kaydedilmedi; girdiğiniz değerler korundu';
}

})();
"""
