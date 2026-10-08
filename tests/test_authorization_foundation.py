"""Real migrated PostgreSQL tests for disabled authorization and atomic audit."""
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Barrier
from uuid import uuid4
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select, text, event, func
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema
from app.models import *
from app import authorization_service as auth
from tests.conftest import sample as sample_fixture

ROOT=Path(__file__).resolve().parents[1]
pytestmark=pytest.mark.postgres


@pytest.fixture
def foundation_db(request):
    url=os.environ.get('CIVENSA_TEST_POSTGRES_URL')
    if not url:pytest.fail('Authorization foundation requires disposable PostgreSQL')
    admin=create_engine(url);schema='auth_'+uuid4().hex
    with admin.begin() as c:c.execute(CreateSchema(schema))
    scoped=make_url(url).update_query_dict({'options':'-csearch_path='+schema}).render_as_string(hide_password=False)
    result=subprocess.run([sys.executable,'-m','alembic','upgrade',getattr(request,'param','head')],cwd=ROOT,
        env={**os.environ,'DATABASE_URL':scoped},capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    engine=create_engine(scoped)
    try:
        with Session(engine,expire_on_commit=False) as db:yield db
    finally:
        engine.dispose()
        with admin.begin() as c:c.execute(DropSchema(schema,cascade=True))
        admin.dispose()


@pytest.fixture
def people(foundation_db):
    db=foundation_db;x=sample_fixture.__wrapped__(db)
    for key in ('director','editor2','editor3'):
        x[key]=User(email=key+'@example.invalid',full_name=key,role='department',department_id=x['department'].id,password_hash='unused')
        db.add(x[key])
    db.commit()
    return x


def member(db,x,key,role,slot):
    row=auth.assign_membership(db,x['strategy'],x['department'].organization_id,x['department'].id,x[key].id,role,slot,'Resmî atama / 2026-1')
    db.commit();return row


def established(db,x):
    editor=member(db,x,'user','department_editor',1)
    director=member(db,x,'director','department_director',3)
    return editor,director


def eligible(db,x,key,action='director_approve',**kw):
    return auth.eligibility(db,x[key],action,x['department'].organization_id,x['department'].id,
        resource_scope='performance_program',workflow_state='director_review',**kw)


def grant(db,x,start=None,end=None):
    now=auth.server_now(db)
    row=auth.create_delegation(db,x['director'],x['department'].organization_id,x['department'].id,x['user'].id,
        start or now-timedelta(minutes=1),end or now+timedelta(hours=1),'Vekâlet yazısı 2026-1')
    db.commit();return row


def change(db,x,key='director',source='manual',**kw):
    value=db.scalar(select(IndicatorValue))
    def mutate():value.value=Decimal('2.50');db.flush();return value
    return auth.atomic_change(db,x[key],x['department'].organization_id,x['department'].id,'indicator',x['indicator'].id,
        {'period_id':x['period'].id,'revision':1},[{'field_key':'target.2027','field_type':'decimal','old':Decimal('1.75'),'new':Decimal('2.50')}],
        mutate,source=source,reason='Kaynak cetveline göre düzeltme',recipients=(x['director'].id,),**kw)


def test_slots_and_unique_people(foundation_db,people):
    db=foundation_db;x=people;established(db,x);member(db,x,'editor2','department_editor',2)
    for key,role,slot in [('editor3','department_editor',2),('editor3','department_director',3),('user','department_director',3)]:
        with pytest.raises(IntegrityError):
            with db.begin_nested():auth.assign_membership(db,x['strategy'],1,1,x[key].id,role,slot,'Atama')
    assert db.scalar(select(func.count()).select_from(DirectorateMembership).where(DirectorateMembership.active))==3
    with pytest.raises(HTTPException,match='slotu'):
        auth.assign_membership(db,x['strategy'],1,1,x['editor3'].id,'department_editor',4,'Atama')


def test_concurrent_fourth_person_cannot_enter(foundation_db,people):
    db=foundation_db;x=people;established(db,x);barrier=Barrier(2)
    def enter(uid):
        with Session(db.get_bind()) as other:
            barrier.wait(timeout=5)
            try:
                auth.assign_membership(other,x['strategy'],1,1,uid,'department_editor',2,'Atama');other.commit();return True
            except IntegrityError:other.rollback();return False
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(enter,[x['editor2'].id,x['editor3'].id]))
    assert sorted(results)==[False,True]
    assert db.scalar(select(func.count()).select_from(DirectorateMembership).where(DirectorateMembership.active))==3


