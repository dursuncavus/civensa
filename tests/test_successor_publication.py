"""S3B migrated PostgreSQL: exact lineage, completion, rollback and races."""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import select,func,text,event,update
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.exc import DBAPIError
from app.models import *
from app import report_workflow_service as reports, revision_workflow_service as corrections, authorization_service as auth
from tests.test_authorization_foundation import foundation_db, ROOT
from tests.test_materialized_successor import people,package,ready,assemble,counts,sealed,assert_sealed
from tests.test_report_workflow import approved,candidate,review,approve,publish,rejects
from tests.test_revision_workflow import released,request,accept,grant,edit
from tests.test_package_workflow import act
pytestmark=pytest.mark.postgres


@pytest.fixture
def successor(foundation_db,people,released,ready):
    db=foundation_db;p,rev,q,g=ready
    c=assemble(db,people,released,p);db.commit();review(db,people,c);approve(db,people,c)
    return c


def all_counts(db):
    return counts(db)+(db.scalar(select(func.count(RevisionRequestEvent.id))),db.scalar(select(func.count(NotificationRecipient.id))))


def test_first_successor_lineage_applied_history(foundation_db,people,released,ready,successor):
    db=foundation_db;x=people;p,rev,q,g=ready;before=sealed(db)
    first=publish(db,x,successor)
    assert (released.major,released.minor,first.major,first.minor)==(1,0,1,1)
    assert_sealed(db,before)
    rejects(409,lambda:corrections.current_source(db,released.id))
    assert corrections.current_source(db,first.id)[1].id==successor.id
    applied=db.get(RevisionRequestState,q.id);assert applied.state=='applied' and applied.version==3
    audit=db.scalar(select(RevisionRequestEvent).where(RevisionRequestEvent.request_id==q.id,RevisionRequestEvent.to_state=='applied'))
    e=db.get(WorkflowEvent,audit.workflow_event_id);context=json.loads(e.context_json)
    assert e.actor_user_id==x['strategy'].id
    assert context==dict(request_id=q.id,source_release_id=released.id,predecessor_release_id=released.id,successor_release_id=first.id,
        successor_candidate_id=successor.id,successor_candidate_sha256=successor.sha256,correction_cycle_id=g.cycle_id,grant_id=g.id,
        from_state='editing',to_state='applied',version=3)
    notice=db.scalar(select(Notification).where(Notification.event_type=='revision_applied'))
    assert set(db.scalars(select(NotificationRecipient.user_id).where(NotificationRecipient.notification_id==notice.id)))>={x['director'].id,q.requester_user_id}
    edge=db.scalar(select(ReportReleaseSuccession).where(ReportReleaseSuccession.predecessor_release_id==released.id))
    assert edge.successor_release_id==first.id and edge.workflow_event_id==first.workflow_event_id
    assert edge.predecessor_candidate_sha256==db.get(ReportCandidate,released.candidate_id).sha256
    assert edge.successor_candidate_sha256==successor.sha256
    for r in (released,first):
        artifact=reports.verify_artifact(db,r)
        assert artifact.object_version=='1.0' and json.loads(artifact.content_json)['version']==f'{r.major}.{r.minor}'
        reports.verify(db,db.get(ReportCandidate,r.candidate_id))
    assert_sealed(db,before)
    rejects(409,lambda:assemble(db,x,released,p))
    before=all_counts(db)
    assert publish(db,x,successor).id==first.id and all_counts(db)==before


def test_generic_assembly_bypass_closed(foundation_db,people,released,ready):
    db=foundation_db;p,rev,q,g=ready;before=all_counts(db)
    with pytest.raises(auth.HTTPException) as caught:
        reports.assemble_candidate(db,people['strategy'],p.organization_id,'activity_report',int(p.source_key),[p.id],released.candidate_id)
    assert caught.value.status_code==409 and 'assemble_activity_successor' in caught.value.detail
    assert all_counts(db)==before


def test_lineageless_publish_bypass_closed(foundation_db,people,released,successor):
    db=foundation_db;c=successor
    m=json.loads(c.manifest_json)
    for key in ('predecessor_release_id','predecessor_candidate_sha256','successor_contract','correction_cycle_ids','correction_request_grants'):m.pop(key)
    raw=reports.canonical(m);set_committed_value(c,'manifest_json',raw);set_committed_value(c,'sha256',reports.hash_content(c.payload_json,raw))
    before=all_counts(db)
    with pytest.raises(auth.HTTPException) as caught:publish(db,people,c)
    assert caught.value.status_code==409 and 'assemble_activity_successor' in caught.value.detail
    assert all_counts(db)==before


