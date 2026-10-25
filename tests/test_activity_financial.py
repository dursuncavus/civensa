"""CIV-038 acceptance through real login/CSRF against disposable PostgreSQL."""
import hashlib
import io
import json
from decimal import Decimal
import pytest
from openpyxl import load_workbook
from sqlalchemy import select
from app.models import (ARBudgetRow, ARContentEvent, ARDocumentFreeze, ARFinancialImport,
    ARFinancialStatement, Publication, EconomicValue)
from app import activity_financial_service as finance
from app import activity_sections_service as sections
from test_activity_sections import section_client, login, save, ready_and_freeze

pytestmark=pytest.mark.postgres


def endpoint(doc):return f'/api/activity-sections/reports/{doc.id}/financial'


def financial(client,doc):
    response=client.get(endpoint(doc))
    assert response.status_code==200,response.text
    return response.json()


def post(client,token,doc,path,**values):
    revision=client.get(f'/api/activity-sections/reports/{doc.id}').json().get('revision',0)
    return client.post(endpoint(doc)+path,headers={'X-CSRF-Token':token},json={'expected_revision':revision,**values})


def expenditure(dep,**updates):
    return {'department_id':dep,'economic_code':'01','initial':12500.23,'added':100,'deducted':50,
        'actual':10000,'cancelled':0,'carried':0,'explanation':'',**updates}


def programme(sample,**updates):
    row=expenditure(sample['department'].id,**updates);row.pop('economic_code',None)
    return {**row,'program_id':sample['subprogram'].program_id,'subprogram_id':sample['subprogram'].id}


def xlsx(client,doc,kind,rows):
    response=client.get(endpoint(doc)+f'/template/{kind}')
    assert response.status_code==200,response.text
    book=load_workbook(io.BytesIO(response.content));sheet=book.active
    keys=[k for k,_ in finance.budget_columns(kind)]
    for row in rows:sheet.append([row.get(k) for k in keys])
    output=io.BytesIO();book.save(output);return output.getvalue()


def preview(client,token,doc,kind,rows):
    revision=client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    return client.post(endpoint(doc)+f'/imports/{kind}/preview',headers={'X-CSRF-Token':token},
        data={'expected_revision':revision},files={'file':('mali.xlsx',xlsx(client,doc,kind,rows))})


def test_computed_totals_scope_and_turkish_mismatch(section_client,sample):
    client,docs,other,finance_dep=section_client;doc=docs['idare'];token=login(client,'finance@example.invalid')
    rows=[expenditure(sample['department'].id),expenditure(other.id,actual=0,initial=0,added=0,deducted=0),
          expenditure(finance_dep.id,actual=0,initial=0,added=0,deducted=0)]
    assert post(client,token,doc,'/budget/expenditure',rows=rows).status_code==200
    assert post(client,token,doc,'/budget/programme',rows=[programme(sample,initial=12000.23)]).status_code==200
    data=financial(client,doc);table=data['tables']['expenditure']
    assert table['rows'][0]['final']==12550.23
    assert table['rows'][0]['rate']==79.68
    assert table['rows'][1]['rate'] is None
    assert table['totals']['actual']=={'value':10000,'missing':0}
    assert table['totals']['actual']['value']==sum(d['totals']['actual']['value'] for d in table['by_department'])
    message=' '.join(data['checks'])
    assert '12.500,23' in message and '12.000,23' in message and 'fark 500' in message
    assert 'İdare' in message and 'Test Müdürlüğü' in message
    own=docs['birim:'+str(sample['department'].id)]
    token=login(client,'test@example.invalid');own_data=financial(client,own)
    assert len(own_data['tables']['expenditure']['rows'])==1
    assert 'revenue' not in own_data['tables']
    assert post(client,token,own,'/budget/expenditure',rows=rows).status_code==403
    assert client.get(f'/activity-sections/reports/{own.id}?code=III.A.1').status_code==200


