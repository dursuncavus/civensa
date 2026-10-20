#!/usr/bin/env python3
"""Basılı PP 2027: varsayılan salt okunur plan; korumalı, müdürlük bazlı ilk yükleme."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from urllib.parse import parse_qsl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.first_load_dryrun import environment, parse_book

# app.db creates its default engine at import time. Initialize it against an
# inert in-memory URL even for callers using the functions outside main().
with environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None):
    import app.db  # noqa: F401

BOOK = ROOT / 'tests/fixtures/first_load/source/2027-performans-programi_16102026_duzeltilmis 2.idml'
BOOK_SHA256 = '261cd17fd0be13dead1c573966bb3cc17b63664adc867b2e6fc4e156df28f36e'
HEAD = 'c048a1b2c3d4'
TARGET_ENV = 'CIVENSA_FIRST_LOAD_DATABASE_URL'
SKIPPED = 'İşletme ve İştirakler Müdürlüğü'
MARKER = 'first_load_department'
LOCK = 520027


class Refusal(ValueError):
    """Only controlled, secret-free messages may cross the CLI boundary."""


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default includes rejected argument values, possibly a URL.
        self.exit(2, 'DURDU: Komut seçenekleri geçersiz. --help çıktısını kullanın; bağlantıyı yalnız gizli ortam değişkeninde girin.\n')


def verify_book(path):
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != BOOK_SHA256:
        raise Refusal('Kitap SHA256 uyuşmuyor. Onaylı basılı IDML dosyasını kullanın; yükleme durdu.')
    # Parse exactly the verified bytes, even if the original file is replaced.
    with TemporaryDirectory(prefix='civensa_verified_book_') as directory:
        snapshot = Path(directory) / BOOK.name
        snapshot.write_bytes(data)
        parsed, _ = parse_book(snapshot)
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


def content_departments(db, period_id):
    from sqlalchemy import select
    from app.models import Activity, DepartmentCostValue, EconomicValue, Indicator, ReportCard
    ids = set()
    for model in (Activity, DepartmentCostValue, EconomicValue, Indicator, ReportCard):
        ids.update(db.scalars(select(model.department_id).where(model.period_id == period_id)))
    return ids


def completed_departments(db, period_id):
    from sqlalchemy import select
    from app.models import AuditLog, ImportBatch
    completed = set()
    for audit, batch in db.execute(select(AuditLog, ImportBatch).join(
            ImportBatch, ImportBatch.id == AuditLog.entity_id).where(
            AuditLog.action == MARKER, AuditLog.entity_type == 'import_batch',
            ImportBatch.period_id == period_id)):
        try:
            details = json.loads(audit.details)
            if (batch.status != 'applied' or details['book_sha256'] != BOOK_SHA256
                    or details['year'] != 2027):
                raise ValueError
            completed.add(int(details['department_id']))
        except (ValueError, KeyError, TypeError):
            raise Refusal('İlk yükleme geçmişi uyuşmuyor. Otomatik devam engellendi; sorumluya bildirin.') from None
    return completed


def context(db, organization_id, actor_id, resume):
    from sqlalchemy import select
    from app.models import Organization, User, ReportingPeriod, Program, OfficialActivity, ImportBatch
    require_head(db)
    orgs = db.scalars(select(Organization)).all()
    if len(orgs) != 1 or orgs[0].id != organization_id:
        raise Refusal('Tek kurum ve doğru --organization-id gerekli. Kurum numarasını sorumluya doğrulatın.')
    actor = db.get(User, actor_id)
    if not actor or not actor.is_active or actor.role not in {'strategy', 'admin'}:
        raise Refusal('--actor-id etkin Strateji/yönetici kullanıcısı olmalıdır. Kullanıcı numarasını doğrulatın.')
    period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == 2027))
    if period and (period.status not in {'draft', 'active'} or period.template_status != 'verified'):
        raise Refusal('2027 dönemi açık ve şablonu doğrulanmış olmalıdır. Dönem durumunu sorumluya bildirin.')
    completed = completed_departments(db, period.id) if period else set()
    if period:
        existing = content_departments(db, period.id)
        other = any(db.scalar(select(model.id).where(model.period_id == period.id).limit(1))
                    for model in (Program, OfficialActivity, ImportBatch))
        if (existing or other or completed) and not resume:
            raise Refusal('2027 PP verisi zaten var; 0 satır yazıldı. Yalnız belgelenmiş --resume ile devam edin.')
        if resume and ((existing - completed) or (other and not completed)):
            raise Refusal('2027 PP verisinde bu yüklemeye ait olmayan kayıt var; 0 satır yazıldı. Devam engellendi.')
    return actor, period, completed


def department_payload(parsed, source):
    # Structural parser errors remain blocking. Institution findings are never data.
    return dict(departments=[deepcopy(source)], summary=parsed['summary'],
                errors=parsed.get('errors', []),
                rejected_economic_tables=parsed.get('rejected_economic_tables', []))


def planned_counts(source):
    return dict(departments=1, cards=len(source['blocks']),
                indicators=sum(len(b['indicators']) for b in source['blocks']),
                activities=len(source['activities']),
                economic_values=len({tuple(v[k] for k in ('year', 'kind', 'category', 'program_group', 'funding_type'))
                                     for t in source.get('economic_tables', []) for v in t['values']}))


def department_plan(db, parsed, completed):
    from app.import_service import build_department_plan, department_key
    plan = build_department_plan(db, parsed)
    mapping = {department_key(m['source_name']): m for m in plan['mappings']}
    items = []
    for source in plan['parsed']['departments']:
        m = mapping[department_key(source['name'])]
        reason = None
        if department_key(source['name']) == department_key(SKIPPED):
            reason = 'Meclis verisi bekleniyor; D-88 gereği atlandı.'
        elif m.get('department_id') in completed:
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


def execute(engine, parsed, *, organization_id, actor_id, apply=False, resume=False):
    """Plan never invokes a write service, including rollback-only trial writes.

    Apply uses one committed transaction per department. A session advisory lock
    serializes loaders across those commits; owners must pause application edits.
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
                actor, period, completed = context(db, organization_id, actor_id, resume)
                items = department_plan(db, parsed, completed)
                output['departments'] = [department_action(item) for item in items]
                period_id = period.id if period else None
                db.rollback()
                if not apply:
                    for item in items:
                        if item['skip']:
                            output['skipped'].append(dict(name=item['source']['name'], reason=item['skip']))
                        else:
                            totals.update(planned_counts(item['source']))
                            totals['created_departments'] += item['mapping']['action'] == 'create'
                    return output
                for index, item in enumerate(items):
                    source = item['source']
                    if item['skip']:
                        output['skipped'].append(dict(name=source['name'], reason=item['skip']))
                        continue
                    try:
                        with db.begin():
                            # Repeat guards after each commit; no migration is ever run.
                            actor, period, completed = context(db, organization_id, actor_id, True)
                            if not period:
                                period = ReportingPeriod(year=2027, status='draft', template_status='verified')
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
                            fresh = department_plan(db, department_payload(parsed, source), completed)[0]
                            if fresh['skip']:
                                raise Refusal('Müdürlük eşleşmesi/geçmişi değişti; yeniden plan alın.')
                            did = fresh['mapping'].get('department_id')
                            if did and did in content_departments(db, period_id):
                                raise Refusal('Müdürlükte mevcut veri var; kullanıcı düzeltmelerine dokunulmadı.')
                            sub = db.scalar(select(Submission).where(Submission.period_id == period_id,
                                                                    Submission.department_id == did)) if did else None
                            if sub and sub.status not in {'draft', 'returned'}:
                                raise Refusal('Müdürlük paketi taslak/iade durumunda değil; paket atlandı.')
                            batch = ImportBatch(period_id=period_id, filename=BOOK.name, status='preview',
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
                                details=json.dumps(dict(book_sha256=BOOK_SHA256, year=2027, department_id=department.id,
                                                        validation_errors=validations), ensure_ascii=False)))
                        totals.update({key: applied[key] for key in totals})
                        output['validation'].extend(validations)
                        print(f"Yüklendi: {source['name']} · taslak · {sum(len(v['errors']) for v in validations)} doğrulama hatası", flush=True)
                    except Exception as exc:
                        # Never expose SQL/driver messages, source payloads or a URL.
                        reason = str(exc) if isinstance(exc, ValueError) else (
                            'Mevcut içe aktarma/katalog hizmeti paketi kabul etmedi; müdürlük işlemi geri alındı '
                            f'({type(exc).__name__}). Yerel provada sorumluya inceletin.')
                        output['failed'].append(dict(name=source['name'], reason=reason))
                        output['departments'][index] = dict(source_name=source['name'], action='skip', reason=reason)
                return output
        finally:
            connection.rollback()
            if locked:
                connection.execute(text('SELECT pg_advisory_unlock(:key)'), {'key': LOCK})
                connection.commit()


