"""CIV-027 acceptance through real sessions/CSRF and migrated PostgreSQL."""
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.models import (Activity, ActivityCatalogueLink, ActivityResponsibility, AuditLog,
    Department, DepartmentScope, Indicator, OfficialActivity, ReportingPeriod,
    StructureChange, StructureChangeCancellation, StructureChangeLink,
    StructureChangeTransfer, Submission, User)
from app.program_service import book_snapshot, department_snapshot, period_departments
from tests.test_authorization_foundation import foundation_db
from tests.test_live_pilot_hardening import live_client, login

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[1]


def strategy(live_client, sample):
    browser = live_client()
    return browser, login(browser, sample['strategy'].email)


def payload(sample, **extra):
    return dict(organization_id=sample['department'].organization_id,
        period_id=sample['period'].id, change_type='RENAMED',
        effective_date='2028-01-01', council_decision_no='2027/48',
        council_decision_date='2027-12-15', from_department_ids=[sample['department'].id],
        new_name='Yeni Hizmetler Müdürlüğü', **extra)


def save(browser, token, data):
    return browser.post('/structure/changes', data={'csrf_token': token, **data})


def test_rename_preserves_old_period_and_new_period_book_and_screens(db, sample, live_client):
    old_name = sample['department'].name
    next_period = ReportingPeriod(year=2028); db.add(next_period); db.commit()
    browser, token = strategy(live_client, sample)
    assert save(browser, token, payload(sample)).status_code == 303
    db.expire_all()
    assert sample['department'].name == 'Yeni Hizmetler Müdürlüğü'
    assert department_snapshot(db,sample['period'].id,sample['department'].id)['department'] == old_name
    assert department_snapshot(db,next_period.id,sample['department'].id)['department'] == 'Yeni Hizmetler Müdürlüğü'
    assert old_name in browser.get('/activity-report?year=2027').text
    assert old_name in browser.get(f'/program/{sample["department"].id}?period_id={sample["period"].id}').text
    assert old_name in browser.get(f'/department/{sample["department"].id}').text
    assert db.scalar(select(StructureChangeLink)).from_department_id == sample['department'].id
    # UI never interpolates free text into HTML/JS.
    assert 'structure-wizard' in browser.get('/structure').text


def split_data(sample, **extra):
    data = payload(sample)
    data.update(change_type='SPLIT', new_name='', new_names='Park İşleri Müdürlüğü\nBahçe İşleri Müdürlüğü', **extra)
    return data


