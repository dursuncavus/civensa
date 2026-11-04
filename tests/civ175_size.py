"""Measure the CIV-174 books without changing the publication format.

Run from the repository root: python -m tests.civ175_size
Only CIVENSA_TEST_POSTGRES_URL is accepted, via the local-only disposable DB
helper. The approved-book HTTP endpoint runs only against that disposable DB.
Compression/deletion candidates exist in memory for measurement only.
"""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import gc
import bz2
import lzma
import sys
import gzip
import hashlib
import json
from pathlib import Path
import platform
import re
import time
import tracemalloc
from unittest.mock import patch
import zlib
import base64

from scripts.first_load_dryrun import (
    disposable_database, environment, inspect_import, local_test_url,
)


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':')).encode('utf-8')


def members(value):
    """Exclusive UTF-8 object member sizes; punctuation is accounted separately."""
    entries = {key: dict(value_bytes=len(encode(item)),
                        member_bytes=len(encode(key)) + 1 + len(encode(item)))
               for key, item in value.items()}
    punctuation = 2 + max(0, len(value) - 1)
    assert sum(item['member_bytes'] for item in entries.values()) + punctuation == len(encode(value))
    return dict(total_bytes=len(encode(value)), members=entries,
                punctuation_bytes=punctuation)


def collection_fields(rows):
    totals = defaultdict(lambda: dict(value_bytes=0, member_bytes=0))
    punctuation = 2 + max(0, len(rows) - 1)  # list brackets and separators
    for row in rows:
        measured = members(row)
        punctuation += measured['punctuation_bytes']
        for key, sizes in measured['members'].items():
            for kind, size in sizes.items():
                totals[key][kind] += size
    assert sum(item['member_bytes'] for item in totals.values()) + punctuation == len(encode(rows))
    return dict(total_bytes=len(encode(rows)), row_count=len(rows),
                fields=dict(sorted(totals.items(), key=lambda item: -item[1]['member_bytes'])),
                punctuation_bytes=punctuation)


def snapshot_measurements(payload):
    departments = payload['departments']
    reconciliation = payload['cost_reconciliation']
    errors = [message for row in reconciliation for message in row['errors']]
    warnings = [message for row in reconciliation for message in row['warnings']]
    row_sizes = [(len(encode(row)), index) for index, row in enumerate(reconciliation)]
    return dict(
        top_level=members(payload),
        departments=collection_fields(departments),
        economic_fields=collection_fields([v for d in departments for v in d['economics']]),
        department_counts={key: sum(len(d[key]) for d in departments)
                           for key in ('cards', 'indicators', 'activities', 'department_costs', 'economics')},
        populated_departments=sum(bool(d['cards'] or d['indicators'] or d['activities']) for d in departments),
        largest_departments=[dict(department=d['department'], bytes=len(encode(d)))
                             for d in sorted(departments, key=lambda d: -len(encode(d)))[:5]],
        cost_reconciliation=dict(
            **collection_fields(reconciliation),
            levels=dict(Counter(row['level'] for row in reconciliation)),
            errors=len(errors), unique_errors=len(set(errors)),
            warnings=len(warnings), unique_warnings=len(set(warnings)),
            activity_id_references=sum(len(row['activity_ids']) for row in reconciliation),
            largest_rows=[dict(index=index, bytes=size, level=reconciliation[index]['level'],
                               path=reconciliation[index]['path'],
                               errors=len(reconciliation[index]['errors']))
                          for size, index in sorted(row_sizes, reverse=True)[:5]],
        ),
    )


def load_memory(raw):
    # raw is an existing Python str, as returned by the Text column. Do not
    # include fixture construction, UTF-8 encoding or profiling of SQLAlchemy.
    gc.collect()
    tracemalloc.start()
    started = time.perf_counter()
    loaded = json.loads(raw)
    elapsed = time.perf_counter() - started
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del loaded
    return dict(input_str_bytes=sys.getsizeof(raw), retained_bytes=current, peak_bytes=peak, seconds=elapsed)


