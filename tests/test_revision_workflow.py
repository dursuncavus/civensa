"""Phase 5A only: migrated PostgreSQL correction scopes and immutable releases."""
import json
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import select,func,text,event
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.exc import DBAPIError
from app.models import *
from app import revision_workflow_service as service, authorization_service as auth
from tests.test_report_workflow import foundation_db,people,package,approved,candidate,review,approve,publish,rejects
pytestmark=pytest.mark.postgres

@pytest.fixture
def released(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate;review(db,x,c);approve(db,x,c);return publish(db,x,c)

def address(release,other=False):
    if release.resource_scope=='activity_report':return ['entries',0,'explanation' if other else 'value']
    return ['indicators',0,'explanation'] if other else ['indicators',0,'values',0,'value']

def request(db,x,r,key='user',other=False):
    q=service.create_request(db,x[key],r.id,x['department'].id,[{'path':address(r,other)}],'Kaynak cetveli düzeltmesi',[{'reference':'2027/1'}]);db.commit();return q

def accept(db,x,q):
    s=db.get(RevisionRequestState,q.id);service.decide_request(db,x['strategy'],q.id,'accept',s.version);db.commit()

def grant(db,x,q,narrow=None,key='user',offset=0):
    s=db.get(RevisionRequestState,q.id);now=auth.server_now(db);m=auth.active_membership(db,x[key].id,q.organization_id,q.department_id)
    g=service.open_grant(db,x['strategy'],q.id,s.version,narrow or service.paths(q),[m.id],now+timedelta(hours=offset)-timedelta(minutes=1),now+timedelta(hours=offset+1),'Resmî düzeltme izni');db.commit();return g

def edit(db,x,g,key='user',other=False,reason='',value='2.50'):
    cycle=db.get(RevisionCorrectionCycle,g.cycle_id);p=db.get(DirectoratePackage,cycle.package_id);rev=service.packages.revision(db,p);r=db.get(ReportRelease,g.source_release_id)
    new=service.edit_under_grant(db,x[key],g.id,p.version,rev.sha256,[{'path':address(r,other),'value':value}],reason);db.commit();return new

@pytest.mark.parametrize('key',['user','director'])
def test_own_department_request(foundation_db,people,released,key):
    db=foundation_db;x=people;q=request(db,x,released,key)
    assert q.requester_user_id==x[key].id and db.get(RevisionRequestState,q.id).state=='requested'
    assert json.loads(q.patches_json)[0]['path']==address(released)
    assert db.scalar(select(func.count(RevisionEditGrant.id)))==0

@pytest.mark.parametrize('bad',['strategy','cross_department','reason','identity','duplicate','unknown'])
def test_invalid_request(foundation_db,people,released,bad):
    db=foundation_db;x=people;r=released;actor=x['user'];dep=x['department'].id;reason='Düzelt';patches=[{'path':address(r)}];code=422
    if bad=='strategy':actor=x['strategy'];code=403
    elif bad=='cross_department':dep+=999;code=403
    elif bad=='reason':reason=' '
    elif bad=='identity':patches=[{'path':['entries',0,'definition_revision_id']}] if r.resource_scope=='activity_report' else [{'path':['indicators',0,'id']}]
    elif bad=='duplicate':patches*=2
    else:actor.role='unknown';db.commit();code=403
    rejects(code,lambda:service.create_request(db,actor,r.id,dep,patches,reason))
    assert db.scalar(select(func.count(RevisionRequest.id)))==0

@pytest.mark.parametrize('action',['cancel','reject','accept'])
def test_lifecycle(foundation_db,people,released,action):
    db=foundation_db;x=people;q=request(db,x,released);key='user' if action=='cancel' else 'strategy'
    if action!='accept':rejects(422,lambda:service.decide_request(db,x[key],q.id,action,0,' '))
    service.decide_request(db,x[key],q.id,action,0,'Karar gerekçesi');db.commit()
    assert db.get(RevisionRequestState,q.id).state=={'cancel':'cancelled','reject':'rejected','accept':'accepted'}[action]
    rejects(409,lambda:service.decide_request(db,x['user'],q.id,'cancel',1,'İptal'))
    assert db.scalar(select(func.count(RevisionCorrectionCycle.id)))==0


def test_disjoint_grants_share_correction_branch(foundation_db,people,released):
    db=foundation_db;x=people;r=released;first=request(db,x,r);second=request(db,x,r,other=True)
    accept(db,x,first);accept(db,x,second);g=grant(db,x,first);h=grant(db,x,second)
    assert g.cycle_id==h.cycle_id
    cycle=db.get(RevisionCorrectionCycle,g.cycle_id);opening=db.get(PackageRevision,cycle.opening_revision_id);src=db.get(PackageRevision,first.source_package_revision_id)
    assert opening.previous_revision_id==src.id and opening.content_json==src.content_json and opening.sha256==src.sha256
    assert service.reports.candidate_detail(db,x['strategy'],r.organization_id,r.candidate_id)['state']=='published'
    assert service.reports.verify_artifact(db,r)


def test_overlap_accept_and_concurrency(foundation_db,people,released):
    db=foundation_db;x=people;r=released;q=request(db,x,r);s=request(db,x,r);actor_id=x['strategy'].id;ids=[q.id,s.id];db.commit();barrier=Barrier(2)
    def run(rid):
        with Session(db.get_bind(),expire_on_commit=False) as other:
            actor=other.get(User,actor_id);barrier.wait()
            try:service.decide_request(other,actor,rid,'accept',0);other.commit();return 1
            except service.auth.HTTPException as exc:other.rollback();return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(run,ids))
    assert sorted(out)==[1,409]
    db.expire_all();assert sorted(db.get(RevisionRequestState,rid).state for rid in ids)==['accepted','requested']

