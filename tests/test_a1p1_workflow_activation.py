"""A1-P1 workflow-activation blockers on migrated PostgreSQL: F1, F2, F3, F5 and K-7."""
import json
import os
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select, func, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from app.models import *
from app import (report_workflow_service as reports, revision_workflow_service as corrections, authorization_service as auth,
                 activity_contract_service as contract, package_service as packages)
from tests.test_authorization_foundation import foundation_db, ROOT, member, grant as delegate
from tests.test_materialized_successor import people, package, ready, assemble, counts, sealed, assert_sealed
from tests.test_report_workflow import approved, candidate, review, approve, publish, rejects
from tests.test_revision_workflow import released, request, accept, grant, edit
from tests.test_package_workflow import act
from tests.test_successor_publication import raw_release
pytestmark=pytest.mark.postgres

from app.main import migration_head
HEAD = migration_head()
DEVIATION=['entries',0,'deviation']


def state(db,c):return db.get(ReportCandidateState,c.id,populate_existing=True)


def final_return(db,x,c,key='director',reason='Nihai kaynak incelemesi sonrası iade'):
    s=state(db,c);d=reports.final_decision(db,x[key],c.organization_id,c.id,'final_return',s.version,c.sha256,reason);db.commit();return d


def package_of(db,g):return db.get(DirectoratePackage,db.get(RevisionCorrectionCycle,g.cycle_id).package_id)


def source_content(db,g):
    cycle=db.get(RevisionCorrectionCycle,g.cycle_id)
    return json.loads(db.get(PackageRevision,cycle.source_package_revision_id).content_json)


def reapprove(db,x,p,key='user'):
    act(db,x,p,'submit_to_director',key);act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')


def deviation_request(db,x,r):
    q=corrections.create_request(db,x['user'],r.id,x['department'].id,[{'path':DEVIATION}],'Düzeltici işlem düzeltmesi');db.commit();return q


def edit_deviation(db,x,g,**changes):
    p=package_of(db,g);rev=packages.revision(db,p);value=dict(json.loads(rev.content_json)['entries'][0]['deviation'],**changes)
    new=corrections.edit_under_grant(db,x['user'],g.id,p.version,rev.sha256,[{'path':DEVIATION,'value':value}]);db.commit();return new


def raw(db,sql,**params):
    """Trigger-free write, only to forge legacy/inconsistent data in this disposable schema."""
    db.execute(text('SET session_replication_role=replica'))
    try:db.execute(text(sql),params)
    finally:db.execute(text('SET session_replication_role=origin'))
    db.commit()


def wait_past(db,moment):
    db.execute(text('SELECT pg_sleep(:delay)'),{'delay':max(0,(moment-auth.server_now(db)).total_seconds())+0.05});db.commit()


def short_grant(db,x,q,key='user',seconds=4):
    s=db.get(RevisionRequestState,q.id);now=auth.server_now(db);m=auth.active_membership(db,x[key].id,q.organization_id,q.department_id)
    g=corrections.open_grant(db,x['strategy'],q.id,s.version,corrections.paths(q),[m.id],now-timedelta(seconds=1),now+timedelta(seconds=seconds),'Kısa asli izin')
    db.commit();return g


def renewals(db):return db.scalar(select(func.count(RevisionEditGrantRenewal.id)))


# ---------------------------------------------------------------- F1

@pytest.mark.parametrize('mix',['single','mixed'])
def test_f1_net_zero_participant_rejected_before_any_write(foundation_db,people,released,mix):
    db=foundation_db;x=people;r=released;q=request(db,x,r);accept(db,x,q);g=grant(db,x,q);source=source_content(db,g)
    if mix=='mixed':
        other=request(db,x,r,other=True);accept(db,x,other);h=grant(db,x,other);edit(db,x,g)
        edit(db,x,h,other=True,value='Geçici açıklama');edit(db,x,h,other=True,value=source['entries'][0]['explanation']);empty=other
    else:
        edit(db,x,g);edit(db,x,g,value=source['entries'][0]['value']);empty=q
    p=package_of(db,g);reapprove(db,x,p);before=counts(db)
    with pytest.raises(HTTPException) as caught:assemble(db,x,r,p)
    assert caught.value.status_code==409 and f'#{empty.id}' in caught.value.detail and 'değişikliksiz kapat' in caught.value.detail
    if mix=='mixed':assert f'#{q.id}' not in caught.value.detail
    db.rollback();assert counts(db)==before


def test_f1_database_refuses_net_zero_successor_at_commit(foundation_db,people,released,monkeypatch):
    db=foundation_db;x=people;r=released;q=request(db,x,r);accept(db,x,q);g=grant(db,x,q)
    edit(db,x,g);edit(db,x,g,value=source_content(db,g)['entries'][0]['value'])
    p=package_of(db,g);reapprove(db,x,p);before=counts(db)
    monkeypatch.setattr(reports,'successor_participation_gate',lambda *args:None)
    with pytest.raises(DBAPIError,match='Successor participant has no semantic net correction'):
        assemble(db,x,r,p);db.commit()
    db.rollback();assert counts(db)==before


@pytest.mark.parametrize('stage',['assembling','final_review','final_approved'])
def test_f1_close_rejected_while_live_successor_lists_request(foundation_db,people,released,stage,monkeypatch):
    db=foundation_db;x=people;r=released;q=request(db,x,r);other=request(db,x,r,other=True)
    accept(db,x,q);accept(db,x,other);g=grant(db,x,q);h=grant(db,x,other);edit(db,x,g);edit(db,x,h,other=True,value='Yeni açıklama')
    p=package_of(db,g);reapprove(db,x,p);c=assemble(db,x,r,p);db.commit()
    if stage!='assembling':review(db,x,c)
    if stage=='final_approved':approve(db,x,c)
    s=db.get(RevisionRequestState,other.id);before=(s.state,s.version)
    with pytest.raises(HTTPException) as caught:corrections.close_no_change(db,x['strategy'],other.id,s.version,'Net değişiklik yok')
    assert caught.value.status_code==409 and f'#{c.id}' in caught.value.detail and 'iade' in caught.value.detail
    db.rollback()
    monkeypatch.setattr(corrections,'live_successor_listing',lambda db,request:None)
    with pytest.raises(DBAPIError,match='Live successor lists this correction request'):
        corrections.close_no_change(db,x['strategy'],other.id,s.version,'Net değişiklik yok')
    db.rollback();s=db.get(RevisionRequestState,other.id,populate_existing=True);assert (s.state,s.version)==before


def test_f1_final_approved_return_by_current_authority_keeps_history(foundation_db,people,released,ready):
    db=foundation_db;x=people;r=released;p=ready[0]
    c=assemble(db,x,r,p);db.commit();review(db,x,c);d=approve(db,x,c)
    freeze=db.get(ActivityReportApproval,d.activity_approval_id)
    frozen=[tuple(getattr(row,col.name) for col in row.__table__.columns) for row in (d,freeze)]
    s=state(db,c)
    rejects(422,lambda:reports.final_decision(db,x['director'],c.organization_id,c.id,'final_return',s.version,c.sha256,'   '))
    rejects(403,lambda:reports.final_decision(db,x['strategy'],c.organization_id,c.id,'final_return',s.version,c.sha256,'Strateji iadesi'))
    db.rollback();assert state(db,c).state=='final_approved'
    back=final_return(db,x,c)
    assert state(db,c).state=='returned_to_strategy' and back.action=='final_return' and back.activity_approval_id is None
    assert [tuple(getattr(row,col.name) for col in row.__table__.columns) for row in (db.get(ReportDecision,d.id),db.get(ActivityReportApproval,freeze.id))]==frozen
    event=db.get(WorkflowEvent,back.workflow_event_id);context=json.loads(event.context_json)
    assert event.actor_user_id==x['director'].id and event.reason.strip() and (context['from_state'],context['to_state'])==('final_approved','returned_to_strategy')
    assert reports.returned_attempt_proof(db,c,r)
    with pytest.raises(HTTPException):publish(db,x,c)
    db.rollback();s=state(db,c)
    with pytest.raises(HTTPException):  # terminal as an attempt: no fresh approval of the returned candidate
        reports.final_decision(db,x['director'],c.organization_id,c.id,'final_approve',s.version,c.sha256)
    db.rollback();assert db.scalar(select(func.count(ReportRelease.id)).where(ReportRelease.candidate_id==c.id))==0
    assert state(db,c).state=='returned_to_strategy'