def test_disabled_legacy_adapter_and_unknown_denial(foundation_db,people):
    db=foundation_db;x=people;org=x['department'].organization_id
    assert auth.can(db,x['user'],'legacy_edit_draft',org,1,resource_scope='performance_program')
    assert not auth.can(db,x['user'],'legacy_edit_draft',org,1,resource_scope='performance_program',revision_locked=True)
    assert not auth.can(db,x['strategy'],'final_approve',org,resource_scope='final_candidate')
    assert not auth.can(db,x['user'],'unknown',org,1,resource_scope='performance_program')
    established(db,x)
    assert eligible(db,x,'director')
    assert not auth.can(db,x['director'],'director_approve',org,1,resource_scope='performance_program')
    db.add(AuthorizationConfiguration(organization_id=org,workflow_enabled=True))
    with pytest.raises(IntegrityError):db.commit()
    db.rollback()


def test_no_director_blocks_submission_preview(foundation_db,people):
    db=foundation_db;x=people;member(db,x,'user','department_editor',1)
    assert not auth.eligibility(db,x['user'],'submit_to_director',1,1,resource_scope='performance_program')
    member(db,x,'director','department_director',3)
    assert auth.eligibility(db,x['user'],'submit_to_director',1,1,resource_scope='performance_program')


def test_scope_and_inactive_fail_closed(foundation_db,people):
    db=foundation_db;x=people;established(db,x)
    assert not auth.eligibility(db,x['director'],'director_approve',2,1,resource_scope='performance_program',workflow_state='director_review')
    assert not auth.eligibility(db,x['director'],'director_approve',1,999,resource_scope='performance_program',workflow_state='director_review')
    assert not eligible(db,x,'director',revision_locked=True)
    assert not auth.eligibility(db,x['director'],'edit_draft',1,1,resource_scope='performance_program',workflow_state='unknown')
    x['director'].is_active=False;db.commit()
    assert not eligible(db,x,'director')


def test_director_contribution_preserved_without_self_approval_ban(foundation_db,people):
    db=foundation_db;x=people;established(db,x);_,wf=change(db,x);db.commit()
    field=db.scalar(select(FieldChangeEvent));snapshot=json.loads(wf.actor_snapshot_json)
    assert wf.actor_user_id==x['director'].id and snapshot['memberships'][0]['role']=='department_director'
    assert json.loads(field.previous_json)=='1.75' and json.loads(field.new_json)=='2.50'
    assert wf.created_at.tzinfo is not None and wf.reason
    assert eligible(db,x,'director')  # Contribution does not revoke approval eligibility.
    x['director'].full_name='Renamed';db.commit()
    assert json.loads(wf.actor_snapshot_json)['name']=='director'


@pytest.mark.parametrize('timing',['scheduled','active','expired'])
def test_delegation_server_time_boundaries(foundation_db,people,timing):
    db=foundation_db;x=people;established(db,x);now=auth.server_now(db)
    if timing=='scheduled':row=grant(db,x,now+timedelta(hours=1),now+timedelta(hours=2))
    elif timing=='active':row=grant(db,x)
    else:
        row=grant(db,x,now-timedelta(minutes=1),now+timedelta(milliseconds=300))
        # Database wait; permission clock remains DB time, never a supplied test/client timestamp.
        db.execute(text('SELECT pg_sleep(0.4)'))
    assert eligible(db,x,'user')==(timing=='active')
    assert eligible(db,x,'director')==(timing!='active')


def test_delegate_cannot_redelegate_and_revoke_restores_primary(foundation_db,people):
    db=foundation_db;x=people;established(db,x);row=grant(db,x)
    with pytest.raises(HTTPException):auth.create_delegation(db,x['user'],1,1,x['editor2'].id,auth.server_now(db),auth.server_now(db)+timedelta(hours=1),'Yazı')
    assert not eligible(db,x,'director') and eligible(db,x,'user')
    auth.revoke_delegation(db,x['director'],row.id,'Göreve dönüş');db.commit()
    assert eligible(db,x,'director') and not eligible(db,x,'user')
    assert db.scalar(select(DelegationRevocation)).reason=='Göreve dönüş'
    assert len(db.scalars(select(DelegationEvent)).all())==2
    grant(db,x)  # Revoked reservation no longer blocks replacement; old interval retained.


def test_removed_delegate_does_not_revive_original(foundation_db,people):
    db=foundation_db;x=people;established(db,x);grant(db,x)
    auth.deactivate_membership(db,x['strategy'],db.scalar(select(DirectorateMembership).where(DirectorateMembership.user_id==x['user'].id)).id,'Ayrıldı');db.commit()
    assert not eligible(db,x,'user') and not eligible(db,x,'director')


