"""A1-P1.1 pre-activation recovery paths on migrated PostgreSQL: R10 initial-candidate return/rework, TE-1 direct cycle reopen."""
import json
import os
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func, text, insert, inspect
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from app.models import *
from app import (report_workflow_service as reports, revision_workflow_service as corrections, authorization_service as auth,
                 package_service as packages, activity_contract_service as contract)
from tests.test_authorization_foundation import foundation_db, ROOT
from tests.test_materialized_successor import people, package, assemble, counts, sealed, assert_sealed
from tests.test_report_workflow import approved, candidate, review, approve, publish, rejects
from tests.test_revision_workflow import released, request, accept, grant, edit
from tests.test_package_workflow import act, package as base_package, edit as package_edit
from tests.test_a1p1_workflow_activation import state, final_return, package_of, reapprove, raw, source_content
pytestmark=pytest.mark.postgres

HEAD='f2b7c4d91e08'


def rows(db,*objects):return [tuple(getattr(db.get(type(o),inspect(o).identity,populate_existing=True),c.name) for c in o.__table__.columns) for o in objects]


def returned_first(db,x,c,stage='final_approved'):
    """The first candidate is final-approved (or only in review) and returned by the final authority."""
    review(db,x,c);d=approve(db,x,c) if stage=='final_approved' else None
    return d,final_return(db,x,c)


def reopen(db,x,p,key='strategy',reason='İade edilen ilk adayın paket düzeltmesi'):
    act(db,x,p,'strategy_reopen',key,reason);return p


def rework(db,x,p,c,value='3.10'):
    """Explicit initial rework: reopen the attempt's package, correct it, re-approve, assemble a NEW candidate."""
    reopen(db,x,p);package_edit(db,x,p,'user',value);reapprove(db,x,p)
    new=reports.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,int(p.source_key),[p.id],c.id);db.commit();return new


def event_of(db,decision):return db.get(WorkflowEvent,decision.workflow_event_id)


# ---------------------------------------------------------------- R10

def test_r10_initial_final_approved_return_keeps_history(foundation_db,people,candidate):
    """R10 1, 4, 8: the current final authority returns an unpublished first candidate; nothing historical changes."""
    db=foundation_db;x=people;c=candidate;review(db,x,c);d=approve(db,x,c)
    freeze=db.get(ActivityReportApproval,d.activity_approval_id);revision=db.get(ActivityReportRevision,c.activity_revision_id)
    before=rows(db,c,d,freeze,revision);s=state(db,c);snapshot=counts(db)
    rejects(422,lambda:reports.final_decision(db,x['director'],c.organization_id,c.id,'final_return',s.version,c.sha256,'  '))
    db.rollback();assert counts(db)==snapshot and state(db,c).state=='final_approved'
    back=final_return(db,x,c)
    assert state(db,c).state=='returned_to_strategy' and back.action=='final_return' and back.activity_approval_id is None
    assert rows(db,c,d,freeze,revision)==before
    event=event_of(db,back);context=json.loads(event.context_json)
    assert event.actor_user_id==x['director'].id and event.reason.strip() and context['sha256']==c.sha256
    assert (context['from_state'],context['to_state'])==('final_approved','returned_to_strategy')
    assert reports.returned_initial_proof(db,c) is c
    data=contract.report_data(db,x['strategy'],c.activity_revision_id);assert data['approved'] and data['returned_after_approval']
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(text('UPDATE report_decisions SET reason=reason WHERE id=:id'),{'id':back.id})
    db.rollback()


@pytest.mark.parametrize('who',['strategy','user','previous_authority'])
def test_r10_only_current_final_authority_returns(foundation_db,people,candidate,who):
    """R10 2, 3: Strategy, a department user and a replaced authority cannot return; the current one can."""
    db=foundation_db;x=people;c=candidate;review(db,x,c);approve(db,x,c)
    if who=='previous_authority':auth.assign_final_authority(db,x['strategy'],c.organization_id,x['editor2'].id,'Yeni resmî atama');db.commit()
    key='director' if who=='previous_authority' else who;s=state(db,c);before=counts(db)
    rejects(403,lambda:reports.final_decision(db,x[key],c.organization_id,c.id,'final_return',s.version,c.sha256,'Yetkisiz iade'))
    db.rollback();assert counts(db)==before and state(db,c).state=='final_approved'
    final_return(db,x,c,'editor2' if who=='previous_authority' else 'director');assert state(db,c).state=='returned_to_strategy'


def test_r10_raw_strategy_return_refused(foundation_db,people,candidate):
    """R10 3, 15: even an exact-looking decision by a Strategy actor cannot move final_approved -> returned."""
    db=foundation_db;x=people;c=candidate;review(db,x,c);approve(db,x,c);s=state(db,c)
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            e=reports.event_notice(db,x['strategy'],c,'final_return','final_approved','returned_to_strategy',s.version+1,'Ham Strateji iadesi')
            db.add(ReportDecision(candidate_id=c.id,action='final_return',candidate_sha256=c.sha256,
                assignment_id=reports.assignment(db,c.organization_id).id,workflow_event_id=e.id));db.flush()
            reports.move(db,s,'returned_to_strategy')
    db.rollback();assert state(db,c).state=='final_approved'


def test_r10_published_candidate_cannot_be_returned(foundation_db,people,candidate):
    """R10 5: publication ends the exit, in Python and in the database."""
    db=foundation_db;x=people;c=candidate;review(db,x,c);approve(db,x,c);publish(db,x,c);s=state(db,c)
    with pytest.raises(HTTPException):reports.final_decision(db,x['director'],c.organization_id,c.id,'final_return',s.version,c.sha256,'Yayın sonrası iade')
    db.rollback()
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(text("UPDATE report_candidate_states SET state='returned_to_strategy',version=version+1 WHERE candidate_id=:id"),{'id':c.id})
    db.rollback();assert state(db,c).state=='published'


def test_r10_return_refused_once_report_has_a_release(foundation_db,people,candidate,monkeypatch):
    """R10 5, 15: a forged non-successor final_approved candidate of a published report cannot use the exit."""
    db=foundation_db;x=people;c=candidate;review(db,x,c);approve(db,x,c);publish(db,x,c)
    report=db.get(ActivityReport,int(c.report_key))
    revision=db.get(ActivityReportRevision,c.activity_revision_id)
    raw(db,"INSERT INTO activity_report_revisions (report_id,revision,publication_id,publication_sha256,contract_version,previous_revision_id,diff_json,revision_reason,created_by,created_at) "
        "SELECT report_id,revision+1,publication_id,publication_sha256,contract_version,id,diff_json,'Ham',created_by,created_at FROM activity_report_revisions WHERE id=:id",id=revision.id)
    extra=db.scalar(select(ActivityReportRevision.id).where(ActivityReportRevision.report_id==revision.report_id,ActivityReportRevision.revision==revision.revision+1))
    raw(db,"INSERT INTO report_candidates (organization_id,period_id,resource_scope,report_key,sequence,activity_revision_id,payload_json,payload_sha256,manifest_json,sha256,created_by) "
        "SELECT organization_id,period_id,resource_scope,report_key,sequence+1,:rev,payload_json,payload_sha256,manifest_json,sha256,created_by FROM report_candidates WHERE id=:id",id=c.id,rev=extra)
    forged=db.scalar(select(ReportCandidate).where(ReportCandidate.sequence==c.sequence+1))
    raw(db,"INSERT INTO report_candidate_states (candidate_id,state,version) VALUES (:id,'final_approved',2)",id=forged.id)
    s=state(db,forged)
    rejects(409,lambda:reports.final_decision(db,x['director'],c.organization_id,forged.id,'final_return',s.version,forged.sha256,'Ham iade'))
    db.rollback()
    # TE-8: even a forged candidate that verified (and whose revision is current) meets the explicit release refusal.
    raw(db,'UPDATE activity_reports SET current_revision=current_revision+1 WHERE id=:r',r=revision.report_id)
    with monkeypatch.context() as m:
        m.setattr(reports,'verify',lambda db,candidate:None)
        with pytest.raises(HTTPException) as caught:
            reports.final_decision(db,x['director'],c.organization_id,forged.id,'final_return',s.version,forged.sha256,'Ham iade')
    assert caught.value.status_code==409 and 'Bu Faaliyet Raporu yayımlandı' in caught.value.detail;db.rollback()
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            e=reports.event_notice(db,x['director'],forged,'final_return','final_approved','returned_to_strategy',s.version+1,'Ham iade')
            db.add(ReportDecision(candidate_id=forged.id,action='final_return',candidate_sha256=forged.sha256,
                assignment_id=reports.assignment(db,c.organization_id).id,workflow_event_id=e.id));db.flush()
            reports.move(db,s,'returned_to_strategy')
    db.rollback();assert state(db,forged).state=='final_approved' and report.id


def test_r10_returned_attempt_is_terminal(foundation_db,people,candidate):
    """R10 6: never final-approved, published or mutated again (Python and raw SQL)."""
    db=foundation_db;x=people;c=candidate;returned_first(db,x,c);before=rows(db,c)
    rejects(403,lambda:approve(db,x,c));rejects(403,lambda:publish(db,x,c))
    for sql in ("UPDATE report_candidate_states SET state='final_approved',version=version+1 WHERE candidate_id=:id",
                "UPDATE report_candidate_states SET state='published',version=version+1 WHERE candidate_id=:id",
                "UPDATE report_candidates SET payload_json=payload_json WHERE id=:id","DELETE FROM report_candidates WHERE id=:id"):
        with pytest.raises(DBAPIError):
            with db.begin_nested():db.execute(text(sql),{'id':c.id})
        db.rollback()
    assert rows(db,c)==before and state(db,c).state=='returned_to_strategy'


