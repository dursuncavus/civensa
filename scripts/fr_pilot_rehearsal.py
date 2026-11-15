"""CIV-228 pilot-week rehearsal (ROLLOUT C3, D-479 model).

Strateji holds one Müdür account per directorate ("<Müdürlük> (Strateji)");
there are no staff accounts. Indicator actuals arrive through Strateji's
master-workbook import (CIV-192); unit sections, tables, photo and EK-2 are
entered with the directorate account. The Strateji Müdürü only reviews,
returns and approves. Run: python scripts/guide_screenshots.py --fr-pilot
"""
from decimal import Decimal
import io
import json
from pathlib import Path
import re
import secrets
from urllib.parse import urlsplit

from scripts import fr_rehearsal as base
from scripts.guide_screenshots import ROOT, check

OUT = ROOT / 'docs/reports/civ-228'
SCREENS = ROOT / 'docs/screenshots/civ-228'
UNITS = [('fen', 'Fen İşleri Müdürlüğü', 'Fen İşleri Müdürlüğü'),
         ('afet', 'Afet İşleri ve Risk Değerlendirme Müdürlüğü', 'Afet İşleri ve Risk Yönetimi Müdürlüğü'),
         ('ozel', 'Özel Kalem Müdürlüğü', 'Özel Kalem Müdürlüğü')]
KEEP = {'Strateji Excel önizlemesi', 'Strateji Excel sonucu', 'Excel düzeltme sonucu',
        'Müdürlük hesabı ilk parola', 'Açıklamasız sapmayla gönderim denemesi', 'Birim raporunu gönder',
        'Gerekçeli iade', 'Düzelt ve yeniden gönder', 'Strateji bağımsız birim onayı'}
EXPLANATION = 'SENTETİK CIV-228: hedef farkı müdürlük yazısıyla açıklanmıştır.'


def setup(engine):
    """Load the 2026 book like CIV-188, then open the D-479 account set."""
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from app.models import Department, User
    from app.personal_accounts import prepare_user_creation
    from app.released_permissions import commit_user_change
    from app.security import hash_password
    # C3 has no staff accounts: base.setup only loads the book and the Strateji Müdürü.
    data = base.setup(engine, guide=False, unit_accounts=False)
    with Session(engine, expire_on_commit=False) as db:
        strategy = db.scalar(select(User).where(User.email == data['accounts']['strategy']))
        # Live (D-480): account 1 "Strateji Kullanıcısı" does the Strateji work,
        # the Strateji Müdürü (account 36) only reviews and approves.
        importer = User(email='civ228.strateji.kullanici@example.invalid', full_name='Strateji Kullanıcısı (SENTETİK)',
                        role='strategy', department_id=strategy.department_id, position='staff', is_active=True,
                        password_hash=hash_password(data['password']), must_change_password=False)
        prepare_user_creation(db, strategy, importer); db.add(importer); commit_user_change(db)
        data['accounts']['strategy_user'] = importer.email
        data['importer_id'] = importer.id
        data['units'] = []
        for key, name, system in UNITS:
            dep = db.scalar(select(Department).where(Department.name == system))
            check(dep is not None, 'Prova müdürlüğü bulunamadı.')
            # D-481: bulk CSV, Müdür row, "<Müdürlük> (Strateji)", first login sets the password.
            user = User(email=f'civ228.{key}.fr2026@example.invalid', full_name=f'{name} (Strateji)',
                        role='department', department_id=dep.id, position='director', is_active=True,
                        password_hash=hash_password(data['password']), must_change_password=True)
            prepare_user_creation(db, strategy, user); db.add(user); commit_user_change(db)
            data['accounts'][key] = user.email
            data['units'].append({'key': key, 'name': name, 'department_id': dep.id})
    data['shared_password'] = secrets.token_urlsafe(32)
    data['pilot'] = True
    return data