def test_overlap_exclusion_even_concurrent_repeatable_read(foundation_db,people):
    db=foundation_db;x=people;editor,director=established(db,x);now=auth.server_now(db);db.commit();barrier=Barrier(2)
    def insert(_):
        with db.get_bind().connect().execution_options(isolation_level='REPEATABLE READ') as conn:
            with Session(bind=conn) as other:
                other.execute(text('SELECT 1 FROM departments WHERE id=1'));barrier.wait(timeout=5)
                try:
                    other.add(AuthorityDelegation(organization_id=1,department_id=1,director_membership_id=director.id,
                        delegate_membership_id=editor.id,start_at=now+timedelta(hours=1),end_at=now+timedelta(hours=2),formal_basis='Yazı',created_by=x['director'].id))
                    other.commit();return True
                except DBAPIError:other.rollback();return False
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(insert,[1,2]))
    assert sorted(results)==[False,True]


def test_final_authority_explicit_and_change_requires_new_approval(foundation_db,people):
    db=foundation_db;x=people
    args=dict(resource_scope='final_candidate',workflow_state='final_review')
    assert not auth.eligibility(db,x['strategy'],'final_approve',1,**args)
    with pytest.raises(HTTPException):auth.assign_final_authority(db,x['strategy'],1,x['director'].id,' ')
    first=auth.assign_final_authority(db,x['strategy'],1,x['director'].id,'Başkan yetki yazısı A');db.commit()
    assert auth.eligibility(db,x['director'],'final_approve',1,**args)
    second=auth.assign_final_authority(db,x['strategy'],1,x['editor2'].id,'Yeni atama B');db.commit()
    assert not auth.eligibility(db,x['director'],'final_approve',1,**args)
    assert auth.eligibility(db,x['editor2'],'final_approve',1,**args)
    kwargs=dict(resource_scope='final_candidate',workflow_state='final_approved')
    assert not auth.eligibility(db,x['strategy'],'publish_final',1,approved_assignment_id=first.id,**kwargs)
    assert auth.eligibility(db,x['strategy'],'publish_final',1,approved_assignment_id=second.id,**kwargs)
    assert db.scalar(select(func.count()).select_from(FinalAuthorityEvent))==3


@pytest.mark.parametrize('table',['membership_events','authority_delegations','delegation_events','delegation_revocations','final_authority_events','workflow_events','field_change_events'])
@pytest.mark.parametrize('operation',['UPDATE','DELETE'])
def test_raw_sql_immutable_history(foundation_db,people,table,operation):
    db=foundation_db;x=people;established(db,x);row=grant(db,x);auth.revoke_delegation(db,x['director'],row.id,'İptal')
    auth.assign_final_authority(db,x['strategy'],1,x['director'].id,'Nihai yetki yazısı');change(db,x);db.commit()
    statement=f'UPDATE {table} SET id=id' if operation=='UPDATE' else f'DELETE FROM {table}'
    with pytest.raises(DBAPIError,match='değiştirilemez'):
        with db.begin_nested():db.execute(text(statement))
    assert db.scalar(text(f'SELECT count(*) FROM {table}'))>0


@pytest.mark.parametrize('model',[FieldChangeEvent,NotificationRecipient])
def test_required_audit_or_notification_failure_rolls_back_business(foundation_db,people,model):
    db=foundation_db;x=people;established(db,x)
    def fail_insert(*args):raise RuntimeError('mandatory failure')
    event.listen(model,'before_insert',fail_insert)
    try:
        with pytest.raises(RuntimeError,match='mandatory failure'):change(db,x)
    finally:event.remove(model,'before_insert',fail_insert)
    db.expire_all()
    assert db.scalar(select(IndicatorValue)).value==Decimal('1.75')
    assert db.scalar(select(func.count()).select_from(WorkflowEvent))==0
    assert db.scalar(select(func.count()).select_from(Notification))==0
    assert db.scalar(select(func.count()).select_from(NotificationRecipient))==0


def test_ex_officio_reason_and_director_notification(foundation_db,people):
    db=foundation_db;x=people;established(db,x)
    _,wf=change(db,x,'strategy','ex_officio');db.commit()
    assert wf.source=='ex_officio' and wf.reason
    receipt=db.scalar(select(NotificationRecipient));assert receipt.user_id==x['director'].id
    assert db.get(Notification,receipt.notification_id).delivery_mode=='recipients'


