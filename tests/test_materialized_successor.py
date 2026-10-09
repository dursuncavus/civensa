"""S3A only: migrated PostgreSQL, fresh materialization, no successor publication."""
import json
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import select, func, text, event, insert
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.exc import DBAPIError
from app.models import *
from app import report_workflow_service as reports, revision_workflow_service as corrections, authorization_service as auth
from tests.test_authorization_foundation import foundation_db, people as base_people
from tests.test_package_workflow import package as base_package, act
from tests.test_report_workflow import approved, candidate, review, approve, publish, rejects
from tests.test_revision_workflow import released, request, accept, grant, edit, address
pytestmark=pytest.mark.postgres


@pytest.fixture
def people(foundation_db):
    db=foundation_db;x=base_people.__wrapped__(db)
    indicator=Indicator(period_id=x['period'].id,department_id=x['department'].id,subprogram_id=x['subprogram'].id,
                        card_id=x['card'].id,name='İkinci değişmeyen gösterge',unit='Adet')
    db.add(indicator);db.flush();db.add(IndicatorValue(indicator_id=indicator.id,year=2027,value_kind='target',value='1.75'))
    db.commit();return x


@pytest.fixture
def package(foundation_db,people):
    db=foundation_db;x=people;p=base_package.__wrapped__(db,x,SimpleNamespace(param='activity_report'))
    reports.packages.edit_package(db,x['user'],p.id,p.version,reports.packages.revision(db,p).sha256,
        [{'path':['entries',1,'value'],'value':'1.75'},{'path':['entries',1,'state'],'value':'verified'},
         {'path':['entries',1,'evidence'],'value':[{'title':'Defter','locator':'s2','source_revision':'r1'}]},
         {'path':['entries',1,'explanation'],'value':'Hedef gerçekleşti'}])
    db.commit();return p


@pytest.fixture
def ready(foundation_db,people,released):
    db=foundation_db;x=people;r=released
    q=request(db,x,r,'director');accept(db,x,q);g=grant(db,x,q,key='director')
    corrected=edit(db,x,g,'director',reason='Müdür kaynak düzeltmesi')
    p=db.get(DirectoratePackage,corrected.package_id)
    act(db,x,p,'submit_to_director','director');act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    return p,corrected,q,g


def assemble(db,x,r,p):
    return reports.assemble_activity_successor(db,x['strategy'],r.organization_id,int(r.report_key),r.id,[p.id])


def counts(db):
    return tuple(db.scalar(select(func.count(cls.id))) for cls in
        (ReportCandidate,ReportRelease,ReportReleaseSuccession,ReportArtifact,ActivityReportRevision,ReportIndicator,ActualRevision,WorkflowEvent,Notification))


def sealed(db):
    return {cls:{row.id:tuple(getattr(row,c.name) for c in cls.__table__.columns) for row in db.scalars(select(cls))}
            for cls in (ReportRelease,ReportCandidate,ReportArtifact,ActivityReportApproval,ActivityReportRevision,ActualRevision,PackageRevision)}


def assert_sealed(db,before):
    for cls,rows in before.items():
        for rid,values in rows.items():assert tuple(getattr(db.get(cls,rid),c.name) for c in cls.__table__.columns)==values


def test_successor_exact_predecessor_and_all_fresh_actuals(foundation_db,people,released,ready):
    db=foundation_db;x=people;r=released;p,corrected,q,g=ready;before=sealed(db)
    previous=db.get(ReportCandidate,r.candidate_id);old=json.loads(previous.payload_json)
    c=assemble(db,x,r,p);db.commit();payload=json.loads(c.payload_json);manifest=reports.verify(db,c)
    assert c.predecessor_candidate_id==previous.id and c.activity_revision_id!=previous.activity_revision_id
    revision=db.get(ActivityReportRevision,c.activity_revision_id)
    assert revision.previous_revision_id==previous.activity_revision_id
    assert revision.revision==db.get(ActivityReportRevision,previous.activity_revision_id).revision+1
    assert manifest['predecessor_release_id']==r.id and manifest['predecessor_candidate_sha256']==previous.sha256
    assert manifest['correction_cycle_ids']==[g.cycle_id] and manifest['packages'][0]['revision_id']==corrected.id
    assert payload['schema_version']=='activity-candidate-1' and len(payload['entries'])==2
    assert payload['entries'][0]['value']=='2.50' and payload['entries'][1]['value']==old['entries'][1]['value']=='1.75'
    assert {e['materialized_report_indicator_id'] for e in payload['entries']}.isdisjoint(e['materialized_report_indicator_id'] for e in old['entries'])
    for entry in payload['entries']:
        actuals=db.scalars(select(ActualRevision).where(ActualRevision.report_indicator_id==entry['materialized_report_indicator_id'])).all()
        assert len(actuals)==1 and actuals[0].id==entry['materialized_actual_revision_id']
        assert actuals[0].id not in before[ActualRevision]
        assert actuals[0].revision==1 and actuals[0].supersedes_id is None
        assert not any('reference' in k for k in entry)
    assert_sealed(db,before)
    reports.verify_artifact(db,r)
    assert db.get(ReportCandidateState,previous.id).state=='published'
    assert db.get(RevisionRequestState,q.id).state=='editing'
    assert db.scalar(select(func.count(ReportRelease.id)))==1 and db.scalar(select(func.count(ReportReleaseSuccession.id)))==0


