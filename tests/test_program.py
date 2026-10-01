from decimal import Decimal
import io,json,hashlib
import pytest
from sqlalchemy import select,func
from app.models import *
from app.numbers import parse_number,source_cell,format_number
from app.program_service import validate_department,department_snapshot,book_snapshot,save_activity_costs
from app.book_export import blocks,export_book

@pytest.mark.parametrize('raw,expected',[('1,75','1.75'),('12.345,67','12345.67'),('1.5 Mn','1500000'),('3500 İçerik','3500'),('0','0'),('',None),('—',None),(Decimal('1.234'),'1.234')])
def test_exact_numbers(raw,expected):assert parse_number(raw)==(Decimal(expected) if expected else None)

@pytest.mark.parametrize('raw',['1,2,3','tanımsız 45','1.23.4','NaN','Infinity','1e309'])
def test_no_digit_stripping(raw):
    with pytest.raises(ValueError):parse_number(raw)

def test_source_ambiguity():
    assert source_cell('111,001')['state']=='needs_review'
    assert source_cell('111,001')['raw_text']=='111,001'
    assert format_number(Decimal('1.75'))=='1,75'
    assert format_number(None)=='—'
    assert source_cell(0)['raw_text']=='0'

def test_shared_card_metadata_and_costs(db,sample):
    c=sample['card'];d=sample['department'];p=sample['period']
    db.add(ReportCard(period_id=p.id,department_id=d.id,subprogram_id=c.subprogram_id,source_title='2027/2',goal='İkinci hedef'));db.commit()
    snap=department_snapshot(db,p.id,d.id)
    assert [x['goal'] for x in snap['cards']]==['Birinci hedef','İkinci hedef']
    content=blocks({'period':2027,'departments':[snap]})
    assert sum(1 for kind,text in content if kind=='heading' and text=='Faaliyetler ve Maliyetler')==1
    assert len(snap['activities'])==1

def test_validation_exact_and_missing(db,sample):
    p=sample['period'];d=sample['department']
    assert validate_department(db,p.id,d.id)[0]==[]
    row=db.scalar(select(EconomicValue).where(EconomicValue.year==2027,EconomicValue.category=='goods_services'));row.amount=Decimal('123.46');db.commit()
    assert any('uyuşmuyor' in e for e in validate_department(db,p.id,d.id)[0])
    row.amount=Decimal('123.45')
    missing=db.scalar(select(ActivityCostValue).where(ActivityCostValue.year==2028,ActivityCostValue.funding_type=='outside'));db.delete(missing);db.commit();db.expire_all()
    assert any('2028' in e and 'eksik' in e for e in validate_department(db,p.id,d.id)[0])

def test_zero_and_blank_not_equivalent(db,sample):
    a=sample['activity'];save_activity_costs(db,a,2027,{'cost_2027_budget_inside':'','cost_2027_budget_outside':''});db.commit();db.expire_all()
    assert not [v for v in a.cost_values if v.year==2027]
    save_activity_costs(db,a,2027,{'cost_2027_budget_inside':'0','cost_2027_budget_outside':'0'});db.commit();db.expire_all()
    assert len([v for v in a.cost_values if v.year==2027 and v.amount==0])==3

def test_finance_rejects_partial_and_total_only(db,sample):
    from fastapi import HTTPException
    with pytest.raises(HTTPException):save_activity_costs(db,sample['activity'],2027,{'cost_2026_budget_inside':'1'})
    with pytest.raises(HTTPException):save_activity_costs(db,sample['activity'],2027,{'cost_2027_budget':'200'})

def test_warning_does_not_change_unit(db,sample):
    sample['indicator'].unit='Oran (%)';db.commit()
    errors,warnings=validate_department(db,sample['period'].id,sample['department'].id)
    assert not errors and warnings
    assert sample['indicator'].unit=='Oran (%)'

def test_locked_and_wrong_department(client,db,sample):
    a=sample['activity'];d=sample['department'];p=sample['period'];sub=db.scalar(select(Submission));sub.status='approved';db.commit()
    assert client.post(f'/program/{d.id}/assign',data={'period_id':p.id,'kind':'activity','record_id':a.id,'card_id':sample['card'].id}).status_code==409
    other=Department(organization_id=d.organization_id,name='Başka');db.add(other);db.commit()
    assert client.get(f'/program/{other.id}?period_id={p.id}').status_code==403

def test_new_period_has_no_fake_zero(client,db,sample):
    from app.main import app,require_user
    app.dependency_overrides[require_user]=lambda:sample['strategy']
    r=client.post('/api/periods',json={'year':2028,'base_period_id':sample['period'].id});assert r.status_code==200,r.text
    pid=r.json()['id'];ids=db.scalars(select(Indicator.id).where(Indicator.period_id==pid)).all()
    assert ids and not db.scalar(select(func.count()).select_from(IndicatorValue).where(IndicatorValue.indicator_id.in_(ids)))
    aids=db.scalars(select(Activity.id).where(Activity.period_id==pid)).all()
    assert aids and not db.scalar(select(func.count()).select_from(ActivityCostValue).where(ActivityCostValue.activity_id.in_(aids)))

def test_templates_render(client,db,sample):
    assert client.get('/program/1?period_id=1').status_code==200
    assert client.get('/department/1').status_code==200
    from app.main import app,require_user
    app.dependency_overrides[require_user]=lambda:sample['strategy']
    assert client.get('/report-builder').status_code==200

