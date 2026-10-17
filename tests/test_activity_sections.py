"""EK-1 acceptance through real login and CSRF on disposable PostgreSQL."""
import importlib.util
import json
import re
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.db import get_db
from app.main import app
from app.models import (ARSectionDefinition, ARDocument, ARSectionContent, ARContentEvent,
    ARDocumentFreeze, ARResourceRow, Department, DepartmentScope, User, ReportingPeriod)
from app.security import hash_password
from app import activity_sections_service as service
from app.activity_sections_routes import form_blocks, blocks_text

pytestmark=pytest.mark.postgres
PASSWORD='Civ037-Test-Password!'
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('civ037_migration',next((ROOT/'migrations/versions').glob('c037*.py')))
MIGRATION=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MIGRATION)
EXPECTED_TREE=[
('SUNUS','ÜST YÖNETİCİ SUNUŞU'),('OZET','YÖNETİCİ ÖZETİ'),('I','I- GENEL BİLGİLER'),
('I.A','A- Misyon ve Vizyon'),('I.B','B- Yetki, Görev ve Sorumluluklar'),('I.C','C- İdareye İlişkin Bilgiler'),
('I.C.1','1- Fiziksel Yapı'),('I.C.2','2- Teşkilat Yapısı'),('I.C.3','3- Teknoloji ve Bilişim Altyapısı'),
('I.C.4','4- İnsan Kaynakları'),('I.C.5','5- Sunulan Hizmetler'),('I.C.6','6- Yönetim ve İç Kontrol Sistemi'),('I.D','D- Diğer Hususlar'),
('II','II- AMAÇLAR ve HEDEFLER'),('II.A','A- Temel Politika ve Öncelikler'),('II.B','B- İdarenin Stratejik Planında Yer Alan Amaç ve Hedefler'),('II.C','C- Diğer Hususlar'),
('III','III- FAALİYETLERE İLİŞKİN BİLGİ VE DEĞERLENDİRMELER'),('III.A','A- Malî Bilgiler'),('III.A.1','1- Bütçe Uygulama Sonuçları'),
('III.A.2','2- Temel Malî Tablolara İlişkin Açıklamalar'),('III.A.3','3- Malî Denetim Sonuçları'),('III.A.4','4- Diğer Hususlar'),
('III.B','B- Performans Bilgileri'),('III.B.1','1- Program, Alt Program, Faaliyet Bilgileri'),('III.B.2','2- Performans Sonuçlarının Değerlendirilmesi'),
('III.B.2.i','i. Alt program hedef ve göstergeleriyle ilgili gerçekleşme sonuçları ve değerlendirmeler'),('III.B.2.ii','ii. Performans denetim sonuçları'),
('III.B.3','3- Stratejik Plan Değerlendirme Tabloları'),('III.B.4','4- Performans Bilgi Sisteminin Değerlendirilmesi'),('III.B.5','5- Diğer Hususlar'),
('IV','IV- KURUMSAL KABİLİYET VE KAPASİTENİN DEĞERLENDİRİLMESİ'),('IV.A','A- Üstünlükler'),('IV.B','B- Zayıflıklar'),('IV.C','C- Değerlendirme'),('V','V- ÖNERİ VE TEDBİRLER'),('EKLER','EKLER')]


@pytest.fixture
def section_client(db,sample):
    db.add_all([ARSectionDefinition(**row) for row in MIGRATION.SECTION_SEED])
    other=Department(organization_id=sample['department'].organization_id,name='Park ve Bahçeler Müdürlüğü')
    finance=Department(organization_id=sample['department'].organization_id,name='Mali Hizmetler Müdürlüğü')
    db.add_all([other,finance]);db.flush()
    for dep in (other,finance):db.add(DepartmentScope(period_id=sample['period'].id,department_id=dep.id,status='required'))
    for dep,email in ((other,'park@example.invalid'),(finance,'finance@example.invalid')):
        db.add(User(email=email,full_name=dep.name,role='department',department_id=dep.id,password_hash=hash_password(PASSWORD)))
    for user in (sample['user'],sample['strategy']):user.password_hash=hash_password(PASSWORD)
    db.commit()
    def database():yield db
    app.dependency_overrides[get_db]=database
    client=TestClient(app,follow_redirects=False)
    token=login(client,'strategy@example.invalid')
    response=client.post('/api/activity-sections/years',json={'organization_id':sample['department'].organization_id,'period_id':sample['period'].id},headers={'X-CSRF-Token':token})
    assert response.status_code==200,response.text
    docs=db.scalars(select(ARDocument).order_by(ARDocument.id)).all()
    yield client,{d.scope:d for d in docs},other,finance
    client.close();app.dependency_overrides.clear()