@pytest.mark.parametrize('bad',['wrong_org','wrong_report','wrong_key','wrong_scope','stale','no_correction','duplicate','missing'])
def test_invalid_predecessor_and_selection_fail_closed(foundation_db,people,released,ready,bad,monkeypatch):
    db=foundation_db;x=people;r=released;p,rev,q,g=ready;before=counts(db)
    org=r.organization_id;report=int(r.report_key);ids=[p.id]
    if bad=='wrong_org':
        other=Organization(name='Başka kurum');db.add(other);db.commit();org=other.id
        before=counts(db)
    elif bad=='wrong_report':report+=999
    elif bad=='wrong_key':set_committed_value(r,'report_key','wrong')
    elif bad=='wrong_scope':set_committed_value(r,'resource_scope','performance_program')
    elif bad=='duplicate':ids*=2
    elif bad=='missing':ids=[]
    elif bad=='no_correction':
        original=db.scalars
        def scalars(statement,*a,**kw):
            if 'FROM revision_correction_cycles' in str(statement):return FakeRows([])
            return original(statement,*a,**kw)
        monkeypatch.setattr(db,'scalars',scalars)
    else:
        original=db.scalar
        def scalar(statement,*a,**kw):
            if 'report_releases.major DESC' in str(statement):return r.id+1
            return original(statement,*a,**kw)
        monkeypatch.setattr(db,'scalar',scalar)
    rejects(409,lambda:reports.assemble_activity_successor(db,x['strategy'],org,report,r.id,ids))
    assert counts(db)==before


class FakeRows:
    def __init__(self,rows):self.rows=rows
    def all(self):return self.rows
    def __iter__(self):return iter(self.rows)


@pytest.mark.parametrize('bad',['hash','decision_revision','decision_hash','decision_event','event_revision','event_hash'])
def test_exact_current_approval_binding_required(foundation_db,people,released,ready,bad):
    db=foundation_db;x=people;r=released;p,rev,q,g=ready;before=counts(db)
    d=db.scalar(select(PackageDecision).where(PackageDecision.package_revision_id==rev.id,PackageDecision.action=='strategy_approve'))
    if bad=='hash':set_committed_value(rev,'sha256','0'*64)
    elif bad=='decision_revision':set_committed_value(d,'package_revision_id',rev.id+999)
    elif bad=='decision_hash':set_committed_value(d,'snapshot_sha256','0'*64)
    elif bad=='decision_event':set_committed_value(d,'workflow_event_id',d.workflow_event_id+999)
    else:
        e=db.get(WorkflowEvent,d.workflow_event_id);context=json.loads(e.context_json)
        context['revision_id' if bad=='event_revision' else 'sha256']=rev.id+999 if bad=='event_revision' else '0'*64
        set_committed_value(e,'context_json',auth.encode(context))
    rejects(409,lambda:assemble(db,x,r,p))
    db.expire_all();assert counts(db)==before
    assert db.get(ActivityReport,int(r.report_key)).current_revision==db.get(ActivityReportRevision,db.get(ReportCandidate,r.candidate_id).activity_revision_id).revision


@pytest.mark.parametrize('state',['requested','accepted'])
def test_pending_request_blocks_without_stranding(foundation_db,people,released,ready,state):
    db=foundation_db;x=people;r=released;p,rev,q,g=ready
    other=request(db,x,r,other=True)
    if state=='accepted':accept(db,x,other)
    before=counts(db)
    with pytest.raises(auth.HTTPException) as caught:assemble(db,x,r,p)
    assert caught.value.status_code==409 and 'talebi' in str(caught.value.detail).lower()
    assert counts(db)==before and db.get(RevisionRequestState,other.id).state==state
    assert db.get(RevisionRequestState,q.id).state=='editing'