def candidates(raw, payload):
    """Counterfactual sizes only; never persisted or sent to an app reader."""
    original = raw.encode('utf-8')
    codecs = {}
    for name, compress, decompress in (
        ('gzip', lambda value: gzip.compress(value, compresslevel=9, mtime=0), gzip.decompress),
        ('bzip2', lambda value: bz2.compress(value, compresslevel=9), bz2.decompress),
        ('xz', lambda value: lzma.compress(value, preset=3),
         lambda value: lzma.decompress(value, memlimit=32 * 1024 * 1024)),
    ):
        gc.collect()
        tracemalloc.start()
        started = time.perf_counter()
        compressed = compress(original)
        compression_seconds = time.perf_counter() - started
        _, compression_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        tracemalloc.start()
        started = time.perf_counter()
        restored = decompress(compressed)
        decompression_seconds = time.perf_counter() - started
        _, decompression_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert restored == original
        envelope = dict(snapshot_storage_version='1.0', codec=name + '+base64',
                        uncompressed_bytes=len(original),
                        payload_sha256=hashlib.sha256(original).hexdigest(),
                        data=base64.b64encode(compressed).decode('ascii'))
        assert base64.b64decode(envelope['data']) == compressed
        codecs[name] = dict(compressed_bytes=len(compressed), envelope_bytes=len(encode(envelope)),
                            saved_bytes=len(original)-len(encode(envelope)),
                            compression_seconds=compression_seconds, decompression_seconds=decompression_seconds,
                            compression_peak_bytes=compression_peak, decompression_peak_bytes=decompression_peak,
                            lossless_roundtrip=True)
        del restored, compressed, envelope
    without_reconciliation = {k: v for k, v in payload.items() if k != 'cost_reconciliation'}
    without_messages = dict(payload, cost_reconciliation=[
        {k: v for k, v in row.items() if k not in {'errors', 'warnings'}}
        for row in payload['cost_reconciliation']])
    # String interning is lossless and can keep JSON's expanded view unchanged.
    # This measures a diagnostic-only pool, including its field names/indices.
    pool = []
    indices = {}
    compact_rows = []
    for row in payload['cost_reconciliation']:
        compact = dict(row)
        for key in ('errors', 'warnings'):
            references = []
            for message in row[key]:
                if message not in indices:
                    indices[message] = len(pool)
                    pool.append(message)
                references.append(indices[message])
            compact[key] = references
        compact_rows.append(compact)
    pooled = dict(payload, cost_reconciliation=dict(messages=pool, rows=compact_rows))
    expanded = [dict(row, **{key: [pool[i] for i in row[key]] for key in ('errors', 'warnings')})
                for row in compact_rows]
    assert expanded == payload['cost_reconciliation']
    sizes = dict(drop_cost_reconciliation=len(encode(without_reconciliation)),
                 drop_errors_warnings=len(encode(without_messages)),
                 pool_errors_warnings=len(encode(pooled)))
    return dict(codecs=codecs,
                sizes={key: dict(bytes=size, saved_bytes=len(original)-size,
                                 under_2000000=size < 2_000_000)
                       for key, size in sizes.items()},
                lossless_pool_roundtrip=True)