@pytest.mark.parametrize('state',['requested','accepted','editing'])
def test_new_work_after_assembly_blocks(foundation_db,people,released,ready,successor,state):
    db=foundation_db;x=people;p,rev,q,g=ready
    other=request(db,x,released,other=True)
    if state!='requested':accept(db,x,other)
    if state=='editing':rejects(409,lambda:grant(db,x,other))
    before=all_counts(db)
    rejects(409,lambda:publish(db,x,successor))
    assert all_counts(db)==before and db.get(RevisionRequestState,other.id).state==('accepted' if state=='editing' else state)
    assert db.get(RevisionRequestState,q.id).state=='editing'


def test_unedited_represented_request_blocks(foundation_db,people,released):
    db=foundation_db;x=people
    q=request(db,x,released);other=request(db,x,released,other=True)
    accept(db,x,q);accept(db,x,other);g=grant(db,x,q);grant(db,x,other)
    rev=edit(db,x,g);p=db.get(DirectoratePackage,rev.package_id)
    act(db,x,p,'submit_to_director','user');act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    c=assemble(db,x,released,p);db.commit();review(db,x,c);approve(db,x,c);before=all_counts(db)
    rejects(409,lambda:publish(db,x,c))
    assert all_counts(db)==before and db.get(RevisionRequestState,other.id).state=='editing'


def test_multiple_edited_requests_apply_together(foundation_db,people,released):
    db=foundation_db;x=people;q=request(db,x,released);other=request(db,x,released,other=True)
    accept(db,x,q);accept(db,x,other);g=grant(db,x,q);h=grant(db,x,other)
    edit(db,x,g);rev=edit(db,x,h,other=True,value='Yeni açıklama');p=db.get(DirectoratePackage,rev.package_id)
    act(db,x,p,'submit_to_director','user');act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    c=assemble(db,x,released,p);db.commit();review(db,x,c);approve(db,x,c);publish(db,x,c)
    assert db.get(RevisionRequestState,q.id).state==db.get(RevisionRequestState,other.id).state=='applied'


@pytest.mark.parametrize('change',['state','revision'])
def test_package_projection_changes_block(foundation_db,people,ready,successor,change,monkeypatch):
    # S3C reopen is deliberately unavailable. Inject a later observed projection
    # to exercise publication's current-snapshot gate without enabling reopen.
    db=foundation_db;p,rev,q,g=ready;original=db.get
    def get(cls,identity,*a,**kw):
        row=original(cls,identity,*a,**kw)
        if cls is DirectoratePackage and identity==p.id and kw.get('populate_existing'):
            set_committed_value(row,'state','returned') if change=='state' else set_committed_value(row,'current_revision',rev.revision-1)
        return row
    monkeypatch.setattr(db,'get',get);before=all_counts(db)
    rejects(409,lambda:publish(db,people,successor))
    assert all_counts(db)==before and db.get(RevisionRequestState,q.id).state=='editing'


@pytest.mark.parametrize('bad',['revision_hash','decision_revision','decision_hash','event_revision','event_hash'])
def test_snapshot_integrity_blocks(foundation_db,people,ready,successor,bad):
    db=foundation_db;p,rev,q,g=ready
    b=db.scalar(select(CandidatePackage).where(CandidatePackage.candidate_id==successor.id));d=db.get(PackageDecision,b.strategy_decision_id);e=db.get(WorkflowEvent,d.workflow_event_id)
    if bad=='revision_hash':set_committed_value(rev,'sha256','0'*64)
    elif bad=='decision_revision':set_committed_value(d,'package_revision_id',q.source_package_revision_id)
    elif bad=='decision_hash':set_committed_value(d,'snapshot_sha256','0'*64)
    else:
        context=json.loads(e.context_json);context['revision_id' if bad=='event_revision' else 'sha256']=99999 if bad=='event_revision' else '0'*64
        set_committed_value(e,'context_json',auth.encode(context))
    before=all_counts(db);rejects(409,lambda:publish(db,people,successor));assert all_counts(db)==before