def test_blank_zero_revenue_and_final_consistency(section_client,sample):
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'strategy@example.invalid')
    assert post(client,token,doc,'/budget/expenditure',rows=[expenditure(sample['department'].id,added=None,actual=0,entered_final=100)]).status_code==200
    data=financial(client,doc);r=data['tables']['expenditure']['rows'][0]
    assert r['actual']==0 and r['added'] is None and r['final'] is None and r['rate'] is None
    assert data['tables']['expenditure']['totals']['added']=={'value':None,'missing':3}
    assert any('boş' in m for m in data['missing']['III.A.1'])
    assert post(client,token,doc,'/budget/expenditure',rows=[expenditure(sample['department'].id,entered_final=12500.23)]).status_code==200
    assert any('hesaplanan 12.550,23, bildirilen 12.500,23, fark -50' in m for m in financial(client,doc)['checks'])
    rows=[{'economic_code':'01','estimate':1000,'actual':900,'refunds':100,'explanation':''},
        {'economic_code':'03.01','estimate':0,'actual':0,'refunds':None,'explanation':''}]
    assert post(client,token,doc,'/budget/revenue',rows=rows).status_code==200
    data=financial(client,doc)['tables']['revenue']['rows']
    assert data[0]['net']==800 and data[0]['rate']==80
    assert data[1]['net'] is None and data[1]['actual']==0
    page=client.get(f'/activity-sections/reports/{doc.id}?code=III.A.1')
    assert page.status_code==200 and '12.500,23' in page.text and '<th>Net tahsilat</th>' in page.text


def test_thresholds_and_own_explanations(section_client,sample):
    client,docs,other,_=section_client;doc=docs['idare'];token=login(client,'strategy@example.invalid')
    assert post(client,token,doc,'/budget/expenditure',rows=[expenditure(sample['department'].id,actual=100)]).status_code==200
    assert not any('Sapma açıklaması gerekli' in m for m in financial(client,doc)['missing']['III.A.1'])
    assert post(client,token,doc,'/policy',lower_rate=80,upper_rate=110).status_code==200
    assert any('Sapma açıklaması gerekli' in m for m in financial(client,doc)['missing']['III.A.1'])
    assert post(client,token,doc,'/policy',lower_rate=110,upper_rate=80).status_code==422
    token=login(client,'finance@example.invalid')
    assert post(client,token,doc,'/policy',lower_rate=80,upper_rate=110).status_code==403
    token=login(client,'test@example.invalid');own=docs['birim:'+str(sample['department'].id)]
    key=financial(client,own)['tables']['expenditure']['rows'][0]['row_key']
    assert post(client,token,own,'/entries/explanations',rows=[{'row_key':key,'explanation':'İhale ertelendi.'}]).status_code==200
    assert not any('Sapma açıklaması gerekli' in m for m in financial(client,own)['missing']['III.A.1'])
    assert post(client,token,own,'/entries/explanations',rows=[{'row_key':'başka müdürlük','explanation':'Değişiklik'}]).status_code==403
    assert client.get(f'/api/activity-sections/reports/{docs["birim:"+str(other.id)].id}/financial').status_code==403
    assert post(client,token,doc,'/policy',lower_rate=None,upper_rate=None).status_code==403
    token=login(client,'strategy@example.invalid')
    assert post(client,token,doc,'/policy',lower_rate=None,upper_rate=None).status_code==200
    assert financial(client,doc)['policy']=={'lower_rate':None,'upper_rate':None}


@pytest.mark.parametrize('kind',['expenditure','programme','revenue'])
def test_xlsx_round_trip_and_history(section_client,sample,db,kind):
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'finance@example.invalid')
    row=programme(sample) if kind=='programme' else {'economic_code':'01','estimate':12500.23,'actual':0,'refunds':0,'explanation':'Gelir'} if kind=='revenue' else expenditure(sample['department'].id)
    response=preview(client,token,doc,kind,[row]);assert response.status_code==200,response.text
    data=response.json();assert not data['errors'] and data['differences'][0]['action']=='added'
    assert financial(client,doc)['tables'][kind]['rows']==[]
    assert post(client,token,doc,f'/imports/{data["id"]}/apply').status_code==200
    old_import=data['id']
    row['actual']=500
    response=preview(client,token,doc,kind,[row]);data=response.json()
    assert not data['errors'] and data['differences'][0]['action']=='changed'
    assert data['differences'][0]['before']['actual']==0 if kind=='revenue' else data['differences'][0]['before']['actual']==10000
    assert data['differences'][0]['after']['actual']==500
    assert post(client,token,doc,f'/imports/{data["id"]}/apply').status_code==200
    assert db.get(ARFinancialImport,old_import) is not None
    assert len(financial(client,doc)['tables'][kind]['rows'])==1
    assert financial(client,doc)['tables'][kind]['rows'][0]['actual']==500
    event=db.scalar(select(ARContentEvent).where(ARContentEvent.action=='financial_import').order_by(ARContentEvent.id.desc()))
    assert '500' in event.after_json and event.before_json!='[]'
    assert post(client,token,doc,f'/imports/{data["id"]}/apply').status_code==409


