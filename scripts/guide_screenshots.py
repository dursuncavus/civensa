#!/usr/bin/env python3
"""CIV-054: refresh the Turkish PP guide from local, disposable book data.

Run from the checkout: python scripts/guide_screenshots.py --out docs/screenshots/guide-pp-v1
Only CIVENSA_TEST_POSTGRES_URL is an input; application database URLs are ignored.
"""
import argparse
from contextlib import closing, contextmanager, ExitStack
from copy import deepcopy
from dataclasses import dataclass
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'tests/fixtures/first_load/source/pp2027_print_d3.idml'
MAX_PNG_BYTES = 1_500_000


@dataclass(frozen=True)
class Shot:
    filename: str
    path: str
    visible: str
    account: str = 'strategy'
    action: str = 'top'
    full: bool = False


SHOTS = (
    Shot('01-genel-bakis-ust.png', '/dashboard', 'Genel Bakış · üst bölüm'),
    Shot('02-ilerleme-panosu.png', '/dashboard', 'Müdürlük İlerleme Panosu', action='progress'),
    Shot('03-mudurluk-strateji-gorunumu.png', '/department/{submitted}', 'Gönderilmiş paketin Strateji inceleme görünümü'),
    Shot('04-inceleme-kuyrugu.png', '/review', 'İnceleme Kuyruğu · Onayla / İade Et', full=True),
    Shot('05-iade-penceresi.png', '/review', 'İade penceresi · boş gerekçe · ardından Vazgeç', action='return'),
    Shot('06-faaliyet-eslestirme.png', '/activity-mapping', 'Faaliyet Eşleştirme · üst bölüm'),
    Shot('07-kurum-yapisi.png', '/structure', 'Kurum Yapısı · üst bölüm'),
    Shot('08-kullanicilar.png', '/users', 'Kullanıcılar · üst bölüm'),
    Shot('09-butce-aktarma.png', '/budget-reallocations', 'Bütçe Aktarma', full=True),
    Shot('10-sistem-durumu.png', '/operations', 'Sistem Durumu · üst bölüm'),
    Shot('11-denetim-gecmisi.png', '/audit', 'Denetim Geçmişi · üst bölüm'),
    Shot('12-moduller.png', '/modules', 'Modüller', full=True),
    Shot('13-giris.png', '/login', 'Oturum kapalı giriş ekranı · alanlar boş', 'anonymous'),
    Shot('14-veri-girisi-ust.png', '/department/{own}', 'Müdürlük veri girişi · üst bölüm', 'department'),
    Shot('15-faaliyet-maliyetleri.png', '/department/{own}', 'Faaliyet Maliyetleri sekmesi · başlık ve maliyet tablosu', 'department', 'costs'),
    Shot('16-gonder-bolumu.png', '/department/{own}', 'Müdürlük paketi · Stratejiye Gönder (tıklanmaz)', 'department', 'submit'),
    Shot('17-gonderim-yetkileri.png', '/submit-authorizations', 'Gönderim Yetkileri · üst bölüm', 'department'),
    Shot('18-parola-degistir.png', '/submit-authorizations', 'Parolamı Değiştir penceresi · alanlar boş · ardından Vazgeç', 'department', 'password'),
)


class GuideError(Exception):
    """Only fixed, credential-free messages may be passed here."""


def check(condition, message):
    if not condition:
        raise GuideError(message)