def test_stale_predecessor_publish_has_no_writes(foundation_db,people,released,successor,monkeypatch):
    db=foundation_db;original=db.scalar
    def scalar(statement,*a,**kw):
        if 'report_releases.major DESC' in str(statement):return released.id+999
        return original(statement,*a,**kw)
    monkeypatch.setattr(db,'scalar',scalar);before=all_counts(db)
    rejects(409,lambda:publish(db,people,successor));assert all_counts(db)==before


def test_current_final_authority_reapproval(foundation_db,people,successor):
    db=foundation_db;x=people;c=successor
    auth.assign_final_authority(db,x['strategy'],c.organization_id,x['editor2'].id,'Yeni resmî nihai yetki');db.commit()
    before=all_counts(db);rejects(409,lambda:publish(db,x,c));assert all_counts(db)==before
    approve(db,x,c,'editor2');assert publish(db,x,c).minor==1


@pytest.mark.parametrize('failure',['report_notice','request_notice','request_recipient','artifact','lineage','applied_event'])
def test_publication_failure_rolls_back_everything(foundation_db,people,ready,successor,failure,monkeypatch):
    db=foundation_db;p,rev,q,g=ready;before=all_counts(db);state=db.get(RevisionRequestState,q.id);projection=db.get(ReportCandidateState,successor.id)
    versions=state.version,projection.version
    if failure=='request_notice':
        def fail(*a,**kw):raise RuntimeError('Mandatory request notification')
        monkeypatch.setattr(corrections,'notify',fail)
        with pytest.raises(RuntimeError):publish(db,people,successor)
        monkeypatch.undo()
    else:
        model={'report_notice':Notification,'request_recipient':NotificationRecipient,'artifact':ReportArtifact,'lineage':ReportReleaseSuccession,'applied_event':RevisionRequestEvent}[failure]
        def fail(mapper,connection,target):
            if failure=='request_recipient':
                action=connection.scalar(select(Notification.event_type).where(Notification.id==target.notification_id))
                if action!='revision_applied':return
            if failure=='applied_event' and target.to_state!='applied':return
            raise RuntimeError('Mandatory insert failed')
        event.listen(model,'before_insert',fail)
        try:
            with pytest.raises(RuntimeError):publish(db,people,successor)
        finally:event.remove(model,'before_insert',fail)
    db.expire_all()
    assert all_counts(db)==before and state.state=='editing' and projection.state=='final_approved'
    assert (state.version,projection.version)==versions
    assert db.scalar(select(ReportRelease).where(ReportRelease.candidate_id==successor.id)) is None
    assert publish(db,people,successor).minor==1


@pytest.mark.parametrize('bad',['actor','source','release','candidate','hash','grant','cycle'])
def test_applied_audit_forgery_rejected_by_database(foundation_db,people,ready,successor,bad,monkeypatch):
    db=foundation_db;original=corrections.history
    def history(db,actor,request,action,context,reason=''):
        if action=='revision_applied':
            context=dict(context)
            if bad=='actor':actor=people['user']
            elif bad=='source':context['predecessor_release_id']=99999
            else:context[{'release':'successor_release_id','candidate':'successor_candidate_id','hash':'successor_candidate_sha256','grant':'grant_id','cycle':'correction_cycle_id'}[bad]]= '0'*64 if bad=='hash' else 99999
        return original(db,actor,request,action,context,reason)
    monkeypatch.setattr(corrections,'history',history);before=all_counts(db)
    with pytest.raises(DBAPIError):publish(db,people,successor)
    db.expire_all();assert all_counts(db)==before and db.get(RevisionRequestState,ready[2].id).state=='editing'


def test_raw_state_update_without_publication_rejected(foundation_db,ready,successor):
    db=foundation_db;q=ready[2];before=all_counts(db)
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(text("UPDATE revision_request_states SET state='applied',version=version+1 WHERE request_id=:id"),{'id':q.id})
    assert all_counts(db)==before


def test_concurrent_publication_one_release_edge_no_orphans(foundation_db,people,ready,successor):
    db=foundation_db;c=successor;barrier=Barrier(2);version=db.get(ReportCandidateState,c.id).version;before=all_counts(db);db.commit()
    def attempt():
        with Session(db.bind,expire_on_commit=False) as other:
            actor=other.get(User,people['strategy'].id);barrier.wait()
            try:
                r=reports.publish(other,actor,c.organization_id,c.id,version,c.sha256);other.commit();return r.id
            except auth.HTTPException as exc:other.rollback();assert exc.status_code==409;return None
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:attempt(),range(2)))
    assert sum(r is not None for r in results)==1
    db.expire_all();assert db.scalar(select(func.count(ReportRelease.id)))==before[1]+1
    assert db.scalar(select(func.count(ReportReleaseSuccession.id)))==before[2]+1
    assert db.scalar(select(func.count(ReportArtifact.id)))==before[3]+1
    assert db.get(RevisionRequestState,ready[2].id).state=='applied'
    assert db.scalar(select(func.count(RevisionRequestEvent.id)).where(RevisionRequestEvent.to_state=='applied'))==1