def measure(engine, year):
    from fastapi.testclient import TestClient
    from sqlalchemy import select, func
    from sqlalchemy.orm import Session
    from app.db import get_db
    from app.main import app
    from app.models import Activity, Program, Publication, ReportCard, ReportingPeriod, SubProgram, User
    from app.program_service import book_snapshot, publication_checks
    from app import activity_contract_service as contract

    result = {}
    with Session(engine) as db:
        period = db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == year))
        pid = period.id
        result['publications_before'] = db.scalar(select(func.count()).select_from(Publication).where(Publication.period_id == pid))
        assert result['publications_before'] == 0
        started = time.perf_counter()
        payload = book_snapshot(db, pid)
        result['book_snapshot_seconds'] = time.perf_counter() - started
        result['book_snapshot'] = snapshot_measurements(payload)
        del payload
        program_ids = set(db.scalars(select(Program.id).where(Program.period_id == pid)))
        subprogram_ids = set(db.scalars(select(SubProgram.id).where(SubProgram.period_id == pid, SubProgram.program_id.in_(program_ids))))
        card_subprograms = {c.id: (c.subprogram_id, c.department_id) for c in db.scalars(select(ReportCard).where(ReportCard.period_id == pid))}
        activities = list(db.scalars(select(Activity).where(Activity.period_id == pid)))
        result['attribution'] = dict(programs=len(program_ids), subprograms=len(subprogram_ids),
            activities_without_trustworthy_parent=sum(
                a.subprogram_id not in subprogram_ids and not (
                    a.card_id in card_subprograms and card_subprograms[a.card_id][1] == a.department_id
                    and card_subprograms[a.card_id][0] in subprogram_ids) for a in activities))
    with Session(engine) as db:
        started = time.perf_counter()
        checks = publication_checks(db, pid)
        result['publication_checks_seconds'] = time.perf_counter() - started
        result['checks'] = dict(count=len(checks), errors=sum(len(c['errors']) for c in checks),
                               warnings=sum(len(c.get('warnings', [])) for c in checks))
        del checks
    with Session(engine, expire_on_commit=False) as db:
        strategy = db.scalar(select(User).where(User.role == 'strategy'))
        original_freeze = contract.freeze_program_payload

        def timed_freeze(*args, **kwargs):
            started = time.perf_counter()
            frozen, definitions = original_freeze(*args, **kwargs)
            result['freeze_program_payload_seconds'] = time.perf_counter() - started
            result['frozen_payload_bytes'] = len(encode(frozen))
            return frozen, definitions

        previous_overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = lambda: db
        try:
            # No TestClient lifespan: app startup must not create/seed another DB.
            with patch.object(contract, 'freeze_program_payload', timed_freeze):
                client = TestClient(app, follow_redirects=False)
                try:
                    response = client.post('/login', data=dict(email=strategy.email, password='Civ174-local-test-only!'))
                    assert response.status_code == 303
                    token = re.search(r'name="csrf_token" value="([^"]+)"', client.get('/modules').text).group(1)
                    response = client.post('/report-builder/publish-approved-book', data=dict(
                        csrf_token=token, period_id=pid, approval_reference='Meclis kararı, 16.10.2025'))
                    assert response.status_code == 303, 'Disposable approved-book publication failed'
                finally:
                    client.close()
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
        pub = db.scalar(select(Publication).where(Publication.period_id == pid))
        raw = pub.snapshot_json
        assert hashlib.sha256(raw.encode()).hexdigest() == pub.sha256
        assert encode(json.loads(raw)) == raw.encode(), 'Publication must use the measured serialization'
        result['json_loads'] = load_memory(raw)
        payload = json.loads(raw)
        result['publication_snapshot'] = members(payload)
        result['candidates'] = candidates(raw, payload)
        assert result['candidates']['codecs']['xz']['envelope_bytes'] < 2_000_000
        assert result['candidates']['codecs']['bzip2']['envelope_bytes'] < 2_000_000
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('docs/reports/civ-175/measurements.json'))
    parser.add_argument('--verify', type=Path, help='Compare structural byte counts/counts against a saved run; codec sizes allow 1%% metadata variance')
    args = parser.parse_args()
    expected = json.loads(args.verify.read_text(encoding='utf-8')) if args.verify else None
    # Read/validate only the local test URL; mask app URLs before app imports.
    url = local_test_url()
    with environment(DATABASE_URL='sqlite://', MIGRATION_DATABASE_URL=None, DEMO_SEED='0'):
        from sqlalchemy import select, text
        from sqlalchemy.orm import Session
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from app.models import Department, User
        from app.security import hash_password
        from scripts import first_load_live as live

        heads = ScriptDirectory.from_config(Config('alembic.ini')).get_heads()
        assert len(heads) == 1
        output = dict(python=platform.python_version(), zlib=zlib.ZLIB_VERSION,
                      alembic_heads=heads, serialization='UTF-8, ensure_ascii=False, sort_keys=True, separators=comma/colon',
                      source_books={str(year): live.book_config(year)[1] for year in (2026, 2027)}, years={})
        with disposable_database(url) as engine:
            with Session(engine) as db:
                output['postgresql'] = db.scalar(text('SHOW server_version'))
                parsed = live.verify_book(live.book_config(2026)[0], year=2026)
                loaded = inspect_import(db, deepcopy(parsed), live.book_config(2026)[0].name, year=2026)
                assert not loaded['apply_error']
                assert loaded['protected_2027_before'] == loaded['protected_2027_after']
                strategy = db.scalar(select(User).where(User.role == 'strategy'))
                strategy.department_id = db.scalar(select(Department.id).where(Department.name == 'Strateji Geliştirme Müdürlüğü'))
                strategy.position = 'director'
                strategy.password_hash = hash_password('Civ174-local-test-only!')
                db.commit()
                del parsed, loaded
            for year in (2026, 2027):
                print(f'{year}: measuring disposable fixture', flush=True)
                output['years'][str(year)] = measure(engine, year)
                print(f"{year}: {output['years'][str(year)]['publication_snapshot']['total_bytes']} publication bytes", flush=True)
    if expected:
        for year, measured in output['years'].items():
            baseline = expected['years'][year]
            for key in ('book_snapshot', 'publication_snapshot', 'frozen_payload_bytes', 'checks', 'attribution', 'publications_before'):
                assert measured[key] == baseline[key], f'{year}: {key} differs from saved run'
            for codec, sizes in measured['candidates']['codecs'].items():
                reference = baseline['candidates']['codecs'][codec]['envelope_bytes']
                assert abs(sizes['envelope_bytes']-reference) / reference < .01, f'{year}: codec size differs by >=1%'
            assert measured['candidates']['sizes'] == baseline['candidates']['sizes']
        print('Saved structural byte counts and counts reproduced; codec sizes within 1%; timings/memory are observations.')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(f'Measurements: {args.out}')


if __name__ == '__main__':
    main()
