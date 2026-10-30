"""CIV-085 real Chromium state matrix, synthetic questions, desktop and mobile."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import pytest
from sqlalchemy import select
from app import internal_control_questionnaire_service as q
from test_internal_control_monitoring import monitoring
from test_internal_control_questionnaire import question_file

pytestmark = pytest.mark.postgres
ARTIFACTS = Path(__file__).parent / 'artifacts/civ085'


def test_questionnaire_screen_matrix(db, monitoring, client):
    from app.main import app, require_user
    d = monitoring
    current = {'user': d['strategy']}
    app.dependency_overrides[require_user] = lambda: current['user']
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    captures = []
    with sync_playwright() as p:
        options = dict(headless=True, args=['--no-sandbox'])
        if os.getenv('CIVENSA_CHROMIUM_PATH'):
            options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        browser = p.chromium.launch(**options)
        try:
            with browser.new_context(viewport={'width':1366,'height':900}) as context:
                def serve(route):
                    request = route.request
                    response = client.request(request.method, request.url, content=request.post_data_buffer,
                        headers={'content-type':request.headers.get('content-type',''), 'accept':request.headers.get('accept','')}, follow_redirects=True)
                    headers = dict(response.headers)
                    headers.pop('set-cookie',None)
                    route.fulfill(status=response.status_code,headers=headers,body=response.content)
                context.route('http://testserver/**',serve)
                page = context.new_page()
                def capture(name):
                    for width, height in ((1366,900),(390,844)):
                        page.set_viewport_size({'width':width,'height':height})
                        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), name
                        page.screenshot(path=str(ARTIFACTS/f'{name}-{width}.png'),full_page=True)
                        captures.append(f'{name}-{width}.png')
                def goto(path):
                    page.goto('http://testserver'+path)
                def upload(content):
                    page.locator('input[name="name"]').fill('Sentetik ekran soru listesi')
                    page.locator('input[name="file"]').set_input_files({'name':'sentetik.xlsx','mimeType':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','buffer':content})
                    page.get_by_role('button',name='Yükle ve önizle').click()

                goto('/internal-control')
                expect(page.get_by_role('link',name='Soru formu listeleri')).to_be_visible()
                page.get_by_role('link',name='Soru formu listeleri').click()
                capture('yukleme-bos')
                upload(question_file([[1,'KOS','T1','']]))
                expect(page.get_by_text('Satır 2: Soru boş',exact=False)).to_be_visible()
                capture('yukleme-hata')
                upload(question_file(count=4))
                expect(page.get_by_role('heading',name='Kaydetmeden önce inceleyin')).to_be_visible()
                capture('yukleme-onizleme')
                page.get_by_role('button',name='İncelenen listeyi yeni sürüm olarak kaydet').click()
                expect(page.get_by_role('heading',name='Sentetik ekran soru listesi',exact=False)).to_be_visible()
                capture('yukleme-kayitli')
                period_path = f'/internal-control/monitoring?period_id={d["period"].id}'
                goto(period_path)
                capture('baglama-bos')
                for checkbox in page.locator('input[name="department_ids"][type="checkbox"]').all(): checkbox.uncheck()
                page.get_by_role('button',name='Listeyi ve katılımcıları döneme bağla').click()
                expect(page.get_by_text('Katılımcı birim seçilmedi.',exact=False).first).to_be_visible()
                assert page.locator('input[name="department_ids"][type="checkbox"]:checked').count() == 0
                capture('baglama-hata')
                for checkbox in page.locator('input[name="department_ids"][type="checkbox"]').all(): checkbox.check()
                page.get_by_role('button',name='Listeyi ve katılımcıları döneme bağla').click()
                expect(page.get_by_role('heading',name='Soru formu sonuçları',exact=True)).to_be_visible()
                capture('baglama-bagli')
                owned = next(b for b in q.batches(db,d['period'].id) if b.department_id==d['department'].id)
                form_path = f'/internal-control/questionnaires/batches/{owned.id}'
                ours_path = f'/internal-control/our-actions?period_id={d["period"].id}'
                def state_screens(state):
                    current['user'] = d['user']
                    goto(ours_path)
                    expect(page.get_by_role('heading',name=f'Soru formu · {owned.label}',exact=True)).to_be_visible()
                    capture('mudurluk-'+state)
                    current['user'] = d['strategy']
                    goto(period_path)
                    capture('genel-'+state)
                    goto(form_path)
                    capture('detay-'+state)
                state_screens('bos')
                current['user'] = d['user']
                goto(ours_path)
                form = page.locator('form[action$="/answers"]')
                form.locator('input[name="answer_T1"][value="yes"]').check()
                form.locator('[name="explanation_T1"]').fill('Korunan sentetik ekran açıklaması')
                form.get_by_role('button',name='Kaydet ve incelemeye gönder').click()
                expect(page.get_by_text('Yanıtı eksik sorular: T2, T3, T4.',exact=False).first).to_be_visible()
                expect(page.locator('input[name="answer_T1"][value="yes"]')).to_be_checked()
                expect(page.locator('[name="explanation_T1"]')).to_have_value('Korunan sentetik ekran açıklaması')
                capture('mudurluk-hata')
                capture('detay-hata')
                page.get_by_role('button',name='Yanıtları kaydet',exact=True).click()
                state_screens('kismi')
                current['user'] = d['user']
                goto(form_path)
                for code, answer in [('T2','no'),('T3','developing'),('T4','yes')]:
                    page.locator(f'input[name="answer_{code}"][value="{answer}"]').check()
                page.get_by_role('button',name='Kaydet ve incelemeye gönder').click()
                state_screens('gonderildi')
                # Missing review reason is rendered in the detail form and retained.
                page.get_by_role('button',name='Gerekçeli iade',exact=True).click()
                expect(page.get_by_text('İade veya yeniden açma gerekçesi eksik.',exact=False).first).to_be_visible()
                capture('inceleme-hata')
                page.locator('[name="reason"]').fill('Sentetik açıklamayı tamamlayın.')
                page.get_by_role('button',name='Gerekçeli iade',exact=True).click()
                state_screens('iade')
                current['user'] = d['user']
                goto(form_path)
                page.get_by_role('button',name='Kaydet ve incelemeye gönder').click()
                current['user'] = d['strategy']
                goto(form_path)
                page.get_by_role('button',name='Onayla',exact=True).click()
                state_screens('onayli')
                page.locator('[name="reason"]').fill('Sentetik yeniden açma gerekçesi.')
                page.get_by_role('button',name='Gerekçeli yeniden aç',exact=True).click()
                state_screens('yeniden-acildi')
                assert db.scalars(select(q.Event).where(q.Event.batch_id==owned.id,q.Event.action=='approve')).first()
        finally:
            browser.close()
    (ARTIFACTS/'ekran-ozeti.txt').write_text(
        f'{len(captures)} ekran görüntüsü; {len(captures)//2} durum × 2 genişlik (1366 ve 390 px).\n'
        'Yükleme: boş, hata, önizleme, kayıtlı. Bağlama: boş, hata, bağlı.\n'
        'Müdürlük, genel görünüm ve detay: boş, kısmi, gönderildi, iade, onaylı, yeniden açıldı.\n'
        'Müdürlük gönderim hatası ve Strateji inceleme hatası ayrıca doğrulandı.\n'
        'Her durumda sayfa taşması yok; tablolar kendi alanında yatay kaydırılır.\n'
        'Tüm sorular sentetiktir (Test sorusu 1…4).\n',encoding='utf-8')
