#!/usr/bin/env python3
"""CIV-040: inspect a PP Word book using a disposable, local PostgreSQL database.

Usage (from the repository root):
    python scripts/first_load_dryrun.py BOOK.docx --out docs/first-load/NAME.md

Set CIVENSA_TEST_POSTGRES_URL to a local PostgreSQL 16+ database whose user can
CREATE DATABASE. DATABASE_URL and MIGRATION_DATABASE_URL are never inputs.
The database created by this script is dropped even if import/validation fails.
"""
import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
NAME_MAP = ROOT / 'tests/fixtures/first_load/name_map.json'
YEAR = 2027
FUNDS = {'inside': 'Bütçe içi', 'outside': 'Bütçe dışı', 'total': 'Toplam'}


def label_key(text):
    text = str(text or '').lower().replace('ı', 'i')
    text = ''.join(c for c in unicodedata.normalize('NFKD', text)
                   if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]', '', text)


def scan_names(parsed):
    """Independent of parser header skipping; retain source locations for review."""
    labels = {label_key(s) for s in (
        'Performans Göstergesi', 'Performans Göstergeleri', 'Ölçü Birimi',
        'Gösterge Adı', 'Gösterge Kodu', 'Sıra No', 'Bütçe Yılı', 'Program Adı',
        'Alt Program Adı', 'İdare Birim Adı', 'Gerçekleşme', 'Hedef', 'Tahmin',
        'Göstergeye İlişkin Açıklama', 'Göstergelere İlişkin Açıklamalar',
        'Hesaplama Yöntemi', 'Verinin Kaynağı', 'Sorumlu İdare',
        'Planlanan', 'Bütçe', 'Değer', 'Faaliyetler', 'Ekonomik Ad',
    )}
    findings = []
    for department in parsed['departments']:
        name = department['name']
        for block in department['blocks']:
            for indicator in block['indicators']:
                text = indicator.get('name', '').strip()
                key = label_key(text)
                if not text:
                    cause = 'empty_indicator'
                elif key in labels or re.fullmatch(
                    r'20\d{2}(?:yili)?(?:gerceklesme|hedef|tahmin|butce|planlanan|deger|'
                    r'haziransonuharcama|yilsonu(?:harcama)?tahmin)(?:i|si)?', key
                ):
                    cause = 'header_label_indicator'
                elif re.fullmatch(r'20\d{2}(?:yili)?(?:20\d{2})?', key):
                    cause = 'year_indicator'
                else:
                    continue
                findings.append({'cause': cause, 'department': name, 'name': text,
                                 'table': block.get('table_number')})
        codes = defaultdict(list)
        for activity in department['activities']:
            text = activity.get('name', '').strip()
            location = [{'table': c.get('table_number'), 'row': c.get('row_number')}
                        for c in activity.get('costs', [])[:1]]
            if not text:
                findings.append({'cause': 'empty_activity', 'department': name,
                                 'name': text, 'locations': location})
            code = activity.get('code') or re.match(r'^\s*(\d+)[.)\s]', text)
            if code:
                code = code.group(1) if isinstance(code, re.Match) else str(code)
                codes[code].append({'name': text, 'locations': location})
        for code, activities in codes.items():
            if len(activities) > 1:
                findings.append({'cause': 'duplicate_activity_code', 'department': name,
                                 'code': code, 'activities': activities})
    return findings


@contextmanager
def environment(**values):
    previous = {key: os.environ.get(key) for key in values}
    try:
        for key, value in values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def local_test_url():
    from sqlalchemy.engine import make_url

    raw = os.getenv('CIVENSA_TEST_POSTGRES_URL')
    if not raw:
        raise ValueError('CIVENSA_TEST_POSTGRES_URL gerekli; yerel PostgreSQL test veritabanını belirtin.')
    # Importing app.db creates an engine, so mask application URLs even here.
    with environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None):
        from app.db import normalize_database_url
        try:
            url = make_url(normalize_database_url(raw))
        except Exception:
            raise ValueError('Test veritabanı URL biçimi geçersiz.') from None
    if (url.drivername != 'postgresql+psycopg'
            or url.host not in {'localhost', '127.0.0.1', '::1'}
            or not url.database or url.query):
        raise ValueError('Yalnızca localhost/127.0.0.1/::1 üzerinde, sorgu parametresiz '
                         'PostgreSQL test URL adresi kullanılabilir.')
    return url