def test_f1_final_approved_return_never_by_strategy_or_previous_authority(foundation_db,people,released,ready):
    db=foundation_db;x=people;r=released;p=ready[0]
    c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c)
    # A Strategy user that formally holds the assignment still cannot use the recovery exit.
    auth.assign_final_authority(db,x['strategy'],c.organization_id,x['strategy'].id,'Ayrı resmî nihai görevlendirme');db.commit()
    s=state(db,c)
    for key in ('director','strategy'):
        rejects(403,lambda:reports.final_decision(db,x[key],c.organization_id,c.id,'final_return',s.version,c.sha256,'İade'))
        db.rollback()
    assert state(db,c).state=='final_approved'


def test_f1_final_approved_return_by_new_current_authority(foundation_db,people,released,ready):
    db=foundation_db;x=people;r=released;p=ready[0]
    c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c)
    auth.assign_final_authority(db,x['strategy'],c.organization_id,x['editor2'].id,'Yeni nihai onaycı görevlendirmesi');db.commit()
    s=state(db,c)
    rejects(403,lambda:reports.final_decision(db,x['director'],c.organization_id,c.id,'final_return',s.version,c.sha256,'Eski yetkili iadesi'))
    db.rollback();back=final_return(db,x,c,key='editor2')
    assert state(db,c).state=='returned_to_strategy' and db.get(WorkflowEvent,back.workflow_event_id).actor_user_id==x['editor2'].id


def test_f1_rework_after_final_approved_return_needs_fresh_approval(foundation_db,people,released,ready):
    db=foundation_db;x=people;r=released;p,corrected,q,g=ready
    c=assemble(db,x,r,p);db.commit();review(db,x,c);old=approve(db,x,c);final_return(db,x,c)
    act(db,x,p,'strategy_reopen','strategy',reason='Nihai onay sonrası iade edilen aday için kaynak düzeltmesi')
    edit(db,x,g,'director',value='3.50',reason='İade sonrası düzeltme');reapprove(db,x,p,'director')
    b=assemble(db,x,r,p);db.commit();m=json.loads(b.manifest_json)
    assert (m['reworks_candidate_id'],m['reworks_candidate_sha256'])==(c.id,c.sha256) and b.activity_revision_id!=c.activity_revision_id
    review(db,x,b)
    with pytest.raises(HTTPException):publish(db,x,b)
    db.rollback()
    fresh=approve(db,x,b);freeze=db.get(ActivityReportApproval,fresh.activity_approval_id)
    assert fresh.id!=old.id and freeze.id!=old.activity_approval_id and freeze.report_revision_id==b.activity_revision_id and freeze.created_by==x['director'].id
    release=publish(db,x,b)
    assert release.final_decision_id==fresh.id and release.activity_approval_id==freeze.id and (release.major,release.minor)==(1,1)
    assert state(db,c).state=='returned_to_strategy' and db.get(RevisionRequestState,q.id).state=='applied'


def test_f1_published_candidate_cannot_be_returned(foundation_db,people,released):
    db=foundation_db;x=people;c=db.get(ReportCandidate,released.candidate_id);s=state(db,c)
    with pytest.raises(HTTPException):
        reports.final_decision(db,x['director'],c.organization_id,c.id,'final_return',s.version,c.sha256,'Yayın sonrası iade')
    db.rollback();assert state(db,c).state=='published'


@pytest.mark.parametrize('bad',['no_decision','strategy_authority','blank_reason'])
def test_f1_raw_final_approved_return_requires_current_authority_decision(foundation_db,people,released,ready,bad):
    db=foundation_db;x=people;r=released;p=ready[0]
    c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c)
    key='director'
    if bad=='strategy_authority':
        auth.assign_final_authority(db,x['strategy'],c.organization_id,x['strategy'].id,'Ayrı resmî nihai görevlendirme');db.commit();key='strategy'
    s=state(db,c)
    with pytest.raises(DBAPIError,match='Unaudited/invalid report state transition'):
        with db.begin_nested():
            e=reports.event_notice(db,x[key],c,'final_return','final_approved','returned_to_strategy',s.version+1,' ' if bad=='blank_reason' else 'Ham iade')
            if bad!='no_decision':
                db.add(ReportDecision(candidate_id=c.id,action='final_return',candidate_sha256=c.sha256,assignment_id=reports.assignment(db,c.organization_id).id,
                    workflow_event_id=e.id));db.flush()
            reports.move(db,s,'returned_to_strategy')
    db.rollback();assert state(db,c).state=='final_approved'


# ---------------------------------------------------------------- F2

def current(db,report_id):
    report=db.get(ActivityReport,report_id,populate_existing=True)
    revision=db.scalar(select(ActivityReportRevision).where(ActivityReportRevision.report_id==report.id,ActivityReportRevision.revision==report.current_revision))
    return report,revision,db.scalar(select(ReportIndicator).where(ReportIndicator.report_revision_id==revision.id).order_by(ReportIndicator.id))


def legacy_counts(db,report_id):
    report=db.get(ActivityReport,report_id,populate_existing=True)
    return (report.current_revision,report.lock_version)+tuple(db.scalar(select(func.count(cls.id))) for cls in (ActivityReportRevision,ActualRevision,ActivityReportApproval,ReportIndicator))


