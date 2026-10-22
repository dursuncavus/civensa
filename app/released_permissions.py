"""CIV-025 permissions for the released flow; independent of workflow flags."""
import json

from fastapi import Depends, HTTPException, Request
from sqlalchemy import event, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .models import (Activity, ActivityCatalogueLink, ActivityCostValue, ActivityResponsibility,
                     AuditLog, Department, DepartmentCostValue, DepartmentScope, Indicator,
                     IndicatorValue, OfficialActivity, Program, ReportCard, Submission,
                     SubmissionEvent, SubProgram, EconomicValue, ImportBatch, User, Organization)

DIRECTOR_ERROR = ("Bu müdürlükte etkin bir Müdür zaten var. Kullanıcılar ekranında önce mevcut "
                  "Müdürü Personel olarak değiştirin veya hesabını devre dışı bırakın; sonra yeni Müdürü atayın.")
SOD_ERROR = ("{record} onaylanamadı: bu revizyonda veri oluşturdunuz veya değiştirdiniz. "
             "Görevler ayrılığı gereği veriyi giren/değiştiren kişi aynı revizyonu onaylayamaz. "
             "Kullanıcılar ekranında bu revizyonda veri değiştirmemiş bir Strateji Geliştirme Müdürü atanmasını sağlayın.")


def require_strategy_director(user):
    if user.role != 'strategy' or user.position != 'director' or not user.is_active or not user.department_id:
        raise HTTPException(403, "Paket iadesi/onayı ve Faaliyet Raporu onayı yalnızca Strateji Geliştirme Müdürü tarafından yapılabilir. "
                            "Kullanıcılar ekranındaki Müdür atamasını kontrol ettirmek için Strateji birimine başvurun.")


def require_submit(user):
    if user.position != 'director' and not user.can_submit:
        raise HTTPException(403, "PP paketi gönderilemedi. Yalnızca müdürlüğün Müdürü veya gönderim yetkisi verilen Personel gönderebilir. "
                            "Müdürünüzden Gönderim Yetkileri ekranında ya da Strateji biriminden Kullanıcılar ekranında yetki vermesini isteyin.")


def validate_position(position):
    if not isinstance(position, str) or position not in {'staff', 'director'}:
        raise HTTPException(422, "Kullanıcı unvanı geçersiz. Kullanıcılar ekranında Müdür veya Personel seçin.")


def strategy_department(db):
    department = db.scalar(select(Department).where(Department.name == 'Strateji Geliştirme Müdürlüğü'))
    if not department:
        raise HTTPException(422, "Strateji Geliştirme Müdürlüğü kaydı bulunamadı. Kullanıcılar ekranındaki müdürlük kaydını Strateji birimine kontrol ettirin.")
    return department


def check_director_available(db, target):
    if not target.department_id:
        raise HTTPException(422, "Müdür ataması için kullanıcının müdürlüğü olmalı. Kullanıcılar ekranından müdürlük seçin.")
    db.scalar(select(Department).where(Department.id == target.department_id).with_for_update())
    query = select(User.id).where(User.department_id == target.department_id,
                                  User.position == 'director', User.is_active.is_(True))
    if target.id:
        query = query.where(User.id != target.id)
    if db.scalar(query.limit(1)):
        raise HTTPException(409, DIRECTOR_ERROR)


def commit_user_change(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, DIRECTOR_ERROR) from None


def lock_user_administration(db, actor, target):
    """Serialize authority checks with appointments, activation and account edits."""
    department_ids = sorted({did for did in (actor.department_id, target.department_id) if did})
    organization_ids = sorted(set(db.scalars(select(Department.organization_id).where(
        Department.id.in_(department_ids))).all()))
    # Organization first, then departments: concurrent bootstrap requests must
    # observe the winner, including legacy Strategy accounts in another department.
    for oid in organization_ids:
        db.scalar(select(Organization).where(Organization.id == oid).with_for_update())
    for did in department_ids:
        db.scalar(select(Department).where(Department.id == did).with_for_update())
    actor = db.get(User, actor.id, populate_existing=True)
    if target.id:
        target = db.get(User, target.id, populate_existing=True)
    if not actor or not actor.is_active or actor.role != 'strategy':
        raise HTTPException(403, "Kullanıcı yönetimi için etkin Strateji hesabı gerekir. Yeniden giriş yapın; Strateji Geliştirme Müdürüne başvurun.")
    return actor, target


