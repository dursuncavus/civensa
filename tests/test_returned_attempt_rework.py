"""S3C-2: migrated PostgreSQL attempt history, reopen, renewal and races."""
import json
import os
import subprocess
import sys
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import select,func,text,event
from sqlalchemy.orm import Session
from sqlalchemy.exc import DBAPIError
from app.models import *
from app import report_workflow_service as reports, revision_workflow_service as corrections, authorization_service as auth
from tests.test_authorization_foundation import foundation_db,ROOT
from tests.test_materialized_successor import people,package,ready,assemble,sealed,assert_sealed,counts
from tests.test_report_workflow import approved,candidate,review,approve,publish,rejects
from tests.test_revision_workflow import released,request,accept,grant,edit
from tests.test_package_workflow import act
from tests.test_successor_publication import successor,raw_release
from tests.test_current_release_recorrection import opening_protocol,insert_opening
pytestmark=pytest.mark.postgres


def return_attempt(db,x,c):
    state=db.get(ReportCandidateState,c.id)
    reports.final_decision(db,x['director'],c.organization_id,c.id,'final_return',state.version,c.sha256,'Nihai kaynak incelemesi');db.commit()
    return c


@pytest.fixture
def returned(foundation_db,people,released,ready):
    db=foundation_db;c=assemble(db,people,released,ready[0]);db.commit();review(db,people,c)
    return return_attempt(db,people,c)


def reassemble(db,x,r,p):
    c=assemble(db,x,r,p);db.commit();return c


def reapprove(db,x,p):
    act(db,x,p,'submit_to_director','director');act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')


def renewal(db,x,g,paths=None):
    now=auth.server_now(db)
    n=corrections.renew_grant(db,x['strategy'],g.id,paths or json.loads(g.paths_json),now-timedelta(seconds=1),now+timedelta(hours=1),'Yeniden inceleme izni');db.commit();return n


@pytest.fixture
def expired_returned(foundation_db,people,released):
    db=foundation_db;x=people;q=request(db,x,released,'director');accept(db,x,q)
    now=auth.server_now(db);m=auth.active_membership(db,x['director'].id,q.organization_id,q.department_id)
    g=corrections.open_grant(db,x['strategy'],q.id,1,corrections.paths(q),[m.id],now-timedelta(seconds=1),now+timedelta(seconds=4),'Kısa asli izin');db.commit()
    corrected=edit(db,x,g,'director',reason='İlk düzeltme');p=db.get(DirectoratePackage,corrected.package_id);reapprove(db,x,p)
    c=reassemble(db,x,released,p);review(db,x,c);return_attempt(db,x,c)
    remaining=max(0,(g.end_at-auth.server_now(db)).total_seconds());db.execute(text('SELECT pg_sleep(:delay)'),{'delay':remaining+0.02});db.commit()
    return p,q,g,c


def test_happy_return_reopen_renew_edit_publish(foundation_db,people,released,expired_returned):
    db=foundation_db;x=people;p,q,g,a=expired_returned;before=sealed(db);original=tuple(getattr(g,c.name) for c in g.__table__.columns)
    cycle=db.get(RevisionCorrectionCycle,g.cycle_id);old=reports.packages.revision(db,p)
    act(db,x,p,'strategy_reopen','strategy',reason='Nihai iade sonrası kaynak düzeltmesi')
    copy=reports.packages.revision(db,p)
    assert copy.previous_revision_id==old.id and copy.content_json==old.content_json and copy.sha256==old.sha256
    n=renewal(db,x,g);edit(db,x,g,'director',value='3.50',reason='İade sonrası gerçek değişiklik');reapprove(db,x,p)
    b=reassemble(db,x,released,p);m=json.loads(b.manifest_json)
    assert b.predecessor_candidate_id==released.candidate_id and b.sequence==a.sequence+1
    assert (m['reworks_candidate_id'],m['reworks_candidate_sha256'])==(a.id,a.sha256)
    assert db.get(ActivityReportRevision,b.activity_revision_id).previous_revision_id==a.activity_revision_id
    review(db,x,b);approve(db,x,b);r=publish(db,x,b)
    edge=db.scalar(select(ReportReleaseSuccession).where(ReportReleaseSuccession.successor_release_id==r.id))
    assert (r.major,r.minor)==(1,1) and edge.predecessor_release_id==released.id
    assert db.scalar(select(func.count(ReportRelease.id)).where(ReportRelease.candidate_id==a.id))==0
    assert db.get(RevisionCorrectionCycle,g.cycle_id).id==cycle.id
    assert tuple(getattr(g,c.name) for c in g.__table__.columns)==original
    assert_sealed(db,before);reports.verify(db,a);reports.verify_artifact(db,released)
    e=db.scalar(select(WorkflowEvent).where(WorkflowEvent.event_type=='correction_edit').order_by(WorkflowEvent.id.desc()))
    assert json.loads(e.context_json)['renewal_id']==n.id
    rejects(409,lambda:edit(db,x,g,'director',value='4.50',reason='Eski kaynak'))
    rejects(409,lambda:renewal(db,x,g))


