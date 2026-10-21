"""CIV-072: reopen an approved PP package for the ordinary correction cycle."""
from datetime import datetime, UTC
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .main import current_user, pp_period, require_pp_period, require_strategy, session_period
from .models import (AuditLog, Department, Notification, ReportingPeriod, Submission,
                     SubmissionEvent, User)
from .pp_errors import pp_error, recover_form
from .pp_display import EVENT_LABELS, STATUS_LABELS
from .program_service import department_snapshot
from .released_permissions import require_strategy_director
from .serialization import json_dumps
from .structure_service import period_name


def require_active_reopen_session(request: Request, db: Session = Depends(get_db)):
    # Give an authenticated but deactivated account the same forbidden response
    # as other ineligible actors; normal authentication/CSRF still run below.
    user = current_user(request, db)
    if user and not user.is_active:
        raise pp_error(403, "Etkin olmayan hesap paketi düzeltme için açamaz. Strateji Geliştirme Müdürüne başvurun.")


# Register the new event with both existing PP history renderers.
EVENT_LABELS['reopen'] = STATUS_LABELS['reopen'] = 'Düzeltme için açıldı'

router = APIRouter(dependencies=[Depends(require_active_reopen_session), Depends(require_pp_period)])


def check_reopen(db, user, sub):
    user = db.get(User, user.id, populate_existing=True)
    if not user:
        raise pp_error(403)
    require_strategy_director(user)
    actor_department = db.get(Department, user.department_id, populate_existing=True)
    department = db.get(Department, sub.department_id, populate_existing=True)
    if (not actor_department or not actor_department.is_active or not department
            or actor_department.organization_id != department.organization_id):
        raise pp_error(403, "Bu kurumun paketini düzeltme için açamazsınız. Kendi kurumunuzun yetkili hesabıyla giriş yapın.", "department_id")
    period = db.get(ReportingPeriod, sub.period_id, populate_existing=True)
    if period.status == 'closed':
        raise pp_error(409, f"{period.year} yılı dönemi kapalı; paket düzeltme için açılamaz. Strateji Geliştirme birimine başvurun.", "period_id")
    if sub.status != 'approved':
        raise pp_error(409, "Yalnızca onaylanmış paket düzeltme için açılabilir.", "submission_id")
    return user, department


@router.post('/api/submissions/{submission_id}/reopen')
async def reopen_submission(submission_id: int, request: Request,
                            db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    # Consume the body before acquiring any locks; never await with a row locked.
    try:
        data = await request.json()
    except ValueError:
        data = None
    return reopen_package(submission_id, request, db, user, data)


def reopen_package(submission_id, request, db, user, data):
    if not hasattr(data, 'get') or not isinstance(data.get('reason'), str) or not data['reason'].strip():
        raise pp_error(422, "Gerekçe zorunlu. Düzeltilecek noktaları gerekçe alanına yazın.", "reason")
    reason = data['reason'].strip()
    scope = db.get(Submission, submission_id, populate_existing=True)
    if not scope:
        raise pp_error(404, "İnceleme paketi bulunamadı. İnceleme kuyruğunu yenileyip kaydı yeniden seçin.", "submission_id")
    pp_period(request, db, user, scope.department_id, data, scope.period_id)
    check_reopen(db, user, scope)
    # Match decision/edit/submit lock order and recheck everything after waiting.
    db.scalar(select(Department).where(Department.id == scope.department_id).with_for_update())
    sub = db.scalar(select(Submission).where(Submission.id == submission_id)
                    .with_for_update().execution_options(populate_existing=True))
    if not sub:
        raise pp_error(404, "İnceleme paketi bulunamadı. İnceleme kuyruğunu yenileyin.", "submission_id")
    user, department = check_reopen(db, user, sub)
    snapshot = json_dumps(department_snapshot(db, sub.period_id, sub.department_id), ensure_ascii=False)
    sub.status = 'returned'
    sub.return_note = reason
    sub.reviewed_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(SubmissionEvent(submission_id=sub.id, department_id=sub.department_id,
        period_id=sub.period_id, actor_user_id=user.id, event_type='reopen',
        revision=sub.revision or 1, note=reason, snapshot_json=snapshot))
    db.add(Notification(role='department', department_id=sub.department_id,
        event_type='submission_reopen',
        message=f"{period_name(db, sub.period_id, department)} revizyon {sub.revision or 1} düzeltme için açıldı. Gerekçe: {reason}",
        link=f"/department/{sub.department_id}?period_id={sub.period_id}"))
    db.add(AuditLog(user_id=user.id, action='submission_reopen', entity_type='submission',
        entity_id=sub.id, details=json_dumps({'revision': sub.revision or 1, 'reason': reason}, ensure_ascii=False)))
    db.commit()
    return {'ok': True, 'status': 'returned'}


def reopen_screen(request, db, user, department_id, data):
    from .main import review
    period = session_period(request, db, data)
    display_request = Request({**request.scope, 'query_string': urlencode({'period_id': period.id}).encode()})
    return review(display_request, db, user)


@router.post('/review/submissions/{submission_id}/reopen')
@recover_form(reopen_screen)
async def reopen_form(submission_id: int, request: Request,
                      db: Session = Depends(get_db), user: User = Depends(require_strategy)):
    data = await request.form()  # All body reads precede the shared lock path.
    period = session_period(request, db, data, require=True)
    reopen_package(submission_id, request, db, user, data)
    return RedirectResponse('/review?' + urlencode({'period_id': period.id}), 303)