@pytest.fixture(params=['assembling','final_review','final_approved','returned','released'])
def managed(request,foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate
    if request.param!='assembling':review(db,x,c)
    if request.param in {'final_approved','released'}:approve(db,x,c)
    if request.param=='returned':final_return(db,x,c)
    if request.param=='released':publish(db,x,c)
    return request.param,c,db.get(ActivityReportRevision,c.activity_revision_id).report_id


def legacy_call(db,x,report_id,operation,via):
    report,revision,slot=current(db,report_id);user=x['user' if operation=='save_actual' else 'strategy']
    actual={'expected_revision':db.scalar(select(func.count(ActualRevision.id)).where(ActualRevision.report_indicator_id==slot.id)),
        'value':'8.75','state':'verified','evidence':[{'title':'Defter','locator':'s9','source_revision':'r9'}],'explanation':'Eski ekran','deviation':{}}
    if via=='service':
        if operation=='create_report_revision':
            return contract.create_report_revision(db,user,revision.publication_id,report.organization_id,report.id,report.current_revision,'Eski ekrandan revizyon')
        if operation=='save_actual':return contract.save_actual(db,user,slot.id,**actual)
        return contract.approve_report(db,user,revision.id)
    from app.main import app,require_user
    from app.db import get_db
    def database():yield db
    app.dependency_overrides[get_db]=database;app.dependency_overrides[require_user]=lambda:user
    try:
        with TestClient(app) as client:
            if operation=='create_report_revision':
                response=client.post('/api/activity-reports/revisions',json={'publication_id':revision.publication_id,'organization_id':report.organization_id,
                    'report_id':report.id,'expected_revision':report.current_revision,'revision_reason':'Eski ekrandan revizyon'})
            elif operation=='save_actual':response=client.post(f'/api/activity-reports/indicators/{slot.id}/actuals',json=actual)
            else:response=client.post(f'/api/activity-reports/revisions/{revision.id}/approve')
    finally:app.dependency_overrides.clear()
    raise HTTPException(response.status_code,response.json().get('detail'))


@pytest.mark.parametrize('via',['service','http'])
@pytest.mark.parametrize('operation',['create_report_revision','save_actual','approve_report'])
def test_f2_legacy_writes_refused_on_workflow_managed_report(foundation_db,people,managed,operation,via):
    db=foundation_db;x=people;stage,c,report_id=managed;before=legacy_counts(db,report_id)
    with pytest.raises(HTTPException) as caught:legacy_call(db,x,report_id,operation,via)
    assert caught.value.status_code==409 and 'iş akışı' in str(caught.value.detail)
    db.rollback();assert legacy_counts(db,report_id)==before


def test_f2_workflow_continues_after_refused_legacy_writes(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate;review(db,x,c);report_id=db.get(ActivityReportRevision,c.activity_revision_id).report_id
    for operation in ('create_report_revision','save_actual','approve_report'):
        with pytest.raises(HTTPException):legacy_call(db,x,report_id,operation,'service')
        db.rollback()
    d=approve(db,x,c);release=publish(db,x,c);freeze=db.get(ActivityReportApproval,release.activity_approval_id)
    assert d.activity_approval_id==freeze.id and freeze.created_by==x['director'].id and freeze.report_revision_id==c.activity_revision_id


def test_f2_pre_workflow_legacy_report_unchanged(foundation_db,people,approved):
    db=foundation_db;x=people;p=approved;report_id=db.get(ActivityReportRevision,int(p.source_key)).report_id
    report,revision,slot=current(db,report_id)
    # A report with no candidate or release keeps the full legacy write path.
    for item in db.scalars(select(ReportIndicator).where(ReportIndicator.report_revision_id==revision.id).order_by(ReportIndicator.id)):
        last=db.scalar(select(func.max(ActualRevision.revision)).where(ActualRevision.report_indicator_id==item.id)) or 0
        contract.save_actual(db,x['user'],item.id,last,'2.25','verified',[{'title':'Defter','locator':'s3','source_revision':'r3'}],'Güncel',{'corrective_action':'İzle'});db.commit()
    # The released flow now requires a separate Strategy director.
    strategy_department=Department(organization_id=x['department'].organization_id,name='Strateji Geliştirme Müdürlüğü')
    db.add(strategy_department);db.flush()
    approver=User(email='legacy-approver@example.invalid',full_name='Strateji Müdürü',role='strategy',
                  department_id=strategy_department.id,
                  position='director',password_hash='unused')
    db.add(approver);db.commit()
    approval=contract.approve_report(db,approver,revision.id);db.commit()
    assert approval.created_by==approver.id and db.scalar(select(func.count(ReportCandidate.id)))==0


def test_f2_legacy_revision_racing_assembly_never_deadlocks(foundation_db,people,approved):
    """REL-1: the legacy period lock must not deadlock the candidate insert's foreign-key lock."""
    db=foundation_db;x=people;p=approved;report_id=db.get(ActivityReportRevision,int(p.source_key)).report_id
    report,revision,slot=current(db,report_id);args=(revision.publication_id,report.organization_id,report.id,report.current_revision);db.commit()
    barrier=Barrier(2)
    def legacy():
        with Session(db.get_bind(),expire_on_commit=False) as other:
            barrier.wait(timeout=10)
            try:contract.create_report_revision(other,other.get(User,x['strategy'].id),*args,'Eş zamanlı eski revizyon');other.commit();return 'revised'
            except HTTPException as exc:other.rollback();return exc.status_code
    def assembly():
        with Session(db.get_bind(),expire_on_commit=False) as other:
            barrier.wait(timeout=10)
            try:reports.assemble_candidate(other,other.get(User,x['strategy'].id),p.organization_id,p.resource_scope,int(p.source_key),[p.id]);other.commit();return 'assembled'
            except HTTPException as exc:other.rollback();return exc.status_code
    for _ in range(3):
        with ThreadPoolExecutor(2) as pool:first,second=pool.submit(legacy),pool.submit(assembly);results=(first.result(),second.result())
        assert results[0]==409 and results[1] in ('assembled',409)  # a deadlock would surface as a DBAPIError here
        if results[1]=='assembled':break
    db.expire_all();c=db.scalar(select(ReportCandidate));assert c and db.get(ActivityReport,report_id).current_revision==db.get(ActivityReportRevision,c.activity_revision_id).revision


@pytest.mark.parametrize('stage',['assembling','released','returned','forged_candidate','forged_candidate_with_state'])
def test_f2_raw_revision_insert_on_managed_report_rejected(foundation_db,people,candidate,stage):
    db=foundation_db;x=people;c=candidate;forged=stage.startswith('forged')
    if stage=='released':review(db,x,c);approve(db,x,c);publish(db,x,c)
    if stage=='returned' or forged:review(db,x,c);final_return(db,x,c)  # only the deferred checks see this
    report,revision,slot=current(db,db.get(ActivityReportRevision,c.activity_revision_id).report_id);before=legacy_counts(db,report.id)
    # DB-1 (A1-P1) and WF-1 (A1-P1.1): even a lineage-valid forged rework row cannot launder the legacy revision,
    # without a workflow state (owner check) or with one but no audited assembly (completeness check).
    match='Initial Activity candidate is incomplete at commit' if stage=='forged_candidate_with_state' else 'Workflow-managed Activity report rejects legacy revision'
    with pytest.raises(DBAPIError,match=match):
        legacy=ActivityReportRevision(report_id=report.id,revision=report.current_revision+1,publication_id=revision.publication_id,
            publication_sha256=revision.publication_sha256,contract_version=revision.contract_version,previous_revision_id=revision.id,
            diff_json='[]',revision_reason='Ham eski revizyon',created_by=x['strategy'].id)
        db.add(legacy);db.flush()
        if forged:
            manifest=json.loads(c.manifest_json);manifest.update(reworks_candidate_id=c.id,reworks_candidate_sha256=c.sha256)
            mraw=reports.canonical(manifest)
            forgery=ReportCandidate(organization_id=c.organization_id,period_id=c.period_id,resource_scope='activity_report',report_key=c.report_key,
                sequence=c.sequence+1,predecessor_candidate_id=c.id,activity_revision_id=legacy.id,payload_json=c.payload_json,
                payload_sha256=c.payload_sha256,manifest_json=mraw,sha256=reports.hash_content(c.payload_json,mraw),created_by=x['strategy'].id)
            db.add(forgery);db.flush()  # the insert-time lineage guard accepts it
            if stage=='forged_candidate_with_state':db.add(ReportCandidateState(candidate_id=forgery.id,state='assembling',version=0));db.flush()
        db.commit()
    db.rollback();assert legacy_counts(db,report.id)==before


@pytest.mark.parametrize('target',['candidate_revision','source_revision'])
def test_f2_raw_approval_insert_rejected(foundation_db,people,candidate,target):
    db=foundation_db;x=people;c=candidate;review(db,x,c)
    revision_id=c.activity_revision_id if target=='candidate_revision' else db.get(ActivityReportRevision,c.activity_revision_id).previous_revision_id
    match='Candidate freeze requires the current final authority decision' if target=='candidate_revision' else 'Workflow-managed Activity report rejects legacy approval'
    for key in ('strategy','director'):
        with pytest.raises(DBAPIError,match=match):
            db.add(ActivityReportApproval(report_revision_id=revision_id,created_by=x[key].id));db.flush()
        db.rollback()
    assert db.scalar(select(func.count(ActivityReportApproval.id)))==0


def test_f2_final_decision_never_adopts_foreign_approval(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate;review(db,x,c)
    raw(db,'INSERT INTO activity_report_approvals (report_revision_id,created_by,created_at) VALUES (:r,:u,now())',r=c.activity_revision_id,u=x['strategy'].id)
    before=(db.scalar(select(func.count(ReportDecision.id))),db.scalar(select(func.count(WorkflowEvent.id))))
    with pytest.raises(HTTPException) as caught:approve(db,x,c)
    assert caught.value.status_code==409 and 'devralınmaz' in caught.value.detail
    db.rollback();assert state(db,c).state=='final_review'
    assert (db.scalar(select(func.count(ReportDecision.id))),db.scalar(select(func.count(WorkflowEvent.id))))==before


def test_f2_candidate_freeze_must_be_bound_to_its_decision_at_commit(foundation_db,people,candidate):
    db=foundation_db;x=people;c=candidate;review(db,x,c);s=state(db,c)
    with pytest.raises(DBAPIError,match='Candidate freeze is not bound to its final decision'):
        reports.event_notice(db,x['director'],c,'final_approve','final_review','final_approved',s.version+1)
        db.add(ActivityReportApproval(report_revision_id=c.activity_revision_id,created_by=x['director'].id));db.flush();db.commit()
    db.rollback();assert db.scalar(select(func.count(ActivityReportApproval.id)))==0


# ---------------------------------------------------------------- F3

def test_f3_corrective_action_only_is_net_applied_and_published(foundation_db,people,released):
    db=foundation_db;x=people;r=released;q=deviation_request(db,x,r);accept(db,x,q);g=grant(db,x,q)
    new=edit_deviation(db,x,g,corrective_action='Kaynak kurumla mutabakat yapılacak')
    cycle=db.get(RevisionCorrectionCycle,g.cycle_id)
    assert corrections.has_net_correction(db,q,g,cycle,new)
    p=package_of(db,g);reapprove(db,x,p);c=assemble(db,x,r,p);db.commit()
    assert db.scalar(select(func.civensa_successor_request_participates(c.id,q.id)))
    review(db,x,c);approve(db,x,c);release=publish(db,x,c)
    assert db.get(RevisionRequestState,q.id).state=='applied' and (release.major,release.minor)==(1,1)
    assert json.loads(c.payload_json)['entries'][0]['deviation']['corrective_action']=='Kaynak kurumla mutabakat yapılacak'


def test_f3_closed_request_whose_corrective_action_survives_blocks(foundation_db,people,released):
    db=foundation_db;x=people;r=released;q=request(db,x,r);d=deviation_request(db,x,r)
    accept(db,x,q);accept(db,x,d);g=grant(db,x,q);h=grant(db,x,d);edit(db,x,g)
    new=edit_deviation(db,x,h,corrective_action='Kapanan talebin metni')
    s=db.get(RevisionRequestState,d.id);corrections.close_no_change(db,x['strategy'],d.id,s.version,'Talep gereksiz');db.commit()
    p=package_of(db,g);reapprove(db,x,p);bound=packages.revision(db,p)
    assert corrections.closed_request_survives(db,d,h,db.get(RevisionCorrectionCycle,h.cycle_id),bound)
    # S3C-2 B2 unchanged: a surviving closed edit is refused at publication in both layers.
    c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c);before=counts(db)
    assert db.scalar(select(func.civensa_closed_request_survives(c.id,d.id)))
    rejects(409,lambda:publish(db,x,c))
    with pytest.raises(DBAPIError,match='closed_no_change request participates'):
        with db.begin_nested():raw_release(db,x,c)
    db.rollback();assert counts(db)==before and db.get(RevisionRequestState,q.id).state=='editing'


def test_f1_surviving_closed_edit_keeps_return_and_reopen_exit(foundation_db,people,released):
    """WF-1: closing an edited request must not strand the release; the returned candidate reopens the package."""
    db=foundation_db;x=people;r=released;q=request(db,x,r);accept(db,x,q);g=grant(db,x,q);edit(db,x,g,value='2.50')
    p=package_of(db,g);reapprove(db,x,p)
    s=db.get(RevisionRequestState,q.id);corrections.close_no_change(db,x['strategy'],q.id,s.version,'Değişiklik istenmiyor');db.commit()
    c=assemble(db,x,r,p);db.commit()
    assert json.loads(c.manifest_json)['correction_request_grants']==[]
    review(db,x,c);approve(db,x,c);rejects(409,lambda:publish(db,x,c));db.rollback()  # B2: refused at publication
    final_return(db,x,c,reason='Kapatılan talebin değeri geri alınacak')
    act(db,x,p,'strategy_reopen','strategy',reason='Kapatılan talebin değerini düzeltme')
    other=request(db,x,r);accept(db,x,other);h=grant(db,x,other);edit(db,x,h,value='3.50');reapprove(db,x,p)
    b=assemble(db,x,r,p);db.commit();review(db,x,b);approve(db,x,b);release=publish(db,x,b)
    assert (release.major,release.minor)==(1,1) and json.loads(b.manifest_json)['reworks_candidate_id']==c.id
    assert db.get(RevisionRequestState,other.id).state=='applied' and db.get(RevisionRequestState,q.id).state=='closed_no_change'


def test_f1_first_candidate_final_approved_return_needs_exact_decision(foundation_db,people,candidate):
    """WF-2, superseded by A1-P1.1 R10: an unpublished first candidate may be returned, but only with an exact authority decision."""
    db=foundation_db;x=people;c=candidate;review(db,x,c);approve(db,x,c);s=state(db,c)
    with pytest.raises(DBAPIError,match='Unaudited/invalid report state transition'):
        with db.begin_nested():
            e=reports.event_notice(db,x['director'],c,'final_return','final_approved','returned_to_strategy',s.version+1,'')
            db.add(ReportDecision(candidate_id=c.id,action='final_return',candidate_sha256=c.sha256,
                assignment_id=reports.assignment(db,c.organization_id).id,workflow_event_id=e.id));db.flush()
            reports.move(db,s,'returned_to_strategy')
    db.rollback();assert state(db,c).state=='final_approved'
    with pytest.raises(DBAPIError,match='Unaudited/invalid report state transition'):  # an audited event without the decision row
        with db.begin_nested():
            reports.event_notice(db,x['director'],c,'final_return','final_approved','returned_to_strategy',s.version+1,'Ham iade')
            reports.move(db,s,'returned_to_strategy')
    db.rollback();assert publish(db,x,c).major==1


def test_f1_returned_successor_is_not_shown_as_approved(foundation_db,people,released,ready):
    """SEC-1: the kept freeze is history; the legacy reader labels the returned attempt."""
    db=foundation_db;x=people;r=released;p=ready[0]
    c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c)
    data=contract.report_data(db,x['strategy'],c.activity_revision_id)
    assert data['approved'] and not data['returned_after_approval']
    final_return(db,x,c)
    data=contract.report_data(db,x['strategy'],c.activity_revision_id)
    assert data['approved'] and data['returned_after_approval']


def test_f1_closed_request_renewal_names_the_closure(foundation_db,people,released):
    db=foundation_db;x=people;q=request(db,x,released);accept(db,x,q);g=short_grant(db,x,q,seconds=2);wait_past(db,g.end_at)
    s=db.get(RevisionRequestState,q.id);corrections.close_no_change(db,x['strategy'],q.id,s.version,'Talep geri çekildi');db.commit()
    now=auth.server_now(db)
    with pytest.raises(HTTPException) as caught:
        corrections.renew_grant(db,x['strategy'],g.id,json.loads(g.paths_json),now,now+timedelta(hours=1),'Yenileme')
    assert caught.value.status_code==409 and 'değişikliksiz kapatıldı' in caught.value.detail
    db.rollback();assert renewals(db)==0


def test_f3_derived_only_difference_is_not_a_correction(foundation_db,people,released):
    db=foundation_db;x=people;r=released;q=deviation_request(db,x,r);accept(db,x,q);g=grant(db,x,q)
    # A client-supplied derived value is recomputed; with nothing else changed there is no edit at all.
    rejects(422,lambda:edit_deviation(db,x,g,delta='999999'))
    db.rollback()
    before=json.loads(packages.revision(db,package_of(db,g)).content_json);after=json.loads(json.dumps(before))
    after['entries'][0]['deviation'].update(delta='99.00',calculation_rule_version='difference-v2',achievement_percent='50')
    for path in (DEVIATION,DEVIATION+['delta'],DEVIATION+['achievement_percent']):assert not corrections.net_changed(before,after,path)


def test_f3_other_deviation_keys_are_not_correctable(foundation_db,people,released):
    db=foundation_db;x=people;r=released;q=deviation_request(db,x,r);accept(db,x,q);g=grant(db,x,q)
    rejects(422,lambda:edit_deviation(db,x,g,corrective_action='Geçerli',foo='Serbest anahtar'))
    db.rollback()
    p=package_of(db,g);cur=packages.revision(db,p);old=json.loads(cur.content_json);doc=json.loads(cur.content_json)
    doc['entries'][0]['deviation']['foo']='Serbest anahtar';body=auth.encode(doc);m=auth.active_membership(db,x['user'].id,q.organization_id,q.department_id)
    with pytest.raises(DBAPIError,match='Deviation field is not correctable'):
        with db.begin_nested():
            e=corrections.history(db,x['user'],q,'correction_edit',{'grant_id':g.id,'renewal_id':None,'membership_id':m.id,'package_id':p.id,
                'previous_revision_id':cur.id,'next_revision':cur.revision+1,'next_sha256':packages.digest(body)})
            for path in corrections.change_paths(old,doc):
                db.add(FieldChangeEvent(workflow_event_id=e.id,revision_request_id=q.id,field_key=auth.encode(path),field_type='json',
                    previous_json=auth.encode(corrections.value_at(old,path)),new_json=auth.encode(corrections.value_at(doc,path))))
            db.flush();packages.append_revision(db,p,x['user'],body,cur,'')
    db.rollback()


PARITY=[
    (DEVIATION,{'corrective_action':'A','delta':'1'},{'corrective_action':'A','delta':'2'},False),
    (DEVIATION,{'corrective_action':'A','delta':'1'},{'corrective_action':'B','delta':'1'},True),
    (DEVIATION,{'corrective_action':'A'},{'corrective_action':'A','calculation_rule_version':'difference-v1'},False),
    (DEVIATION+['delta'],'1','2',False),
    (DEVIATION+['target_definition_revision_id'],1,2,False),
    (DEVIATION+['corrective_action'],'A','B',True),
    (DEVIATION+['corrective_action'],None,'',True),
    (['entries',0,'value'],'1.50','1.5',False),
    (['entries',0,'value'],'1.500000','1.50',False),
    (['entries',0,'value'],None,'0',True),
    (['entries',0,'explanation'],'A','A',False),
]


@pytest.mark.parametrize('path,old,new,expected',PARITY)
def test_f3_python_and_postgresql_net_change_agree(foundation_db,path,old,new,expected):
    def doc(value):
        entry={'value':None,'explanation':'','deviation':{}}
        if len(path)==3:entry[path[2]]=value
        else:entry['deviation'][path[3]]=value
        return {'entries':[entry]}
    a,b=doc(old),doc(new)
    python=corrections.net_changed(a,b,path)
    # Same expression as civensa_successor_request_participates / civensa_closed_request_survives.
    pg=foundation_db.scalar(text("""SELECT NOT civensa_derived_deviation_key(CAST(:k AS jsonb)) AND CASE WHEN jsonb_array_length(CAST(:k AS jsonb))=3
        AND CAST(:k AS jsonb)->>0='entries' AND CAST(:k AS jsonb)->>2='value'
        THEN (CAST(:a AS jsonb) #>> ARRAY(SELECT jsonb_array_elements_text(CAST(:k AS jsonb))))::numeric IS DISTINCT FROM (CAST(:b AS jsonb) #>> ARRAY(SELECT jsonb_array_elements_text(CAST(:k AS jsonb))))::numeric
        ELSE civensa_net_value(CAST(:k AS jsonb),CAST(:a AS jsonb) #> ARRAY(SELECT jsonb_array_elements_text(CAST(:k AS jsonb))))
        IS DISTINCT FROM civensa_net_value(CAST(:k AS jsonb),CAST(:b AS jsonb) #> ARRAY(SELECT jsonb_array_elements_text(CAST(:k AS jsonb)))) END"""),
        {'k':json.dumps(path),'a':json.dumps(a),'b':json.dumps(b)})
    assert python==pg==expected


# ---------------------------------------------------------------- F5

def director_membership(db,x,key='director'):return auth.active_membership(db,x[key].id,x['department'].organization_id,x['department'].id)


def test_f5_director_replacement_ends_delegation_and_restores_primary_authority(foundation_db,people,package):
    db=foundation_db;x=people;p=package;g=delegate(db,x);original=tuple(getattr(g,c.name) for c in g.__table__.columns if c.name!='active')
    act(db,x,p,'submit_to_director','user');old=director_membership(db,x)
    auth.deactivate_membership(db,x['strategy'],old.id,'Müdür görev değişikliği');db.commit()
    db.expire_all();g=db.get(AuthorityDelegation,g.id)
    assert not g.active and tuple(getattr(g,c.name) for c in g.__table__.columns if c.name!='active')==original
    revocation=db.scalar(select(DelegationRevocation).where(DelegationRevocation.delegation_id==g.id))
    events=list(db.scalars(select(DelegationEvent).where(DelegationEvent.delegation_id==g.id).order_by(DelegationEvent.id)))
    assert revocation.reason.startswith('terminated_due_to_director_change') and revocation.actor_user_id==x['strategy'].id
    assert [e.event_type for e in events]==['granted','revoked'] and json.loads(events[1].context_json)['cause']=='terminated_due_to_director_change'
    assert auth.active_delegation(db,p.organization_id,p.department_id) is None
    rejects(403,lambda:act(db,x,p,'director_approve','user'));db.rollback()
    member(db,x,'editor3','department_director',3)
    act(db,x,p,'director_approve','editor3');assert p.state=='strategy_review'
    decision=db.scalar(select(PackageDecision).where(PackageDecision.action=='director_approve'));assert decision.delegation_id is None
    now=auth.server_now(db)
    fresh=auth.create_delegation(db,x['editor3'],p.organization_id,p.department_id,x['user'].id,now,now+timedelta(hours=2),'Yeni müdür vekâlet yazısı');db.commit()
    assert fresh.id!=g.id and fresh.director_membership_id==director_membership(db,x,'editor3').id
    assert (fresh.start_at,fresh.end_at,fresh.formal_basis)!=(g.start_at,g.end_at,g.formal_basis)
    rejects(403,lambda:auth.create_delegation(db,x['user'],p.organization_id,p.department_id,x['editor2'].id,now,now+timedelta(hours=1),'Yeniden devir'))


def test_f5_termination_is_atomic_with_deactivation(foundation_db,people,package):
    from sqlalchemy import event
    db=foundation_db;x=people;g=delegate(db,x);old=director_membership(db,x)
    def fail(*args):raise RuntimeError('mandatory delegation event failure')
    event.listen(DelegationEvent,'before_insert',fail)
    try:
        with pytest.raises(RuntimeError):auth.deactivate_membership(db,x['strategy'],old.id,'Müdür görev değişikliği')
    finally:event.remove(DelegationEvent,'before_insert',fail)
    db.rollback();db.expire_all()
    assert db.get(DirectorateMembership,old.id).active and db.get(AuthorityDelegation,g.id).active
    assert db.scalar(select(func.count(DelegationRevocation.id)))==0


def test_f5_raw_director_deactivation_with_live_delegation_refused(foundation_db,people,package):
    db=foundation_db;x=people;g=delegate(db,x);old=director_membership(db,x)
    with pytest.raises(DBAPIError,match='Director delegation must be terminated with the director membership'):
        with db.begin_nested():db.execute(text('UPDATE directorate_memberships SET active=false WHERE id=:id'),{'id':old.id})
    db.rollback();assert db.get(DirectorateMembership,old.id,populate_existing=True).active


def correction_package(db,x,r):
    q=request(db,x,r);accept(db,x,q);g=grant(db,x,q);edit(db,x,g);return package_of(db,g)


def test_f5_stale_active_delegation_of_inactive_director_fails_closed(foundation_db,people,released):
    db=foundation_db;x=people;p=correction_package(db,x,released);g=delegate(db,x);act(db,x,p,'submit_to_director','user')
    old=director_membership(db,x)
    raw(db,'UPDATE directorate_memberships SET active=false WHERE id=:id',id=old.id)
    db.expire_all();assert db.get(AuthorityDelegation,g.id).active
    assert auth.active_delegation(db,p.organization_id,p.department_id) is None
    rejects(403,lambda:act(db,x,p,'director_approve','user'));db.rollback()
    member(db,x,'editor3','department_director',3)
    # The PostgreSQL correction decision guard ignores the stale row as well.
    act(db,x,p,'director_approve','editor3');assert p.state=='strategy_review'
    now=auth.server_now(db)
    fresh=auth.create_delegation(db,x['editor3'],p.organization_id,p.department_id,x['user'].id,now,now+timedelta(hours=1),'Yeni müdür vekâlet yazısı');db.commit()
    db.expire_all();stale=db.get(AuthorityDelegation,g.id)
    assert not stale.active and fresh.active
    assert db.scalar(select(DelegationRevocation.reason).where(DelegationRevocation.delegation_id==g.id)).startswith('terminated_due_to_director_change')


def test_f5_concurrent_director_replacement_and_delegate_approval(foundation_db,people,package):
    db=foundation_db;x=people;p=package;g=delegate(db,x);act(db,x,p,'submit_to_director','user')
    old=director_membership(db,x);rev=packages.revision(db,p);version=p.version;db.commit();barrier=Barrier(2)
    def deactivate():
        with Session(db.get_bind(),expire_on_commit=False) as other:
            barrier.wait(timeout=10);auth.deactivate_membership(other,other.get(User,x['strategy'].id),old.id,'Müdür görev değişikliği');other.commit();return 'deactivated'
    def approve_as_delegate():
        with Session(db.get_bind(),expire_on_commit=False) as other:
            barrier.wait(timeout=10)
            try:packages.transition(other,other.get(User,x['user'].id),p.id,'director_approve',version,rev.sha256);other.commit();return 'approved'
            except HTTPException as exc:other.rollback();return exc.status_code
    with ThreadPoolExecutor(2) as pool:first,second=pool.submit(deactivate),pool.submit(approve_as_delegate);results=(first.result(),second.result())
    db.expire_all();decision=db.scalar(select(PackageDecision).where(PackageDecision.action=='director_approve'))
    revocation=db.scalar(select(DelegationRevocation).where(DelegationRevocation.delegation_id==g.id))
    assert results[0]=='deactivated' and results[1] in ('approved',403) and revocation and not db.get(AuthorityDelegation,g.id).active
    if results[1]=='approved':
        assert decision.delegation_id==g.id and db.get(WorkflowEvent,decision.workflow_event_id).created_at<revocation.created_at
        assert db.get(DirectoratePackage,p.id).state=='strategy_review'
    else:assert decision is None and db.get(DirectoratePackage,p.id).state=='director_review'


# ---------------------------------------------------------------- K-7

def test_k7_expiry_in_director_review_needs_no_renewal(foundation_db,people,released):
    db=foundation_db;x=people;q=request(db,x,released);accept(db,x,q);g=short_grant(db,x,q)
    rev=edit(db,x,g);p=package_of(db,g);act(db,x,p,'submit_to_director','user');wait_past(db,g.end_at)
    act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    assert p.state=='strategy_approved' and renewals(db)==0 and packages.revision(db,p).id==rev.id
    assert {d.snapshot_sha256 for d in db.scalars(select(PackageDecision).where(PackageDecision.package_revision_id==rev.id))}=={rev.sha256}


def test_k7_expiry_in_strategy_review_then_successor_publishes(foundation_db,people,released):
    db=foundation_db;x=people;r=released;q=request(db,x,r);accept(db,x,q);g=short_grant(db,x,q)
    rev=edit(db,x,g);p=package_of(db,g);act(db,x,p,'submit_to_director','user');act(db,x,p,'director_approve');wait_past(db,g.end_at)
    act(db,x,p,'strategy_approve','strategy');c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c);release=publish(db,x,c)
    assert renewals(db)==0 and db.get(RevisionRequestState,q.id).state=='applied' and (release.major,release.minor)==(1,1)
    assert json.loads(c.manifest_json)['packages'][0]['revision_id']==rev.id


