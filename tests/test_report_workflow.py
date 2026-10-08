"""Real migrated PostgreSQL Phase 4; both resource scopes and real connections."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import json
import os
import subprocess
import sys
from decimal import Decimal
import pytest
from fastapi import HTTPException
from sqlalchemy import select,func,text,event
from sqlalchemy.orm import Session
from sqlalchemy.exc import DBAPIError
from app.models import *
from app import report_workflow_service as service, authorization_service as auth, activity_contract_service as contract
from tests.test_package_workflow import foundation_db,people,package,act,submit
from tests.test_authorization_foundation import ROOT
pytestmark=pytest.mark.postgres

@pytest.fixture
def approved(foundation_db,people,package):
    db=foundation_db;x=people;p=package
    submit(db,x,p);act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    if p.resource_scope=='performance_program':db.add(ReportSection(period_id=p.period_id,title='Genel Bilgiler',kind='text',content_json='{}'))
    auth.assign_final_authority(db,x['strategy'],p.organization_id,x['director'].id,'Nihai yetki yazısı');db.commit()
    return p

@pytest.fixture
def candidate(foundation_db,people,approved):
    db=foundation_db;x=people;p=approved
    c=service.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,int(p.source_key),[p.id]);db.commit();return c

def review(db,x,c):
    state=db.get(ReportCandidateState,c.id)
    service.request_final_review(db,x['strategy'],c.organization_id,c.id,state.version,c.sha256);db.commit()

def approve(db,x,c,key='director'):
    state=db.get(ReportCandidateState,c.id)
    d=service.final_decision(db,x[key],c.organization_id,c.id,'final_approve',state.version,c.sha256);db.commit();return d

def publish(db,x,c,key='strategy'):
    state=db.get(ReportCandidateState,c.id)
    r=service.publish(db,x[key],c.organization_id,c.id,state.version,c.sha256);db.commit();return r

def rejects(code,fn):
    with pytest.raises(HTTPException) as caught:fn()
    assert caught.value.status_code==code

@pytest.mark.parametrize('bad',['missing','duplicate','cross_report','not_approved','stale'])
def test_candidate_bad_packages(foundation_db,people,approved,bad):
    db=foundation_db;x=people;p=approved;source=int(p.source_key);ids=[p.id]
    if bad=='missing':ids=[]
    elif bad=='duplicate':ids=[p.id,p.id]
    elif bad=='cross_report':source+=999
    elif bad=='not_approved':service.packages.move(db,p,p.version,'director_review',p.current_revision);db.commit()
    else:service.packages.move(db,p,p.version,p.state,p.current_revision+1);db.commit()
    rejects(403 if bad=='cross_report' and p.resource_scope=='activity_report' else 409,lambda:service.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,source,ids))
    assert db.scalar(select(func.count(ReportCandidate.id)))==0

def test_candidate_exact_manifest_and_no_early_freeze(foundation_db,people,candidate,approved):
    db=foundation_db;c=candidate;p=approved;m=json.loads(c.manifest_json)
    rev=service.packages.revision(db,p);d=db.scalar(select(PackageDecision).where(PackageDecision.action=='strategy_approve'))
    assert m['packages'][0]['revision_id']==rev.id and m['packages'][0]['sha256']==rev.sha256
    assert m['packages'][0]['decision_id']==d.id and m['packages'][0]['strategy_event_id']==d.workflow_event_id
    assert db.scalar(select(func.count(ActivityReportApproval.id)))==0
    if c.resource_scope=='performance_program':
        assert db.scalar(select(func.count(Publication.id)))==0
        assert 'validation_context' not in c.payload_json
    assert service.hash_content(c.payload_json,c.manifest_json)==c.sha256

@pytest.mark.parametrize('table',['report_candidates','candidate_packages'])
@pytest.mark.parametrize('operation',['update','delete'])
def test_candidate_history_sql_immutable(foundation_db,candidate,table,operation):
    db=foundation_db
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(text(f'DELETE FROM {table}' if operation=='delete' else f'UPDATE {table} SET sha256=sha256'))

def test_only_assigned_final_authority_and_private_scope(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate;review(db,x,c)
    for key in ('strategy','user'):
        rejects(403,lambda:approve(db,x,c,key))
    rejects(403,lambda:service.candidate_detail(db,x['user'],c.organization_id,c.id))
    rejects(403,lambda:service.candidate_detail(db,x['strategy'],c.organization_id+999,c.id))
    d=approve(db,x,c);assert d.candidate_sha256==c.sha256
    assert db.get(FinalAuthorityAssignment,d.assignment_id).user_id==x['director'].id

def test_return_terminal_and_new_predecessor(foundation_db,people,candidate,approved):
    db=foundation_db;x=people;c=candidate;review(db,x,c);state=db.get(ReportCandidateState,c.id)
    rejects(422,lambda:service.final_decision(db,x['director'],c.organization_id,c.id,'final_return',state.version,c.sha256,''))
    service.final_decision(db,x['director'],c.organization_id,c.id,'final_return',state.version,c.sha256,'Kaynağı tekrar inceleyin');db.commit()
    rejects(403,lambda:approve(db,x,c))
    new=service.assemble_candidate(db,x['strategy'],c.organization_id,c.resource_scope,int(approved.source_key),[approved.id],c.id);db.commit()
    assert new.predecessor_candidate_id==c.id and new.sequence==2
    assert service.candidate_detail(db,x['strategy'],c.organization_id,c.id)['state']=='returned_to_strategy'

def test_stale_decision(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate;review(db,x,c);state=db.get(ReportCandidateState,c.id)
    rejects(409,lambda:service.final_decision(db,x['director'],c.organization_id,c.id,'final_approve',state.version,'0'*64))
    rejects(409,lambda:service.final_decision(db,x['director'],c.organization_id,c.id,'final_approve',state.version-1,c.sha256))

def test_authority_change_new_decision_same_candidate(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate;review(db,x,c);first=approve(db,x,c)
    payload=c.payload_json;oldfreeze=first.activity_approval_id
    auth.assign_final_authority(db,x['strategy'],c.organization_id,x['editor2'].id,'Yeni resmî atama');db.commit()
    rejects(409,lambda:publish(db,x,c))
    rejects(403,lambda:approve(db,x,c))
    second=approve(db,x,c,'editor2')
    assert second.assignment_id!=first.assignment_id and second.activity_approval_id==oldfreeze
    assert db.get(ReportDecision,first.id).candidate_sha256==c.sha256 and c.payload_json==payload
    release=publish(db,x,c);assert release.final_decision_id==second.id

def test_publish_needs_final_approval_strategy_only(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate
    rejects(403,lambda:publish(db,x,c));review(db,x,c);rejects(403,lambda:publish(db,x,c))
    approve(db,x,c);rejects(403,lambda:publish(db,x,c,'director'));publish(db,x,c)

def test_release_exact_target_bytes_and_idempotency(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate;before=c.payload_json
    x['indicator'].name='Live mutation';db.scalar(select(IndicatorValue)).value=Decimal('999');x['card'].goal='Live goal';db.commit()
    review(db,x,c);d=approve(db,x,c);r=publish(db,x,c)
    assert bool(r.publication_id)!=bool(r.activity_approval_id)
    if r.publication_id:
        pub=db.get(Publication,r.publication_id);assert pub.snapshot_json==before and pub.sha256==c.payload_sha256
        bindings=db.scalars(select(PublicationIndicatorBinding).where(PublicationIndicatorBinding.publication_id==pub.id)).all()
        assert {b.definition_revision_id for b in bindings}=={row['definition_revision_id'] for row in contract.snapshot_rows(json.loads(before)).values()}
    else:
        freeze=db.get(ActivityReportApproval,r.activity_approval_id);assert freeze.report_revision_id==c.activity_revision_id
        assert d.activity_approval_id==freeze.id and freeze.created_by==x['director'].id
    artifact=service.verify_artifact(db,r)
    assert artifact.sha256==contract.digest(artifact.content_json) and artifact.byte_size==len(artifact.content_json.encode('utf8'))
    assert json.loads(artifact.content_json)['payload']==json.loads(before)
    assert publish(db,x,c).id==r.id
    assert db.scalar(select(func.count(ReportRelease.id)))==1

def test_activity_package_values_not_latest_source(foundation_db,people,approved):
    db=foundation_db;x=people;p=approved
    if p.resource_scope=='activity_report':
        ri=db.scalar(select(ReportIndicator).where(ReportIndicator.report_revision_id==int(p.source_key)))
        contract.save_actual(db,x['user'],ri.id,1,'9.75','verified',[{'title':'New','locator':'s2','source_revision':'r2'}],'Later live value',{});db.commit()
    else:db.scalar(select(IndicatorValue)).value=Decimal('9.75');db.commit()
    c=service.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,int(p.source_key),[p.id]);db.commit()
    if p.resource_scope=='activity_report':
        payload=json.loads(c.payload_json);e=payload['entries'][0]
        assert Decimal(e['value'])==Decimal('1.75')
        assert db.get(ActualRevision,e['materialized_actual_revision_id']).value==Decimal('1.75')
        with pytest.raises(DBAPIError):
            with db.begin_nested():contract.save_actual(db,x['user'],e['materialized_report_indicator_id'],1,'8.75','needs_review',[],'',{})
    else:assert Decimal(json.loads(c.payload_json)['departments'][0]['indicators'][0]['values'][0]['value'])==Decimal('1.75')

@pytest.mark.parametrize('table',['report_decisions','report_releases','report_artifacts'])
@pytest.mark.parametrize('operation',['update','delete'])
def test_final_history_sql_immutable(foundation_db,people,candidate,table,operation):
    db=foundation_db;x=people;c=candidate;review(db,x,c);approve(db,x,c);publish(db,x,c)
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(text(f'DELETE FROM {table}' if operation=='delete' else f'UPDATE {table} SET id=id'))

@pytest.mark.parametrize('failure',['WorkflowEvent','NotificationRecipient','ReportArtifact'])
def test_publish_atomic_failure(foundation_db,people,candidate,failure):
    db=foundation_db;x=people;c=candidate;review(db,x,c);approve(db,x,c)
    counts={cls:db.scalar(select(func.count(cls.id))) for cls in (Publication,ReportRelease,ReportArtifact,WorkflowEvent,NotificationRecipient)}
    def fail(*args):raise RuntimeError('mandatory failure')
    cls=globals()[failure];event.listen(cls,'before_insert',fail)
    try:
        with pytest.raises(RuntimeError):publish(db,x,c)
    finally:event.remove(cls,'before_insert',fail)
    db.expire_all();assert db.get(ReportCandidateState,c.id).state=='final_approved'
    for cls,count in counts.items():assert db.scalar(select(func.count(cls.id)))==count


def test_concurrent_publish_one_release(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate;review(db,x,c);approve(db,x,c)
    v=db.get(ReportCandidateState,c.id).version;uid=x['strategy'].id;org=c.organization_id;cid=c.id;sha=c.sha256;db.commit();barrier=Barrier(2)
    def run(_):
        with Session(db.get_bind(),expire_on_commit=False) as s:
            actor=s.get(User,uid);barrier.wait()
            try:r=service.publish(s,actor,org,cid,v,sha);s.commit();return r.id
            except HTTPException as exc:s.rollback();return -exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,(0,1)))
    assert sum(r>0 for r in results)==1 and -409 in results
    db.expire_all();assert db.scalar(select(func.count(ReportRelease.id)))==1
    if c.resource_scope=='performance_program':assert db.scalar(select(func.count(Publication.id)))==1


def test_unknown_actions_disabled_runtime(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate
    assert not auth.report_workflow_eligibility(db,x['strategy'],'unknown',c.organization_id)
    assert not auth.can(db,x['strategy'],'publish_report',c.organization_id,resource_scope=c.resource_scope)
    rejects(403,lambda:service.final_decision(db,x['strategy'],c.organization_id,c.id,'unknown',0,c.sha256))

@pytest.mark.parametrize('foundation_db',['153acbd48290'],indirect=True)
def test_populated_phase3_upgrade_exact(foundation_db,people,package):
    db=foundation_db;x=people;p=package
    submit(db,x,p);act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    tables=('directorate_packages','package_revisions','package_decisions','workflow_events','publications','activity_report_revisions','actual_revisions','indicator_definition_revisions')
    before={t:[dict(r) for r in db.execute(text(f'SELECT * FROM {t} ORDER BY id')).mappings()] for t in tables};db.commit()
    for _ in range(2):
        result=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env={**os.environ,'DATABASE_URL':db.get_bind().url.render_as_string(hide_password=False)},capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    for t,rows in before.items():assert [dict(r) for r in db.execute(text(f'SELECT * FROM {t} ORDER BY id')).mappings()]==rows
    for cls in (ReportCandidate,ReportDecision,ReportRelease,ReportArtifact):assert db.scalar(select(func.count(cls.id)))==0

@pytest.mark.parametrize('target',['candidate','package','artifact'])
def test_tampered_hash_fails_closed(foundation_db,people,candidate,target):
    from sqlalchemy.orm.attributes import set_committed_value
    db=foundation_db;x=people;c=candidate
    # Simulate corrupted fetched bytes without weakening DB triggers or rewriting history.
    if target=='candidate':
        set_committed_value(c,'sha256','0'*64)
        rejects(409,lambda:service.candidate_detail(db,x['strategy'],c.organization_id,c.id))
    elif target=='package':
        b=db.scalar(select(CandidatePackage));r=db.get(PackageRevision,b.package_revision_id)
        set_committed_value(r,'sha256','0'*64)
        rejects(409,lambda:service.candidate_detail(db,x['strategy'],c.organization_id,c.id))
    else:
        review(db,x,c);approve(db,x,c);r=publish(db,x,c);a=service.verify_artifact(db,r)
        set_committed_value(a,'sha256','0'*64)
        rejects(409,lambda:publish(db,x,c))
    db.expire_all()

@pytest.mark.parametrize('cls',[ReportCandidate,ReportDecision,ReportRelease,ReportArtifact])
@pytest.mark.parametrize('operation',['update','delete'])
def test_report_history_orm_immutable(foundation_db,people,candidate,cls,operation):
    db=foundation_db;x=people;c=candidate;review(db,x,c);approve(db,x,c);publish(db,x,c)
    row=db.scalar(select(cls))
    with pytest.raises(ValueError):
        with db.begin_nested():
            if operation=='delete':db.delete(row)
            else:
                if cls==ReportCandidate:row.payload_json='tampered'
                elif cls==ReportDecision:row.candidate_sha256='0'*64
                elif cls==ReportRelease:row.major=2
                else:row.content_json='tampered'
            db.flush()

@pytest.mark.parametrize('failure',[WorkflowEvent,NotificationRecipient,ReportDecision])
def test_final_approval_failure_rolls_back_freeze(foundation_db,people,candidate,failure):
    db=foundation_db;x=people;c=candidate;review(db,x,c)
    before={cls:db.scalar(select(func.count(cls.id))) for cls in (ActivityReportApproval,ReportDecision,WorkflowEvent,NotificationRecipient)}
    def fail(*args):raise RuntimeError('mandatory failure')
    event.listen(failure,'before_insert',fail)
    try:
        with pytest.raises(RuntimeError):approve(db,x,c)
    finally:event.remove(failure,'before_insert',fail)
    db.expire_all();assert db.get(ReportCandidateState,c.id).state=='final_review'
    for cls,count in before.items():assert db.scalar(select(func.count(cls.id)))==count


def test_required_extra_department_and_wrong_period(foundation_db,people,approved):
    db=foundation_db;x=people;p=approved
    if p.resource_scope=='performance_program':
        d=Department(organization_id=p.organization_id,name='Eksik birim');db.add(d);db.flush()
        db.add(DepartmentScope(period_id=p.period_id,department_id=d.id,status='required'));db.commit()
        rejects(409,lambda:service.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,int(p.source_key),[p.id]))
    else:
        rejects(404,lambda:service.assemble_candidate(db,x['strategy'],p.organization_id+999,p.resource_scope,int(p.source_key),[p.id]))


def test_formally_assigned_strategy_cannot_release(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate
    auth.assign_final_authority(db,x['strategy'],c.organization_id,x['strategy'].id,'Ayrı resmî nihai görevlendirme');db.commit()
    review(db,x,c);approve(db,x,c,'strategy')
    rejects(403,lambda:publish(db,x,c))


def test_assembly_failure_rolls_back_materialization_and_definitions(foundation_db,people,approved):
    db=foundation_db;x=people;p=approved
    classes=(ReportCandidate,ReportCandidateState,CandidatePackage,ActivityReportRevision,ActualRevision,IndicatorDefinitionRevision,WorkflowEvent)
    counts={cls:db.scalar(select(func.count(list(cls.__table__.primary_key)[0]))) for cls in classes}
    report=db.get(ActivityReport,db.get(ActivityReportRevision,int(p.source_key)).report_id) if p.resource_scope=='activity_report' else None
    old_revision=report.current_revision if report else None
    def fail(*args):raise RuntimeError('mandatory candidate notice failure')
    event.listen(NotificationRecipient,'before_insert',fail)
    try:
        with pytest.raises(RuntimeError):service.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,int(p.source_key),[p.id])
    finally:event.remove(NotificationRecipient,'before_insert',fail)
    db.expire_all()
    for cls,count in counts.items():assert db.scalar(select(func.count(list(cls.__table__.primary_key)[0])))==count
    if report:assert report.current_revision==old_revision


def test_existing_source_history_byte_stable(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate
    classes=(Publication,IndicatorDefinitionRevision,ActivityReportRevision,ActualRevision,PackageRevision,PackageDecision)
    before={cls:{r.id:{column.name:getattr(r,column.name) for column in cls.__table__.columns} for r in db.scalars(select(cls))} for cls in classes}
    review(db,x,c);approve(db,x,c);publish(db,x,c)
    for cls,rows in before.items():
        for key,expected in rows.items():assert {column.name:getattr(db.get(cls,key),column.name) for column in cls.__table__.columns}==expected


def test_candidate_state_no_unaudited_update(foundation_db,candidate):
    db=foundation_db
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(text("UPDATE report_candidate_states SET state='final_approved',version=version+1"))
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(text('DELETE FROM report_candidate_states'))