@pytest.mark.parametrize('foundation_db',['597efbc82634'],indirect=True)
def test_populated_migration_preserves_history(foundation_db,people,released,ready,successor):
    db=foundation_db;before=sealed(db);state=db.get(RevisionRequestState,ready[2].id);version=state.version;db.commit()
    url=db.bind.url.render_as_string(hide_password=False)
    for _ in range(2):
        run=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True)
        assert run.returncode==0,run.stderr
    db.expire_all();assert_sealed(db,before);assert state.state=='editing' and state.version==version
    assert publish(db,people,successor).minor==1


def reapprove(db,x,p):
    act(db,x,p,'submit_to_director','user');act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')


def close(db,x,q,reason='Bu talep için net değişiklik uygulanmayacak'):
    state=db.get(RevisionRequestState,q.id)
    corrections.close_no_change(db,x['strategy'],q.id,state.version,reason);db.commit()


@pytest.mark.parametrize('bad',['unedited','roundtrip'])
def test_no_net_change_blocks_until_explicit_closure(foundation_db,people,released,bad):
    db=foundation_db;x=people;q=request(db,x,released);other=request(db,x,released,other=True)
    accept(db,x,q);accept(db,x,other);g=grant(db,x,q);h=grant(db,x,other)
    edit(db,x,g)
    if bad=='roundtrip':
        edit(db,x,h,other=True,value='Geçici açıklama');edit(db,x,h,other=True,value='Hedef gerçekleşti')
    p=db.get(DirectoratePackage,db.get(RevisionCorrectionCycle,g.cycle_id).package_id);reapprove(db,x,p)
    c=assemble(db,x,released,p);db.commit();review(db,x,c);approve(db,x,c);before=all_counts(db)
    assert not db.scalar(select(func.civensa_successor_request_participates(c.id,other.id)))
    with pytest.raises(DBAPIError,match='Unresolved or unedited'):
        with db.begin_nested():raw_release(db,x,c)
    rejects(409,lambda:publish(db,x,c));assert all_counts(db)==before
    assert db.get(RevisionRequestState,other.id).state=='editing'
    close(db,x,other);assert db.get(RevisionRequestState,other.id).state=='closed_no_change'
    publication=publish(db,x,c);assert publication.minor==1
    assert db.get(RevisionRequestState,q.id).state=='applied'
    closure=db.scalar(select(RevisionRequestEvent).where(RevisionRequestEvent.request_id==other.id,RevisionRequestEvent.to_state=='closed_no_change'))
    audit=db.get(WorkflowEvent,closure.workflow_event_id)
    assert audit.reason and audit.actor_user_id==x['strategy'].id


@pytest.mark.parametrize('stage',['accepted','editing'])
def test_closed_no_change_strategy_reason_terminal(foundation_db,people,released,stage):
    db=foundation_db;x=people;q=request(db,x,released);accept(db,x,q)
    if stage=='editing':grant(db,x,q)
    state=db.get(RevisionRequestState,q.id);before=all_counts(db)
    rejects(403,lambda:corrections.close_no_change(db,x['user'],q.id,state.version,'Gerekçe'))
    rejects(422,lambda:corrections.close_no_change(db,x['strategy'],q.id,state.version,' '))
    assert all_counts(db)==before
    close(db,x,q);assert state.state=='closed_no_change'
    rejects(409,lambda:corrections.close_no_change(db,x['strategy'],q.id,state.version,'Tekrar'))
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(text("UPDATE revision_request_states SET state='editing',version=version+1 WHERE request_id=:id"),{'id':q.id})


