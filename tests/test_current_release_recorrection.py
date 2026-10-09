"""S3C-1 only: migrated PostgreSQL, exact re-correction opening after 1.1."""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import select,func,text,event,update,cast
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session
from sqlalchemy.exc import DBAPIError
from app.models import *
from app import revision_workflow_service as corrections, report_workflow_service as reports, authorization_service as auth
from tests.test_authorization_foundation import foundation_db,ROOT
from tests.test_materialized_successor import people,package,ready,assemble,sealed,assert_sealed
from tests.test_report_workflow import approved,candidate,review,approve,publish,rejects
from tests.test_revision_workflow import released,request,accept,grant,edit
from tests.test_successor_publication import successor,all_counts
from tests.test_package_workflow import act
pytestmark=pytest.mark.postgres


@pytest.fixture
def one_one(foundation_db,people,successor):
    return publish(foundation_db,people,successor)


def correction_history(db):
    return {cls:{row.id:tuple(getattr(row,col.name) for col in cls.__table__.columns) for row in db.scalars(select(cls))}
        for cls in (RevisionCorrectionCycle,RevisionEditGrant,RevisionRequest,RevisionRequestEvent)}


def assert_history(db,before):
    for cls,rows in before.items():
        for rid,values in rows.items():assert tuple(getattr(db.get(cls,rid),col.name) for col in cls.__table__.columns)==values


def test_exact_one_one_cycle_reapproval_and_one_two_publication(foundation_db,people,released,ready,one_one):
    db=foundation_db;x=people;r=one_one;p,old_revision,old_request,old_grant=ready
    before=sealed(db);history=correction_history(db)
    binding=db.scalar(select(CandidatePackage).where(CandidatePackage.candidate_id==r.candidate_id))
    q=request(db,x,r,'director');assert q.source_package_revision_id==binding.package_revision_id==old_revision.id
    accept(db,x,q);g=grant(db,x,q,key='director');cycle=db.get(RevisionCorrectionCycle,g.cycle_id)
    source=db.get(PackageRevision,cycle.source_package_revision_id);opening=db.get(PackageRevision,cycle.opening_revision_id)
    assert cycle.id!=old_grant.cycle_id and cycle.source_release_id==r.id and cycle.package_id==p.id
    assert source.id==binding.package_revision_id and opening.previous_revision_id==source.id
    assert opening.revision==source.revision+1 and opening.content_json==source.content_json and opening.sha256==source.sha256
    assert (p.state,p.current_revision)==('returned',opening.revision)
    assert corrections.correction_context(db,p).id==cycle.id
    revised=edit(db,x,g,'director',value='3.50',reason='1.1 yayını kaynak düzeltmesi')
    act(db,x,p,'submit_to_director','director');act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    assert p.state=='strategy_approved' and revised.previous_revision_id==opening.id
    # The existing S3A/S3B publication path is unchanged, now reachable by exact
    # new-cycle provenance. No final-return/reassembly or grant renewal.
    c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c);next_release=publish(db,x,c)
    assert (next_release.major,next_release.minor)==(1,2)
    edge=db.scalar(select(ReportReleaseSuccession).where(ReportReleaseSuccession.successor_release_id==next_release.id))
    assert edge.predecessor_release_id==r.id
    assert reports.verify_artifact(db,next_release).object_version=='1.0'
    assert json.loads(reports.verify_artifact(db,next_release).content_json)['version']=='1.2'
    assert db.get(RevisionRequestState,q.id).state=='applied'
    assert_history(db,history);assert_sealed(db,before)
    assert db.get(RevisionRequestState,old_request.id).state=='applied'
    rejects(409,lambda:corrections.current_source(db,released.id))


def test_context_no_historical_fallback(foundation_db,people,ready,one_one):
    db=foundation_db;p,rev,q,g=ready;before=all_counts(db)
    for validate in (True,False):
        with pytest.raises(auth.HTTPException) as caught:corrections.correction_context(db,p,validate_grant=validate)
        assert caught.value.status_code==409 and 'güncel sürüm için yeni düzeltme talebi' in caught.value.detail
    rejects(409,lambda:act(db,people,p,'submit_to_director','director'))
    assert all_counts(db)==before


