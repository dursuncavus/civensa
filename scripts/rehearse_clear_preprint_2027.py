#!/usr/bin/env python3
"""Owner-run CIV-058 rehearsal: verified backup -> empty disposable PostgreSQL 18."""
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
from ops.release_rehearsal import database_state, require_fresh_backup, RehearsalFailure

EXPECTED = dict(departments=33, cards=61, indicators=256, activities=285, economic_values=1300)


def private(command, env):
    result = subprocess.run(command, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode:
        raise live.Refusal('Yerel PostgreSQL yedek/geri yükleme komutu başarısız; ayrıntılar gizlendi.')


def pg_environment(url):
    # Credentials go only in the child environment, never argv or output.
    env = {k: v for k, v in os.environ.items() if not k.startswith('PG')
           and k not in {'DATABASE_URL', 'MIGRATION_DATABASE_URL', live.TARGET_ENV}}
    env['PGDATABASE'] = url.set(drivername='postgresql', query={}).render_as_string(hide_password=False)
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
    private(['pg_restore', '--exit-on-error', '--single-transaction', '--no-owner',
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
            plan = clear.execute(engine, **ids)
            if snapshot(engine) != before:
                raise live.Refusal('Temizleme planı satır/sıra değiştirdi.')
            record['steps'].append(dict(step='clear-plan', counts=plan['counts'], writes=0))
            print('Temizleme planı: ' + json.dumps(plan['counts'], ensure_ascii=False))
            if input(f'Yalnız geçici yerel kopya için {clear.CONFIRMATION} yazın: ') != clear.CONFIRMATION:
                raise live.Refusal('Yerel temizleme onayı uyuşmuyor.')
            dump = fresh_clone_backup(engine, Path(directory), admin_url)
            live.verify_backup(dump)
            applied = clear.execute(engine, apply=True, before_write=lambda: live.verify_backup(dump), **ids)
            if applied['counts'] != plan['counts'] or applied['already_cleared']:
                raise live.Refusal('Temizleme uygulama sayımı plan ile uyuşmuyor.')
            record['steps'].append(dict(step='clear-apply', counts=applied['counts']))
            again_before = snapshot(engine)
            again = clear.execute(engine, apply=True, **ids)
            if not again['already_cleared'] or snapshot(engine) != again_before:
                raise live.Refusal('İkinci temizleme sıfır yazma kontrolü başarısız.')
            record['steps'].append(dict(step='clear-apply-again', counts=again['counts'], writes=0))
            before = snapshot(engine)
            plan = live.execute(engine, parsed, **ids)
            if snapshot(engine) != before or any(plan['counts'][k] != v for k, v in EXPECTED.items()):
                raise live.Refusal('Basılı ilk yükleme planı 33/61/256/285/1300 veya sıfır yazma ile uyuşmuyor.')
            record['steps'].append(dict(step='first-load-plan', counts=dict(plan['counts']), writes=0))
            print('İlk yükleme planı: ' + json.dumps(dict(plan['counts']), ensure_ascii=False))
            if input(f'Yalnız geçici yerel yükleme için {live.BOOK_SHA256[:12]} yazın: ') != live.BOOK_SHA256[:12]:
                raise live.Refusal('Yerel kitap SHA256 onayı uyuşmuyor.')
            dump = fresh_clone_backup(engine, Path(directory), admin_url)
            live.verify_backup(dump)
            with redirect_stdout(io.StringIO()):
                loaded = live.execute(engine, parsed, apply=True, **ids)
            if loaded['failed'] or loaded['counts'] != plan['counts']:
                raise live.Refusal('Yerel ilk yükleme uygulaması plan sayımlarını tamamlayamadı.')
            record['steps'].append(dict(step='first-load-apply', counts=dict(loaded['counts'])))
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
    if args.out.resolve() in {args.backup.resolve(), args.backup.with_suffix('.manifest.json').resolve()}:
        print('DURDU: Sayım raporu yedek/manifest dosyasının üzerine yazılamaz.', file=sys.stderr)
        return 1
    record = dict(status='FAIL', steps=[])
    # No source contents, source URL, database password or row values in output.
    previous_mask = os.umask(0o077)
    try:
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
        finally:
            os.umask(previous_mask)
    print('CIV-058 yerel prova: ' + record['status'])
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