@pytest.mark.parametrize('stage',['final_approved','final_review'])
def test_r10_rework_new_candidate_fresh_approval_and_only_new_publishes(foundation_db,people,approved,candidate,stage):
    """R10 7-14: explicit package reopen, new content, NEW candidate with exact provenance, fresh freeze and release."""
    db=foundation_db;x=people;p=approved;c=candidate;old_decision,back=returned_first(db,x,c,stage)
    history=sealed(db);old=[o for o in (c,old_decision,back,db.get(ActivityReportApproval,old_decision.activity_approval_id) if old_decision else None) if o]
    old_rows=rows(db,*old);old_revision=db.get(ActivityReportRevision,c.activity_revision_id)
    new=rework(db,x,p,c)
    manifest=json.loads(new.manifest_json)
    # 7, 9, 10: a new row, exact provenance, deterministic sequence; never a predecessor release.
    assert new.id!=c.id and new.sequence==c.sequence+1 and new.predecessor_candidate_id==c.id
    assert manifest['reworks_candidate_id']==c.id and manifest['reworks_candidate_sha256']==c.sha256 and 'predecessor_release_id' not in manifest
    assert manifest['source_id']==json.loads(c.manifest_json)['source_id']
    # 11: content changed -> a NEW materialized revision directly after the attempt's.
    revision=db.get(ActivityReportRevision,new.activity_revision_id)
    assert revision.id!=old_revision.id and revision.previous_revision_id==old_revision.id and revision.revision==old_revision.revision+1
    assert json.loads(new.payload_json)!=json.loads(c.payload_json)
    fresh=db.scalars(select(ActualRevision).join(ReportIndicator,ReportIndicator.id==ActualRevision.report_indicator_id).where(ReportIndicator.report_revision_id==revision.id)).all()
    assert sorted(str(a.value) for a in fresh)[0].startswith('1.75') and any(str(a.value).startswith('3.1') for a in fresh)
    # 8: the returned attempt, its decisions and its freeze are byte-for-byte unchanged.
    assert rows(db,*old)==old_rows;assert_sealed(db,history)
    # The package moved through an explicit, reasoned strategy_reopen with an exact-copy revision.
    reopen_decision=db.scalar(select(PackageDecision).where(PackageDecision.action=='strategy_reopen'))
    context=json.loads(event_of(db,reopen_decision).context_json)
    assert context['initial_rework_candidate_id']==c.id and context['initial_rework_candidate_sha256']==c.sha256 and context['correction_cycle_id'] is None
    copy=db.get(PackageRevision,context['next_revision_id']);prior=db.get(PackageRevision,reopen_decision.package_revision_id)
    assert copy.previous_revision_id==prior.id and copy.content_json==prior.content_json and copy.revision==prior.revision+1
    # 12, 13: no approval carry-forward; a fresh final approval is required.
    rejects(403,lambda:publish(db,x,new));review(db,x,new);rejects(403,lambda:publish(db,x,new))
    d=approve(db,x,new);assert d.activity_approval_id and (not old_decision or d.activity_approval_id!=old_decision.activity_approval_id)
    assert db.get(ActivityReportApproval,d.activity_approval_id).report_revision_id==revision.id
    # 14: only the new candidate publishes.
    rejects(403,lambda:publish(db,x,c))
    release=publish(db,x,new);assert (release.candidate_id,release.major,release.minor)==(new.id,1,0) and release.activity_approval_id==d.activity_approval_id
    reports.verify(db,new);reports.verify(db,c);reports.verify_artifact(db,release)
    assert rows(db,*old)==old_rows


def test_r10_rework_without_content_change_still_new_attempt(foundation_db,people,approved,candidate):
    """A re-assembly of unchanged approved packages is a legitimate new attempt: new revision, fresh approval."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c)
    new=reports.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,int(p.source_key),[p.id],c.id);db.commit()
    assert json.loads(new.manifest_json)['reworks_candidate_id']==c.id and new.activity_revision_id!=c.activity_revision_id
    review(db,x,new);d=approve(db,x,new);assert db.get(ActivityReportApproval,d.activity_approval_id).report_revision_id==new.activity_revision_id


@pytest.mark.parametrize('case',['not_returned','strategy_review_only','non_strategy','no_reason','after_rework_assembly','published'])
def test_r10_package_reopen_preconditions(foundation_db,people,approved,candidate,case):
    """The initial package reopen exists only for the report's latest returned, unpublished attempt."""
    db=foundation_db;x=people;p=approved;c=candidate;review(db,x,c);approve(db,x,c)
    if case=='published':publish(db,x,c)
    elif case!='not_returned':final_return(db,x,c)
    if case=='after_rework_assembly':
        reports.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,int(p.source_key),[p.id],c.id);db.commit()
    before=counts(db),rows(db,p)
    with pytest.raises(HTTPException) as caught:
        if case=='non_strategy':act(db,x,p,'strategy_reopen','director','Müdür yeniden açması')
        elif case=='no_reason':act(db,x,p,'strategy_reopen','strategy',' ')
        elif case=='strategy_review_only':act(db,x,p,'strategy_return','strategy','Yanlış işlem')
        else:reopen(db,x,p)
    attempt='son rapor adayına bağlıysa yeniden açılabilir';forbidden='yetkiniz yok'
    expected={'not_returned':(409,attempt),'after_rework_assembly':(409,attempt),'published':(409,attempt),'strategy_review_only':(403,forbidden),
              'non_strategy':(403,forbidden),'no_reason':(422,'gerekçesi belirtilmedi')}[case]
    assert (caught.value.status_code,expected[1] in caught.value.detail)==(expected[0],True)  # TE-10: one exact refusal per case
    db.rollback();assert (counts(db),rows(db,p))==before


def test_r10_pre_reopen_edit_and_new_package_refused(foundation_db,people,approved,candidate):
    """Before the explicit reopen the attempt's package stays frozen; a package on the frozen revision is refused."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c)
    with pytest.raises(HTTPException):package_edit(db,x,p,'user','4.00')
    db.rollback()
    with pytest.raises(HTTPException):
        packages.create_package(db,x['user'],p.organization_id,p.department_id,'activity_report',c.activity_revision_id)
    db.rollback()


@pytest.mark.parametrize('stage',['final_review','final_approved'])
def test_r10_rework_must_continue_the_attempt_source(foundation_db,people,approved,candidate,stage):
    """WF-2, one rework lineage: no package can be opened on a candidate's own revision; the error names the candidate."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c,stage);before=counts(db)
    with pytest.raises(HTTPException) as caught:
        packages.create_package(db,x['user'],p.organization_id,p.department_id,'activity_report',c.activity_revision_id)
    assert caught.value.status_code==409 and f'#{c.id}' in caught.value.detail and 'yeniden açmalıdır' in caught.value.detail
    db.rollback();assert counts(db)==before


def candidate_row(c,**changes):
    values={col.name:getattr(c,col.name) for col in c.__table__.columns if col.name not in {'id','created_at'}};values.update(changes)
    return values


def replica(db,statement,**params):
    """Trigger-free write (test-only forgery setup); the forged row under test is then inserted WITH triggers."""
    db.execute(text('SET session_replication_role=replica'))
    try:return db.execute(text(statement),params) if isinstance(statement,str) else db.execute(statement)
    finally:db.execute(text('SET session_replication_role=origin'))


LINEAGE_FORGERIES=['valid_control','resurrect_revision','missing_rework_keys','wrong_rework_sha','wrong_rework_id','skip_sequence',
                   'while_live','returned_without_final_return','other_source_id','other_required_departments']


@pytest.mark.parametrize('forgery',LINEAGE_FORGERIES)
def test_r10_raw_candidate_lineage_forgeries_rejected(foundation_db,people,approved,candidate,forgery):
    """R10 15, WF-R10-RAW, SEC-A1, TE-1: raw candidate inserts on a FRESH next revision cannot resurrect or mis-link an
    initial attempt; each case differs from the accepted control in one property only."""
    db=foundation_db;x=people;p=approved;c=candidate;review(db,x,c)
    if forgery=='while_live':approve(db,x,c)
    elif forgery=='returned_without_final_return':replica(db,"UPDATE report_candidate_states SET state='returned_to_strategy',version=version+1 WHERE candidate_id=:c",c=c.id)
    else:final_return(db,x,c)
    db.commit();db.refresh(c);before=counts(db)
    fresh=c.activity_revision_id if forgery=='resurrect_revision' else replica(db,stray_revision_statement(db,c)).scalar_one()
    manifest=json.loads(c.manifest_json)
    if forgery!='missing_rework_keys':
        manifest.update(reworks_candidate_id=c.id+1000 if forgery=='wrong_rework_id' else c.id,
                        reworks_candidate_sha256='0'*64 if forgery=='wrong_rework_sha' else c.sha256)
    if forgery=='other_source_id':manifest['source_id']=manifest['source_id']+1000
    if forgery=='other_required_departments':manifest['required_department_ids']=manifest['required_department_ids']+[999]
    mraw=reports.canonical(manifest)
    values=candidate_row(c,sequence=c.sequence+(2 if forgery=='skip_sequence' else 1),predecessor_candidate_id=c.id,activity_revision_id=fresh,
        manifest_json=mraw,sha256=reports.hash_content(c.payload_json,mraw))
    if forgery=='valid_control':
        with db.begin_nested():db.execute(insert(ReportCandidate).values(**values))  # the insert guard accepts the exact lineage
    else:
        with pytest.raises(DBAPIError,match='Invalid initial Activity rework lineage' if forgery!='resurrect_revision' else 'uq_report_candidate_activity_revision|Invalid initial Activity rework lineage'):
            with db.begin_nested():db.execute(insert(ReportCandidate).values(**values))
    db.rollback();assert counts(db)==before


