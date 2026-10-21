"""CIV-064: real PP form recovery and the common HTTP error contract."""
import ast
from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.main import app, require_user
from app.models import Activity, AuditLog, Indicator, Publication, ReportCard, ReportSection
from app.pp_errors import install

pytestmark = pytest.mark.postgres


class Forms(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.forms = []
        self.current = None
        self.textarea = None
        self.select = None
        self.option = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.current = {'action': attrs.get('action'), 'fields': {}, 'invalid': set()}
            self.forms.append(self.current)
        if self.current is None:
            return
        name = attrs.get('name')
        if attrs.get('aria-invalid') == 'true':
            self.current['invalid'].add(name)
        if tag == 'input':
            self.current['fields'][name] = attrs.get('value', '')
        if tag == 'textarea':
            self.textarea = name
            self.current['fields'][name] = ''
        if tag == 'select':
            self.select = name
        if tag == 'option' and 'selected' in attrs:
            self.current['fields'].setdefault(self.select, [])
            self.current['fields'][self.select].append(attrs.get('value'))

    def handle_data(self, value):
        if self.textarea and self.current:
            if not self.current['fields'][self.textarea] and value.startswith('\n'):
                value=value[1:]  # Browser textarea parsing ignores the initial newline.
            self.current['fields'][self.textarea] += value

    def handle_endtag(self, tag):
        if tag == 'form': self.current = None
        if tag == 'textarea': self.textarea = None
        if tag == 'select': self.select = None


def form(response, action, **identity):
    assert response.status_code == 422, response.text
    assert response.headers['content-type'].startswith('text/html')
    assert 'location' not in response.headers
    matches = [f for f in Forms(response.text).forms if f['action'] == action and all(
        f['fields'].get(k) == (str(v) if v is not None else None) for k, v in identity.items())]
    assert len(matches) == 1, matches
    return matches[0]


def strategy(sample):
    app.dependency_overrides[require_user] = lambda: sample['strategy']


@pytest.mark.parametrize('raw', ['yanlış', '-1', '1,2,3'])
def test_finance_retains_every_attempt_and_is_atomic(client, db, sample, raw):
    path = '/program/1/finance/1'
    before = [(v.id, v.amount) for v in sample['activity'].cost_values]
    data = {'period_id': '1', 'cost_2027_budget_inside': raw, 'cost_2027_budget_outside': '0',
            'cost_2028_forecast_inside': '', 'cost_2028_forecast_outside': ''}
    result = form(client.post(path, data=data), path)
    assert all(result['fields'][key] == value for key, value in data.items())
    assert 'cost_2027_budget_inside' in result['invalid']
    assert 'Finansman tutarı geçersiz' in client.post(path, data=data).text
    db.expire_all()
    assert [(v.id, v.amount) for v in sample['activity'].cost_values] == before


def test_finance_partial_pair_names_missing_field(client, sample):
    path = '/program/1/finance/1'
    result = form(client.post(path, data={'period_id':1, 'cost_2027_budget_inside':'',
        'cost_2027_budget_outside':'12,50'}), path)
    assert result['fields']['cost_2027_budget_outside'] == '12,50'
    assert 'cost_2027_budget_inside' in result['invalid']


@pytest.mark.parametrize('group,fund', [('service','inside'), ('management','outside')])
def test_economic_grid_retains_bad_number_zero_blank_and_selection(client, sample, group, fund):
    path = '/program/1/economic-grid'
    data = {'period_id':'1', 'program_group':group, 'funding_type':fund,
        'goods_services:2027:budget':'yanlış', 'personnel:2027:budget':'0',
        'capital:2028:forecast':'', 'capital:2029:forecast':'12.345,67'}
    response = client.post(path, data=data)
    result = form(response, path)
    assert all(result['fields'][key] == value for key, value in data.items())
    assert 'goods_services:2027:budget' in result['invalid']
    assert 'Türkçe sayı biçiminde' in response.text


def test_cards_preserve_new_and_existing_forms_without_cross_contamination(client, db, sample):
    path = '/program/1/cards'
    before = db.scalar(select(ReportCard)).goal
    data = {'period_id':'1', 'id':'1', 'subprogram_id':'999', 'position':'sıra?',
        'goal':'  Denenen hedef <script>alert(1)</script> & açıklama  ', 'source_title':'Taslak başlık'}
    response = client.post(path, data=data)
    result = form(response, path, id=1)
    assert result['fields']['goal'] == data['goal']
    assert result['fields']['position'] == 'sıra?'
    assert result['fields']['subprogram_id'] == ['999']
    assert 'subprogram_id' in result['invalid']
    assert '<script>alert(1)</script>' not in response.text
    assert len([f for f in Forms(response.text).forms if f['action']==path and f['fields'].get('goal')==data['goal']]) == 1
    db.refresh(sample['card']); assert sample['card'].goal == before
    data.pop('id')
    assert form(client.post(path, data=data), path, id=None)['fields']['goal'] == data['goal']
    assert len(db.scalars(select(ReportCard)).all()) == 1


def test_assign_rolls_back_earlier_mutations_and_retains_values(client, db, sample):
    path='/program/1/assign'
    data={'period_id':1, 'kind':'activity', 'record_id':1, 'card_id':1, 'position':'yanlış', 'code':'  F-99  '}
    result=form(client.post(path, data=data), path, kind='activity', record_id=1)
    assert result['fields']['position']=='yanlış' and result['fields']['code']==data['code']
    assert result['fields']['card_id']==['1'] and 'position' in result['invalid']
    db.refresh(sample['activity']); assert sample['activity'].code != 'F-99'


def test_indicator_retains_name_unit_and_card(client, db, sample):
    path='/program/1/indicator'
    data={'period_id':1, 'card_id':1, 'name':'  Yeni gösterge  ', 'unit':'x'*51}
    result=form(client.post(path,data=data),path)
    assert result['fields']['name']==data['name'] and result['fields']['unit']==data['unit']
    assert result['fields']['card_id']==['1'] and 'unit' in result['invalid']
    assert len(db.scalars(select(Indicator)).all())==1


@pytest.mark.parametrize('existing', [False, True])
def test_section_retains_title_kind_placement_and_table_content(client, db, sample, existing):
    strategy(sample)
    data={'period_id':1,'title':'  Kurumsal bilgi  ','position':'7','placement':'after','kind':'table',
        'content':'ilk\tikinci\nüçüncü'}
    if existing:
        obj=ReportSection(period_id=1,title='Eski başlık',kind='text',content_json='{"text":"Eski metin"}')
        db.add(obj);db.commit();data['id']=str(obj.id)
    path='/report-builder/section'
    result=form(client.post(path,data=data),path,**({'id':data['id']} if existing else {}))
    assert result['fields']['content']==data['content'] and result['fields']['title']==data['title']
    assert result['fields']['kind']==['table'] and result['fields']['placement']==['after']
    assert 'content' in result['invalid']
    if existing:
        db.refresh(obj);assert obj.title=='Eski başlık'
    else: assert not db.scalars(select(ReportSection)).all()


def test_publish_rerenders_builder_in_same_period_without_publication(client, db, sample):
    strategy(sample)
    path='/report-builder/publish'
    response=client.post(path,data={'period_id':1})
    result=form(response,path)
    assert result['fields']['period_id']=='1'
    assert 'Nihai yayın oluşturulamadı' in response.text and 'onay' in response.text
    assert not db.scalars(select(Publication)).all()


@pytest.mark.parametrize('path,data,field', [
    ('/program/1/finance/1',{'cost_2027_budget_inside':'yanlış'},'cost_2027_budget_inside'),
    ('/program/1/economic-grid',{'program_group':'service','funding_type':'inside','personnel:2027:budget':'yanlış'},'personnel:2027:budget'),
    ('/program/1/cards',{'subprogram_id':999},'subprogram_id'),
    ('/program/1/assign',{'card_id':999},'card_id'),
    ('/program/1/indicator',{'card_id':1,'name':'Deneme','unit':''},'unit'),
    ('/report-builder/section',{'title':'Deneme','content':''},'content'),
    ('/report-builder/publish',{},'publish'),
])
def test_json_errors_have_field_contract(client, sample, path, data, field):
    if path.startswith('/report-builder'): strategy(sample)
    response=client.post(path,data={'period_id':1,**data},headers={'Accept':'application/json'})
    assert response.status_code==422,response.text
    body=response.json()
    assert isinstance(body['detail'],str) and body['detail']
    assert body['errors'][0]['field']==field and body['errors'][0]['message']


@pytest.mark.parametrize('status', [401,403,404,405,422])
@pytest.mark.parametrize('accept', ['application/json','text/html'])
def test_framework_defaults_are_turkish_and_do_not_leak_internals(status, accept):
    # Isolated FastAPI app exercises real Starlette defaults and Pydantic validation.
    api=FastAPI()
    install(api,Jinja2Templates(directory=Path(__file__).parents[1]/'app/templates'))
    @api.get('/program/failure')
    def fail(): raise HTTPException(status)
    @api.get('/program/number/{department_id}')
    def number(department_id:int): return department_id
    client=TestClient(api)
    if status==404: response=client.get('/program/missing',headers={'Accept':accept})
    elif status==405: response=client.post('/program/failure',headers={'Accept':accept})
    elif status==422: response=client.get('/program/number/private-input',headers={'Accept':accept})
    else: response=client.get('/program/failure',headers={'Accept':accept})
    assert response.status_code==status
    assert all(raw not in response.text for raw in ['Not Found','Forbidden','Unauthorized','Method Not Allowed','Unprocessable','private-input','int_parsing'])
    if accept=='application/json':
        assert response.json()['detail'] and response.json()['errors'][0]['field']
    else: assert '<html lang="tr">' in response.text
    if status==405: assert response.headers['allow']=='GET'


def test_pp_route_error_response_scan(client, sample):
    strategy(sample)
    for method,path,data in [
        ('get','/program/999?period_id=1',None),
        ('get','/program/wrong?period_id=1',None),
        ('get','/program/1?period_id=1&group=wrong',None),
        ('post','/program/1/cards',{'period_id':1,'id':999}),
        ('post','/report-builder/section',{'period_id':1,'id':999}),
        ('get','/publications/999.json',None),
        ('delete','/program/1',None),
    ]:
        response=client.request(method,path,data=data,headers={'Accept':'application/json'})
        assert response.status_code in {403,404,405,422}
        assert isinstance(response.json()['detail'],str) and response.json()['detail'].strip()
        assert response.json()['errors']
    tree=ast.parse((Path(__file__).parents[1]/'app/program_routes.py').read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='HTTPException':
            assert len(node.args)>1 or any(k.arg=='detail' for k in node.keywords),node.lineno


@pytest.mark.parametrize('other_blocker', [False,True])
def test_draft_removal_fix_hint_only_when_values_are_sole_blocker(client, db, sample, other_blocker):
    indicator=sample['indicator']
    if other_blocker: indicator.status='submitted'
    db.commit()
    response=client.post('/program/1/indicator/1/remove',data={'period_id':1},headers={'Accept':'application/json'})
    assert response.status_code==409,response.text
    hint='Önce göstergenin değerlerini silip kaydedin, sonra kaldırın.'
    assert (hint in response.json()['detail']) is not other_blocker
    assert db.get(Indicator,indicator.id)


def test_additional_pp_forms_retain_attempted_fields(client, sample):
    path='/program/1/economic'
    data={'period_id':1,'year':'2027','value_kind':'budget','category':'goods_services',
        'program_group':'service','funding_type':'inside','amount':'bozuk'}
    result=form(client.post(path,data=data),path)
    assert result['fields']['amount']=='bozuk' and 'amount' in result['invalid']
    strategy(sample)
    path='/report-builder/scope'
    data={'period_id':1,'department_id':1,'status':'zero','reason':'','display_name':'Denenen birim','position':'7'}
    result=form(client.post(path,data=data),path,department_id=1)
    assert result['fields']['display_name']=='Denenen birim' and result['fields']['status']==['zero']
    assert 'reason' in result['invalid']
    path='/report-builder/catalogue'
    data={'period_id':1,'program_code':'1','program_name':'Denenen program', 'subprogram_code':'1.1',
        'subprogram_name':'Alt','code':'Yeni kod','name':'','department_ids':['1']}
    result=form(client.post(path,data=data),path,id=None)
    assert result['fields']['program_name']=='Denenen program' and result['fields']['department_ids']==['1']
    assert 'name' in result['invalid']


def test_section_upload_failure_retains_caption_and_requests_reselection(client, sample):
    strategy(sample)
    path='/report-builder/section'
    response=client.post(path,data={'period_id':1,'kind':'image','title':'Görsel başlığı',
        'content':'  Denenen açıklama  ','placement':'after'},files={'image':('broken.png',b'broken','image/png')})
    result=form(response,path)
    assert result['fields']['content']=='  Denenen açıklama  '
    assert result['fields']['kind']==['image'] and 'image' in result['invalid']
    assert 'yeniden seç' in response.text


def test_invalid_number_stays_visible_in_browser_and_retry_saves(client, db, sample):
    from playwright.sync_api import sync_playwright
    import os
    path='/program/1/cards'
    data={'period_id':1,'id':1,'subprogram_id':1,'position':'sıra?','goal':'\n  Taslak hedef  '}
    response=client.post(path,data=data)
    assert response.status_code==422
    with sync_playwright() as playwright:
        options={'headless':True,'args':['--no-sandbox']}
        if os.getenv('CIVENSA_CHROMIUM_PATH'): options['executable_path']=os.environ['CIVENSA_CHROMIUM_PATH']
        browser=playwright.chromium.launch(**options)
        page=browser.new_page()
        page.set_content(response.text)
        saved_form=page.locator('form[action="/program/1/cards"]').filter(has=page.locator('input[name="id"][value="1"]'))
        assert saved_form.locator('[name="position"]').input_value()=='sıra?'
        assert saved_form.locator('[name="position"]').get_attribute('aria-invalid')=='true'
        assert saved_form.locator('[name="goal"]').input_value()=='\n  Taslak hedef  '
        assert saved_form.locator('.field-error').is_visible()
        browser.close()
    data['position']='7'
    assert client.post(path,data=data,follow_redirects=False).status_code==303
    db.refresh(sample['card']); assert sample['card'].position==7 and sample['card'].goal=='Taslak hedef'


@pytest.mark.parametrize('period_data', [{}, {'period_id':'bozuk'}, {'period_id':'2'}])
def test_period_guard_still_422_and_retains_attempts_before_endpoint(client, db, sample, period_data):
    path='/program/1/cards'
    data={'subprogram_id':1,'goal':'  Dönem hatasında saklanacak hedef  ','source_title':'Başlık',**period_data}
    before=len(db.scalars(select(ReportCard)).all())
    response=client.post(path+'?period_id=1' if period_data else path,data=data,headers={'Accept':'text/html'})
    result=form(response,path,id=None)
    assert result['fields']['goal']==data['goal'] and result['fields']['source_title']=='Başlık'
    assert 'period_id' in result['invalid']
    assert len(db.scalars(select(ReportCard)).all())==before
    if period_data:
        assert result['fields']['period_id']==[period_data['period_id']]
    assert 'Bu ekranda görünen dönem' in response.text
    # The rejected request did not write; explicitly selecting the displayed period can retry.
    data['period_id']=1
    assert client.post(path,data=data,follow_redirects=False).status_code==303
    assert len(db.scalars(select(ReportCard)).all())==before+1


def test_inactive_scope_row_disappearing_from_list_keeps_form_and_error(client, db, sample):
    from app.models import ReportingPeriod
    strategy(sample)
    sample['department'].is_active=False
    period=ReportingPeriod(year=2028)
    db.add(period);db.commit()
    path='/report-builder/scope'
    data={'period_id':period.id,'department_id':1,'status':'required',
        'display_name':'  Denenen birim adı  ','reason':'Denenen açıklama','position':'3'}
    response=client.post(path,data=data)
    result=form(response,path,department_id=1)
    assert 'pasif' in response.text and 'Kurum Yapısı' in response.text
    assert result['fields']['display_name']==data['display_name']
    assert result['fields']['reason']==data['reason']
