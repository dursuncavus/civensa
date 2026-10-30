#!/usr/bin/env python3
"""CIV-058 sahibin yerel provası: doğrulanmış yedek → yeni boş geçici PostgreSQL 18."""
from contextlib import contextmanager, redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.first_load_dryrun import environment, local_test_url
from scripts import first_load_live as live
from scripts import clear_preprint_2027 as clear
from ops.backup_crypto import decrypt_backup
from ops.release_rehearsal import database_state, require_fresh_backup, RehearsalFailure

EXPECTED = dict(departments=34, cards=64, indicators=263, activities=291, economic_values=1340)


def private(command, env):
    result = subprocess.run(command, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode:
        raise live.Refusal('Yerel PostgreSQL yedek/geri yükleme komutu başarısız; ayrıntılar gizlendi.')


def pg_environment(url):
    # Credentials go only in the child environment, never argv or output.
    env = {k: v for k, v in os.environ.items() if not k.startswith('PG')
           and k not in {'DATABASE_URL', 'MIGRATION_DATABASE_URL', live.TARGET_ENV}}
    env['PGDATABASE'] = url.database
    env['PGHOST'] = url.host
    env['PGPORT'] = str(url.port or 5432)
    if url.username is not None:
        env['PGUSER'] = url.username
    if url.password is not None:
        env['PGPASSWORD'] = url.password
    env['PGHOSTADDR'] = '::1' if url.host == '::1' else '127.0.0.1'
    env['PGCONNECT_TIMEOUT'] = '10'
    return env


@contextmanager
def empty_database(url):
    """Unlike the parser dry run, NEVER migrate before restoring the source dump."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool
    connect = dict(hostaddr='::1' if url.host == '::1' else '127.0.0.1', connect_timeout=10)
    admin = create_engine(url, isolation_level='AUTOCOMMIT', poolclass=NullPool,
                          connect_args=connect, hide_parameters=True)
    name = 'civensa_civ058_' + uuid4().hex
    created, engine = False, None
    try:
        with admin.connect() as conn:
            if int(conn.exec_driver_sql('SHOW server_version_num').scalar()) // 10000 != 18:
                raise live.Refusal('Prova yalnız yerel PostgreSQL 18 üzerinde çalışır.')
            conn.exec_driver_sql(f'CREATE DATABASE "{name}"')
            created = True
        engine = create_engine(url.set(database=name), poolclass=NullPool,
                               connect_args=connect, hide_parameters=True)
        yield engine
    finally:
        if engine:
            engine.dispose()
        try:
            if created:
                with admin.connect() as conn:
                    conn.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        finally:
            admin.dispose()


def snapshot(engine):
    """Rows and sequences for zero-write proof; only hashes/counts leave this function."""
    from psycopg import sql
    with engine.connect() as conn:
        conn.exec_driver_sql('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        tables = list(conn.exec_driver_sql(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").scalars())
        hashes = {}
        for table in tables:
            query = sql.SQL('SELECT * FROM public.{}').format(sql.Identifier(table)).as_string()
            rows = sorted(repr(row) for row in conn.exec_driver_sql(query))
            hashes[table] = hashlib.sha256(repr(rows).encode()).hexdigest()
        seqs = list(conn.exec_driver_sql(
            "SELECT sequencename, last_value FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename"))
    return hashes, seqs


def retained_rows(engine):
    """Hashes only: prove clear preserved every non-target row, audit and batch."""
    from sqlalchemy import select, text
    from sqlalchemy.orm import Session
    from app.db import Base
    from app.models import ReportingPeriod, Indicator, Activity, SubProgram, AuditLog, ImportBatch
    with Session(engine) as db:
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY'))
        pid = db.scalar(select(ReportingPeriod.id).where(ReportingPeriod.year == 2027))
        rows = {}
        for table in Base.metadata.sorted_tables:
            if table.name in {'audit_log', 'import_batches'}:
                continue
            query = select(table)
            if table.name in clear.FIELDS:
                if 'period_id' in table.c:
                    query = query.where(table.c.period_id != pid)
                else:
                    parent, column = {'indicator_values': (Indicator, 'indicator_id'),
                        'activity_cost_values': (Activity, 'activity_id'),
                        'activity_catalogue_links': (Activity, 'activity_id'),
                        'subprogram_scopes': (SubProgram, 'subprogram_id')}[table.name]
                    query = query.where(table.c[column].not_in(select(parent.id).where(parent.period_id == pid)))
            rows[table.name] = clear.digest(sorted(
                [dict(row) for row in db.execute(query).mappings()], key=clear.encoded))
        audit = {a.id: clear.digest({c.name: getattr(a, c.name) for c in a.__table__.columns})
                 for a in db.scalars(select(AuditLog))}
        batches = {b.id: clear.digest(dict(clear.batch_state(b),
            status='preprint' if b.period_id == pid and b.id in clear.BATCH_STATES else b.status))
            for b in db.scalars(select(ImportBatch))}
        return dict(rows=rows, audit=audit, batches=batches)


def source_backup(path):
    # A production ARTIFACT may be older than 60 minutes. CIV-050's 48-hour
    # freshness applies to the source; applies require a NEW verified clone dump.
    saved = json.loads(path.with_suffix('.manifest.json').read_text())
    try:
        require_fresh_backup(saved.get('utc_timestamp'))
    except RehearsalFailure:
        raise live.Refusal('Kaynak üretim yedeği 48 saatten yeni olmalıdır. Mevcut yeşil yedek artifact tarihini sorumluya kontrol ettirin.') from None
    stamp = datetime.fromisoformat(saved['utc_timestamp'].replace('Z', '+00:00'))
    live.verify_backup(path, now=stamp)  # Integrity/head only; source age checked above.
    return saved


def restore(engine, dump):
    private(['pg_restore', '--dbname', engine.url.database, '--exit-on-error', '--single-transaction', '--no-owner',
             '--no-privileges', str(dump)], pg_environment(engine.url))


def state(engine):
    raw = engine.url.set(drivername='postgresql', query={}).render_as_string(hide_password=False)
    return database_state(raw)


def fresh_clone_backup(engine, directory, admin_url):
    stamp = datetime.now(timezone.utc).isoformat()
    dump = directory / (uuid4().hex + '.dump')
    before = state(engine)
    before_rows = snapshot(engine)
    private(['pg_dump', '--format=custom', '--file', str(dump)], pg_environment(engine.url))
    saved = dict(before, utc_timestamp=stamp, file_name=dump.name,
                 file_size_bytes=dump.stat().st_size,
                 sha256=hashlib.sha256(dump.read_bytes()).hexdigest())
    dump.with_suffix('.manifest.json').write_text(json.dumps(saved))
    # Match CIV-050: restore and compare every public table + Alembic version.
    # Also prove the clone backup reproduces every row and sequence.
    with empty_database(admin_url) as verifier:
        restore(verifier, dump)
        if state(verifier) != before or snapshot(verifier) != before_rows:
            raise live.Refusal('Yerel yedek geri yükleme sayım/satır/sıra doğrulaması uyuşmuyor.')
    live.verify_backup(dump)
    return dump


def rehearse(backup, organization_id, actor_id, record):
    ids = dict(organization_id=organization_id, actor_id=actor_id)
    cleared = {key: None for key in os.environ if key.startswith('PG')}
    with environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None,
                     CIVENSA_FIRST_LOAD_DATABASE_URL=None, **cleared):
        admin_url = local_test_url()  # Strict loopback/no query; no live URL accepted.
        for tool in ('pg_dump', 'pg_restore'):
            version = subprocess.run([tool, '--version'], capture_output=True, text=True)
            if version.returncode or ' 18.' not in version.stdout:
                raise live.Refusal('pg_dump ve pg_restore 18 araçlarını PATH içinde seçin.')
        saved = source_backup(backup)
        record['source_sha256'] = saved['sha256']
        record['source_utc_timestamp'] = saved['utc_timestamp']
        parsed = live.verify_book(live.BOOK)
        with TemporaryDirectory(prefix='civ058_private_') as directory, empty_database(admin_url) as engine:
            restore(engine, backup)
            if state(engine) != {k: saved[k] for k in ('public_table_row_counts', 'alembic_version')}:
                raise live.Refusal('Üretim yedeği restore sayımları/şeması manifest ile uyuşmuyor.')
            record['restored_table_counts'] = state(engine)['public_table_row_counts']
            before = snapshot(engine)
            retained_before = retained_rows(engine)
            try:
                plan = clear.execute(engine, **ids)
            except live.Refusal:
                unchanged = snapshot(engine) == before
                record['steps'].append(dict(step='clear-plan', status='REFUSED',
                    rows_and_sequences_unchanged=unchanged, writes=0 if unchanged else 'UNKNOWN'))
                if not unchanged:
                    raise live.Refusal('Reddedilen temizleme planı satır/sıra durumunu değiştirdi.') from None
                raise
            if snapshot(engine) != before:
                raise live.Refusal('Temizleme planı satır/sıra değiştirdi.')
            record['steps'].append(dict(step='clear-plan', counts=plan['counts'], writes=0,
                rows_and_sequences_unchanged=True,
                departments=[{k: d[k] for k in ('department_id', 'batch_id', 'counts')} for d in plan['departments']]))
            if plan['counts']['department_cost_values'] != 93:
                raise live.Refusal('D-135 provası tam 93 personel/SGK maliyet satırı planlamalıdır; 0 satır yazıldı.')
            print('Temizleme planı: ' + json.dumps(plan['counts'], ensure_ascii=False))
            if input(f'Yalnız geçici yerel kopya için {clear.CONFIRMATION} yazın: ') != clear.CONFIRMATION:
                raise live.Refusal('Yerel temizleme onayı uyuşmuyor.')
            dump = fresh_clone_backup(engine, Path(directory), admin_url)
            live.verify_backup(dump)
            applied = clear.execute(engine, apply=True, before_write=lambda: live.verify_backup(dump), **ids)
            if applied['counts'] != plan['counts'] or applied['already_cleared']:
                raise live.Refusal('Temizleme uygulama sayımı plan ile uyuşmuyor.')
            retained_after = retained_rows(engine)
            if (retained_before['rows'] != retained_after['rows']
                    or retained_before['batches'] != retained_after['batches']
                    or len(retained_after['audit']) != len(retained_before['audit']) + 1
                    or any(retained_after['audit'].get(k) != v for k, v in retained_before['audit'].items())):
                raise live.Refusal('Temizleme korunacak satır/paket/denetim parmak izini değiştirdi.')
            record['steps'].append(dict(step='clear-apply', counts=applied['counts'],
                retained_rows_unchanged=True, existing_audit_unchanged=True,
                batches_preserved=True, table_counts=state(engine)['public_table_row_counts']))
            again_before = snapshot(engine)
            again = clear.execute(engine, apply=True, **ids)
            if not again['already_cleared'] or snapshot(engine) != again_before:
                raise live.Refusal('İkinci temizleme sıfır yazma kontrolü başarısız.')
            record['steps'].append(dict(step='clear-apply-again', counts=again['counts'], writes=0))
            before = snapshot(engine)
            plan = live.execute(engine, parsed, **ids)
            if snapshot(engine) != before or any(plan['counts'][k] != v for k, v in EXPECTED.items()):
                raise live.Refusal('Basılı ilk yükleme planı 34/64/263/291/1340 veya sıfır yazma ile uyuşmuyor.')
            skipped = [d['name'] for d in plan['skipped']]
            if skipped:
                raise live.Refusal('Onaylı kitap planında hiçbir müdürlük atlanmamalıdır.')
            record['steps'].append(dict(step='first-load-plan', counts=dict(plan['counts']), writes=0,
                created_source_names=[d['source_name'] for d in plan['departments'] if d['action'] == 'create'],
                skipped_source_names=skipped))
            print('İlk yükleme planı: ' + json.dumps(dict(plan['counts']), ensure_ascii=False))
            if input(f'Yalnız geçici yerel yükleme için {live.BOOK_SHA256[:12]} yazın: ') != live.BOOK_SHA256[:12]:
                raise live.Refusal('Yerel kitap SHA256 onayı uyuşmuyor.')
            dump = fresh_clone_backup(engine, Path(directory), admin_url)
            live.verify_backup(dump)
            with redirect_stdout(io.StringIO()):
                loaded = live.execute(engine, parsed, apply=True, **ids)
            if loaded['failed'] or loaded['counts'] != plan['counts']:
                raise live.Refusal('Yerel ilk yükleme uygulaması plan sayımlarını tamamlayamadı.')
            record['steps'].append(dict(step='first-load-apply', counts=dict(loaded['counts']),
                validation_departments=len(loaded['validation']),
                validation_errors=sum(len(v['errors']) for v in loaded['validation'])))
            before = snapshot(engine)
            plan = live.execute(engine, parsed, resume=True, **ids)
            if snapshot(engine) != before or any(plan['counts'].values()):
                raise live.Refusal('Son --resume planı sıfır yazma kontrolü başarısız.')
            record['steps'].append(dict(step='first-load-plan-again', counts=dict(plan['counts']), writes=0))
            record['final_table_counts'] = state(engine)['public_table_row_counts']


def main(argv=None):
    parser = live.SafeParser(description=__doc__)
    parser.add_argument('--backup', type=Path, required=True)
    parser.add_argument('--organization-id', type=int, required=True)
    parser.add_argument('--actor-id', type=int, required=True)
    parser.add_argument('--out', type=Path, default=Path('civ058-rehearsal-counts.json'))
    args = parser.parse_args(argv)
    try:
        protected = {args.backup.resolve(), args.backup.with_suffix('.manifest.json').resolve()}
        if args.backup.name.endswith('.dump.age'):
            protected.add(args.backup.with_name(
                args.backup.name.removesuffix('.dump.age') + '.manifest.json.age').resolve())
        if args.out.resolve() in protected:
            print('DURDU: Sayım raporu yedek/manifest dosyasının üzerine yazılamaz.', file=sys.stderr)
            return 1
    except Exception:
        print('DURDU: Rapor/yedek dosya yolu doğrulanamadı; ayrıntılar gizlendi.', file=sys.stderr)
        return 1
    record = dict(status='FAIL', steps=[])
    # No source contents, source URL, database password or row values in output.
    previous_mask = os.umask(0o077)
    try:
        if args.backup.name.endswith('.dump.age'):
            with TemporaryDirectory(prefix='civ092-restore-') as directory:
                dump = decrypt_backup(args.backup.parent, Path(directory) / 'decrypted')
                rehearse(dump, args.organization_id, args.actor_id, record)
        else:
            # Disposable clone dumps remain local and never enter an artifact.
            rehearse(args.backup, args.organization_id, args.actor_id, record)
        record['status'] = 'PASS'
    except KeyboardInterrupt:
        print('DURDU: Yerel prova kesildi; geçici kopyalar kaldırıldı.', file=sys.stderr)
    except live.Refusal as exc:
        print('DURDU: ' + str(exc), file=sys.stderr)
    except Exception:
        print('DURDU: Yerel prova tamamlanamadı; dosya/bağlantı ayrıntıları gizlendi. Sorumluya bildirin.',
              file=sys.stderr)
    finally:
        try:
            args.out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        except Exception:
            record['status'] = 'FAIL'
            print('DURDU: Sayım raporu yazılamadı; çıktı klasörünü sorumluya kontrol ettirin. Dosya ayrıntıları gizlendi.',
                  file=sys.stderr)
        finally:
            os.umask(previous_mask)
    print('CIV-058 yerel prova: ' + record['status'])
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