def test_two_returns_identical_content_attempt_chain(foundation_db,people,released,ready,returned):
    db=foundation_db;x=people;p=ready[0];a=returned;before=sealed(db)
    b=reassemble(db,x,released,p);review(db,x,b);return_attempt(db,x,b)
    c=reassemble(db,x,released,p);review(db,x,c);approve(db,x,c);r=publish(db,x,c)
    for previous,new in ((a,b),(b,c)):
        m=json.loads(new.manifest_json)
        assert m['reworks_candidate_id']==previous.id and m['reworks_candidate_sha256']==previous.sha256
        assert new.predecessor_candidate_id==released.candidate_id and new.sequence==previous.sequence+1
        assert db.get(ActivityReportRevision,new.activity_revision_id).previous_revision_id==previous.activity_revision_id
        assert json.loads(new.payload_json)['entries'][0]['value']==json.loads(a.payload_json)['entries'][0]['value']
    assert r.minor==1 and db.scalar(select(func.count(ReportReleaseSuccession.id)))==1
    assert_sealed(db,before)


@pytest.mark.parametrize('state',['assembling','final_review','final_approved'])
def test_live_attempt_blocks_reassembly_reopen_and_new_grant(foundation_db,people,released,ready,state):
    db=foundation_db;x=people;p=ready[0]
    c=reassemble(db,x,released,p)
    other=request(db,x,released,other=True);accept(db,x,other)
    if state!='assembling':review(db,x,c)
    if state=='final_approved':approve(db,x,c)
    rejects(409,lambda:assemble(db,x,released,p))
    rejects(409,lambda:act(db,x,p,'strategy_reopen','strategy',reason='Canlı deneme'))
    rejects(409,lambda:grant(db,x,other))
    with pytest.raises(DBAPIError,match='Live successor freezes correction opening'):
        with db.begin_nested():
            g=ready[3]
            db.execute(RevisionEditGrant.__table__.insert().values(request_id=other.id,source_release_id=released.id,
                department_id=other.department_id,cycle_id=g.cycle_id,membership_ids_json=g.membership_ids_json,
                paths_json=auth.encode(corrections.paths(other)),start_at=g.start_at,end_at=g.end_at,created_by=x['strategy'].id,formal_basis='Sahte canlı izin'))
    with pytest.raises(DBAPIError,match='Live successor freezes correction opening'):
        with db.begin_nested():
            cycle=db.get(RevisionCorrectionCycle,ready[3].cycle_id)
            db.execute(RevisionCorrectionCycle.__table__.insert().values(source_release_id=cycle.source_release_id,
                package_id=cycle.package_id,source_package_revision_id=cycle.source_package_revision_id,
                opening_revision_id=cycle.opening_revision_id,workflow_event_id=cycle.workflow_event_id))
    with pytest.raises(DBAPIError,match='strategy_reopen requires current returned successor|Missing active scoped correction authorization|Missing exact correction transition'):
        with db.begin_nested():
            current=reports.packages.revision(db,p)
            e=reports.packages.history_event(db,x['strategy'],p,'strategy_reopen',{'from_state':p.state,'to_state':'returned','revision_id':current.id,'sha256':current.sha256,
                'delegation_id':None,'correction_cycle_id':ready[3].cycle_id,'expected_version':p.version,'returned_revision':current.revision+1},'Sahte canlı reopen')
            db.add(PackageDecision(package_revision_id=current.id,snapshot_sha256=current.sha256,action='strategy_reopen',from_state=p.state,to_state='returned',workflow_event_id=e.id));db.flush()
            insert_opening(db,x,p,current)


def test_returned_candidate_cannot_publish_or_change(foundation_db,people,released,returned):
    db=foundation_db;x=people;a=returned
    rejects(403,lambda:publish(db,x,a))
    with pytest.raises(DBAPIError,match='Published state requires exact release and successor lineage|Unaudited/invalid report state transition'):
        with db.begin_nested():db.execute(text("UPDATE report_candidate_states SET state='published',version=version+1 WHERE candidate_id=:id"),{'id':a.id})
    with pytest.raises(DBAPIError,match='Missing current authorized successor publication'):
        with db.begin_nested():
            state=db.get(ReportCandidateState,a.id);assignment=reports.assignment(db,a.organization_id)
            e=reports.event_notice(db,x['director'],a,'final_approve','returned_to_strategy','final_approved',state.version+1)
            d=ReportDecision(candidate_id=a.id,action='final_approve',candidate_sha256=a.sha256,assignment_id=assignment.id,workflow_event_id=e.id)
            db.add(d);db.flush();raw_release(db,x,a)


