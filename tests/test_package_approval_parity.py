"""Approval blockers operate on exact immutable snapshots at both control layers."""
import json
from copy import deepcopy
from decimal import Decimal
import pytest
from sqlalchemy import select, func
from app.models import *
from app import package_service as service, program_service as program
from tests.test_package_workflow import foundation_db, people, package, act, submit, error, edit
pytestmark=pytest.mark.postgres


def patch(db,x,p,items):
    current=service.revision(db,p)
    service.edit_package(db,x['user'],p.id,p.version,current.sha256,items);db.commit()


def corrupt_copy(db,x,p,modify):
    # Simulate a snapshot admitted by the pre-fix checkpoint. Append a new immutable
    # fixture revision, never overwrite protected content; bypass service only in tests.
    old=service.revision(db,p);content=json.loads(old.content_json);modify(content)
    new=service.append_revision(db,p,x['user'],service.auth.encode(content),old,'Pre-fix snapshot fixture')
    service.move(db,p,p.version,p.state,new.revision);db.commit()


def assert_blocked(db,x,p,action='director_approve',key='director'):
    before=(p.state,p.version,db.scalar(select(func.count(PackageDecision.id))),db.scalar(select(func.count(WorkflowEvent.id))))
    with pytest.raises(Exception) as caught:act(db,x,p,action,key)
    from fastapi import HTTPException
    assert isinstance(caught.value,HTTPException) and caught.value.status_code==409
    detail=caught.value.detail;assert detail['blockers'] and detail['sha256']==service.revision(db,p).sha256
    assert detail['revision_id']==service.revision(db,p).id
    assert (p.state,p.version,db.scalar(select(func.count(PackageDecision.id))),db.scalar(select(func.count(WorkflowEvent.id))))==before
    return detail


@pytest.mark.parametrize('invalid',['missing','needs_review','explanation','evidence','delta','definition','missing_entry'])
def test_activity_director_blockers(foundation_db,people,package,invalid):
    if package.resource_scope!='activity_report':
        # Performance counterpart: parity checker consumes the same exact snapshot.
        assert program.validate_department_snapshot(json.loads(service.revision(foundation_db,package).content_json),package.period_id,package.department_id)[0]==[]
        return
    db=foundation_db;x=people;p=package
    if invalid=='missing':patch(db,x,p,[{'path':['entries',0,'value'],'value':''},{'path':['entries',0,'state'],'value':'missing'}])
    elif invalid=='needs_review':patch(db,x,p,[{'path':['entries',0,'state'],'value':'needs_review'}])
    elif invalid=='explanation':patch(db,x,p,[{'path':['entries',0,'value'],'value':'2.75'},{'path':['entries',0,'explanation'],'value':''}])
    elif invalid=='evidence':corrupt_copy(db,x,p,lambda c:c['entries'][0].update(evidence=[]))
    elif invalid=='delta':corrupt_copy(db,x,p,lambda c:c['entries'][0]['deviation'].update(delta='999'))
    elif invalid=='definition':corrupt_copy(db,x,p,lambda c:c['entries'][0]['definition'].update(name='Client supplied definition'))
    else:corrupt_copy(db,x,p,lambda c:c.update(entries=[]))
    # Editor submission is an internal review; approval, not submission, is the gate.
    if invalid in {'evidence','delta','definition','missing_entry'}:service.move(db,p,p.version,'director_review',p.current_revision);db.commit()
    else:submit(db,x,p)
    assert_blocked(db,x,p)


@pytest.mark.parametrize('invalid',['field','finance'])
def test_director_business_blockers(foundation_db,people,package,invalid):
    db=foundation_db;x=people;p=package
    if p.resource_scope=='performance_program':
        items=[{'path':['cards',0,'goal'],'value':''}] if invalid=='field' else [{'path':['activities',0,'costs',0,'amount'],'value':'999'}]
    else:
        items=[{'path':['entries',0,'explanation'],'value':''},{'path':['entries',0,'value'],'value':'2.75'}] if invalid=='field' else [{'path':['entries',0,'state'],'value':'needs_review'}]
    patch(db,x,p,items);submit(db,x,p);assert_blocked(db,x,p)


def test_valid_snapshots_both_controls_and_live_invalid_rows_ignored(foundation_db,people,package):
    db=foundation_db;x=people;p=package;submit(db,x,p)
    frozen=service.revision(db,p)
    # Contradict live business rows; they cannot substitute for the reviewed copy.
    x['card'].goal='';db.scalar(select(IndicatorValue)).state='needs_review';db.commit()
    act(db,x,p,'director_approve');act(db,x,p,'strategy_approve','strategy')
    assert p.state=='strategy_approved' and service.revision(db,p).sha256==frozen.sha256


def test_strategy_independently_revalidates(foundation_db,people,package):
    db=foundation_db;x=people;p=package;submit(db,x,p);act(db,x,p,'director_approve')
    if p.resource_scope=='performance_program':corrupt_copy(db,x,p,lambda c:c['cards'][0].update(goal=''))
    else:corrupt_copy(db,x,p,lambda c:c['entries'][0].update(state='needs_review'))
    assert_blocked(db,x,p,'strategy_approve','strategy')