def test_k7_edit_after_expiry_refused_in_both_layers(foundation_db,people,released,monkeypatch):
    db=foundation_db;x=people;q=request(db,x,released);accept(db,x,q);g=short_grant(db,x,q,seconds=2);wait_past(db,g.end_at)
    rejects(403,lambda:edit(db,x,g));db.rollback()
    monkeypatch.setattr(corrections,'effective_grant',lambda db,grant,now:grant)
    with pytest.raises(DBAPIError,match='Missing active scoped correction authorization/audit'):edit(db,x,g)
    db.rollback();assert renewals(db)==0


def test_k7_return_after_expiry_then_renewal_then_edit_and_publish(foundation_db,people,released):
    db=foundation_db;x=people;r=released;q=request(db,x,r);accept(db,x,q);g=short_grant(db,x,q)
    edit(db,x,g);p=package_of(db,g);act(db,x,p,'submit_to_director','user');wait_past(db,g.end_at)
    act(db,x,p,'director_return',reason='Kaynak belgesi eksik');assert p.state=='returned'
    rejects(403,lambda:edit(db,x,g,value='3.25'));db.rollback()
    original=tuple(getattr(g,c.name) for c in g.__table__.columns);now=auth.server_now(db)
    n=corrections.renew_grant(db,x['strategy'],g.id,json.loads(g.paths_json),now,now+timedelta(hours=1),'İade sonrası ek düzenleme izni');db.commit()
    edit(db,x,g,value='3.25')
    e=db.scalar(select(WorkflowEvent).where(WorkflowEvent.event_type=='correction_edit').order_by(WorkflowEvent.id.desc()))
    assert json.loads(e.context_json)['renewal_id']==n.id
    db.expire_all();assert tuple(getattr(db.get(RevisionEditGrant,g.id),c.name) for c in g.__table__.columns)==original
    reapprove(db,x,p);c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c);publish(db,x,c)
    assert json.loads(c.payload_json)['entries'][0]['value']=='3.25' and db.get(RevisionRequestState,q.id).state=='applied'