@contextmanager
def disposable_database(url):
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool

    # Pin localhost to loopback; hostaddr also defeats inherited PGHOSTADDR.
    connect_args = {'hostaddr': '::1' if url.host == '::1' else '127.0.0.1',
                    'connect_timeout': 5}
    # libpq service/options must not redirect connections or alter session setup.
    cleared = {key: None for key in os.environ if key.startswith('PG')}
    name = 'civensa_first_load_' + uuid4().hex
    with environment(**cleared):
        admin = create_engine(url, isolation_level='AUTOCOMMIT', poolclass=NullPool,
                              connect_args=connect_args)
        created = False
        runtime = None
        try:
            with admin.connect() as connection:
                if int(connection.exec_driver_sql('SHOW server_version_num').scalar()) < 160000:
                    raise ValueError('Yerel PostgreSQL 16 veya üzeri gerekli.')
                connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
                created = True
            temporary = url.set(database=name).update_query_dict(
                {'hostaddr': connect_args['hostaddr'], 'connect_timeout': '5'})
            rendered = temporary.render_as_string(hide_password=False)
            with environment(DATABASE_URL=rendered, MIGRATION_DATABASE_URL=rendered, DEMO_SEED='0'):
                from alembic import command
                from alembic.config import Config

                command.upgrade(Config(str(ROOT / 'alembic.ini')), 'head')
                runtime = create_engine(temporary, poolclass=NullPool)
                yield runtime
        finally:
            if runtime is not None:
                runtime.dispose()
            try:
                if created:
                    with admin.connect() as connection:
                        connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
            finally:
                admin.dispose()


def inspect_import(db, parsed, filename):
    from sqlalchemy import select
    from sqlalchemy.exc import SQLAlchemyError
    from app.import_service import (DISPLAY_OVERRIDES, apply_import_batch,
                                    build_department_plan, department_key,
                                    import_validation_errors)
    from app.models import Department, ImportBatch, Organization, ReportingPeriod, User
    from app.program_service import validate_department

    names = json.loads(NAME_MAP.read_text(encoding='utf-8'))
    system_names = set(names['map'].values())
    for source in parsed['departments']:
        override = DISPLAY_OVERRIDES.get(department_key(source['name']))
        if override:
            system_names.add(override)
    organization = Organization(name='İlk yükleme denemesi Belediyesi')
    strategy = User(email='dryrun@example.invalid', full_name='Strateji deneme kullanıcısı',
                    role='strategy', password_hash='unused')
    period = ReportingPeriod(year=YEAR, status='draft', template_status='verified')
    db.add_all([organization, strategy, period])
    db.flush()
    db.add_all(Department(organization_id=organization.id, name=name)
               for name in sorted(system_names))
    db.commit()
    plan = build_department_plan(db, parsed)
    errors = import_validation_errors(parsed)
    unresolved = [m for m in plan['mappings'] if m['action'] != 'match']
    batch = ImportBatch(period_id=period.id, filename=filename, status='preview',
                        payload_json=json.dumps(parsed, ensure_ascii=False), created_by=strategy.id)
    db.add(batch)
    db.commit()
    applied = None
    apply_error = None
    # Exercise the real gate even if preview reports blocking issues. Never choose
    # source candidates or remove a bad directorate to make the book applicable.
    try:
        applied = apply_import_batch(db, batch)
        db.commit()
    except ValueError as exc:
        db.rollback()
        apply_error = str(exc)
    except SQLAlchemyError as exc:
        db.rollback()
        # SQL/driver messages can contain credentials or complete source payloads.
        apply_error = f'Veritabanı uygulama hatası ({type(exc).__name__}); paket uygulanmadı.'
    results = []
    for department in db.scalars(select(Department).order_by(Department.name)):
        validation_errors, warnings = validate_department(db, period.id, department.id)
        results.append({'name': department.name, 'ready': applied is not None and not validation_errors,
                        'errors': validation_errors, 'warnings': warnings})
    return {'plan': plan, 'errors': errors, 'unresolved': unresolved, 'applied': applied,
            'apply_error': apply_error, 'results': results, 'pending': names.get('pending_ali', [])}


def budget_sum(rows, expected):
    """Unknown/absent cells never turn into zero; retain a known subtotal too."""
    rows = list(rows)
    known = [Decimal(str(row['amount'])) for row in rows if row.get('amount') is not None]
    subtotal = sum(known, Decimal(0))
    complete = len(rows) == expected and len(known) == expected and expected > 0
    return subtotal if complete else None, subtotal, expected - len(known)


