"""Confirmed browser acceptance fixes, without reinterpreting historical contracts."""
import json
import re
from html import unescape
from pathlib import Path
from datetime import datetime, timezone
import pytest
from sqlalchemy import select, func
from app.main import app, require_user
from app import activity_contract_service as service
from app.models import (Indicator, IndicatorIdentity, IndicatorDefinitionRevision, Publication,
 PublicationIndicatorBinding, ActualRevision, ActivityReportApproval, IndicatorValue)
from app.time_display import turkey_time
from test_activity_contract import publish, new_report, actual_payload

pytestmark = pytest.mark.postgres

@pytest.mark.parametrize('own', ['Göstergeye özel açıklama', '', '  '])
def test_v3_effective_explanation(client, db, sample, own):
    sample['indicator'].explanation=own; db.commit()
    report=new_report(client,publish(client,db,sample),sample)
    assert report['contract_version']=='3.0'
    assert report['indicators'][0]['definition']['explanation']==(own if own.strip() else 'Ortak açıklama')


def test_explanation_change_is_frozen_and_diffed(client,db,sample):
    first=publish(client,db,sample); before=(first.snapshot_json,first.sha256)
    report=new_report(client,first,sample)
    did=report['indicators'][0]['definition_revision_id'];definition=db.get(IndicatorDefinitionRevision,did)
    definition_before=(definition.definition_json,definition.sha256)
    sample['card'].explanation='Yeni ortak açıklama';db.commit()
    second=publish(client,db,sample)
    revised=new_report(client,second,sample,report_id=report['report_id'],expected_revision=1)
    assert revised['differences'][0]['before']['explanation']=='Ortak açıklama'
    assert revised['differences'][0]['after']['explanation']=='Yeni ortak açıklama'
    assert revised['indicators'][0]['definition_revision_id']!=did
    page=client.get(f"/activity-reports/revisions/{revised['revision_id']}")
    assert 'Yeni ortak açıklama' in page.text and 'Ortak açıklama' in page.text
    db.expire_all()
    assert (first.snapshot_json,first.sha256)==before
    assert (definition.definition_json,definition.sha256)==definition_before

@pytest.mark.parametrize('version',['1','2'])
def test_frozen_checkpoint_interpretations_stable(client,db,sample,version):
    f=json.loads((Path(__file__).parent/f'fixtures/activity_contract_v{version}_checkpoint.json').read_text())
    identity=f['indicator_id'];db.add(IndicatorIdentity(indicator_id=identity,organization_id=sample['department'].organization_id));db.flush()
    sample['indicator'].persistent_indicator_id=identity
    definition=IndicatorDefinitionRevision(indicator_id=identity,revision=1,period_id=sample['period'].id,definition_json=f['definition_json'],sha256=f['definition_sha256'],created_by=sample['strategy'].id)
    pub=Publication(period_id=sample['period'].id,version=1,snapshot_json=f['publication_snapshot_json'],sha256=f['publication_sha256'],created_by=sample['strategy'].id)
    db.add_all([definition,pub]);db.flush()
    binding=PublicationIndicatorBinding(publication_id=pub.id,snapshot_indicator_id=sample['indicator'].id,definition_revision_id=definition.id,department_id=sample['department'].id,created_by=sample['strategy'].id,reason='Historical checkpoint fixture')
    db.add(binding);db.commit();app.dependency_overrides[require_user]=lambda:sample['strategy']
    before=(pub.snapshot_json,pub.sha256,definition.definition_json,definition.sha256,binding.reason)
    old=new_report(client,pub,sample)
    assert old['contract_version']==version+'.0'
    assert old['indicators'][0]['definition']['explanation']==''
    sample['card'].explanation='Changed live card';db.commit()
    current=publish(client,db,sample)
    new_report(client,current,sample,report_id=old['report_id'],expected_revision=1)
    assert client.get(f"/activity-reports/revisions/{old['revision_id']}").status_code==200
    db.expire_all();assert (pub.snapshot_json,pub.sha256,definition.definition_json,definition.sha256,binding.reason)==before

@pytest.mark.parametrize('state,number,expected',[('verified','0',422),('needs_review','0',200),('missing',None,200)])
def test_verified_requires_evidence_but_review_missing_do_not(client,db,sample,state,number,expected):
    report=new_report(client,publish(client,db,sample),sample);slot=report['indicators'][0]['report_indicator_id']
    response=client.post(f'/api/activity-reports/indicators/{slot}/actuals',json=actual_payload(state=state,value=number,evidence=[]))
    assert response.status_code==expected
    if expected==422:
        assert 'kaynak' in response.json()['detail'] and 'İncelenmeli' in response.json()['detail']
        assert db.scalar(select(func.count()).select_from(ActualRevision))==0

