"""Bounded Phase 5B1: real migrated PostgreSQL, both immutable resource scopes."""
import json
from datetime import timedelta
import pytest
from sqlalchemy import select, func, event, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.attributes import set_committed_value
from app.models import *
from app import package_service as packages, authorization_service as auth
from tests.test_revision_workflow import foundation_db, people, package, approved, candidate, released, request, accept, grant, edit, service, rejects
from tests.test_package_workflow import act
from tests.test_authorization_foundation import grant as delegate
pytestmark=pytest.mark.postgres


def correction(db,x,r,key='user'):
    q=request(db,x,r,key);accept(db,x,q);g=grant(db,x,q,key=key)
    rev=edit(db,x,g,key,reason='Müdür kaynak düzeltmesi')
    return db.get(DirectoratePackage,rev.package_id),rev,g,q


def counts(db):
    return tuple(db.scalar(select(func.count(cls.id))) for cls in
                 (PackageRevision,PackageDecision,WorkflowEvent,Notification,NotificationRecipient))


@pytest.mark.parametrize('key',['user','director'])
def test_exact_reapproval_preserves_release_and_director_contribution(foundation_db,people,released,key):
    db=foundation_db;x=people;r=released
    frozen={cls:{row.id:tuple(getattr(row,c.name) for c in cls.__table__.columns) for row in db.scalars(select(cls))}
            for cls in (ReportRelease,ReportCandidate,ReportArtifact,Publication,ActivityReportApproval,ActualRevision,PackageRevision)}
    p,rev,g,q=correction(db,x,r,key)
    for action,actor,state in [('submit_to_director',key,'director_review'),('director_approve','director','strategy_review'),('strategy_approve','strategy','strategy_approved')]:
        act(db,x,p,action,actor);assert p.state==state and packages.revision(db,p).id==rev.id
        d=db.scalar(select(PackageDecision).where(PackageDecision.package_revision_id==rev.id,PackageDecision.action==action))
        assert d.snapshot_sha256==rev.sha256
        assert json.loads(db.get(WorkflowEvent,d.workflow_event_id).context_json)['correction_cycle_id']==g.cycle_id
    for cls,rows in frozen.items():
        for rid,values in rows.items():assert tuple(getattr(db.get(cls,rid),c.name) for c in cls.__table__.columns)==values
    assert db.get(RevisionRequestState,q.id).state=='editing'
    assert db.scalar(select(func.count(ReportRelease.id)))==len(frozen[ReportRelease])


@pytest.mark.parametrize('gate',['submit_to_director','director_approve','strategy_approve'])
@pytest.mark.parametrize('bad',['version','hash','tampered'])
def test_stale_and_tampered_fail_without_writes(foundation_db,people,released,gate,bad):
    db=foundation_db;x=people;p,rev,g,q=correction(db,x,released)
    if gate!='submit_to_director':act(db,x,p,'submit_to_director','user')
    if gate=='strategy_approve':act(db,x,p,'director_approve')
    version=p.version;sha=rev.sha256
    if bad=='version':version-=1
    elif bad=='hash':sha='0'*64
    else:set_committed_value(rev,'content_json',rev.content_json+' ')
    before=counts(db);state=(p.state,p.version,p.current_revision)
    rejects(409,lambda:packages.transition(db,x['strategy' if gate=='strategy_approve' else 'director' if gate=='director_approve' else 'user'],p.id,gate,version,sha))
    assert counts(db)==before and (p.state,p.version,p.current_revision)==state


@pytest.mark.parametrize('gate',['director_approve','strategy_approve'])
def test_both_gates_validate_exact_correction_content(foundation_db,people,released,gate,monkeypatch):
    db=foundation_db;x=people;r=released
    path=['cards',0,'goal'] if r.resource_scope=='performance_program' else ['entries',0,'state']
    q=service.create_request(db,x['user'],r.id,x['department'].id,[{'path':path}],'Kontrol gereken alan');db.commit();accept(db,x,q);g=grant(db,x,q)
    p=db.get(DirectoratePackage,db.get(RevisionCorrectionCycle,g.cycle_id).package_id);old=packages.revision(db,p)
    rev=service.edit_under_grant(db,x['user'],g.id,p.version,old.sha256,[{'path':path,'value':'' if r.resource_scope=='performance_program' else 'needs_review'}]);db.commit()
    act(db,x,p,'submit_to_director','user')
    if gate=='strategy_approve':
        # Isolate the independent second gate: admit only the first decision in this fixture.
        original=packages.validate_package_approval
        monkeypatch.setattr(packages,'validate_package_approval',lambda *args:None)
        act(db,x,p,'director_approve');monkeypatch.setattr(packages,'validate_package_approval',original)
    before=counts(db)
    with pytest.raises(auth.HTTPException) as caught:act(db,x,p,gate,'strategy' if gate=='strategy_approve' else 'director')
    assert caught.value.status_code==409 and caught.value.detail['revision_id']==rev.id
    assert caught.value.detail['sha256']==rev.sha256 and caught.value.detail['blockers']
    assert counts(db)==before


