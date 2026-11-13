"""CIV-188 scenario for guide_screenshots.py; no application writes outside setup."""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter
from urllib.parse import urlsplit

from scripts.guide_screenshots import ROOT, MAX_PNG_BYTES, Shot, check, local_http

OUT = ROOT / 'docs/reports/civ-188'
SCREENS = ROOT / 'docs/screenshots/civ-188'
CANCELLED = False
SYNTHETIC = 'SENTETİK CIV-188 provası: 2026 faaliyetleri yerel deneme kayıtlarıyla değerlendirilmiştir.'


# A stable, small selection from the existing end-to-end walk. Titles are
# harness step identifiers, not UI copy. Other rehearsal captures stay temporary.
GUIDE_SHOTS = {
    'Giriş ekranı': '01-giris',
    'Kılavuz mobil giriş': '02-giris-mobil',
    'Kılavuz ilk parola': '03-ilk-parola',
    'Kılavuz mobil ilk parola': '04-ilk-parola-mobil',
    'Hesapla giriş': '05-moduller',
    'Müdürlük 2026 gösterge raporunu bul': '06-gosterge-raporlari',
    '2026 gösterge girişini aç': '07-gosterge-ozet',
    'Kılavuz gerçekleşme alanları': '08-gerceklesme',
    'Kılavuz kanıt alanları': '09-kanit',
    'Kılavuz sapma açıklaması': '10-sapma',
    'Müdürlük 2026 birim raporunu bul': '11-birim-raporlari',
    'Kılavuz bölüm alanları': '12-bolum',
    'Kılavuz uygulanamaz': '13-uygulanamaz',
    'Harcama yetkilisi güvence beyanı': '14-ek2',
    'Mali Hizmetler uyarıları': '15-mali-uyarilar',
    'Sapma açıklaması boşken gönderim kontrolü': '16-gonder',
    'Açıklamasız gerçekleşmeyi gönderme denemesi': '17-gonderim-engeli',
    'Birim raporunu gönder': '18-gonderildi',
    'İade notunu gör ve düzelt': '19-iade',
    'İade notuna göre düzeltmeyi kaydet': '20-duzeltme',
    'Düzelt ve yeniden gönder': '21-yeniden-gonder',
    'Kılavuz onaylı indirme': '22-onayli-indirme',
}


def guide_filename(role, title):
    if role != ('fen_director' if title in {
            'Sapma açıklaması boşken gönderim kontrolü',
            'Açıklamasız gerçekleşmeyi gönderme denemesi', 'Birim raporunu gönder',
            'Düzelt ve yeniden gönder', 'Kılavuz onaylı indirme'} else 'fen_staff'):
        return None
    name = GUIDE_SHOTS.get(title)
    return name + '.png' if name else None


def setup(engine, *, guide=False):
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from app.models import Department, ReportingPeriod, User
    from app.personal_accounts import prepare_user_creation
    from app.released_permissions import commit_user_change
    from app.security import hash_password
    from scripts import first_load_live as live
    from scripts.first_load_dryrun import inspect_import
    book, digest = live.book_config(2026)
    parsed = live.verify_book(book, year=2026)
    with Session(engine, expire_on_commit=False) as db:
        inspection = inspect_import(db, deepcopy(parsed), book.name, year=2026)
        check(not inspection['apply_error'], '2026 onaylı kitap yüklenemedi.')
        check(inspection['protected_2027_before'] == inspection['protected_2027_after'], '2027 bazı değişti.')
        check(inspection['applied']['indicators'] == 226, '2026 gösterge sayısı beklenenden farklı.')
        password = secrets.token_urlsafe(32)
        strategy = db.scalar(select(User).where(User.role == 'strategy'))
        strategy.department_id = db.scalar(select(Department.id).where(Department.name == 'Strateji Geliştirme Müdürlüğü'))
        strategy.position = 'director'
        strategy.full_name = 'Strateji Müdürü (SENTETİK)'
        strategy.password_hash = hash_password(password)
        db.commit()
        data = dict(rehearsal=True, guide=guide, accounts={'strategy':strategy.email}, password=password,
                    period=db.scalar(select(ReportingPeriod.id).where(ReportingPeriod.year == 2026)),
                    units=[], book=str(book.relative_to(ROOT)), book_sha256=digest,
                    counts=inspection['applied'], _server_errors=[])
        for key, name in [('fen','Fen İşleri Müdürlüğü'), ('afet','Afet İşleri ve Risk Değerlendirme Müdürlüğü'),
                          ('ozel','Özel Kalem Müdürlüğü')]:
            dep = db.scalar(select(Department).where(Department.name == ('Afet İşleri ve Risk Yönetimi Müdürlüğü' if key == 'afet' else name)))
            check(dep is not None, 'Prova müdürlüğü bulunamadı.')
            for position in ('staff', 'director'):
                account = f'{key}_{position}'
                user = User(email=f'civ188.{account}@example.invalid', full_name=f'{name} {"Personel" if position == "staff" else "Müdür"} (SENTETİK)',
                    role='department', department_id=dep.id, position=position, is_active=True,
                    password_hash=hash_password(password),
                    must_change_password=guide and account == 'fen_staff')
                prepare_user_creation(db, strategy, user)
                db.add(user)
                commit_user_change(db)
                data['accounts'][account] = user.email
            data['units'].append({'key':key, 'name':name, 'department_id':dep.id})
        if guide:
            data['units'] = [unit for unit in data['units'] if unit['key'] == 'fen']
        return data