def test_preview_row_errors_and_manual_protection(section_client,sample):
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'finance@example.invalid');dep=sample['department'].id
    rows=[expenditure(999999),expenditure(dep,economic_code='99'),expenditure(dep,initial='sayı değil'),
        expenditure(dep,initial=-1),expenditure(dep),expenditure(dep)]
    response=preview(client,token,doc,'expenditure',rows)
    assert response.status_code==200,response.text
    data=response.json();message=' '.join(e['message'] for e in data['errors'])
    assert all(term in message for term in ('Bilinmeyen müdürlük','Bilinmeyen ekonomik kod','Sayı okunamadı','negatif','Yinelenen','XLSX 2. satır')),message
    assert post(client,token,doc,f'/imports/{data["id"]}/apply').status_code==422
    assert post(client,token,doc,'/budget/expenditure',rows=[expenditure(dep)]).status_code==200
    data=preview(client,token,doc,'expenditure',[expenditure(dep)]).json()
    assert any('Elle girilmiş' in e['message'] for e in data['errors'])
    assert post(client,token,doc,f'/imports/{data["id"]}/apply').status_code==422
    # The replacement removes imported rows only, preserving a different manual key.
    data=preview(client,token,doc,'expenditure',[expenditure(dep,economic_code='02')]).json()
    assert not data['errors']
    assert post(client,token,doc,f'/imports/{data["id"]}/apply').status_code==200
    data=preview(client,token,doc,'expenditure',[]).json()
    assert data['differences'][0]['action']=='removed'
    assert post(client,token,doc,f'/imports/{data["id"]}/apply').status_code==200
    assert [r['economic_code'] for r in financial(client,doc)['tables']['expenditure']['rows']]==['01']


def test_stale_preview_csrf_formula_and_parent_double_count(section_client,sample):
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'finance@example.invalid');dep=sample['department'].id
    data=preview(client,token,doc,'expenditure',[expenditure(dep)]).json()
    assert post(client,token,doc,'/budget/revenue',rows=[]).status_code==200
    assert post(client,token,doc,f'/imports/{data["id"]}/apply').status_code==409
    no_csrf=client.post(endpoint(doc)+'/budget/expenditure',json={'expected_revision':1,'rows':[]})
    assert no_csrf.status_code==403
    data=preview(client,token,doc,'expenditure',[expenditure(dep,actual='=1+1')]).json()
    assert data['errors']
    result=post(client,token,doc,'/budget/expenditure',rows=[expenditure(dep),expenditure(dep,economic_code='01.01')])
    assert result.status_code==422 and 'Çift toplam' in result.text