@pytest.mark.parametrize('patch',[{'value':'abc'},{'value':'abc','state':'needs_review'},{'value':'abc','state':'missing'},{'source_revision':''},{'source_title':'','source_locator':'','source_revision':''}])
def test_failed_form_preserves_every_field(client,db,sample,patch):
    report=new_report(client,publish(client,db,sample),sample);slot=report['indicators'][0]['report_indicator_id']
    fields=dict(expected_revision='0',value='12.500,23',state='verified',source_title='Taslak kaynak',source_locator='Sayfa 9',source_revision='2027-v1',explanation='Taslak açıklama',corrective_action='Taslak işlem')
    fields.update(patch)
    response=client.post(f'/activity-reports/indicators/{slot}/actuals',data=fields)
    assert response.status_code==422
    form=re.search(r'<form[^>]+action="/activity-reports/indicators/'+str(slot)+r'/actuals"[^>]*>(.*?)</form>',response.text,re.S).group(1)
    for key in ['value','source_title','source_locator','source_revision']:
        assert unescape(re.search(r'name="'+key+r'" value="([^"]*)"',form).group(1))==fields[key]
    for key in ['explanation','corrective_action']:
        assert unescape(re.search(r'<textarea name="'+key+r'">(.*?)</textarea>',form,re.S).group(1))==fields[key]
    assert re.search(r'<option value="'+fields['state']+r'"\s+selected',form)
    assert 'role="alert"' in response.text and 'Hizmet sayısı —' in response.text
    assert db.scalar(select(func.count()).select_from(ActualRevision))==0


def test_all_approval_blockers_atomic_and_visible(client,db,sample):
    for name in ['İkinci gösterge','Üçüncü gösterge']:
        indicator=Indicator(period_id=sample['period'].id,department_id=sample['department'].id,subprogram_id=sample['subprogram'].id,card_id=sample['card'].id,name=name,unit='Adet')
        db.add(indicator);db.flush();db.add(IndicatorValue(indicator_id=indicator.id,year=2027,value_kind='target',value='1'))
    db.commit();report=new_report(client,publish(client,db,sample),sample)
    slot=report['indicators'][0]['report_indicator_id']
    assert client.post(f'/api/activity-reports/indicators/{slot}/actuals',json=actual_payload(explanation='')).status_code==200
    url=f"/api/activity-reports/revisions/{report['revision_id']}/approve"
    response=client.post(url);assert response.status_code==409
    blockers=response.json()['detail']['blockers'];assert len(blockers)==3
    html=client.post(url.replace('/api','')).text
    assert all(x in html for x in ['Hizmet sayısı','İkinci gösterge','Üçüncü gösterge','farkı için açıklama'])
    assert db.scalar(select(func.count()).select_from(ActivityReportApproval))==0


def test_duplicate_same_year_has_actionable_message(client,db,sample):
    pub=publish(client,db,sample);new_report(client,pub,sample)
    response=client.post('/activity-reports/revisions',data={'publication_id':pub.id,'organization_id':sample['department'].organization_id})
    assert response.status_code==409
    assert 'kurum ve yıl' in response.text and 'mevcut raporu açıp yeni revizyon' in response.text
    assert 'başka bir işlemle çakıştı' not in response.text


def test_audit_people_and_turkey_time_without_timestamp_mutation(client,db,sample):
    report=new_report(client,publish(client,db,sample),sample);slot=report['indicators'][0]['report_indicator_id']
    app.dependency_overrides[require_user]=lambda:sample['user']
    assert client.post(f'/api/activity-reports/indicators/{slot}/actuals',json=actual_payload()).status_code==200
    actual=db.scalar(select(ActualRevision));actual_time=actual.created_at
    app.dependency_overrides[require_user]=lambda:sample['strategy']
    assert client.post(f"/api/activity-reports/revisions/{report['revision_id']}/approve").status_code==200
    approval=db.scalar(select(ActivityReportApproval));approval_time=approval.created_at
    page=client.get(f"/activity-reports/revisions/{report['revision_id']}")
    assert 'Giren: Test' in page.text and 'Onaylayan: Strateji' in page.text and 'Türkiye saati, UTC+03:00' in page.text
    data=client.get(f"/api/activity-reports/revisions/{report['revision_id']}").json()
    assert data['approval']['created_by']==sample['strategy'].id
    assert data['indicators'][0]['actuals'][0]['created_by']==sample['user'].id
    db.expire_all();assert actual.created_at==actual_time and approval.created_at==approval_time

@pytest.mark.parametrize('value',[datetime(2027,1,1,22,30),datetime(2027,1,1,22,30,tzinfo=timezone.utc),'2027-01-01T22:30:00'])
def test_turkey_time_rollover(value):
    assert turkey_time(value)=='02.01.2027 01:30 (Türkiye saati, UTC+03:00)'

@pytest.mark.parametrize('field',['department_id','subprogram_id'])
def test_v3_card_relationship_still_validated(field):
    from fastapi import HTTPException
    row={'card_id':1,'department_id':1,'subprogram_id':1,'values':[], '_report_card':{'id':1,'department_id':1,'subprogram_id':1,'explanation':'Shared'}}
    row['_report_card'][field]=2
    with pytest.raises(HTTPException) as error: service.definition_payload(row,2027,'3.0')
    assert error.value.status_code==409