def login(client,email):
    client.cookies.clear()
    result=client.post('/login',data={'email':email,'password':PASSWORD})
    assert result.status_code==303,result.text
    page=client.get('/modules')
    return re.search(r'name="csrf_token" value="([^"]+)"',page.text).group(1)


def save(client,token,doc,code='I.A',status='draft',reason='',blocks=None,revision=None):
    data=client.get(f'/api/activity-sections/reports/{doc.id}').json()
    return client.post(f'/api/activity-sections/reports/{doc.id}/sections/{code}',headers={'X-CSRF-Token':token},json={
        'expected_revision':data['revision'] if revision is None else revision,
        'blocks':[{'type':'paragraph','text':'Yıllık değerlendirme'}] if blocks is None else blocks,'status':status,'reason':reason})


def resource(client,token,doc,kind,rows):
    revision=client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    return client.post(f'/api/activity-sections/reports/{doc.id}/resources/{kind}',headers={'X-CSRF-Token':token},json={'expected_revision':revision,'rows':rows})


def ready_and_freeze(client,token,doc):
    data=client.get(f'/api/activity-sections/reports/{doc.id}').json()
    for section in data['sections']:
        if section['code']!=service.CORE:
            financial_na=bool(data.get('financial',{}).get('missing',{}).get(section['code']))
            result=save(client,token,doc,section['code'],status='not_applicable' if financial_na else 'ready',
                reason='Bu testin örnek raporunda malî veri bulunmuyor.' if financial_na else '')
            assert result.status_code==200,result.text
    revision=client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    response=client.post(f'/api/activity-sections/reports/{doc.id}/freeze',headers={'X-CSRF-Token':token},json={'expected_revision':revision})
    assert response.status_code==200,response.text
    return response.json()


def test_tree_and_scope_exact(section_client,db,sample):
    client,docs,other,finance=section_client
    definitions=db.scalars(select(ARSectionDefinition).order_by(ARSectionDefinition.position)).all()
    assert [(d.code,d.title) for d in definitions]==EXPECTED_TREE
    assert [d.position for d in definitions]==list(range(1,38))
    ids={d.code:d.id for d in definitions}
    for d in definitions:
        assert d.parent_id==ids.get(d.code.rpartition('.')[0])
        assert d.applies_to==('idare' if d.code=='SUNUS' else 'both')
    idare=client.get(f"/api/activity-sections/reports/{docs['idare'].id}").json()
    unit=client.get(f"/api/activity-sections/reports/{docs['birim:'+str(sample['department'].id)].id}").json()
    assert len(idare['sections'])==37 and len(unit['sections'])==36
    assert all(s['status']=='empty' for s in idare['sections'])
    assert len(docs)==4
    assert client.get('/activity-sections').status_code==200
    assert client.get(f"/activity-sections/reports/{docs['idare'].id}").status_code==200


@pytest.mark.parametrize('email,scope,code,allowed',[
('test@example.invalid','own','I.A',True),('test@example.invalid','other','I.A',False),
('test@example.invalid','idare','I.A',False),('strategy@example.invalid','idare','I.A',True),
('strategy@example.invalid','other','I.A',True),('test@example.invalid','own','III.A.1',False),
('finance@example.invalid','idare','III.A.1',True),('finance@example.invalid','finance','III.A.1',True),
('finance@example.invalid','idare','I.A',False),('finance@example.invalid','other','III.A.1',False),
('strategy@example.invalid','idare','III.B.2.i',False)])
def test_permissions_real_login(section_client,sample,db,email,scope,code,allowed):
    client,docs,other,finance=section_client
    scope_id={'own':'birim:'+str(sample['department'].id),'other':'birim:'+str(other.id),'finance':'birim:'+str(finance.id),'idare':'idare'}[scope]
    token=login(client,email)
    doc=docs[scope_id]
    result=client.post(f'/api/activity-sections/reports/{doc.id}/sections/{code}',headers={'X-CSRF-Token':token},json={'expected_revision':0,'blocks':[{'type':'paragraph','text':'İçerik'}],'status':'draft'})
    assert result.status_code==(200 if allowed else 403),result.text
    if allowed:
        event=db.scalar(select(ARContentEvent).where(ARContentEvent.document_id==doc.id,ARContentEvent.action=='section_save'))
        assert json.loads(event.before_json)['blocks']==[]
        assert json.loads(event.after_json)['blocks'][0]['text']=='İçerik'


