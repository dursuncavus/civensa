"""Browser acceptance: safe rich content, resource input and completeness filters."""
import os
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright, expect
from test_activity_sections import section_client, login, resource, save

pytestmark=pytest.mark.postgres


def test_editor_resource_and_completeness_in_browser(section_client,sample,tmp_path):
    client,docs,_,_=section_client
    token=login(client,'strategy@example.invalid')
    own=docs['birim:'+str(sample['department'].id)]
    assert resource(client,token,own,'employment',[{'category':'memur','count':12500},
        {'category':'sözleşmeli personel','count':None},{'category':'diğer','count':0}]).status_code==200
    assert save(client,token,own,'I.A',status='draft',blocks=[{'type':'paragraph','text':'2027 yılında erişilebilir ve güvenilir belediye hizmetleri sunuyoruz.'},
        {'type':'bullets','items':['Vatandaş odaklı hizmet','Kaynakların verimli kullanımı']},
        {'type':'table','rows':[['İlke','Yaklaşım'],['Şeffaflık','Düzenli raporlama']]}]).status_code==200
    folder=Path(os.getenv('CIVENSA_UI_SCREENSHOTS',str(tmp_path)));folder.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        options={'headless':True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'):options['executable_path']=os.environ['CIVENSA_CHROMIUM_PATH']
        browser=p.chromium.launch(**options)
        context=browser.new_context(viewport={'width':1440,'height':1060})
        errors=[]
        def serve(route):
            request=route.request
            response=client.request(request.method,request.url,content=request.post_data_buffer,
                headers={'content-type':request.headers.get('content-type','')},follow_redirects=False)
            headers=dict(response.headers);headers.pop('set-cookie',None)
            route.fulfill(status=response.status_code,headers=headers,body=response.content)
        context.route('http://testserver/**',serve)
        page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(f'http://testserver/activity-sections/reports/{own.id}?code=I.A')
        expect(page.locator('[data-ar-preview]')).to_contain_text('Vatandaş odaklı hizmet')
        assert page.locator('[data-ar-preview] table tr').count()==2
        page.screenshot(path=str(folder/'section-editor.png'))
        page.locator('[name=text]').fill('<script>window.bad=true</script>\n\n- Güvenli metin')
        expect(page.locator('[data-ar-preview]')).to_contain_text('<script>window.bad=true</script>')
        assert page.locator('[data-ar-preview] script').count()==0
        # Leaving unsaved input asks the user; declining keeps the draft.
        page.once('dialog',lambda dialog:dialog.dismiss())
        page.get_by_role('link',name='4- İnsan Kaynakları',exact=False).click(no_wait_after=True)
        assert 'code=I.A' in page.url
        page.once('dialog',lambda dialog:dialog.accept())
        page.get_by_role('link',name='4- İnsan Kaynakları',exact=False).click()
        expect(page.get_by_role('heading',name='İstihdam Türüne Göre Personel',exact=True)).to_be_visible()
        table_form=page.locator('form[action$="resources/employment"]')
        assert table_form.locator('[name=count_0]').input_value()=='12.500'
        assert table_form.locator('[name=count_1]').input_value()==''
        assert table_form.locator('[name=count_2]').input_value()=='0'
        table_form.get_by_role('button',name='Satır ekle',exact=True).click()
        assert table_form.locator('[name=count_6]').count()==1
        page.get_by_role('heading',name='İstihdam Türüne Göre Personel',exact=True).evaluate('(el) => { el.scrollIntoView(); window.scrollBy(0,-30); }')
        page.screenshot(path=str(folder/'resource-table.png'))
        page.goto('http://testserver/activity-sections?section=I.A')
        expect(page.locator('.ar-table tbody tr')).to_have_count(4)
        page.screenshot(path=str(folder/'completeness-view.png'))
        page.locator('select[name=status]').select_option('draft')
        page.get_by_role('button',name='Filtrele',exact=True).click()
        expect(page.locator('.ar-table tbody tr')).to_have_count(1)
        assert not errors,errors
        context.close();browser.close()