@pytest.mark.parametrize('new_cycle',[False,True])
def test_old_grant_and_request_never_reactivate(foundation_db,people,released,ready,one_one,new_cycle):
    db=foundation_db;x=people;p,rev,q,g=ready
    old_version=p.version;old_hash=reports.packages.revision(db,p).sha256
    if new_cycle:
        fresh=request(db,x,one_one);accept(db,x,fresh);grant(db,x,fresh)
    before=all_counts(db)
    rejects(409,lambda:reports.packages.transition(db,x['director'],p.id,'submit_to_director',old_version,old_hash))
    rejects(409,lambda:edit(db,x,g,'director',value='4.50',reason='Eski izin'))
    rejects(409,lambda:corrections.open_grant(db,x['strategy'],q.id,db.get(RevisionRequestState,q.id).version,
        corrections.paths(q),[x['user'].id],auth.server_now(db),auth.server_now(db),'Eski talep'))
    assert all_counts(db)==before
    # An old source copy with a forged old correction_opened audit cannot bypass
    # either stale protection or the current-cycle grant protocol.
    old_source=db.get(PackageRevision,q.source_package_revision_id)
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            corrections.history(db,x['strategy'],q,'correction_opened',{'package_id':p.id,'source_package_revision_id':old_source.id},'Eski yayın')
            db.execute(PackageRevision.__table__.insert().values(package_id=p.id,revision=p.current_revision+1,
                previous_revision_id=old_source.id,content_json=old_source.content_json,sha256=old_source.sha256,created_by=x['strategy'].id,reason='Eski'))
    assert all_counts(db)==before
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            current=reports.packages.revision(db,p)
            e=reports.packages.history_event(db,x['director'],p,'submit_to_director',{'from_state':p.state,'to_state':'director_review',
                'expected_version':p.version,'revision_id':current.id,'sha256':current.sha256,'delegation_id':None,'correction_cycle_id':g.cycle_id})
            db.add(PackageDecision(package_revision_id=current.id,snapshot_sha256=current.sha256,action='submit_to_director',from_state=p.state,to_state='director_review',workflow_event_id=e.id));db.flush()
            db.execute(text("UPDATE directorate_packages SET state='director_review',version=version+1 WHERE id=:id"),{'id':p.id})
    assert all_counts(db)==before
    with pytest.raises(DBAPIError,match='Stale correction cycle|Missing active scoped correction authorization'):
        with db.begin_nested():
            current=reports.packages.revision(db,p);payload=json.loads(current.content_json)
            payload['entries'][0]['value']='4.50';reports.packages.validate_actual(payload['entries'][0]);raw=auth.encode(payload)
            e=corrections.history(db,x['director'],q,'correction_edit',{'grant_id':g.id,'membership_id':json.loads(g.membership_ids_json)[0],
                'package_id':p.id,'previous_revision_id':current.id,'next_revision':current.revision+1,'next_sha256':reports.contract.digest(raw)},'Eski izinle sahte SQL düzeltme')
            changes=db.scalars(select(func.civensa_revision_changes(cast(current.content_json,JSONB),cast(raw,JSONB)))).all()
            for path in changes:
                db.add(FieldChangeEvent(workflow_event_id=e.id,revision_request_id=q.id,field_key=auth.encode(path),field_type='json',
                    previous_json=auth.encode(corrections.value_at(json.loads(current.content_json),path)),new_json=auth.encode(corrections.value_at(payload,path))))
            db.flush()
            insert_opening(db,x,p,current,content_json=raw,sha256=reports.contract.digest(raw),created_by=x['director'].id)
    assert all_counts(db)==before


def opening_protocol(db,x,r,p,q,*,event_source=None,actor=None):
    source=db.get(PackageRevision,q.source_package_revision_id)
    proof=corrections.history(db,actor or x['strategy'],q,'correction_opened',
        {'package_id':p.id,'source_package_revision_id':(event_source or source).id},'Yeni yayının düzeltme açılışı')
    return source,proof


def insert_opening(db,x,p,source,**changes):
    values=dict(package_id=p.id,revision=source.revision+1,previous_revision_id=source.id,
        content_json=source.content_json,sha256=source.sha256,created_by=x['strategy'].id,reason='Yeni açılış')
    values.update(changes)
    return db.scalar(PackageRevision.__table__.insert().values(**values).returning(PackageRevision.id))


