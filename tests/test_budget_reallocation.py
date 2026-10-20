"""CIV-031 acceptance over real login + CSRF and disposable PostgreSQL."""
import copy
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app import budget_service as service
from app import authorization_service as auth
from app.models import (Activity, ActivityCostValue, EconomicValue, Department, Submission,
    SubmissionEvent, BudgetOperation, BudgetOperationLine, AuditLog, Notification,
    DirectorateMembership, AuthorityDelegation, DelegationRevocation)
from app.program_service import activity_source_disagreements
from tests.test_released_permissions import actors, http

pytestmark = pytest.mark.postgres


@pytest.fixture
def budget(db, sample, actors):
    a = sample['department']
    b = db.get(Department, actors['other'].department_id)
    # Leave other PP years intact; replace only the selected year values.
    for row in db.scalars(select(EconomicValue).where(EconomicValue.year == 2027)):
        db.delete(row)
    for row in db.scalars(select(ActivityCostValue).where(ActivityCostValue.year == 2027)):
        db.delete(row)
    db.flush()
    for dep in [a, b]:
        sub = db.scalar(select(Submission).where(Submission.department_id == dep.id))
        if not sub:
            sub = Submission(department_id=dep.id, period_id=sample['period'].id)
            db.add(sub)
        sub.status = 'approved'; sub.revision = 1
        for category, amount in [('personnel','1000000.00'),('sgk','200000.00'),('goods_services','4000000.01'),('capital','4000000.02'),('current_transfers','4000000.03')]:
            for fund, value in [('inside',Decimal(amount)),('outside',Decimal('100000.00')),('total',Decimal(amount)+Decimal('100000.00'))]:
                db.add(EconomicValue(period_id=sample['period'].id, department_id=dep.id, year=2027,
                    value_kind='budget', category=category, program_group='service', funding_type=fund, amount=value))
        for i, amount in enumerate(['4000000.01','4000000.02','4000000.03','1200000.00']):
            act = sample['activity'] if dep.id == a.id and i == 0 else Activity(period_id=sample['period'].id,
                department_id=dep.id, name=f'{dep.name} Faaliyet {i+1}', subprogram_id=sample['subprogram'].id)
            act.contract_bound = i == 3
            db.add(act); db.flush()
            for fund, value in [('inside',Decimal(amount)),('outside',Decimal('100000.00')),('total',Decimal(amount)+Decimal('100000.00'))]:
                db.add(ActivityCostValue(activity_id=act.id, year=2027, value_kind='budget', funding_type=fund, amount=value))
    db.commit()
    return {'period_id':sample['period'].id, 'year':2027, 'value_kind':'budget', 'change_total':False,
            'change_outside':False, 'legs':[{'department_id':a.id,'direction':'decrease','amount':'5000000.00'},
            {'department_id':b.id,'direction':'increase','amount':'5000000.00'}]}


def reference(**kwargs):
    return {'phase':'before_adoption','reference_type':'mayor_instruction','reference_date':'2026-10-01',
            'reference_number':'2026/123','reason':'Başkanlık talimatına uygun yatırım ödeneği aktarımı.', **kwargs}


def preview(client, request):
    response = client.post('/api/budget-reallocations/preview', json=request)
    assert response.status_code == 200, response.text
    return response.json()


def apply(client, data, **ref):
    return client.post('/api/budget-reallocations/apply', json={'token':data['token'],**reference(**ref)})


