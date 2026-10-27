"""Phase 3 real migrated PostgreSQL, both resources, no rollout."""
from datetime import timedelta
import json
import pytest
from tests.race_helpers import run_race
from fastapi import HTTPException
from sqlalchemy import select, text, event, func
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from app.models import *
from app import authorization_service as auth, package_service as service, activity_contract_service as contract
from tests.test_authorization_foundation import foundation_db, people, established, grant
pytestmark=pytest.mark.postgres

@pytest.fixture(params=['performance_program','activity_report'])
def package(foundation_db,people,request):
    db=foundation_db;x=people;established(db,x)
    if request.param=='performance_program':source=x['period'].id
    else:
        payload,defs=contract.freeze_program_payload(db,x['period'].id,x['strategy']);raw=contract.canonical(payload)
        pub=Publication(period_id=x['period'].id,version=1,snapshot_json=raw,sha256=contract.digest(raw),created_by=x['strategy'].id)
        db.add(pub);db.flush();contract.attach_publication_definitions(db,pub,defs,x['strategy']);db.commit()
        r=contract.create_report_revision(db,x['strategy'],pub.id,x['department'].organization_id);db.commit();source=r.id
        slot=db.scalar(select(ReportIndicator)).id
        contract.save_actual(db,x['user'],slot,0,'1.75','verified',
            [{'title':'Defter','locator':'s1','source_revision':'r1'}],'Hedef gerçekleşti',{});db.commit()
    row=service.create_package(db,x['user'],x['department'].organization_id,x['department'].id,request.param,source)
    db.commit();return row

def act(db,x,p,action,key='director',reason=''):
    r=service.revision(db,p)
    result=service.transition(db,x[key],p.id,action,p.version,r.sha256,reason)
    db.commit();return result

def submit(db,x,p):return act(db,x,p,'submit_to_director','user')

def patches(p,value='2.50'):
    if p.resource_scope=='performance_program':return [{'path':['indicators',0,'values',0,'value'],'value':value},{'path':['indicators',0,'values',0,'state'],'value':'verified'}]
    return [{'path':['entries',0,'value'],'value':value},{'path':['entries',0,'state'],'value':'verified'},
        {'path':['entries',0,'explanation'],'value':'Kaynak kayıtlarına göre fark oluştu.'}]

def edit(db,x,p,key='director',value='2.50'):
    row=service.edit_package(db,x[key],p.id,p.version,service.revision(db,p).sha256,patches(p,value),'Kaynak düzeltmesi')
    db.commit();return row

def error(code,fn):
    with pytest.raises(HTTPException) as caught:fn()
    assert caught.value.status_code==code

def test_editor_submit_cannot_director_approve(foundation_db,people,package):
    db=foundation_db;x=people;p=package
    submit(db,x,p);assert p.state=='director_review'
    error(403,lambda:act(db,x,p,'director_approve','user'))
    assert db.scalar(select(func.count(PackageDecision.id)))==1

def test_director_return_reason_new_editable_revision(foundation_db,people,package):
    db=foundation_db;x=people;p=package;submit(db,x,p);old=service.revision(db,p)
    error(422,lambda:act(db,x,p,'director_return',reason='   '))
    act(db,x,p,'director_return',reason='Kaynak cetvelini düzeltin')
    new=service.revision(db,p)
    assert p.state=='returned' and new.id!=old.id and new.previous_revision_id==old.id
    assert new.content_json==old.content_json
    edit(db,x,p,'user');assert service.revision(db,p).id!=new.id

def test_director_correction_own_approval_exact_hash(foundation_db,people,package):
    db=foundation_db;x=people;p=package;submit(db,x,p);submitted=service.revision(db,p)
    error(403,lambda:edit(db,x,p))
    act(db,x,p,'director_reopen',reason='Müdür kaynak düzeltmesi')
    corrected=edit(db,x,p);submit(db,x,p);act(db,x,p,'director_approve')
    decision=db.scalar(select(PackageDecision).where(PackageDecision.action=='director_approve'))
    assert decision.package_revision_id==corrected.id and decision.snapshot_sha256==corrected.sha256
    assert submitted.content_json!=corrected.content_json
    detail=service.package_detail(db,x['strategy'],p.id)
    change=next(e for e in detail['events'] if e['action']=='field_change')
    assert change['actor']['user_id']==x['director'].id
    assert change['actor']['memberships'][0]['role']=='department_director'
    assert change['changes'][0]['old']!=change['changes'][0]['new'] and change['reason']
    assert p.state=='strategy_review'