@pytest.mark.parametrize('bad',['old_source','wrong_source','content','hash','revision','no_accepted','no_event','actor','event_source','existing_cycle'])
def test_forged_one_one_opening_fails_closed(foundation_db,people,released,ready,one_one,bad):
    db=foundation_db;x=people;p,rev,old_request,old_grant=ready;q=request(db,x,one_one)
    if bad!='no_accepted':accept(db,x,q)
    source=db.get(PackageRevision,q.source_package_revision_id)
    if bad=='existing_cycle':grant(db,x,q)
    before=all_counts(db);revision_count=db.scalar(select(func.count(PackageRevision.id)))
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            if bad!='no_event':opening_protocol(db,x,one_one,p,q,actor=x['user'] if bad=='actor' else None,
                event_source=db.get(PackageRevision,old_request.source_package_revision_id) if bad=='event_source' else None)
            overrides={}
            if bad=='old_source':source=db.get(PackageRevision,old_request.source_package_revision_id)
            elif bad=='wrong_source':source=db.get(PackageRevision,db.get(RevisionCorrectionCycle,old_grant.cycle_id).opening_revision_id)
            elif bad=='content':
                payload=json.loads(source.content_json);payload['entries'][0]['explanation']='Sahte açılış değişikliği'
                overrides['content_json']=auth.encode(payload);overrides['sha256']=reports.contract.digest(overrides['content_json'])
            elif bad=='hash':overrides['sha256']='0'*64
            elif bad=='revision':overrides['revision']=source.revision+2
            insert_opening(db,x,p,source,**overrides)
    assert all_counts(db)==before and db.scalar(select(func.count(PackageRevision.id)))==revision_count


@pytest.mark.parametrize('projection',[False,True])
def test_opening_without_exact_cycle_fails_at_commit(foundation_db,people,ready,one_one,projection):
    db=foundation_db;x=people;p=ready[0];q=request(db,x,one_one);accept(db,x,q)
    before=all_counts(db);revision_count=db.scalar(select(func.count(PackageRevision.id)));version=p.version;current=p.current_revision
    source,proof=opening_protocol(db,x,one_one,p,q);rid=insert_opening(db,x,p,source)
    if projection:
        db.execute(text("UPDATE directorate_packages SET state='returned',version=version+1,current_revision=current_revision+1 WHERE id=:id"),{'id':p.id})
    # Immediate statement guards admit the complete protocol; commit must reject
    # the missing cycle even if the projection was never moved.
    with pytest.raises(DBAPIError,match='requires its exact current-release cycle at commit'):db.commit()
    db.rollback();db.expire_all()
    assert all_counts(db)==before and db.scalar(select(func.count(PackageRevision.id)))==revision_count
    assert (p.state,p.version,p.current_revision)==('strategy_approved',version,current)
    assert db.get(PackageRevision,rid) is None


def test_raw_complete_opening_protocol_can_commit(foundation_db,people,ready,one_one):
    db=foundation_db;x=people;p=ready[0];q=request(db,x,one_one);accept(db,x,q)
    source,proof=opening_protocol(db,x,one_one,p,q);rid=insert_opening(db,x,p,source)
    db.execute(text("UPDATE directorate_packages SET state='returned',version=version+1,current_revision=current_revision+1 WHERE id=:id"),{'id':p.id})
    cycle=RevisionCorrectionCycle(source_release_id=one_one.id,package_id=p.id,source_package_revision_id=source.id,opening_revision_id=rid,workflow_event_id=proof.id)
    db.add(cycle);db.commit();db.refresh(p)
    assert corrections.correction_context(db,p,validate_grant=False).id==cycle.id
    rejects(409,lambda:corrections.correction_context(db,p))


def test_shared_cycle_nonoverlap_and_overlap_rejection(foundation_db,people,ready,one_one):
    db=foundation_db;x=people;p=ready[0];q=request(db,x,one_one);other=request(db,x,one_one,other=True)
    accept(db,x,q);accept(db,x,other);g=grant(db,x,q);h=grant(db,x,other)
    assert g.cycle_id==h.cycle_id
    assert db.scalar(select(func.count(RevisionCorrectionCycle.id)).where(RevisionCorrectionCycle.source_release_id==one_one.id,RevisionCorrectionCycle.package_id==p.id))==1
    overlapping=request(db,x,one_one)
    rejects(409,lambda:accept(db,x,overlapping))
    edit(db,x,g,value='3.50');edit(db,x,h,other=True,value='1.1 yeni açıklama')


def test_current_context_and_second_opening_organization_first(foundation_db,people,ready,one_one):
    db=foundation_db;x=people;q=request(db,x,one_one);accept(db,x,q);locks=[]
    def capture(conn,cursor,statement,parameters,context,executemany):
        if 'FOR UPDATE' in statement:locks.append(statement.lower())
    event.listen(db.bind,'before_cursor_execute',capture)
    try:
        g=grant(db,x,q);cycle=corrections.correction_context(db,ready[0])
    finally:event.remove(db.bind,'before_cursor_execute',capture)
    assert cycle.id==g.cycle_id and locks and 'from organizations' in locks[0]
    assert db.execute(text("SELECT count(*) FROM pg_trigger WHERE tgname IN ('correction_opening_revision_complete','correction_opening_projection_complete') AND tgdeferrable AND tginitdeferred AND tgrelid IN ('package_revisions'::regclass,'directorate_packages'::regclass)")).scalar_one()==2