def test_exact_amounts_protected_lines_rounding_history_and_reverse(db, sample, budget, http):
    client = http('strategy_director')
    before = {(r.__tablename__,r.id):service.state(r) for model in (EconomicValue,ActivityCostValue) for r in db.scalars(select(model))}
    p = preview(client, budget)
    assert db.scalar(select(func.count(BudgetOperation.id))) == 0
    assert db.scalar(select(func.count(SubmissionEvent.id))) == 0
    for leg in budget['legs']:
        sign = -1 if leg['direction']=='decrease' else 1
        for table in ('economic_values','activity_cost_values'):
            lines = [l for l in p['lines'] if l['department_id']==leg['department_id'] and l['value_table']==table and l['funding_type']=='inside']
            assert sum((Decimal(l['change']) for l in lines),Decimal(0)) == sign * Decimal('5000000.00')
            changed = [Decimal(l['change']) for l in lines if l['changed']]
            assert sorted(abs(x) for x in changed) == [Decimal('1666666.66'),Decimal('1666666.67'),Decimal('1666666.67')]
        assert [l for l in p['lines'] if l['department_id']==leg['department_id'] and l['funding_type']=='outside' and l['changed']] == []
    response = apply(client,p)
    assert response.status_code == 200, response.text
    oid = response.json()['id']
    db.expire_all()
    assert all(s.status=='approved' and s.revision==2 for s in db.scalars(select(Submission)))
    assert db.scalar(select(func.count(Notification.id))) == 2
    assert all(n.link == f'/department/{n.department_id}?period_id={budget["period_id"]}'
               for n in db.scalars(select(Notification)))
    assert all('Başkanlık talimatı ile aktarma' in s.note for s in db.scalars(select(SubmissionEvent)))
    for row in db.scalars(select(EconomicValue).where(EconomicValue.category.in_(['personnel','sgk']))):
        assert service.state(row) == before[(row.__tablename__,row.id)]
    for act in db.scalars(select(Activity).where(Activity.contract_bound.is_(True))):
        for row in act.cost_values:
            assert service.state(row) == before[(row.__tablename__,row.id)]
    assert client.get(f'/budget-reallocations/{oid}').status_code == 200
    response = client.post(f'/api/budget-reallocations/{oid}/reverse', json=reference())
    assert response.status_code == 200, response.text
    db.expire_all()
    for model in (EconomicValue,ActivityCostValue):
        for row in db.scalars(select(model)):
            assert service.state(row) == before[(row.__tablename__,row.id)]
    assert db.scalar(select(BudgetOperation).where(BudgetOperation.reverses_id==oid))
    assert client.post(f'/api/budget-reallocations/{oid}/reverse',json=reference()).status_code == 409


def test_ratio_outside_and_source_disagreement_preserved(db, sample, budget, http):
    client=http('strategy_director')
    total=db.scalar(select(ActivityCostValue).where(ActivityCostValue.activity_id==sample['activity'].id, ActivityCostValue.year==2027,ActivityCostValue.funding_type=='total'))
    total.source_amount = total.amount + Decimal('13.45'); db.commit()
    db.refresh(sample['activity'])
    old = activity_source_disagreements(sample['activity'])
    budget['change_outside']=True
    for leg in budget['legs']:
        del leg['amount']; leg['ratio']='3'
    p=preview(client,budget)
    assert p['summaries'][0]['amount']=='396000.00'
    assert p['summaries'][0]['outside_change']=='-9000.00'
    assert '13,45' in p['warnings'][0]
    for did in [x['department_id'] for x in budget['legs']]:
        for table in ('economic_values','activity_cost_values'):
            delta=sum((Decimal(l['change']) for l in p['lines'] if l['department_id']==did and l['funding_type']=='outside' and l['value_table']==table),Decimal(0))
            assert abs(delta)==Decimal('9000')
    assert apply(client,p).status_code==200
    db.expire_all()
    assert activity_source_disagreements(sample['activity'])==old
    assert total.source_amount == Decimal('4100013.46')


def test_ratio_matching_source_does_not_create_conflict(db,sample,budget,http):
    total=db.scalar(select(ActivityCostValue).where(ActivityCostValue.activity_id==sample['activity'].id, ActivityCostValue.year==2027,ActivityCostValue.funding_type=='total'))
    total.source_amount=total.amount;db.commit()
    client=http('strategy_director')
    assert apply(client,preview(client,budget)).status_code==200
    db.expire_all()
    assert not activity_source_disagreements(sample['activity'])


def test_decrease_exceeds_eligible_and_no_write(db,budget,http):
    budget['legs'][0]['amount']='12000000.07';budget['change_total']=True
    response=http('strategy_director').post('/api/budget-reallocations/preview',json=budget)
    assert response.status_code==422
    assert all(x in response.json()['detail'] for x in ['12.000.000,06','12.000.000,07','azaltın'])
    assert db.scalar(select(func.count(BudgetOperation.id)))==0


def test_eligibility_choices_and_one_sided(budget,http):
    client=http('strategy_director')
    budget['legs']=budget['legs'][:1]
    assert client.post('/api/budget-reallocations/preview',json=budget).status_code==422
    budget['change_total']=True;budget['legs'][0]['excluded_categories']=['capital']
    p=preview(client,budget)
    assert all(not l['changed'] for l in p['lines'] if l['label'].startswith('Sermaye Giderleri'))
    activity_id=p['choices'][0]['activities'][0]['id']
    budget['legs'][0]['excluded_activities']=[activity_id]
    p=preview(client,budget)
    assert apply(client,p).status_code==200