def test_csrf_and_stale_edit_and_applicability(section_client):
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'strategy@example.invalid')
    response=client.post(f'/api/activity-sections/reports/{doc.id}/sections/I.A',json={'expected_revision':0,'blocks':[],'status':'draft'})
    assert response.status_code==403
    assert save(client,token,doc,status='not_applicable',reason='  ').status_code==422
    assert save(client,token,doc,status='not_applicable',reason='Bu yıl uygulanmıyor.',blocks=[]).status_code==200
    assert save(client,token,doc,revision=0).status_code==409
    assert save(client,token,doc,status='ready',blocks=[]).status_code==422
    assert save(client,token,doc,blocks=[{'type':'html','text':'<script>bad()</script>'}]).status_code==422


def test_tables_consolidate_without_turning_blank_into_zero(section_client,sample):
    client,docs,other,_=section_client;token=login(client,'strategy@example.invalid')
    own=docs['birim:'+str(sample['department'].id)];second=docs['birim:'+str(other.id)]
    rows=[{'category':'memur','count':12500},{'category':'sözleşmeli personel','count':None},{'category':'diğer','count':0}]
    assert resource(client,token,own,'employment',rows).status_code==200
    assert resource(client,token,second,'employment',[{'category':'memur','count':3}]).status_code==200
    assert resource(client,token,own,'buildings',[{'name':'Ana bina','category':'Hizmet','address':'Merkez','area':12500.23,'ownership':'mülk'}]).status_code==200
    data=client.get(f"/api/activity-sections/reports/{docs['idare'].id}").json()
    table=data['resources']['employment']
    assert table['totals']['count']=={'value':12503,'missing':1}
    assert [r['count'] for r in table['rows']]==[12500,None,0,3]
    assert table['groups'][0]['count']==12503
    assert resource(client,token,docs['idare'],'hardware',[{'category':'PC','count':10}]).status_code==403
    page=client.get(f"/activity-sections/reports/{docs['idare'].id}?code=I.C.4")
    assert page.status_code==200 and '12.503' in page.text and '1 boş değer' in page.text
    page=client.get(f"/activity-sections/reports/{docs['idare'].id}?code=I.C.1")
    assert '12.500,23' in page.text
    assert resource(client,token,own,'hardware',[{'category':'PC','count':'1'}]).status_code==422
    assert resource(client,token,own,'hardware',[{'category':'PC','count':1.5}]).status_code==422
    assert resource(client,token,own,'hardware',[{'category':'PC','count':-1}]).status_code==422
    assert resource(client,token,own,'hardware',[{'category':'PC','count':2147483648}]).status_code==422


@pytest.mark.parametrize('kind,rows',[
('education',[{'category':'Lisans','count':2}]),('gender',[{'category':'Kadın','count':0},{'category':'Erkek','count':None}]),
('vehicles',[{'category':'Binek','count':2,'ownership':'kira'}]),('hardware',[{'category':'Bilgisayar','count':4}]),
('software',[{'name':'Civensa','purpose':'Kurumsal raporlama'}])])
def test_all_resource_kinds(section_client,sample,kind,rows):
    client,docs,_,_=section_client;token=login(client,'test@example.invalid')
    doc=docs['birim:'+str(sample['department'].id)]
    response=resource(client,token,doc,kind,rows)
    assert response.status_code==200,response.text
    stored=client.get(f'/api/activity-sections/reports/{doc.id}').json()['resources'][kind]['rows']
    for expected,actual in zip(rows,stored):
        assert all(expected[k]==actual[k] for k in expected)