def test_strategy_return_requires_director_again(foundation_db,people,package):
    db=foundation_db;x=people;p=package;submit(db,x,p);act(db,x,p,'director_approve')
    old=service.revision(db,p);error(422,lambda:act(db,x,p,'strategy_return','strategy'))
    act(db,x,p,'strategy_return','strategy','Eksik kaynağı tamamlayın')
    assert service.revision(db,p).previous_revision_id==old.id
    edit(db,x,p,'user');error(403,lambda:act(db,x,p,'strategy_approve','strategy'))
    submit(db,x,p);error(403,lambda:act(db,x,p,'strategy_approve','strategy'))
    act(db,x,p,'director_approve');current=service.revision(db,p);act(db,x,p,'strategy_approve','strategy')
    d=db.scalar(select(PackageDecision).where(PackageDecision.action=='strategy_approve'))
    assert p.state=='strategy_approved' and d.package_revision_id==current.id and d.snapshot_sha256==current.sha256
    error(403,lambda:edit(db,x,p,'user'))
    assert db.scalar(select(func.count(ActivityReportApproval.id)))==0

def test_delegate_only_authority_recorded(foundation_db,people,package):
    db=foundation_db;x=people;p=package;g=grant(db,x);submit(db,x,p)
    error(403,lambda:act(db,x,p,'director_approve'))
    error(403,lambda:act(db,x,p,'director_return',reason='İade'))
    act(db,x,p,'director_approve','user')
    d=db.scalar(select(PackageDecision).where(PackageDecision.action=='director_approve'));e=db.get(WorkflowEvent,d.workflow_event_id)
    assert d.delegation_id==g.id and e.actor_user_id==x['user'].id
    assert json.loads(e.context_json)['delegation_id']==g.id

@pytest.mark.parametrize('termination',['expiry','revocation','inactive','removed'])
def test_delegate_termination(foundation_db,people,package,termination):
    db=foundation_db;x=people;p=package;now=auth.server_now(db)
    g=grant(db,x,end=now+timedelta(seconds=1) if termination=='expiry' else None);submit(db,x,p)
    if termination=='expiry':db.execute(text('SELECT pg_sleep(1.1)'))
    elif termination=='revocation':auth.revoke_delegation(db,x['director'],g.id,'İptal');db.commit()
    elif termination=='inactive':x['user'].is_active=False;db.commit()
    else:
        m=auth.active_membership(db,x['user'].id,p.organization_id,p.department_id)
        auth.deactivate_membership(db,x['strategy'],m.id,'Görev sonu');db.commit()
    error(403,lambda:act(db,x,p,'director_approve','user'))
    if termination in {'expiry','revocation'}:act(db,x,p,'director_approve')
    else:error(403,lambda:act(db,x,p,'director_approve'))

def test_stale_hash_revision_state(foundation_db,people,package):
    db=foundation_db;x=people;p=package;r=service.revision(db,p);v=p.version
    error(409,lambda:service.transition(db,x['user'],p.id,'submit_to_director',v,'0'*64))
    submit(db,x,p);error(409,lambda:service.transition(db,x['director'],p.id,'director_approve',v,r.sha256))
    act(db,x,p,'director_approve');error(403,lambda:act(db,x,p,'director_approve'))