def test_dynamic_statements_hash_assets_aid_and_audit(section_client,sample,db):
    client,docs,other,_=section_client;doc=docs['idare'];token=login(client,'finance@example.invalid')
    assert {s['name'] for s in financial(client,doc)['statements']}==set(finance.DEFAULT_STATEMENTS)
    raw=b'%PDF-1.4\nCIV-038 local fixture\n%%EOF'
    metadata={'name':'Nakit Akış Tablosu','period':'2027','statement_date':'2027-12-31','explanation':'Nakit hareketleri.',
        'figures':[{'label':'Net nakit','amount':12500.23}]}
    revision=client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    response=client.post(endpoint(doc)+'/statements',headers={'X-CSRF-Token':token},
        data={'expected_revision':revision,'metadata':json.dumps(metadata)},files={'file':('nakit.pdf',raw,'application/pdf')})
    assert response.status_code==200,response.text
    row=db.scalar(select(ARFinancialStatement).where(ARFinancialStatement.name=='Nakit Akış Tablosu'))
    assert row.sha256==hashlib.sha256(raw).hexdigest() and row.file_data==raw
    assert client.get(endpoint(doc)+f'/statements/{row.id}/file').content==raw
    assert post(client,token,doc,'/entries/assets',rows=[{'label':'Yükümlülükler','amount':0,'previous':12500.23,'explanation':'Borçlar kapatıldı.'}]).status_code==200
    assert client.get(f'/activity-sections/reports/{doc.id}?code=III.A.2').status_code==200
    token=login(client,'test@example.invalid');own=docs['birim:'+str(sample['department'].id)]
    aid={'name':'Belediyeler Birliği','aid_type':'Nakdî','amount':0,'basis':'Meclis kararı','explanation':'Faaliyet tamamlandı.'}
    audit={'audit_type':'iç denetim','auditor':'İç denetçi','period':'2027','report_date':'2027-12-31','report_number':'1',
        'findings':'Bulgu özeti','measures':'Önlem alındı','status':'Tamamlandı'}
    assert post(client,token,own,'/entries/aid',rows=[aid]).status_code==200
    assert post(client,token,own,'/entries/audit',rows=[audit,{**audit,'audit_type':'dış denetim (Sayıştay)','auditor':'Sayıştay'}]).status_code==200
    assert financial(client,own)['missing']['III.A.3']==[]
    assert post(client,token,docs['birim:'+str(other.id)],'/entries/aid',rows=[aid]).status_code==403
    assert post(client,token,doc,'/entries/aid',rows=[aid]).status_code==403
    assert post(client,token,own,'/entries/assets',rows=[]).status_code==403
    assert save(client,token,own,code='III.A.4',status='not_applicable',reason='Bu yıl yardım yapılmadı.',blocks=[]).status_code==200
    report=client.get(f'/api/activity-sections/reports/{own.id}').json()
    assert next(s for s in report['sections'] if s['code']=='III.A.4')['missing']==[]
    token=login(client,'strategy@example.invalid')
    assert len(financial(client,doc)['entries']['aid_directorates'])==0
    assert len(financial(client,doc)['entries']['audit_directorates'])==0
    assert post(client,token,doc,'/entries/aid',rows=[aid]).status_code==200
    assert db.scalar(select(ARContentEvent).where(ARContentEvent.action=='financial_save',ARContentEvent.actor_id==sample['strategy'].id))


def test_frozen_numeric_financial_copy_and_immutable_writes(section_client,sample,db):
    client,docs,other,finance_dep=section_client;doc=docs['idare'];token=login(client,'strategy@example.invalid')
    zeros={'initial':0,'added':0,'deducted':0,'actual':0,'cancelled':0,'carried':0}
    expense_rows=[expenditure(sample['department'].id)]+[expenditure(dep.id,**zeros) for dep in (other,finance_dep)]
    programme_rows=[programme(sample)]+[programme(sample,department_id=dep.id,**zeros) for dep in (other,finance_dep)]
    assert post(client,token,doc,'/budget/expenditure',rows=expense_rows).status_code==200
    assert post(client,token,doc,'/budget/programme',rows=programme_rows).status_code==200
    data=preview(client,token,doc,'revenue',[{'economic_code':'01','estimate':100,'actual':0,'refunds':0}]).json()
    assert post(client,token,doc,f'/imports/{data["id"]}/apply').status_code==200
    ready_and_freeze(client,token,doc)
    before=client.get(f'/api/activity-sections/reports/{doc.id}').json()
    freeze=db.scalar(select(ARDocumentFreeze).where(ARDocumentFreeze.document_id==doc.id))
    payload=json.loads(freeze.payload_json)
    assert payload['financial']['tables']['expenditure']['rows'][0]['initial']==12500.23
    assert '"initial":12500.23' in freeze.payload_json
    assert post(client,token,doc,'/budget/expenditure',rows=[]).status_code==409
    assert post(client,token,doc,'/entries/aid',rows=[]).status_code==409
    assert post(client,token,doc,'/policy',lower_rate=80,upper_rate=110).status_code==409
    assert preview(client,token,doc,'expenditure',[expenditure(sample['department'].id)]).status_code==409
    assert client.get(f'/api/activity-sections/reports/{doc.id}').json()==before
    assert client.get(f'/activity-sections/reports/{doc.id}?code=III.A.1').status_code==200