@pytest.mark.parametrize('bad',['broader','membership','expired','future','inactive_user','inactive_member','outside','before_grant','director_reason'])
def test_grant_restrictions(foundation_db,people,released,bad):
    db=foundation_db;x=people;r=released;q=request(db,x,r);accept(db,x,q);now=auth.server_now(db)
    if bad in {'broader','membership'}:
        mids=[999999] if bad=='membership' else [auth.active_membership(db,x['user'].id,q.organization_id,q.department_id).id]
        rejects(422,lambda:service.open_grant(db,x['strategy'],q.id,1,[address(r,True)] if bad=='broader' else service.paths(q),mids,now,now+timedelta(hours=1),'Gerekçe'));return
    if bad=='before_grant':rejects(403,lambda:service.edit_under_grant(db,x['user'],999999,0,'',[],''));return
    g=grant(db,x,q,key='director' if bad=='director_reason' else 'user',offset=-2 if bad=='expired' else 2 if bad=='future' else 0)
    if bad=='inactive_user':x['user'].is_active=False;db.commit()
    if bad=='inactive_member':
        m=auth.active_membership(db,x['user'].id,q.organization_id,q.department_id)
        # Use established audited membership removal; no history protections disabled.
        auth.deactivate_membership(db,x['strategy'],m.id,'Görevlendirme sona erdi');db.commit()
    rejects(422 if bad=='director_reason' else 403,lambda:edit(db,x,g,key='director' if bad=='director_reason' else 'user',other=bad=='outside'))

@pytest.mark.parametrize('key',['user','director'])
def test_edit_audit_and_release_unchanged(foundation_db,people,released,key):
    db=foundation_db;x=people;r=released;q=request(db,x,r);accept(db,x,q);g=grant(db,x,q,key=key)
    classes=(ReportCandidate,Publication,ReportArtifact,ActivityReportRevision,ActualRevision,ActivityReportApproval,PackageRevision)
    before={cls:{row.id:{col.name:getattr(row,col.name) for col in cls.__table__.columns} for row in db.scalars(select(cls))} for cls in classes}
    new=edit(db,x,g,key,reason='Müdür kaynak düzeltmesi')
    for cls,rows in before.items():
        for rid,old in rows.items():assert {col.name:getattr(db.get(cls,rid),col.name) for col in cls.__table__.columns}==old
    service.reports.verify(db,db.get(ReportCandidate,r.candidate_id));service.reports.verify_artifact(db,r)
    changes=db.scalars(select(FieldChangeEvent).where(FieldChangeEvent.revision_request_id==q.id)).all()
    assert changes and any(json.loads(c.field_key)==address(r) and json.loads(c.new_json)=='2.50' for c in changes)
    e=db.get(WorkflowEvent,changes[0].workflow_event_id);assert e.actor_user_id==x[key].id
    assert json.loads(e.actor_snapshot_json)['memberships'] and json.loads(e.context_json)['source_release_id']==r.id
    assert new.previous_revision_id==db.get(RevisionCorrectionCycle,g.cycle_id).opening_revision_id