@pytest.mark.parametrize('state',['returned_to_strategy','final_review','final_approved','published'])
def test_initial_candidate_state_forgery(foundation_db,people,released,ready,state):
    db=foundation_db;c=assemble(db,people,released,ready[0]);db.commit()
    # A separate candidate clone would require a new legitimate attempt; the
    # insert guard is tested before duplicate-key handling on this existing ID.
    with pytest.raises(DBAPIError,match='Invalid initial candidate state'):
        with db.begin_nested():db.execute(ReportCandidateState.__table__.insert().values(candidate_id=c.id,state=state,version=0))


@pytest.mark.parametrize('bad',['wrong_sha','published_parent','wrong_parent','non_latest','non_returned'])
def test_forged_attempt_manifest_fails(foundation_db,people,released,ready,returned,bad):
    db=foundation_db;x=people;a=returned
    if bad=='non_latest':
        b=reassemble(db,x,released,ready[0]);review(db,x,b);return_attempt(db,x,b)
    def forge(mapper,connection,target):
        if target.resource_scope!='activity_report':return
        m=json.loads(target.manifest_json)
        if bad=='wrong_sha':m['reworks_candidate_sha256']='0'*64
        elif bad=='wrong_parent':target.predecessor_candidate_id=a.id
        elif bad=='published_parent':m['reworks_candidate_id']=released.candidate_id;m['reworks_candidate_sha256']=db.get(ReportCandidate,released.candidate_id).sha256
        elif bad=='non_latest':m['reworks_candidate_id']=a.id;m['reworks_candidate_sha256']=a.sha256
        else:m.pop('reworks_candidate_id');m.pop('reworks_candidate_sha256')
        target.manifest_json=reports.canonical(m);target.sha256=reports.hash_content(target.payload_json,target.manifest_json)
    event.listen(ReportCandidate,'before_insert',forge)
    try:
        with pytest.raises(DBAPIError,match='Invalid latest returned rework attempt|Invalid/current materialized successor predecessor|Successor attempt already exists'):
            assemble(db,x,released,ready[0])
    finally:event.remove(ReportCandidate,'before_insert',forge)


def test_unrelated_report_revision_after_return_fails(foundation_db,people,released,ready,returned):
    db=foundation_db;source=db.get(ActivityReportRevision,returned.activity_revision_id)
    report=db.get(ActivityReport,source.report_id);current=report.current_revision;before=counts(db)
    # A1-P1 F2: a returned candidate keeps the report workflow-managed, so an
    # unbound revision cannot even commit (deferred owner guard).
    reports.materialize(db,people['strategy'],source,[json.loads(reports.packages.revision(db,ready[0]).content_json)])
    with pytest.raises(DBAPIError,match='Workflow-managed Activity report rejects legacy revision'):db.commit()
    db.rollback();db.expire_all();assert counts(db)==before and db.get(ActivityReport,report.id).current_revision==current


@pytest.mark.parametrize('bad',['broader','active','reason','time','stale'])
def test_renewal_app_limits(foundation_db,people,released,expired_returned,bad):
    db=foundation_db;x=people;p,q,g,a=expired_returned;now=auth.server_now(db)
    if bad=='active':renewal(db,x,g)
    if bad=='stale':
        b=reassemble(db,x,released,p);review(db,x,b);approve(db,x,b);publish(db,x,b)
    rejects(422 if bad in {'broader','reason','time'} else 409,lambda:corrections.renew_grant(db,x['strategy'],g.id,
        [['entries',0,'explanation']] if bad=='broader' else json.loads(g.paths_json),now,now-timedelta(seconds=1) if bad=='time' else now+timedelta(hours=1),'' if bad=='reason' else 'Yenileme'))