def test_no_ex_officio_without_reason_or_director(foundation_db,people):
    db=foundation_db;x=people
    def attempt(reason):
        return auth.atomic_change(db,x['strategy'],1,1,'indicator',1,{'revision':1},
            [{'field_key':'name','field_type':'text','old':'a','new':'b'}],lambda:None,source='ex_officio',reason=reason,recipients=(x['user'].id,))
    with pytest.raises(HTTPException):attempt('')
    with pytest.raises(HTTPException):attempt('Resen düzeltme')
    assert db.scalar(select(func.count()).select_from(WorkflowEvent))==0


def test_per_recipient_read_state_and_visibility(foundation_db,people):
    from app.main import notifications_api, notification_read
    db=foundation_db;x=people
    notice=Notification(role='department',department_id=1,event_type='test',message='Birim bildirimi');db.add(notice);db.commit()
    assert notifications_api(db,x['user'])['unread']==1
    notification_read(notice.id,db,x['user'])
    assert notifications_api(db,x['user'])['unread']==0
    assert notifications_api(db,x['editor2'])['unread']==1
    db.refresh(notice);assert not notice.is_read
    notification_read(notice.id,db,x['user'])
    assert db.scalar(select(func.count()).select_from(NotificationRecipient))==1
    established(db,x);change(db,x);db.commit()
    assert len(notifications_api(db,x['director'])['items'])==2
    assert len(notifications_api(db,x['user'])['items'])==1
    other=Department(organization_id=1,name='Diğer');db.add(other);db.flush();x['editor3'].department_id=other.id;db.commit()
    with pytest.raises(HTTPException):notification_read(notice.id,db,x['editor3'])


def test_database_timestamp_and_no_float_coercion(foundation_db,people):
    db=foundation_db;x=people;established(db,x)
    with pytest.raises(ValueError):auth.encode({'value':1.75})
    membership=db.scalar(select(DirectorateMembership))
    row=MembershipEvent(membership_id=membership.id,actor_user_id=x['strategy'].id,actor_snapshot_json='{}',event_type='test',
        previous_json='null',new_json='{}',reason='test',created_at=datetime(2000,1,1,tzinfo=UTC))
    db.add(row);db.commit();db.refresh(row)
    assert row.created_at.year==auth.server_now(db).year


def test_one_person_cannot_hold_editor_and_director_slots(foundation_db,people):
    db=foundation_db;x=people;member(db,x,'user','department_editor',1)
    with pytest.raises(IntegrityError,match='uq_active_directorate_person'):
        with db.begin_nested():auth.assign_membership(db,x['strategy'],1,1,x['user'].id,'department_director',3,'Atama')


def test_unknown_legacy_role_and_missing_resource_deny(foundation_db,people):
    db=foundation_db;x=people;x['user'].role='unknown';db.commit()
    assert not auth.can(db,x['user'],'legacy_edit_draft',1,1,resource_scope='performance_program')
    x['user'].role='department';db.commit()
    assert not auth.can(db,x['user'],'legacy_edit_draft',1,1)


def test_concurrent_notification_reads_are_idempotent(foundation_db,people):
    from app.main import notification_read
    db=foundation_db;x=people
    notice=Notification(role='department',department_id=1,event_type='test',message='Test');db.add(notice);db.commit()
    barrier=Barrier(2)
    def read(_):
        with Session(db.get_bind()) as other:
            barrier.wait(timeout=5);return notification_read(notice.id,other,x['user'])
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(read,[1,2]))
    assert all(r['ok'] for r in results)
    assert db.scalar(select(func.count()).select_from(NotificationRecipient))==1


def test_historical_shared_read_flag_not_fabricated_per_user(foundation_db,people):
    from app.main import notifications_api
    db=foundation_db;x=people
    notice=Notification(role='department',department_id=1,event_type='old',message='Old',is_read=True);db.add(notice);db.commit()
    assert not notifications_api(db,x['user'])['items'][0]['is_read']
    assert not notifications_api(db,x['editor2'])['items'][0]['is_read']
    db.refresh(notice);assert notice.is_read


def test_invalid_delegation_party_and_interval(foundation_db,people):
    db=foundation_db;x=people;established(db,x);now=auth.server_now(db)
    for uid,start,end,basis in [(x['editor3'].id,now,now+timedelta(hours=1),'Yazı'),
            (x['user'].id,now,now,'Yazı'),(x['user'].id,now.replace(tzinfo=None),now+timedelta(hours=1),'Yazı'),
            (x['user'].id,now,now+timedelta(hours=1),' ')]:
        with pytest.raises(HTTPException):auth.create_delegation(db,x['director'],1,1,uid,start,end,basis)
    assert db.scalar(select(func.count()).select_from(AuthorityDelegation))==0