def test_frozen_pp_reference_never_becomes_actual(section_client,sample,db):
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'finance@example.invalid')
    from app.program_service import book_snapshot
    payload=book_snapshot(db,sample['period'].id)
    raw=sections.numeric_canonical(payload)
    pub=Publication(period_id=sample['period'].id,version=1,snapshot_json=raw,sha256=hashlib.sha256(raw.encode()).hexdigest(),created_by=sample['strategy'].id)
    db.add(pub);db.commit()
    assert post(client,token,doc,'/budget/expenditure',rows=[expenditure(sample['department'].id,initial=None)]).status_code==200
    data=financial(client,doc)['tables']['expenditure']['rows'][0]
    assert data['pp_budget']==15 and data['pp_publication_id']==pub.id
    assert data['initial'] is None
    live=db.scalar(select(EconomicValue).where(EconomicValue.category=='personnel',EconomicValue.value_kind=='budget',EconomicValue.year==2027,EconomicValue.funding_type=='inside'))
    live.amount=999;db.commit()
    assert financial(client,doc)['tables']['expenditure']['rows'][0]['pp_budget']==15


def test_forms_retain_invalid_turkish_input_and_financial_completeness(section_client,sample):
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'finance@example.invalid')
    response=client.post(f'/activity-sections/reports/{doc.id}/financial/budget/expenditure',data={
        'csrf_token':token,'expected_revision':0,'include_0':'on','department_id_0':sample['department'].id,
        'economic_code_0':'01','initial_0':'hatalı sayı','explanation_0':'Girdi korunmalı'})
    assert response.status_code==422 and 'hatalı sayı' in response.text and 'Girdi korunmalı' in response.text
    response=client.post(f'/activity-sections/reports/{doc.id}/financial/budget/expenditure',data={
        'csrf_token':token,'expected_revision':0,'include_0':'on','department_id_0':sample['department'].id,
        'economic_code_0':'01','initial_0':'12.500,23','added_0':'0','deducted_0':'0','actual_0':'0','cancelled_0':'0','carried_0':'0','explanation_0':''})
    assert response.status_code==303,response.text
    assert financial(client,doc)['tables']['expenditure']['rows'][0]['initial']==12500.23
    page=client.get('/activity-sections?section=III.A.1')
    assert page.status_code==200 and 'Program / alt program' in page.text


def test_revenue_threshold_boundaries_and_na_cannot_hide_issues(section_client,sample):
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'strategy@example.invalid')
    assert post(client,token,doc,'/policy',lower_rate=80,upper_rate=110).status_code==200
    rows=[{'economic_code':'01','estimate':100,'actual':80,'refunds':0},
        {'economic_code':'03','estimate':100,'actual':110,'refunds':0},
        {'economic_code':'05','estimate':100,'actual':111,'refunds':0}]
    assert post(client,token,doc,'/budget/revenue',rows=rows).status_code==200
    missing=[m for m in financial(client,doc)['missing']['III.A.1'] if 'Sapma açıklaması gerekli' in m]
    assert len(missing)==1 and '111' in missing[0]
    assert save(client,token,doc,'III.A.1',status='not_applicable',reason='Eksik veri bekleniyor.',blocks=[]).status_code==200
    report=client.get(f'/api/activity-sections/reports/{doc.id}').json()
    assert any('Sapma açıklaması gerekli' in m for s in report['sections'] if s['code']=='III.A.1' for m in s['missing'])
    assert post(client,token,doc,'/policy',lower_rate=None,upper_rate=None).status_code==200
    assert not any('Sapma açıklaması gerekli' in m for m in financial(client,doc)['missing']['III.A.1'])