@pytest.mark.parametrize('ref',[
    {'phase':''}, {'reference_number':''}, {'reference_date':'2026-02-30'}, {'reason':''},
    {'phase':'after_adoption','reference_type':'mayor_instruction'},
    {'phase':'after_adoption','reference_type':'executive_decision'}])
def test_invalid_reference_refused(budget,http,ref):
    client=http('strategy_director');p=preview(client,budget)
    assert apply(client,p,**ref).status_code==422


def test_council_after_adoption_and_csrf(budget,http):
    client=http('strategy_director');p=preview(client,budget)
    token=client.headers.pop('X-CSRF-Token')
    assert apply(client,p).status_code==403
    client.headers['X-CSRF-Token']=token
    assert apply(client,p,phase='after_adoption',reference_type='council_decision').status_code==200


def test_staff_denied_delegation_grant_and_revocation(db,actors,budget,http):
    staff=http('strategy_staff');director=http('strategy_director')
    assert staff.post('/api/budget-reallocations/preview',json=budget).status_code==403
    for user,role,slot in [(actors['strategy_director'],'department_director',3),(actors['strategy_staff'],'department_editor',1)]:
        db.add(DirectorateMembership(organization_id=db.get(Department,user.department_id).organization_id,
            department_id=user.department_id,user_id=user.id,role_code=role,slot=slot,active=True,
            formal_basis='Test görevlendirme',created_by=actors['strategy_director'].id))
    db.commit()
    now=auth.server_now(db)
    grant=director.post('/api/budget-reallocations/delegations',json={'delegate_user_id':actors['strategy_staff'].id,
        'start_at':(now-timedelta(minutes=1)).isoformat(),'end_at':(now+timedelta(days=1)).isoformat(),'formal_basis':'Onaylı veri düzeltme yetki devri'})
    assert grant.status_code==200,grant.text
    gid=grant.json()['id']
    assert db.get(AuthorityDelegation,gid).authority_kind=='approved_data_correction'
    assert auth.active_delegation(db,db.get(Department,actors['strategy_staff'].department_id).organization_id,actors['strategy_staff'].department_id) is None
    p=preview(staff,budget)
    assert apply(staff,p).status_code==200
    p=preview(staff,budget)
    assert director.post(f'/api/budget-reallocations/delegations/{gid}/revoke',json={'reason':'Yetki süreci tamamlandı.'}).status_code==200
    assert apply(staff,p).status_code==403


def test_flag_audited_approved_status_and_stale(db,sample,budget,http):
    client=http('strategy_director');p=preview(client,budget)
    path=f"/api/activities/{sample['activity'].id}/contract-bound"
    assert http('other').post(path,json={'contract_bound':True}).status_code==403
    assert http('staff').post(path,json={'contract_bound':True}).status_code==200
    assert apply(client,p).status_code==409
    assert all(s.status=='approved' for s in db.scalars(select(Submission)))
    assert client.post(path,json={'contract_bound':False}).status_code==200
    assert db.scalar(select(func.count(AuditLog.id)).where(AuditLog.action=='activity_contract_bound'))==2


def test_stale_repeat_and_reversal_changed_value(db,budget,http):
    client=http('strategy_director');p=preview(client,budget)
    response=apply(client,p);assert response.status_code==200
    assert apply(client,p).status_code==409
    oid=response.json()['id']
    row=db.scalar(select(EconomicValue).where(EconomicValue.category=='capital',EconomicValue.year==2027,EconomicValue.funding_type=='inside'))
    row.amount+=Decimal('.01');db.commit()
    response=client.post(f'/api/budget-reallocations/{oid}/reverse',json=reference())
    assert response.status_code==409 and 'değer değişti' in response.json()['detail']


def test_concurrent_apply_exactly_once(db,actors,budget,http):
    p=preview(http('strategy_director'),budget)
    actor_id=actors['strategy_director'].id
    barrier=threading.Barrier(2)
    def run():
        with Session(db.get_bind(),expire_on_commit=False) as session:
            actor=session.get(type(actors['strategy_director']),actor_id)
            barrier.wait(timeout=5)
            try:
                operation=service.apply(session,actor,{'token':p['token'],**reference()})
                session.commit();return 200
            except HTTPException as exc:
                session.rollback();return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run) for _ in range(2)]
        assert sorted(f.result(timeout=15) for f in futures)==[200,409]
    db.expire_all()
    assert db.scalar(select(func.count(BudgetOperation.id)))==1