@pytest.mark.parametrize('forged',['before_grant','before_renewal'])
def test_k7_edit_outside_every_interval_cannot_pass_provenance(foundation_db,people,released,forged,monkeypatch):
    db=foundation_db;x=people;q=request(db,x,released);accept(db,x,q)
    if forged=='before_grant':g=grant(db,x,q);edit(db,x,g);moment='start'
    else:
        g=short_grant(db,x,q,seconds=2);edit(db,x,g);p=package_of(db,g);act(db,x,p,'submit_to_director','user');wait_past(db,g.end_at)
        act(db,x,p,'director_return',reason='Ek düzenleme');now=auth.server_now(db)
        n=corrections.renew_grant(db,x['strategy'],g.id,json.loads(g.paths_json),now,now+timedelta(hours=1),'Ek izin');db.commit();edit(db,x,g,value='3.25')
    p=package_of(db,g)
    e=db.scalar(select(WorkflowEvent).where(WorkflowEvent.event_type=='correction_edit').order_by(WorkflowEvent.id.desc()))
    if forged=='before_grant':raw(db,'UPDATE workflow_events SET created_at=:t WHERE id=:id',t=g.start_at-timedelta(seconds=1),id=e.id)
    else:raw(db,'UPDATE revision_edit_grant_renewals SET created_at=:t WHERE id=:id',t=e.created_at+timedelta(seconds=1),id=n.id)
    db.expire_all();before=db.scalar(select(func.count(PackageDecision.id)))
    with pytest.raises(HTTPException) as caught:act(db,x,p,'submit_to_director','user')
    assert caught.value.status_code==409 and 'izin' in caught.value.detail
    db.rollback()
    monkeypatch.setattr(corrections,'require_correction_authority',lambda *args:None)
    with pytest.raises(DBAPIError,match='Correction lineage is not historically authorized'):act(db,x,p,'submit_to_director','user')
    db.rollback();assert db.scalar(select(func.count(PackageDecision.id)))==before and db.get(DirectoratePackage,p.id,populate_existing=True).state=='returned'


