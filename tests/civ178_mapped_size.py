"""Measure the mapped 2026 approved publication in disposable local PostgreSQL.

Run from the repository root: python -m tests.civ178_mapped_size
Only CIVENSA_TEST_POSTGRES_URL is accepted. Never invokes the live loader CLI.
"""
import argparse
from collections import defaultdict
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
import platform
import re
import signal
import time

from scripts.first_load_dryrun import disposable_database, environment, inspect_import, local_test_url
from tests.civ175_size import encode, load_memory, members

CSV_PATH = Path('docs/lead/data/2026-faaliyet-eslestirme-taslagi.csv')
PASSWORD = 'Civ178-local-test-only!'


def translated_csv(db, pid):
    """Exact (department, name, ordinal by ID) translation; never reuse live IDs."""
    from sqlalchemy import select
    from app.models import Activity, Department
    from app.structure_service import period_name

    original = CSV_PATH.read_bytes()
    reader = csv.DictReader(io.StringIO(original.decode('utf-8-sig')))
    source_rows = list(reader)
    assert len(source_rows) == 128
    assert len({int(row['Faaliyet ID']) for row in source_rows}) == 128
    local = defaultdict(list)
    names = {d.id: period_name(db, pid, d) for d in db.scalars(select(Department))}
    for activity in db.scalars(select(Activity).where(Activity.period_id == pid).order_by(Activity.id)):
        local[names[activity.department_id], activity.name].append(activity)
    live_groups = defaultdict(list)
    for row in source_rows:
        assert row['Seçilecek Program / Alt Program'].strip()
        live_groups[row['Müdürlük'], row['Faaliyet']].append(row)
    matched = set()
    for key, rows in live_groups.items():
        candidates = local[key]
        # All occurrences must be present, otherwise the live ordinal is ambiguous.
        assert len(candidates) == len(rows), f'Non-unique/missing exact activity match: {key}'
        for row, activity in zip(sorted(rows, key=lambda r: int(r['Faaliyet ID'])), candidates):
            assert activity.id not in matched and activity.subprogram_id is None
            matched.add(activity.id)
            row['Faaliyet ID'] = str(activity.id)
    assert len(matched) == 128
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(source_rows)
    return output.getvalue().encode('utf-8-sig'), dict(
        source_sha256=hashlib.sha256(original).hexdigest(), rows=len(matched),
        identity='exact department name, activity name, ordinal ordered by id')


def pdf_measurement(payload):
    from app.book_export import export_book

    def timeout(signum, frame):
        raise TimeoutError('Full PP PDF exceeded 120 seconds')

    previous_handler = signal.signal(signal.SIGALRM, timeout)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, 120)
    started = time.perf_counter()
    try:
        data, mime = export_book(payload, 'pdf')
        assert mime == 'application/pdf' and data.startswith(b'%PDF-')
        return dict(status='ok', seconds=time.perf_counter() - started, bytes=len(data), limit_seconds=120)
    except TimeoutError:
        return dict(status='timeout', seconds=time.perf_counter() - started, limit_seconds=120)
    finally:
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)
        signal.signal(signal.SIGALRM, previous_handler)


def measure(engine):
    from fastapi.testclient import TestClient
    from sqlalchemy import select, func
    from sqlalchemy.orm import Session
    from app.db import get_db
    from app.main import app
    from app.models import Activity, Publication, ReportingPeriod, User
    from app.program_service import publication_checks

    result = {}
    with Session(engine, expire_on_commit=False) as db:
        pid = db.scalar(select(ReportingPeriod.id).where(ReportingPeriod.year == 2026))
        assert db.scalar(select(func.count()).select_from(Publication).where(Publication.period_id == pid)) == 0
        data, result['mapping'] = translated_csv(db, pid)
        strategy = db.scalar(select(User).where(User.role == 'strategy'))
        previous_overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = lambda: db
        client = TestClient(app, follow_redirects=False)  # no lifespan/startup DB
        try:
            response = client.post('/login', data=dict(email=strategy.email, password=PASSWORD))
            assert response.status_code == 303
            token = re.search(r'name="csrf_token" value="([^"]+)"', client.get('/modules').text).group(1)
            response = client.post('/api/activity-mappings/import-apply',
                data=dict(csrf_token=token, period_id=pid),
                files={'file': ('mapping.csv', data, 'text/csv')})
            assert response.status_code == 200, response.text[:1200]
            result['mapping']['response'] = response.json()
            assert response.json()['updated'] == 128
            assert db.scalar(select(func.count()).select_from(Activity).where(
                Activity.period_id == pid, Activity.subprogram_id.is_(None))) == 0
            started = time.perf_counter()
            checks = publication_checks(db, pid)
            result['publication_checks'] = dict(seconds=time.perf_counter() - started,
                count=len(checks), errors=sum(len(c['errors']) for c in checks),
                warnings=sum(len(c.get('warnings', [])) for c in checks))
            del checks
            started = time.perf_counter()
            response = client.post('/report-builder/publish-approved-book', data=dict(
                csrf_token=token, period_id=pid, approval_reference='Meclis kararı, 16.10.2025'))
            assert response.status_code == 303, response.text[:1200]
            result['publish_seconds'] = time.perf_counter() - started
        finally:
            client.close()
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
        publication = db.scalar(select(Publication).where(Publication.period_id == pid))
        raw = publication.snapshot_json
        assert hashlib.sha256(raw.encode()).hexdigest() == publication.sha256
        result['json_loads'] = load_memory(raw)
        payload = json.loads(raw)
        assert encode(payload) == raw.encode()
        assert payload['activity_mapping'] == dict(count=128, batch_ids=[result['mapping']['response']['batch_id']])
        result['publication_snapshot'] = members(payload)
        result['cost_reconciliation_bytes'] = len(encode(payload['cost_reconciliation']))
        result['activity_mapping'] = payload['activity_mapping']
        print('2026: measuring full published PP PDF (120 s limit)', flush=True)
        result['pdf'] = pdf_measurement(payload)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('docs/reports/civ-178/measurements.json'))
    args = parser.parse_args()
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
        output = dict(python=platform.python_version(), alembic_heads=heads,
            serialization='UTF-8, ensure_ascii=False, sort_keys=True, separators=comma/colon',
            source_book_sha256=live.book_config(2026)[1], year=2026)
        with disposable_database(url) as engine:
            with Session(engine) as db:
                output['postgresql'] = db.scalar(text('SHOW server_version'))
                parsed = live.verify_book(live.book_config(2026)[0], year=2026)
                loaded = inspect_import(db, deepcopy(parsed), live.book_config(2026)[0].name, year=2026)
                assert not loaded['apply_error']
                assert loaded['protected_2027_before'] == loaded['protected_2027_after']
                output['protected_2027_unchanged'] = True
                strategy = db.scalar(select(User).where(User.role == 'strategy'))
                strategy.department_id = db.scalar(select(Department.id).where(Department.name == 'Strateji Geliştirme Müdürlüğü'))
                strategy.position = 'director'
                strategy.password_hash = hash_password(PASSWORD)
                db.commit()
            output.update(measure(engine))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(f"2026: {output['publication_snapshot']['total_bytes']} publication bytes; PDF {output['pdf']}", flush=True)
    print(f'Measurements: {args.out}')


if __name__ == '__main__':
    main()