def test_r10_unique_activity_revision_even_without_triggers(foundation_db,people,candidate):
    """SEC-A1 defence in depth: one Activity revision (and its freeze) belongs to one candidate."""
    db=foundation_db;x=people;c=candidate
    db.execute(text('SET session_replication_role=replica'))
    try:
        with pytest.raises(IntegrityError,match='uq_report_candidate_activity_revision'):
            with db.begin_nested():db.execute(insert(ReportCandidate).values(**candidate_row(c,sequence=c.sequence+1,predecessor_candidate_id=c.id)))
    finally:db.rollback();db.execute(text('SET session_replication_role=origin'));db.commit()


def test_r10_old_freeze_cannot_be_reused_by_the_rework(foundation_db,people,approved,candidate):
    """R10 12, 15, SEC-A1: a forged decision or release carrying the returned attempt's freeze is refused."""
    db=foundation_db;x=people;p=approved;c=candidate;old,back=returned_first(db,x,c)
    new=rework(db,x,p,c);review(db,x,new);s=state(db,new)
    with pytest.raises(DBAPIError,match='Final decision freeze mismatch'):
        with db.begin_nested():
            e=reports.event_notice(db,x['director'],new,'final_approve','final_review','final_approved',s.version+1)
            db.add(ReportDecision(candidate_id=new.id,action='final_approve',candidate_sha256=new.sha256,activity_approval_id=old.activity_approval_id,
                assignment_id=reports.assignment(db,new.organization_id).id,workflow_event_id=e.id));db.flush()
    db.rollback()
    d=approve(db,x,new);s=state(db,new)
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            e=reports.event_notice(db,x['strategy'],new,'publish','final_approved','published',s.version+1)
            db.add(ReportRelease(candidate_id=new.id,final_decision_id=d.id,organization_id=new.organization_id,resource_scope='activity_report',
                report_key=new.report_key,major=1,minor=0,activity_approval_id=old.activity_approval_id,workflow_event_id=e.id));db.flush()
    db.rollback();assert db.scalar(select(func.count(ReportRelease.id)))==0


@pytest.mark.parametrize('forgery',['move_without_reopen','move_while_live','reopen_without_provenance','reopen_live_attempt'])
def test_r10_raw_package_reopen_forgeries_rejected(foundation_db,people,approved,candidate,forgery):
    """R10 15: a candidate-bound initial package leaves strategy_approved only through the audited reopen."""
    db=foundation_db;x=people;p=approved;c=candidate;review(db,x,c);approve(db,x,c)
    if forgery not in {'reopen_live_attempt','move_while_live'}:final_return(db,x,c)
    current=packages.revision(db,p);before=rows(db,p),counts(db)
    match='Candidate-bound package requires an audited initial rework reopen' if forgery.startswith('move') else 'strategy_reopen requires a returned unpublished initial attempt'
    with pytest.raises(DBAPIError,match=match):
        with db.begin_nested():
            if forgery.startswith('move'):
                copy=packages.append_revision(db,p,x['strategy'],current.content_json,current,'Ham yeniden açma')
                packages.move(db,p,p.version,'returned',copy.revision)
            else:
                e=packages.history_event(db,x['strategy'],p,'strategy_reopen',{'revision_id':current.id,'sha256':current.sha256,'next_revision_id':None,
                    'next_revision':current.revision+1,'next_sha256':current.sha256,'from_state':'strategy_approved','to_state':'returned','delegation_id':None,
                    'decision_time':None,'correction_cycle_id':None,'expected_version':p.version,'returned_revision':current.revision+1,
                    **({'initial_rework_candidate_id':c.id,'initial_rework_candidate_sha256':c.sha256} if forgery=='reopen_live_attempt' else {})},'Ham yeniden açma')
                db.add(PackageDecision(package_revision_id=current.id,snapshot_sha256=current.sha256,action='strategy_reopen',
                    from_state='strategy_approved',to_state='returned',workflow_event_id=e.id));db.flush()
    db.rollback();assert (rows(db,p),counts(db))==before


def stray_revision_statement(db,c):
    src=db.get(ActivityReportRevision,c.activity_revision_id)
    values={col.name:getattr(src,col.name) for col in src.__table__.columns if col.name not in {'id','created_at'}}
    values.update(revision=src.revision+1,previous_revision_id=src.id)
    return insert(ActivityReportRevision).values(**values).returning(ActivityReportRevision.id)


def stray_revision(db,c):
    """A raw next Activity revision after the attempt's materialization (what a forged rework would need)."""
    src=db.get(ActivityReportRevision,c.activity_revision_id)
    values={col.name:getattr(src,col.name) for col in src.__table__.columns if col.name not in {'id','created_at'}}
    values.update(revision=src.revision+1,previous_revision_id=src.id)
    return db.execute(insert(ActivityReportRevision).values(**values).returning(ActivityReportRevision.id)).scalar_one()


def forged_rework_values(c,revision_id,**manifest_changes):
    manifest=json.loads(c.manifest_json);manifest.update(reworks_candidate_id=c.id,reworks_candidate_sha256=c.sha256,**manifest_changes)
    mraw=reports.canonical(manifest)
    return candidate_row(c,sequence=c.sequence+1,predecessor_candidate_id=c.id,activity_revision_id=revision_id,manifest_json=mraw,
        sha256=reports.hash_content(c.payload_json,mraw))


@pytest.mark.parametrize('forgery',['valid_lineage_no_bindings','other_package_set'])
def test_r10_raw_rework_candidate_refused(foundation_db,people,approved,candidate,forgery):
    """WF-1, SEC-3: a raw rework row with a correct lineage still needs its state, event and exact bindings at commit;
    a different package set is refused at insert."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c);before=counts(db)
    if forgery=='other_package_set':
        manifest=json.loads(c.manifest_json)
        changes={'packages':[{**b,'package_id':b['package_id']+1000} for b in manifest['packages']]}
        with pytest.raises(DBAPIError,match='Invalid initial Activity rework lineage'):
            with db.begin_nested():db.execute(insert(ReportCandidate).values(**forged_rework_values(c,stray_revision(db,c),**changes)))
    else:
        new=db.execute(insert(ReportCandidate).values(**forged_rework_values(c,stray_revision(db,c))).returning(ReportCandidate.id)).scalar_one()
        db.add(ReportCandidateState(candidate_id=new,state='assembling',version=0));db.flush()  # the BEFORE guards accept the lineage
        with pytest.raises(DBAPIError,match='Initial Activity candidate is incomplete at commit'):db.commit()
    db.rollback();assert counts(db)==before
    new=rework(db,x,p,c);assert new.sequence==c.sequence+1  # the legitimate rework is still open


@pytest.mark.parametrize('swap',['content_in_place','report_revision','approved_without_review'])
def test_r10_raw_bound_package_content_swap_refused(foundation_db,people,approved,candidate,swap):
    """SEC-1, DB-1: a candidate-bound initial package cannot change content or skip review by raw SQL."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c)
    if swap=='approved_without_review':reopen(db,x,p);db.commit()
    current=packages.revision(db,p);before=rows(db,p),counts(db)
    match={'content_in_place':'audited initial rework reopen','report_revision':'audited initial rework reopen',
           'approved_without_review':'exact package decision'}[swap]
    with pytest.raises(DBAPIError,match=match):
        with db.begin_nested():
            if swap=='content_in_place':
                content=json.loads(current.content_json);content['explanation']='Gizlice değiştirildi'
                copy=packages.append_revision(db,p,x['strategy'],reports.canonical(content),current,'Ham içerik değişimi')
                packages.move(db,p,p.version,'strategy_approved',copy.revision)
            elif swap=='report_revision':
                db.execute(text('UPDATE directorate_packages SET report_revision_id=:r,version=version+1 WHERE id=:p'),{'r':c.activity_revision_id,'p':p.id})
            else:
                db.execute(text("UPDATE directorate_packages SET state='strategy_approved',version=version+1 WHERE id=:p"),{'p':p.id})
    db.rollback();assert (rows(db,p),counts(db))==before