def test_k7_edit_by_membership_deactivated_before_the_edit_is_not_authorized(foundation_db,people,released,monkeypatch):
    """TE-3 / K-7 F: the editing membership must not have been deactivated at or before the edit."""
    db=foundation_db;x=people;q=request(db,x,released);accept(db,x,q);g=grant(db,x,q);edit(db,x,g);p=package_of(db,g)
    e=db.scalar(select(WorkflowEvent).where(WorkflowEvent.event_type=='correction_edit').order_by(WorkflowEvent.id.desc()))
    raw(db,"""INSERT INTO membership_events (membership_id,actor_user_id,actor_snapshot_json,event_type,previous_json,new_json,reason,created_at)
        VALUES (:m,:a,'{}','deactivated','{}','{}','Sahte geçmiş',:t)""",m=json.loads(e.context_json)['membership_id'],a=x['strategy'].id,t=e.created_at-timedelta(seconds=1))
    before=db.scalar(select(func.count(PackageDecision.id)))
    with pytest.raises(HTTPException) as caught:act(db,x,p,'submit_to_director','user')
    assert caught.value.status_code==409 and 'izin' in caught.value.detail
    db.rollback();monkeypatch.setattr(corrections,'require_correction_authority',lambda *args:None)
    with pytest.raises(DBAPIError,match='Correction lineage is not historically authorized'):act(db,x,p,'submit_to_director','user')
    db.rollback();assert db.scalar(select(func.count(PackageDecision.id)))==before and db.get(DirectoratePackage,p.id,populate_existing=True).state=='returned'


