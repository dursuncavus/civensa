"""Fixed-scope foundation; no future workflow is enabled or exposed by these helpers.

Mutators flush only. A trusted local bootstrap transaction owns commit/rollback.
Eligibility is a preview, not an authorization grant. Runtime `can` denies new
workflow actions until a later reviewed activation migration.
"""
from datetime import UTC, datetime
from decimal import Decimal
import json
from uuid import uuid4
from sqlalchemy import select, func, exists, text
from sqlalchemy.orm import aliased
from fastapi import HTTPException
from .models import (User, Department, Organization, DirectorateMembership, MembershipEvent,
    AuthorityDelegation, DelegationRevocation, DelegationEvent, FinalAuthorityAssignment,
    FinalAuthorityEvent, WorkflowEvent, FieldChangeEvent, Notification, NotificationRecipient)


def encode(value):
    def convert(item):
        if isinstance(item, float):
            raise ValueError('Audit numeric values must be Decimal, integer or raw text.')
        if isinstance(item, Decimal):
            return str(item)
        if isinstance(item, datetime):
            return item.isoformat()
        if isinstance(item, dict):
            return {key: convert(val) for key, val in item.items()}
        if isinstance(item, (list, tuple)):
            return [convert(val) for val in item]
        return item
    return json.dumps(convert(value), ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def fail(message, status=403):
    raise HTTPException(status, message)


def required(value, label):
    if not isinstance(value, str) or not value.strip():
        fail(f'{label} belirtilmedi. Resmî dayanağı / gerekçeyi girin.', 422)
    return value.strip()


def server_now(db):
    value = db.scalar(select(func.clock_timestamp() if db.get_bind().dialect.name == 'postgresql' else func.current_timestamp()))
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def active_actor(db, actor):
    db.flush()
    row = db.get(User, actor.id, populate_existing=True) if actor is not None else None
    if not row or not row.is_active:
        fail('Aktif kullanıcı yetkisi bulunamadı.')
    return row


def scope_department(db, organization_id, department_id, lock=False):
    stmt = select(Department).where(Department.id == department_id, Department.organization_id == organization_id)
    if lock:
        stmt = stmt.with_for_update()
    row = db.scalar(stmt)
    if not row:
        fail('Müdürlük seçilen kuruma ait değil.')
    return row


def actor_snapshot(db, actor, organization_id):
    roles = db.scalars(select(DirectorateMembership).where(
        DirectorateMembership.user_id == actor.id, DirectorateMembership.organization_id == organization_id,
        DirectorateMembership.active.is_(True))).all()
    return encode({'user_id': actor.id, 'name': actor.full_name, 'email': actor.email,
                   'legacy_role': actor.role,
                   'memberships': [{'id': m.id, 'department_id': m.department_id, 'role': m.role_code} for m in roles]})


def membership_snapshot(row):
    return {name: getattr(row, name) for name in ('id','organization_id','department_id','user_id','role_code','slot','active','formal_basis')}


def assign_membership(db, actor, organization_id, department_id, user_id, role_code, slot, formal_basis):
    actor = active_actor(db, actor)
    scope_department(db, organization_id, department_id, lock=True)
    user = db.get(User, user_id)
    if not user or not user.is_active or user.department_id != department_id:
        fail('Üye, bu müdürlüğün mevcut aktif kullanıcısı olmalıdır.')
    if (role_code, slot) not in {('department_editor',1),('department_editor',2),('department_director',3)}:
        fail('Müdürlük için iki veri girişçisi ve bir müdür slotu kullanılabilir.',422)
    row = DirectorateMembership(organization_id=organization_id, department_id=department_id,
        user_id=user_id, role_code=role_code, slot=slot, formal_basis=required(formal_basis,'Atama dayanağı'), created_by=actor.id)
    db.add(row); db.flush()
    db.add(MembershipEvent(membership_id=row.id, actor_user_id=actor.id,
        actor_snapshot_json=actor_snapshot(db,actor,organization_id), event_type='assigned',
        previous_json='null',new_json=encode(membership_snapshot(row)),reason=row.formal_basis))
    db.flush()
    return row


def deactivate_membership(db, actor, membership_id, reason):
    actor=active_actor(db,actor); reason=required(reason,'Görevlendirme kaldırma gerekçesi')
    row=db.get(DirectorateMembership,membership_id)
    if not row:fail('Görevlendirme bulunamadı.',404)
    scope_department(db,row.organization_id,row.department_id,lock=True)
    previous=encode(membership_snapshot(row)); updated={**membership_snapshot(row),'active':False}
    db.add(MembershipEvent(membership_id=row.id,actor_user_id=actor.id,
        actor_snapshot_json=actor_snapshot(db,actor,row.organization_id),event_type='deactivated',
        previous_json=previous,new_json=encode(updated),reason=reason));db.flush()
    # A1-F5: a delegation derives from this director membership; end it in the
    # same transaction, before the membership changes (DB-enforced). It never
    # transfers to the next director.
    if row.role_code=='department_director':
        terminate_director_delegations(db,actor,row.organization_id,row.department_id,reason,director_membership_id=row.id)
    db.execute(text('UPDATE directorate_memberships SET active=false WHERE id=:id'),{'id':row.id});db.expire(row)


DIRECTOR_CHANGE_TERMINATION='terminated_due_to_director_change'


def terminate_director_delegations(db, actor, organization_id, department_id, reason, director_membership_id=None):
    """End unrevoked active delegations whose director membership is (being) inactive.

    Immutable revocation + 'revoked' DelegationEvent whose cause/reason is
    terminated_due_to_director_change (the existing PG/SQLite delegation guards
    accept only this audited revocation); interval/basis stay untouched.
    Caller holds the department lock."""
    query=select(AuthorityDelegation).where(
        AuthorityDelegation.organization_id==organization_id,AuthorityDelegation.department_id==department_id,
        AuthorityDelegation.active.is_(True),~exists().where(DelegationRevocation.delegation_id==AuthorityDelegation.id))
    director=aliased(DirectorateMembership);person=aliased(User)
    query=query.where(AuthorityDelegation.director_membership_id==director_membership_id) if director_membership_id is not None else query.where(
        ~exists().where(director.id==AuthorityDelegation.director_membership_id,director.active.is_(True),
            person.id==director.user_id,person.is_active.is_(True)))
    rows=db.scalars(query.order_by(AuthorityDelegation.id).with_for_update(of=AuthorityDelegation)).all()
    for delegation in rows:
        db.add(DelegationRevocation(delegation_id=delegation.id,actor_user_id=actor.id,reason=f'{DIRECTOR_CHANGE_TERMINATION}: {reason}'));db.flush()
        db.add(DelegationEvent(delegation_id=delegation.id,actor_user_id=actor.id,
            actor_snapshot_json=actor_snapshot(db,actor,organization_id),event_type='revoked',
            context_json=encode({'delegation_id':delegation.id,'director_membership_id':delegation.director_membership_id,
                'delegate_membership_id':delegation.delegate_membership_id,'cause':DIRECTOR_CHANGE_TERMINATION}),reason=reason));db.flush()
        db.execute(text('UPDATE authority_delegations SET active=false WHERE id=:id'),{'id':delegation.id});db.expire(delegation)
    return rows


def active_membership(db, user_id, org_id, dep_id):
    return db.scalar(select(DirectorateMembership).join(User,User.id==DirectorateMembership.user_id).where(
        DirectorateMembership.user_id==user_id,DirectorateMembership.organization_id==org_id,
        DirectorateMembership.department_id==dep_id,DirectorateMembership.active.is_(True),User.is_active.is_(True)))


def active_delegation(db, org_id, dep_id, *, at=None):
    now=at if at is not None else server_now(db)
    # A1-F5 defense in depth: authority derives from the delegating director's
    # active membership; a stale active row of a replaced director grants nothing.
    return db.scalar(select(AuthorityDelegation).join(DirectorateMembership,DirectorateMembership.id==AuthorityDelegation.director_membership_id)
        .join(User,User.id==DirectorateMembership.user_id).where(AuthorityDelegation.organization_id==org_id,
        AuthorityDelegation.department_id==dep_id,AuthorityDelegation.active.is_(True),
        AuthorityDelegation.start_at<=now,AuthorityDelegation.end_at>now,
        DirectorateMembership.active.is_(True),DirectorateMembership.role_code=='department_director',
        DirectorateMembership.organization_id==org_id,DirectorateMembership.department_id==dep_id,User.is_active.is_(True),
        ~exists().where(DelegationRevocation.delegation_id==AuthorityDelegation.id)))


def eligibility(db, actor, action, organization_id, department_id=None, *, resource_scope=None,
                workflow_state='draft', revision_locked=False, approved_assignment_id=None, delegation_at=None):
    """Preview foundation eligibility only; cannot activate a workflow or authorize HTTP."""
    try:
        actor=active_actor(db,actor)
        if resource_scope not in {'performance_program','activity_report','final_candidate'}:
            return False
        if revision_locked or workflow_state not in {'draft','returned','director_review','final_review','final_approved'}:
            return False
        if department_id is None:
            if resource_scope!='final_candidate' or action not in {'final_approve','publish_final'}:
                return False
            if not db.get(Organization,organization_id):return False
            assigned=db.scalar(select(FinalAuthorityAssignment).join(User,User.id==FinalAuthorityAssignment.user_id).where(
                FinalAuthorityAssignment.organization_id==organization_id,FinalAuthorityAssignment.active.is_(True),User.is_active.is_(True)))
            if not assigned:return False
            if action=='final_approve':return workflow_state=='final_review' and assigned.user_id==actor.id
            # A changed assignment never inherits a previous approval.
            return workflow_state=='final_approved' and actor.role=='strategy' and assigned.id==approved_assignment_id
        scope_department(db,organization_id,department_id)
        if resource_scope=='final_candidate':return False
        member=active_membership(db,actor.id,organization_id,department_id)
        if not member:return False
        director=db.scalar(select(DirectorateMembership).join(User,User.id==DirectorateMembership.user_id).where(
            DirectorateMembership.department_id==department_id,DirectorateMembership.organization_id==organization_id,
            DirectorateMembership.active.is_(True),DirectorateMembership.role_code=='department_director',User.is_active.is_(True)))
        if action=='edit_draft':return workflow_state in {'draft','returned'}
        if action=='submit_to_director':return workflow_state in {'draft','returned'} and director is not None
        delegated=active_delegation(db,organization_id,department_id,at=delegation_at)
        if action in {'director_approve','director_return'}:
            if workflow_state!='director_review' or not director:return False
            if delegated:
                delegate=active_membership(db,actor.id,organization_id,department_id)
                # If delegate is removed, fail closed until revocation/expiry; do not revive original.
                return delegated.director_membership_id==director.id and delegate.id==delegated.delegate_membership_id
            return member.id==director.id
        if action=='delegate_authority':
            return director is not None and member.id==director.id and delegated is None
        return False
    except HTTPException:
        return False


LEGACY_ACTIONS = {
    'department': {'legacy_read_department','legacy_edit_draft','legacy_submit'},
    'strategy': {'legacy_review','legacy_publish','legacy_operations','legacy_activity_approve'},
}


def can(db, actor, action, organization_id, department_id=None, *, resource_scope=None,
        workflow_state='draft', revision_locked=False, **unused):
    """Explicit legacy adapter; all new actions denied during foundation rollout."""
    try:
        actor=active_actor(db,actor)
        if action not in LEGACY_ACTIONS.get(actor.role,set()) or not db.get(Organization,organization_id):return False
        if resource_scope not in {'performance_program','activity_report'} or workflow_state not in {'draft','returned','submitted','approved'}:return False
        if department_id is not None:scope_department(db,organization_id,department_id)
        if actor.role=='department':
            if department_id is None or actor.department_id!=department_id:return False
            if action!='legacy_read_department' and (revision_locked or workflow_state not in {'draft','returned'}):return False
        elif revision_locked and action in {'legacy_publish','legacy_activity_approve'}:return False
        return True
    except HTTPException:
        return False


def create_delegation(db, actor, organization_id, department_id, delegate_user_id, start_at, end_at, formal_basis):
    actor=active_actor(db,actor);scope_department(db,organization_id,department_id,lock=True)
    if not eligibility(db,actor,'delegate_authority',organization_id,department_id,resource_scope='performance_program'):
        fail('Yalnız asıl müdür yetki devri oluşturabilir; vekil yeniden devir yapamaz.')
    if any(t.tzinfo is None for t in (start_at,end_at)) or start_at>=end_at or end_at<=server_now(db):
        fail('Saat dilimi belirtilmiş geçerli başlangıç ve bitiş girin.',422)
    # A stale active row of a replaced director must not block the new director.
    terminate_director_delegations(db,actor,organization_id,department_id,'Yeni müdür yetki devri öncesi önceki müdürün devri sonlandırıldı.')
    director=active_membership(db,actor.id,organization_id,department_id)
    delegate=active_membership(db,delegate_user_id,organization_id,department_id)
    if not delegate or delegate.role_code!='department_editor':fail('Vekil, müdürlüğün mevcut aktif veri girişçisi olmalıdır.')
    row=AuthorityDelegation(organization_id=organization_id,department_id=department_id,
        director_membership_id=director.id,delegate_membership_id=delegate.id,start_at=start_at,end_at=end_at,
        formal_basis=required(formal_basis,'Yetki devri dayanağı'),created_by=actor.id)
    db.add(row);db.flush()
    db.add(DelegationEvent(delegation_id=row.id,actor_user_id=actor.id,
        actor_snapshot_json=actor_snapshot(db,actor,organization_id),event_type='granted',
        context_json=encode({'director_membership_id':director.id,'delegate_membership_id':delegate.id,
            'start_at':start_at,'end_at':end_at,'formal_basis':row.formal_basis}),reason=row.formal_basis));db.flush()
    return row


def revoke_delegation(db, actor, delegation_id, reason):
    actor=active_actor(db,actor);reason=required(reason,'Yetki devri iptal gerekçesi')
    row=db.get(AuthorityDelegation,delegation_id)
    if not row:fail('Yetki devri bulunamadı.',404)
    scope_department(db,row.organization_id,row.department_id,lock=True)
    member=active_membership(db,actor.id,row.organization_id,row.department_id)
    if not member or member.id!=row.director_membership_id:fail('Yetki devrini asıl müdür iptal etmelidir.')
    db.add(DelegationRevocation(delegation_id=row.id,actor_user_id=actor.id,reason=reason));db.flush()
    db.add(DelegationEvent(delegation_id=row.id,actor_user_id=actor.id,
        actor_snapshot_json=actor_snapshot(db,actor,row.organization_id),event_type='revoked',
        context_json=encode({'delegation_id':row.id}),reason=reason));db.flush()
    # Only reservation state changes; original grant interval/basis remain immutable.
    db.execute(text('UPDATE authority_delegations SET active=false WHERE id=:id'),{'id':row.id});db.expire(row)


def assign_final_authority(db, actor, organization_id, user_id, formal_basis):
    """Trusted local administrative bootstrap ONLY; never a Strategy HTTP permission."""
    actor=active_actor(db,actor);basis=required(formal_basis,'Nihai onaycı atama dayanağı')
    org=db.scalar(select(Organization).where(Organization.id==organization_id).with_for_update())
    user=db.get(User,user_id)
    if not org or not user or not user.is_active:fail('Kurum / aktif nihai onaycı bulunamadı.',422)
    old=db.scalar(select(FinalAuthorityAssignment).where(FinalAuthorityAssignment.organization_id==organization_id,FinalAuthorityAssignment.active.is_(True)))
    if old:
        previous=encode({'user_id':old.user_id,'formal_basis':old.formal_basis,'active':True})
        db.add(FinalAuthorityEvent(assignment_id=old.id,actor_user_id=actor.id,
            actor_snapshot_json=actor_snapshot(db,actor,organization_id),previous_json=previous,
            new_json=encode({'active':False}),reason=basis));db.flush()
        db.execute(text('UPDATE final_authority_assignments SET active=false WHERE id=:id'),{'id':old.id});db.expire(old)
    row=FinalAuthorityAssignment(organization_id=organization_id,user_id=user_id,formal_basis=basis,created_by=actor.id)
    db.add(row);db.flush()
    db.add(FinalAuthorityEvent(assignment_id=row.id,actor_user_id=actor.id,
        actor_snapshot_json=actor_snapshot(db,actor,organization_id),previous_json='null',
        new_json=encode({'user_id':user_id,'formal_basis':basis,'active':True}),reason=basis));db.flush()
    return row


def atomic_change(db, actor, organization_id, department_id, resource_type, resource_id,
                  context, changes, mutate, *, reason='', source='manual', recipients=()):
    """Business mutation + field audit + recipient inbox, one savepoint, caller commits.

    Not exposed through HTTP and does not grant editing rights. Future workflow
    callers must authorize/lock/revalidate their resource before calling this.
    """
    actor=active_actor(db,actor);scope_department(db,organization_id,department_id,lock=True)
    if not context or not changes:fail('Revizyon bağlamı ve değişen alanlar belirtilmelidir.',422)
    if source not in {'manual','import','ex_officio'}:fail('Değişiklik kaynağı tanınmıyor.',422)
    if actor.role not in {'department','strategy'} or (actor.role=='department' and actor.department_id!=department_id):
        fail('Değişiklik aktörü bu müdürlük için yetkili değil.')
    if source=='import' and actor.role!='strategy':fail('İçe aktarma aktörü Strateji olmalıdır.')
    recipients=set(recipients)
    if source=='ex_officio':
        reason=required(reason,'Resen değişiklik gerekçesi')
        if actor.role!='strategy':fail('Resen değişikliği Strateji yapmalıdır.')
        director=db.scalar(select(DirectorateMembership).join(User,User.id==DirectorateMembership.user_id).where(
            DirectorateMembership.department_id==department_id,DirectorateMembership.organization_id==organization_id,
            DirectorateMembership.role_code=='department_director',DirectorateMembership.active.is_(True),User.is_active.is_(True)))
        if not director:fail('Aktif müdür atayın; zorunlu bildirim alıcısı bulunamadı.',409)
        recipients.add(director.user_id)
    if not recipients:fail('Zorunlu iç bildirim alıcısını belirtin.',422)
    for uid in recipients:
        recipient=db.get(User,uid)
        if not recipient or not recipient.is_active or (recipient.role!='strategy' and recipient.department_id!=department_id):
            fail('Bildirim alıcısı kapsam içinde ve aktif olmalıdır.',422)
    with db.begin_nested():
        result=mutate()
        event=WorkflowEvent(actor_user_id=actor.id,actor_snapshot_json=actor_snapshot(db,actor,organization_id),
            organization_id=organization_id,department_id=department_id,event_type='field_change',
            resource_type=required(resource_type,'Kaynak türü'),resource_id=str(resource_id),context_json=encode(context),
            reason=reason,source=source,correlation_id=str(uuid4()))
        db.add(event);db.flush()
        for change in changes:
            db.add(FieldChangeEvent(workflow_event_id=event.id,field_key=required(change['field_key'],'Alan'),
                field_type=required(change['field_type'],'Alan türü'),previous_json=encode(change['old']),new_json=encode(change['new'])))
        notice=Notification(role='department',department_id=department_id,event_type='field_change',
            message=f'{resource_type} kaydı değişti. Gerekçe: {reason}'[:500],link='',delivery_mode='recipients')
        db.add(notice);db.flush()
        for uid in recipients:db.add(NotificationRecipient(notification_id=notice.id,user_id=uid))
        db.flush()
    return result,event


def package_eligibility(db, actor, action, package, *, transition_time=None):
    """Internal Phase 3 backend eligibility. No HTTP/runtime activation grant.

    The caller must hold the package and department locks and derive state from DB.
    `can()` continues to deny every new workflow action until reviewed rollout.
    """
    try:
        actor = active_actor(db, actor)
        if actor.role not in {'department', 'strategy'}:
            return False
        if package.resource_scope not in {'performance_program', 'activity_report'}:
            return False
        scope_department(db, package.organization_id, package.department_id)
        if action == 'read_package':
            return actor.role == 'strategy' or (actor.department_id == package.department_id and
                active_membership(db, actor.id, package.organization_id, package.department_id) is not None)
        if action=='strategy_reopen':
            return actor.role=='strategy' and package.state=='strategy_approved'
        if action in {'strategy_approve', 'strategy_return'}:
            return actor.role == 'strategy' and package.state == 'strategy_review'
        if actor.role != 'department' or actor.department_id != package.department_id:
            return False
        if action == 'director_reopen':
            action = 'director_return'
        return eligibility(db, actor, action, package.organization_id, package.department_id,
            resource_scope=package.resource_scope, workflow_state=package.state, delegation_at=transition_time)
    except HTTPException:
        return False


def report_workflow_eligibility(db, actor, action, organization_id, state='assembling'):
    """Internal backend only; runtime can()/routes remain database-disabled."""
    try:
        actor=active_actor(db,actor)
        if not db.get(Organization,organization_id):return False
        if action in {'assemble_candidate','request_final_review','publish_report'}:
            if action=='publish_report' and db.scalar(select(FinalAuthorityAssignment.id).where(
                FinalAuthorityAssignment.organization_id==organization_id,FinalAuthorityAssignment.active.is_(True),FinalAuthorityAssignment.user_id==actor.id)):
                return False
            return actor.role=='strategy' and state in {'assemble_candidate':{'assembling'},
                'request_final_review':{'assembling'},'publish_report':{'final_approved','published'}}[action]
        if action not in {'view_candidate','final_approve','final_return'}:return False
        if state not in {'assembling','final_review','returned_to_strategy','final_approved','published'}:return False
        if action=='view_candidate' and actor.role=='strategy':return True
        assigned=db.scalar(select(FinalAuthorityAssignment).join(User,User.id==FinalAuthorityAssignment.user_id).where(
            FinalAuthorityAssignment.organization_id==organization_id,FinalAuthorityAssignment.active.is_(True),User.is_active.is_(True)))
        if not assigned or assigned.user_id!=actor.id:return False
        # A1-F1: the current final authority may also return a final_approved,
        # unpublished candidate (controlled recovery); Strategy never may.
        return action=='view_candidate' or (action in {'final_approve','final_return'} and state in {'final_review','final_approved'})
    except HTTPException:return False
