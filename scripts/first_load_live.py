#!/usr/bin/env python3
"""Basılı PP 2027: varsayılan salt okunur plan; korumalı, müdürlük bazlı ilk yükleme."""
import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
import time
import traceback
from urllib.parse import parse_qsl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.first_load_dryrun import environment, parse_book

# app.db creates its default engine at import time. Initialize it against an
# inert in-memory URL even for callers using the functions outside main().
with environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None):
    import app.db  # noqa: F401

from scripts.book_to_load_docx import FIRST_LOAD_BOOKS

BOOK = ROOT / 'tests/fixtures/first_load/source' / FIRST_LOAD_BOOKS[2027][0]
BOOK_SHA256 = FIRST_LOAD_BOOKS[2027][1]
HEAD = 'c219b1c2d3e4'
TARGET_ENV = 'CIVENSA_FIRST_LOAD_DATABASE_URL'
MARKER = 'first_load_department'
LOCK = 520027
TTY_REFUSAL = 'Onay için etkileşimli terminal gerekli; komutu tee/grep olmadan doğrudan çalıştırın. 0 satır yazıldı.'
COUNT_LABELS = {
    'departments': 'müdürlük',
    'created_departments': 'oluşturulan müdürlük',
    'cards': 'kart',
    'indicators': 'gösterge',
    'indicator_values': 'gösterge değeri',
    'activities': 'faaliyet',
    'activity_cost_values': 'faaliyet maliyeti',
    'activity_catalogue_links': 'katalog bağlantısı',
    'economic_values': 'ekonomik değer',
    'department_cost_values': 'personel/SGK maliyeti',
    'submissions': 'taslak teslim',
    'submission_events': 'teslim olayı',
    'department_scopes': 'müdürlük kapsamı',
    'subprogram_scopes': 'alt program kapsamı',
}


def open_tty():
    return io.TextIOWrapper(open('/dev/tty', 'r+b', buffering=0), encoding='utf-8', write_through=True)


def read_confirmation(prompt):
    try:
        with open_tty() as tty:
            tty.write(prompt)
            tty.flush()
            line = tty.readline()
    except OSError:
        raise Refusal(TTY_REFUSAL) from None
    if not line:
        raise EOFError
    return line.rstrip('\r\n')


def print_progress(index, total, name, action, elapsed):
    print(f'[{index}/{total}] {name} · {action} · {elapsed:.1f} sn', file=sys.stderr, flush=True)


@contextmanager
def phase(name):
    started = time.monotonic()
    print(f'Aşama: {name} …', file=sys.stderr, flush=True)
    yield
    print(f'Aşama: {name} · tamam · {time.monotonic() - started:.1f} sn', file=sys.stderr, flush=True)


def format_summary(result, *, year=2027, apply=False, clear_preprint=False):
    is_clear = clear_preprint or str(result.get('mode', '')).startswith('clear-preprint')
    mode = 'TEMİZLİK' if is_clear else ('UYGULAMA' if apply or result.get('mode') == 'uygula' else 'PLAN')
    departments = result.get('departments', [])
    failed = len(result.get('failed', []))
    skipped = len(result['skipped']) if 'skipped' in result else sum(d.get('action') == 'skip' for d in departments)
    if is_clear:
        matched = len(departments)
        created = 0
    else:
        matched = sum(d.get('action') == 'match' for d in departments)
        created = sum(d.get('action') == 'create' for d in departments)
    counts = result.get('counts') if 'counts' in result else result.get('totals', {})
    totals_text = ' · '.join(f'{COUNT_LABELS.get(k, k)}: {v}' for k, v in counts.items()) or '0'
    refusals = result.get('refusals', failed)
    if isinstance(refusals, list):
        refusals = len(refusals)
    lines = [
        'ÖZET',
        f'Mod: {mode} · Yıl: {year} · Kitap SHA256: {book_config(year)[1][:12]}',
        f'Müdürlükler: eşleşen: {matched} · oluşturulan: {created} · atlanan: {skipped} · başarısız: {failed}',
        f'Toplamlar: {totals_text}',
        f'Reddedilen: {refusals}',
    ]
    if year == 2026:
        protected = (result.get('protected_2027_before') == result.get('protected_2027_after')
                     and ('protected_2027_before' in result or mode == 'PLAN'))
        lines.append(f"2027 korunuyor: {'EVET' if protected else 'HAYIR'}")
    return '\n'.join(lines)