@pytest.mark.parametrize('bad',['request','cycle','source','paths','audit'])
def test_raw_renewal_binding_fails(foundation_db,people,expired_returned,bad):
    db=foundation_db;x=people;p,q,g,a=expired_returned;now=auth.server_now(db)
    e=corrections.history(db,x['strategy'],q,'correction_grant_renewed',{'original_grant_id':g.id,'cycle_id':g.cycle_id,'paths':json.loads(g.paths_json),'start_at':now,'end_at':now+timedelta(hours=1)},'Yenileme')
    values=dict(original_grant_id=g.id,request_id=q.id,cycle_id=g.cycle_id,source_release_id=g.source_release_id,paths_json=g.paths_json,start_at=now,end_at=now+timedelta(hours=1),created_by=x['strategy'].id,reason='Yenileme',workflow_event_id=e.id)
    if bad in {'request','cycle','source'}:values[{'request':'request_id','cycle':'cycle_id','source':'source_release_id'}[bad]]+=999
    elif bad=='paths':values['paths_json']='[["entries",0,"explanation"]]'
    else:values['reason']='Yanlış gerekçe'
    with pytest.raises(DBAPIError,match='Renewal source/request/cycle is not reworkable|Renewal cannot broaden primary grant|Missing exact Strategy renewal audit'):
        with db.begin_nested():db.execute(RevisionEditGrantRenewal.__table__.insert().values(**values))
    db.rollback()


def test_renewals_primary_immutable_and_narrow_edit_scope(foundation_db,people,expired_returned):
    db=foundation_db;x=people;p,q,g,a=expired_returned
    act(db,x,p,'strategy_reopen','strategy',reason='Yeniden çalışma');n=renewal(db,x,g)
    for model,row in ((RevisionEditGrant,g),(RevisionEditGrantRenewal,n)):
        with pytest.raises(DBAPIError,match='Yetki ve değişiklik geçmişi değiştirilemez'):
            with db.begin_nested():db.execute(text(f'UPDATE {model.__tablename__} SET end_at=end_at+interval \'1 hour\' WHERE id=:id'),{'id':row.id})
    assert corrections.correction_context(db,p).id==g.cycle_id
    assert db.scalar(select(func.count(RevisionCorrectionCycle.id)))==1


def test_projection_left_behind_rejects_even_matching_cycle(foundation_db,people,released):
    db=foundation_db;x=people;q=request(db,x,released);accept(db,x,q);source=db.get(PackageRevision,q.source_package_revision_id);p=db.get(DirectoratePackage,source.package_id)
    source,e=opening_protocol(db,x,released,p,q);rid=insert_opening(db,x,p,source)
    db.add(RevisionCorrectionCycle(source_release_id=released.id,package_id=p.id,source_package_revision_id=source.id,opening_revision_id=rid,workflow_event_id=e.id));db.flush()
    with pytest.raises(DBAPIError,match='Correction opening projection left behind'):db.commit()
    db.rollback();assert db.get(PackageRevision,rid) is None


def test_closed_no_change_participating_request_blocks_app_and_db(foundation_db,people,released,ready):
    db=foundation_db;x=people;p,rev,q,g=ready
    # Include a second genuine correction so publication otherwise remains valid.
    a=reassemble(db,x,released,p);review(db,x,a);return_attempt(db,x,a)
    act(db,x,p,'strategy_reopen','strategy',reason='İkinci izin alanı')
    other=request(db,x,released,other=True);accept(db,x,other);h=grant(db,x,other,key='director')
    edit(db,x,h,'director',other=True,value='Yeni açıklama',reason='İkinci alan');reapprove(db,x,p)
    b=reassemble(db,x,released,p);review(db,x,b);approve(db,x,b)
    # A1-P1 F1: a live successor lists q, so closure is refused in both layers.
    state=db.get(RevisionRequestState,q.id);before=counts(db)
    rejects(409,lambda:corrections.close_no_change(db,x['strategy'],q.id,state.version,'Uygulanmayacak'))
    db.rollback();assert counts(db)==before and db.get(RevisionRequestState,q.id).state=='editing'
    with pytest.raises(DBAPIError,match='Live successor lists this correction request'):
        with db.begin_nested():
            e=corrections.history(db,x['strategy'],q,'revision_closed_no_change',{'from_state':'editing','to_state':'closed_no_change','version':state.version+1},'Uygulanmayacak')
            db.add(RevisionRequestEvent(request_id=q.id,workflow_event_id=e.id,from_state='editing',to_state='closed_no_change',version=state.version+1));db.flush()
            db.execute(text("UPDATE revision_request_states SET state='closed_no_change',version=version+1 WHERE request_id=:id"),{'id':q.id})
    db.rollback();assert publish(db,x,b).minor==1
    assert db.get(RevisionRequestState,q.id).state==db.get(RevisionRequestState,other.id).state=='applied'