def cross_tables(parsed):
    checks = []
    for department in parsed['departments']:
        activities = department['activities']
        tables = department.get('economic_tables', [])
        for fund in FUNDS:
            activity = budget_sum((v for a in activities for v in a['costs']
                                   if (v['year'], v['kind'], v['funding_type']) == (YEAR, 'budget', fund)),
                                  len(activities))
            economic = budget_sum((v for t in tables for v in t.get('totals', {}).get(fund, [])
                                   if (v['year'], v['kind']) == (YEAR, 'budget')), len(tables))
            checks.append({'department': department['name'], 'fund': fund,
                           'activity': activity, 'economic': economic,
                           'status': 'Eksik/belirsiz' if None in (activity[0], economic[0]) else
                           ('Eşit' if activity[0] == economic[0] else 'FARK')})
    return checks


def cell(value):
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '&#124;').replace('\n', '<br>')


def money(value):
    if value is None:
        return 'Bilinmiyor'
    return f'{value:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def amount_text(result):
    amount, subtotal, unknown = result
    return money(amount) if amount is not None else f'Bilinmiyor (bilinen: {money(subtotal)}; eksik: {unknown})'


def state_counts(values):
    counts = Counter(v.get('state', 'missing') for v in values)
    return '; '.join(f'{key}: {value}' for key, value in sorted(counts.items())) or '—'