def test_frozen_content_and_previous_year_copy(section_client,db,sample):
    client,docs,_,_=section_client;token=login(client,'strategy@example.invalid')
    own=docs['birim:'+str(sample['department'].id)]
    assert resource(client,token,own,'employment',[{'category':'memur','count':None},{'category':'diğer','count':0}]).status_code==200
    assert resource(client,token,own,'buildings',[{'name':'Hizmet binası','category':'Bina','address':'Merkez','area':12500.23,'ownership':'mülk'}]).status_code==200
    approval=ready_and_freeze(client,token,own)
    before=client.get(f'/api/activity-sections/reports/{own.id}').json()
    assert before['frozen'] and before['sha256']==approval['sha256']
    assert save(client,token,own).status_code==409
    assert resource(client,token,own,'employment',[]).status_code==409
    freeze=db.scalar(select(ARDocumentFreeze).where(ARDocumentFreeze.document_id==own.id))
    assert '12500.23' in freeze.payload_json and '"area":"12500.23"' not in freeze.payload_json
    with pytest.raises(ValueError,match='değiştirilemez'):
        freeze.payload_json='{}';db.flush()
    db.rollback()
    period=ReportingPeriod(year=2028,status='draft');db.add(period);db.flush()
    db.add(DepartmentScope(period_id=period.id,department_id=sample['department'].id,status='required'));db.commit()
    created=client.post('/api/activity-sections/years',headers={'X-CSRF-Token':token},json={'organization_id':own.organization_id,'period_id':period.id,'copy_previous':True})
    assert created.status_code==200,created.text
    new=db.scalar(select(ARDocument).where(ARDocument.period_id==period.id,ARDocument.department_id==sample['department'].id))
    copied=client.get(f'/api/activity-sections/reports/{new.id}').json()
    sections=[s for s in copied['sections'] if s['code']!=service.CORE]
    assert all(s['status']=='draft' and s['copied_needs_review'] and s['copied_from_id']==approval['freeze_id'] for s in sections)
    assert [r['count'] for r in copied['resources']['employment']['rows']]==[None,0]
    page=client.get(f'/activity-sections/reports/{new.id}')
    assert 'Geçen yıldan kopyalandı — gözden geçirin' in page.text
    assert save(client,token,new,status='draft').status_code==200
    data=client.get(f'/api/activity-sections/reports/{new.id}').json()
    assert next(s for s in data['sections'] if s['code']=='I.A')['copied_needs_review']
    assert save(client,token,new,status='ready').status_code==200
    data=client.get(f'/api/activity-sections/reports/{new.id}').json()
    assert not next(s for s in data['sections'] if s['code']=='I.A')['copied_needs_review']
    assert client.get(f'/api/activity-sections/reports/{own.id}').json()==before


def test_frozen_idare_preserves_computed_sources(section_client,sample):
    client,docs,_,_=section_client;token=login(client,'strategy@example.invalid')
    unit=docs['birim:'+str(sample['department'].id)];idare=docs['idare']
    assert resource(client,token,unit,'hardware',[{'category':'PC','count':5}]).status_code==200
    ready_and_freeze(client,token,idare)
    before=client.get(f'/api/activity-sections/reports/{idare.id}').json()
    assert resource(client,token,unit,'hardware',[{'category':'PC','count':7}]).status_code==200
    assert client.get(f'/api/activity-sections/reports/{idare.id}').json()==before
    assert before['resources']['hardware']['totals']['count']['value']==5


def test_core_is_live_readonly_summary(section_client,db,sample):
    from test_activity_contract import actual_payload
    client,docs,_,_=section_client;token=login(client,'strategy@example.invalid')
    # Use the existing production PP/AR services; login/CSRF is still required.
    from app import activity_contract_service
    from app.models import Publication, ReportSection, Submission
    db.scalar(select(Submission)).status='approved'
    db.add(ReportSection(period_id=sample['period'].id,title='Genel Bilgiler',kind='text',content_json='{}'))
    for dep_id in (section_client[2].id,section_client[3].id):
        scope=db.scalar(select(DepartmentScope).where(DepartmentScope.department_id==dep_id))
        scope.status='excluded';scope.reason='Bu PP örneğinin dışında'
    db.commit()
    published=client.post('/report-builder/publish',data={'csrf_token':token,'period_id':sample['period'].id})
    assert published.status_code==303,published.text
    pub=db.scalar(select(Publication))
    revision=activity_contract_service.create_report_revision(db,sample['strategy'],pub.id,sample['department'].organization_id)
    db.commit()
    data=client.get(f"/api/activity-sections/reports/{docs['idare'].id}").json()
    assert data['core']['total']==1 and data['core']['verified']==0
    assert data['core']['link']==f'/activity-reports/revisions/{revision.id}'
    from app.models import ReportIndicator
    slot=db.scalar(select(ReportIndicator).where(ReportIndicator.report_revision_id==revision.id))
    result=client.post(f'/api/activity-reports/indicators/{slot.id}/actuals',headers={'X-CSRF-Token':token},json=actual_payload())
    assert result.status_code==200,result.text
    updated=client.get(f"/api/activity-sections/reports/{docs['idare'].id}").json()
    assert updated['core']['verified']==1
    assert next(s for s in updated['sections'] if s['code']==service.CORE)['status']=='ready'