@pytest.mark.parametrize('race',['reassembly','request','decision','reopen_publish','renewal','renewal_publish'])
def test_concurrent_serialization(foundation_db,people,released,expired_returned,race):
    db=foundation_db;x=people;p,q,g,a=expired_returned;barrier=Barrier(2)
    if race in {'decision','reopen_publish','grant_live','renewal_publish'}:
        b=reassemble(db,x,released,p)
        if race!='grant_live':review(db,x,b)
        if race in {'reopen_publish','renewal_publish'}:approve(db,x,b)
    db.commit()
    def run(i):
        with Session(db.bind,expire_on_commit=False) as worker:
            worker.execute(text("SET LOCAL lock_timeout='5s'"));actor=worker.get(User,x['strategy'].id);barrier.wait(timeout=10)
            try:
                if race=='reassembly' or (race=='request' and i==0):result=reports.assemble_activity_successor(worker,actor,p.organization_id,int(released.report_key),released.id,[p.id]);label='assembled'
                elif race=='request':result=corrections.create_request(worker,worker.get(User,x['user'].id),released.id,p.department_id,[{'path':['entries',0,'explanation']}],'Başka talep');label='requested'
                elif race=='decision':
                    state=worker.get(ReportCandidateState,b.id);result=reports.final_decision(worker,worker.get(User,x['director'].id),b.organization_id,b.id,'final_return' if i==0 else 'final_approve',1,b.sha256,'İade');label='decision'
                elif race in {'reopen_publish','renewal_publish'} and i==1:result=reports.publish(worker,actor,b.organization_id,b.id,2,b.sha256);label='published'
                elif race=='reopen_publish':result=reports.packages.transition(worker,actor,p.id,'strategy_reopen',p.version,reports.packages.revision(worker,worker.get(DirectoratePackage,p.id)).sha256,'Yeniden');label='reopened'
                elif race=='grant_live':
                    if i==0:result=reports.assemble_activity_successor(worker,actor,p.organization_id,int(released.report_key),released.id,[p.id]);label='assembled'
                    else:result=corrections.renew_grant(worker,actor,g.id,json.loads(g.paths_json),auth.server_now(worker),auth.server_now(worker)+timedelta(hours=1),'Canlı izin');label='renewed'
                else:result=corrections.renew_grant(worker,actor,g.id,json.loads(g.paths_json),auth.server_now(worker)-timedelta(seconds=1),auth.server_now(worker)+timedelta(hours=1),'Eşzamanlı');label='renewed'
                worker.commit();return label
            except auth.HTTPException as exc:worker.rollback();return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(run,[0,1]))
    db.expire_all()
    if race=='reassembly':assert sorted(map(str,out))==['409','assembled']
    elif race=='request':assert 'requested' in out and all(v in {'assembled','requested',409} for v in out)
    elif race=='decision':assert out.count('decision')==1 and any(v in {403,409} for v in out)
    elif race in {'reopen_publish','renewal_publish'}:assert 'published' in out and 409 in out
    elif race=='grant_live':assert out==[409,409]
    else:assert sorted(map(str,out))==['409','renewed']


def test_reopen_and_renewal_organization_first(foundation_db,people,expired_returned):
    db=foundation_db;x=people;p,q,g,a=expired_returned;locks=[]
    def capture(conn,cursor,statement,parameters,context,executemany):
        if 'FOR UPDATE' in statement:locks.append(statement.lower())
    event.listen(db.bind,'before_cursor_execute',capture)
    try:
        act(db,x,p,'strategy_reopen','strategy',reason='Sıra');assert 'from organizations' in locks[0]
        locks.clear();renewal(db,x,g);assert 'from organizations' in locks[0]
    finally:event.remove(db.bind,'before_cursor_execute',capture)


@pytest.mark.parametrize('foundation_db',['7b90cde04856'],indirect=True)
def test_populated_migration_preserves_returned_history(foundation_db,people,released,ready,returned):
    db=foundation_db;before=sealed(db);db.commit();url=db.bind.url.render_as_string(hide_password=False)
    for _ in range(2):
        run=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True);assert run.returncode==0,run.stderr
    down=subprocess.run([sys.executable,'-m','alembic','downgrade','-1'],cwd=ROOT,env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True)
    # A1-P1: the newest revision (c5e8a1f0b247) refuses first; history below it stays unreachable.
    assert down.returncode!=0 and 'A1-P1 workflow activation guards cannot be discarded' in down.stderr
    db.expire_all();assert_sealed(db,before)
    assert db.execute(text('SELECT version_num FROM alembic_version')).scalar_one()=='c5e8a1f0b247'
    act(db,people,ready[0],'strategy_reopen','strategy',reason='Migration sonrası');db.commit()