def setup(engine):
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from app.models import Department, ReportingPeriod, User
    from app.personal_accounts import prepare_user_creation
    from app.program_service import validate_department
    from app.released_permissions import audit_user_change, commit_user_change
    from app.security import hash_password
    from scripts.first_load_dryrun import inspect_import, parse_book

    print('2027 kitabı ayrıştırılıyor (kaynak tablo 195 hariç)…', flush=True)
    parsed, _ = parse_book(BOOK, exclude_source_tables=[195])
    print('Kitap verisi yükleniyor; hesaplar ve tek gönderim hazırlanıyor…', flush=True)
    with Session(engine, expire_on_commit=False) as db:
        inspection = inspect_import(db, deepcopy(parsed), BOOK.name)
        check(inspection['applied'] is not None and not inspection['apply_error'],
              '2027 kitap verisi gerçek içe aktarma servisinden yüklenemedi.')
        departments = db.scalars(select(Department).order_by(Department.name)).all()
        ready_names = {row['name'] for row in inspection['results'] if row['ready']}
        ready = [d for d in departments if d.name in ready_names]
        check(len(ready) >= 2, 'Kurulum için en az iki doğrulaması temiz müdürlük gerekli.')
        own = next((d for d in departments if d.name == 'Strateji Geliştirme Müdürlüğü'
                    and any(row['name'] == d.name and (row['stored']['indicators'] or
                            row['stored']['activities']) for row in inspection['results'])), None)
        fallback = own is None
        own = own or ready[0]
        submitted = next(d for d in ready if d.id != own.id)
        # The unique active-director constraint also covers strategy accounts.
        anchor = next(d for d in departments if d.id not in {own.id, submitted.id})
        period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == 2027))
        check(period.template_status == 'verified', '2027 şablonu doğrulanmış değil.')
        password = secrets.token_urlsafe(32)
        password_hash = hash_password(password)
        strategy = db.scalar(select(User).where(User.email == 'dryrun@example.invalid'))
        strategy.email = 'guide.strategy@example.invalid'
        strategy.full_name = 'Strateji Müdürü (test)'
        strategy.password_hash = password_hash
        strategy.department_id = anchor.id
        db.commit()
        # Bootstrap the imported strategy actor through the real appointment checks.
        candidate = User(full_name=strategy.full_name, email=strategy.email, role='strategy',
                         department_id=anchor.id, position='director', is_active=True)
        _, reason = prepare_user_creation(db, strategy, candidate)
        strategy.position = 'director'
        audit_user_change(db, strategy, strategy, 'position', 'staff', 'director', reason)
        commit_user_change(db)

        department = User(email='guide.department@example.invalid',
                          full_name='Strateji Geliştirme Müdürlüğü (test)', role='department',
                          department_id=own.id, position='director', is_active=True,
                          password_hash=password_hash)
        sender = User(email='guide.setup@example.invalid', full_name='Gönderim kurulumu (test)',
                      role='department', department_id=submitted.id, position='director',
                      is_active=True, password_hash=password_hash)
        for target in (department, sender):
            prepare_user_creation(db, strategy, target)
            db.add(target)
            commit_user_change(db)

        errors, _ = validate_department(db, period.id, submitted.id)
        check(not errors, 'Seçilen müdürlüğün PP doğrulaması temiz değil.')
        # This is the production submit implementation, also called by the API.
        from app.main import activate_period, submit_department
        activated = activate_period(period.id, db=db, user=strategy)
        check(activated.get('ok'), '2027 dönemi gerçek aktivasyon servisinden etkinleştirilemedi.')
        result = submit_department(submitted.id, db=db, user=sender)
        check(isinstance(result, dict) and result.get('ok'), 'Gerçek gönderim servisi paketi gönderemedi.')
        sender.is_active = False  # Setup-only actor; never opens a browser session.
        db.commit()
        return dict(own=own.id, submitted=submitted.id, own_name=own.name,
                    submitted_name=submitted.name, anchor_name=anchor.name,
                    fallback=fallback, ready=len(ready), password=password,
                    departments=len(departments),
                    indicators=sum(len(row['stored']['indicators']) for row in inspection['results']),
                    activities=sum(len(row['stored']['activities']) for row in inspection['results']),
                    accounts={'strategy': strategy.email, 'department': department.email})


def persisted_state(engine):
    """Prove that capturing/cancelling dialogs did not save a decision or password."""
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from app.models import AuditLog, Submission, SubmissionEvent, User
    with Session(engine) as db:
        return (
            list(db.execute(select(Submission.id, Submission.status, Submission.revision,
                                   Submission.return_note, Submission.reviewed_at).order_by(Submission.id))),
            list(db.execute(select(SubmissionEvent.id, SubmissionEvent.event_type).order_by(SubmissionEvent.id))),
            list(db.execute(select(User.id, User.password_hash).order_by(User.id))),
            list(db.execute(select(AuditLog.id).order_by(AuditLog.id))),
        )