def test_permissions_imports_statement_xlsx_and_incomplete_explanations(section_client,sample):
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'finance@example.invalid')
    content=xlsx(client,doc,'revenue',[{'economic_code':'01','estimate':100,'actual':80,'refunds':0}])
    revision=client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    metadata={'name':'Bilanço','period':'2027','explanation':''}
    response=client.post(endpoint(doc)+'/statements',headers={'X-CSRF-Token':token},data={'expected_revision':revision,'metadata':json.dumps(metadata)},files={'file':('bilanco.xlsx',content)})
    assert response.status_code==200,response.text
    statement=next(s for s in financial(client,doc)['statements'] if s['name']=='Bilanço')
    assert statement['sha256']==hashlib.sha256(content).hexdigest()
    assert any('Bilanço: Açıklamalar eksik' in m for m in financial(client,doc)['missing']['III.A.2'])
    token=login(client,'test@example.invalid')
    assert client.get(endpoint(doc)+'/template/expenditure').status_code==403
    revision=client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    response=client.post(endpoint(doc)+'/imports/revenue/preview',headers={'X-CSRF-Token':token},data={'expected_revision':revision},files={'file':('mali.xlsx',content)})
    assert response.status_code==403
    response=client.post(endpoint(doc)+'/statements',headers={'X-CSRF-Token':token},data={'expected_revision':revision,'metadata':json.dumps(metadata)},files={'file':('bilanco.xlsx',content)})
    assert response.status_code==403


def test_import_entered_final_checked_with_turkish_values(section_client,sample):
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'finance@example.invalid')
    response=preview(client,token,doc,'expenditure',[expenditure(sample['department'].id,entered_final=12500.23)])
    assert response.status_code==200,response.text
    data=response.json();message=' '.join(e['message'] for e in data['errors'])
    assert 'hesaplanan 12.550,23, bildirilen 12.500,23, fark -50' in message
    assert post(client,token,doc,f'/imports/{data["id"]}/apply').status_code==422
    assert financial(client,doc)['tables']['expenditure']['rows']==[]


def test_invalid_upload_and_boolean_threshold_have_turkish_errors(section_client,sample):
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'strategy@example.invalid')
    revision=client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    for data in (b'not an xlsx',b''):
        response=client.post(endpoint(doc)+'/imports/expenditure/preview',headers={'X-CSRF-Token':token},
            data={'expected_revision':revision},files={'file':('bozuk.xlsx',data)})
        assert response.status_code==422 and 'XLSX dosyası okunamadı' in response.text
    response=post(client,token,doc,'/policy',lower_rate=True,upper_rate=None)
    assert response.status_code==422 and 'Alt gerçekleşme oranı' in response.text
    # A structurally valid ZIP with malformed workbook XML must also produce a usable error.
    from zipfile import ZipFile
    workbook=xlsx(client,doc,'expenditure',[])
    output=io.BytesIO()
    with ZipFile(io.BytesIO(workbook)) as original,ZipFile(output,'w') as broken:
        for name in original.namelist():broken.writestr(name,b'<broken' if name=='xl/workbook.xml' else original.read(name))
    response=client.post(endpoint(doc)+'/imports/expenditure/preview',headers={'X-CSRF-Token':token},
        data={'expected_revision':revision},files={'file':('bozuk.xlsx',output.getvalue())})
    assert response.status_code==422 and 'XLSX dosyası okunamadı' in response.text


def test_birim_freeze_preserves_numbers_when_idare_draft_changes(section_client,sample):
    client,docs,_,_=section_client;doc=docs['idare'];own=docs['birim:'+str(sample['department'].id)]
    token=login(client,'strategy@example.invalid')
    assert post(client,token,doc,'/budget/expenditure',rows=[expenditure(sample['department'].id)]).status_code==200
    assert post(client,token,doc,'/budget/programme',rows=[programme(sample)]).status_code==200
    ready_and_freeze(client,token,own)
    before=client.get(f'/api/activity-sections/reports/{own.id}').json()
    assert before['financial']['tables']['expenditure']['rows'][0]['actual']==10000
    assert post(client,token,doc,'/budget/expenditure',rows=[expenditure(sample['department'].id,actual=9000)]).status_code==200
    assert client.get(f'/api/activity-sections/reports/{own.id}').json()==before
    token=login(client,'test@example.invalid')
    assert post(client,token,own,'/entries/explanations',rows=[]).status_code==409