def test_r10_raw_stale_binding_on_rework_refused(foundation_db,people,approved,candidate):
    """DB-1: an initial candidate binds exactly the current approved revision named in its manifest."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c)
    old=db.scalar(select(CandidatePackage).where(CandidatePackage.candidate_id==c.id))
    new=rework(db,x,p,c);before=counts(db)
    with pytest.raises(DBAPIError,match='Initial candidate must bind the current approved package revision'):
        with db.begin_nested():
            db.add(CandidatePackage(candidate_id=new.id,package_revision_id=old.package_revision_id,strategy_decision_id=old.strategy_decision_id,sha256=old.sha256));db.flush()
    db.rollback();assert counts(db)==before


def forge_initial_reopen_decision(db,x,p,c):
    """Raw strategy_reopen event + decision naming attempt c (what transition() writes before the package move)."""
    current=packages.revision(db,p)
    e=packages.history_event(db,x['strategy'],p,'strategy_reopen',{'revision_id':current.id,'sha256':current.sha256,'next_revision_id':None,
        'next_revision':current.revision+1,'next_sha256':current.sha256,'from_state':'strategy_approved','to_state':'returned','delegation_id':None,
        'decision_time':None,'correction_cycle_id':None,'expected_version':p.version,'returned_revision':current.revision+1,
        'initial_rework_candidate_id':c.id,'initial_rework_candidate_sha256':c.sha256},'Ham yeniden açma')
    db.add(PackageDecision(package_revision_id=current.id,snapshot_sha256=current.sha256,action='strategy_reopen',
        from_state='strategy_approved',to_state='returned',workflow_event_id=e.id));db.flush()


@pytest.mark.parametrize('case',['valid_control','superseded_attempt','later_candidate_row','report_revision_moved'])
def test_r10_raw_reopen_of_superseded_or_stale_attempt_rejected(foundation_db,people,approved,candidate,case):
    """TE-3: the initial-rework reopen names the LATEST returned attempt whose materialization is still current."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c)
    if case=='superseded_attempt':rework(db,x,p,c,'3.20');p=db.get(DirectoratePackage,p.id,populate_existing=True)  # a live rework now exists
    if case=='later_candidate_row':  # only the 'latest candidate' clause differs from the control (report revision unchanged)
        fresh=replica(db,stray_revision_statement(db,c)).scalar_one()
        replica(db,insert(ReportCandidate).values(**candidate_row(c,sequence=c.sequence+1,predecessor_candidate_id=c.id,activity_revision_id=fresh)))
    if case=='report_revision_moved':
        report=db.get(ActivityReportRevision,c.activity_revision_id).report_id
        replica(db,'UPDATE activity_reports SET current_revision=current_revision+1 WHERE id=:r',r=report)
    db.commit();before=counts(db)
    if case=='valid_control':
        with db.begin_nested():forge_initial_reopen_decision(db,x,p,c)
    else:
        with pytest.raises(DBAPIError,match='strategy_reopen requires a returned unpublished initial attempt'):
            with db.begin_nested():forge_initial_reopen_decision(db,x,p,c)
    db.rollback();assert counts(db)==before


@pytest.mark.parametrize('forgery',['zero_packages','own_source_revision'])
def test_raw_first_candidate_must_be_complete(foundation_db,people,approved,forgery):
    """Delta DB-1: even with its state row and assembled event, a raw first candidate needs one binding per required
    department and its own fresh materialization of the source."""
    db=foundation_db;x=people;p=approved
    c=reports.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,int(p.source_key),[p.id])
    values=candidate_row(c);event=db.scalar(select(WorkflowEvent).where(WorkflowEvent.resource_type=='report_candidate',WorkflowEvent.resource_id==str(c.id)))
    event_values={col.name:getattr(event,col.name) for col in event.__table__.columns if col.name not in {'id','created_at','resource_id'}}
    db.rollback();before=counts(db)
    manifest=json.loads(values['manifest_json'])
    if forgery=='zero_packages':  # a correct fresh materialization of the source, but no package
        manifest['packages']=[];src=db.get(ActivityReportRevision,p.report_revision_id)
        fresh={col.name:getattr(src,col.name) for col in src.__table__.columns if col.name not in {'id','created_at'}}
        fresh.update(revision=src.revision+1,previous_revision_id=src.id)
        values['activity_revision_id']=db.execute(insert(ActivityReportRevision).values(**fresh).returning(ActivityReportRevision.id)).scalar_one()
    else:values['activity_revision_id']=p.report_revision_id
    values['manifest_json']=reports.canonical(manifest);values['sha256']=reports.hash_content(values['payload_json'],values['manifest_json'])
    context=json.loads(event_values['context_json']);context['sha256']=values['sha256'];event_values['context_json']=json.dumps(context)
    new=db.execute(insert(ReportCandidate).values(**values).returning(ReportCandidate.id)).scalar_one()
    db.add(ReportCandidateState(candidate_id=new,state='assembling',version=0))
    if forgery=='own_source_revision':
        for b in manifest['packages']:
            decision=db.scalar(select(PackageDecision.id).where(PackageDecision.package_revision_id==b['revision_id'],PackageDecision.action=='strategy_approve'))
            db.add(CandidatePackage(candidate_id=new,package_revision_id=b['revision_id'],strategy_decision_id=decision,sha256=b['sha256']))
    db.execute(insert(WorkflowEvent).values(resource_id=str(new),**event_values))
    with pytest.raises(DBAPIError,match='Initial Activity candidate is incomplete at commit'):db.commit()
    db.rollback();assert counts(db)==before


def test_r10_full_package_review_cycle_after_reopen(foundation_db,people,approved,candidate):
    """Delta hand-off: every normal review transition still works on a candidate-bound package after the R10 reopen,
    and assembly + final-review request in one transaction passes the commit-time completeness check."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c);reopen(db,x,p)
    package_edit(db,x,p,'user','3.30');act(db,x,p,'submit_to_director','user');act(db,x,p,'director_return','director','Müdür iadesi')
    package_edit(db,x,p,'user','3.40');act(db,x,p,'submit_to_director','user');act(db,x,p,'director_approve')
    act(db,x,p,'strategy_return','strategy','Strateji iadesi');package_edit(db,x,p,'user','3.50')
    act(db,x,p,'submit_to_director','user');act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    new=reports.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,int(p.source_key),[p.id],c.id)
    s=db.get(ReportCandidateState,new.id);reports.request_final_review(db,x['strategy'],new.organization_id,new.id,s.version,new.sha256);db.commit()
    approve(db,x,new);publish(db,x,new)
    assert state(db,new).state=='published' and state(db,c).state=='returned_to_strategy'


def pp_candidate(db,x):
    p=base_package.__wrapped__(db,x,SimpleNamespace(param='performance_program'))
    act(db,x,p,'submit_to_director','user');act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    db.add(ReportSection(period_id=p.period_id,title='Genel Bilgiler',kind='text',content_json='{}'))
    auth.assign_final_authority(db,x['strategy'],p.organization_id,x['director'].id,'Nihai yetki yazısı');db.commit()
    c=reports.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,int(p.source_key),[p.id]);db.commit();return c


def test_r10_performance_program_final_approved_return_still_refused(foundation_db,people):
    """The exit stays Activity-only: Performance Program candidates cannot leave final_approved (Python and raw SQL)."""
    from tests.test_authorization_foundation import people as base_people
    db=foundation_db;x=people;c=pp_candidate(db,x);review(db,x,c);approve(db,x,c);s=state(db,c)
    with pytest.raises(HTTPException) as caught:
        reports.final_decision(db,x['director'],c.organization_id,c.id,'final_return',s.version,c.sha256,'PP iadesi')
    assert caught.value.status_code==409 and 'Performans Programı' in caught.value.detail;db.rollback()
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            e=reports.event_notice(db,x['director'],c,'final_return','final_approved','returned_to_strategy',s.version+1,'Ham PP iadesi')
            db.add(ReportDecision(candidate_id=c.id,action='final_return',candidate_sha256=c.sha256,
                assignment_id=reports.assignment(db,c.organization_id).id,workflow_event_id=e.id));db.flush()
            reports.move(db,s,'returned_to_strategy')
    db.rollback();assert state(db,c).state=='final_approved'


@pytest.mark.parametrize('rival',['publish','double_return'])
def test_r10_concurrent_return_and_final_action_one_winner(foundation_db,people,candidate,rival):
    """R10 16: final_return racing publish (or a double-clicked second final_return) has exactly one deterministic winner."""
    db=foundation_db;x=people;c=candidate;review(db,x,c);approve(db,x,c);s=state(db,c);version=s.version;db.commit();barrier=Barrier(2)
    def returning():
        with Session(db.get_bind(),expire_on_commit=False) as other:
            barrier.wait(timeout=10)
            try:reports.final_decision(other,other.get(User,x['director'].id),c.organization_id,c.id,'final_return',version,c.sha256,'Eş zamanlı iade');other.commit();return 'returned'
            except HTTPException as exc:other.rollback();return exc.status_code
    def racing():
        with Session(db.get_bind(),expire_on_commit=False) as other:
            barrier.wait(timeout=10)
            try:
                if rival=='publish':reports.publish(other,other.get(User,x['strategy'].id),c.organization_id,c.id,version,c.sha256)
                else:reports.final_decision(other,other.get(User,x['director'].id),c.organization_id,c.id,'final_return',version,c.sha256,'İkinci iade')
                other.commit();return 'won'
            except HTTPException as exc:other.rollback();return exc.status_code
    with ThreadPoolExecutor(2) as pool:first,second=pool.submit(returning),pool.submit(racing);results=(first.result(),second.result())
    db.expire_all();final=state(db,c).state
    returns=db.scalar(select(func.count(ReportDecision.id)).where(ReportDecision.candidate_id==c.id,ReportDecision.action=='final_return'))
    releases=db.scalar(select(func.count(ReportRelease.id)))
    if rival=='publish':
        assert sorted(map(str,results)).count('409')+sorted(map(str,results)).count('403')==1
        assert (returns,releases) in {(1,0),(0,1)} and final==('returned_to_strategy' if returns else 'published')
    else:  # REL-1: both calls are valid on their own; exactly one may commit
        loser=[r for r in results if r not in ('returned','won')]
        assert len(loser)==1 and loser[0] in (403,409) and returns==1 and final=='returned_to_strategy' and releases==0


def test_r10_concurrent_rework_assembly_one_candidate(foundation_db,people,approved,candidate):
    """Two Strategy assemblies of the same rework: one new candidate, one deterministic refusal."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c);db.commit();barrier=Barrier(2)
    def assembling():
        with Session(db.get_bind(),expire_on_commit=False) as other:
            barrier.wait(timeout=10)
            try:reports.assemble_candidate(other,other.get(User,x['strategy'].id),p.organization_id,p.resource_scope,int(p.source_key),[p.id],c.id);other.commit();return 'assembled'
            except HTTPException as exc:other.rollback();return exc.status_code
    with ThreadPoolExecutor(2) as pool:first,second=pool.submit(assembling),pool.submit(assembling);results=sorted(map(str,(first.result(),second.result())))
    db.expire_all();assert db.scalar(select(func.count(ReportCandidate.id)))==2 and 'assembled' in results


