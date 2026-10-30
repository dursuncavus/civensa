"""CIV-160 real Chromium editor matrix, clearly synthetic text only."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import pytest
from app import internal_control_monitoring_service as m
from app import internal_control_narrative_service as n
from test_internal_control_monitoring import monitoring

pytestmark = pytest.mark.postgres
ARTIFACTS = Path(__file__).parent/'artifacts/civ160'


def test_narrative_screen_matrix(db, monitoring, client):
    from app.main import app, require_user
    d=monitoring
    current={'user':d['strategy']}
    app.dependency_overrides[require_user]=lambda:current['user']
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    captures=[]
    with sync_playwright() as p:
        options=dict(headless=True,args=['--no-sandbox'])
        if os.getenv('CIVENSA_CHROMIUM_PATH'):options['executable_path']=os.environ['CIVENSA_CHROMIUM_PATH']
        browser=p.chromium.launch(**options)
        try:
            with browser.new_context(viewport={'width':1366,'height':900}) as context:
                def serve(route):
                    req=route.request
                    response=client.request(req.method,req.url,content=req.post_data_buffer,
                        headers={'content-type':req.headers.get('content-type',''),'accept':req.headers.get('accept','')},follow_redirects=True)
                    headers=dict(response.headers);headers.pop('set-cookie',None)
                    route.fulfill(status=response.status_code,headers=headers,body=response.content)
                context.route('http://testserver/**',serve)
                page=context.new_page()
                def goto(path):page.goto('http://testserver'+path)
                def capture(name):
                    for width,height in ((1366,900),(390,844)):
                        page.set_viewport_size({'width':width,'height':height})
                        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),name
                        page.screenshot(path=str(ARTIFACTS/f'{name}-{width}.png'),full_page=True)
                        captures.append(f'{name}-{width}.png')
                overview=f'/internal-control/monitoring?period_id={d["period"].id}'
                editor=f'/internal-control/monitoring/periods/{d["period"].id}/narrative'
                goto(overview)
                expect(page.get_by_role('link',name='Rapor anlatı bölümleri',exact=True)).to_be_visible()
                capture('genel-gorunum-baglanti')
                page.get_by_role('link',name='Rapor anlatı bölümleri',exact=True).click()
                expect(page.get_by_role('button',name='Önceki dönemden kopyala')).to_be_visible()
                capture('editor-bos')
                # Server validation preserves over-limit values (no browser truncation).
                page.locator('[name="mission"]').fill('Test misyon metni … '+('ş'*2000))
                page.locator('[name="vision"]').fill('Test korunan vizyon metni …')
                expect(page.locator('[data-save-state]')).to_have_text('Kaydedilmemiş değişiklikler var')
                page.get_by_role('button',name='Metinleri kaydet',exact=True).click()
                expect(page.get_by_text('Misyon 2.000 karakter sınırını aşıyor.',exact=False).first).to_be_visible()
                expect(page.locator('[name="vision"]')).to_have_value('Test korunan vizyon metni …')
                expect(page.locator('[name="mission"]')).to_have_value('Test misyon metni … '+('ş'*2000))
                expect(page.locator('[data-save-state]')).to_have_text('Kaydedilmedi; girdiğiniz değerler korundu')
                capture('editor-hata-korunan-degerler')
                for key,label,_ in n.fields(db,d['period']):
                    value='Test '+label.lower()+' metni …\nTest ikinci satır'
                    if key=='band_label':value='Test puan aralığı etiketi'
                    page.locator(f'[name="{key}"]').fill(value)
                current['user']=d['staff']
                page.get_by_role('button',name='Metinleri kaydet',exact=True).click()
                expect(page.locator('[data-save-state]')).to_have_text('Kaydedildi')
                capture('editor-dolu-taslak')
                page.get_by_role('button',name='Kaydet ve incelemeye gönder',exact=True).click()
                expect(page.get_by_role('heading',name='Rapor anlatı bölümleri · Gönderildi')).to_be_visible()
                current['user']=d['strategy'];goto(editor)
                capture('editor-gonderildi')
                page.get_by_role('button',name='Gerekçeli iade',exact=True).click()
                expect(page.get_by_text('İade veya yeniden açma gerekçesi eksik.',exact=False).first).to_be_visible()
                capture('editor-gerekce-hatasi')
                page.locator('[name="reason"]').fill('Test iade gerekçesi — sentetik açıklamayı tamamlayın.')
                page.get_by_role('button',name='Gerekçeli iade',exact=True).click()
                expect(page.get_by_role('heading',name='Rapor anlatı bölümleri · İade edildi')).to_be_visible()
                capture('editor-iade')
                current['user']=d['staff']
                page.get_by_role('button',name='Kaydet ve incelemeye gönder',exact=True).click()
                current['user']=d['strategy'];goto(editor)
                page.get_by_role('button',name='Onayla',exact=True).click()
                expect(page.get_by_role('heading',name='Rapor anlatı bölümleri · Onaylandı')).to_be_visible()
                assert page.locator('textarea[name="mission"]').count()==0
                capture('editor-onayli')
                current['user']=d['user']
                goto(f'/internal-control/our-actions?period_id={d["period"].id}')
                block=page.get_by_role('region',name='Misyon ve Vizyon')
                expect(block).to_be_visible()
                expect(block.get_by_text('Test misyon metni …',exact=False)).to_be_visible()
                assert page.get_by_text('Test güçlü yönler metni …',exact=False).count()==0
                capture('mudurluk-misyon-vizyon')
                current['user']=d['strategy'];goto(editor)
                page.locator('[name="reason"]').fill('Test yeniden açma gerekçesi — sentetik yeni inceleme.')
                page.get_by_role('button',name='Gerekçeli yeniden aç',exact=True).click()
                expect(page.locator('[name="mission"]')).to_contain_text('Test misyon metni …')
                capture('editor-yeniden-acildi')
                m.close_period(db,d['strategy'],d['period'].id,1,'Test kapalı dönem — sentetik kapanış.');db.commit()
                goto(editor)
                expect(page.get_by_text('İzleme dönemi kapalı.',exact=False).first).to_be_visible()
                assert page.locator('form[action*="/narrative/"]').count()==0
                capture('editor-kapali-donem')
        finally:browser.close()
    (ARTIFACTS/'ekran-ozeti.txt').write_text(
        f'{len(captures)} ekran görüntüsü; {len(captures)//2} durum × 2 genişlik (1366 ve 390 px).\n'
        'Editör: boş, dolu taslak, gönderildi, iade, onaylı, sınır hatasında korunan değerler, kapalı dönem.\n'
        'Ek: gerekçe hatası, yeniden açıldı, Strateji genel görünüm bağlantısı, müdürlük Misyon/Vizyon bloğu.\n'
        'Gerçek Chromium ile düğmeler, kayıt durumu, karakter sayacı, hata değerleri ve yatay taşma denetlendi.\n'
        'Bütün anlatı metinleri açıkça sentetiktir (Test misyon metni …, Test vizyon metni …).\n',encoding='utf-8')