def test_private_scope_unknown_permission(foundation_db,people,package):
    db=foundation_db;x=people;p=package
    other=Department(organization_id=p.organization_id,name='Diğer');db.add(other);db.flush()
    outsider=User(email='outsider@test.invalid',full_name='Dış',department_id=other.id,role='department',password_hash='unused');db.add(outsider);db.commit()
    error(403,lambda:service.package_detail(db,outsider,p.id))
    error(403,lambda:service.edit_package(db,outsider,p.id,p.version,service.revision(db,p).sha256,patches(p)))
    error(403,lambda:service.transition(db,x['user'],p.id,'invented',p.version,service.revision(db,p).sha256))
    assert not auth.package_eligibility(db,x['user'],'unknown',p)
    assert not auth.can(db,x['director'],'director_approve',p.organization_id,p.department_id,resource_scope=p.resource_scope,workflow_state='director_review')

@pytest.mark.parametrize('failure',['WorkflowEvent','NotificationRecipient'])
def test_atomic_transition_failure(foundation_db,people,package,failure):
    db=foundation_db;x=people;p=package;version=p.version
    counts={cls:db.scalar(select(func.count(cls.id))) for cls in (WorkflowEvent,PackageDecision,Notification,NotificationRecipient)}
    def break_insert(*args):raise RuntimeError('mandatory failure')
    cls=globals()[failure];event.listen(cls,'before_insert',break_insert)
    try:
        with pytest.raises(RuntimeError):submit(db,x,p)
    finally:event.remove(cls,'before_insert',break_insert)
    db.expire_all();assert db.get(DirectoratePackage,p.id).version==version and p.state=='draft'
    for cls,count in counts.items():assert db.scalar(select(func.count(cls.id)))==count

@pytest.mark.parametrize('table,sql',[('package_revisions','sha256'),('package_decisions','snapshot_sha256')])
@pytest.mark.parametrize('operation',['update','delete'])
def test_history_db_immutable(foundation_db,people,package,table,sql,operation):
    db=foundation_db;x=people;p=package;submit(db,x,p)
    statement=f"UPDATE {table} SET {sql}='tampered'" if operation=='update' else f'DELETE FROM {table}'
    with pytest.raises(DBAPIError):
        with db.begin_nested():db.execute(text(statement))

@pytest.mark.parametrize('race',['approve_return','edit_approve'])
def test_concurrent_only_one_winner(foundation_db,people,package,race):
    db=foundation_db;x=people;p=package
    if race=='approve_return':submit(db,x,p)
    version=p.version;sha=service.revision(db,p).sha256;pid=p.id;director_id=x['director'].id;db.commit()
    engine=db.get_bind()
    def operation(index,barrier):
        with Session(engine,expire_on_commit=False) as session:
            actor=session.get(User,director_id);barrier.wait()
            try:
                if race=='edit_approve' and index==0:service.edit_package(session,actor,pid,version,sha,patches(p),'Kaynak düzeltmesi')
                else:service.transition(session,actor,pid,'director_approve' if index==0 or race=='edit_approve' else 'director_return',version,sha,'İade gerekçesi')
                session.commit();return 'success'
            except HTTPException as exc:session.rollback();return exc.status_code
    results=run_race('test_concurrent_only_one_winner', [lambda b:operation(0,b),lambda b:operation(1,b)])
    if race=='approve_return':assert sorted(results,key=str)==[409,'success']
    else:assert results[0]=='success' and results[1] in {403,409}
    db.expire_all()

def test_actual_zero_evidence_no_live_write(foundation_db,people,package):
    if package.resource_scope!='activity_report':return
    db=foundation_db;x=people;p=package;old=service.revision(db,p)
    error(422,lambda:service.edit_package(db,x['user'],p.id,p.version,old.sha256,
        [{'path':['entries',0,'value'],'value':'0'},{'path':['entries',0,'state'],'value':'verified'},{'path':['entries',0,'evidence'],'value':[]}]))
    valid=[{'path':['entries',0,'value'],'value':'0'},{'path':['entries',0,'state'],'value':'verified'},
        {'path':['entries',0,'evidence'],'value':[{'title':'Defter','locator':'s1','source_revision':'r1'}]}]
    service.edit_package(db,x['user'],p.id,p.version,old.sha256,valid);db.commit()
    data=json.loads(service.revision(db,p).content_json)['entries'][0]
    assert data['value']=='0' and Decimal(data['deviation']['delta'])==Decimal('-1.75')
    assert db.scalar(select(func.count(ActualRevision.id)))==1
    assert db.scalar(select(ActualRevision.value))==Decimal('1.75')
    submit(db,x,p)