class Refusal(ValueError):
    """Only controlled, secret-free messages may cross the CLI boundary."""


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default includes rejected argument values, possibly a URL.
        self.exit(2, 'DURDU: Komut seçenekleri geçersiz. --help çıktısını kullanın; bağlantıyı yalnız gizli ortam değişkeninde girin.\n')


def book_config(year=2027):
    if year == 2027:
        return BOOK, BOOK_SHA256
    from scripts.book_to_load_docx import FIRST_LOAD_BOOKS
    name, digest = FIRST_LOAD_BOOKS[year]
    return BOOK.with_name(name), digest


def verify_book(path, *, year=2027):
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != book_config(year)[1]:
        raise Refusal('Kitap SHA256 uyuşmuyor. Onaylı basılı IDML dosyasını kullanın; yükleme durdu.')
    # Parse exactly the verified bytes, even if the original file is replaced.
    with TemporaryDirectory(prefix='civensa_verified_book_') as directory:
        snapshot = Path(directory) / book_config(year)[0].name
        snapshot.write_bytes(data)
        parsed, _ = parse_book(snapshot, **({'year': year} if year == 2026 else {}))
    return parsed


def verify_backup(path, now=None):
    """Check the manifest recovery point against the verified dump."""
    if path is None:
        raise Refusal('--backup gerekli. Başarılı doğrulanmış yedeğin .dump yolunu belirtin.')
    try:
        manifest = json.loads(path.with_suffix('.manifest.json').read_text())
        stamp = datetime.fromisoformat(manifest['utc_timestamp'].replace('Z', '+00:00'))
        current = now or datetime.now(timezone.utc)
        age = (current - stamp).total_seconds()
        with path.open('rb') as stream:
            magic = stream.read(5)
            stream.seek(0)
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        valid = (stamp.tzinfo is not None and 0 <= age < 3600
                 and path.is_file() and magic == b'PGDMP'
                 and manifest['file_name'] == path.name
                 and manifest['file_size_bytes'] == path.stat().st_size
                 and manifest['sha256'] == digest
                 and manifest['alembic_version']['version_num'] == [HEAD]
                 and bool(manifest['public_table_row_counts']))
    except (OSError, KeyError, ValueError, TypeError, AttributeError):
        valid = False
    if not valid:
        raise Refusal('Yedek doğrulanamadı: .dump ve .manifest.json, SHA256/boyut, şema ve '
                      '60 dakikadan yeni yedek zamanı gerekli. db-backup.md adımlarını tekrarlayın.')


def target_url():
    from sqlalchemy.engine import make_url
    raw = os.environ.get(TARGET_ENV)
    if not raw:
        raise Refusal(f'{TARGET_ENV} gerekli. Bağlantıyı gizli terminal isteminde girin.')
    try:
        for prefix in ('postgres://', 'postgresql://'):
            if raw.startswith(prefix):
                raw = 'postgresql+psycopg://' + raw[len(prefix):]
        url = make_url(raw)
        # libpq host/service overrides can silently redirect a reviewed endpoint.
        # Retain blank values: make_url otherwise drops e.g. channel_binding=.
        query_pairs = parse_qsl(raw.partition('?')[2], keep_blank_values=True)
        if any(key not in {'sslmode', 'channel_binding'}
               or (key == 'channel_binding' and value != 'require') for key, value in query_pairs):
            raise ValueError
        if (url.drivername != 'postgresql+psycopg' or not url.host or not url.database
                or ',' in url.host or set(url.query) - {'sslmode', 'channel_binding'}
                or url.query.get('channel_binding', 'require') != 'require'
                or url.query.get('sslmode', 'require') not in {'require', 'verify-ca', 'verify-full'}):
            raise ValueError
        if url.host not in {'localhost', '127.0.0.1', '::1'}:
            if '-pooler' in url.host or 'sslmode' not in url.query:
                raise ValueError
    except Exception:
        raise Refusal('Hedef bağlantı geçersiz. Doğrudan PostgreSQL adresi ve uzak hedefte '
                      'sslmode=require (veya verify-ca/verify-full) kullanın; isteğe bağlı channel_binding '
                      'yalnız require olabilir. Başka bağlantı parametresi eklemeyin.') from None
    return url