def test_f2_materialize_rechecks_report_revision_under_lock(foundation_db,people,approved):
    """TE-4: a legacy write that committed after the caller's unlocked check never becomes a candidate base."""
    db=foundation_db;x=people;p=approved;source=db.get(ActivityReportRevision,int(p.source_key));report=db.get(ActivityReport,source.report_id)
    before=legacy_counts(db,report.id)
    with pytest.raises(HTTPException) as caught:
        reports.materialize(db,x['strategy'],source,[json.loads(packages.revision(db,p).content_json)],expected_revision=report.current_revision-1)
    assert caught.value.status_code==409
    db.rollback();assert legacy_counts(db,report.id)==before


def test_k7_review_after_closed_only_request_is_not_stranded(foundation_db,people,released):
    """WF-6: closing the cycle's only request must not freeze an already-submitted package."""
    db=foundation_db;x=people;q=request(db,x,released);accept(db,x,q);g=grant(db,x,q);edit(db,x,g)
    p=package_of(db,g);act(db,x,p,'submit_to_director','user')
    s=db.get(RevisionRequestState,q.id);corrections.close_no_change(db,x['strategy'],q.id,s.version,'Talep geri çekildi');db.commit()
    act(db,x,p,'director_return',reason='Değişiklik geri alınacak');assert p.state=='returned'


# ---------------------------------------------------------------- migration

def test_migration_functions_and_triggers_present(foundation_db):
    db=foundation_db
    assert db.execute(text('SELECT version_num FROM alembic_version')).scalar_one()==HEAD
    names={'civensa_derived_deviation_key','civensa_net_value','civensa_activity_report_managed','civensa_correction_edit_authorized',
        'civensa_correction_lineage_authorized','civensa_final_approved_return','civensa_activity_revision_owner_guard',
        'civensa_activity_approval_owner_guard','civensa_successor_participation_check','civensa_director_deactivation_guard'}
    assert names<=set(db.scalars(text('SELECT proname FROM pg_proc')))
    triggers=dict(db.execute(text("SELECT tgname,tgdeferrable FROM pg_trigger WHERE NOT tgisinternal")).all())
    assert triggers['activity_revision_owner'] and triggers['activity_approval_decision'] and triggers['activity_successor_participation']
    assert triggers['activity_revision_live_owner'] is False and triggers['activity_approval_owner'] is False and triggers['director_deactivation_delegation'] is False
    defs={name:db.scalar(text("SELECT pg_get_functiondef(CAST(:n AS regproc))"),{'n':name}) for name in
        ('report_state_guard','civensa_successor_request_participates','civensa_closed_request_survives','civensa_revision_projection_guard',
         'civensa_revision_edit_guard','civensa_renewal_guard','civensa_revision_state_guard','civensa_correction_decision_authorized','report_binding_guard')}
    assert 'civensa_final_approved_return' in defs['report_state_guard']
    assert all('civensa_derived_deviation_key' in defs[n] and '["deviation"]' not in defs[n] for n in ('civensa_successor_request_participates','civensa_closed_request_survives'))
    assert 'civensa_correction_lineage_authorized' in defs['civensa_revision_projection_guard'] and 'No active correction grant' not in defs['civensa_revision_projection_guard']
    assert 'Deviation field is not correctable' in defs['civensa_revision_edit_guard']
    assert 'civensa_live_successor' in defs['civensa_renewal_guard'] and 'civensa_latest_returned' not in defs['civensa_renewal_guard']
    assert 'Live successor lists this correction request' in defs['civensa_revision_state_guard']
    assert 'od.director_membership_id' not in defs['civensa_correction_decision_authorized'] and 'od.id=a.director_membership_id' in defs['civensa_correction_decision_authorized']
    assert 'a.active AND au.is_active' in defs['report_binding_guard']