def test_invalid_inputs_are_turkish_422(budget,http):
    client=http('strategy_director')
    for bad in [None,{},dict(budget,year=True),dict(budget,change_outside='false'),dict(budget,legs=[{'department_id':1,'direction':'increase','amount':0.1}])]:
        response=client.post('/api/budget-reallocations/preview',json=bad)
        assert response.status_code==422,response.text
        assert isinstance(response.json()['detail'],str)


@pytest.mark.parametrize('transfer_scope,ref_type',[('functional_classes','executive_decision'),('other','mayor_approval')])
def test_within_directorate_selections_and_reference(db,budget,http,transfer_scope,ref_type):
    client=http('strategy_director')
    budget['change_total']=False
    did=budget['legs'][0]['department_id']
    acts=db.scalars(select(Activity).where(Activity.department_id==did,Activity.contract_bound.is_(False)).order_by(Activity.id)).all()
    budget['legs']=[{'department_id':did,'direction':'decrease','amount':'10.01',
        'excluded_categories':['capital','current_transfers'],'excluded_activities':[a.id for a in acts[1:]]},
        {'department_id':did,'direction':'increase','amount':'10.01',
        'excluded_categories':['goods_services'],'excluded_activities':[acts[0].id]}]
    p=preview(client,budget)
    assert sum(Decimal(s['change']) for s in p['summaries'])==0
    assert apply(client,p,phase='after_adoption',transfer_scope=transfer_scope,reference_type='council_decision').status_code==422
    assert apply(client,p,phase='after_adoption',transfer_scope=transfer_scope,reference_type=ref_type).status_code==200


def test_concurrent_http_apply_real_sessions(db,actors,budget,http):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import get_db
    first=http('strategy_director');second=http('strategy_director')
    p=preview(first,budget)
    bind=db.get_bind();db.rollback()
    def database():
        with Session(bind,expire_on_commit=False) as session:
            yield session
    app.dependency_overrides[get_db]=database
    barrier=threading.Barrier(2)
    def run(client):
        barrier.wait(timeout=5)
        return apply(client,p)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run,client) for client in [first,second]]
        results=[f.result(timeout=15) for f in futures]
    assert sorted(r.status_code for r in results)==[200,409]
    assert 'önizleme' in next(r for r in results if r.status_code==409).json()['detail']


def test_package_projection_history_approval_preserved(db,budget,http):
    from app.models import DirectoratePackage, WorkflowEvent
    packages=[]
    for leg in budget['legs']:
        dep=db.get(Department,leg['department_id'])
        p=DirectoratePackage(organization_id=dep.organization_id,department_id=dep.id,
            resource_scope='performance_program',period_id=budget['period_id'],source_key=str(budget['period_id']),
            state='strategy_approved',version=3,current_revision=1)
        db.add(p);packages.append(p)
    db.commit()
    client=http('strategy_director');assert apply(client,preview(client,budget)).status_code==200
    db.expire_all()
    assert all(p.state=='strategy_approved' for p in packages)
    assert db.scalar(select(func.count(WorkflowEvent.id)).where(WorkflowEvent.event_type=='budget_reallocation'))==2


def test_preview_tampering_and_other_actor_refused(budget,http):
    client=http('strategy_director');p=preview(client,budget)
    damaged=dict(p,token=p['token']+'corrupt')
    assert apply(client,damaged).status_code==409
    assert apply(http('strategy_staff'),p).status_code==403


def test_missing_split_is_not_zero_and_transaction_rolls_back(db,sample,budget,http):
    row=db.scalar(select(ActivityCostValue).where(ActivityCostValue.activity_id==sample['activity'].id,ActivityCostValue.year==2027,ActivityCostValue.funding_type=='outside'))
    row.amount=None;db.commit()
    client=http('strategy_director')
    response=client.post('/api/budget-reallocations/preview',json=budget)
    assert response.status_code==422 and 'eksik' in response.json()['detail']
    assert db.scalar(select(func.count(BudgetOperation.id)))==0