def is_strategy_user(db, target):
    department = db.get(Department, target.department_id) if target.department_id else None
    return target.role == 'strategy' or bool(department and department.name == 'Strateji Geliştirme Müdürlüğü')


def require_strategy_user_management(db, actor, target, *, appointment=False):
    """Call only after lock_user_administration; return an explicit bootstrap reason."""
    if not is_strategy_user(db, target):
        return None
    department = db.get(Department, target.department_id) if target.department_id else None
    directors = select(User.id).where(User.role == 'strategy', User.position == 'director', User.is_active.is_(True))
    if department:
        directors = directors.join(Department).where(Department.organization_id == department.organization_id)
    director_ids = set(db.scalars(directors).all())
    if actor.id in director_ids:
        return None
    if not director_ids and appointment and target.role == 'strategy':
        return 'Strateji Müdürü başlangıç ataması: etkin Strateji Geliştirme Müdürü bulunmadığı için etkin Strateji kullanıcısı tarafından yapıldı (bootstrap).'
    raise HTTPException(403, f"{target.full_name} ({target.email}) kullanıcısının Strateji unvanını veya Müdür hesabını değiştiremezsiniz. "
                        "Kullanıcılar ekranındaki işlem için etkin Strateji Geliştirme Müdürüne başvurun. "
                        "Etkin Müdür yoksa başka bir etkin Strateji kullanıcısı yalnızca yeni Müdür atayabilir.")


def audit_user_change(db, actor, target, field, old, new, reason=None):
    details = {'field': field, 'old': old, 'new': new}
    if reason:
        details['reason'] = reason
    db.add(AuditLog(user_id=actor.id, action='user_' + field + '_change', entity_type='user',
                    entity_id=target.id, details=json.dumps(details, ensure_ascii=False)))


def register(app):
    from .main import require_user, require_strategy, templates, session_period

    @app.get('/submit-authorizations')
    def authorizations(request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        if user.role != 'department' or user.position != 'director':
            raise HTTPException(403, "Gönderim Yetkileri ekranını yalnızca müdürlüğün Müdürü açabilir. Yetki için Müdürünüze başvurun.")
        users = db.scalars(select(User).where(User.department_id == user.department_id,
                                             User.role == 'department', User.position == 'staff').order_by(User.full_name)).all()
        return templates.TemplateResponse(request, 'submit_authorizations.html',
                                          {'user': user, 'period': session_period(request, db), 'users': users, 'department': db.get(Department, user.department_id)})

    @app.post('/api/users/{user_id}/submit-authorization')
    async def submit_authorization(user_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_user)):
        data = await request.json()  # All awaits precede locks.
        value = data.get('can_submit') if isinstance(data, dict) else None
        if not isinstance(value, bool):
            raise HTTPException(422, "Gönderim yetkisi geçersiz. Gönderim Yetkileri ekranında Yetki ver veya Yetkiyi kaldır seçin.")
        target = db.get(User, user_id)
        if not target:
            raise HTTPException(404, "Kullanıcı bulunamadı. Kullanıcı listesini yenileyin.")
        db.scalar(select(Department).where(Department.id == target.department_id).with_for_update())
        db.refresh(user)
        db.refresh(target)
        if user.role != 'strategy' and not (user.role == 'department' and user.position == 'director'
                                            and user.department_id == target.department_id):
            raise HTTPException(403, "Bu personelin gönderim yetkisini değiştiremezsiniz. Kendi müdürlüğünüzün Müdürüne veya Strateji birimine başvurun.")
        if target.role != 'department' or target.position != 'staff':
            raise HTTPException(422, "Gönderim yetkisi yalnızca müdürlük Personeline verilir. Müdür kendi müdürlüğünün paketini zaten gönderebilir.")
        old = target.can_submit
        target.can_submit = value
        if old != value:
            audit_user_change(db, user, target, 'can_submit', old, value)
        db.commit()
        return {'ok': True, 'can_submit': value}

    @app.post('/api/users/{user_id}/position')
    async def position(user_id: int, request: Request, db: Session = Depends(get_db), user=Depends(require_strategy)):
        data = await request.json()
        value = data.get('position') if isinstance(data, dict) else None
        validate_position(value)
        target = db.get(User, user_id)
        if not target:
            raise HTTPException(404, "Kullanıcı bulunamadı. Kullanıcılar ekranını yenileyin.")
        user, target = lock_user_administration(db, user, target)
        if user.id == target.id:
            raise HTTPException(403, f"{target.full_name} ({target.email}): kendi unvanınızı değiştiremezsiniz. "
                                "Kullanıcılar ekranındaki atama için Strateji Geliştirme Müdürüne başvurun; "
                                "etkin Müdür yoksa başka bir etkin Strateji kullanıcısından Müdür atamasını isteyin.")
        reason = require_strategy_user_management(db, user, target, appointment=value == 'director' and target.is_active)
        if value == 'director' and target.is_active:
            check_director_available(db, target)
        old = target.position
        target.position = value
        if old != value:
            audit_user_change(db, user, target, 'position', old, value, reason)
        commit_user_change(db)
        return {'ok': True, 'position': value}