class Rehearsal:
    def __init__(self, base, data, folder):
        self.base, self.data, self.folder = base, data, folder
        self.steps, self.http, self.js, self.logs, self.unexpected = [], [], [], [], []
        self.stack = ExitStack()

    def capture(self, page, role, title, start, result='OK', note=''):
        from PIL import Image
        page.wait_for_load_state('networkidle')
        page.evaluate('document.fonts.ready')
        elapsed = round((perf_counter() - start) * 1000)
        if result=='OK' and elapsed>3000: result='SLOW'
        shot = Shot(f'{len(self.steps)+1:03d}-{role}.png', urlsplit(page.url).path +
                    ('?' + urlsplit(page.url).query if urlsplit(page.url).query else ''), title, role)
        # Keep the full capture only in the disposable run folder. Commit the
        # changed screens and formerly blocked steps, at most 40 images.
        keep = (title in {
            'Mali Hizmetler uyarıları', 'Açıklamasız gerçekleşmeyi gönderme denemesi',
            'Birim raporunu gönder', 'Strateji birim incelemesi', 'Gerekçeli iade',
            'İade notuna göre düzeltmeyi kaydet', 'Düzelt ve yeniden gönder',
            'Strateji bağımsız birim onayı', 'Kaydet sonrası özet sayaçları',
            'Faaliyet gerçekleşmesi girişi ara', 'İdare raporunu onayla ve dondur denemesi'}
            or title.startswith(('Onaylı Word ', 'Onaylı PDF '))
            or (role == 'fen_staff' and title in {
                'Hesapla giriş', '390 piksel giriş formu alanları', 'Doğrulanmamış hedefin sonraki adımı'}))
        full = self.folder / 'full-screenshots'
        full.mkdir(exist_ok=True)
        if self.data.get('guide'):
            name = guide_filename(role, title)
            keep = name is not None and not any(
                row['screenshot'] == name for row in self.steps)
            if keep:
                shot = Shot(name, shot.path, title, role)
        if self.data.get('guide') and keep and title == 'Mali Hizmetler uyarıları':
            page.locator('[aria-label="Malî bilgi uyarıları"]').evaluate(
                "el => el.scrollIntoView({block: 'center'})")
        target = (SCREENS if keep else full) / shot.filename
        check(self.data['password'] not in page.content(), 'Parola sayfa içeriğinde bulundu.')
        page.screenshot(path=str(target), animations='disabled', caret='hide')
        with Image.open(target) as png:
            check(png.size in {(1440,900),(390,900)}, 'Ekran boyutu geçersiz.')
            png.save(target, optimize=True)
        check(target.stat().st_size <= MAX_PNG_BYTES, 'PNG boyut sınırı aşıldı.')
        visible = page.locator('body').inner_text()
        technical = sorted(set(re.findall(r'name:[0-9a-f]+|\bNone\b|\b(?:structured-from-PP|needs_review|verified|missing|directorate)\b', visible)))
        row = dict(role=role, step=title, result=result, route=shot.path, screenshot=shot.filename,
                   load_ms=elapsed, note=note, technical=technical, screenshot_retained=keep,
                   server_errors=list(self.data['_server_errors'][self.server_cursor:]),
                   http=list(self.http[self.http_cursor:]), js=list(self.js[self.js_cursor:]),
                   warnings=list(self.logs[self.log_cursor:]))
        row['viewport']=page.viewport_size
        row['document_width']=page.evaluate('document.documentElement.scrollWidth')
        self.steps.append(row)
        self.write()
        print(f"{len(self.steps):03d} {role}: {title}: {result} ({elapsed} ms)", flush=True)
        return row

    def begin(self):
        check(not CANCELLED, 'Prova iptal edildi; mevcut istekten sonra güvenli temizleme yapılıyor.')
        self.server_cursor=len(self.data['_server_errors'])
        self.http_cursor=len(self.http); self.js_cursor=len(self.js); self.log_cursor=len(self.logs)
        return perf_counter()

    def goto(self, page, role, path, title, result='OK', note=''):
        start=self.begin()
        response=page.goto(self.base+path, wait_until='networkidle')
        check(response is not None and response.status == 200, 'UI sayfası açılamadı: '+path+' HTTP '+str(response.status if response else None)+' '+(page.locator('body').inner_text()[:300] if response else ''))
        return self.capture(page, role, title, start, result, note)

    def click(self, page, role, button, title, result='OK', note=''):
        start=self.begin()
        form=button.locator('xpath=ancestor::form[1]')
        if form.count():
            action=urlsplit(form.get_attribute('action') or page.url).path
            actual=form.locator('[name=evidence_rows]').count()>0
            expected=int(form.locator('[name=expected_revision]').input_value())+1 if actual else None
            with page.expect_response(lambda response: response.request.method == 'POST' and urlsplit(response.url).path == action, timeout=180000) as response_info:
                button.click()
            if actual:
                from playwright.sync_api import expect
                saved_form=page.locator(f'form[action="{action}"]')
                expect(saved_form.locator('[name=expected_revision]')).to_have_value(str(expected))
                saved_form.locator('xpath=ancestor::section[1]').get_by_role('heading',level=2).scroll_into_view_if_needed()
        else:
            button.click()
        return self.capture(page, role, title, start, result, note)

    def login(self, role):
        page=self.pages[role]
        self.goto(page,role,'/login','Giriş ekranı')
        if self.data.get('guide') and role == 'fen_staff':
            page.set_viewport_size({'width':390,'height':900})
            self.goto(page,role,'/login','Kılavuz mobil giriş')
            page.set_viewport_size({'width':1440,'height':900})
        page.locator('[name=email]').fill(self.data['accounts'][role])
        page.locator('[name=password]').fill(self.data['password'])
        self.click(page,role,page.get_by_role('button', name='Giriş yap', exact=False),'İlk hesapla giriş' if self.data.get('guide') and role == 'fen_staff' else 'Hesapla giriş')
        if self.data.get('guide') and role == 'fen_staff':
            check(urlsplit(page.url).path == '/change-password', 'İlk parola ekranı açılmadı.')
            self.goto(page, role, '/change-password', 'Kılavuz ilk parola')
            page.set_viewport_size({'width':390,'height':900})
            self.goto(page, role, '/change-password', 'Kılavuz mobil ilk parola')
            page.set_viewport_size({'width':1440,'height':900})
            new_password = secrets.token_urlsafe(32)
            page.locator('#firstCurrentPassword').fill(self.data['password'])
            page.locator('#firstNewPassword').fill(new_password)
            page.locator('#firstConfirmPassword').fill(new_password)
            page.get_by_role('button', name='Parolamı belirle ve devam et').click()
            page.wait_for_url(self.base+'/modules')
            self.goto(page, role, '/modules', 'Hesapla giriş')
        check(urlsplit(page.url).path == '/modules', 'UI girişi modüllere ulaşmadı.')
        return page

    def write(self):
        rows = [s for s in self.steps if s['screenshot_retained']] if self.data.get('guide') else self.steps
        (OUT/'steps.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n')

    def actual(self,page,role,action,explanation,attach=False):
        form=page.locator(f'form[action="{action}"]')
        form.locator('[name=value]').fill('12,5')
        form.locator('[name=state]').select_option('verified')
        form.locator('[name=source_title]').first.fill('SENTETİK 2026 birim kayıtları')
        form.locator('[name=source_locator]').first.fill('Prova sayfa 1')
        form.locator('[name=source_revision]').first.fill('CIV-188 sentetik v1')
        form.locator('[name=explanation]').fill(explanation)
        if attach:
            form.locator('[type=file]').first.set_input_files(str(self.folder/'sentetik-kanit.pdf'))
        if self.data.get('guide') and role == 'fen_staff':
            for selector,title in [('[name=value]', 'Kılavuz gerçekleşme alanları'),
                                   ('[name=source_title]', 'Kılavuz kanıt alanları'),
                                   ('[name=explanation]', 'Kılavuz sapma açıklaması')]:
                name = guide_filename(role, title)
                if any(row['screenshot'] == name for row in self.steps) or (selector == '[name=explanation]' and not explanation):
                    continue
                start=self.begin()
                if title == 'Kılavuz kanıt alanları':
                    form.locator('[data-evidence-row]').first.evaluate(
                        "el => el.scrollIntoView({block: 'center'})")
                elif title == 'Kılavuz gerçekleşme alanları':
                    form.evaluate("el => el.scrollIntoView({block: 'start'})")
                else:
                    form.locator(selector).first.scroll_into_view_if_needed()
                self.capture(page,role,title,start)
        expected=int(form.locator('[name=expected_revision]').input_value())+1
        self.click(page,role,form.get_by_role('button',name='Yeni gerçekleşme revizyonu kaydet'),
                   'Gösterge gerçekleşmesi + '+('dosya kanıtı' if attach else 'kaynak')+(' (açıklama boş)' if not explanation else ''))
        from playwright.sync_api import expect
        expect(page.locator(f'form[action="{action}"] [name=expected_revision]')).to_have_value(str(expected))
        check(page.locator('[role=alert]').count() == 0, 'Gerçekleşme kaydında beklenmeyen form hatası.')
        if attach:
            check(page.get_by_role('link',name=re.compile('sentetik-kanit.pdf')).count()>0,'Dosya kanıtı kayıtta görünmedi.')

    def sections(self,page,role,document):
        self.goto(page,role,document,'Birim raporu ve bölüm ağacı')
        links=page.locator('nav[aria-label="EK-1 bölümleri"] a').evaluate_all('(els)=>els.map(e=>({href:e.getAttribute("href"),text:e.textContent.trim()}))')
        for link in links:
            path=document+link['href']
            self.goto(page,role,path,'Bölüm aç: '+link['text'])
            form=page.locator('form[data-ar-section-form]')
            if not form.count():
                continue
            form.locator('[name=text]').fill(SYNTHETIC)
            inapplicable=link['href'].split('code=')[-1] in {'III.A.3','III.A.4'}
            form.locator('[name=status]').select_option('not_applicable' if inapplicable else 'ready')
            if inapplicable:
                form.locator('[name=reason]').fill('SENTETİK prova: bu müdürlük için denetim/yardım olayı kurgulanmadı.')
            if self.data.get('guide') and role == 'fen_staff':
                start=self.begin(); form.scroll_into_view_if_needed()
                self.capture(page,role,'Kılavuz uygulanamaz' if inapplicable else 'Kılavuz bölüm alanları',start)
            self.click(page,role,form.get_by_role('button',name='Bölümü kaydet'),'Bölüm metni kaydet: '+link['text'])
            check(page.locator('[role=alert]').count()==0, 'Bölüm kaydında beklenmeyen hata.')
        self.goto(page,role,document+'/assurances/EK-2','EK-2 aç' if self.data.get('guide') else 'Harcama yetkilisi güvence beyanı')
        values={'place':'Prova Belediyesi (SENTETİK)','date':'2027-01-15','person_ref_0':'CIV188-SENTETIK',
            'name_0':'Prova Müdürü (SENTETİK)','title_0':'Müdür','start_date_0':'2026-01-01','end_date_0':'2026-12-31'}
        for field,value in values.items(): page.locator(f'[name="{field}"]').fill(value)
        if self.data.get('guide'):
            self.capture(page,role,'Harcama yetkilisi güvence beyanı',self.begin())
        self.click(page,role,page.get_by_role('button',name='Beyan alanlarını kaydet'),'EK-2 beyan alanlarını kaydet')

    def unit_tables(self,page,role,document):
        """CIV-220: fill rehber Tablo 1, 2, 7, 8 and one activity photo through the real forms."""
        path=document+'/unit-tables'
        self.goto(page,role,path,'Birim tabloları aç')
        def save(kind,title):
            form=page.locator(f'form[data-unit-table="{kind}"]')
            self.click(page,role,form.get_by_role('button',name=f'Tablo {kind} kaydet'),title)
            check(page.locator('[role=alert]').count()==0,f'Tablo {kind} kaydında beklenmeyen hata: '+
                  (page.locator('[role=alert]').first.inner_text() if page.locator('[role=alert]').count() else ''))
        form=page.locator('form[data-unit-table="1"]')
        form.locator('[name=include_0]').check()
        for field,value in {'name_0':'Hizmet binası (SENTETİK)','address_0':'Prova Mahallesi (SENTETİK)',
                'purpose_0':'Ofis','area_0':'1.250,5','ownership_0':'Belediye mülkü'}.items():
            form.locator(f'[name="{field}"]').fill(value)
        save('1','Tablo 1 fiziksel yapı kaydet')
        form=page.locator('form[data-unit-table="2"]')
        for i in range(4):
            for field,value in {'status':'Genel idare (SENTETİK)','positions':'10','actual':'8','women':'3','men':'5'}.items():
                form.locator(f'[name="{field}_{i}"]').fill(value)
        save('2','Tablo 2 personel kaydet')
        form=page.locator('form[data-unit-table="7"]')
        count=int(form.locator('[name=row_count]').input_value())
        check(count>0,'Tablo 7 müdürlük faaliyeti göstermedi.')
        for i in range(count):
            if count>1 and i==count-1:
                form.locator(f'[name="not_applied_{i}"]').check()
                form.locator(f'[name="reason_{i}"]').fill('SENTETİK: faaliyet 2026 yılında uygulanmadı.')
                continue
            form.locator(f'[name="outputs_{i}"]').fill(SYNTHETIC)
            form.locator(f'[name="inside_{i}"]').fill('1.234,56')
            form.locator(f'[name="outside_{i}"]').fill('0')
        save('7',f'Tablo 7 faaliyet çıktı ve maliyet kaydet ({count} faaliyet)')
        form=page.locator('form[data-unit-table="8"]')
        form.locator('[name=project_choice]').select_option('none')
        form.locator('[name=include_0]').uncheck()
        save('8','Tablo 8 Bu yıl proje yok kaydet')
        from PIL import Image
        photo=self.folder/'sentetik-foto.png'
        if not photo.exists(): Image.new('RGB',(320,200),(64,128,112)).save(photo)
        form=page.locator('form[action$="/unit-tables/photos/upload"]')
        form.locator('[name=caption]').fill('SENTETİK faaliyet fotoğrafı')
        form.locator('[name=file]').set_input_files(str(photo))
        self.click(page,role,form.get_by_role('button',name='Fotoğraf yükle'),'Faaliyet fotoğrafı yükle')
        check(page.locator('figure figcaption').filter(has_text='Fotoğraf 1').count()==1,'Yüklenen fotoğraf listede görünmedi.')
        open_items=page.locator('details.unit-notice summary').count()
        if open_items:
            self.goto(page,role,path,'Tablolarda kalan gönderim eksikleri','BLOCKER',page.locator('details.unit-notice').inner_text())

    def workflow(self,page,role,document,label,title,expected):
        self.goto(page,role,document,title+' öncesi')
        button=page.get_by_role('button',name=label,exact=True)
        row=self.click(page,role,button,title)
        status=page.locator('[data-ar-workflow-status]').inner_text() if page.locator('[data-ar-workflow-status]').count() else ''
        if status!=expected:
            row['result']='BLOCKER'
            row['note']='Beklenen durum: '+expected+'; görünen: '+(status or 'İşlem tamamlanamadı hata sayfası')+'; '+page.locator('body').inner_text()
            self.write()
            return False
        return True

    def walk(self):
        from playwright.sync_api import sync_playwright
        from reportlab.pdfgen import canvas
        pdf=canvas.Canvas(str(self.folder/'sentetik-kanit.pdf')); pdf.drawString(50,750,'SENTETIK CIV-188 2026 prova kaniti'); pdf.save()
        pw=self.stack.enter_context(sync_playwright())
        options={'headless':True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'): options['executable_path']=os.environ['CIVENSA_CHROMIUM_PATH']
        browser=self.stack.enter_context(pw.chromium.launch(**options))
        self.data['browser']=browser.version
        self.pages={}
        for role in self.data['accounts']:
            context=self.stack.enter_context(browser.new_context(viewport={'width':1440,'height':900},
                locale='tr-TR',timezone_id='Europe/Istanbul',reduced_motion='reduce',
                service_workers='block',extra_http_headers={'X-Guide-Account':role},accept_downloads=True))
            def guard(route):
                if urlsplit(route.request.url).netloc==urlsplit(self.base).netloc:
                    route.continue_()
                else:
                    self.unexpected.append('Dış ağ isteği engellendi.'); route.abort()
            context.route('**/*',guard)
            page=context.new_page(); page.set_default_timeout(15000); page.set_default_navigation_timeout(180000)
            page.on('pageerror',lambda e:self.js.append(type(e).__name__+': '+str(e)[:300]))
            page.on('response',lambda r: self.http.append({'route':urlsplit(r.url).path,'status':r.status}) if r.status>=400 else None)
            self.pages[role]=page
        strategy=self.login('strategy'); pid=self.data['period']
        self.goto(strategy,'strategy',f'/report-builder?period_id={pid}','2026 onaylı kitap yayın hazırlığı')
        form=strategy.locator('form[action="/report-builder/publish-approved-book"]')
        form.locator('[name=approval_reference]').fill('SENTETİK CIV-188 prova onay dayanağı; gerçek meclis kararı değildir.')
        self.click(strategy,'strategy',form.get_by_role('button'),'Onaylı kitaptan yayınla')
        check(strategy.locator('form[action="/report-builder/publish-approved-book"]').count()==0, 'Onaylı kitap yayınlanamadı.')
        self.goto(strategy,'strategy','/activity-reports','2026 gösterge raporu oluşturma')
        option=strategy.locator('select[name=publication_id] option').filter(has_text='2026').first
        strategy.locator('select[name=publication_id]').select_option(option.get_attribute('value'))
        self.click(strategy,'strategy',strategy.get_by_role('button',name='Seçilen yayınla rapor oluştur'),'Yayına bağlı 2026 FR revizyonu oluştur')
        revision=urlsplit(strategy.url).path
        check('/revisions/' in revision,'FR revizyonu oluşmadı.')
        self.goto(strategy,'strategy','/activity-sections','2026 birim ve idare raporları oluşturma')
        strategy.locator('form[action="/activity-sections/years"] select[name=period_id]').select_option(str(pid))
        self.click(strategy,'strategy',strategy.get_by_role('button',name='Raporları oluştur'),'2026 EK-1 raporlarını oluştur')
        approvals=[]
        for unit in self.data['units']:
            role=unit['key']+'_staff'; page=self.login(role)
            self.goto(page,role,'/activity-reports','Müdürlük 2026 gösterge raporunu bul')
            self.click(page,role,page.locator(f'a[href="{revision}"]').first,'2026 gösterge girişini aç')
            actions=page.locator('form[data-actual-form]').evaluate_all('(els)=>els.map(e=>e.getAttribute("action"))')
            check(bool(actions),'Müdürlüğün gösterge giriş formu bulunamadı.')
            unit['targets']=page.locator('.indicator-target').all_inner_texts()
            candidates=page.locator('section[data-draft-record]').evaluate_all(
                '(els)=>els.filter(e=>!e.querySelector("[data-unverified-target]")).map(e=>e.querySelector("form").getAttribute("action"))')
            if candidates:
                actions=[candidates[0]]+[a for a in actions if a!=candidates[0]]
            else:
                self.goto(page,role,revision,'Sapma açıklaması zorunluluğu senaryosu','BLOCKER',
                    'Bütün hedefler Doğrulanmalı görünüyor; sayısal fark hesaplanamıyor. Boş açıklamalı gerçekleşme kaydedilecek, ancak sapma kapısı kanıtlanamaz.')
            page.set_viewport_size({'width':390,'height':900})
            self.goto(page,role,revision,'390 piksel gösterge giriş sayfası')
            start=self.begin()
            page.locator('form[data-actual-form]').first.scroll_into_view_if_needed()
            self.capture(page,role,'390 piksel giriş formu alanları',start)
            page.set_viewport_size({'width':1440,'height':900})
            if unit['key']=='fen' and page.locator('[data-unverified-target]').count():
                start=self.begin()
                page.locator('[data-unverified-target]').first.scroll_into_view_if_needed()
                self.capture(page,role,'Doğrulanmamış hedefin sonraki adımı',start)
            for i,action in enumerate(actions):
                self.actual(page,role,action,'' if i==0 else SYNTHETIC,attach=i==0)
                if i==0:
                    # A successful AJAX save must already match a fresh page.
                    summary=page.locator('.indicator-report-summary')
                    saved_counts=summary.inner_text()
                    start=self.begin()
                    summary.scroll_into_view_if_needed()
                    self.capture(page,role,'Kaydet sonrası özet sayaçları',start,note=saved_counts)
                    page.reload(wait_until='networkidle')
                    check(page.locator('.indicator-report-summary').inner_text()==saved_counts,
                          'AJAX kaydı sonrası sayaçlar yeni sayfa yüklemesiyle eşleşmiyor.')
            self.goto(page,role,'/activity-sections','Müdürlük 2026 birim raporunu bul')
            # The year prefix is shown only when several years are listed (CIV-199/201).
            heading=re.compile('^(2026 · )?'+re.escape(unit['name'])+'$')
            group=page.locator('article.report-group').filter(has=page.get_by_role('heading',name=heading))
            link=group.locator('a[href*="/activity-sections/reports/"]').first
            document=urlsplit(link.get_attribute('href')).path
            unit['document']=document
            self.sections(page,role,document)
            self.unit_tables(page,role,document)
            self.goto(page,role,document+'?code=III.A.1','Mali Hizmetler uyarıları')
            warnings=page.locator('[aria-label="Malî bilgi uyarıları"]').inner_text()
            check('gönderimi engellemez' in warnings,'Mali Hizmetler uyarısı bulunamadı.')
            self.steps[-1]['note']=warnings
            self.goto(page,role,f'/activity-report?year=2026&period_id={pid}','Faaliyet gerçekleşmesi girişi ara',
                      'OK','Faaliyet başına sonuç girişi beklenmiyor (Strateji kararı 9.11.2026); açıklama EK-1 bölüm metnine yazılır.')
            director_role=unit['key']+'_director'; director=self.login(director_role)
            self.goto(director,director_role,document,'Sapma açıklaması boşken gönderim kontrolü')
            row=self.click(director,director_role,director.get_by_role('button',name='Strateji’ye gönder',exact=True),
                           'Açıklamasız gerçekleşmeyi gönderme denemesi')
            body=director.locator('body').inner_text()
            check(any(r['status']==409 for r in row['http']),'Açıklamasız gerçekleşme gönderiminde beklenen engel yok.')
            if 'hedef farkı açıklaması eksik' in body:
                row['note']='Beklenen engel: açıklamasız sapma ile gönderilemedi.'
            else:
                row['result']='BLOCKER'
                row['note']='Sapma kontrolüne ulaşmadan bölüm tamamlanma kapısı engelledi: '+body
            self.goto(director,director_role,document,'Gönderim engelinden birim raporuna dön')
            check(director.locator('[data-ar-workflow-status]').inner_text()=='Taslak','Gönderilemeyen rapor taslak durumda değil.')
            self.goto(page,role,revision,'Sapma gerekçesini tamamla')
            self.actual(page,role,actions[0],SYNTHETIC)
            sent=self.workflow(director,director_role,document,'Strateji’ye gönder','Birim raporunu gönder','Gönderildi')
            if not sent:
                self.blocked_followups(document,unit)
                self.goto(strategy,'strategy',document,'Strateji gönderilemeyen birimi incele')
                self.downloads(strategy,unit,'Taslak')
                continue
            self.goto(strategy,'strategy',document,'Strateji birim incelemesi')
            strategy.get_by_label('İade gerekçesi').fill('SENTETİK: Faaliyet anlatımına tamamlanma bilgisini ekleyin.')
            self.click(strategy,'strategy',strategy.get_by_role('button',name='Gerekçeyle iade et'),'Gerekçeli iade')
            check(strategy.locator('[data-ar-workflow-status]').inner_text()=='İade edildi','İade başarısız.')
            self.goto(page,role,document+'?code=III.B.1','İade notunu gör ve düzelt')
            form=page.locator('form[data-ar-section-form]')
            check(form.count()==1,'İade düzeltme formu bulunamadı.')
            form.locator('[name=text]').fill(SYNTHETIC+' SENTETİK düzeltme: faaliyet tamamlandı.')
            form.locator('[name=status]').select_option('ready')
            self.click(page,role,form.get_by_role('button',name='Bölümü kaydet'),'İade notuna göre düzeltmeyi kaydet')
            check(page.locator('[role=alert]').count()==0,'İade düzeltmesi kaydedilemedi.')
            check(self.workflow(director,director_role,document,'Yeniden gönder','Düzelt ve yeniden gönder','Gönderildi'),'Yeniden gönderim başarısız.')
            self.goto(strategy,'strategy',document,'Strateji yeniden inceleme')
            self.click(strategy,'strategy',strategy.get_by_role('button',name='Birimi onayla',exact=True),'Strateji bağımsız birim onayı')
            check(strategy.locator('[data-ar-workflow-status]').inner_text()=='Onaylandı','Birim onaylanamadı.')
            approvals.append(unit['key'])
            self.downloads(strategy,unit,'Onaylı')
            if self.data.get('guide') and unit['key']=='fen':
                self.goto(director,director_role,document,'Kılavuz onaylı raporu aç')
                director.locator('[data-section-export] summary').click()
                self.capture(director,director_role,'Kılavuz onaylı indirme',self.begin())
                self.downloads(director,unit,'Onaylı müdürlük',role=director_role)
        self.goto(strategy,'strategy',f'/activity-sections?period_id={pid}','İdare raporuna geçiş')
        groups=strategy.locator('article.report-group')
        institution=next(g for g in groups.all() if 'İdare' in g.locator('h3').first.inner_text())
        path=urlsplit(institution.locator('td a[href*="?code="]').first.get_attribute('href')).path
        self.goto(strategy,'strategy',path,'İdare konsolidasyonu ve eksik birimler')
        row=self.click(strategy,'strategy',strategy.get_by_role('button',name='İçeriği onayla ve dondur'),
                       'İdare raporunu onayla ve dondur denemesi','BLOCKER',
                       'Yalnız üç müdürlük provası; diğer birimlerin onayları ve idare içerikleri tamamlanmadı. Beklenen kapsam engeli.')
        check(any(r['status']==409 for r in row['http']),'Eksik İdare raporu dondurma denemesi reddedilmedi.')
        self.data['approvals']=approvals
        expected_units = [unit['key'] for unit in self.data['units']]
        check(approvals==expected_units,'Prova müdürlüklerinin bağımsız onayı tamamlanamadı.')
        self.check_blockers()

    def check_blockers(self):
        blockers=[step['step'] for step in self.steps if step['result']=='BLOCKER']
        check(blockers==['İdare raporunu onayla ve dondur denemesi'],
              'Beklenen İdare kapsam sınırı dışında engel kaldı veya kapsam engeli bulunamadı.')

    def downloads(self,page,unit,status,role='strategy'):
        if page.locator('[data-section-export]').get_attribute('open') is None:
            page.locator('[data-section-export] summary').click()
        for label,magic in [('Word olarak indir',b'PK'),('PDF olarak indir',b'%PDF')]:
            start=self.begin()
            with page.expect_download(timeout=180000) as info:
                page.get_by_role('link',name=label,exact=True).click()
            download=info.value; local=Path(download.path())
            raw=local.read_bytes()
            check(raw.startswith(magic),'İndirme dosya biçimi beklenenden farklı.')
            self.capture(page,role,status+' '+label+' · '+unit['name'],start,
                         note=f'{len(raw)} bayt; SHA256: {hashlib.sha256(raw).hexdigest()}; dosya başlığı doğrulandı.')

    def blocked_followups(self,document,unit):
        for role,title in [
            ('strategy','Gönderilmiş birimin Strateji incelemesi'),
            ('strategy','Gerekçeli iade'),
            (unit['key']+'_staff','İade üzerine düzeltme'),
            (unit['key']+'_director','İade üzerine yeniden gönderim'),
            ('strategy','Strateji bağımsız onayı'),
            ('strategy','Onaylı birim Word indir'),
            ('strategy','Onaylı birim PDF indir')]:
            self.goto(self.pages[role],role,document,title,'BLOCKER',
                      'Gönderim, Mali Hizmetler sahipli bölüm durumları nedeniyle tamamlanamadı; bu akış adımına ulaşılamadı.')


def write_report(rehearsal, failed):
    """Keep the human step table tied to the machine evidence on every rerun."""
    from collections import Counter
    from PIL import Image
    steps=rehearsal.steps
    sizes=[p.stat().st_size for p in SCREENS.glob('*.png')]
    check(len(sizes)<=40,'CIV-188 için 40 PNG sınırı aşıldı.')
    dimensions=Counter()
    for path in SCREENS.glob('*.png'):
        with Image.open(path) as png: dimensions[f'{png.width}×{png.height}']+=1
    def cell(value): return str(value).replace('|','&#124;').replace('\n',' ')
    labels={'strategy':'Strateji Müdürü'}
    for unit in rehearsal.data['units']:
        for suffix,label in [('staff','Personel'),('director','Müdür')]:
            labels[unit['key']+'_'+suffix]=unit['name']+' · '+label
    lines=['# CIV-188 — 2026 Faaliyet Raporu müdürlük provası','',
        '**SENTETİK düzeltme provası. Yalnız atılabilir yerel PostgreSQL kullanıldı; canlı veritabanı bağlantısı, birleştirme ve dağıtım yapılmadı.**','',
        '## Tekrar çalıştırma','',
        'Depo kökünde, mevcut `requirements-dev.txt` bağımlılıkları ve Playwright Chromium kuruluyken:', '',
        '```sh','python scripts/guide_screenshots.py --fr-rehearsal','```','',
        '`CIVENSA_TEST_POSTGRES_URL` önceden yalnız localhost üzerinde CREATE DATABASE yetkili PostgreSQL 16+ test rolünü göstermelidir. '
        'İsteğe bağlı `CIVENSA_CHROMIUM_PATH` mevcut Chromium yoludur. Uygulama bağlantı değişkenleri başlangıçta maskelenir. '
        'Mevcut `guide_screenshots.local_http`, `Shot`, PNG sınırı ve `first_load_dryrun.disposable_database` altyapısı kullanılır. '
        'Her koşu yeni rastgele veritabanı oluşturur ve bağlam çıkışında siler; SIGINT/SIGTERM mevcut UI isteği tamamlandığında aynı temizliğe gider. '
        'Başarısız kurulum/seçici/beklenmeyen sunucu veya JS hatası sıfır dışı çıkıştır. Kanıtlanmış ürün engeli, çizelgede BLOCKER olarak kaydedilerek koşu sürdürülür.','',
        '## Veri ve yöntem','',
        f"Kaynak: `{rehearsal.data['book']}`; SHA-256 `{rehearsal.data['book_sha256']}`. "
        '`verify_book` + `inspect_import(..., year=2026)` gerçek operasyonel `first_load_live.execute` yolunu kullanır: '
        'önce 2027 onaylı tabanı, sonra 2026 kitabını yükler; 2027 koruma hash eşitliği doğrulanır. '
        'İçe aktarıcı sabit şeması mevcut `tests.first_load_checkpoint` ile hazırlanır; kurulum bitmeden mevcut migrasyonlarla tekrar depo head şemasına çıkılır. '
        'Bu sırada test yardımcısının boş yardımcı sunum tabloları kontrol edilip mevcut migrasyonlarına bırakılır. Yeni migrasyon yazılmaz.','',
        f"Yükleyici sayımları: `{json.dumps(rehearsal.data['counts'],ensure_ascii=False,sort_keys=True)}`. "
        '2026 yayını kurulumda taklit edilmez: Strateji tarayıcıda **Onaylı kitaptan yayınla** düğmesini kullanır; '
        'Onay dayanağı açıkça sentetiktir. Gösterge revizyonu ve EK-1 yıl raporları da UI üzerinden açılır.','',
        'Hesaplar: bir `strategy/director`; Fen İşleri, Afet İşleri ve Risk Değerlendirme ve Özel Kalem için ayrı '
        '`department/staff` ve `department/director` (toplam 7). Özel Kalem küçük müdürlük örneğidir. '
        'Afet hesabı mevcut D-372 eşlemesindeki Risk Yönetimi sistem kaydına bağlıdır; 2026 görünen adı korunur. '
        'Rastgele parola bellekte tutulur; raporlanmaz. Personel veri girer; müdür gönderir. Strateji birim içeriğini düzenlemeden bağımsız inceleme yapar.','',
        'Kurulumdan sonraki bütün istekler Playwright tarafından görünen sayfa/formlar üzerinden yapılır. '
        'TestClient köprüsü yalnız loopback sunucuyu uygulamaya bağlar; oturumlar tarayıcıdaki gerçek giriş formuyla açılır. '
        'Doğrudan API çağrısı, JS ile form üretimi veya kurulum sonrası DB yazması yoktur. Dış ağ tarayıcıda engellenir. '
        'Tüm gerçekleşmeler 12,5; kaynaklar, açıklamalar, beyan kişileri ve PDF kanıtı SENTETİK olarak işaretlidir. '
        'Denetim/yardım olayı kurgulanmayan bölümler gerekçeli Uygulanamaz seçilir; boş mali tutarlar sıfıra çevrilmez.','',
        f"Tarayıcı: Chromium {rehearsal.data.get('browser','?')}; tr-TR, Europe/Istanbul; açık tema. "
        'Süre, navigasyon veya tıklamadan `networkidle` ve font hazır olmasına kadar duvar saati ölçümüdür (ms); '
        'ekran görüntüsü kodlamasını kapsamaz. Formu yazma süresi dahil değildir. Loopback/TestClient ve paylaşılan makine ölçümüdür; '
        'canlı kapasite/SLA testi değildir. 3.000 ms üzeri başarılı adımlar SLOW işaretlenir.','',
        '## Bulgular','',
        'Aşağıdaki bulgular bu koşunun ekranları ve `steps.json` ile birlikte değerlendirilmelidir. '
        'BLOCKER kayıtları tamamlanamayan kullanıcı işlerini; beklenen kapsam kapısı ürün hatası olmayan sınırı ayrıca belirtir.','',
        '<!-- CIV188_FINDINGS -->','',
        '## CIV-187 ile karşılaştırma','',
        '| Koşu | OK | BLOCKER | SLOW | Toplam |',
        '| --- | ---: | ---: | ---: | ---: |',
        '| CIV-187 | 289 | 31 | 5 | 325 |',
        f"| CIV-188 | {sum(s['result']=='OK' for s in steps)} | {sum(s['result']=='BLOCKER' for s in steps)} | {sum(s['result']=='SLOW' for s in steps)} | {len(steps)} |", '',
        '## Adım çizelgesi','',
        '| Rol | Adım | Sonuç | Sayfa / route | Ekran | Süre (ms) | Hata / uyarı / not |',
        '| --- | --- | --- | --- | --- | ---: | --- |']
    for step in steps:
        notes=[]
        if step['http']: notes.append('HTTP: '+', '.join(f"{r['status']} {r['route']}" for r in step['http']))
        if step['server_errors']: notes.append('Sunucu: '+json.dumps(step['server_errors'],ensure_ascii=False))
        if step['js']: notes.append('JS: '+str(step['js']))
        if step['warnings']: notes.append('Log uyarısı: '+str(step['warnings']))
        if step['technical']: notes.append('Teknik metin: '+', '.join(step['technical']))
        if step['note']: notes.append(step['note'])
        if not notes: notes=['Sunucu/JS/log uyarısı gözlenmedi.']
        result='SLOW' if step['result']=='OK' and step['load_ms']>3000 else step['result']
        lines.append('| '+' | '.join([cell(labels[step['role']]),cell(step['step']),result,
            '`'+cell(step['route'])+'`',(f"[PNG](../../screenshots/civ-188/{step['screenshot']})" if step['screenshot_retained'] else 'Tam koşuda yakalandı; depoya alınmadı'),str(step['load_ms']),cell(' '.join(notes))])+' |')
    lines+=['','## D-252 ekran sayımı','',f"Tam koşuda {len(steps)} adım yakalandı. Depoda yalnız değişen ekranlar ve önceki engelli adımlar tutulur; diğer PNG dosyaları geçici klasörle temizlenir.", '', f"Toplam **{len(sizes)} PNG**: "+', '.join(f'{k}: {v}' for k,v in sorted(dimensions.items()))+'. '
        +f"En büyük dosya **{max(sizes,default=0)} bayt**; her PNG ≤ 1.500.000 bayt. ", '',
        f"Koşu sonucu: {'BEKLENMEYEN HATA — sıfır dışı çıkış; unexpected.txt konumu incelenmeli' if failed else 'tamamlandı (çıkış 0; ürün engelleri yukarıda)'}. "
        +f"Onaylanabilen prova birimleri: {', '.join(rehearsal.data.get('approvals',[])) or 'yok'}. ", '',
        'Makine kanıtı: [steps.json](steps.json), [run.json](run.json). İndirmelerde gerçek tarayıcı indirme olayı, '
        'dosya başlığı, byte sayısı ve SHA-256 denetlenir; dosyalar geçici klasörde kalır. '
        'Bu prova gerçek kişisel hesap dağıtımını, Ali Abi kabulünü veya tam ölçekli 33 birim kapanışını karşılamaz. '
        'CI durumu ve bu teslimin SHA bilgisi PR açıklamasında tutulur.','']
    findings=OUT/'findings.md'
    if findings.exists(): lines=[line.replace('<!-- CIV188_FINDINGS -->',findings.read_text().strip()) for line in lines]
    (OUT/'report.md').write_text('\n'.join(line.rstrip() for line in lines))


def _run(url, *, guide=False):
    from scripts.first_load_dryrun import environment
    from tests.first_load_checkpoint import disposable_first_load_database
    OUT.mkdir(parents=True,exist_ok=True); SCREENS.mkdir(parents=True,exist_ok=True)
    # Delete only this scenario's previously generated numbered images.
    for path in SCREENS.glob('[0-9][0-9]-*.png' if guide else '[0-9][0-9][0-9]-*.png'): path.unlink()
    outputs = ['steps.json', 'run.json', 'unexpected.txt'] + ([] if guide else ['report.md'])
    for path in (OUT/name for name in outputs):
        path.unlink(missing_ok=True)
    rehearsal=None; failed=False
    global CANCELLED
    CANCELLED=False
    def cancel(signum,frame):
        global CANCELLED
        CANCELLED=True
    signal.signal(signal.SIGINT,cancel); signal.signal(signal.SIGTERM,cancel)
    logging.disable(logging.NOTSET)
    try:
        with TemporaryDirectory(prefix='civ188_') as temporary:
            with disposable_first_load_database(url) as engine:
                import app.db as app_db
                app_db.engine.dispose(); app_db.engine=engine; app_db.SessionLocal.configure(bind=engine)
                data=setup(engine, guide=guide)
                # The operational importer is pinned; bring disposable schema back to
                # current head before the first browser action, using existing migrations.
                from alembic import command
                from alembic.config import Config
                # The existing first-load test harness creates two empty auxiliary
                # tables for current metadata guards. Recreate them through their
                # migrations now that the pinned loader has finished.
                from app.sunum.models import SunumPhoto, SunumHighlight
                from sqlalchemy import select, func
                from sqlalchemy.orm import Session
                # CIV-220: since CIV-219 the live loader pin equals the migration
                # head, so the loaded schema is already current. Dropping the
                # auxiliary tables then left them missing (upgrade is a no-op).
                from alembic.runtime.migration import MigrationContext
                from alembic.script import ScriptDirectory
                with engine.connect() as connection:
                    current = set(MigrationContext.configure(connection).get_current_heads())
                at_head = current == set(ScriptDirectory.from_config(Config(str(ROOT/'alembic.ini'))).get_heads())
                with Session(engine) as db:
                    for model in (SunumHighlight, SunumPhoto):
                        check(db.scalar(select(func.count()).select_from(model)) == 0, 'Yardımcı prova tablosu boş değil.')
                for model in (SunumHighlight, SunumPhoto):
                    if not at_head: model.__table__.drop(engine)
                # CIV-199: the metadata-built schema also carries the later CIV-194/197
                # auxiliary tables; drop them when present and still empty so their
                # migrations can recreate them during the upgrade below.
                from sqlalchemy import inspect as schema_inspect
                from app.actual_import_models import ActualImport
                from app.models import IndicatorDirection
                for model in (ActualImport, IndicatorDirection) if not at_head else ():
                    if schema_inspect(engine).has_table(model.__tablename__):
                        with Session(engine) as db:
                            check(db.scalar(select(func.count()).select_from(model)) == 0, 'Yardımcı prova tablosu boş değil.')
                    model.__table__.drop(engine, checkfirst=True)
                rendered=engine.url.render_as_string(hide_password=False)
                with environment(DATABASE_URL=rendered,MIGRATION_DATABASE_URL=rendered):
                    command.upgrade(Config(str(ROOT/'alembic.ini')),'head')
                with local_http(engine,data) as base:
                    rehearsal=Rehearsal(base,data,Path(temporary))
                    class Warnings(logging.Handler):
                        def emit(self,record):
                            if record.levelno>=logging.WARNING:
                                rehearsal.logs.append({'logger':record.name,'level':record.levelname})
                    handler=Warnings(); logging.getLogger().addHandler(handler)
                    try: rehearsal.walk()
                    finally:
                        rehearsal.stack.close(); logging.getLogger().removeHandler(handler)
                        safe={k:v for k,v in data.items() if k not in {'password','_clients','accounts'}}
                        safe.update(unexpected=rehearsal.unexpected,server_errors=data['_server_errors'],js=rehearsal.js)
                        (OUT/'run.json').write_text(json.dumps(safe,ensure_ascii=False,indent=2)+'\n')
                check(not rehearsal.unexpected and not rehearsal.js and not data['_server_errors'],'Beklenmeyen tarayıcı/sunucu hatası.')
    except (Exception, KeyboardInterrupt) as exc:
        import traceback
        failed=True
        # Exception text may contain credentials: output only class and code locations.
        locations=' -> '.join(f'{Path(f.filename).name}:{f.lineno}' for f in traceback.extract_tb(exc.__traceback__))
        print(f'CIV-188 beklenmeyen hata: {type(exc).__name__}; {locations}',flush=True)
        (OUT/'unexpected.txt').write_text(f'{type(exc).__name__}: {locations}\n')
    else:
        (OUT/'unexpected.txt').unlink(missing_ok=True)
    if rehearsal:
        rehearsal.write()
        if guide:
            write_guide_index(rehearsal, failed)
        else:
            write_report(rehearsal,failed)
    return 1 if failed else 0


def write_guide_index(rehearsal, failed):
    rows = [row for row in rehearsal.steps if row['screenshot_retained']]
    expected = {name+'.png' for name in GUIDE_SHOTS.values()}
    actual = {row['screenshot'] for row in rows}
    if not failed:
        check(actual == expected, 'Kılavuz ekran listesi tamamlanmadı.')
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    lines = ['# CIV-189 · Müdürlük FR 2026 · ekran görüntüleri', '',
        'Yenileme: `python scripts/guide_screenshots.py --fr-guide`.', '',
        'Yalnız yerel PostgreSQL 16+ için `CIVENSA_TEST_POSTGRES_URL` kullanılır. '
        'Geçici veritabanı koşu sonunda silinir. Canlı veritabanına bağlanılmaz.', '',
        f'Kaynak kod: `{commit}`. Chromium: `{rehearsal.data["browser"]}`.',
        f'2026 kitap SHA-256: `{rehearsal.data["book_sha256"]}`.', '',
        'Veri notu: **SENTETİK**. Kurumsal başlık ve hedefler test kitabından; hesaplar, '
        'gerçekleşmeler, kanıt, beyan, iade ve onay deneme verisidir. Gerçek kişi adı yoktur. '
        'Parolalar rastgele üretilir, görsellere ve dosyalara yazılmaz.', '',
        '1440×900; yalnız giriş ve ilk parola ekranları ayrıca 390×900. '
        'deviceScaleFactor 1 · tr-TR · Europe/Istanbul · açık tema. '
        'Tarih ve kayıt kimlikleri değişebilir; bayt eşitliği beklenmez. '
        'Adım listesi sabittir. Her PNG ≤ 1.500.000 bayt; toplam ≤ 40.', '',
        '| Dosya | Harness adımı | Hesap | URL | Viewport |',
        '| --- | --- | --- | --- | --- |']
    for row in sorted(rows,key=lambda r:r['screenshot']):
        lines.append(f"| [{row['screenshot']}](img/{row['screenshot']}) | {row['step']} | {row['role']} | `{row['route']}` | {row['viewport']['width']}×900 |")
    (SCREENS.parent/'INDEX.md').write_text('\n'.join(lines)+'\n')


def run(url, *, guide=False):
    global OUT, SCREENS
    previous = OUT, SCREENS
    if guide:
        OUT = ROOT/'docs/reports/civ-189'
        SCREENS = ROOT/'docs/guides/mudurluk-fr-2026/img'
    try:
        return _run(url, guide=guide)
    finally:
        OUT, SCREENS = previous