def main(argv=None):
    parser = SafeParser(description=__doc__)
    parser.add_argument('--book', type=Path, default=BOOK)
    parser.add_argument('--organization-id', type=int, required=True)
    parser.add_argument('--actor-id', type=int, required=True)
    parser.add_argument('--apply', action='store_true', help='Sahibin yazma onayı; diğer korumalar da zorunlu')
    parser.add_argument('--backup', type=Path, help='Doğrulanmış, 60 dakikadan yeni .dump dosyası')
    parser.add_argument('--resume', action='store_true', help='Tamamlanmış müdürlükleri hiç değiştirmeden atla')
    args = parser.parse_args(argv)
    try:
        # The app.db module creates a default engine on import. It must only see
        # this inert URL, never application/migration environment credentials.
        cleared = {key: None for key in os.environ if key.startswith('PG')}
        with environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None, **cleared):
            url = target_url()
            parsed = verify_book(args.book)
            if args.apply:
                verify_backup(args.backup)
                try:
                    confirmation = input(f'Yazma onayı: kitap SHA256 ilk 12 karakterini yazın ({BOOK_SHA256[:12]}): ')
                except (EOFError, KeyboardInterrupt):
                    raise Refusal('Yazma onayı alınamadı; 0 satır yazıldı.') from None
                if confirmation != BOOK_SHA256[:12]:
                    raise Refusal('Kitap SHA256 onayı uyuşmuyor; 0 satır yazıldı.')
                verify_backup(args.backup)  # A long pause at the prompt cannot bypass freshness.
            from sqlalchemy import create_engine
            from sqlalchemy.pool import NullPool
            engine = create_engine(url, poolclass=NullPool, hide_parameters=True,
                                   connect_args={'connect_timeout': 10, 'options': '-c search_path=public'})
            try:
                result = execute(engine, parsed, organization_id=args.organization_id, actor_id=args.actor_id,
                                 apply=args.apply, resume=args.resume)
            finally:
                engine.dispose()
        print('PLAN: Hedefe 0 satır yazıldı.' if not args.apply else 'UYGULAMA SONUCU:')
        if not args.apply:
            for department in result['departments']:
                source = department['source_name']
                if department['action'] == 'match':
                    print(f"Eşleştir: {source} → {department['name']} (müdürlük #{department['department_id']})")
                elif department['action'] == 'create':
                    print(f"Oluştur: {source} → {department['name']}")
                else:
                    print(f"Atla: {source} · {department['reason']}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result['failed'] else 0
    except Refusal as exc:
        print(f'DURDU: {exc}', file=sys.stderr)
    except KeyboardInterrupt:
        print('DURDU: İşlem kesildi; tamamlanmış müdürlükler korunur. Yeniden yazmadan önce --resume ile plan alın.', file=sys.stderr)
    except Exception as exc:
        print(f'DURDU: İşlem tamamlanamadı ({type(exc).__name__}); bağlantı/dosya ayrıntıları gizlendi. '
              'Günlüğü sorumluya iletin; yeniden uygulamadan önce --resume ile plan alın.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