@pytest.fixture
def two_department_ready(foundation_db,people):
    from tests.test_authorization_foundation import established
    db=foundation_db;x=people
    dept=Department(organization_id=x['department'].organization_id,name='İlk düzeltmesi 1.1 birimi')
    db.add(dept);db.flush()
    user=User(email='first-cycle-editor@example.invalid',full_name='İkinci editör',role='department',department_id=dept.id,password_hash='unused')
    director=User(email='first-cycle-director@example.invalid',full_name='İkinci müdür',role='department',department_id=dept.id,password_hash='unused')
    card=ReportCard(**{col.name:getattr(x['card'],col.name) for col in ReportCard.__table__.columns if col.name not in {'id','department_id'}},department_id=dept.id)
    db.add(card);db.flush()
    indicator=Indicator(period_id=x['period'].id,department_id=dept.id,subprogram_id=x['subprogram'].id,
        card_id=card.id,name='Değişmeyen ikinci birim göstergesi',unit='Adet')
    db.add_all([user,director,indicator]);db.flush()
    db.add_all([IndicatorValue(indicator_id=indicator.id,year=2027,value_kind='target',value='1.75'),
        DepartmentScope(period_id=x['period'].id,department_id=dept.id,status='required')]);db.commit()
    other={**x,'department':dept,'user':user,'director':director};established(db,other)
    first=package.__wrapped__(db,x)
    slot=db.scalar(select(ReportIndicator).join(PublicationIndicatorBinding,ReportIndicator.publication_binding_id==PublicationIndicatorBinding.id).where(PublicationIndicatorBinding.snapshot_indicator_id==indicator.id))
    reports.contract.save_actual(db,user,slot.id,0,'1.75','verified',
        [{'title':'Defter','locator':'ikinci-birim','source_revision':'r1'}],'Hedef gerçekleşti',{});db.commit()
    untouched=reports.packages.create_package(db,user,dept.organization_id,dept.id,'activity_report',first.report_revision_id);db.commit()
    for pkg,actors in ((first,x),(untouched,other)):
        act(db,actors,pkg,'submit_to_director','user');act(db,actors,pkg,'director_approve');act(db,actors,pkg,'strategy_approve','strategy')
    auth.assign_final_authority(db,x['strategy'],dept.organization_id,x['director'].id,'Nihai yetki');db.commit()
    c=reports.assemble_candidate(db,x['strategy'],dept.organization_id,'activity_report',first.report_revision_id,[first.id,untouched.id]);db.commit()
    review(db,x,c);approve(db,x,c);initial=publish(db,x,c)

    q=request(db,x,initial,'director');accept(db,x,q);g=grant(db,x,q,key='director');edit(db,x,g,'director',reason='İlk birim kaynak düzeltmesi');reapprove(db,x,first)
    return initial,first,untouched,other


def test_open_grant_vs_live_assembly_serializes(foundation_db,people,two_department_ready):
    db=foundation_db;x=people;r,p,untouched,other=two_department_ready;db.commit();barrier=Barrier(2)
    def run(i):
        with Session(db.bind,expire_on_commit=False) as worker:
            actor=worker.get(User,x['strategy'].id);barrier.wait(timeout=10)
            try:
                if i==0:
                    reports.assemble_activity_successor(worker,actor,p.organization_id,int(r.report_key),r.id,[p.id,untouched.id]);result='assembled'
                else:
                    q=corrections.create_request(worker,worker.get(User,other['user'].id),r.id,untouched.department_id,[{'path':['entries',0,'value']}],'İkinci birim')
                    corrections.decide_request(worker,actor,q.id,'accept',0)
                    m=auth.active_membership(worker,other['user'].id,q.organization_id,q.department_id);now=auth.server_now(worker)
                    corrections.open_grant(worker,actor,q.id,1,corrections.paths(q),[m.id],now-timedelta(seconds=1),now+timedelta(hours=1),'İlk izin');result='granted'
                worker.commit();return result
            except auth.HTTPException as e:worker.rollback();return e.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(run,[0,1]))
    assert out in (['assembled',409],[409,'granted'])
    db.expire_all()
    if out[0]=='assembled':
        assert db.scalar(select(func.count(RevisionCorrectionCycle.id)).where(RevisionCorrectionCycle.package_id==untouched.id))==0
    else:assert db.get(DirectoratePackage,untouched.id).state=='returned'


