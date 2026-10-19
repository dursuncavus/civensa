"""Browser acceptance and review screenshots for III-A entry, preview and checks."""
import os
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright, expect
from test_activity_sections import section_client, login
from test_activity_financial import expenditure, programme, post, preview

pytestmark=pytest.mark.postgres


def test_financial_entry_preview_and_completeness_browser(section_client,sample,tmp_path):
    client,docs,_,_=section_client;doc=docs['idare'];token=login(client,'strategy@example.invalid')
    assert post(client,token,doc,'/budget/expenditure',rows=[expenditure(sample['department'].id)]).status_code==200
    assert post(client,token,doc,'/budget/programme',rows=[programme(sample,initial=12000.23)]).status_code==200
    assert post(client,token,doc,'/policy',lower_rate=85,upper_rate=110).status_code==200
    # The screenshot includes both a changed value and a row error.
    first=preview(client,token,doc,'revenue',[{'economic_code':'01','estimate':12500.23,'actual':10000,'refunds':0}]).json()
    assert post(client,token,doc,f'/imports/{first["id"]}/apply').status_code==200
    pending=preview(client,token,doc,'revenue',[{'economic_code':'01','estimate':12500.23,'actual':11000,'refunds':0},
        {'economic_code':'99','estimate':'hatalı','actual':None,'refunds':0}]).json()
    folder=Path(os.getenv('CIVENSA_UI_SCREENSHOTS',str(tmp_path)));folder.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        options={'headless':True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'):options['executable_path']=os.environ['CIVENSA_CHROMIUM_PATH']
        browser=p.chromium.launch(**options);context=browser.new_context(viewport={'width':1600,'height':1100})
        errors=[]
        def serve(route):
            req=route.request
            response=client.request(req.method,req.url,content=req.post_data_buffer,
                headers={'content-type':req.headers.get('content-type','')},follow_redirects=False)
            headers=dict(response.headers);headers.pop('set-cookie',None)
            route.fulfill(status=response.status_code,headers=headers,body=response.content)
        context.route('http://testserver/**',serve)
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://testserver/activity-sections/reports/{doc.id}?code=III.A.1')
        form=page.locator('form[action$="/financial/budget/expenditure"]')
        expect(form.locator('[name=initial_0]')).to_have_value('12.500,23')
        expect(form).to_contain_text('PP Bütçesi (salt okunur)')
        form.get_by_role('button',name='Satır ekle',exact=True).click()
        assert form.locator('[name=initial_4]').count()==1
        page.get_by_role('heading',name='Bütçe Uygulama Sonuçları',exact=True).evaluate('(el)=>{el.scrollIntoView();window.scrollBy(0,-20)}')
        page.screenshot(path=str(folder/'financial-entry.png'))
        page.goto(f'http://testserver/activity-sections/reports/{doc.id}/financial/imports/{pending["id"]}')
        expect(page.get_by_role('alert')).to_contain_text('Bilinmeyen ekonomik kod')
        expect(page.locator('.ar-table')).to_contain_text('10.000')
        expect(page.locator('.ar-table')).to_contain_text('11.000')
        assert page.get_by_role('button',name='Farkları onayla ve içe aktarmayı uygula').count()==0
        page.screenshot(path=str(folder/'financial-import-preview.png'))
        page.goto('http://testserver/activity-sections?section=III.A.1')
        expect(page.locator('.ar-table')).to_contain_text('Sapma açıklaması gerekli')
        expect(page.locator('.ar-table')).to_contain_text('fark 500')
        page.get_by_role('heading',name='Tamamlanma görünümü').evaluate('(el)=>{el.scrollIntoView();window.scrollBy(0,-20)}')
        page.screenshot(path=str(folder/'financial-completeness.png'))
        assert not errors,errors
        context.close();browser.close()