@pytest.mark.parametrize('bad',['actor','reason','audit'])
def test_raw_closed_no_change_guard(foundation_db,people,released,bad):
    db=foundation_db;x=people;q=request(db,x,released);accept(db,x,q);state=db.get(RevisionRequestState,q.id)
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            if bad!='audit':
                e=corrections.history(db,x['user'] if bad=='actor' else x['strategy'],q,'revision_closed_no_change',
                    {'from_state':'accepted','to_state':'closed_no_change','version':state.version+1},'' if bad=='reason' else 'Gerekçe')
                db.add(RevisionRequestEvent(request_id=q.id,workflow_event_id=e.id,from_state='accepted',to_state='closed_no_change',version=state.version+1));db.flush()
            db.execute(text("UPDATE revision_request_states SET state='closed_no_change',version=version+1 WHERE request_id=:id"),{'id':q.id})
    assert state.state=='accepted'


def test_closure_notification_failure_atomic(foundation_db,people,released,monkeypatch):
    db=foundation_db;q=request(db,people,released);accept(db,people,q);before=all_counts(db)
    def fail(*a,**kw):raise RuntimeError('Zorunlu bildirim')
    monkeypatch.setattr(corrections,'notify',fail)
    with pytest.raises(RuntimeError):close(db,people,q)
    db.expire_all();assert all_counts(db)==before and db.get(RevisionRequestState,q.id).state=='accepted'


def test_applied_notifications_without_active_director(foundation_db,people,ready,successor):
    db=foundation_db;x=people
    membership=auth.active_membership(db,x['director'].id,successor.organization_id,x['department'].id)
    auth.deactivate_membership(db,x['strategy'],membership.id,'Görevlendirme sona erdi');db.commit()
    assert publish(db,x,successor).minor==1
    assert db.get(RevisionRequestState,ready[2].id).state=='applied'


def test_publish_locks_organization_first_no_department_package(foundation_db,people,successor):
    db=foundation_db;locks=[]
    def capture(conn,cursor,statement,parameters,context,executemany):
        if 'FOR UPDATE' in statement:locks.append(statement)
    event.listen(db.bind,'before_cursor_execute',capture)
    try:publish(db,people,successor)
    finally:event.remove(db.bind,'before_cursor_execute',capture)
    assert locks and 'FROM organizations' in locks[0]
    assert not any('FROM departments' in sql or 'FROM directorate_packages' in sql for sql in locks)


def test_exact_cycle_set_rechecked(foundation_db,people,successor,monkeypatch):
    db=foundation_db;original=db.scalars
    def scalars(statement,*a,**kw):
        result=original(statement,*a,**kw)
        if str(statement).startswith('SELECT revision_correction_cycles.id'):
            return list(result)+[99999]
        return result
    monkeypatch.setattr(db,'scalars',scalars);before=all_counts(db)
    rejects(409,lambda:publish(db,people,successor));assert all_counts(db)==before


def raw_release(db,x,c,major=1,minor=1):
    state=db.get(ReportCandidateState,c.id)
    decision=db.scalar(select(ReportDecision).where(ReportDecision.candidate_id==c.id,ReportDecision.action=='final_approve').order_by(ReportDecision.id.desc()))
    e=reports.event_notice(db,x['strategy'],c,'publish_report',state.state,'published',state.version+1)
    r=ReportRelease(candidate_id=c.id,final_decision_id=decision.id,organization_id=c.organization_id,resource_scope=c.resource_scope,report_key=c.report_key,
        major=major,minor=minor,activity_approval_id=decision.activity_approval_id,workflow_event_id=e.id)
    db.add(r);db.flush();return r


def test_deferred_release_requires_lineage(foundation_db,people,successor):
    db=foundation_db;before=all_counts(db)
    with pytest.raises(DBAPIError,match='exactly one immutable succession'):
        with db.begin_nested():
            raw_release(db,people,successor)
            db.execute(text('SET CONSTRAINTS activity_release_completion_guard IMMEDIATE'))
    assert all_counts(db)==before
    deferred=db.execute(text("SELECT tgdeferrable,tginitdeferred FROM pg_trigger WHERE tgname='activity_release_completion_guard' AND tgrelid='report_releases'::regclass")).one()
    assert tuple(deferred)==(True,True)


@pytest.mark.parametrize('missing',['release','lineage'])
def test_published_projection_requires_release_and_lineage(foundation_db,people,successor,missing):
    db=foundation_db;state=db.get(ReportCandidateState,successor.id);before=all_counts(db)
    with pytest.raises(DBAPIError,match='requires exact release'):
        with db.begin_nested():
            if missing=='lineage':raw_release(db,people,successor)
            else:reports.event_notice(db,people['strategy'],successor,'publish_report',state.state,'published',state.version+1)
            db.execute(update(ReportCandidateState).where(ReportCandidateState.candidate_id==successor.id).values(state='published',version=state.version+1))
    assert all_counts(db)==before