def test_html_blocks_errors_filters_and_turkish_input(section_client,sample):
    client,docs,_,_=section_client;token=login(client,'test@example.invalid');doc=docs['birim:'+str(sample['department'].id)]
    text='Birinci paragraf\n\n- Bir madde\n- İkinci madde\n\n| Başlık | Değer |\n| Personel | 0 |'
    assert blocks_text(form_blocks(text))==text
    response=client.post(f'/activity-sections/reports/{doc.id}/sections/I.A',data={'csrf_token':token,'expected_revision':0,'status':'not_applicable','reason':'','text':text})
    assert response.status_code==422 and 'Birinci paragraf' in response.text and 'gerekçe' in response.text
    response=client.post(f'/activity-sections/reports/{doc.id}/sections/I.A',data={'csrf_token':token,'expected_revision':0,'status':'ready','reason':'','text':text})
    assert response.status_code==303
    response=client.post(f'/activity-sections/reports/{doc.id}/resources/buildings',data={'csrf_token':token,'expected_revision':1,'include_0':'on','name_0':'Bina','category_0':'Hizmet','address_0':'Merkez','area_0':'12.500,23','ownership_0':'mülk'})
    assert response.status_code==303,response.text
    assert client.get(f'/api/activity-sections/reports/{doc.id}').json()['resources']['buildings']['rows'][0]['area']==12500.23
    token=login(client,'strategy@example.invalid')
    page=client.get('/activity-sections?section=I.A&status=ready')
    assert 'A- Misyon ve Vizyon</a>' in page.text
    assert 'III.A.1 · 1- Bütçe Uygulama Sonuçları</a>' not in page.text


def test_frozen_rendering_keeps_definition_snapshot(section_client,db):
    client,docs,_,_=section_client;token=login(client,'strategy@example.invalid');doc=docs['idare']
    ready_and_freeze(client,token,doc)
    before=client.get(f'/api/activity-sections/reports/{doc.id}').json()
    definition=db.scalar(select(ARSectionDefinition).where(ARSectionDefinition.code=='I.A'))
    definition.code='I.X';definition.title='Gelecek tanım sürümünün başlığı';db.commit()
    assert client.get(f'/api/activity-sections/reports/{doc.id}').json()==before
    page=client.get(f'/activity-sections/reports/{doc.id}?code=I.A')
    assert page.status_code==200 and 'A- Misyon ve Vizyon' in page.text
    assert 'Gelecek tanım sürümünün başlığı' not in page.text


def test_turkish_validation_and_resource_form_retains_failed_input(section_client,sample):
    client,docs,_,_=section_client;token=login(client,'test@example.invalid');doc=docs['birim:'+str(sample['department'].id)]
    response=client.post(f'/api/activity-sections/reports/{doc.id}/sections/I.A',headers={'X-CSRF-Token':token},json={'expected_revision':'wrong','blocks':[],'status':'draft'})
    assert response.status_code==422 and 'Rapor sürümü' in response.json()['detail']
    response=client.post(f'/activity-sections/reports/{doc.id}/resources/hardware',data={'csrf_token':token,'expected_revision':0,'include_0':'on','category_0':'Korunacak cihaz','count_0':'bozuk sayı'})
    assert response.status_code==422 and 'Korunacak cihaz' in response.text and 'bozuk sayı' in response.text
    assert client.get('/activity-sections?period_id=&section=I.A&status=draft').status_code==200