def test_closed_work_split_copy_routes_every_kind_drafts_and_lists_untransferred(db, sample, live_client):
    omitted = Activity(period_id=sample['period'].id, department_id=sample['department'].id,
        subprogram_id=sample['subprogram'].id, name='Devri kararlaştırılmayan iş')
    db.add(omitted); db.commit()
    browser, token = strategy(live_client, sample)
    data = split_data(sample, effective_date='2027-07-01', council_decision_date='2027-06-20')
    data.update({f'transfer_activity_{sample["activity"].id}_{sample["department"].id}': 'new:0',
        f'transfer_indicator_{sample["indicator"].id}_{sample["department"].id}': 'new:1',
        f'transfer_official_{sample["official"].id}_{sample["department"].id}': 'new:0', 'transfer_note': 'Meclis görev dağılımı'})
    response = save(browser,token,data)
    assert response.status_code == 303, response.text
    receivers = {d.name:d.id for d in db.scalars(select(Department))}
    assert 'Devri kararlaştırılmayan iş' in browser.get('/structure').text
    assert sample['user'].email in browser.get('/structure').text
    before_accounts = [(u.id,u.is_active,u.department_id) for u in db.scalars(select(User).order_by(User.id))]
    response = browser.post('/api/periods',headers={'X-CSRF-Token':token},json={'year':2028,'base_period_id':sample['period'].id})
    assert response.status_code == 200, response.text
    pid = response.json()['id']
    assert any(row['id'] == omitted.id and row['kind'] == 'activity' for row in response.json()['untransferred'])
    assert [(u.id,u.is_active,u.department_id) for u in db.scalars(select(User).order_by(User.id))] == before_accounts
    copied_a = db.scalar(select(Activity).where(Activity.period_id == pid))
    copied_i = db.scalar(select(Indicator).where(Indicator.period_id == pid))
    copied_o = db.scalar(select(OfficialActivity).where(OfficialActivity.period_id == pid))
    assert copied_a.name == sample['activity'].name and copied_a.department_id == receivers['Park İşleri Müdürlüğü']
    assert copied_i.department_id == receivers['Bahçe İşleri Müdürlüğü'] and copied_i.status == 'draft'
    assert copied_i.persistent_indicator_id == sample['indicator'].persistent_indicator_id
    assert not copied_i.values and not copied_a.cost_values  # No actuals/budgets fabricated.
    assert db.scalar(select(ActivityResponsibility.department_id).where(ActivityResponsibility.official_activity_id == copied_o.id)) == copied_a.department_id
    assert db.scalar(select(ActivityCatalogueLink).where(ActivityCatalogueLink.activity_id == copied_a.id))
    assert all(s.status == 'draft' for s in db.scalars(select(Submission).where(Submission.period_id == pid)))
    assert not db.scalar(select(Activity.id).where(Activity.period_id == pid,Activity.name == omitted.name))
    assert sample['department'].id not in {d.id for d in period_departments(db,pid)}
    assert sample['department'].id in {d.id for d in period_departments(db,sample['period'].id)}
    assert all(d['department_id'] != sample['department'].id for d in book_snapshot(db,pid)['departments'])
    assert sample['activity'].department_id == sample['department'].id
    assert db.scalar(select(func.count(StructureChangeTransfer.id))) == 3
    logs = db.scalars(select(AuditLog).where(AuditLog.action.in_(['structure_change','structure_link','structure_transfer','structure_profile','structure_period_copy']))).all()
    assert {'structure_change','structure_link','structure_transfer','structure_profile','structure_period_copy'} <= {l.action for l in logs}
    assert all(l.user_id == sample['strategy'].id and l.created_at and set(json.loads(l.details)) == {'old','new'} for l in logs)
    assert db.scalar(select(AuditLog).where(AuditLog.action=='pp_data_change',AuditLog.entity_id==copied_i.department_id,AuditLog.details==f'period_id={pid}'))
    assert browser.post(f'/structure/changes/{db.scalar(select(StructureChange.id))}/cancel?period_id=1', data={'csrf_token':token,'note':'Yanlış karar'}).status_code == 303
    db.expire_all()
    assert copied_a.department_id == receivers['Park İşleri Müdürlüğü']
    assert copied_i.department_id == receivers['Bahçe İşleri Müdürlüğü']
    assert 'İptal bu taslakların sahipliğini değiştirmez' in browser.get('/structure').text
    cancel_log = db.scalar(select(AuditLog).where(AuditLog.action=='structure_cancel'))
    assert json.loads(cancel_log.details)['new']['copied_periods_preserved'] == [pid]


def test_in_year_closure_keeps_ar_scope_note_and_department_authorization(db, sample, live_client):
    browser, token = strategy(live_client,sample)
    data = split_data(sample, effective_date='2027-07-01', council_decision_date='2027-06-20')
    assert save(browser,token,data).status_code == 303
    scope = db.scalar(select(DepartmentScope).where(DepartmentScope.department_id==sample['department'].id,DepartmentScope.period_id==sample['period'].id))
    assert scope.status == 'required' and scope.active_to == date(2027,7,1)
    assert sample['department'].id in {d.id for d in period_departments(db,sample['period'].id)}
    response = browser.get('/activity-report?year=2027')
    assert '01.07.2027 tarihinde kapandı/birleşti' in response.text
    assert 'Park İşleri Müdürlüğü' in response.text and 'Bahçe İşleri Müdürlüğü' in response.text
    assert 'Meclis kararı 2027/48' in response.text and 'Hizmet sayısı' in response.text
    user_browser = live_client(); login(user_browser,sample['user'].email)
    assert '01.07.2027 tarihinde kapandı/birleşti' in user_browser.get('/activity-report?year=2027').text
    assert user_browser.get('/structure').status_code == 403


def test_cancellation_is_append_only_and_restores_profiles_with_audit(db,sample,live_client):
    browser,token = strategy(live_client,sample)
    old_name = sample['department'].name
    assert save(browser,token,payload(sample)).status_code == 303
    change = db.scalar(select(StructureChange)); original = change.snapshot_json
    response = browser.post(f'/structure/changes/{change.id}/cancel?period_id=1',data={'csrf_token':token,'note':'Meclis kararındaki ad düzeltildi'})
    assert response.status_code == 303,response.text
    db.expire_all()
    assert sample['department'].name == old_name and change.snapshot_json == original
    assert db.scalar(select(StructureChangeCancellation)).note == 'Meclis kararındaki ad düzeltildi'
    assert db.scalar(select(func.count(StructureChange.id))) == 1
    assert db.scalar(select(func.count(StructureChangeLink.id))) == 1
    assert db.scalar(select(AuditLog).where(AuditLog.action=='structure_cancel')).user_id == sample['strategy'].id
    assert browser.delete(f'/structure/changes/{change.id}',headers={'X-CSRF-Token':token}).status_code in {404,405}
    db.delete(change)
    with pytest.raises(HTTPException): db.flush()
    db.rollback()