@pytest.mark.parametrize('foundation_db',['6a8fcbd93745'],indirect=True)
def test_populated_one_one_migration_preserves_history(foundation_db,people,ready,one_one):
    db=foundation_db;x=people;history=correction_history(db);before=sealed(db);db.commit()
    url=db.bind.url.render_as_string(hide_password=False)
    for _ in range(2):
        run=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True)
        assert run.returncode==0,run.stderr
    db.expire_all();assert_history(db,history);assert_sealed(db,before)
    q=request(db,x,one_one);accept(db,x,q);g=grant(db,x,q)
    assert db.get(RevisionCorrectionCycle,g.cycle_id).source_release_id==one_one.id


def test_two_current_requests_concurrently_share_exact_cycle(foundation_db,people,ready,one_one):
    db=foundation_db;x=people;q=request(db,x,one_one);h=request(db,x,one_one,other=True);accept(db,x,q);accept(db,x,h)
    before=db.scalar(select(func.count(PackageRevision.id)));db.commit();barrier=Barrier(2)
    def attempt(rid):
        with Session(db.bind,expire_on_commit=False) as other:
            actor=other.get(User,x['strategy'].id);req=other.get(RevisionRequest,rid)
            state=other.get(RevisionRequestState,rid);m=auth.active_membership(other,x['user'].id,req.organization_id,req.department_id)
            now=auth.server_now(other);barrier.wait()
            from datetime import timedelta
            g=corrections.open_grant(other,actor,rid,state.version,corrections.paths(req),[m.id],now-timedelta(minutes=1),now+timedelta(hours=1),'Eşzamanlı izin');other.commit();return g.cycle_id
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(attempt,[q.id,h.id]))
    assert results[0]==results[1]
    db.expire_all();assert db.scalar(select(func.count(PackageRevision.id)))==before+1
    assert db.scalar(select(func.count(RevisionCorrectionCycle.id)).where(RevisionCorrectionCycle.source_release_id==one_one.id))==1


@pytest.mark.parametrize('change',['state','no_advance'])
def test_projection_opening_is_only_approved_to_returned_copy(foundation_db,people,ready,one_one,change):
    db=foundation_db;x=people;p=ready[0];q=request(db,x,one_one);accept(db,x,q);before=all_counts(db)
    with pytest.raises(DBAPIError,match='Stale correction cycle'):
        with db.begin_nested():
            source,proof=opening_protocol(db,x,one_one,p,q);insert_opening(db,x,p,source)
            db.execute(text("UPDATE directorate_packages SET state=:state,version=version+1,current_revision=current_revision+:advance WHERE id=:id"),
                {'id':p.id,'state':'director_review' if change=='state' else 'returned','advance':0 if change=='no_advance' else 1})
    assert all_counts(db)==before


def test_opening_completion_survives_atomic_reapproval_and_publication(foundation_db,people,ready,one_one):
    """Deferred opening checks bind insertion-time source, not commit-time state."""
    from datetime import timedelta
    db=foundation_db;x=people;p=ready[0];q=request(db,x,one_one,'director');accept(db,x,q)
    now=auth.server_now(db);member=auth.active_membership(db,x['director'].id,q.organization_id,q.department_id)
    g=corrections.open_grant(db,x['strategy'],q.id,db.get(RevisionRequestState,q.id).version,corrections.paths(q),[member.id],
        now-timedelta(minutes=1),now+timedelta(hours=1),'Tek atomik düzeltme')
    source=reports.packages.revision(db,p)
    corrections.edit_under_grant(db,x['director'],g.id,p.version,source.sha256,[{'path':['entries',0,'value'],'value':'3.50'}],'Kaynak düzeltmesi')
    for action,actor in [('submit_to_director',x['director']),('director_approve',x['director']),('strategy_approve',x['strategy'])]:
        reports.packages.transition(db,actor,p.id,action,p.version,reports.packages.revision(db,p).sha256)
    c=assemble(db,x,one_one,p)
    projection=db.get(ReportCandidateState,c.id)
    reports.request_final_review(db,x['strategy'],c.organization_id,c.id,projection.version,c.sha256)
    reports.final_decision(db,x['director'],c.organization_id,c.id,'final_approve',projection.version,c.sha256)
    r=reports.publish(db,x['strategy'],c.organization_id,c.id,projection.version,c.sha256)
    db.commit()
    assert r.minor==2 and db.get(RevisionRequestState,q.id).state=='applied'
    assert db.get(RevisionCorrectionCycle,g.cycle_id).source_release_id==one_one.id
    assert corrections.current_source(db,r.id)[0].id==r.id