def test_reopen_does_not_automatically_move_other_package(foundation_db,people,two_department_ready):
    db=foundation_db;x=people;r,p,untouched,other=two_department_ready
    c=reports.assemble_activity_successor(db,x['strategy'],r.organization_id,int(r.report_key),r.id,[p.id,untouched.id]);db.commit();review(db,x,c);return_attempt(db,x,c)
    before=(untouched.state,untouched.version,untouched.current_revision)
    act(db,x,p,'strategy_reopen','strategy',reason='Yalnız seçili birim')
    assert (untouched.state,untouched.version,untouched.current_revision)==before


@pytest.mark.parametrize('key',['user','director'])
def test_reopen_is_strategy_only(foundation_db,people,ready,returned,key):
    rejects(403,lambda:act(foundation_db,people,ready[0],'strategy_reopen',key,reason='Yetkisiz'))


def test_reopen_requires_reason(foundation_db,people,ready,returned):
    rejects(422,lambda:act(foundation_db,people,ready[0],'strategy_reopen','strategy',reason=' '))


@pytest.mark.parametrize('stage',['before_assembly','after_assembly'])
def test_closed_contribution_cannot_hide_from_manifest(foundation_db,people,released,ready,stage):
    db=foundation_db;x=people;p,rev,q,g=ready
    # A second request supplies the legitimate applied contribution.
    a=reassemble(db,x,released,p);review(db,x,a);return_attempt(db,x,a);act(db,x,p,'strategy_reopen','strategy',reason='İkinci alan')
    other=request(db,x,released,other=True);accept(db,x,other);h=grant(db,x,other,key='director')
    edit(db,x,h,'director',other=True,value='İkinci talep katkısı',reason='Kaynak');reapprove(db,x,p)
    if stage=='before_assembly':
        # S3C-2 B2: a surviving closed edit is refused at publication, not at
        # assembly, so this candidate can still be returned and reopened.
        corrections.close_no_change(db,x['strategy'],q.id,db.get(RevisionRequestState,q.id).version,'Katılmayacak');db.commit()
        b=reassemble(db,x,released,p);review(db,x,b);approve(db,x,b)
        assert q.id not in {e['request_id'] for e in json.loads(b.manifest_json)['correction_request_grants']}
        rejects(409,lambda:publish(db,x,b))
        with pytest.raises(DBAPIError,match='closed_no_change request participates'):
            with db.begin_nested():raw_release(db,x,b)
    else:
        # A1-P1 F1: a live successor lists q, so closing it is refused.
        b=reassemble(db,x,released,p);review(db,x,b);approve(db,x,b)
        rejects(409,lambda:corrections.close_no_change(db,x['strategy'],q.id,db.get(RevisionRequestState,q.id).version,'Katılmayacak'))
        db.rollback();assert db.get(RevisionRequestState,q.id).state=='editing' and publish(db,x,b).minor==1


@pytest.mark.parametrize('operation',['reopen','renew'])
def test_required_notification_failure_atomic(foundation_db,people,expired_returned,operation):
    db=foundation_db;x=people;p,q,g,a=expired_returned;before=counts(db);projection=(p.state,p.version,p.current_revision)
    def fail(*args):raise RuntimeError('mandatory recipient failure')
    event.listen(NotificationRecipient,'before_insert',fail)
    try:
        with pytest.raises(RuntimeError,match='mandatory recipient failure'):
            if operation=='reopen':act(db,x,p,'strategy_reopen','strategy',reason='Kaynak')
            else:renewal(db,x,g)
    finally:event.remove(NotificationRecipient,'before_insert',fail)
    db.expire_all();assert counts(db)==before and (p.state,p.version,p.current_revision)==projection
    assert db.scalar(select(func.count(RevisionEditGrantRenewal.id)))==0