@pytest.mark.parametrize('foundation_db',['e69c04e721a5'],indirect=True)
def test_populated_upgrade_keeps_history_and_refuses_downgrade(foundation_db,people,released,ready):
    db=foundation_db;x=people;p=ready[0];before=sealed(db);db.commit();url=db.bind.url.render_as_string(hide_password=False)
    for _ in range(2):
        run=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True)
        assert run.returncode==0,run.stderr
    down=subprocess.run([sys.executable,'-m','alembic','downgrade','c5e8a1f0b247'],cwd=ROOT,env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True)
    assert down.returncode!=0 and 'A1-P1.1 recovery guards cannot be discarded' in down.stderr
    db.expire_all();assert_sealed(db,before)
    assert db.execute(text('SELECT version_num FROM alembic_version')).scalar_one()==HEAD
    reports.verify(db,db.get(ReportCandidate,released.candidate_id));reports.verify_artifact(db,released)
    c=assemble(db,x,released,p);db.commit();review(db,x,c);approve(db,x,c);assert publish(db,x,c).minor==1


@pytest.mark.parametrize('foundation_db',['e69c04e721a5'],indirect=True)
def test_f1_preupgrade_net_zero_successor_still_blocked_at_publication(foundation_db,people,released,monkeypatch):
    """TE-1: a candidate assembled before c5e8a1f0b247 has only the publication guard left."""
    db=foundation_db;x=people;q=request(db,x,released);other=request(db,x,released,other=True)
    accept(db,x,q);accept(db,x,other);g=grant(db,x,q);grant(db,x,other);edit(db,x,g);p=package_of(db,g);reapprove(db,x,p)
    monkeypatch.setattr(reports,'successor_participation_gate',lambda *args:None)  # base behaviour before the gate existed
    c=assemble(db,x,released,p);db.commit();review(db,x,c);approve(db,x,c);monkeypatch.undo()
    url=db.bind.url.render_as_string(hide_password=False)
    run=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    db.expire_all();before=counts(db)
    rejects(409,lambda:publish(db,x,c))
    with pytest.raises(DBAPIError,match='Unresolved or unedited successor requests'):
        with db.begin_nested():raw_release(db,x,c)
    db.rollback();assert counts(db)==before and state(db,c).state=='final_approved'


@pytest.fixture
def sqlite_head(tmp_path):
    path=tmp_path/'a1p1.db'
    run=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env={**os.environ,'DATABASE_URL':f'sqlite:///{path}'},capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    db=sqlite3.connect(path);db.execute('PRAGMA foreign_keys=OFF');yield db;db.close()


def insert(db,table,**values):
    """Fill other NOT NULL columns with neutral values; this throwaway database only exercises triggers."""
    for _,name,kind,notnull,default,pk in db.execute(f'PRAGMA table_info({table})').fetchall():
        if notnull and default is None and not pk and name not in values:values[name]=0 if 'INT' in kind.upper() or 'BOOL' in kind.upper() else 'a'*64
    db.execute(f"INSERT INTO {table} ({','.join(values)}) VALUES ({','.join('?'*len(values))})",list(values.values()))
    return db.execute('SELECT last_insert_rowid()').fetchone()[0]


@pytest.mark.parametrize('owner',['none','live','returned','release'])
def test_sqlite_parity_guards(sqlite_head,owner):
    db=sqlite_head
    triggers={name for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
    assert {'activity_revision_owner','activity_approval_owner','director_deactivation_delegation','guard_delegation_update',
            'candidate_actual_seal','package_decision_binding','activity_successor_guard'}<=triggers
    report=insert(db,'activity_reports',organization_id=1,period_id=1,current_revision=1,lock_version=0)
    revision=insert(db,'activity_report_revisions',report_id=report,revision=1,publication_id=1,previous_revision_id=None)
    if owner in {'live','returned'}:
        c=insert(db,'report_candidates',organization_id=1,resource_scope='activity_report',report_key=str(report),activity_revision_id=revision,sequence=1,payload_json='{}',manifest_json='{}')
        insert(db,'report_candidate_states',candidate_id=c,state='assembling',version=0)
        # Throwaway database: drop only the candidate-state audit triggers so a state can be staged without a full workflow.
        for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='report_candidate_states'").fetchall():
            db.execute(f'DROP TRIGGER {name}')
        for state in ['final_review']+(['returned_to_strategy'] if owner=='returned' else []):
            db.execute('UPDATE report_candidate_states SET state=?,version=version+1 WHERE candidate_id=?',(state,c))
    if owner=='release':  # A1-P1.1: a release must carry its final decision's freeze, even in this throwaway database
        d=insert(db,'report_decisions',candidate_id=1,action='final_approve',activity_approval_id=1)
        insert(db,'report_releases',organization_id=1,resource_scope='activity_report',report_key=str(report),candidate_id=1,final_decision_id=d,activity_approval_id=1,major=1,minor=0)
    legacy=lambda:insert(db,'activity_report_revisions',report_id=report,revision=2,publication_id=1,previous_revision_id=revision)
    if owner in {'live','release'}:
        with pytest.raises(sqlite3.IntegrityError,match='Workflow-managed Activity report rejects legacy revision'):legacy()
    else:legacy()  # returned-only: the application layer refuses (no deferred trigger on SQLite)
    approval=lambda:insert(db,'activity_report_approvals',report_revision_id=revision,created_by=1)
    if owner=='none':approval()
    else:
        with pytest.raises(sqlite3.IntegrityError,match='Workflow-managed Activity report rejects legacy approval'):approval()


def test_sqlite_live_successor_listing_is_dialect_independent(sqlite_head,tmp_path):
    """SEC-3: close_no_change's live-successor check must not need JSONB (SQLite has no successors at all)."""
    from types import SimpleNamespace
    from sqlalchemy import create_engine
    db=sqlite_head;report=insert(db,'activity_reports',organization_id=1,period_id=1,current_revision=1,lock_version=0)
    revision=insert(db,'activity_report_revisions',report_id=report,revision=1,publication_id=1,previous_revision_id=None)
    with pytest.raises(sqlite3.IntegrityError,match='Successor requires PostgreSQL'):
        insert(db,'report_candidates',organization_id=1,resource_scope='activity_report',report_key=str(report),activity_revision_id=revision,
            sequence=1,payload_json='{}',manifest_json=json.dumps({'predecessor_release_id':5,'correction_request_grants':[{'request_id':7}]}))
    c=insert(db,'report_candidates',organization_id=1,resource_scope='activity_report',report_key=str(report),activity_revision_id=revision,
        sequence=1,payload_json='{}',manifest_json='{}')
    insert(db,'report_candidate_states',candidate_id=c,state='assembling',version=0);db.commit()
    engine=create_engine(f"sqlite:///{tmp_path/'a1p1.db'}")
    with Session(engine) as session:
        assert corrections.live_successor_listing(session,SimpleNamespace(id=7,organization_id=1,source_release_id=5)) is None
    engine.dispose()


def test_sqlite_director_deactivation_requires_termination(sqlite_head):
    db=sqlite_head
    director=insert(db,'directorate_memberships',organization_id=1,department_id=1,user_id=1,role_code='department_director',slot=3,active=1)
    insert(db,'authority_delegations',organization_id=1,department_id=1,director_membership_id=director,delegate_membership_id=99,active=1,
           start_at='2026-01-01',end_at='2099-01-01',formal_basis='Vekâlet')
    with pytest.raises(sqlite3.IntegrityError,match='Director delegation must be terminated with the director membership'):
        db.execute('UPDATE directorate_memberships SET active=0 WHERE id=?',(director,))