def test_exports_same_content_and_decimals(db,sample,tmp_path):
    from docx import Document
    from pypdf import PdfReader
    snap=book_snapshot(db,sample['period'].id)
    docx,_=export_book(snap,'docx');pdf,_=export_book(snap,'pdf')
    doc=Document(io.BytesIO(docx));text='\n'.join(c.text for t in doc.tables for row in t.rows for c in row.cells)
    pdfdoc=PdfReader(io.BytesIO(pdf));pdftext='\n'.join(p.extract_text() for p in pdfdoc.pages)
    for target in [text,pdftext]:
        for expected in ['1,75','133,50','2025','2029','Resmî faaliyet']:assert expected in target
    assert len(pdfdoc.pages)>0

def test_publication_is_immutable(client,db,sample):
    from app.main import app,require_user
    app.dependency_overrides[require_user]=lambda:sample['strategy']
    sub=db.scalar(select(Submission));sub.status='approved'
    db.add(ReportSection(period_id=1,title='Genel Bilgiler',kind='text',content_json='{"text":"Onaylı içerik"}'));db.commit()
    r=client.post('/report-builder/publish',data={'period_id':1},follow_redirects=False);assert r.status_code==303,r.text
    pub=db.scalar(select(Publication));before=pub.snapshot_json
    sample['card'].goal='Sonraki değişiklik';db.commit()
    r=client.get(f'/publications/{pub.id}.json');assert r.status_code==200 and r.text==before
    assert 'Sonraki değişiklik' not in r.text
    pub.snapshot_json+=' ';db.commit()
    assert client.get(f'/publications/{pub.id}.pdf').status_code==409

def test_image_upload_and_csrf(db,sample):
    import base64
    from itsdangerous import TimestampSigner
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import get_db
    from app.config import session_secret
    from PIL import Image
    def database():yield db
    app.dependency_overrides[get_db]=database
    try:
        client=TestClient(app)
        cookie=TimestampSigner(session_secret()).sign(base64.b64encode(json.dumps({'user_id':sample['strategy'].id,'csrf_token':'test-token'}).encode())).decode()
        client.cookies.set('session',cookie)
        content=io.BytesIO();Image.new('RGB',(100,50),'white').save(content,format='PNG')
        data={'period_id':1,'kind':'image','title':'Kaynak Görsel','content':'Açıklama'}
        denied=client.post('/report-builder/section',data=data,files={'image':('image.png',content.getvalue(),'image/png')})
        assert denied.status_code==403
        data['csrf_token']='test-token'
        ok=client.post('/report-builder/section',data=data,files={'image':('image.png',content.getvalue(),'image/png')},follow_redirects=False)
        assert ok.status_code==303,ok.text
        section=db.scalar(select(ReportSection));assert json.loads(section.content_json)['caption']=='Açıklama'
        bad=client.post('/report-builder/section',data=data,files={'image':('image.png',b'not an image','image/png')})
        assert bad.status_code==422
    finally:app.dependency_overrides.clear()

def test_import_unclear_source_survives(db,sample):
    from app.import_service import _serialize_department_state
    i=sample['indicator'];v=db.scalar(select(IndicatorValue));v.raw_text='111,001';v.state='needs_review';v.value=None;db.commit()
    snap=_serialize_department_state(db,1,1)
    assert snap['indicators'][0]['values'][0]['raw_text']=='111,001'
    assert snap['activities'][0]['card_id']==sample['card'].id
    # Serialization is the rollback fingerprint, so source metadata edits must change it.
    from app.serialization import json_dumps
    before=json_dumps(snap,sort_keys=True)
    v.raw_text='111,002';db.commit()
    assert json_dumps(_serialize_department_state(db,1,1),sort_keys=True)!=before

def test_malformed_and_cross_period_card_rejected(client,db,sample):
    period=ReportingPeriod(year=2030,status='draft');db.add(period);db.flush()
    program=Program(period_id=period.id,name='Başka');db.add(program);db.flush()
    sp=SubProgram(period_id=period.id,program_id=program.id,name='Başka');db.add(sp);db.commit()
    assert client.post('/program/1/cards',data={'period_id':1,'subprogram_id':sp.id}).status_code==422
    assert client.post('/program/1/cards',data={'period_id':1,'subprogram_id':sample['subprogram'].id,'id':999}).status_code==404

def test_unrelated_edit_keeps_source_review(client,db,sample):
    v=db.scalar(select(IndicatorValue));v.value=None;v.raw_text='111,001';v.state='needs_review';db.commit()
    r=client.post(f'/api/indicators/{sample["indicator"].id}/save',json={'name':'Düzeltilmiş ad','value_2027_target':''})
    assert r.status_code==200
    db.refresh(v);assert v.raw_text=='111,001' and v.state=='needs_review' and v.value is None

def test_economic_grid_atomic_on_bad_cell(client,db,sample):
    before=db.scalar(select(EconomicValue).where(EconomicValue.year==2027,EconomicValue.category=='goods_services',EconomicValue.funding_type=='inside')).amount
    r=client.post('/program/1/economic-grid',data={'period_id':1,'program_group':'service','funding_type':'inside','goods_services:2027:budget':'99','personnel:2027:budget':'yanlış'})
    assert r.status_code==422
    db.expire_all()
    after=db.scalar(select(EconomicValue).where(EconomicValue.year==2027,EconomicValue.category=='goods_services',EconomicValue.funding_type=='inside')).amount
    assert before==after

def test_missing_economic_zero_is_not_complete(db,sample):
    row=db.scalar(select(EconomicValue).where(EconomicValue.year==2027,EconomicValue.category=='lending',EconomicValue.funding_type=='outside'))
    assert row.amount==0;db.delete(row);db.commit()
    assert any('ekonomik gider hücresi eksik' in e for e in validate_department(db,1,1)[0])