# Persist scope before a row can be deleted/replaced. The audit and data commit
# together, so failed edits leave no authorship and later editors cannot erase it.
DIRECT_SCOPE = (Indicator, Activity, ReportCard, DepartmentCostValue, EconomicValue, DepartmentScope)


def pp_scopes(db, row):
    if isinstance(row, DIRECT_SCOPE):
        return {(row.period_id, row.department_id)}
    if isinstance(row, IndicatorValue):
        parent = db.get(Indicator, row.indicator_id)
        return pp_scopes(db, parent) if parent else set()
    if isinstance(row, (ActivityCostValue, ActivityCatalogueLink)):
        parent = db.get(Activity, row.activity_id)
        return pp_scopes(db, parent) if parent else set()
    if isinstance(row, ActivityResponsibility):
        parent = db.get(OfficialActivity, row.official_activity_id)
        return {(parent.period_id, row.department_id)} if parent else set()
    if isinstance(row, (SubProgram, Program, OfficialActivity)):
        # Shared definitions appear in all linked directorate packages.
        if isinstance(row, OfficialActivity):
            dids = db.scalars(select(ActivityResponsibility.department_id).where(
                ActivityResponsibility.official_activity_id == row.id)).all()
        else:
            sub_ids = [row.id] if isinstance(row, SubProgram) else db.scalars(select(SubProgram.id).where(SubProgram.program_id == row.id)).all()
            dids = set()
            for model in (Indicator, Activity, ReportCard):
                dids.update(db.scalars(select(model.department_id).where(model.subprogram_id.in_(sub_ids))).all())
        return {(row.period_id, did) for did in dids}
    return set()


@event.listens_for(Session, 'before_flush')
def track_pp_authorship(db, flush_context, instances):
    actor_id = db.info.get('released_actor_id')
    if actor_id is None:
        return
    scopes = set()
    for row in list(db.new) + list(db.dirty) + list(db.deleted):
        if row in db.dirty:
            changed = {attr.key for attr in inspect(row).attrs if attr.history.has_changes()}
            # Allocating stable identity during publication isn't a content edit.
            if not changed or (isinstance(row, Indicator) and changed <= {'persistent_indicator_id'}):
                continue
        scopes.update(pp_scopes(db, row))
    for period_id, department_id in sorted(scopes):
        if period_id is None or department_id is None:
            continue
        # Same lock as submit/decision; this hook never awaits.
        db.scalar(select(Department).where(Department.id == department_id).with_for_update())
        status = db.scalar(select(Submission.status).where(Submission.period_id == period_id,
                                                           Submission.department_id == department_id))
        if status in {'submitted', 'approved'}:
            raise HTTPException(409, "PP paketi incelemede veya onaylı olduğu için verisi değiştirilemez. İnceleme kuyruğundan iade edilmesini isteyin.")
        db.add(AuditLog(user_id=actor_id, action='pp_data_change', entity_type='department',
                        entity_id=department_id, details=f'period_id={period_id}'))