def test_binding_fields_director_reason(foundation_db,people,package):
    db=foundation_db;x=people;p=package;r=service.revision(db,p)
    error(422,lambda:service.edit_package(db,x['director'],p.id,p.version,r.sha256,patches(p),''))
    error(422,lambda:service.edit_package(db,x['user'],p.id,p.version,r.sha256,[{'path':['entries' if p.resource_scope=='activity_report' else 'indicators',0,'id'],'value':999}]))

@pytest.mark.parametrize('race',['director_approve','director_return'])
def test_reopen_vs_decision_single_winner(foundation_db,people,package,race):
    db=foundation_db;x=people;p=package;submit(db,x,p)
    version=p.version;sha=service.revision(db,p).sha256;pid=p.id;uid=x['director'].id;db.commit()
    def run(action,barrier):
        with Session(db.get_bind(),expire_on_commit=False) as s:
            actor=s.get(User,uid);barrier.wait()
            try:service.transition(s,actor,pid,action,version,sha,'Kaynak kontrolü');s.commit();return 'ok'
            except HTTPException as exc:s.rollback();return exc.status_code
    results=run_race('test_reopen_vs_decision_single_winner', [lambda b:run('director_reopen',b),lambda b:run(race,b)])
    assert sorted(results,key=str)==[409,'ok']
    db.expire_all()
    if p.state=='returned':
        edit(db,x,p)
        error(409,lambda:service.transition(db,x['director'],pid,'director_approve',version,sha))


def test_duplicate_and_no_director_submission(foundation_db,people,package):
    db=foundation_db;x=people;p=package
    error(409,lambda:service.create_package(db,x['user'],p.organization_id,p.department_id,p.resource_scope,int(p.source_key)))
    director=auth.active_membership(db,x['director'].id,p.organization_id,p.department_id)
    auth.deactivate_membership(db,x['strategy'],director.id,'Görev sonu');db.commit()
    error(403,lambda:submit(db,x,p))


def test_unknown_role_denied_and_config_disabled(foundation_db,people,package):
    db=foundation_db;x=people;p=package;x['user'].role='unknown';db.commit()
    error(403,lambda:service.package_detail(db,x['user'],p.id))
    error(403,lambda:submit(db,x,p))
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            db.add(AuthorizationConfiguration(organization_id=p.organization_id,workflow_enabled=True));db.flush()


def test_raw_decision_hash_mismatch_denied(foundation_db,people,package):
    db=foundation_db;x=people;p=package;submit(db,x,p)
    d=db.scalar(select(PackageDecision));e=db.get(WorkflowEvent,d.workflow_event_id)
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            clone=WorkflowEvent(actor_user_id=e.actor_user_id,actor_snapshot_json=e.actor_snapshot_json,
                organization_id=e.organization_id,department_id=e.department_id,event_type=e.event_type,
                resource_type=e.resource_type,resource_id=e.resource_id,context_json=e.context_json,reason=e.reason,
                source=e.source,correlation_id='other')
            db.add(clone);db.flush()
            db.add(PackageDecision(package_revision_id=d.package_revision_id,snapshot_sha256='0'*64,
                action=d.action,from_state=d.from_state,to_state=d.to_state,workflow_event_id=clone.id));db.flush()