def require_head(db):
    from sqlalchemy import text
    versions = list(db.scalars(text('SELECT version_num FROM public.alembic_version ORDER BY version_num')))
    if versions != [HEAD]:
        raise Refusal(f'Hedef şema uyuşmuyor; yalnız {HEAD} kabul edilir. Migrasyon çalıştırmayın; sorumluya bildirin.')


SCHEMA_NAME = re.compile(r'[a-z_][a-z0-9_]{0,62}')
SQLSTATE = re.compile(r'[0-9A-Z]{5}')


def failure_detail(exc):
    """Exception class plus schema identifiers and code location only (D-396).

    Driver messages can quote row values, so message text never leaves; table,
    constraint and column names come from the schema, frame locations from code.
    """
    parts = [type(exc).__name__]
    orig = getattr(exc, 'orig', None)
    code = getattr(orig, 'sqlstate', None) or getattr(orig, 'pgcode', None)
    if isinstance(code, str) and SQLSTATE.fullmatch(code):
        parts.append('SQLSTATE ' + code)
    diag = getattr(orig, 'diag', None)
    for label, attr in (('tablo', 'table_name'), ('kısıt', 'constraint_name'), ('sütun', 'column_name')):
        value = getattr(diag, attr, None)
        if isinstance(value, str) and SCHEMA_NAME.fullmatch(value):
            parts.append(f'{label} {value}')
    # Only project code (a virtualenv may live inside the checkout).
    for name in getattr(exc, 'changed_tables', None) or []:
        if isinstance(name, str) and SCHEMA_NAME.fullmatch(name):
            parts.append(f'tablo {name}')
    frames = [(Path(frame.filename).resolve().relative_to(ROOT).as_posix(), frame.lineno)
              for frame in traceback.extract_tb(exc.__traceback__)
              if Path(frame.filename).resolve().is_relative_to(ROOT)]
    frames = [(name, line) for name, line in frames if name.split('/')[0] in {'app', 'scripts', 'ops', 'tests'}]
    if frames:
        parts.append(f'konum {frames[-1][0]}:{frames[-1][1]}')
    return ', '.join(parts)


def content_departments(db, period_id):
    from sqlalchemy import select
    from app.models import Activity, DepartmentCostValue, EconomicValue, Indicator, ReportCard
    ids = set()
    for model in (Activity, DepartmentCostValue, EconomicValue, Indicator, ReportCard):
        ids.update(db.scalars(select(model.department_id).where(model.period_id == period_id)))
    return ids


def completed_departments(db, period_id, *, year=2027):
    from app.first_load_sources import active_first_loads
    completed = set()
    loads = active_first_loads(db, period_id)
    if loads is None:
        raise Refusal('İlk yükleme değiştirme geçmişi uyuşmuyor; 0 satır yazıldı. Sorumluya bildirin.')
    for audit, batch in loads:
        try:
            details = json.loads(audit.details)
            if (batch.status != 'applied' or details['book_sha256'] != book_config(year)[1]
                    or details['year'] != year):
                raise ValueError
            completed.add(int(details['department_id']))
        except (ValueError, KeyError, TypeError):
            raise Refusal('İlk yükleme geçmişi uyuşmuyor. Otomatik devam engellendi; sorumluya bildirin.') from None
    return completed