@pytest.mark.parametrize('action',['director_return','director_reopen','strategy_return'])
def test_return_copy_and_reapproval(foundation_db,people,released,action):
    db=foundation_db;x=people;p,rev,g,q=correction(db,x,released)
    act(db,x,p,'submit_to_director','user')
    if action=='strategy_return':act(db,x,p,'director_approve')
    act(db,x,p,action,'strategy' if action=='strategy_return' else 'director','Kaynağı yeniden kontrol edin')
    new=packages.revision(db,p)
    assert new.previous_revision_id==rev.id and new.content_json==rev.content_json and new.sha256==rev.sha256
    rejects(403,lambda:act(db,x,p,'strategy_approve','strategy'))
    act(db,x,p,'submit_to_director','user');act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    assert p.state=='strategy_approved'


def test_active_delegate_only_and_revocation(foundation_db,people,released):
    db=foundation_db;x=people;p,rev,g,q=correction(db,x,released,'director');d=delegate(db,x)
    act(db,x,p,'submit_to_director','director')
    rejects(403,lambda:act(db,x,p,'director_approve'))
    act(db,x,p,'director_approve','user')
    decision=db.scalar(select(PackageDecision).where(PackageDecision.package_revision_id==rev.id,PackageDecision.action=='director_approve'))
    assert decision.delegation_id==d.id
    act(db,x,p,'strategy_return','strategy','Yeniden kontrol');act(db,x,p,'submit_to_director','director')
    auth.revoke_delegation(db,x['director'],d.id,'Vekâlet sona erdi');db.commit()
    rejects(403,lambda:act(db,x,p,'director_approve','user'))
    act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')


@pytest.mark.parametrize('action',['submit_to_director','director_approve','strategy_approve','director_return','strategy_return'])
def test_notification_failure_rolls_back_everything(foundation_db,people,released,action):
    db=foundation_db;x=people;p,rev,g,q=correction(db,x,released)
    if action!='submit_to_director':act(db,x,p,'submit_to_director','user')
    if action in ('strategy_approve','strategy_return'):act(db,x,p,'director_approve')
    before=counts(db);state=(p.state,p.version,p.current_revision)
    def fail(*args):raise RuntimeError('mandatory notification failed')
    event.listen(NotificationRecipient,'before_insert',fail)
    try:
        with pytest.raises(RuntimeError):act(db,x,p,action,'strategy' if action.startswith('strategy') else 'user' if action=='submit_to_director' else 'director','İade gerekçesi')
    finally:event.remove(NotificationRecipient,'before_insert',fail)
    db.expire_all();assert counts(db)==before and (p.state,p.version,p.current_revision)==state


@pytest.mark.parametrize('bad',['no_decision','skip_director','old_decision','copy_without_audit'])
def test_sql_projection_and_copy_fail_closed(foundation_db,people,released,bad):
    db=foundation_db;x=people;p,rev,g,q=correction(db,x,released)
    if bad=='old_decision':
        act(db,x,p,'submit_to_director','user');act(db,x,p,'director_approve');act(db,x,p,'strategy_return','strategy','İade');rev=packages.revision(db,p)
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            if bad=='copy_without_audit':packages.append_revision(db,p,x['director'],rev.content_json,rev,'Sahte iade')
            else:db.execute(text("UPDATE directorate_packages SET state=:state,version=version+1 WHERE id=:id"),{'state':'strategy_approved' if bad=='skip_director' else 'director_review','id':p.id})


def test_stale_release_fails_closed_and_expired_grant_does_not_block_review(foundation_db,people,released,monkeypatch):
    db=foundation_db;x=people;p,rev,g,q=correction(db,x,released)
    original=db.scalar
    def scalar(statement,*args,**kw):
        if 'report_releases.major DESC' in str(statement):return released.id+1
        return original(statement,*args,**kw)
    monkeypatch.setattr(db,'scalar',scalar)
    before=counts(db)
    rejects(409,lambda:act(db,x,p,'submit_to_director','user'))
    assert counts(db)==before
    monkeypatch.setattr(db,'scalar',original)
    # A1-P1 K-7: the grant authorized the edit; its later expiry does not freeze submission/review.
    monkeypatch.setattr(auth,'server_now',lambda db:g.end_at+timedelta(seconds=1))
    act(db,x,p,'submit_to_director','user');assert p.state=='director_review'
    assert db.scalar(select(func.count(RevisionEditGrantRenewal.id)))==0