def report(parsed, inspection, path, digest):
    findings = scan_names(parsed)
    checks = cross_tables(parsed)
    plan = inspection['plan']
    ready = sum(r['ready'] for r in inspection['results'])
    lines = ['# 2027 PP ilk yükleme kuru denemesi', '',
             f'Dosya: `{path.name}` (taslak; nihai kitapla tekrar çalıştırılmalı).', '',
             f'SHA256: `{digest}`', '',
             '## Çalıştırma ve kapsam', '',
             '```sh',
             '# Yerel PostgreSQL 16+ test URL adresini CIVENSA_TEST_POSTGRES_URL olarak ayarlayın.',
             f'python scripts/first_load_dryrun.py {path.as_posix()} --out docs/first-load/dryrun-d3.md',
             '```', '',
             'Yalnızca CIVENSA_TEST_POSTGRES_URL okunur; yerel host ve sorgu parametresi kontrol edilir. '
             'Her çalıştırma ayrı bir veritabanı oluşturur, alembic upgrade head çalıştırır ve sonunda siler. '
             'Test kullanıcısının CREATE DATABASE yetkisi olmalıdır. Canlı veritabanı kullanılmaz.', '',
             'Tek kurum, Strateji kullanıcısı, doğrulanmış şablonlu 2027 dönemi ve name_map.json hedef adları '
             '(ayrıca kitapta bulunan yerleşik ad eşlemeleri) ekilir. Resmî faaliyet kataloğu, sorumluluklar '
             've elle veri düzeltmesi ekilmez; katalog bağlantısı eksikleri doğrulama sonucuna dahildir.', '',
             'name_map.json içinde teyit bekleyen kitap adları: ' + '; '.join(inspection['pending']) + '.', '',
             '## Genel sonuç', '',
             f'- Kitap müdürlükleri: {len(parsed["departments"])}; ekili/uygulama sonrası müdürlükler: {len(inspection["results"])}.',
             f'- Kartlar: {sum(len(d["blocks"]) for d in parsed["departments"])}; '
             f'göstergeler: {parsed["summary"]["indicator_count"]}; faaliyetler: {parsed["summary"]["activity_count"]}; '
             f'ekonomik tablolar: {parsed["summary"]["economic_table_count"]}.',
             f'- import_validation_errors: {len(inspection["errors"])}; source_conflicts: {len(plan["conflicts"])}; '
             f'çözümlenemeyen ad: {len(inspection["unresolved"])}.',
             f'- Uygulama: {"başarılı" if inspection["applied"] is not None else "engellendi"}; '
             f'gönderime hazır: {ready}/{len(inspection["results"])}.',
             f'- Doğrulama: {sum(len(r["errors"]) for r in inspection["results"])} hata, '
             f'{sum(len(r["warnings"]) for r in inspection["results"])} uyarı.',
             f'- Ad taraması: {len(findings)} bulgu; çapraz toplam farkı: '
             f'{sum(c["status"] == "FARK" for c in checks)}; '
             f'eksik/belirsiz karşılaştırma: {sum(c["status"] == "Eksik/belirsiz" for c in checks)}.', '',
             '| 2027 bütçesi | Faaliyetler | Ekonomik kaynak toplamları |',
             '| --- | ---: | ---: |']
    for fund, label in FUNDS.items():
        group = [c for c in checks if c['fund'] == fund]
        def overall(key):
            complete = all(c[key][0] is not None for c in group)
            subtotal = sum((c[key][1] for c in group), Decimal(0))
            unknown = sum(c[key][2] for c in group)
            return (subtotal if complete else None, subtotal, unknown)
        lines.append(f'| {label} | {amount_text(overall("activity"))} | {amount_text(overall("economic"))} |')
    lines.extend(['', '## Müdürlük bazında ayrıştırma', '',
                  '| Müdürlük | Kart | Gösterge | Gösterge değerleri / durum | Faaliyet | Faaliyet maliyet değerleri / durum | Personel değerleri / durum | Ekonomik tablo | Ekonomik değerler / durum |',
                  '| --- | ---: | ---: | --- | ---: | --- | --- | ---: | --- |'])
    for d in parsed['departments']:
        indicators = [i for b in d['blocks'] for i in b['indicators']]
        lines.append(f'| {cell(d["name"])} | {len(d["blocks"])} | {len(indicators)} | '
                     f'{state_counts(v for i in indicators for v in i["values"])} | {len(d["activities"])} | '
                     f'{state_counts(v for a in d["activities"] for v in a["costs"])} | '
                     f'{state_counts(d["personnel"])} | {len(d.get("economic_tables", []))} | '
                     f'{state_counts(v for t in d.get("economic_tables", []) for v in t["values"])} |')
    if inspection['applied'] is not None:
        result = inspection['applied']
        lines.extend(['', f'Uygulanan kayıtlar: {result["departments"]} müdürlük, {result["cards"]} kart, '
                      f'{result["indicators"]} gösterge, {result["activities"]} faaliyet, '
                      f'{result["economic_values"]} ekonomik değer, {result["personnel_values"]} ortak personel değeri. '
                      f'Alt programa bağlanamayan faaliyet: {result["unlinked_activities"]}.'])
    lines.extend(['', '## İçe aktarma hataları ve kaynak çelişkileri', '',
                  f'### import_validation_errors ({len(inspection["errors"])})', ''])
    # Parser errors carry table numbers; add the owning directorate/activity when known.
    owners = {}
    for d in parsed['departments']:
        for b in d['blocks']:
            owners[b.get('table_number')] = (d['name'], 'Gösterge tablosu')
        for a in d['activities']:
            for v in a['costs']:
                owners[v.get('table_number')] = (d['name'], a['name'])
        for t in d.get('economic_tables', []):
            owners[t['table_number']] = (d['name'], 'Ekonomik tablo')
    for error in inspection['errors']:
        table = re.search(r'Tablo (\d+)', error)
        owner = owners.get(int(table.group(1))) if table else None
        lines.append(f'- {cell(" / ".join(owner) if owner else "Müdürlük/faaliyet: ayrıştırılamadı")}: {cell(error)}')
    if not inspection['errors']:
        lines.append('Yok.')
    lines.extend(['', f'### source_conflicts ({len(plan["conflicts"])})', ''])
    for conflict in plan['conflicts']:
        # source_conflicts omits activity identity; recover it from candidate locations.
        locations = {(loc['table_number'], loc['row_number'])
                     for c in conflict['candidates'] for loc in c['locations']}
        activities = [a['name'] for d in plan['parsed']['departments']
                      if d['name'] == conflict['department'] for a in d['activities']
                      if any((v.get('table_number'), v.get('row_number')) in locations for v in a['costs'])]
        lines.append(f'- {cell(conflict["department"])} / {cell("; ".join(activities) or "Ortak personel ve SGK")}: '
                     f'{cell(conflict["message"])}')
    if not plan['conflicts']:
        lines.append('Yok.')
    if inspection['apply_error']:
        lines.extend(['', 'Uygulama engeli: ' + cell(inspection['apply_error'])])
    lines.extend(['', '## Sistem adına çözümlenemeyen kitap müdürlükleri', ''])
    lines.extend(f'- {cell(m["source_name"])}: {cell(m.get("reason", "Sistemde eşleşme yok; içe aktarıcı yeni müdürlük oluşturmayı öneriyor."))}'
                 for m in inspection['unresolved'])
    if not inspection['unresolved']:
        lines.append('Yok; tüm kitap müdürlükleri ekili sistem adlarıyla eşleşti.')
    lines.extend(['', '## 2027 bütçesi çapraz tablo kontrolü', '',
                  'Faaliyet maliyet hücrelerinin toplamı, ekonomik tablodaki açık Bütçe İçi / Bütçe Dışı / '
                  'Faaliyet Maliyeti Toplamı kaynak satırlarıyla doğrudan karşılaştırılır. Ekonomik toplamlar '
                  'ortak personel/SGK giderlerini de içerebilir; bu nedenle FARK tek başına içe aktarıcı hatası değildir. '
                  'Bu karşılaştırma personeli düşmez, tutarları değiştirmez. Gönderime hazırlık için mevcut '
                  'validate_department kuralları ayrıca uygulanır. Boş/belirsiz hücreler sıfır sayılmaz.', '',
                  '| Müdürlük | Finansman | Faaliyet toplamı | Ekonomik kaynak toplamı | Sonuç |',
                  '| --- | --- | ---: | ---: | --- |'])
    for c in checks:
        lines.append(f'| {cell(c["department"])} | {FUNDS[c["fund"]]} | {amount_text(c["activity"])} | '
                     f'{amount_text(c["economic"])} | {c["status"]} |')
    lines.extend(['', '## Ad düzeyinde tarama', '',
                  'Tarama ayrıştırılmış kaynak kayıtlarını inceler; ayrıştırıcının atladığı boş satırları '
                  'yeni kayıt saymaz. Kod tekrarı müdürlük içinde taranır, kayıtlar birleştirilmez.', ''])
    for cause, label in [('header_label_indicator', 'Tablo başlığı adlı gösterge'),
                         ('year_indicator', 'Yıl biçimli gösterge'), ('empty_indicator', 'Boş gösterge adı'),
                         ('empty_activity', 'Boş faaliyet adı'), ('duplicate_activity_code', 'Tekrarlanan faaliyet kodu')]:
        found = [f for f in findings if f['cause'] == cause]
        lines.extend([f'### {label} ({len(found)})', ''])
        lines.extend('- ' + cell(json.dumps(f, ensure_ascii=False)) for f in found)
        if not found:
            lines.append('Yok.')
        lines.append('')
    lines.extend(['## Uygulama sonrası gönderime hazırlık', '',
                  'Hazır = paket uygulandı ve validate_department hata listesi boş. Uyarılar engelleyici değildir. '
                  'Aşağıdaki hata ve uyarı metinleri doğrulayıcıdan aynen alınmıştır.', ''])
    for result in inspection['results']:
        lines.extend([f'### {result["name"]}', '', f'Gönderime hazır: **{"Evet" if result["ready"] else "Hayır"}**.', '',
                      f'Hatalar ({len(result["errors"])}):', ''])
        lines.extend('- ' + cell(e) for e in result['errors'])
        if not result['errors']:
            lines.append('Yok.')
        lines.extend(['', f'Uyarılar ({len(result["warnings"])}):', ''])
        lines.extend('- ' + cell(w) for w in result['warnings'])
        if not result['warnings']:
            lines.append('Yok.')
        lines.append('')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('docx', type=Path)
    parser.add_argument('--out', type=Path, help='Markdown çıktı dosyası; verilmezse stdout')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    try:
        url = local_test_url()  # Refuse unsafe targets before any connection.
        data = args.docx.read_bytes()
        from app.data_importer import parse_performance_docx
        from sqlalchemy.orm import Session

        parsed = parse_performance_docx(data)
        with disposable_database(url) as engine:
            with Session(engine, expire_on_commit=False) as db:
                inspection = inspect_import(db, deepcopy(parsed), args.docx.name)
        content = report(parsed, inspection, args.docx, hashlib.sha256(data).hexdigest())
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(content, encoding='utf-8')
            print(f'Rapor yazıldı: {args.out}')
        else:
            print(content)
    except ValueError as exc:
        print(f'Kuru deneme çalıştırılamadı: {exc}', file=sys.stderr)
        return 1
    except Exception as exc:
        # DB exceptions can include connection details; never print them/tracebacks.
        print(f'Kuru deneme çalıştırılamadı ({type(exc).__name__}); yerel PostgreSQL, '
              'dosya ve CREATE DATABASE yetkisini kontrol edin.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
