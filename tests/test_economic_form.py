"""D3: economic-grid errors stay in the form without losing input."""
from decimal import Decimal
import subprocess

import pytest
from sqlalchemy import select

from app.models import EconomicValue
from test_json_fetch import APP_JS, HARNESS, NODE

DOM = r"""
function element(tag){return {tag,children:[],hidden:true,textContent:'',
  append(child){this.children.push(child)},replaceChildren(...children){this.children=children},
  focus(){this.focused=true},scrollIntoView(){this.scrolled=true},
}}
const box=element('div'),button={disabled:false},handlers={};
const form={action:'/program/1/economic-grid',values:{period_id:'1',program_group:'service',funding_type:'outside','goods_services:2027:budget':'99,50','personnel:2027:budget':'yanlış'},
  querySelector(){return button},addEventListener(name,fn){handlers[name]=fn},
};
class FormData{constructor(form){this.values={...form.values}}get(key){return this.values[key]}}
"""
SETUP = r"""
context.document.createElement=element;
context.location.assign=url=>{context.destination=url};
const submit=()=>handlers.submit({preventDefault(){context.prevented=true}});
const messages=()=>box.children[1].children.map(item=>item.textContent);
const original={...form.values};
"""
SCENARIOS = {
    "failure_preserves_inputs": """reply(422,{detail:'Personel Giderleri / 2027: Sayı biçimi doğrulanmalı.'});await submit();assert.equal(context.prevented,true);assert.deepEqual(form.values,original);assert.equal(context.destination,undefined);assert.equal(box.hidden,false);assert.equal(box.focused,true);assert.ok(messages()[0].includes('Personel Giderleri / 2027'));assert.equal(button.disabled,false);assert.equal(sent.options.body.get('goods_services:2027:budget'),'99,50');assert.equal(sent.options.headers.get('Accept'),'application/json');assert.equal(sent.options.headers.get('X-CSRF-Token'),'test-token');""",
    "multiple_safe_errors": """reply(422,{detail:['Tutar geçersiz.','<img src=x onerror=alert(1)>']});await submit();assert.deepEqual(messages(),['Tutar geçersiz.','<img src=x onerror=alert(1)>']);assert.equal(box.children[1].children[1].innerHTML,undefined);""",
    "network_failure": """context.fetch=async()=>{throw Error('offline')};await submit();assert.match(messages()[0],/Sunucuya ulaşılamadı/);assert.deepEqual(form.values,original);assert.equal(button.disabled,false);assert.equal(context.destination,undefined);""",
    "session_failure": """reply(401,{detail:'Unauthorized'});await submit();assert.match(messages()[0],/Oturumunuz/);assert.deepEqual(form.values,original);assert.equal(context.destination,undefined);""",
    "non_json_failure": """reply(200,null,{broken:true});await submit();assert.match(messages()[0],/beklenen yanıt alınamadı/);assert.deepEqual(form.values,original);assert.equal(context.destination,undefined);""",
    "retry_success": """reply(422,{detail:'Tutar geçersiz.'});await submit();form.values['personnel:2027:budget']='15,00';reply(200,{ok:true,redirect_url:'/program/1?period_id=1&group=service&fund=outside'});await submit();assert.equal(context.destination,'/program/1?period_id=1&group=service&fund=outside');assert.equal(box.hidden,true);assert.equal(box.children.length,0);assert.equal(sent.options.body.get('personnel:2027:budget'),'15,00');""",
    "unexpected_success_is_not_confirmed": """reply(200,{unexpected:true});await submit();assert.equal(box.hidden,false);assert.match(messages()[0],/İşlem sonucu doğrulanamadı/);assert.equal(context.destination,undefined);""",
    "duplicate_submission_blocked": """let resolve;context.fetch=async()=>{calls++;return new Promise(r=>resolve=r)};const pending=submit();assert.equal(button.disabled,true);await submit();assert.equal(calls,1);resolve({ok:false,status:422,async json(){return {detail:'Hata.'}}});await pending;assert.equal(button.disabled,false);assert.equal(box.hidden,false);""",
}


@pytest.mark.skipif(not NODE, reason="Node.js is required for economic form regression tests")
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_economic_form(scenario):
    script = HARNESS.replace("const context=", DOM + "\nconst context=")
    script = script.replace("Headers,URL,", "Headers,URL,FormData,")
    script = script.replace("getElementById(id){return id==='toast'?toastElement:null}", "getElementById(id){return id==='economicGridForm'?form:id==='economicGridErrors'?box:id==='toast'?toastElement:null}")
    script = script.replace("SCENARIO", SETUP + SCENARIOS[scenario])
    result = subprocess.run([NODE, "-e", script, str(APP_JS)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_economic_grid_json_success(client, db, sample):
    response = client.post('/program/1/economic-grid', headers={'Accept':'application/json'}, data={
        'period_id':1,'program_group':'service','funding_type':'outside','goods_services:2027:budget':'12,34',
    })
    assert response.status_code == 200
    assert response.json() == {'ok':True,'redirect_url':'/program/1?period_id=1&group=service&fund=outside'}
    row = db.scalar(select(EconomicValue).where(EconomicValue.year==2027, EconomicValue.category=='goods_services', EconomicValue.funding_type=='outside'))
    assert row.amount == Decimal('12.34')


def test_economic_grid_normal_form_keeps_redirect(client):
    response = client.post('/program/1/economic-grid', data={
        'period_id':1,'program_group':'service','funding_type':'inside','goods_services:2027:budget':'123,45',
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers['location'] == '/program/1?period_id=1&group=service&fund=inside'


def test_economic_grid_json_failure_is_atomic(client, db):
    before = db.scalar(select(EconomicValue).where(EconomicValue.year==2027, EconomicValue.category=='goods_services', EconomicValue.funding_type=='inside')).amount
    response = client.post('/program/1/economic-grid', headers={'Accept':'application/json'}, data={
        'period_id':1,'program_group':'service','funding_type':'inside','goods_services:2027:budget':'99','personnel:2027:budget':'yanlış',
    })
    assert response.status_code == 422
    assert 'Personel Giderleri / 2027' in response.json()['detail']
    db.expire_all()
    after = db.scalar(select(EconomicValue).where(EconomicValue.year==2027, EconomicValue.category=='goods_services', EconomicValue.funding_type=='inside')).amount
    assert before == after


def test_economic_template_has_form_and_error_region(client):
    text = client.get('/program/1?period_id=1').text
    assert 'id="economicGridForm"' in text
    assert 'id="economicGridErrors" class="return-note" role="alert" tabindex="-1" hidden' in text