@pytest.mark.parametrize('op',['create','accept','grant'])
def test_notification_failure_atomic(foundation_db,people,released,op):
    db=foundation_db;x=people;r=released;q=None
    if op!='create':q=request(db,x,r)
    if op=='grant':accept(db,x,q)
    classes=(RevisionRequest,RevisionRequestEvent,RevisionEditGrant,RevisionCorrectionCycle,PackageRevision,WorkflowEvent)
    before={cls:db.scalar(select(func.count(cls.id))) for cls in classes}
    def fail(*args):raise RuntimeError('mandatory failure')
    event.listen(NotificationRecipient,'before_insert',fail)
    try:
        with pytest.raises(RuntimeError):
            if op=='create':request(db,x,r)
            elif op=='accept':accept(db,x,q)
            else:grant(db,x,q)
    finally:event.remove(NotificationRecipient,'before_insert',fail)
    db.expire_all()
    for cls,count in before.items():assert db.scalar(select(func.count(cls.id)))==count
    if q:assert db.get(RevisionRequestState,q.id).state==('accepted' if op=='grant' else 'requested')

@pytest.mark.parametrize('table',['revision_requests','revision_request_events','revision_edit_grants','revision_correction_cycles'])
@pytest.mark.parametrize('operation',['UPDATE','DELETE'])
def test_sql_history_immutable(foundation_db,people,released,table,operation):
    db=foundation_db;x=people;q=request(db,x,released);accept(db,x,q);grant(db,x,q)
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(text(f'DELETE FROM {table}' if operation=='DELETE' else f'UPDATE {table} SET id=id'))

@pytest.mark.parametrize('target',['release','package','artifact'])
def test_tampered_source_fails(foundation_db,people,released,target):
    db=foundation_db;x=people;r=released
    if target=='release':set_committed_value(db.get(ReportCandidate,r.candidate_id),'sha256','0'*64)
    elif target=='package':
        binding=db.scalar(select(CandidatePackage).where(CandidatePackage.candidate_id==r.candidate_id));corrupted=db.get(PackageRevision,binding.package_revision_id);set_committed_value(corrupted,'sha256','0'*64)
    else:
        corrupted=db.scalar(select(ReportArtifact).where(ReportArtifact.release_id==r.id));set_committed_value(corrupted,'sha256','0'*64)
    rejects(409,lambda:request(db,x,r));db.expire_all()


def test_stale_source_rejected_at_create_accept(foundation_db,people,released,monkeypatch):
    db=foundation_db;x=people;r=released;q=request(db,x,r)
    # Simulate a later release's currentness without introducing Phase 5B release semantics.
    original=db.scalar
    def scalar(statement,*a,**kw):
        sql=str(statement)
        if 'report_releases.major DESC' in sql:return r.id+1
        return original(statement,*a,**kw)
    monkeypatch.setattr(db,'scalar',scalar)
    rejects(409,lambda:request(db,x,r));rejects(409,lambda:accept(db,x,q))
    assert db.get(RevisionRequestState,q.id).state=='requested'

@pytest.mark.parametrize('cls',[RevisionRequest,RevisionRequestEvent,RevisionEditGrant,RevisionCorrectionCycle])
@pytest.mark.parametrize('operation',['update','delete'])
def test_orm_history_immutable(foundation_db,people,released,cls,operation):
    db=foundation_db;x=people;q=request(db,x,released);accept(db,x,q);grant(db,x,q)
    row=db.scalar(select(cls))
    with pytest.raises(ValueError):
        with db.begin_nested():
            if operation=='delete':db.delete(row)
            elif cls==RevisionRequest:row.reason='Changed'
            elif cls==RevisionRequestEvent:row.to_state='cancelled'
            elif cls==RevisionEditGrant:row.formal_basis='Changed'
            else:row.source_release_id+=999
            db.flush()