@pytest.mark.parametrize('bad',['inactive_director','removed_director','inactive_strategy','removed_delegate','expired_delegate'])
def test_current_authority_changes_fail_closed(foundation_db,people,released,bad,monkeypatch):
    db=foundation_db;x=people;p,rev,g,q=correction(db,x,released)
    if bad in ('removed_delegate','expired_delegate'):d=delegate(db,x)
    act(db,x,p,'submit_to_director','user')
    if bad=='inactive_strategy':
        act(db,x,p,'director_approve');x['strategy'].is_active=False;db.commit()
    elif bad=='inactive_director':x['director'].is_active=False;db.commit()
    elif bad in ('removed_director','removed_delegate'):
        key='director' if bad=='removed_director' else 'user'
        m=auth.active_membership(db,x[key].id,p.organization_id,p.department_id)
        auth.deactivate_membership(db,x['strategy'],m.id,'Görevlendirme sona erdi');db.commit()
    else:
        monkeypatch.setattr(auth,'server_now',lambda db:d.end_at+timedelta(seconds=1))
    before=counts(db)
    rejects(403,lambda:act(db,x,p,'strategy_approve' if bad=='inactive_strategy' else 'director_approve',
                         'strategy' if bad=='inactive_strategy' else 'user' if bad in ('removed_delegate','expired_delegate') else 'director'))
    assert counts(db)==before
    if bad=='removed_delegate':rejects(403,lambda:act(db,x,p,'director_approve'))


def test_concurrent_submission_binds_one_decision(foundation_db,people,released):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.orm import Session
    db=foundation_db;x=people;p,rev,g,q=correction(db,x,released);version=p.version
    pid=p.id;uid=x['user'].id;sha=rev.sha256;db.commit();barrier=Barrier(2)
    def run(_):
        with Session(db.get_bind(),expire_on_commit=False) as other:
            actor=other.get(User,uid);barrier.wait()
            try:packages.transition(other,actor,pid,'submit_to_director',version,sha);other.commit();return 1
            except auth.HTTPException as exc:other.rollback();return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(run,range(2)))==[1,409]
    db.expire_all()
    assert p.state=='director_review' and p.version==version+1
    assert db.scalar(select(func.count(PackageDecision.id)).where(PackageDecision.package_revision_id==rev.id,
                     PackageDecision.action=='submit_to_director'))==1


@pytest.mark.parametrize('table',['package_revisions','package_decisions','workflow_events'])
@pytest.mark.parametrize('operation',['UPDATE','DELETE'])
def test_reapproval_audit_remains_immutable(foundation_db,people,released,table,operation):
    db=foundation_db;x=people;p,rev,g,q=correction(db,x,released)
    act(db,x,p,'submit_to_director','user');act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(text(f'DELETE FROM {table}' if operation=='DELETE' else f'UPDATE {table} SET id=id'))


@pytest.mark.parametrize('foundation_db',['375cefa60412'],indirect=True)
def test_populated_phase5a_upgrade_preserves_correction_history(foundation_db,people,released):
    import os,sys,subprocess
    from tests.test_authorization_foundation import ROOT
    db=foundation_db;x=people;p,rev,g,q=correction(db,x,released)
    tables=('report_candidates','report_releases','report_artifacts','package_revisions','package_decisions','workflow_events',
            'revision_requests','revision_request_states','revision_edit_grants','revision_correction_cycles','field_change_events')
    before={t:[dict(r) for r in db.execute(text(f'SELECT * FROM {t} ORDER BY 1')).mappings()] for t in tables};db.commit()
    for _ in range(2):
        result=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,
                              env={**os.environ,'DATABASE_URL':db.get_bind().url.render_as_string(hide_password=False)},capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    for t,rows in before.items():assert [dict(r) for r in db.execute(text(f'SELECT * FROM {t} ORDER BY 1')).mappings()]==rows
    act(db,x,p,'submit_to_director','user');act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    assert p.state=='strategy_approved'


@pytest.mark.parametrize('bad',['editor_approval','delegated_director','old_version','wrong_hash'])
def test_forged_sql_decision_cannot_move_correction(foundation_db,people,released,bad):
    db=foundation_db;x=people;p,rev,g,q=correction(db,x,released)
    act(db,x,p,'submit_to_director','user')
    if bad=='delegated_director':delegate(db,x)
    before=counts(db)
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            e=packages.history_event(db,x['user' if bad=='editor_approval' else 'director'],p,'director_approve',
                {'revision_id':rev.id,'sha256':'0'*64 if bad=='wrong_hash' else rev.sha256,
                 'from_state':'director_review','to_state':'strategy_review','delegation_id':None,
                 'correction_cycle_id':g.cycle_id,'expected_version':p.version-1 if bad=='old_version' else p.version})
            db.add(PackageDecision(package_revision_id=rev.id,snapshot_sha256=rev.sha256,action='director_approve',
                                   from_state='director_review',to_state='strategy_review',workflow_event_id=e.id))
            db.flush();packages.move(db,p,p.version,'strategy_review',rev.revision)
    db.expire_all();assert counts(db)==before and p.state=='director_review'