def test_cancellation_refuses_overwriting_later_profile_edits(db,sample,live_client):
    browser,token = strategy(live_client,sample)
    data=payload(sample); data.update(effective_date='2027-01-01',council_decision_date='2026-12-01')
    assert save(browser,token,data).status_code == 303
    scope=db.scalar(select(DepartmentScope)); scope.budget_code='Sonraki düzeltme'; db.commit()
    cid=db.scalar(select(StructureChange.id))
    result=browser.post(f'/structure/changes/{cid}/cancel?period_id=1',data={'csrf_token':token,'note':'Düzeltme'})
    assert result.status_code == 409 and 'sonrasında değişmiş' in result.text
    db.expire_all(); assert scope.budget_code == 'Sonraki düzeltme'
    assert not db.scalar(select(StructureChangeCancellation.id))


def test_merged_departments_and_created_directorate_appear_only_in_correct_year(db,sample,live_client):
    second=Department(organization_id=sample['department'].organization_id,name='İkinci Müdürlük'); db.add(second);db.commit()
    browser,token = strategy(live_client,sample)
    data=payload(sample);data.update(change_type='MERGED',from_department_ids=[sample['department'].id,second.id],new_names='Birleşik Müdürlük',new_name='')
    assert save(browser,token,data).status_code == 303
    merged=db.scalar(select(Department).where(Department.name=='Birleşik Müdürlük'))
    assert merged.id not in {d.id for d in period_departments(db,sample['period'].id)}
    data=payload(sample);data.update(change_type='CREATED',from_department_ids=[],new_names='Yeni Oluşan Müdürlük',new_name='')
    assert save(browser,token,data).status_code == 303
    created=db.scalar(select(Department).where(Department.name=='Yeni Oluşan Müdürlük'))
    assert created.id not in {d.id for d in period_departments(db,sample['period'].id)}
    result=browser.post('/api/periods',headers={'X-CSRF-Token':token},json={'year':2028,'base_period_id':sample['period'].id})
    assert result.status_code == 200,result.text
    assert {merged.id,created.id} <= {d.id for d in period_departments(db,result.json()['id'])}


@pytest.mark.parametrize('field,value,message',[
    ('effective_date','bad','Yürürlük tarihi'), ('council_decision_no','','Meclis karar no'),
    ('council_decision_date','2029-01-01','Meclis karar tarihi'),
    ('change_type','INVALID','Yapı değişikliği türü'), ('from_department_ids',['99999'],'Müdürlük #99999')])
def test_turkish_errors_keep_values_and_rollback(db,sample,live_client,field,value,message):
    browser,token=strategy(live_client,sample)
    data=payload(sample);data[field]=value
    response=save(browser,token,data)
    assert response.status_code == 422,response.text
    assert message in response.text and 'Değişiklik kaydedilemedi' in response.text
    assert 'Yeni Hizmetler Müdürlüğü' in response.text
    assert not db.scalar(select(StructureChange.id))
    assert sample['department'].name == 'Test Müdürlüğü'


def test_only_strategy_csrf_and_pp_review_locks(db,sample,live_client):
    department=live_client();token=login(department,sample['user'].email)
    assert save(department,token,payload(sample)).status_code == 403
    browser,token=strategy(live_client,sample)
    assert save(browser,'wrong',payload(sample)).status_code == 403
    submission=db.scalar(select(Submission)); submission.status='submitted';db.commit()
    data=payload(sample);data.update(effective_date='2027-07-01',council_decision_date='2027-06-01')
    response=save(browser,token,data)
    assert response.status_code == 409 and 'PP paketi incelemede' in response.text
    assert not db.scalar(select(StructureChange.id))
    db.refresh(sample['department']);assert sample['department'].name=='Test Müdürlüğü'