@pytest.mark.parametrize('version',[(1,0),(1,2),(2,1)])
def test_raw_wrong_successor_version_rejected(foundation_db,people,successor,version):
    db=foundation_db;before=all_counts(db)
    with pytest.raises(DBAPIError):
        with db.begin_nested():raw_release(db,people,successor,*version)
    assert all_counts(db)==before


@pytest.mark.parametrize('version',[(1,1),(2,0)])
def test_raw_initial_version_must_be_one_zero(foundation_db,people,candidate,version):
    db=foundation_db;review(db,people,candidate);approve(db,people,candidate);before=all_counts(db)
    with pytest.raises(DBAPIError,match='explicit lineage'):
        with db.begin_nested():raw_release(db,people,candidate,*version)
    assert all_counts(db)==before


def test_raw_generic_activity_candidate_bypass_rejected(foundation_db,people,released):
    db=foundation_db;parent=db.get(ReportCandidate,released.candidate_id);before=all_counts(db)
    copy={col.name:getattr(parent,col.name) for col in ReportCandidate.__table__.columns if col.name not in ('id','created_at')}
    copy.update(sequence=parent.sequence+1,predecessor_candidate_id=parent.id)
    with pytest.raises(DBAPIError,match='explicit successor assembly'):
        with db.begin_nested():db.execute(ReportCandidate.__table__.insert().values(**copy))
    assert all_counts(db)==before


def test_raw_generic_release_bypass_rejected(foundation_db,people,released):
    db=foundation_db;parent=db.get(ReportCandidate,released.candidate_id);before=all_counts(db)
    # Reusing an initial-style candidate must fail before uniqueness/commit too.
    with pytest.raises(DBAPIError,match='explicit lineage'):
        with db.begin_nested():raw_release(db,people,parent,1,0)
    assert all_counts(db)==before


@pytest.mark.parametrize('foundation_db',['597efbc82634'],indirect=True)
def test_successor_minor_uses_existing_predecessor_version(foundation_db,people,candidate):
    """Seed a historical 1.1 boundary; do not enable post-1.1 re-correction."""
    db=foundation_db;x=people;review(db,x,candidate);approve(db,x,candidate)
    def seed_version(mapper,connection,target):target.minor=1
    event.listen(ReportRelease,'before_insert',seed_version)
    try:predecessor=publish(db,x,candidate)
    finally:event.remove(ReportRelease,'before_insert',seed_version)
    # This is a pre-S3B published fixture, not a 1.0 correction/release chain.
    url=db.bind.url.render_as_string(hide_password=False)
    run=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    p,rev,q,g=ready.__wrapped__(db,x,predecessor)
    c=assemble(db,x,predecessor,p);db.commit();review(db,x,c);approve(db,x,c)
    successor=publish(db,x,c)
    assert (predecessor.major,predecessor.minor,successor.major,successor.minor)==(1,1,1,2)
    assert json.loads(reports.verify_artifact(db,successor).content_json)['version']=='1.2'
    assert reports.verify_artifact(db,successor).object_version=='1.0'
    edge=db.scalar(select(ReportReleaseSuccession).where(ReportReleaseSuccession.successor_release_id==successor.id))
    assert edge.predecessor_release_id==predecessor.id