@pytest.mark.parametrize('bad',['state','overlap','broader_grant','revision_without_audit','request_identity','edit_outside_scope'])
def test_direct_sql_cannot_bypass_scope(foundation_db,people,released,bad):
    from sqlalchemy import insert
    db=foundation_db;x=people;r=released;q=request(db,x,r)
    if bad=='state':
        with pytest.raises(DBAPIError):
            with db.begin_nested():db.execute(text("UPDATE revision_request_states SET state='accepted',version=version+1"))
        return
    if bad=='request_identity':
        values={c.name:getattr(q,c.name) for c in RevisionRequest.__table__.columns if c.name not in {'id','created_at'}}
        values['patches_json']=auth.encode([{'path':['entries',0,'definition_revision_id'] if r.resource_scope=='activity_report' else ['indicators',0,'id']}])
        with pytest.raises(DBAPIError):
            with db.begin_nested():db.execute(insert(RevisionRequest).values(**values))
        return
    if bad=='overlap':
        other=request(db,x,r);accept(db,x,q)
        with pytest.raises(DBAPIError):
            with db.begin_nested():service.transition(db,x['strategy'],other,db.get(RevisionRequestState,other.id),'accepted')
        return
    accept(db,x,q);g=grant(db,x,q)
    if bad=='broader_grant':
        other=request(db,x,r,other=True);accept(db,x,other)
        values={c.name:getattr(g,c.name) for c in RevisionEditGrant.__table__.columns if c.name not in {'id','created_at'}}
        values['request_id']=other.id
        with pytest.raises(DBAPIError):
            with db.begin_nested():db.execute(insert(RevisionEditGrant).values(**values))
        return
    cycle=db.get(RevisionCorrectionCycle,g.cycle_id);pkg=db.get(DirectoratePackage,cycle.package_id);old=service.packages.revision(db,pkg)
    doc=json.loads(old.content_json)
    if bad=='edit_outside_scope':service.packages.apply_patch(doc,pkg.resource_scope,address(r,True),'Unapproved change')
    raw=auth.encode(doc)
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            if bad=='edit_outside_scope':
                m=auth.active_membership(db,x['user'].id,q.organization_id,q.department_id)
                service.history(db,x['user'],q,'correction_edit',{'grant_id':g.id,'membership_id':m.id,'package_id':pkg.id,'previous_revision_id':old.id,'next_revision':old.revision+1,'next_sha256':service.packages.digest(raw)})
            db.execute(insert(PackageRevision).values(package_id=pkg.id,revision=old.revision+1,previous_revision_id=old.id,
                content_json=raw,sha256=service.packages.digest(raw),created_by=x['user'].id,reason='Direct SQL'))

@pytest.mark.parametrize('foundation_db',['264bdce59301'],indirect=True)
def test_populated_phase4_upgrade_preserves_history(foundation_db,people,released):
    import os,sys,subprocess
    from tests.test_authorization_foundation import ROOT
    db=foundation_db
    tables=('report_candidates','report_decisions','report_releases','report_artifacts','candidate_packages','package_revisions','workflow_events','actual_revisions','activity_report_approvals','publications','field_change_events')
    before={t:[dict(r) for r in db.execute(text(f'SELECT * FROM {t} ORDER BY id')).mappings()] for t in tables};db.commit()
    for _ in range(2):
        result=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env={**os.environ,'DATABASE_URL':db.get_bind().url.render_as_string(hide_password=False)},capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    for t,rows in before.items():
        actual=[dict(r) for r in db.execute(text(f'SELECT * FROM {t} ORDER BY id')).mappings()]
        if t=='field_change_events':
            assert all(row.pop('revision_request_id') is None for row in actual)
        assert actual==rows
    assert db.scalar(select(func.count(RevisionRequest.id)))==0