# ---------------------------------------------------------------- TE-1

def closed_q1(db,x,r):
    """Q1 accepted, granted, edited back to its source value, re-approved and closed_no_change BEFORE any candidate."""
    q1=request(db,x,r);accept(db,x,q1);g1=grant(db,x,q1);source=source_content(db,g1)
    edit(db,x,g1);edit(db,x,g1,value=source['entries'][0]['value']);p=package_of(db,g1);reapprove(db,x,p)
    s=db.get(RevisionRequestState,q1.id);corrections.close_no_change(db,x['strategy'],q1.id,s.version,'Net değişiklik yok');db.commit()
    return q1,g1,p


def reopen_cycle(db,x,q,key='strategy',reason='Yeni kabul edilen düzeltme talebi için döngü yeniden açıldı'):
    p=package_of_request(db,q);rev=packages.revision(db,p);s=db.get(RevisionRequestState,q.id)
    copy=corrections.reopen_cycle(db,x[key],q.id,s.version,p.version,rev.sha256,reason);db.commit();return copy


def package_of_request(db,q):return db.get(DirectoratePackage,db.get(PackageRevision,q.source_package_revision_id).package_id)


def te1(db,x,r):
    q1,g1,p=closed_q1(db,x,r);q2=request(db,x,r);accept(db,x,q2);return q1,g1,p,q2


def test_te1_dead_end_without_reopen(foundation_db,people,released):
    """Baseline: after Q1 closed_no_change the approved cycle package cannot take Q2's grant directly."""
    db=foundation_db;x=people;q1,g1,p,q2=te1(db,x,released);assert p.state=='strategy_approved'
    with pytest.raises(HTTPException) as caught:grant(db,x,q2)
    assert caught.value.status_code==409 and 'yeniden açmalıdır' in caught.value.detail;db.rollback()


def test_te1_direct_reopen_new_grant_edit_and_publish(foundation_db,people,released):
    """TE-1 A-G: no dummy candidate; Q1 immutable; exact-copy revision; immutable reopen event; NEW grant; full path to 1.1."""
    db=foundation_db;x=people;r=released;q1,g1,p,q2=te1(db,x,r)
    q1_state=db.get(RevisionRequestState,q1.id);q1_before=rows(db,q1,q1_state,g1);candidates=db.scalar(select(func.count(ReportCandidate.id)))
    prior=packages.revision(db,p);history=sealed(db)
    copy=reopen_cycle(db,x,q2)
    # A: no candidate of any kind was created.
    assert db.scalar(select(func.count(ReportCandidate.id)))==candidates
    # B: Q1, its state and its grant are untouched.
    assert rows(db,q1,q1_state,g1)==q1_before and db.get(RevisionRequestState,q1.id).state=='closed_no_change'
    # C: a new append-only exact copy; the package is editable.
    p=db.get(DirectoratePackage,p.id,populate_existing=True)
    assert (copy.previous_revision_id,copy.revision,copy.content_json,copy.sha256)==(prior.id,prior.revision+1,prior.content_json,prior.sha256)
    assert p.state=='returned' and p.current_revision==copy.revision;assert_sealed(db,history)
    # D: immutable provenance with every required field.
    e=db.scalar(select(WorkflowEvent).where(WorkflowEvent.event_type=='correction_cycle_reopened'));context=json.loads(e.context_json)
    cycle=db.get(RevisionCorrectionCycle,g1.cycle_id)
    assert e.actor_user_id==x['strategy'].id and e.reason.strip() and e.created_at and e.resource_id==str(q2.id)
    assert (context['request_id'],context['source_release_id'],context['cycle_id'],context['package_id'])==(q2.id,r.id,cycle.id,p.id)
    assert (context['previous_revision_id'],context['previous_sha256'],context['resulting_revision'],context['resulting_sha256'])==(prior.id,prior.sha256,copy.revision,copy.sha256)
    decision=db.scalar(select(PackageDecision).where(PackageDecision.action=='strategy_reopen'))
    package_context=json.loads(event_of(db,decision).context_json)
    assert (package_context['reopen_request_id'],package_context['reopen_event_id'],package_context['correction_cycle_id'])==(q2.id,e.id,cycle.id)
    for sql in ('UPDATE workflow_events SET reason=reason WHERE id=:id','DELETE FROM workflow_events WHERE id=:id'):
        with pytest.raises(DBAPIError):
            with db.begin_nested():db.execute(text(sql),{'id':e.id})
        db.rollback()
    # E: Q2 gets its own NEW grant on the same cycle.
    g2=grant(db,x,q2);assert g2.id!=g1.id and g2.cycle_id==g1.cycle_id and g2.request_id==q2.id
    # The exact-copy reopen revision is not a semantic correction.
    p=db.get(DirectoratePackage,p.id,populate_existing=True)
    assert not corrections.has_net_correction(db,q2,g2,cycle,packages.revision(db,p))
    # G: Q1's still-unexpired grant cannot authorize anything.
    assert auth.server_now(db)<g1.end_at
    with pytest.raises(HTTPException):edit(db,x,g1,value='9.99')
    db.rollback()
    with pytest.raises(HTTPException):
        now=auth.server_now(db);corrections.renew_grant(db,x['strategy'],g1.id,corrections.paths(q1),now,now+timedelta(hours=2),'Eski izin yenileme')
    db.rollback()
    # F: edit -> director review -> Strategy review -> successor assembly -> publication.
    edit(db,x,g2,value='3.75');reapprove(db,x,p);c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c)
    release=publish(db,x,c);assert release.minor==1
    assert db.get(RevisionRequestState,q2.id).state=='applied' and db.get(RevisionRequestState,q1.id).state=='closed_no_change'
    assert rows(db,q1,g1)==q1_before[::2]


@pytest.mark.parametrize('case',['requested','closed','other_department_actor','non_strategy','no_reason','stale_version','wrong_hash','already_returned','granted'])
def test_te1_reopen_preconditions(foundation_db,people,released,case):
    """TE-1 J and the eligibility predicate: every refusal writes nothing."""
    db=foundation_db;x=people;r=released;q1,g1,p,q2=te1(db,x,r) if case!='requested' else (*closed_q1(db,x,r),None)
    if case=='requested':q2=request(db,x,r)
    target=q1 if case=='closed' else q2;rev=packages.revision(db,p);s=db.get(RevisionRequestState,target.id)
    key={'non_strategy':'director','other_department_actor':'user'}.get(case,'strategy')
    version,package_version,sha=s.version,p.version,rev.sha256
    if case=='stale_version':package_version-=1
    if case=='wrong_hash':sha='0'*64
    if case in {'already_returned','granted'}:reopen_cycle(db,x,q2)
    if case=='granted':grant(db,x,q2);p=db.get(DirectoratePackage,p.id,populate_existing=True);reapprove(db,x,p)
    if case in {'already_returned','granted'}:
        p=db.get(DirectoratePackage,p.id,populate_existing=True);rev=packages.revision(db,p);s=db.get(RevisionRequestState,target.id,populate_existing=True)
        version,package_version,sha=s.version,p.version,rev.sha256
    before=counts(db),rows(db,p)
    with pytest.raises(HTTPException) as caught:
        corrections.reopen_cycle(db,x[key],target.id,version,package_version,sha,' ' if case=='no_reason' else 'Döngü yeniden açma')
    state_rule='yalnız kabul edilmiş ve henüz izni açılmamış';cas='Paket sürümü veya içeriği değişti';strategy='Strateji yapmalıdır'
    expected={'requested':(409,state_rule),'closed':(409,state_rule),'granted':(409,state_rule),'other_department_actor':(403,strategy),
              'non_strategy':(403,strategy),'no_reason':(422,'gerekçesi belirtilmedi'),'stale_version':(409,cas),'wrong_hash':(409,cas),
              'already_returned':(409,'zaten düzenlenebilir')}[case]
    assert (caught.value.status_code,expected[1] in caught.value.detail)==(expected[0],True)  # TE-10: one exact refusal per case
    db.rollback();assert (counts(db),rows(db,p))==before
    if case=='closed':assert db.get(RevisionRequestState,q1.id).state=='closed_no_change'