def test_net_change_needs_exact_request_grant_provenance(foundation_db,people,released):
    db=foundation_db;x=people;first=request(db,x,released);other=request(db,x,released,other=True)
    accept(db,x,first);accept(db,x,other);g=grant(db,x,first);h=grant(db,x,other)
    edit(db,x,g);close(db,x,first)
    same=request(db,x,released);accept(db,x,same);unmodified=grant(db,x,same)
    rev=edit(db,x,h,other=True,value='Kalıcı açıklama');p=db.get(DirectoratePackage,rev.package_id);reapprove(db,x,p)
    c=assemble(db,x,released,p);db.commit();review(db,x,c);approve(db,x,c)
    cycle=db.get(RevisionCorrectionCycle,unmodified.cycle_id)
    assert corrections.value_at(json.loads(db.get(PackageRevision,cycle.source_package_revision_id).content_json),['entries',0,'value'])!=corrections.value_at(json.loads(rev.content_json),['entries',0,'value'])
    # A fabricated edit recorded AFTER an already-existing revision is not
    # evidence that this new request/grant caused that revision.
    original=db.scalar(select(WorkflowEvent).where(WorkflowEvent.event_type=='correction_edit',WorkflowEvent.resource_id==str(first.id)).order_by(WorkflowEvent.id))
    proof=json.loads(original.context_json);proof['grant_id']=unmodified.id
    forged=corrections.history(db,x['user'],same,'correction_edit',proof,'Sahte sonradan eklenen köken')
    field=db.scalar(select(FieldChangeEvent).where(FieldChangeEvent.workflow_event_id==original.id,FieldChangeEvent.field_key.like('%value%')))
    db.add(FieldChangeEvent(workflow_event_id=forged.id,revision_request_id=same.id,field_key=field.field_key,field_type=field.field_type,previous_json=field.previous_json,new_json=field.new_json));db.commit()
    assert not corrections.has_net_correction(db,same,unmodified,cycle,rev)
    assert not db.scalar(select(func.civensa_successor_request_participates(c.id,same.id)))
    rejects(409,lambda:publish(db,x,c))
    with pytest.raises(DBAPIError,match='Unresolved or unedited'):
        with db.begin_nested():raw_release(db,x,c)


def test_derived_deviation_alone_never_counts(foundation_db,people,released):
    db=foundation_db;x=people;q=request(db,x,released);accept(db,x,q);g=grant(db,x,q)
    edit(db,x,g,value='2.50');rev=edit(db,x,g,value='1.75');cycle=db.get(RevisionCorrectionCycle,g.cycle_id)
    # A derived-only observation cannot satisfy the granted value path, even
    # though this exact grant has immutable correction_edit history.
    payload=json.loads(rev.content_json);payload['entries'][0]['deviation']['delta']='99.00'
    set_committed_value(rev,'content_json',auth.encode(payload))
    assert not corrections.has_net_correction(db,q,g,cycle,rev)


def test_nested_granted_evidence_path_has_net_provenance(foundation_db,people,released):
    db=foundation_db;x=people
    q=corrections.create_request(db,x['user'],released.id,x['department'].id,[{'path':['entries',0,'evidence']}],'Kaynak adı düzeltmesi');db.commit()
    accept(db,x,q);g=grant(db,x,q)
    cycle=db.get(RevisionCorrectionCycle,g.cycle_id);p=db.get(DirectoratePackage,cycle.package_id);current=reports.packages.revision(db,p)
    evidence=json.loads(current.content_json)['entries'][0]['evidence'];evidence[0]['title']='Doğru defter adı'
    rev=corrections.edit_under_grant(db,x['user'],g.id,p.version,current.sha256,[{'path':['entries',0,'evidence'],'value':evidence}],'');db.commit()
    reapprove(db,x,p);c=assemble(db,x,released,p);db.commit();review(db,x,c);approve(db,x,c)
    assert corrections.has_net_correction(db,q,g,cycle,rev)
    assert db.scalar(select(func.civensa_successor_request_participates(c.id,q.id)))
    assert publish(db,x,c).minor==1


def test_held_package_lock_does_not_block_successor_publish(foundation_db,people,successor,ready):
    """NO KEY UPDATE allows FK key-share, but would block any added UPDATE lock."""
    db=foundation_db;c=successor;pid=ready[0].id;version=db.get(ReportCandidateState,c.id).version;db.commit()
    with Session(db.bind) as holder:
        holder.execute(text('SELECT id FROM directorate_packages WHERE id=:id FOR NO KEY UPDATE'),{'id':pid})
        def attempt():
            with Session(db.bind,expire_on_commit=False) as other:
                other.execute(text("SET LOCAL lock_timeout='1500ms'"))
                r=reports.publish(other,other.get(User,people['strategy'].id),c.organization_id,c.id,version,c.sha256)
                other.commit();return r.minor
        with ThreadPoolExecutor(max_workers=1) as pool:assert pool.submit(attempt).result(timeout=10)==1


def test_closed_work_does_not_enable_final_return_reassembly(foundation_db,people,successor,ready):
    db=foundation_db;p=ready[0];before=all_counts(db)
    rejects(403,lambda:act(db,people,p,'director_reopen','director',reason='S3C kapsamı'))
    assert all_counts(db)==before