def workbook(indicators, explain):
    """Strateji's master workbook layout (D-443 headers) for the rehearsal units."""
    from openpyxl import Workbook
    book = Workbook(); sheet = book.active; sheet.title = 'veriler'
    sheet.append(['Sorumlu Müdürlük', 'Gösterge Adı', 'Hesaplama Yöntemi', 'Birim', '2026 Q1', '2026 Q2', '2026 Q3',
                  '2026 Q4', '2026 YILI 4. ÇEYREK GERÇEKLEŞEN TOPLAMI', 'Açıklama'])
    plan = []
    for row in indicators:
        target, value, deviates = row['target'], row['value'], row['deviates']
        quarters = [value / 4] * 4
        sheet.append([row['department'], row['name'], 'TOPLA', row['unit'], *[float(q) for q in quarters], None,
                      EXPLANATION if deviates and explain else None])
        plan.append(dict(row, target=str(target) if target is not None else None, value=str(value)))
    raw = io.BytesIO(); book.save(raw)
    return raw.getvalue(), plan


class PilotRehearsal(base.Rehearsal):
    def capture(self, page, role, title, start, result='OK', note=''):
        row = super().capture(page, role, title, start, result, note)
        if row['screenshot_retained'] and any(r['screenshot_retained'] and r['step'] == title for r in self.steps[:-1]):
            # One committed screen per step title; repeats stay in the disposable folder.
            (SCREENS / row['screenshot']).unlink(missing_ok=True); row['screenshot_retained'] = False
            self.write()
        elif title in KEEP and not row['screenshot_retained']:
            source = self.folder / 'full-screenshots' / row['screenshot']
            target = SCREENS / row['screenshot']
            target.write_bytes(source.read_bytes()); row['screenshot_retained'] = True
            self.write()
        return row

    def write(self):
        (OUT / 'steps.json').write_text(json.dumps(self.steps, ensure_ascii=False, indent=2) + '\n')

    def login(self, role):
        page = self.pages[role]
        self.goto(page, role, '/login', 'Giriş ekranı')
        page.locator('[name=email]').fill(self.data['accounts'][role])
        first = role in {u['key'] for u in self.data['units']} and role not in self.data.setdefault('changed', set())
        page.locator('[name=password]').fill(self.data['password'] if first or role.startswith('strategy')
                                             else self.data['shared_password'])
        self.click(page, role, page.get_by_role('button', name='Giriş yap', exact=False), 'Hesapla giriş')
        if first:
            check(urlsplit(page.url).path == '/change-password', 'Müdürlük hesabında ilk parola ekranı açılmadı.')
            self.capture(page, role, 'Müdürlük hesabı ilk parola', self.begin())
            # D-481: Strateji sets the same strong password on every directorate account.
            page.locator('#firstCurrentPassword').fill(self.data['password'])
            page.locator('#firstNewPassword').fill(self.data['shared_password'])
            page.locator('#firstConfirmPassword').fill(self.data['shared_password'])
            page.get_by_role('button', name='Parolamı belirle ve devam et').click()
            page.wait_for_url(self.base + '/modules')
            self.data['changed'].add(role)
            self.goto(page, role, '/modules', 'İlk paroladan sonra modüller')
        check(urlsplit(page.url).path == '/modules', 'UI girişi modüllere ulaşmadı.')
        check(self.data['shared_password'] not in page.content(), 'Parola sayfa içeriğinde bulundu.')
        return page

    def logout(self, role):
        page = self.pages[role]
        form = page.locator('form[action="/logout"]')
        if form.count():
            form.first.get_by_role('button').click(); page.wait_for_load_state('networkidle')

    def indicators(self, revision_id):
        from sqlalchemy.orm import Session
        from app import activity_contract_service as contract
        from app.models import User
        import app.db as app_db
        with Session(app_db.engine) as db:
            report = contract.report_data(db, db.get(User, self.data['importer_id']), revision_id)
        rows = []
        units = {u['department_id']: u for u in self.data['units']}
        for item in report['indicators']:
            definition = item['definition']
            if definition['department_id'] not in units:
                continue
            targets = definition['targets']
            target = (Decimal(str(targets[0]['value'])) if len(targets) == 1 and targets[0].get('state') == 'verified'
                      and targets[0].get('value') is not None else None)
            # One clear deviation per directorate (half the first usable target); others meet it.
            deviates = target not in (None, Decimal(0)) and not any(
                r['deviates'] for r in rows if r['department_id'] == definition['department_id'])
            value = (target / 2 if deviates else target) if target is not None else Decimal(8)
            rows.append({'department_id': definition['department_id'], 'department': item['department'],
                         'name': definition['name'], 'unit': definition['unit'] or 'Adet',
                         'target': target, 'value': value, 'deviates': deviates,
                         'report_indicator_id': item['report_indicator_id']})
        return rows

    def excel_import(self, revision, title, explain):
        role = 'strategy_user'; page = self.pages[role]
        content, plan = workbook(self.data['plan_rows'], explain)
        path = self.folder / ('2026-performans-degerlendirme-' + ('v2' if explain else 'v1') + '.xlsx')
        path.write_bytes(content)
        self.goto(page, role, '/activity-reports', title + ': Excel yükleme alanı')
        form = page.locator('form[action="/activity-reports/imports/preview"]')
        option = form.locator('select[name=revision_id] option').filter(has_text='2026').first
        form.locator('select[name=revision_id]').select_option(option.get_attribute('value'))
        form.locator('[name=file]').set_input_files(str(path))
        row = self.click(page, role, form.get_by_role('button', name='Excel önizlemesini aç'), 'Strateji Excel önizlemesi'
                         if not explain else 'Excel düzeltme önizlemesi')
        badges = ' · '.join(page.locator('section.reports-panel p').first.locator('.badge').all_inner_texts())
        selects = page.locator('select[name^=choice_]')
        total = selects.count()
        manual = 0
        # Same-named indicators of one directorate (different cards) need one row each;
        # Strateji picks the not yet claimed candidate, as the card context shows.
        claimed = {v.split(':')[0] for v in selects.evaluate_all('(els)=>els.map(e=>e.value)') if v}
        for i in range(selects.count()):
            select = selects.nth(i)
            if select.input_value() == '':
                values = select.locator('option').evaluate_all('(els)=>els.map(e=>e.value).filter(Boolean)')
                free = [v for v in values if v.split(':')[0] not in claimed] or values
                if free:
                    select.select_option(free[0]); manual += 1; claimed.add(free[0].split(':')[0])
        row['note'] = f'Önizleme: {badges}. Elle seçilen satır: {manual} / {total}.'
        self.write()
        result = self.click(page, role, page.get_by_role('button', name='Onaylanan satırları uygula'),
                            'Strateji Excel sonucu' if not explain else 'Excel düzeltme sonucu')
        counts = ' · '.join(page.locator('section.reports-panel p').first.locator('.badge').all_inner_texts())
        lines = page.locator('section.reports-panel ul li').all_inner_texts()
        result['note'] = f'Sonuç: {counts}. ' + ' | '.join(lines[:6])
        self.data.setdefault('imports', []).append({'title': title, 'preview': badges, 'manual': manual,
                                                    'rows': total, 'result': counts, 'lines': lines})
        written = sum(1 for line in lines if 'Yazıldı' in line)
        expected = sum(1 for r in plan if r['deviates']) if explain else len(plan)
        if written != expected:
            result['result'] = 'BLOCKER'
            result['note'] += f' Beklenen yazılan satır: {expected}; yazılan: {written}.'
        self.write()
        return written == expected

    def profile_apply(self, target):
        """Optional (CIV228_PROFILE=<file>): query count and cProfile of each import apply."""
        import cProfile, pstats
        from sqlalchemy import event
        from app import actual_import_service as service
        original = service.apply_import
        def wrapped(db, *args, **kwargs):
            queries = [0]
            def count(*_): queries[0] += 1
            event.listen(db.get_bind(), 'before_cursor_execute', count)
            profiler = cProfile.Profile()
            try:
                return profiler.runcall(original, db, *args, **kwargs)
            finally:
                event.remove(db.get_bind(), 'before_cursor_execute', count)
                out = io.StringIO()
                pstats.Stats(profiler, stream=out).sort_stats('cumulative').print_stats(25)
                with open(target, 'a') as handle:
                    handle.write(f'queries={queries[0]}\n' + out.getvalue())
        service.apply_import = wrapped

    def walk(self):
        from playwright.sync_api import sync_playwright
        import os
        if os.getenv('CIV228_PROFILE'):
            self.profile_apply(os.environ['CIV228_PROFILE'])
        pw = self.stack.enter_context(sync_playwright())
        options = {'headless': True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'): options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        browser = self.stack.enter_context(pw.chromium.launch(**options))
        self.data['browser'] = browser.version
        self.pages = {}
        for role in self.data['accounts']:
            context = self.stack.enter_context(browser.new_context(viewport={'width': 1440, 'height': 900},
                locale='tr-TR', timezone_id='Europe/Istanbul', reduced_motion='reduce',
                service_workers='block', extra_http_headers={'X-Guide-Account': role}, accept_downloads=True))
            def guard(route):
                if urlsplit(route.request.url).netloc == urlsplit(self.base).netloc:
                    route.continue_()
                else:
                    self.unexpected.append('Dış ağ isteği engellendi.'); route.abort()
            context.route('**/*', guard)
            page = context.new_page(); page.set_default_timeout(15000); page.set_default_navigation_timeout(180000)
            page.on('pageerror', lambda e: self.js.append(type(e).__name__ + ': ' + str(e)[:300]))
            page.on('response', lambda r: self.http.append({'route': urlsplit(r.url).path, 'status': r.status}) if r.status >= 400 else None)
            self.pages[role] = page
        # Live setup steps already done once (publish, revision, EK-1 reports); repeated here.
        strategy = self.login('strategy'); pid = self.data['period']
        self.goto(strategy, 'strategy', f'/report-builder?period_id={pid}', '2026 onaylı kitap yayın hazırlığı')
        form = strategy.locator('form[action="/report-builder/publish-approved-book"]')
        form.locator('[name=approval_reference]').fill('SENTETİK CIV-228 prova onay dayanağı; gerçek meclis kararı değildir.')
        self.click(strategy, 'strategy', form.get_by_role('button'), 'Onaylı kitaptan yayınla')
        self.goto(strategy, 'strategy', '/activity-reports', '2026 gösterge raporu oluşturma')
        option = strategy.locator('select[name=publication_id] option').filter(has_text='2026').first
        strategy.locator('select[name=publication_id]').select_option(option.get_attribute('value'))
        self.click(strategy, 'strategy', strategy.get_by_role('button', name='Seçilen yayınla rapor oluştur'), 'Yayına bağlı 2026 FR revizyonu oluştur')
        revision = urlsplit(strategy.url).path
        check('/revisions/' in revision, 'FR revizyonu oluşmadı.')
        self.goto(strategy, 'strategy', '/activity-sections', '2026 birim ve idare raporları oluşturma')
        strategy.locator('form[action="/activity-sections/years"] select[name=period_id]').select_option(str(pid))
        self.click(strategy, 'strategy', strategy.get_by_role('button', name='Raporları oluştur'), '2026 EK-1 raporlarını oluştur')
        # Pilot week: Strateji Kullanıcısı imports the directorates' rows (first file, explanations missing).
        self.login('strategy_user')
        self.data['plan_rows'] = self.indicators(int(re.search(r'/revisions/(\d+)', revision).group(1)))
        check(len({r['department_id'] for r in self.data['plan_rows'] if r['deviates']}) == 3,
              'Her prova müdürlüğünde hedefi doğrulanmış bir gösterge bulunamadı.')
        self.data['first_import_complete'] = self.excel_import(revision, 'İlk Excel', explain=False)
        approvals = []
        for unit in self.data['units']:
            role = unit['key']; page = self.login(role)
            self.goto(page, role, revision, 'Aktarılan göstergeleri müdürlük hesabıyla kontrol et',
                      note=page.locator('.indicator-report-summary').inner_text() if page.locator('.indicator-report-summary').count() else '')
            self.goto(page, role, '/activity-sections', 'Müdürlük 2026 birim raporunu bul')
            heading = re.compile('^(2026 · )?' + re.escape(unit['name']) + '$')
            group = page.locator('article.report-group').filter(has=page.get_by_role('heading', name=heading))
            document = urlsplit(group.locator('a[href*="/activity-sections/reports/"]').first.get_attribute('href')).path
            unit['document'] = document
            self.sections(page, role, document)
            self.unit_tables(page, role, document)
            self.goto(page, role, document, 'Gönderim öncesi birim raporu')
            row = self.click(page, role, page.get_by_role('button', name='Strateji’ye gönder', exact=True),
                             'Açıklamasız sapmayla gönderim denemesi')
            body = page.locator('body').inner_text()
            if 'hedef farkı açıklaması eksik' in body:
                row['note'] = 'Beklenen engel: açıklamasız sapma ile gönderilemedi.'
            elif self.data['first_import_complete']:
                row['result'] = 'BLOCKER'; row['note'] = 'Beklenen sapma engeli görünmedi: ' + body[:600]
            else:
                row['note'] = 'İlk Excel aktarımı göstergeleri yazmadığı için başka engel: ' + body[:600]
            self.write()
            unit['blocked_text'] = body[:2000]
        # Strateji collects the explanations and imports the corrected file.
        self.data['second_import_complete'] = self.excel_import(revision, 'Açıklamalı Excel', explain=True)
        strategy = self.pages['strategy']
        for unit in self.data['units']:
            role = unit['key']; page = self.pages[role]; document = unit['document']
            if not self.workflow(page, role, document, 'Strateji’ye gönder', 'Birim raporunu gönder', 'Gönderildi'):
                continue
            self.goto(strategy, 'strategy', document, 'Strateji birim incelemesi')
            strategy.get_by_label('İade gerekçesi').fill('SENTETİK: Faaliyet anlatımına tamamlanma bilgisini ekleyin.')
            self.click(strategy, 'strategy', strategy.get_by_role('button', name='Gerekçeyle iade et'), 'Gerekçeli iade')
            check(strategy.locator('[data-ar-workflow-status]').inner_text() == 'İade edildi', 'İade başarısız.')
            self.goto(page, role, document + '?code=III.B.1', 'İade notunu gör ve düzelt')
            form = page.locator('form[data-ar-section-form]')
            check(form.count() == 1, 'İade düzeltme formu bulunamadı.')
            form.locator('[name=text]').fill(base.SYNTHETIC + ' SENTETİK düzeltme: faaliyet tamamlandı.')
            form.locator('[name=status]').select_option('ready')
            self.click(page, role, form.get_by_role('button', name='Bölümü kaydet'), 'İade notuna göre düzeltmeyi kaydet')
            check(self.workflow(page, role, document, 'Yeniden gönder', 'Düzelt ve yeniden gönder', 'Gönderildi'), 'Yeniden gönderim başarısız.')
            self.goto(strategy, 'strategy', document, 'Strateji yeniden inceleme')
            self.click(strategy, 'strategy', strategy.get_by_role('button', name='Birimi onayla', exact=True), 'Strateji bağımsız birim onayı')
            status = strategy.locator('[data-ar-workflow-status]').inner_text() if strategy.locator('[data-ar-workflow-status]').count() else ''
            if status != 'Onaylandı':
                self.steps[-1]['result'] = 'BLOCKER'; self.steps[-1]['note'] = 'Onay olmadı: ' + strategy.locator('body').inner_text()[:600]
                self.write(); continue
            approvals.append(unit['key'])
            self.downloads(strategy, unit, 'Onaylı')
        self.data['approvals'] = approvals


def write_report(rehearsal, failed):
    steps = rehearsal.steps
    data = rehearsal.data
    def cell(value): return str(value).replace('|', '&#124;').replace('\n', ' ')
    labels = {'strategy': 'Strateji Müdürü', 'strategy_user': 'Strateji Kullanıcısı'}
    labels.update({u['key']: u['name'] + ' (Strateji)' for u in data['units']})
    count = lambda kind: sum(s['result'] == kind for s in steps)
    lines = ['# CIV-228 — Pilot haftası provası (C3, D-479 modeli)', '',
        '**SENTETİK prova. Yalnız atılabilir yerel PostgreSQL; canlı veritabanı, birleştirme ve dağıtım yok.**', '',
        'Yeniden çalıştırma: `python scripts/guide_screenshots.py --fr-pilot` (`CIVENSA_TEST_POSTGRES_URL` yerel test PostgreSQL, isteğe bağlı `CIVENSA_CHROMIUM_PATH`).', '',
        '## Senaryo', '',
        'Hesaplar canlıdaki D-479/D-480/D-481 düzenini taklit eder: Strateji Müdürü (yalnız inceleme, iade, onay), '
        'Strateji Kullanıcısı (Excel içe aktarma) ve Fen İşleri, Afet İşleri ve Risk Değerlendirme, Özel Kalem için '
        'birer "<Müdürlük> (Strateji)" Müdür hesabı. Personel hesabı yoktur. Müdürlük hesapları ilk girişte aynı güçlü parolaya geçirilir.', '',
        'Akış: onaylı kitap yayını → 2026 FR revizyonu → EK-1 raporları → Strateji Kullanıcısı ana Excel dosyasını önizler ve uygular '
        '(her müdürlükte bir gösterge hedefin yarısı, açıklama yok) → müdürlük hesabıyla bölümler, Tablo 1/2/7/8, fotoğraf, EK-2 → '
        'gönderim denemesi (açıklamasız sapma engeli) → açıklamalı Excel yeniden aktarılır → gönder → Strateji iade → düzelt → '
        'yeniden gönder → Strateji Müdürü onaylar → Word/PDF.', '',
        '## Bulgular', '', '<!-- CIV228_FINDINGS -->', '',
        '## Excel aktarımları', '']
    for item in data.get('imports', []):
        lines.append(f"- **{item['title']}**: önizleme {item['preview']}; elle seçilen {item['manual']} / {item['rows']} satır; sonuç {item['result']}.")
    lines += ['', '## Özet', '', f"OK {count('OK')} · SLOW {count('SLOW')} · BLOCKER {count('BLOCKER')} · toplam {len(steps)} adım. "
        f"Onaylanan birimler: {', '.join(data.get('approvals', [])) or 'yok'}. "
        f"Koşu: {'BEKLENMEYEN HATA (unexpected.txt)' if failed else 'tamamlandı'}.", '',
        '## Adım çizelgesi', '', '| Hesap | Adım | Sonuç | Sayfa | Ekran | Süre (ms) | Not |', '| --- | --- | --- | --- | --- | ---: | --- |']
    for step in steps:
        notes = []
        if step['http']: notes.append('HTTP: ' + ', '.join(f"{r['status']} {r['route']}" for r in step['http']))
        if step['server_errors']: notes.append('Sunucu: ' + json.dumps(step['server_errors'], ensure_ascii=False))
        if step['js']: notes.append('JS: ' + str(step['js']))
        if step['note']: notes.append(step['note'][:700])
        lines.append('| ' + ' | '.join([cell(labels.get(step['role'], step['role'])), cell(step['step']), step['result'],
            '`' + cell(step['route']) + '`', (f"[PNG](../../screenshots/civ-228/{step['screenshot']})" if step['screenshot_retained'] else '—'),
            str(step['load_ms']), cell(' '.join(notes) or '—')]) + ' |')
    findings = OUT / 'findings.md'
    text = '\n'.join(line.rstrip() for line in lines) + '\n'
    if findings.exists():
        text = text.replace('<!-- CIV228_FINDINGS -->', findings.read_text().strip())
    (OUT / 'report.md').write_text(text)


def run(url):
    saved = base.OUT, base.SCREENS
    base.OUT, base.SCREENS = OUT, SCREENS
    try:
        return base._run(url, pilot=True)
    finally:
        base.OUT, base.SCREENS = saved