def test_te1_reopen_rejected_with_live_successor(foundation_db,people,released):
    """TE-1 H: no reopen while a live successor exists for the source release."""
    db=foundation_db;x=people;r=released;q=request(db,x,r);accept(db,x,q);g=grant(db,x,q);edit(db,x,g);p=package_of(db,g);reapprove(db,x,p)
    c=assemble(db,x,r,p);db.commit()
    try:q2=request(db,x,r,other=True);accept(db,x,q2)
    except HTTPException:db.rollback();pytest.skip('a live successor already blocks accepting the new request')
    before=counts(db)
    with pytest.raises(HTTPException) as caught:reopen_cycle(db,x,q2)
    assert caught.value.status_code==409;db.rollback();assert counts(db)==before and state(db,c).state=='assembling'


def test_te1_reopen_rejected_when_source_release_not_latest(foundation_db,people,released):
    """TE-1 I: a request on a superseded release can never reopen (Python first, then the database)."""
    db=foundation_db;x=people;r=released;q=request(db,x,r);accept(db,x,q);g=grant(db,x,q);edit(db,x,g);p=package_of(db,g);reapprove(db,x,p)
    c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c);publish(db,x,c)
    with pytest.raises(HTTPException):request(db,x,r,other=True)
    db.rollback()
    # Forge an accepted request on the superseded 1.0 (trigger-free) and try both layers.
    columns=','.join(c.name for c in RevisionRequest.__table__.columns if c.name!='id')
    raw(db,f"INSERT INTO revision_requests ({columns}) SELECT {columns} FROM revision_requests WHERE id=:id",id=q.id)
    forged=db.scalar(select(RevisionRequest).order_by(RevisionRequest.id.desc()))
    raw(db,"INSERT INTO revision_request_states (request_id,state,version) VALUES (:id,'accepted',1)",id=forged.id)
    before=counts(db)
    with pytest.raises(HTTPException) as caught:reopen_cycle(db,x,forged)
    assert caught.value.status_code==409 and 'Güncel yayın sürümü değişti' in caught.value.detail
    db.rollback();assert counts(db)==before


def te1_with_live_other(db,x,r):
    """Q1 closed_no_change, Q3 (explanation) editing with a live grant, package re-approved, Q2 (value) accepted."""
    q1=request(db,x,r);q3=request(db,x,r,other=True);accept(db,x,q1);accept(db,x,q3)
    g1=grant(db,x,q1);g3=grant(db,x,q3);source=source_content(db,g1)
    edit(db,x,g1);edit(db,x,g1,value=source['entries'][0]['value']);edit(db,x,g3,other=True,value='Yeni açıklama')
    p=package_of(db,g1);reapprove(db,x,p);s=db.get(RevisionRequestState,q1.id)
    corrections.close_no_change(db,x['strategy'],q1.id,s.version,'Net değişiklik yok');db.commit()
    q2=request(db,x,r);accept(db,x,q2);return q1,g1,q3,g3,p,q2


def test_te1_reopen_records_resumed_non_overlapping_authority(foundation_db,people,released):
    """TE-1 K (compatible case): a non-overlapping editing request keeps its own grant; the reopen names it explicitly."""
    from tests.test_authorization_foundation import member
    db=foundation_db;x=people;r=released;q1,g1,q3,g3,p,q2=te1_with_live_other(db,x,r)
    member(db,x,'editor2','department_editor',2)  # an active participant of Q3 who is neither director nor requester
    reopen_cycle(db,x,q2)
    e=db.scalar(select(WorkflowEvent).where(WorkflowEvent.event_type=='correction_cycle_reopened'))
    assert json.loads(e.context_json)['resumed_grant_ids']==[g3.id]
    # SEC-2: the holders of a resumed grant are told their authority is live again (with the directors).
    n=db.scalar(select(Notification).where(Notification.event_type=='correction_cycle_reopened'))
    recipients=set(db.scalars(select(NotificationRecipient.user_id).where(NotificationRecipient.notification_id==n.id)))
    assert x['editor2'].id in recipients and corrections.active_participants(db,q3,g3)|corrections.director_recipients(db,q2)==recipients
    g2=grant(db,x,q2);edit(db,x,g2,value='3.75');p=db.get(DirectoratePackage,p.id,populate_existing=True);reapprove(db,x,p)
    c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c);publish(db,x,c)
    assert [db.get(RevisionRequestState,q.id).state for q in (q1,q2,q3)]==['closed_no_change','applied','applied']


def test_te1_reopen_rejected_for_overlapping_active_request(foundation_db,people,released):
    """TE-1 K (incompatible case): an accepted/editing request on the same cell blocks the reopen (Python and database)."""
    db=foundation_db;x=people;r=released;q1,g1,q3,g3,p,q2=te1_with_live_other(db,x,r)
    # Forge (trigger-free) a second accepted request on Q3's cell; normal acceptance refuses the overlap.
    columns=','.join(c.name for c in RevisionRequest.__table__.columns if c.name!='id')
    raw(db,f"INSERT INTO revision_requests ({columns}) SELECT {columns} FROM revision_requests WHERE id=:id",id=q3.id)
    clash=db.scalar(select(RevisionRequest).order_by(RevisionRequest.id.desc()))
    raw(db,"INSERT INTO revision_request_states (request_id,state,version) VALUES (:id,'accepted',1)",id=clash.id)
    before=counts(db)
    with pytest.raises(HTTPException) as caught:reopen_cycle(db,x,clash)
    assert caught.value.status_code==409 and 'Çakışan' in caught.value.detail;db.rollback();assert counts(db)==before
    p=db.get(DirectoratePackage,p.id,populate_existing=True);current=packages.revision(db,p)
    with pytest.raises(DBAPIError,match='strategy_reopen requires current returned successor'):
        with db.begin_nested():forge_direct_reopen(db,x,clash,p,current,db.get(RevisionCorrectionCycle,g1.cycle_id))
    db.rollback();assert counts(db)==before


def forge_direct_reopen(db,x,q,p,current,cycle,key='strategy',reason='Ham yeniden açma',**override):
    e=corrections.history(db,x[key],q,'correction_cycle_reopened',{'cycle_id':cycle.id,'package_id':p.id,'previous_revision_id':current.id,
        'previous_revision':current.revision,'previous_sha256':current.sha256,'resulting_revision':current.revision+1,'resulting_sha256':current.sha256,
        'expected_package_version':p.version,'from_state':'strategy_approved','to_state':'returned'},reason)
    return packages.reopen_correction_package(db,x[key],p,current,cycle,reason,{'reopen_request_id':q.id,'reopen_event_id':e.id,**override})


@pytest.mark.parametrize('forgery',['valid_control','closed_request','rejected_request','accepted_with_grant','no_reopen_event','foreign_event','granted_request','raw_copy'])
def test_te1_raw_reopen_forgeries_rejected(foundation_db,people,released,forgery):
    """TE-1 L: the database never moves the package into reopened authority without exact provenance."""
    db=foundation_db;x=people;r=released;q1,g1,p,q2=te1(db,x,r);cycle=db.get(RevisionCorrectionCycle,g1.cycle_id)
    current=packages.revision(db,p);before=counts(db),rows(db,p)
    if forgery=='valid_control':  # the forging helper itself is exact: with Q2's real provenance the guards accept it
        forge_direct_reopen(db,x,q2,p,current,cycle);db.commit();assert db.get(DirectoratePackage,p.id,populate_existing=True).state=='returned';return
    match={'raw_copy':'Missing active scoped correction authorization/audit','granted_request':'Grant requires an editable'}.get(forgery,'strategy_reopen requires current returned successor')
    with pytest.raises(DBAPIError,match=match):
        with db.begin_nested():
            if forgery=='closed_request':forge_direct_reopen(db,x,q1,p,current,cycle)
            elif forgery=='rejected_request':  # TE-2 (a): not accepted, no grant
                replica(db,"UPDATE revision_request_states SET state='rejected',version=version+1 WHERE request_id=:q",q=q2.id)
                forge_direct_reopen(db,x,q2,p,current,cycle)
            elif forgery=='accepted_with_grant':  # TE-2 (b): accepted, but it already holds a (trigger-free) grant
                m=auth.active_membership(db,x['user'].id,q2.organization_id,q2.department_id);now=auth.server_now(db)
                replica(db,insert(RevisionEditGrant).values(request_id=q2.id,source_release_id=q2.source_release_id,department_id=q2.department_id,
                    cycle_id=cycle.id,membership_ids_json=auth.encode([m.id]),paths_json=auth.encode(corrections.paths(q2)),start_at=now-timedelta(minutes=1),
                    end_at=now+timedelta(hours=1),created_by=x['strategy'].id,formal_basis='Ham izin'))
                forge_direct_reopen(db,x,q2,p,current,cycle)
            elif forgery=='no_reopen_event':
                packages.reopen_correction_package(db,x['strategy'],p,current,cycle,'Ham',{'reopen_request_id':q2.id})
            elif forgery=='foreign_event':
                other=db.scalar(select(WorkflowEvent).where(WorkflowEvent.resource_type=='revision_request',WorkflowEvent.resource_id==str(q2.id)))
                packages.reopen_correction_package(db,x['strategy'],p,current,cycle,'Ham',{'reopen_request_id':q2.id,'reopen_event_id':other.id})
            elif forgery=='granted_request':
                raw_grant(db,x,q2,cycle)
            else:
                copy=packages.append_revision(db,p,x['strategy'],current.content_json,current,'Ham kopya');packages.move(db,p,p.version,'returned',copy.revision)
    db.rollback();assert (counts(db),rows(db,p))==before
    assert db.get(RevisionRequestState,q1.id).state=='closed_no_change'