def test_notification_failure_rolls_back_every_value_and_history(db,budget,http):
    from sqlalchemy import event
    client=http('strategy_director');p=preview(client,budget)
    before={l['value_id']:l['before'] for l in p['lines'] if l['value_table']=='economic_values'}
    def refuse(*args):raise RuntimeError('synthetic notification failure')
    event.listen(Notification,'before_insert',refuse)
    try:
        with pytest.raises(RuntimeError,match='synthetic notification failure'):
            apply(client,p)
    finally:event.remove(Notification,'before_insert',refuse)
    db.expire_all()
    assert db.scalar(select(func.count(BudgetOperation.id)))==0
    assert db.scalar(select(func.count(BudgetOperationLine.id)))==0
    assert db.scalar(select(func.count(SubmissionEvent.id)))==0
    for row in db.scalars(select(EconomicValue).where(EconomicValue.year==2027)):
        assert str(row.amount)==before[row.id]
    assert all(s.status=='approved' and s.revision==1 for s in db.scalars(select(Submission)))


def test_closed_period_directorate_refuses_increase_with_receivers_but_allows_decrease(db, sample, budget, http, monkeypatch):
    from datetime import date
    from starlette.datastructures import FormData
    from app.models import DepartmentScope
    from app import structure_service

    closed = sample['department']
    receiver = db.get(Department, budget['legs'][1]['department_id'])
    other_receiver = Department(organization_id=closed.organization_id, name='Diğer Devralan Kurum Adı')
    db.add(other_receiver); db.flush()
    scope = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == budget['period_id'], DepartmentScope.department_id == closed.id))
    scope.display_name = 'Dönemde Kapanan Müdürlük'
    for dep, name in [(receiver, 'Dönemde Devralan Birim'), (other_receiver, 'Dönemde İkinci Devralan')]:
        db.add(DepartmentScope(period_id=budget['period_id'], department_id=dep.id, display_name=name, status='required'))
    db.commit()
    structure_service.save_change(db, sample['strategy'], FormData([
        ('organization_id', str(closed.organization_id)), ('period_id', str(budget['period_id'])),
        ('change_type', 'SPLIT'), ('effective_date', '2027-07-01'),
        ('council_decision_date', '2027-06-20'), ('council_decision_no', '2027/48'),
        ('from_department_ids', str(closed.id)), ('to_department_ids', str(receiver.id)),
        ('to_department_ids', str(other_receiver.id))]))
    db.commit()
    assert not closed.is_active and scope.active_to == date(2027, 7, 1)
    client = http('strategy_director')
    incoming = copy.deepcopy(budget)
    incoming['legs'][0]['direction'] = 'increase'
    incoming['legs'][1]['direction'] = 'decrease'
    monkeypatch.setattr(service, 'operation_date', lambda db: date(2027, 7, 1))
    earlier = preview(client, incoming)  # Closure date is inclusive.
    monkeypatch.setattr(service, 'operation_date', lambda db: date(2027, 7, 2))
    for response in [client.post('/api/budget-reallocations/preview', json=incoming), apply(client, earlier)]:
        assert response.status_code == 422, response.text
        message = response.json()['detail']
        assert all(text in message for text in ['Dönemde Kapanan Müdürlük', '01.07.2027', 'Dönemde Devralan Birim', 'Dönemde İkinci Devralan', 'artış'])
        assert closed.name not in message and receiver.name not in message
    assert db.scalar(select(func.count(BudgetOperation.id))) == 0
    page = client.get('/budget-reallocations/new')
    assert 'Dönemde Kapanan Müdürlük' in page.text
    outgoing = preview(client, budget)
    assert outgoing['summaries'][0]['name'] == 'Dönemde Kapanan Müdürlük'
    response = apply(client, outgoing)
    assert response.status_code == 200, response.text
    detail = client.get(f"/budget-reallocations/{response.json()['id']}")
    assert 'Dönemde Kapanan Müdürlük' in detail.text and 'Dönemde Devralan Birim' in detail.text
    assert all('Dönemde' in n.message for n in db.scalars(select(Notification)))
    assert 'Dönemde Kapanan Müdürlük' in db.scalar(select(SubmissionEvent).where(SubmissionEvent.department_id == closed.id)).note
    audit = db.scalar(select(AuditLog).where(AuditLog.action == 'budget_reallocation'))
    assert 'Dönemde Kapanan Müdürlük' in audit.details and 'Dönemde Devralan Birim' in audit.details