@pytest.mark.parametrize('foundation_db',['0429caba7123'],indirect=True)
def test_phase3_additive_upgrade_preserves_phase2_history(foundation_db,people):
    import os,subprocess,sys
    from tests.test_authorization_foundation import ROOT
    db=foundation_db;x=people;established(db,x);delegation=grant(db,x)
    from sqlalchemy import inspect
    assert 'authority_kind' not in {c['name'] for c in inspect(db.connection()).get_columns('authority_delegations')}
    assert 'authority_kind' in inspect(delegation).unloaded
    auth.assign_final_authority(db,x['strategy'],x['department'].organization_id,x['director'].id,'Nihai görevlendirme');db.commit()
    tables=('directorate_memberships','membership_events','authority_delegations','delegation_events','final_authority_assignments','final_authority_events')
    before={t:[dict(r) for r in db.execute(text(f'SELECT * FROM {t} ORDER BY id')).mappings()] for t in tables};db.commit()
    # Compare every field and row, including the sole expected additive default;
    # no historical column is dropped from the equality assertion.
    expected = dict(before, authority_delegations=[dict(row, authority_kind='director_approval') for row in before['authority_delegations']])
    for _ in range(2):
        done=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,
            env={**os.environ,'DATABASE_URL':db.get_bind().url.render_as_string(hide_password=False)},capture_output=True,text=True, timeout=180)
        assert done.returncode==0,done.stderr
    for t,rows in expected.items():assert [dict(r) for r in db.execute(text(f'SELECT * FROM {t} ORDER BY id')).mappings()]==rows
    assert db.scalar(select(AuthorityDelegation.authority_kind)) == 'director_approval'
    for cls in (DirectoratePackage,PackageRevision,PackageDecision):assert db.scalar(select(func.count(cls.id)))==0


def test_delegation_expires_after_initial_check(foundation_db,people,package,monkeypatch):
    db=foundation_db;x=people;p=package;now=auth.server_now(db)
    grant(db,x,end=now+timedelta(seconds=1));submit(db,x,p)
    initial=service.locked
    def delayed(*args,**kwargs):
        result=initial(*args,**kwargs);db.execute(text('SELECT pg_sleep(1.1)'));return result
    monkeypatch.setattr(service,'locked',delayed)
    error(403,lambda:act(db,x,p,'director_approve','user'))
    assert p.state=='director_review'
    assert not db.scalar(select(PackageDecision.id).where(PackageDecision.action=='director_approve'))


def test_package_edit_failure_rolls_back_revision_and_fields(foundation_db,people,package):
    db=foundation_db;x=people;p=package;before=service.revision(db,p);version=p.version
    count=db.scalar(select(func.count(PackageRevision.id)))
    def fail(*args):raise RuntimeError('mandatory field history failure')
    event.listen(FieldChangeEvent,'before_insert',fail)
    try:
        with pytest.raises(RuntimeError):edit(db,x,p)
    finally:event.remove(FieldChangeEvent,'before_insert',fail)
    db.expire_all()
    assert p.version==version and service.revision(db,p).id==before.id
    assert db.scalar(select(func.count(PackageRevision.id)))==count


def test_decision_ignores_mutable_live_rows(foundation_db,people,package):
    db=foundation_db;x=people;p=package;submitted=service.revision(db,p);submit(db,x,p)
    value=db.scalar(select(IndicatorValue));value.value=Decimal('999');db.commit()
    act(db,x,p,'director_approve')
    decision=db.scalar(select(PackageDecision).where(PackageDecision.action=='director_approve'))
    assert decision.snapshot_sha256==submitted.sha256
    assert service.revision(db,p).content_json==submitted.content_json


def test_blank_zero_exact_decimal(foundation_db,people,package):
    db=foundation_db;x=people;p=package
    if p.resource_scope=='performance_program':
        edits=[{'path':['indicators',0,'values',0,'value'],'value':''},{'path':['indicators',0,'values',0,'state'],'value':'missing'}]
    else:
        edits=[{'path':['entries',0,'value'],'value':''},{'path':['entries',0,'state'],'value':'missing'}]
    service.edit_package(db,x['user'],p.id,p.version,service.revision(db,p).sha256,edits);db.commit()
    raw=json.loads(service.revision(db,p).content_json)
    data=raw['entries'][0] if p.resource_scope=='activity_report' else raw['indicators'][0]['values'][0]
    assert data['value'] in {None,''} and data['state']=='missing'
    edit(db,x,p,'user','0')
    raw=json.loads(service.revision(db,p).content_json)
    data=raw['entries'][0] if p.resource_scope=='activity_report' else raw['indicators'][0]['values'][0]
    assert data['value']=='0' and data['state']!='missing'
