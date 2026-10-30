"""Chromium idare release labels, reopen form and retained downloads."""
import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright, expect
from test_activity_sections import section_client
from test_ar_release_chain import release, reopen, freeze, WARNING, REASON

pytestmark=pytest.mark.postgres


def test_idare_release_history_in_chromium(release,tmp_path):
    client,_,token,doc=release
    folder=Path(os.getenv('CIVENSA_UI_SCREENSHOTS',str(tmp_path)))
    folder.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        options={'headless':True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'):options['executable_path']=os.environ['CIVENSA_CHROMIUM_PATH']
        browser=p.chromium.launch(**options)
        context=browser.new_context(viewport={'width':1366,'height':1000})
        def serve(route):
            request=route.request
            response=client.request(request.method,request.url,content=request.post_data_buffer,
                headers={'content-type':request.headers.get('content-type','')},follow_redirects=True)
            headers=dict(response.headers);headers.pop('set-cookie',None)
            route.fulfill(status=response.status_code,headers=headers,body=response.content)
        context.route('http://testserver/**',serve)
        page=context.new_page()
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(f'http://testserver/activity-sections/reports/{doc.id}')
        history=page.get_by_role('region',name='İdare sürüm geçmişi')
        expect(history).to_contain_text('Sürüm 1 · Güncel sürüm')
        form=history.locator('form')
        form.locator('[name=reason]').fill(REASON)
        form.get_by_role('button',name='Gerekçeyle yeniden aç').click()
        expect(page.get_by_role('alert')).to_contain_text(WARNING)
        expect(page.locator('[name=text]')).to_be_visible()
        for width in (1366,390):
            page.set_viewport_size({'width':width,'height':1000})
            page.screenshot(path=str(folder/f'editor-reopened-{width}.png'),full_page=True)
        assert freeze(client,token,doc).status_code==200
        for width in (1366,390):
            page.set_viewport_size({'width':width,'height':1000})
            page.goto(f'http://testserver/activity-sections/reports/{doc.id}')
            history=page.get_by_role('region',name='İdare sürüm geçmişi')
            expect(history).to_contain_text('Sürüm 2 · Güncel sürüm')
            expect(history).to_contain_text('Önceki sürüm — Sürüm 2 ile değiştirildi')
            expect(history).to_contain_text(REASON)
            expect(history).to_contain_text('Strateji')
            expect(history).to_contain_text('TSİ')
            expect(history.get_by_role('link',name='Sürüm 1 JSON indir')).to_have_attribute('href',f'/activity-sections/reports/{doc.id}/export.json?version=1')
            page.screenshot(path=str(folder/f'editor-release2-{width}.png'),full_page=True)
            page.goto('http://testserver/activity-sections?section=I.A')
            expect(page.get_by_text('Sürüm 2 · Güncel sürüm',exact=True)).to_be_visible()
            expect(page.get_by_text('Önceki sürüm — Sürüm 2 ile değiştirildi',exact=False)).to_be_visible()
            page.screenshot(path=str(folder/f'list-release2-{width}.png'),full_page=True)
        assert not errors
        context.close();browser.close()