def test_renewal_subset_constrains_app_and_database_edits(foundation_db,people,released):
    db=foundation_db;x=people
    q=corrections.create_request(db,x['director'],released.id,x['department'].id,
        [{'path':['entries',0,'value']},{'path':['entries',0,'explanation']}],'İki alan');db.commit();accept(db,x,q)
    now=auth.server_now(db);m=auth.active_membership(db,x['director'].id,q.organization_id,q.department_id)
    g=corrections.open_grant(db,x['strategy'],q.id,1,corrections.paths(q),[m.id],now-timedelta(seconds=1),now+timedelta(seconds=4),'Asli iki alan izni');db.commit()
    rev=edit(db,x,g,'director',reason='İlk gerçek düzeltme');p=db.get(DirectoratePackage,rev.package_id);reapprove(db,x,p)
    a=reassemble(db,x,released,p);review(db,x,a);return_attempt(db,x,a)
    db.execute(text('SELECT pg_sleep(:delay)'),{'delay':max(0,(g.end_at-auth.server_now(db)).total_seconds())+0.02});db.commit()
    act(db,x,p,'strategy_reopen','strategy',reason='Daraltılmış yeniden çalışma');n=renewal(db,x,g,[['entries',0,'value']])
    rejects(403,lambda:edit(db,x,g,'director',other=True,value='İzin dışı açıklama',reason='İzin dışı'))
    current=reports.packages.revision(db,p);payload=json.loads(current.content_json);payload['entries'][0]['explanation']='SQL izin dışı';raw=auth.encode(payload)
    with pytest.raises(DBAPIError,match='Correction exceeds granted cell scope'):
        with db.begin_nested():
            e=corrections.history(db,x['director'],q,'correction_edit',{'grant_id':g.id,'renewal_id':n.id,'membership_id':m.id,'package_id':p.id,
                'previous_revision_id':current.id,'next_revision':current.revision+1,'next_sha256':reports.contract.digest(raw)},'Sahte kapsam')
            db.add(FieldChangeEvent(workflow_event_id=e.id,revision_request_id=q.id,field_key='["entries",0,"explanation"]',field_type='json',
                previous_json=auth.encode(json.loads(current.content_json)['entries'][0]['explanation']),new_json=auth.encode(payload['entries'][0]['explanation'])));db.flush()
            insert_opening(db,x,p,current,content_json=raw,sha256=reports.contract.digest(raw),created_by=x['director'].id)
    edit(db,x,g,'director',value='3.50',reason='Dar izinli alan')


def test_raw_renewal_overlap_and_stale_source_fail(foundation_db,people,released,expired_returned):
    db=foundation_db;x=people;p,q,g,a=expired_returned;n=renewal(db,x,g);now=auth.server_now(db)
    with pytest.raises(DBAPIError,match='Renewal overlaps active authority'):
        with db.begin_nested():
            db.execute(RevisionEditGrantRenewal.__table__.insert().values(original_grant_id=g.id,request_id=q.id,cycle_id=g.cycle_id,
                source_release_id=g.source_release_id,paths_json=g.paths_json,start_at=now,end_at=now+timedelta(hours=1),created_by=x['strategy'].id,reason='Çakışma',workflow_event_id=n.workflow_event_id))
    b=reassemble(db,x,released,p);review(db,x,b);approve(db,x,b);publish(db,x,b)
    with pytest.raises(DBAPIError,match='Renewal source/request/cycle is not reworkable'):
        with db.begin_nested():
            db.execute(RevisionEditGrantRenewal.__table__.insert().values(original_grant_id=g.id,request_id=q.id,cycle_id=g.cycle_id,
                source_release_id=g.source_release_id,paths_json=g.paths_json,start_at=now+timedelta(hours=2),end_at=now+timedelta(hours=3),created_by=x['strategy'].id,reason='Eski kaynak',workflow_event_id=n.workflow_event_id))
    current=reports.packages.revision(db,p);payload=json.loads(current.content_json);payload['entries'][0]['value']='4.50';raw=auth.encode(payload)
    with pytest.raises(DBAPIError,match='Stale correction cycle'):
        with db.begin_nested():insert_opening(db,x,p,current,content_json=raw,sha256=reports.contract.digest(raw),created_by=x['director'].id)


@pytest.mark.parametrize('stage',['director_review','strategy_review'])
def test_expiry_during_reapproval_can_be_explicitly_renewed(foundation_db,people,expired_returned,stage):
    db=foundation_db;x=people;p,q,g,a=expired_returned
    act(db,x,p,'strategy_reopen','strategy',reason='İade sonrası kontrol')
    now=auth.server_now(db)
    first=corrections.renew_grant(db,x['strategy'],g.id,json.loads(g.paths_json),now,now+timedelta(seconds=2),'İnceleme kısa izni');db.commit()
    act(db,x,p,'submit_to_director','director')
    if stage=='strategy_review':act(db,x,p,'director_approve')
    db.execute(text('SELECT pg_sleep(:delay)'),{'delay':max(0,(first.end_at-auth.server_now(db)).total_seconds())+0.02});db.commit()
    assert p.state==stage
    now=auth.server_now(db)
    second=corrections.renew_grant(db,x['strategy'],g.id,json.loads(g.paths_json),now,now+timedelta(hours=1),'İnceleme devam izni');db.commit()
    assert second.start_at>=first.end_at and second.id!=first.id
    if stage=='director_review':act(db,x,p,'director_approve')
    act(db,x,p,'strategy_approve','strategy')
    assert p.state=='strategy_approved' and db.scalar(select(func.count(RevisionEditGrantRenewal.id)))==2