def test_returned_edit_must_pass_again(foundation_db,people,package):
    db=foundation_db;x=people;p=package;submit(db,x,p);act(db,x,p,'director_approve')
    act(db,x,p,'strategy_return','strategy','Kaynağı kontrol edin')
    items=[{'path':['cards',0,'responsible'],'value':''}] if p.resource_scope=='performance_program' else [{'path':['entries',0,'state'],'value':'needs_review'}]
    patch(db,x,p,items);submit(db,x,p);assert_blocked(db,x,p)


def test_client_delta_cannot_hide_explanation_requirement(foundation_db,people,package):
    db=foundation_db;x=people;p=package
    if p.resource_scope=='performance_program':
        assert program.validate_department(db,p.period_id,p.department_id)==program.validate_department_snapshot(json.loads(service.revision(db,p).content_json),p.period_id,p.department_id)
        return
    patch(db,x,p,[{'path':['entries',0,'value'],'value':'2.75'},{'path':['entries',0,'explanation'],'value':''},
        {'path':['entries',0,'deviation'],'value':{'delta':'0','target_definition_revision_id':-1}}])
    current=service.revision(db,p);entry=json.loads(current.content_json)['entries'][0]
    assert Decimal(entry['deviation']['delta'])==Decimal('1')
    submit(db,x,p);assert_blocked(db,x,p)


@pytest.mark.parametrize('field',['rationale','goal','responsible','explanation','calculation_method','data_source'])
def test_program_live_snapshot_validation_parity(foundation_db,people,field):
    db=foundation_db;x=people
    setattr(x['card'],field,'');db.commit()
    content=program.department_package_snapshot(db,x['period'].id,x['department'].id)
    live=program.validate_department(db,x['period'].id,x['department'].id)
    assert live[0] and program.validate_department_snapshot(content,x['period'].id,x['department'].id)==live


@pytest.mark.parametrize('invalid',['target_state','no_target','card_scope','subprogram_period','activity_explanation','catalogue','funding','personnel','economic_cells','economic_totals','missing_cards','missing_indicators'])
def test_program_frozen_business_rules(foundation_db,people,invalid):
    db=foundation_db;x=people
    c=program.department_package_snapshot(db,x['period'].id,x['department'].id)
    if invalid=='target_state':c['indicators'][0]['values'][0]['state']='needs_review'
    elif invalid=='no_target':c['indicators'][0]['values']=[]
    elif invalid=='card_scope':c['indicators'][0]['subprogram_id']=999
    elif invalid=='subprogram_period':c['validation_context']['subprograms'][0]['period_id']=999
    elif invalid=='activity_explanation':c['activities'][0]['explanation']=''
    elif invalid=='catalogue':c['validation_context']['responsible_ids']=[]
    elif invalid=='funding':c['activities'][0]['costs'][0]['amount']='999'
    elif invalid=='personnel':c['department_costs'][0]['amount']=None
    elif invalid=='economic_cells':c['economics'].pop()
    elif invalid=='economic_totals':c['economics'][0]['amount']='999'
    elif invalid=='missing_cards':c['cards']=[]
    else:c['indicators']=[]
    assert program.validate_department_snapshot(c,x['period'].id,x['department'].id)[0]


def test_legacy_activity_approval_still_blocks(foundation_db,people,package):
    from app import activity_contract_service as contract
    db=foundation_db;x=people;p=package
    if p.resource_scope=='performance_program':
        snapshot=program.department_package_snapshot(db,p.period_id,p.department_id)
        assert program.validate_department_snapshot(snapshot,p.period_id,p.department_id)==program.validate_department(db,p.period_id,p.department_id)
        return
    item=db.scalar(select(ReportIndicator).where(ReportIndicator.report_revision_id==p.report_revision_id))
    contract.save_actual(db,x['user'],item.id,1,'1.75','needs_review',[],'',{});db.commit()
    # The revision author cannot approve it; reach the original data-validation
    # gate with an independent Strategy director instead.
    strategy_department=Department(organization_id=x['department'].organization_id,name='Strateji Geliştirme Müdürlüğü')
    db.add(strategy_department);db.flush()
    approver=User(email='parity-approver@example.invalid',full_name='Strateji Müdürü',role='strategy',
                  department_id=strategy_department.id,position='director',password_hash='unused')
    db.add(approver);db.commit()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as caught:
        contract.approve_report(db,approver,p.report_revision_id)
    assert caught.value.status_code==409
    assert any(blocker['report_indicator_id']==item.id and
               blocker['message']=='Doğrulanmış gerçekleşme ve tam dayanak kaynağı girin.'
               for blocker in caught.value.detail['blockers'])
    assert db.scalar(select(func.count(ActivityReportApproval.id)))==0


def test_old_program_snapshot_without_frozen_relationship_context_fails_closed(foundation_db,people,package):
    db=foundation_db;x=people;p=package;before=service.revision(db,p)
    if p.resource_scope=='performance_program':corrupt_copy(db,x,p,lambda c:c.pop('validation_context'))
    else:corrupt_copy(db,x,p,lambda c:c.update(publication_sha256='0'*64))
    service.move(db,p,p.version,'director_review',p.current_revision);db.commit()
    assert_blocked(db,x,p)
    assert service.digest(before.content_json)==before.sha256
    assert db.get(PackageRevision,before.id).content_json==before.content_json