@contextmanager
def local_http(engine, data):
    """Reuse the UI tests' loopback TestClient bridge, with pre-browser logins."""
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session
    from app.db import get_db
    from app.main import app

    def database():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = database
    try:
        with ExitStack() as stack:
            # Do not enter TestClient itself: lifespan would migrate again.
            clients = {name: stack.enter_context(closing(TestClient(app, follow_redirects=False)))
                       for name in ('strategy', 'department', 'anonymous')}
            for name, email in data['accounts'].items():
                response = clients[name].post('/login', data={'email': email, 'password': data['password']})
                check(response.status_code == 303 and response.headers.get('location') == '/modules',
                      'Yerel test hesabı ile giriş yapılamadı.')

            class Handler(BaseHTTPRequestHandler):
                def do_GET(self):
                    # No arbitrary hosts, absolute request targets, or write methods.
                    if not self.path.startswith('/') or self.path.startswith('//'):
                        self.send_error(400)
                        return
                    client = clients.get(self.headers.get('X-Guide-Account', 'anonymous'))
                    if client is None:
                        self.send_error(403)
                        return
                    try:
                        response = client.get(self.path)
                    except Exception:
                        self.send_error(500)
                        return
                    self.send_response(response.status_code)
                    for key, value in response.headers.items():
                        if key.lower() not in {'content-length', 'transfer-encoding', 'connection', 'set-cookie'}:
                            self.send_header(key, value)
                    self.send_header('Content-Length', str(len(response.content)))
                    self.end_headers()
                    self.wfile.write(response.content)

                def log_message(self, *args):
                    pass

            server = HTTPServer(('127.0.0.1', 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                yield f'http://127.0.0.1:{server.server_port}'
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
    finally:
        app.dependency_overrides.pop(get_db, None)


def capture(base, folder, data, results):
    from PIL import Image
    from playwright.sync_api import sync_playwright, expect

    with sync_playwright() as pw:
        options = {'headless': True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'):
            options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        with pw.chromium.launch(**options) as browser, ExitStack() as stack:
            contexts = {}
            blocked = []

            def guard(route):
                request = route.request
                if (urlsplit(request.url).netloc == urlsplit(base).netloc
                        and urlsplit(request.url).scheme == 'http'
                        and request.method == 'GET'):
                    route.continue_()
                else:
                    blocked.append(True)
                    route.abort()

            for name in ('strategy', 'department', 'anonymous'):
                context = stack.enter_context(browser.new_context(
                    viewport={'width': 1440, 'height': 900}, device_scale_factor=1,
                    color_scheme='light', locale='tr-TR', timezone_id='Europe/Istanbul',
                    reduced_motion='reduce', service_workers='block', accept_downloads=False,
                    extra_http_headers={'X-Guide-Account': name}))
                context.route('**/*', guard)
                contexts[name] = context

            data['browser'] = browser.version
            for shot in SHOTS:
                page = contexts[shot.account].new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(True))
                target = folder / shot.filename
                try:
                    path = shot.path.format(**data)
                    response = page.goto(base + path, wait_until='networkidle')
                    check(response is not None and response.status == 200 and page.url == base + path,
                          'Sayfa beklenen URL üzerinde HTTP 200 ile açılmadı.')
                    page.evaluate('document.fonts.ready')
                    if shot.account != 'anonymous':
                        expect(page.locator('.userbox strong')).to_have_text(
                            'Strateji Müdürü (test)' if shot.account == 'strategy'
                            else 'Strateji Geliştirme Müdürlüğü (test)')
                    if shot.action == 'progress':
                        page.get_by_role('heading', name='Müdürlük İlerleme Panosu', exact=True).evaluate(
                            "el => el.scrollIntoView({block: 'start', behavior: 'instant'})")
                    elif shot.action == 'costs':
                        page.get_by_role('button', name='Faaliyet Maliyetleri', exact=True).click()
                        heading = page.get_by_role('heading', name='Faaliyet Maliyetleri', exact=True)
                        expect(heading).to_be_visible()
                        heading.evaluate("el => el.scrollIntoView({block: 'start', behavior: 'instant'})")
                    elif shot.action == 'submit':
                        button = page.get_by_role('button', name='Stratejiye Gönder', exact=True)
                        button.evaluate("el => el.scrollIntoView({block: 'center', behavior: 'instant'})")
                        expect(button).to_be_visible()
                    elif shot.action == 'return':
                        row = page.get_by_role('row').filter(has=page.get_by_role(
                            'button', name='Onayla', exact=True))
                        expect(row).to_have_count(1)
                        row.get_by_role('button', name='İade Et', exact=True).click()
                        expect(page.locator('#reviewModal')).to_be_visible()
                    elif shot.action == 'password':
                        page.get_by_role('button', name='Parolamı Değiştir', exact=True).click()
                        expect(page.locator('#passwordModal')).to_be_visible()
                    else:
                        page.evaluate('window.scrollTo(0, 0)')
                    if shot.path == '/review':
                        expect(page.get_by_role('button', name='Onayla', exact=True)).to_have_count(1)
                    check(data['password'] not in page.content(), 'Parola sayfa içeriğine sızdı; görsel kaydedilmedi.')
                    check(not errors and not blocked, 'JavaScript hatası veya engellenmiş ağ/yazma isteği var.')
                    page.screenshot(path=str(target), full_page=shot.full, animations='disabled', caret='hide')
                    if shot.action in {'return', 'password'}:
                        modal = page.locator('#reviewModal' if shot.action == 'return' else '#passwordModal')
                        modal.get_by_role('button', name='Vazgeç', exact=True).click()
                        expect(modal).to_be_hidden()
                    # Lossless optimization only; never scale or quantize guide images.
                    with Image.open(target) as png:
                        check(png.width == 1440 and (shot.full or png.height == 900),
                              'Görsel boyutları istenen viewport ile eşleşmiyor.')
                        png.save(target, optimize=True)
                    check(target.stat().st_size < MAX_PNG_BYTES, 'PNG 1.500.000 bayt sınırının altında değil.')
                    check(not errors and not blocked, 'Yakalama sırasında JavaScript veya ağ/yazma hatası oluştu.')
                    results[shot.filename] = None
                except Exception as exc:
                    target.unlink(missing_ok=True)
                    results[shot.filename] = (str(exc) if isinstance(exc, GuideError) else
                                              f'Ekran adımı tamamlanamadı ({type(exc).__name__}); seçicileri ve yerel Chromium kurulumunu kontrol edin.')
                finally:
                    page.close()
                print(f'{shot.filename}: {"üretildi" if results[shot.filename] is None else "üretilemedi (INDEX.md)"}',
                      flush=True)
            check(not blocked, 'Yakalama sırasında yerel GET dışında bir istek engellendi.')


def write_index(folder, data, results):
    def cell(value):
        return str(value).replace('|', '&#124;').replace('\n', ' ')

    lines = ['# CIV-054 · Strateji PP kullanım kılavuzu · ekran görüntüleri', '',
             'Yenileme (depo kökünden):', '', '```sh',
             'python scripts/guide_screenshots.py --out docs/screenshots/guide-pp-v1', '```', '',
             '`CIVENSA_TEST_POSTGRES_URL` yalnızca yerel PostgreSQL 16+ ve CREATE DATABASE yetkili test rolünü göstermelidir. '
             'Uygulama bağlantı ayarları girdi olarak okunmaz. Geçici veritabanı başarıda, hatada ve SIGINT/SIGTERM sırasında silinir.', '',
             f'Kaynak: `{BOOK.relative_to(ROOT)}` · SHA-256: `{hashlib.sha256(BOOK.read_bytes()).hexdigest()}`.',
             '2027 dönemi aktif, şablon doğrulanmış; dry-run ile aynı gerçek servisler, yalnız kaynak tablo 195 hariç. '
             'Bu, mevcut prova verisidir; kitap eksikleri düzeltilmez, boş değerler doldurulmaz.', '',
             'Chromium · 1440×900 · deviceScaleFactor 1 · açık tema · tr-TR · Europe/Istanbul. '
             'FULL dışındaki görüntüler viewport çekimidir. PNG sınırı: <1.500.000 bayt.', '']
    if data:
        lines += [f"Yüklenen veri: {data['departments']} müdürlük, {data['indicators']} gösterge, {data['activities']} faaliyet.", '',
                  f"Başlangıçta doğrulaması temiz: {data['ready']} müdürlük. Tam bir paket gerçek gönderim servisiyle gönderildi: "
                  f"**{data['submitted_name']}** (ID {data['submitted']}); onay/iade yapılmadı.", '',
                  f"Veri giriş hesabının müdürlüğü: **{data['own_name']}** (ID {data['own']}); paket taslak bırakıldı.",
                  ('**Yedek müdürlük kullanıldı:** Strateji Geliştirme Müdürlüğü bulunamadı veya verisi yoktu; '
                   'ad sırasındaki ilk hazır müdürlük seçildi.' if data['fallback'] else
                   'Strateji Geliştirme Müdürlüğü bulundu ve kitap verisi içeriyor; yedek müdürlük kullanılmadı.'), '',
                  f"Strateji hesabının teknik müdürlük bağı: **{data['anchor_name']}**. Aynı müdürlükte iki aktif Müdürü "
                  'engelleyen uygulama kısıtı nedeniyle veri giriş hesabından farklıdır; rolü strategy, görevi director.', '',
                  'Hesaplar: **strategy** = Strateji Müdürü (test); **department** = Strateji Geliştirme Müdürlüğü (test), '
                  'görevi director; **anonymous** = oturum kapalı (13, müdürlük kullanıcısının giriş öncesi ekranı). '
                  'Ek **Gönderim kurulumu (test)** hesabı yalnız gönderim servisinde kullanılır ve tarayıcıdan önce pasifleştirilir. '
                  'Parola çalışma anında rastgele üretilir; yazdırılmaz veya dosyaya kaydedilmez.', '',
                  f"Chromium sürümü: {data.get('browser', 'başlatılamadı')}. Kaynak kod: "
                  f"`{subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}`. "
                  'Zaman damgaları her yerel yüklemede yenilenir; görsellerin birebir bayt eşitliği beklenmez.', '']
    lines += ['Tarayıcı başlamadan önce oturumlar gerçek yerel giriş akışıyla açılır. '
              'Çekim sırasında yalnız loopback GET istekleri geçer; form/API yazmaları ve dış ağ engellenir. '
              'İade ve parola pencereleri Vazgeç ile kapatılır. Gönderimler, olaylar, parola hashleri ve denetim kayıtları '
              'çekim öncesi/sonrası karşılaştırılır.', '',
              '| Dosya | URL yolu | Görünen içerik | Hesap | Çekim | Sonuç |',
              '| --- | --- | --- | --- | --- | --- |']
    for shot in SHOTS:
        path = shot.path.format(**data) if data else shot.path
        error = results[shot.filename]
        file = f'`{shot.filename}`' if error else f'[{shot.filename}]({shot.filename})'
        lines.append('| ' + ' | '.join([file, f'`{path}`', cell(shot.visible), shot.account,
                                        'FULL' if shot.full else 'Viewport',
                                        cell('ÜRETİLEMEDİ: ' + error) if error else 'Üretildi']) + ' |')
    missing = [name for name, error in results.items() if error]
    lines += ['', 'Üretilemeyen: ' + (', '.join(missing) if missing else 'Yok; 18/18 PNG üretildi.'), '']
    (folder / 'INDEX.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'docs/screenshots/guide-pp-v1')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    # Overwrite, never inspect or use inherited application connection settings.
    os.environ['DATABASE_URL'] = 'sqlite://'
    os.environ.pop('MIGRATION_DATABASE_URL', None)
    os.environ.update(CIVENSA_ENV='development', DEMO_SEED='0', COOKIE_SECURE='0',
                      SESSION_SECRET=secrets.token_urlsafe(48))
    logging.disable(logging.CRITICAL)
    from scripts.first_load_dryrun import disposable_database, local_test_url

    def interrupted(signum, frame):
        # Bypass per-shot Exception handlers so cancellation stops the whole run.
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        url = local_test_url()  # Reject unsafe URLs before any DB connection/output.
    except ValueError as exc:
        print(f'Ekran görüntüleri üretilemedi: {exc}', file=sys.stderr)
        return 1

    data = None
    results = {shot.filename: 'Yerel kurulum veya tarayıcı tamamlanamadı.' for shot in SHOTS}
    with TemporaryDirectory(prefix='civensa_guide_') as temporary:
        folder = Path(temporary)
        try:
            with disposable_database(url) as engine:
                import app.db as app_db
                # local_test_url imports app.db under a harmless SQLite URL. Bind
                # both normal request Sessions and health() to this disposable DB.
                app_db.engine.dispose()
                app_db.engine = engine
                app_db.SessionLocal.configure(bind=engine)
                data = setup(engine)
                with local_http(engine, data) as base:
                    before = persisted_state(engine)
                    check(sum(row[1] == 'submitted' for row in before[0]) == 1,
                          'İnceleme kuyruğunda tam bir gönderilmiş paket bulunmalı.')
                    capture(base, folder, data, results)
                    check(persisted_state(engine) == before, 'Çekim sırasında kalıcı durum değişti; görseller geçersiz.')
        except (Exception, KeyboardInterrupt) as exc:
            error = ('İşlem sinyal ile durduruldu.' if isinstance(exc, KeyboardInterrupt) else
                     str(exc) if isinstance(exc, GuideError) else
                     f'Yerel kurulum/çekim hatası ({type(exc).__name__}).')
            # A global safety/cleanup failure invalidates even already taken shots.
            results = {shot.filename: error for shot in SHOTS}
            for shot in SHOTS:
                (folder / shot.filename).unlink(missing_ok=True)
        if data:
            data.pop('password', None)
        write_index(folder, data, results)
        args.out.mkdir(parents=True, exist_ok=True)
        for shot in SHOTS:
            destination = args.out / shot.filename
            if results[shot.filename]:
                destination.unlink(missing_ok=True)  # Never leave stale success images.
            else:
                shutil.copyfile(folder / shot.filename, destination)
        shutil.copyfile(folder / 'INDEX.md', args.out / 'INDEX.md')
    produced = sum(error is None for error in results.values())
    print(f'{produced}/18 PNG üretildi. Ayrıntılar: {args.out / "INDEX.md"}')
    return 0 if produced == len(SHOTS) else 1


if __name__ == '__main__':
    raise SystemExit(main())