@pytest.mark.parametrize('stage',['returned','director_review','strategy_review'])
def test_editing_cycle_not_ready_blocks(foundation_db,people,released,stage):
    db=foundation_db;x=people;r=released
    q=request(db,x,r);accept(db,x,q);g=grant(db,x,q);rev=edit(db,x,g)
    p=db.get(DirectoratePackage,rev.package_id)
    if stage!='returned':act(db,x,p,'submit_to_director','user')
    if stage=='strategy_review':act(db,x,p,'director_approve')
    before=counts(db)
    with pytest.raises(auth.HTTPException) as caught:assemble(db,x,r,p)
    assert caught.value.status_code==409 and 'hazır' in str(caught.value.detail)
    assert counts(db)==before and p.state==stage and db.get(RevisionRequestState,q.id).state=='editing'


def test_two_editing_requests_in_approved_included_cycle_allowed(foundation_db,people,released):
    db=foundation_db;x=people;r=released
    q=request(db,x,r);other=request(db,x,r,other=True);accept(db,x,q);accept(db,x,other)
    g=grant(db,x,q);h=grant(db,x,other);rev=edit(db,x,g)
    rev=edit(db,x,h,other=True,value='Onaylanan açıklama')
    p=db.get(DirectoratePackage,rev.package_id)
    act(db,x,p,'submit_to_director','user');act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    c=assemble(db,x,r,p);db.commit()
    assert reports.verify(db,c)['correction_cycle_ids']==[g.cycle_id] and g.cycle_id==h.cycle_id
    assert db.get(RevisionRequestState,q.id).state==db.get(RevisionRequestState,other.id).state=='editing'


def test_concurrent_one_successor_no_orphans(foundation_db,people,released,ready):
    db=foundation_db;x=people;r=released;p,rev,q,g=ready
    uid=x['strategy'].id;rid=r.id;org=r.organization_id;report=int(r.report_key);pid=p.id
    before=counts(db);db.commit();barrier=Barrier(2)
    def run(_):
        with Session(db.get_bind(),expire_on_commit=False) as worker:
            actor=worker.get(User,uid);barrier.wait(timeout=5)
            try:
                c=reports.assemble_activity_successor(worker,actor,org,report,rid,[pid]);worker.commit();return 1
            except auth.HTTPException as exc:worker.rollback();return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(run,range(2)))==[1,409]
    db.expire_all();after=counts(db)
    assert after[0]==before[0]+1 and after[4]==before[4]+1 and after[5]==before[5]+2 and after[6]==before[6]+2
    assert after[1:4]==before[1:4]


@pytest.mark.parametrize('failure',[NotificationRecipient,ActualRevision])
def test_atomic_assembly_failure_no_orphans(foundation_db,people,released,ready,failure):
    db=foundation_db;x=people;r=released;p,rev,q,g=ready;before=counts(db)
    report=db.get(ActivityReport,int(r.report_key));version=(report.current_revision,report.lock_version)
    def fail(*a):raise RuntimeError('mandatory failure')
    event.listen(failure,'before_insert',fail)
    try:
        with pytest.raises(RuntimeError):assemble(db,x,r,p)
    finally:event.remove(failure,'before_insert',fail)
    db.expire_all();assert counts(db)==before and (report.current_revision,report.lock_version)==version


def test_successor_publication_is_explicitly_disabled(foundation_db,people,released,ready):
    db=foundation_db;x=people;r=released;p,rev,q,g=ready
    c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c)
    before=counts(db)
    rejects(409,lambda:publish(db,x,c))
    assert counts(db)==before and db.get(ReportCandidateState,c.id).state=='final_approved'


@pytest.mark.parametrize('field',['predecessor_release_id','predecessor_candidate_sha256','source_id','correction_cycle_ids'])
def test_successor_lineage_manifest_tampering_fails(foundation_db,people,released,ready,field):
    db=foundation_db;x=people;r=released;p,rev,q,g=ready;c=assemble(db,x,r,p);db.commit()
    m=json.loads(c.manifest_json);m[field]=[] if field=='correction_cycle_ids' else '0'*64 if field=='predecessor_candidate_sha256' else 999999
    raw=reports.canonical(m);set_committed_value(c,'manifest_json',raw);set_committed_value(c,'sha256',reports.hash_content(c.payload_json,raw))
    rejects(409,lambda:reports.verify(db,c))