def test_narrow_grant_and_ungranted_proposal_not_applied(foundation_db,people,released):
    db=foundation_db;x=people;r=released
    q=service.create_request(db,x['user'],r.id,x['department'].id,
        [{'path':address(r),'value':'99.00'},{'path':address(r,True),'value':'Önerilen açıklama'}],'İki alanı inceleyin');db.commit()
    accept(db,x,q);g=grant(db,x,q,narrow=[address(r)])
    rejects(403,lambda:edit(db,x,g,other=True))
    new=edit(db,x,g);doc=json.loads(new.content_json);old=db.get(PackageRevision,new.previous_revision_id)
    def resolve(content,path):
        for k in path:content=content[k]
        return content
    assert resolve(doc,address(r))=='2.50'
    assert resolve(doc,address(r,True))==resolve(json.loads(old.content_json),address(r,True))


def test_normal_phase3_edit_and_submit_do_not_bypass_grant(foundation_db,people,released):
    db=foundation_db;x=people;r=released;q=request(db,x,r);accept(db,x,q);g=grant(db,x,q)
    cycle=db.get(RevisionCorrectionCycle,g.cycle_id);pkg=db.get(DirectoratePackage,cycle.package_id)
    rev=service.packages.revision(db,pkg)
    # Internal Phase 3 operations are still present, but cannot bypass correction DB guards.
    with pytest.raises((DBAPIError,service.auth.HTTPException)):
        with db.begin_nested():service.packages.edit_package(db,x['director'],pkg.id,pkg.version,rev.sha256,[{'path':address(r,True),'value':'Bypass'}],'Müdür')
    with pytest.raises((DBAPIError,service.auth.HTTPException)):
        with db.begin_nested():service.packages.transition(db,x['user'],pkg.id,'submit_to_director',pkg.version,rev.sha256)

@pytest.mark.parametrize('bad',['blank_verified','no_evidence','untrusted_delta'])
def test_activity_correction_validation_preserved(foundation_db,people,released,bad):
    db=foundation_db;x=people;r=released
    path=address(r)
    if r.resource_scope=='performance_program':
        q=request(db,x,r);accept(db,x,q);g=grant(db,x,q)
        rejects(422,lambda:edit(db,x,g,value=' '));return
    path=['entries',0,'value' if bad=='blank_verified' else 'evidence' if bad=='no_evidence' else 'deviation']
    q=service.create_request(db,x['user'],r.id,x['department'].id,[{'path':path}],'Doğrulama');db.commit();accept(db,x,q);g=grant(db,x,q)
    cycle=db.get(RevisionCorrectionCycle,g.cycle_id);pkg=db.get(DirectoratePackage,cycle.package_id);rev=service.packages.revision(db,pkg)
    if bad=='untrusted_delta':
        new=service.edit_under_grant(db,x['user'],g.id,pkg.version,rev.sha256,[{'path':path,'value':{'delta':'999999','corrective_action':'Kaynağı incele'}}]);db.commit()
        assert json.loads(new.content_json)['entries'][0]['deviation']['delta']!='999999'
    else:
        rejects(422,lambda:service.edit_under_grant(db,x['user'],g.id,pkg.version,rev.sha256,[{'path':path,'value':' ' if bad=='blank_verified' else []}]))


def test_sql_edit_requires_exact_field_history(foundation_db,people,released):
    from sqlalchemy import insert
    db=foundation_db;x=people;r=released;q=request(db,x,r);accept(db,x,q);g=grant(db,x,q)
    cycle=db.get(RevisionCorrectionCycle,g.cycle_id);pkg=db.get(DirectoratePackage,cycle.package_id);old=service.packages.revision(db,pkg)
    doc=json.loads(old.content_json);service.packages.apply_patch(doc,pkg.resource_scope,address(r),'2.50')
    if r.resource_scope=='activity_report':
        for entry in doc['entries']:service.packages.validate_actual(entry)
    raw=auth.encode(doc);m=auth.active_membership(db,x['user'].id,q.organization_id,q.department_id)
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            service.history(db,x['user'],q,'correction_edit',{'grant_id':g.id,'membership_id':m.id,'package_id':pkg.id,
                'previous_revision_id':old.id,'next_revision':old.revision+1,'next_sha256':service.packages.digest(raw)})
            db.execute(insert(PackageRevision).values(package_id=pkg.id,revision=old.revision+1,previous_revision_id=old.id,
                content_json=raw,sha256=service.packages.digest(raw),created_by=x['user'].id,reason='Audit omitted'))