def raw_grant(db,x,q,cycle):
    now=auth.server_now(db);m=auth.active_membership(db,x['user'].id,q.organization_id,q.department_id)
    db.add(RevisionEditGrant(request_id=q.id,source_release_id=q.source_release_id,department_id=q.department_id,cycle_id=cycle.id,
        membership_ids_json=auth.encode([m.id]),paths_json=auth.encode(corrections.paths(q)),start_at=now-timedelta(minutes=1),
        end_at=now+timedelta(hours=1),created_by=x['strategy'].id,formal_basis='Ham izin'));db.flush()


def test_te1_raw_grant_on_approved_package_rejected(foundation_db,people,released):
    """SEC-B1: no grant can wait on an approved package for a later reopen."""
    db=foundation_db;x=people;q1,g1,p,q2=te1(db,x,released)
    with pytest.raises(DBAPIError,match='Grant requires an editable'):
        with db.begin_nested():raw_grant(db,x,q2,db.get(RevisionCorrectionCycle,g1.cycle_id))
    db.rollback();assert db.scalar(select(func.count(RevisionEditGrant.id)).where(RevisionEditGrant.request_id==q2.id))==0


@pytest.mark.parametrize('same',[True,False])
def test_te1_concurrent_reopens_serialize(foundation_db,people,released,same):
    """TE-1 M: two reopen attempts (same or different new requests) produce exactly one event and one copy revision."""
    db=foundation_db;x=people;r=released;q1,g1,p,q2=te1(db,x,r)
    q3=q2 if same else request(db,x,r,other=True)
    if not same:accept(db,x,q3)
    rev=packages.revision(db,p);versions={q.id:db.get(RevisionRequestState,q.id).version for q in (q2,q3)};pv=p.version;revisions=db.scalar(select(func.count(PackageRevision.id)))
    db.commit();barrier=Barrier(2)
    def reopening(q):
        with Session(db.get_bind(),expire_on_commit=False) as other:
            barrier.wait(timeout=10)
            try:corrections.reopen_cycle(other,other.get(User,x['strategy'].id),q.id,versions[q.id],pv,rev.sha256,'Eş zamanlı yeniden açma');other.commit();return 'reopened'
            except HTTPException as exc:other.rollback();return exc.status_code
    with ThreadPoolExecutor(2) as pool:first,second=pool.submit(reopening,q2),pool.submit(reopening,q3);results=sorted(map(str,(first.result(),second.result())))
    db.expire_all()
    assert results==['409','reopened']
    assert db.scalar(select(func.count(WorkflowEvent.id)).where(WorkflowEvent.event_type=='correction_cycle_reopened'))==1
    assert db.scalar(select(func.count(PackageRevision.id)))==revisions+1
    assert db.scalar(select(func.count(PackageDecision.id)).where(PackageDecision.action=='strategy_reopen'))==1


def test_te1_sqlite_reopen_requires_postgresql(tmp_path):
    """SQLite keeps 'Reopen requires PostgreSQL'; the new A1-P1.1 parity triggers and index exist."""
    path=tmp_path/'a1p11.db'
    run=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env={**os.environ,'DATABASE_URL':f'sqlite:///{path}'},capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    db=sqlite3.connect(path)
    try:
        names={n for (n,) in db.execute("SELECT name FROM sqlite_master WHERE type IN ('trigger','index')")}
        assert {'activity_initial_rework_lineage','report_state_terminal','report_state_final_return','activity_release_freeze_binding',
                'uq_report_candidate_activity_revision','strategy_reopen_decision_guard'}<=names
        assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0]==HEAD
    finally:db.close()


def sqlite_db(tmp_path):
    path=tmp_path/'a1p11p.db'
    run=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env={**os.environ,'DATABASE_URL':f'sqlite:///{path}'},capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    db=sqlite3.connect(path);db.execute('PRAGMA foreign_keys=OFF');return db


def test_sqlite_parity_initial_lineage_and_terminal_states(tmp_path):
    """SQLite parity: first/rework lineage, a unique revision per candidate, terminal returned state, exact final_return."""
    from tests.test_a1p1_workflow_activation import insert as row
    db=sqlite_db(tmp_path)
    try:
        report=row(db,'activity_reports',organization_id=1,period_id=1,current_revision=1,lock_version=0)
        revision=row(db,'activity_report_revisions',report_id=report,revision=1,publication_id=1,previous_revision_id=None)
        common=dict(organization_id=1,resource_scope='activity_report',report_key=str(report),payload_json='{}')
        with pytest.raises(sqlite3.IntegrityError,match='Invalid initial Activity candidate lineage'):
            row(db,'report_candidates',**common,activity_revision_id=revision,sequence=2,manifest_json='{}')
        c=row(db,'report_candidates',**common,activity_revision_id=revision,sequence=1,manifest_json='{}')
        with pytest.raises(sqlite3.IntegrityError):  # unique Activity revision per candidate
            db.execute("INSERT INTO report_candidates (organization_id,resource_scope,report_key,payload_json,activity_revision_id,sequence,manifest_json,period_id,payload_sha256,sha256,created_by) "
                       "VALUES (2,'activity_report','x','{}',?,1,'{}',1,'a','a',1)",(revision,))
        # A rework of a live (not returned) attempt is refused.
        second=row(db,'activity_report_revisions',report_id=report,revision=2,publication_id=1,previous_revision_id=revision)
        rework=json.dumps({'reworks_candidate_id':c,'reworks_candidate_sha256':'a'*64})
        with pytest.raises(sqlite3.IntegrityError,match='Invalid initial Activity candidate lineage'):
            row(db,'report_candidates',**common,activity_revision_id=second,sequence=2,predecessor_candidate_id=c,manifest_json=rework)
        row(db,'report_candidate_states',candidate_id=c,state='assembling',version=0)
        # Without the audit triggers the state can be staged; the terminal / final_return triggers remain.
        for name in ('report_state_update',):db.execute(f'DROP TRIGGER {name}')
        db.execute("UPDATE report_candidate_states SET state='final_approved',version=version+1 WHERE candidate_id=?",(c,))
        final=row(db,'users',role='director',is_active=1,email='final@x');strategy=row(db,'users',role='strategy',is_active=1,email='str@x')
        strategy_assignment=row(db,'final_authority_assignments',organization_id=1,user_id=strategy,active=0)
        retired=row(db,'final_authority_assignments',organization_id=1,user_id=final,active=0)
        foreign=row(db,'final_authority_assignments',organization_id=2,user_id=final,active=1)
        assignment=row(db,'final_authority_assignments',organization_id=1,user_id=final,active=1)
        def decision(actor,reason,assignment_id,event_type='final_return',organization_id=1):
            event=row(db,'workflow_events',event_type=event_type,actor_user_id=actor,reason=reason,organization_id=organization_id,source='manual')
            row(db,'report_decisions',candidate_id=c,action='final_return',candidate_sha256='a'*64,assignment_id=assignment_id,workflow_event_id=event)
        # DB-2: a decision alone is not enough; blank reason, Strategy actor, foreign actor or wrong event are each refused.
        for forged in [(final,' ',assignment),(strategy,'Gerekçe',strategy_assignment),(strategy,'Gerekçe',assignment),(final,'Gerekçe',assignment,'final_approve'),
                       (final,'Gerekçe',retired),(final,'Gerekçe',foreign),(final,'Gerekçe',assignment,'final_return',2)]:
            decision(*forged)
            with pytest.raises(sqlite3.IntegrityError,match='exact final_return decision'):
                db.execute("UPDATE report_candidate_states SET state='returned_to_strategy',version=version+1 WHERE candidate_id=?",(c,))
        decision(final,'Yanlış içerik',assignment)
        db.execute("UPDATE report_candidate_states SET state='returned_to_strategy',version=version+1 WHERE candidate_id=?",(c,))
        with pytest.raises(sqlite3.IntegrityError,match='Terminal report candidate state'):
            db.execute("UPDATE report_candidate_states SET state='final_approved',version=version+1 WHERE candidate_id=?",(c,))
        # The exact rework of the returned attempt is accepted; a sequence skip is not.
        with pytest.raises(sqlite3.IntegrityError,match='Invalid initial Activity candidate lineage'):
            row(db,'report_candidates',**common,activity_revision_id=second,sequence=3,predecessor_candidate_id=c,manifest_json=rework)
        # DB-2: the rework must keep the attempt's period, source and departments and materialize the next revision.
        third=row(db,'activity_report_revisions',report_id=report,revision=3,publication_id=1,previous_revision_id=second)
        for forged in [dict(activity_revision_id=second,period_id=5),
                       dict(activity_revision_id=second,manifest_json=json.dumps({**json.loads(rework),'source_id':99})),
                       dict(activity_revision_id=second,manifest_json=json.dumps({**json.loads(rework),'required_department_ids':[9]})),
                       dict(activity_revision_id=third)]:
            with pytest.raises(sqlite3.IntegrityError,match='Invalid initial Activity candidate lineage'):
                row(db,'report_candidates',**{**common,'sequence':2,'predecessor_candidate_id':c,'manifest_json':rework,**forged})
        row(db,'report_candidates',**common,activity_revision_id=second,sequence=2,predecessor_candidate_id=c,manifest_json=rework)
    finally:db.close()