def test_lineage_foundation_constraints_and_no_row_yet(foundation_db,people,released,ready):
    db=foundation_db;x=people;r=released;p,rev,q,g=ready;assemble(db,x,r,p);db.commit()
    assert db.scalar(select(func.count(ReportReleaseSuccession.id)))==0
    constraints=list(db.execute(text("SELECT contype,pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='report_release_successions'::regclass")))
    assert sum(kind=='u' for kind,_ in constraints)==3
    assert any('predecessor_release_id <> successor_release_id' in definition for _,definition in constraints)
    triggers=set(db.scalars(text("SELECT tgname FROM pg_trigger WHERE tgrelid='report_release_successions'::regclass AND NOT tgisinternal")))
    assert {'immutable_report_release_successions','release_succession_guard','timestamp_report_release_successions'}<=triggers
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            db.add(ReportReleaseSuccession(predecessor_release_id=r.id,successor_release_id=r.id,
                predecessor_candidate_sha256='0'*64,successor_candidate_sha256='0'*64,workflow_event_id=r.workflow_event_id));db.flush()


def test_successor_org_first_order_without_package_locked(foundation_db,people,released,ready,monkeypatch):
    db=foundation_db;x=people;r=released;p,rev,q,g=ready;locks=[]
    def forbidden(*a,**kw):raise AssertionError('Assembly must own its organization lock')
    monkeypatch.setattr(reports.packages,'locked',forbidden)
    def record(conn,cursor,statement,parameters,context,many):
        if 'FOR UPDATE' in statement.upper():locks.append(statement.lower())
    event.listen(db.get_bind(),'before_cursor_execute',record)
    try:assemble(db,x,r,p);db.commit()
    finally:event.remove(db.get_bind(),'before_cursor_execute',record)
    assert 'from organizations' in locks[0]
    department=next(i for i,s in enumerate(locks) if 'from departments' in s)
    package_lock=next(i for i,s in enumerate(locks) if 'from directorate_packages' in s)
    report=next(i for i,s in enumerate(locks) if 'from activity_reports' in s)
    assert 0<department<package_lock<report


@pytest.mark.parametrize('foundation_db',['486dfab71523'],indirect=True)
def test_populated_pre_s3a_upgrade_preserves_all_history(foundation_db,people,released,ready):
    import os,sys,subprocess
    from tests.test_authorization_foundation import ROOT
    db=foundation_db;x=people;r=released;p,rev,q,g=ready
    tables=('report_candidates','report_candidate_states','report_releases','report_artifacts','activity_report_revisions',
            'activity_report_approvals','actual_revisions','report_indicators','package_revisions','package_decisions',
            'revision_requests','revision_request_states','revision_correction_cycles','revision_edit_grants','workflow_events')
    before={t:[dict(row) for row in db.execute(text(f'SELECT * FROM {t} ORDER BY 1')).mappings()] for t in tables};db.commit()
    for _ in range(2):
        result=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,
            env={**os.environ,'DATABASE_URL':db.get_bind().url.render_as_string(hide_password=False)},capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    for t,rows in before.items():assert [dict(row) for row in db.execute(text(f'SELECT * FROM {t} ORDER BY 1')).mappings()]==rows
    assert db.scalar(select(func.count(ReportReleaseSuccession.id)))==0
    c=assemble(db,x,r,p);db.commit();assert reports.verify(db,c)['predecessor_release_id']==r.id


@pytest.mark.parametrize('cls',[ReportRelease,ReportCandidate,ReportArtifact,ActivityReportApproval,ActivityReportRevision,ActualRevision,PackageRevision])
@pytest.mark.parametrize('operation',['UPDATE','DELETE'])
def test_predecessor_sql_history_remains_immutable(foundation_db,people,released,ready,cls,operation):
    db=foundation_db;x=people;r=released;p,rev,q,g=ready;assemble(db,x,r,p);db.commit()
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(text(f'DELETE FROM {cls.__tablename__}' if operation=='DELETE' else f'UPDATE {cls.__tablename__} SET id=id'))


def test_sql_successor_fork_rejected(foundation_db,people,released,ready):
    db=foundation_db;x=people;r=released;p,rev,q,g=ready;c=assemble(db,x,r,p);db.commit()
    values={col.name:getattr(c,col.name) for col in ReportCandidate.__table__.columns if col.name not in ('id','created_at')}
    values['sequence']+=1
    before=counts(db)
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(insert(ReportCandidate).values(**values))
    assert counts(db)==before