def context(db, organization_id, actor_id, resume, *, year=2027):
    from sqlalchemy import select
    from app.models import Organization, User, ReportingPeriod, Program, OfficialActivity, ImportBatch
    require_head(db)
    orgs = db.scalars(select(Organization)).all()
    if len(orgs) != 1 or orgs[0].id != organization_id:
        raise Refusal('Tek kurum ve doğru --organization-id gerekli. Kurum numarasını sorumluya doğrulatın.')
    actor = db.get(User, actor_id)
    if not actor or not actor.is_active or actor.role not in {'strategy', 'admin'}:
        raise Refusal('--actor-id etkin Strateji/yönetici kullanıcısı olmalıdır. Kullanıcı numarasını doğrulatın.')
    period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == year))
    if period and (period.status not in {'draft', 'active'} or period.template_status != 'verified'):
        raise Refusal(f'{year} dönemi açık ve şablonu doğrulanmış olmalıdır. Dönem durumunu sorumluya bildirin.')
    completed = completed_departments(db, period.id, year=year) if period else set()
    if period:
        existing = content_departments(db, period.id)
        other = any(db.scalar(select(model.id).where(model.period_id == period.id).limit(1))
                    for model in (Program, OfficialActivity, ImportBatch))
        # CIV-058 keeps approved import history/catalogue. Only the exact,
        # unchanged clearance receipt permits an otherwise empty first load.
        if year == 2027 and other and not existing and not completed:
            from scripts.clear_preprint_2027 import clearance
            if clearance(db, period.id):
                other = False
        if (existing or other or completed) and not resume:
            raise Refusal(f'{year} PP verisi zaten var; 0 satır yazıldı. Yalnız belgelenmiş --resume ile devam edin.')
        if resume and ((existing - completed) or (other and not completed)):
            raise Refusal(f'{year} PP verisinde bu yüklemeye ait olmayan kayıt var; 0 satır yazıldı. Devam engellendi.')
    return actor, period, completed


def department_payload(parsed, source):
    # Structural parser errors remain blocking. Institution findings are never data.
    payload = dict(departments=[deepcopy(source)], summary=parsed['summary'],
                errors=parsed.get('errors', []),
                rejected_economic_tables=parsed.get('rejected_economic_tables', []),
                **({key: parsed[key] for key in ('first_load_year', 'book_department_names',
                    'catalogue_descriptions') if key in parsed} if parsed.get('first_load_year') == 2026 else {}))

    if parsed.get('first_load_year') == 2026:
        payload['catalogue_descriptions'] = [d for d in parsed.get('catalogue_descriptions', [])
                                             if d['department'] == source['name']]
    return payload


def planned_counts(source):
    return dict(departments=1, cards=len(source['blocks']),
                indicators=sum(len(b['indicators']) for b in source['blocks']),
                activities=len(source['activities']),
                economic_values=len({tuple(v[k] for k in ('year', 'kind', 'category', 'program_group', 'funding_type'))
                                     for t in source.get('economic_tables', []) for v in t['values']}))


def department_plan(db, parsed, completed, *, year=2027):
    from app.import_service import build_department_plan, department_key
    plan = build_department_plan(db, parsed)
    mapping = {department_key(m['source_name']): m for m in plan['mappings']}
    if year == 2026:
        bad = [m['source_name'] for m in plan['mappings']
               if m['action'] != 'match' or m['confidence'] != 1]
        if bad:
            raise Refusal('2026 için tekil mevcut müdürlük eşleşmesi gerekli; 0 satır yazıldı: ' + ', '.join(bad))
    items = []
    for source in plan['parsed']['departments']:
        m = mapping[department_key(source['name'])]
        reason = None
        if m.get('department_id') in completed:
            reason = 'Önceki ilk yüklemede tamamlandı; kullanıcı düzeltmeleri korunarak atlandı.'
        elif m['action'] == 'unresolved' or (m['action'] == 'match' and m['confidence'] != 1):
            reason = 'Tekil kesin müdürlük eşleşmesi yok; sorumluya bildirin.'
        items.append(dict(source=source, mapping=m, skip=reason))
    return items


def department_action(item):
    result = dict(source_name=item['source']['name'])
    if item['skip']:
        return dict(result, action='skip', reason=item['skip'])
    mapping = item['mapping']
    result.update(action=mapping['action'], name=mapping['target_name'])
    if mapping['action'] == 'match':
        result['department_id'] = mapping['department_id']
    return result