def test_membership_org_scope_enforced_in_raw_sql(foundation_db,people):
    db=foundation_db;x=people
    org=Organization(name='Other');db.add(org);db.commit()
    with pytest.raises(DBAPIError,match='ilişkisi geçersiz'):
        with db.begin_nested():db.add(DirectorateMembership(organization_id=org.id,department_id=1,user_id=x['user'].id,
            role_code='department_editor',slot=1,formal_basis='Atama',created_by=x['strategy'].id));db.flush()


@pytest.mark.parametrize('foundation_db',['a7c2d3e4f5a6'],indirect=True)
def test_additive_upgrade_preserves_history_and_does_not_invent_assignments(foundation_db,people):
    from app import activity_contract_service as contract
    db=foundation_db;x=people
    # Persist real v3 definition/publication/report/actual history before this migration.
    payload,defs=contract.freeze_program_payload(db,1,x['strategy']);raw=contract.canonical(payload)
    pub=Publication(period_id=1,version=1,snapshot_json=raw,sha256=contract.digest(raw),created_by=x['strategy'].id)
    db.add(pub);db.flush();contract.attach_publication_definitions(db,pub,defs,x['strategy']);db.commit()
    revision=contract.create_report_revision(db,x['strategy'],organization_id=1,publication_id=pub.id,report_id=None,expected_revision=0)
    db.commit();slot=db.scalar(select(ReportIndicator)).id
    contract.save_actual(db,x['user'],slot,0,'1.75','verified',
        [{'title':'Defter','locator':'Sayfa 1','source_revision':'r1'}],'Kaynak kontrolü',{})
    db.commit();contract.approve_report(db,x['strategy'],revision.id);db.commit()
    tables=('publications','indicator_definition_revisions','publication_indicator_bindings','activity_report_revisions','actual_revisions','activity_report_approvals','users','submission_events')
    before={t:db.execute(text(f'SELECT * FROM {t} ORDER BY id')).mappings().all() for t in tables}
    before={t:[dict(r) for r in rows] for t,rows in before.items()};db.commit()
    url=db.get_bind().url.render_as_string(hide_password=False)
    for _ in range(2):
        result=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,
            env={**os.environ,'DATABASE_URL':url},capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    for t in tables:assert [dict(r) for r in db.execute(text(f'SELECT * FROM {t} ORDER BY id')).mappings()]==before[t]
    for t in ('directorate_memberships','final_authority_assignments','authority_delegations','workflow_events','field_change_events'):
        assert db.scalar(text(f'SELECT count(*) FROM {t}'))==0
    for sql in ("UPDATE actual_revisions SET value=0",'DELETE FROM activity_report_approvals'):
        with pytest.raises(DBAPIError,match='değiştirilemez'):
            with db.begin_nested():db.execute(text(sql))
    with pytest.raises(DBAPIError,match='Onaylı'):
        with db.begin_nested():db.execute(text("INSERT INTO actual_revisions (report_indicator_id,revision,value,raw_text,state,evidence_json,explanation,deviation_json,created_by,created_at) VALUES (:slot,2,1.75,'1.75','verified','[]','','{}',:uid,CURRENT_TIMESTAMP)"),{'slot':slot,'uid':x['user'].id})


@pytest.mark.parametrize('table,field',['directorate_memberships,formal_basis'.split(','),'final_authority_assignments,user_id'.split(',')])
def test_assignment_identity_cannot_be_reinterpreted(foundation_db,people,table,field):
    db=foundation_db;x=people;established(db,x);auth.assign_final_authority(db,x['strategy'],1,x['director'].id,'Atama');db.commit()
    expression="'Changed'" if field=='formal_basis' else str(x['editor2'].id)
    with pytest.raises(DBAPIError,match='değiştirilemez'):
        with db.begin_nested():db.execute(text(f'UPDATE {table} SET {field}={expression}'))


def test_orm_immutable_history_rejected(foundation_db,people):
    db=foundation_db;x=people;established(db,x);row=db.scalar(select(MembershipEvent))
    with pytest.raises(ValueError,match='değiştirilemez'):
        with db.begin_nested():row.reason='Changed';db.flush()
    with pytest.raises(ValueError,match='değiştirilemez'):
        with db.begin_nested():db.delete(row);db.flush()


def test_new_workflow_has_no_casual_strategy_assignment_api(client):
    response=client.post('/api/authorization/final-authority',json={'user_id':1,'formal_basis':'self'})
    assert response.status_code==404