# ---------------------------------------------------------------- migration

def test_migration_head_functions_and_downgrade_refusal(foundation_db):
    db=foundation_db
    assert db.execute(text('SELECT version_num FROM alembic_version')).scalar_one()==HEAD
    defs={name:db.scalar(text('SELECT pg_get_functiondef(CAST(:n AS regproc))'),{'n':name}) for name in
        ('civensa_final_approved_return','civensa_activity_initial_candidate_guard','civensa_strategy_reopen_decision_guard',
         'civensa_revision_projection_guard','civensa_revision_edit_guard','civensa_initial_package_reopen_guard',
         'civensa_returned_initial_attempt','civensa_initial_rework_reopen','civensa_direct_cycle_reopen','report_binding_guard','civensa_revision_grant_guard')}
    assert 'civensa_direct_cycle_reopen' in defs['civensa_revision_projection_guard'] and 'civensa_direct_cycle_reopen' in defs['civensa_revision_edit_guard']
    assert 'civensa_correction_lineage_authorized' in defs['civensa_revision_projection_guard'] and 'Deviation field is not correctable' in defs['civensa_revision_edit_guard']
    assert 'Final decision freeze mismatch' in defs['report_binding_guard'] and 'Grant requires an editable' in defs['civensa_revision_grant_guard']
    for trigger in ('initial_rework_package_reopen','initial_candidate_package_current','initial_candidate_complete'):  # DB-3: this schema only
        assert db.scalar(text("SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace "
                              "WHERE t.tgname=:t AND n.nspname=current_schema()"),{'t':trigger})==1
    assert db.scalar(text("SELECT count(*) FROM pg_indexes WHERE indexname='uq_report_candidate_activity_revision' AND schemaname=current_schema()"))==1
    assert db.scalar(text("SELECT tgdeferrable AND tginitdeferred FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace "
                          "WHERE t.tgname='initial_candidate_complete' AND n.nspname=current_schema()"))


@pytest.mark.parametrize('foundation_db',['c5e8a1f0b247'],indirect=True)
def test_populated_upgrade_keeps_history_and_refuses_downgrade(foundation_db,people,approved,candidate,monkeypatch):
    """Populated upgrade from c5e8a1f0b247: history sealed, a pre-upgrade keyless rework still verifies and can be reworked, no downgrade."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c,'final_review')
    monkeypatch.setattr(reports,'returned_initial_proof',lambda db,attempt:None)  # Phase 4 behaviour: no reworks_* keys
    old=reports.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,int(p.source_key),[p.id],c.id);db.commit();monkeypatch.undo()
    assert 'reworks_candidate_id' not in json.loads(old.manifest_json);returned_first(db,x,old,'final_review');c=old
    before=sealed(db);db.commit()
    url=db.bind.url.render_as_string(hide_password=False)
    for _ in range(2):
        run=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True)
        assert run.returncode==0,run.stderr
    down=subprocess.run([sys.executable,'-m','alembic','downgrade','-1'],cwd=ROOT,env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True)
    assert down.returncode!=0 and 'A1-P1.1 recovery guards cannot be discarded' in down.stderr
    db.expire_all();assert_sealed(db,before);assert db.execute(text('SELECT version_num FROM alembic_version')).scalar_one()==HEAD
    reports.verify(db,c);new=rework(db,x,p,c);review(db,x,new);approve(db,x,new);assert publish(db,x,new).major==1


@pytest.mark.parametrize('bad',['lone_sha','string_id','other_attempt'])
def test_r10_verify_rejects_malformed_initial_rework_keys(foundation_db,people,approved,candidate,bad):
    """Historical verification fails closed on a malformed initial rework manifest (lone key, wrong type, foreign attempt)."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c);new=rework(db,x,p,c)
    manifest=json.loads(new.manifest_json)
    if bad=='lone_sha':manifest.pop('reworks_candidate_id')
    elif bad=='string_id':manifest['reworks_candidate_id']=str(c.id)
    else:manifest['reworks_candidate_id']=new.id
    with pytest.raises(HTTPException) as caught:reports.verify_initial_rework(db,new,manifest)
    assert caught.value.status_code==409
    reports.verify(db,new)


def test_r10_verify_dispatches_initial_reworks(foundation_db,people,approved,candidate,monkeypatch):
    """TE-6: verify() routes every candidate carrying reworks_* through the initial-rework verifier (and a first candidate not)."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c);new=rework(db,x,p,c);seen=[]
    real=reports.verify_initial_rework
    monkeypatch.setattr(reports,'verify_initial_rework',lambda db,cand,manifest:(seen.append(cand.id),real(db,cand,manifest)))
    reports.verify(db,new);assert seen==[new.id]
    seen.clear();reports.verify(db,c);assert seen==[]
    monkeypatch.setattr(reports,'verify_initial_rework',lambda db,cand,manifest:packages.conflict())
    with pytest.raises(HTTPException) as caught:reports.verify(db,new)
    assert caught.value.status_code==409


def test_r10_two_rounds_sequence_is_deterministic(foundation_db,people,approved,candidate):
    """R10 10: return and rework twice gives sequences 1, 2, 3, each reworking exactly its predecessor."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c)
    b=rework(db,x,p,c,'3.10');returned_first(db,x,b);d=rework(db,x,p,b,'3.20')
    assert [c.sequence,b.sequence,d.sequence]==[1,2,3] and (b.predecessor_candidate_id,d.predecessor_candidate_id)==(c.id,b.id)
    assert json.loads(d.manifest_json)['reworks_candidate_id']==b.id
    with pytest.raises(HTTPException):  # a second rework of the already reworked attempt
        reports.assemble_candidate(db,x['strategy'],p.organization_id,p.resource_scope,int(p.source_key),[p.id],b.id)
    db.rollback();review(db,x,d);approve(db,x,d);assert publish(db,x,d).candidate_id==d.id


def test_r10_initial_reopen_racing_assembly_never_deadlocks(foundation_db,people,approved,candidate):
    """REL-2: the initial package reopen takes the organization lock first, so it cannot deadlock against assembly."""
    db=foundation_db;x=people;p=approved;c=candidate;returned_first(db,x,c);rev=packages.revision(db,p);version=p.version;db.commit();barrier=Barrier(2)
    def reopening():
        with Session(db.get_bind(),expire_on_commit=False) as other:
            barrier.wait(timeout=10)
            try:packages.transition(other,other.get(User,x['strategy'].id),p.id,'strategy_reopen',version,rev.sha256,'Eş zamanlı yeniden açma');other.commit();return 'reopened'
            except HTTPException as exc:other.rollback();return exc.status_code
    def assembling():
        with Session(db.get_bind(),expire_on_commit=False) as other:
            barrier.wait(timeout=10)
            try:reports.assemble_candidate(other,other.get(User,x['strategy'].id),p.organization_id,p.resource_scope,int(p.source_key),[p.id],c.id);other.commit();return 'assembled'
            except HTTPException as exc:other.rollback();return exc.status_code
    with ThreadPoolExecutor(2) as pool:first,second=pool.submit(reopening),pool.submit(assembling);results=(first.result(),second.result())
    assert set(results)<={'reopened','assembled',409}  # a deadlock would surface as a DBAPIError here
    db.expire_all();package_state=db.get(DirectoratePackage,p.id).state;candidates=db.scalar(select(func.count(ReportCandidate.id)))
    assert (package_state,candidates) in {('returned',1),('strategy_approved',2)}


def test_te1_surviving_closed_edit_still_blocks_publication(foundation_db,people,released):
    """S3C-2 B2 unchanged: after the reopen, a closed_no_change edit that still stands is refused at publication."""
    db=foundation_db;x=people;r=released;q1=request(db,x,r);accept(db,x,q1);g1=grant(db,x,q1);edit(db,x,g1,value='2.75')
    p=package_of(db,g1);reapprove(db,x,p);s=db.get(RevisionRequestState,q1.id)
    corrections.close_no_change(db,x['strategy'],q1.id,s.version,'Uygulanmayacak');db.commit()
    q2=request(db,x,r,other=True);accept(db,x,q2);reopen_cycle(db,x,q2);g2=grant(db,x,q2);edit(db,x,g2,other=True,value='Yeni açıklama')
    p=db.get(DirectoratePackage,p.id,populate_existing=True);reapprove(db,x,p)
    c=assemble(db,x,r,p);db.commit();review(db,x,c);approve(db,x,c);before=counts(db)
    with pytest.raises(HTTPException) as caught:publish(db,x,c)
    assert caught.value.status_code==409 and 'closed_no_change' in caught.value.detail
    db.rollback();assert counts(db)==before and state(db,c).state=='final_approved'