def execute(engine, parsed, *, organization_id, actor_id, apply=False, resume=False, year=2027):
    """Plan never invokes a write service, including rollback-only trial writes.

    2027 commits each department; 2026 uses per-department savepoints and one outer
    commit so a 2027 hash surprise rolls back the entire run. A session advisory
    lock serializes loaders; owners must pause application edits.
    """
    from sqlalchemy import text, select
    from sqlalchemy.orm import Session
    from app.models import (AuditLog, Department, ImportBatch, ReportingPeriod, Submission)
    from app.first_load_service import apply_first_load_batch
    from app.import_service import department_key

    totals = Counter({key: 0 for key in ('departments', 'created_departments', 'cards', 'indicators', 'activities', 'economic_values')})
    output = dict(mode='uygula' if apply else 'plan', counts=totals, departments=[], skipped=[], failed=[], validation=[])
    with engine.connect() as connection:
        locked = False
        try:
            if apply:
                locked = bool(connection.scalar(text('SELECT pg_try_advisory_lock(:key)'), {'key': LOCK}))
                connection.commit()
                if not locked:
                    raise Refusal('Başka ilk yükleme çalışıyor. Bu komut 0 satır yazdı; tamamlanmasını bekleyin.')
            with Session(connection, expire_on_commit=False) as db:
                db.execute(text('SET TRANSACTION READ ONLY'))
                with phase('veritabanı/şema denetimi'):
                    actor, period, completed = context(db, organization_id, actor_id, resume, year=year)
                with phase('müdürlük planı'):
                    items = department_plan(db, parsed, completed, year=year)
                output['departments'] = [department_action(item) for item in items]
                period_id = period.id if period else None
                db.rollback()
                total_items = len(items)
                if not apply:
                    for index, item in enumerate(items, 1):
                        started = time.monotonic()
                        source = item['source']
                        if item['skip']:
                            output['skipped'].append(dict(name=source['name'], reason=item['skip']))
                            action = 'atla'
                        else:
                            totals.update(planned_counts(source))
                            totals['created_departments'] += item['mapping']['action'] == 'create'
                            action = 'oluştur' if item['mapping']['action'] == 'create' else 'eşleştir'
                        print_progress(index, total_items, source['name'], action, time.monotonic() - started)
                    return output
                if year == 2026:
                    # Per-directorate savepoints, one outer commit: a surprise in
                    # the final directorate must undo every 2026 write in this run.
                    db.begin()
                    from app.first_load_service import period_rows_hash
                    with phase('2027 koruma özeti hesabı'):
                        output['protected_2027_before'] = period_rows_hash(db)
                for index, item in enumerate(items):
                    started = time.monotonic()
                    source = item['source']
                    if item['skip']:
                        output['skipped'].append(dict(name=source['name'], reason=item['skip']))
                        print_progress(index + 1, total_items, source['name'], 'atla', time.monotonic() - started)
                        continue
                    try:
                        with (db.begin_nested() if year == 2026 else db.begin()):
                            # Repeat guards after each commit; no migration is ever run.
                            actor, period, completed = context(db, organization_id, actor_id, True, year=year)
                            if not period:
                                period = ReportingPeriod(year=year, status='draft', template_status='verified')
                                db.add(period)
                                db.flush()
                            period_id = period.id
                            # Serialize PP writers that use the existing period lock.
                            db.scalar(select(ReportingPeriod).where(ReportingPeriod.id == period_id).with_for_update())
                            # Block concurrent row writers during this department import.
                            db.execute(text('LOCK TABLE departments, report_cards, indicators, activities, '
                                            'economic_values, department_cost_values, submissions '
                                            'IN SHARE ROW EXCLUSIVE MODE'))
                            # Preserve the initial exact/create decision. Otherwise
                            # a later new name can become a fuzzy suggestion for a
                            # department just created earlier in the same run.
                            created_department = 0
                            if item['mapping']['action'] == 'create':
                                exact = [d for d in db.scalars(select(Department))
                                         if department_key(d.name) == department_key(source['name'])]
                                if not exact:
                                    db.add(Department(organization_id=organization_id,
                                                      name=item['mapping']['target_name']))
                                    db.flush()
                                    created_department = 1
                            fresh = department_plan(db, department_payload(parsed, source), completed, year=year)[0]
                            if fresh['skip']:
                                raise Refusal('Müdürlük eşleşmesi/geçmişi değişti; yeniden plan alın.')
                            did = fresh['mapping'].get('department_id')
                            if did and did in content_departments(db, period_id):
                                raise Refusal('Müdürlükte mevcut veri var; kullanıcı düzeltmelerine dokunulmadı.')
                            sub = db.scalar(select(Submission).where(Submission.period_id == period_id,
                                                                    Submission.department_id == did)) if did else None
                            if sub and sub.status not in {'draft', 'returned'}:
                                raise Refusal('Müdürlük paketi taslak/iade durumunda değil; paket atlandı.')
                            batch = ImportBatch(period_id=period_id, filename=book_config(year)[0].name, status='preview',
                                payload_json=json.dumps(department_payload(parsed, source), ensure_ascii=False), created_by=actor.id)
                            db.add(batch)
                            db.flush()
                            applied, _, validations = apply_first_load_batch(db, batch, actor)
                            applied['created_departments'] += created_department
                            department = next(d for d in db.scalars(select(Department))
                                              if department_key(d.name) == department_key(source['name']))
                            submission = db.scalar(select(Submission).where(Submission.period_id == period_id,
                                                                            Submission.department_id == department.id))
                            submission.status = 'draft'
                            db.add(AuditLog(user_id=actor.id, action=MARKER, entity_type='import_batch', entity_id=batch.id,
                                details=json.dumps(dict(book_sha256=book_config(year)[1], year=year, department_id=department.id,
                                                        validation_errors=validations), ensure_ascii=False)))
                        totals.update({key: applied[key] for key in totals})
                        output['validation'].extend(validations)
                        print(f"{'Hazırlandı' if year == 2026 else 'Yüklendi'}: {source['name']} · taslak · {sum(len(v['errors']) for v in validations)} doğrulama hatası", flush=True)
                        print_progress(index + 1, total_items, source['name'],
                                       'hazırlandı' if year == 2026 else 'yüklendi',
                                       time.monotonic() - started)
                    except Exception as exc:
                        # Never expose SQL/driver messages, source payloads or a URL.
                        reason = str(exc) if isinstance(exc, ValueError) else (
                            'Mevcut içe aktarma/katalog hizmeti paketi kabul etmedi; müdürlük işlemi geri alındı '
                            f'({failure_detail(exc)}). Yerel provada sorumluya inceletin.')
                        # detail: class/SQLSTATE/schema names/code location only (D-396).
                        output['failed'].append(dict(name=source['name'], reason=reason,
                                                     detail=failure_detail(exc)))
                        output['departments'][index] = dict(source_name=source['name'], action='skip', reason=reason)
                        print_progress(index + 1, total_items, source['name'], 'başarısız', time.monotonic() - started)
                        if year == 2026:
                            db.rollback()
                            totals.clear()
                            totals.update({key: 0 for key in ('departments', 'created_departments', 'cards', 'indicators', 'activities', 'economic_values')})
                            with phase('2027 koruma özeti hesabı'):
                                output['protected_2027_after'] = period_rows_hash(db)
                            return output
                if year == 2026:
                    db.flush()
                    with phase('2027 koruma özeti hesabı'):
                        output['protected_2027_after'] = period_rows_hash(db)
                    if output['protected_2027_before'] != output['protected_2027_after']:
                        db.rollback()
                        raise Refusal('2027 satırları değişecekti; işlem geri alındı, 0 satır yazıldı.')
                    db.commit()
                return output
        finally:
            connection.rollback()
            if locked:
                connection.execute(text('SELECT pg_advisory_unlock(:key)'), {'key': LOCK})
                connection.commit()