def test_scope_budget_code_and_dates(db,sample,live_client):
    browser,token=strategy(live_client,sample)
    data=dict(csrf_token=token,period_id=sample['period'].id,department_id=sample['department'].id,status='required',reason='',display_name='Dönem Adı',budget_code='Serbest / 42',active_from='2027-01-01',active_to='2027-07-01')
    result=browser.post('/structure/scopes',data=data)
    assert result.status_code==303,result.text
    scope=db.scalar(select(DepartmentScope));assert scope.budget_code=='Serbest / 42' and scope.active_to==date(2027,7,1)
    assert department_snapshot(db,scope.period_id,scope.department_id)['department']=='Dönem Adı'
    data.update(active_from='2027-08-01')
    result=browser.post('/structure/scopes',data=data)
    assert result.status_code==422 and 'başlangıç tarihi' in result.text


@pytest.mark.parametrize('foundation_db',['c0292027a001'],indirect=True)
def test_additive_migration_preserves_rows_names_and_guards_after_downgrade(foundation_db):
    db=foundation_db
    db.execute(text("INSERT INTO organizations (id,name) VALUES (1,'Pilot')"))
    db.execute(text("INSERT INTO departments (id,organization_id,name,is_active) VALUES (1,1,'Eski Ad',true)"))
    db.execute(text("INSERT INTO reporting_periods (id,year,status,template_status) VALUES (1,2026,'active','verified')"))
    db.execute(text("INSERT INTO department_scopes (id,period_id,department_id,position,display_name,status,reason) VALUES (1,1,1,0,'','required','')"))
    db.execute(text("INSERT INTO users (id,email,full_name,role,password_hash,is_active,position,can_submit) VALUES (1,'test@example.invalid','Test','strategy','unused',true,'staff',false)"));db.commit()
    env={**os.environ,'DATABASE_URL':db.bind.url.render_as_string(hide_password=False)}
    def migrate(action,rev):
        result=subprocess.run([sys.executable,'-m','alembic',action,rev],cwd=ROOT,env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
    migrate('upgrade','head')
    assert db.execute(text('SELECT display_name FROM department_scopes')).scalar()=='Eski Ad'
    db.execute(text("INSERT INTO structure_changes (id,change_type,effective_date,council_decision_no,council_decision_date,note,snapshot_json,created_by,created_at) VALUES (1,'RENAMED','2027-01-01','48','2026-12-01','','{}',1,CURRENT_TIMESTAMP)"))
    db.execute(text("INSERT INTO structure_change_links (id,change_id,from_department_id,to_department_id) VALUES (1,1,1,1)"));db.commit()
    db.execute(text("INSERT INTO departments (id,organization_id,name,is_active) VALUES (2,1,'Devralan',true)"))
    db.execute(text("INSERT INTO official_activities (id,period_id,program_code,program_name,subprogram_code,subprogram_name,code,name) VALUES (1,1,'1','Program','1.1','Alt','1.1.1','İş')"))
    db.execute(text("INSERT INTO structure_change_transfers (id,change_id,from_department_id,to_department_id,official_activity_id,note) VALUES (1,1,1,2,1,'Görev devri')"))
    db.execute(text("INSERT INTO structure_change_cancellations (id,change_id,note,created_by,created_at) VALUES (1,1,'Yanlış karar',1,CURRENT_TIMESTAMP)"));db.commit()
    for table in ('structure_changes','structure_change_links','structure_change_transfers','structure_change_cancellations'):
        for mutation in (f'DELETE FROM {table}',f'UPDATE {table} SET id=id'):
            with pytest.raises(DBAPIError): db.execute(text(mutation));db.commit()
            db.rollback()
    migrate('downgrade','c0292027a001')
    assert db.execute(text('SELECT COUNT(*) FROM structure_changes')).scalar()==1
    assert db.execute(text('SELECT COUNT(*) FROM structure_change_links')).scalar()==1
    assert db.execute(text('SELECT display_name FROM department_scopes')).scalar()=='Eski Ad'
    db.commit();migrate('upgrade','head')
    scripts=ScriptDirectory.from_config(Config(str(ROOT/'alembic.ini')))
    assert len(scripts.get_heads()) == 1
    assert 'c0272027a001' in {r.revision for r in scripts.iterate_revisions('head', 'c0292027a001')}
    assert scripts.get_revision('c0272027a001').down_revision == 'c0292027a001'
    assert db.execute(text('SELECT COUNT(*) FROM departments')).scalar()==2
    assert db.execute(text('SELECT COUNT(*) FROM structure_change_transfers')).scalar()==1
    assert db.execute(text('SELECT COUNT(*) FROM structure_change_cancellations')).scalar()==1


def test_close_without_successor_keeps_year_scope_and_reports_omissions(db,sample,live_client):
    browser,token=strategy(live_client,sample)
    data=payload(sample);data.update(change_type='CLOSED',effective_date='2027-10-01',council_decision_date='2027-09-20',new_name='')
    result=save(browser,token,data);assert result.status_code==303,result.text
    link=db.scalar(select(StructureChangeLink));assert link.to_department_id is None
    note=browser.get('/activity-report?year=2027').text
    assert 'devralan müdürlük belirtilmedi' in note and 'Hizmet sayısı' in note
    result=browser.post('/api/periods',headers={'X-CSRF-Token':token},json={'year':2028,'base_period_id':sample['period'].id})
    assert result.status_code==200,result.text
    assert {item['kind'] for item in result.json()['untransferred']}=={'activity','indicator','official'}
    assert not db.scalar(select(Activity.id).where(Activity.period_id==result.json()['id']))


def test_cancellation_of_new_department_keeps_all_rows(db,sample,live_client):
    browser,token=strategy(live_client,sample)
    data=payload(sample);data.update(change_type='CREATED',from_department_ids=[],new_name='',new_names='Yeni Birim')
    assert save(browser,token,data).status_code==303
    created=db.scalar(select(Department).where(Department.name=='Yeni Birim'))
    change=db.scalar(select(StructureChange))
    result=browser.post(f'/structure/changes/{change.id}/cancel?period_id=1',data={'csrf_token':token,'note':'Meclis kararı düzeltildi'})
    assert result.status_code==303,result.text
    db.refresh(created);assert not created.is_active
    assert db.get(Department,created.id)
    assert db.scalar(select(StructureChangeCancellation))
    assert db.scalar(select(func.count(StructureChangeLink.id)))==1


def test_publication_bound_ar_shows_closure_without_rewriting_publication(db,sample,live_client):
    from app.models import Publication, ReportSection
    browser,token=strategy(live_client,sample)
    submission=db.scalar(select(Submission));submission.status='approved'
    db.add(ReportSection(period_id=sample['period'].id,title='Genel Bilgiler',content_json='{}'));db.commit()
    result=browser.post('/report-builder/publish',data={'csrf_token':token,'period_id':sample['period'].id})
    assert result.status_code==303,result.text
    publication=db.scalar(select(Publication));frozen=publication.snapshot_json
    submission.status='returned';db.commit()
    data=split_data(sample,effective_date='2027-07-01',council_decision_date='2027-06-20')
    result=save(browser,token,data);assert result.status_code==303,result.text
    result=browser.post('/api/activity-reports/revisions',headers={'X-CSRF-Token':token},
        json={'publication_id':publication.id,'organization_id':sample['department'].organization_id})
    assert result.status_code==200,result.text
    rid=result.json()['revision_id']
    report=browser.get(f'/api/activity-reports/revisions/{rid}').json()
    assert report['closure_notes'][0]['department_id']==sample['department'].id
    assert '01.07.2027' in report['closure_notes'][0]['message']
    page=browser.get(f'/activity-reports/revisions/{rid}')
    assert page.status_code==200 and '01.07.2027 tarihinde kapandı/birleşti' in page.text
    db.refresh(publication);assert publication.snapshot_json==frozen


def test_merge_into_existing_department_preserves_its_own_work(db,sample,live_client):
    receiver=Department(organization_id=sample['department'].organization_id,name='Devam Eden Müdürlük');db.add(receiver);db.flush()
    own=Activity(period_id=sample['period'].id,department_id=receiver.id,subprogram_id=sample['subprogram'].id,name='Devralanın kendi işi')
    db.add(own);db.commit()
    browser,token=strategy(live_client,sample)
    data=payload(sample);data.update(change_type='MERGED',effective_date='2027-07-01',council_decision_date='2027-06-20',new_name='',to_department_ids=[receiver.id])
    data[f'transfer_activity_{sample["activity"].id}_{sample["department"].id}']=str(receiver.id)
    result=save(browser,token,data);assert result.status_code==303,result.text
    db.refresh(receiver);assert receiver.is_active
    result=browser.post('/api/periods',headers={'X-CSRF-Token':token},json={'year':2028,'base_period_id':sample['period'].id})
    assert result.status_code==200,result.text
    activities=db.scalars(select(Activity).where(Activity.period_id==result.json()['id'])).all()
    assert {row.name for row in activities}=={sample['activity'].name,own.name}
    assert all(row.department_id==receiver.id for row in activities)