def require_independent_pp_approver(db, user, submission):
    returned = db.scalar(select(SubmissionEvent).where(SubmissionEvent.submission_id == submission.id,
        SubmissionEvent.event_type.in_(['return', 'reopen'])).order_by(SubmissionEvent.id.desc()).limit(1))
    query = select(AuditLog).where(AuditLog.user_id == user.id)
    if returned:
        query = query.where(AuditLog.created_at >= returned.created_at)
    tracking_start = db.scalar(select(AuditLog.id).where(AuditLog.action == 'civ025_tracking_started').order_by(AuditLog.id).limit(1))
    for audit in db.scalars(query):
        if audit.action == 'pp_data_change':
            matches = audit.entity_id == submission.department_id and audit.details == f'period_id={submission.period_id}'
        else:
            matches = (tracking_start is None or audit.id < tracking_start) and historical_pp_edit(db, audit, submission)
        if matches is None:
            raise HTTPException(403, "PP paketi onaylanamadı: eski veri değişikliği kaydınızın müdürlük/dönem kapsamı doğrulanamıyor. Görevler ayrılığı kontrolü için paketi iade edip yeniden gönderilmesini isteyin veya bağımsız Strateji Geliştirme Müdürü atamasını Kullanıcılar ekranından kontrol ettirin.")
        if matches:
            raise HTTPException(403, SOD_ERROR.format(record='PP paketi'))


def historical_pp_edit(db, audit, submission):
    """Honor pre-CIV-025 pilot history too; never assume missing scope is clean."""
    models = {'indicator': Indicator, 'indicators': Indicator, 'activity': Activity, 'activities': Activity,
              'report_card': ReportCard, 'indicator_value': IndicatorValue, 'activity_cost_values': ActivityCostValue,
              'department_cost_values': DepartmentCostValue, 'official_activity': OfficialActivity}
    actions = {'indicator_update', 'indicator_create', 'activity_create', 'activity_update', 'activity_delete',
               'card_save', 'card_assign', 'finance_save', 'source_value_verified', 'source_money_verified',
               'catalogue_link', 'catalogue_create', 'activity_mapping_csv', 'activity_mapping'}
    if audit.action in actions and audit.entity_type in models:
        row = db.get(models[audit.entity_type], audit.entity_id)
        # Historical deletion audits did not retain scope. Fail closed for that
        # actor until the package is returned; new audits always retain scope.
        return None if row is None else (submission.period_id, submission.department_id) in pp_scopes(db, row)
    if audit.action in {'personnel_cost_update', 'economic_save', 'economic_grid_save', 'scope_save'}:
        if audit.action == 'economic_grid_save':
            return audit.entity_id == submission.department_id and audit.details.split('/')[0] == str(submission.period_id)
        return None if audit.entity_id == submission.department_id else False
    if audit.action in {'data_import_apply', 'data_import_revert'}:
        batch = db.get(ImportBatch, audit.entity_id)
        if not batch:
            return None
        if batch.period_id != submission.period_id:
            return False
        try:
            snapshot = json.loads(batch.snapshot_json or '{}')
        except (ValueError, TypeError):
            return None
        if not snapshot:
            return None
        departments = {row['department_id'] for row in snapshot.get('departments', [])}
        departments.update(snapshot.get('created_department_ids', []))
        return submission.department_id in departments
    if audit.action == 'activity_mapping_csv_revert':
        batch_detail = audit.details.split(';')[0] + ';'
        originals = db.scalars(select(AuditLog).where(AuditLog.action == 'activity_mapping_csv',
                                                     AuditLog.details.startswith(batch_detail))).all()
        matches = [historical_pp_edit(db, item, submission) for item in originals]
        return True if any(matches) else None if not originals or None in matches else False
    return False