def main(argv=None):
    parser = SafeParser(description=__doc__)
    parser.add_argument('--year', type=int, choices=(2026, 2027), default=2027)
    parser.add_argument('--book', type=Path)
    parser.add_argument('--organization-id', type=int, required=True)
    parser.add_argument('--actor-id', type=int, required=True)
    parser.add_argument('--apply', action='store_true', help='Sahibin yazma onayı; diğer korumalar da zorunlu')
    parser.add_argument('--backup', type=Path, help='Doğrulanmış, 60 dakikadan yeni .dump dosyası')
    parser.add_argument('--resume', action='store_true', help='Tamamlanmış müdürlükleri hiç değiştirmeden atla')
    parser.add_argument('--clear-preprint', action='store_true',
                        help='D-131 / D-135 ön baskı temizleme planı; yalnız --apply ile yazar')
    args = parser.parse_args(argv)
    args.book = args.book or book_config(args.year)[0]
    try:
        # The app.db module creates a default engine on import. It must only see
        # this inert URL, never application/migration environment credentials.
        cleared = {key: None for key in os.environ if key.startswith('PG')}
        with environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None, **cleared):
            url = target_url()
            if args.clear_preprint and args.resume:
                raise Refusal('--clear-preprint ile --resume birlikte kullanılamaz; 0 satır yazıldı.')
            if args.year == 2026 and args.clear_preprint:
                raise Refusal('--clear-preprint yalnız 2027 içindir; 0 satır yazıldı.')
            with phase('kitap doğrulama'):
                parsed = verify_book(args.book, **({'year': args.year} if args.year == 2026 else {}))
            if args.apply:
                with phase('yedek doğrulama'):
                    verify_backup(args.backup)
                try:
                    if args.clear_preprint:
                        from scripts.clear_preprint_2027 import CONFIRMATION
                        confirmation = read_confirmation(f'Temizleme onayı: {CONFIRMATION} yazın: ')
                    else:
                        confirmation = read_confirmation(f'Yazma onayı: kitap SHA256 ilk 12 karakterini yazın ({book_config(args.year)[1][:12]}): ')
                except (EOFError, KeyboardInterrupt):
                    raise Refusal('Yazma onayı alınamadı; 0 satır yazıldı.') from None
                expected = CONFIRMATION if args.clear_preprint else book_config(args.year)[1][:12]
                if confirmation != expected:
                    raise Refusal('Temizleme onayı uyuşmuyor; 0 satır yazıldı.' if args.clear_preprint else
                                  'Kitap SHA256 onayı uyuşmuyor; 0 satır yazıldı.')
                verify_backup(args.backup)  # A long pause at the prompt cannot bypass freshness.
            from sqlalchemy import create_engine
            from sqlalchemy.pool import NullPool
            engine = create_engine(url, poolclass=NullPool, hide_parameters=True,
                                   connect_args={'connect_timeout': 10, 'options': '-c search_path=public'})
            try:
                if args.clear_preprint:
                    from scripts.clear_preprint_2027 import execute as clear_execute
                    result = clear_execute(engine, organization_id=args.organization_id,
                                           actor_id=args.actor_id, apply=args.apply,
                                           before_write=(lambda: verify_backup(args.backup)) if args.apply else None)
                else:
                    result = execute(engine, parsed, organization_id=args.organization_id, actor_id=args.actor_id,
                                     apply=args.apply, resume=args.resume, year=args.year)
            finally:
                engine.dispose()
        print('PLAN: Hedefe 0 satır yazıldı.' if not args.apply else 'UYGULAMA SONUCU:')
        if args.clear_preprint:
            for department in result['departments']:
                c = department['counts']
                print(f"Temizle: {department['name']} (müdürlük #{department['department_id']}, "
                      f"paket #{department['batch_id']}) · {c['indicators']} gösterge, "
                      f"{c['indicator_values']} gösterge değeri, {c['activities']} faaliyet, "
                      f"{c['activity_cost_values']} faaliyet maliyeti, "
                      f"{c['department_cost_values']} personel/SGK maliyeti, {c['submissions']} taslak teslim")
            if result['already_cleared']:
                print('Ön baskı zaten temizlenmiş; 0 satır yazıldı.')
        elif not args.apply:
            for department in result['departments']:
                source = department['source_name']
                if department['action'] == 'match':
                    print(f"Eşleştir: {source} → {department['name']} (müdürlük #{department['department_id']})")
                elif department['action'] == 'create':
                    print(f"Oluştur: {source} → {department['name']}")
                else:
                    print(f"Atla: {source} · {department['reason']}")
        summary = format_summary(result, year=args.year, apply=args.apply, clear_preprint=args.clear_preprint)
        print(summary)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(summary, flush=True)
        return 2 if result.get('failed') else 0
    except Refusal as exc:
        print(f'DURDU: {exc}', file=sys.stderr)
    except KeyboardInterrupt:
        print('DURDU: İşlem kesildi; yeniden yazmadan önce ' +
              ('--clear-preprint' if args.clear_preprint else '--resume') + ' ile plan alın.', file=sys.stderr)
    except Exception as exc:
        print(f'DURDU: İşlem tamamlanamadı ({type(exc).__name__}); bağlantı/dosya ayrıntıları gizlendi. '
              'Günlüğü sorumluya iletin; yeniden uygulamadan önce ' +
              ('--clear-preprint' if args.clear_preprint else '--resume') + ' ile plan alın.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.modules['scripts.first_load_live'] = sys.modules[__name__]
    raise SystemExit(main())
