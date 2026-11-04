"""CIV-168: real pg_dump/restore of synthetic data; never a production connection."""
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from ops import pp2026_rehearsal as rehearsal
from scripts import first_load_live as live
from scripts.first_load_dryrun import NAME_MAP, local_test_url
from scripts.rehearse_clear_preprint_2027 import pg_environment, private, snapshot, state
from test_first_load_live import printed, target


@pytest.fixture(scope='module')
def pg18_clients(tmp_path_factory):
    """CI already has the service's postgres:18 image; host clients may be 16."""
    if all(shutil.which(tool) and ' 18.' in subprocess.check_output([tool, '--version'], text=True)
           for tool in ('pg_dump', 'pg_restore')):
        yield
        return
    root = tmp_path_factory.getbasetemp()
    bin_dir = tmp_path_factory.mktemp('pg18-bin')
    shim = bin_dir / 'pg-client'
    shim.write_text('''#!/usr/bin/env bash
set -euo pipefail
exec docker run --rm --log-driver=none --network host \\
  --user "$(id -u):$(id -g)" \\
  --env PGDATABASE --env PGHOST --env PGHOSTADDR --env PGPORT \\
  --env PGUSER --env PGPASSWORD --env PGCONNECT_TIMEOUT \\
  --volume "$CIV168_TEST_TMP:$CIV168_TEST_TMP" postgres:18 "$(basename "$0")" "$@"
''')
    shim.chmod(0o700)
    for tool in ('pg_dump', 'pg_restore'):
        (bin_dir / tool).symlink_to(shim)
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv('CIV168_TEST_TMP', str(root))
        patch.setenv('PATH', str(bin_dir) + os.pathsep + os.environ['PATH'])
        yield


def dump_backup(engine, tmp_path):
    dump = tmp_path / 'synthetic.dump'
    private(['pg_dump', '--format=custom', '--file', str(dump)], pg_environment(engine.url))
    saved = dict(state(engine), utc_timestamp=datetime.now(timezone.utc).isoformat(),
                 file_name=dump.name, file_size_bytes=dump.stat().st_size,
                 sha256=hashlib.sha256(dump.read_bytes()).hexdigest())
    dump.with_suffix('.manifest.json').write_text(json.dumps(saved))
    return dump


def dispatch(monkeypatch, tmp_path):
    monkeypatch.setenv('GITHUB_ACTIONS', 'true')
    monkeypatch.setenv('GITHUB_EVENT_NAME', 'workflow_dispatch')
    monkeypatch.setenv('CIVENSA_REHEARSAL_BOOK_CONFIRM', rehearsal.CONFIRMATION)
    monkeypatch.setenv('CIVENSA_REHEARSAL_BACKUP_RUN', '123')
    monkeypatch.setenv('GITHUB_STEP_SUMMARY', str(tmp_path / 'summary.md'))
    monkeypatch.setenv('CIVENSA_REHEARSAL_ORG_ID', '')
    monkeypatch.setenv('CIVENSA_REHEARSAL_ACTOR_ID', '')
    # The production workflow uses a literal IP, never DNS or libpq overrides.
    url = local_test_url().set(host='127.0.0.1')
    monkeypatch.setenv('CIVENSA_TEST_POSTGRES_URL', url.render_as_string(hide_password=False))


def assert_private_summary(tmp_path, capsys):
    report = (tmp_path / 'summary.md').read_text()
    assert not re.search(r'://|[\w.+-]+@[\w.-]+|password|PGPASSWORD|secret-fixture|private-value', report, re.I)
    output = capsys.readouterr()
    assert output.out == output.err == ''
    return report


@pytest.mark.postgres
def test_full_backup_restore_pass_preserves_2027_edit_and_extra_scope(
        target, printed, pg18_clients, tmp_path, monkeypatch, capsys):
    from app.models import (Department, DepartmentScope, IndicatorValue, ReportingPeriod, User)
    engine, ids = target
    names = set(json.loads(NAME_MAP.read_text())['map'].values()) | {'Yapı Kontrol Müdürlüğü'}
    with Session(engine) as db:
        db.add_all(Department(organization_id=ids['organization_id'], name=n) for n in sorted(names))
        db.commit()
    assert not live.execute(engine, printed, apply=True, **ids)['failed']
    with Session(engine) as db:
        user = db.get(User, ids['actor_id'])
        user.full_name, user.email, user.password_hash = 'secret-fixture', 'private@example.invalid', 'secret-fixture-password'
        value = db.scalar(select(IndicatorValue).order_by(IndicatorValue.id))
        value_id = value.id
        value.value, value.raw_text, value.state = Decimal('987654.32'), 'private-value', 'verified'
        pid = db.scalar(select(ReportingPeriod.id).where(ReportingPeriod.year == 2027))
        scoped = select(DepartmentScope.department_id).where(DepartmentScope.period_id == pid)
        did = db.scalar(select(Department.id).where(Department.id.not_in(scoped)).order_by(Department.id))
        assert did is not None
        extra = DepartmentScope(period_id=pid, department_id=did, display_name='private-value scope')
        db.add(extra)
        # Empty 2026 period from another workflow must remain usable.
        db.add(ReportingPeriod(year=2026, status='draft', template_status='verified'))
        db.commit()
        scope_id = extra.id
    protected = rehearsal.protected_state(engine)
    dump = dump_backup(engine, tmp_path)
    dispatch(monkeypatch, tmp_path)
    monkeypatch.setattr(rehearsal, 'download_verified_run', lambda _: (dump, {}))
    seen = {}
    actual_empty = rehearsal.empty_database

    @contextmanager
    def inspect_copy(url):
        with actual_empty(url) as restored:
            yield restored
            seen.update(protected=rehearsal.protected_state(restored))
            with Session(restored) as db:
                saved = db.get(IndicatorValue, value_id)
                seen['value'] = (saved.value, saved.raw_text)
                seen['scope'] = db.get(DepartmentScope, scope_id).display_name
                seen['names'] = list(db.scalars(select(DepartmentScope.display_name).join(
                    ReportingPeriod).where(ReportingPeriod.year == 2026)))
    monkeypatch.setattr(rehearsal, 'empty_database', inspect_copy)
    capsys.readouterr()  # Discard synthetic source preparation, not runner output.
    assert rehearsal.main() == 0
    assert seen['protected'] == protected
    assert seen['value'] == (Decimal('987654.32'), 'private-value')
    assert seen['scope'] == 'private-value scope'
    assert len(seen['names']) == 33
    assert any(seen['names'])
    report = assert_private_summary(tmp_path, capsys)
    assert '2026 PP yedek provası: PASS' in report
    assert '| Uygulama | 33 | 105 | 226 | 0 | 0 |' in report
    assert '0 yazma / 33 atlanan' in report
    assert 'Kalıcı gösterge kimliği atanan: **0**' in report
    assert report.count(protected['hash']) == 4
    assert 'Mevcut: evet; durum: draft; şablon: verified' in report


@pytest.mark.postgres
@pytest.mark.parametrize('pp_model', ['ImportBatch', 'Program', 'OfficialActivity', 'EconomicValue'])
def test_occupied_2026_loader_refusal_zero_writes(
        pp_model, target, pg18_clients, tmp_path, monkeypatch, capsys):
    from app import models
    engine, ids = target
    with Session(engine) as db:
        period = models.ReportingPeriod(year=2026, status='draft', template_status='verified')
        db.add(period)
        db.flush()
        kwargs = dict(period_id=period.id)
        if pp_model == 'ImportBatch':
            kwargs.update(filename='private@example.invalid', status='preview', payload_json='{}', created_by=ids['actor_id'])
        elif pp_model == 'EconomicValue':
            department = models.Department(organization_id=ids['organization_id'], name='Test Müdürlüğü')
            db.add(department)
            db.flush()
            kwargs.update(department_id=department.id, year=2026, value_kind='budget', category='personnel',
                          program_group='total', funding_type='inside', raw_text='private-value')
        else:
            kwargs['name'] = 'private-value'
            if pp_model == 'OfficialActivity':
                kwargs.update(program_name='private-value', subprogram_name='private-value', code='1')
        db.add(getattr(models, pp_model)(**kwargs))
        db.commit()
    original = snapshot(engine)
    dump = dump_backup(engine, tmp_path)
    dispatch(monkeypatch, tmp_path)
    monkeypatch.setattr(rehearsal, 'download_verified_run', lambda _: (dump, {}))
    actual_empty = rehearsal.empty_database
    unchanged = []

    @contextmanager
    def inspect_refusal(url):
        with actual_empty(url) as restored:
            try:
                yield restored
            finally:
                unchanged.append(snapshot(restored) == original)
    monkeypatch.setattr(rehearsal, 'empty_database', inspect_refusal)
    capsys.readouterr()
    assert rehearsal.main() == 1
    assert unchanged == [True]
    assert snapshot(engine) == original
    report = assert_private_summary(tmp_path, capsys)
    assert '2026 dönemi dolu' in report
    assert '| Plan | — | — | — | 1 |' in report
    assert '| ' + getattr(models, pp_model).__tablename__ + ' | 1 |' in report
    assert '0 satır yazıldı' in report


def test_wrong_confirmation_refuses_before_download(tmp_path, monkeypatch, capsys):
    dispatch(monkeypatch, tmp_path)
    monkeypatch.setenv('CIVENSA_REHEARSAL_BOOK_CONFIRM', 'wrong')
    monkeypatch.setattr(rehearsal, 'download_verified_run', lambda _: pytest.fail('download started'))
    assert rehearsal.main() == 1
    assert 'Kitap onayı uyuşmuyor' in assert_private_summary(tmp_path, capsys)


@pytest.mark.parametrize('url', [
    'postgresql+psycopg://u:secret-fixture@live.example.invalid/db',
    'postgresql+psycopg://u:secret-fixture@127.0.0.1/db?host=live.example.invalid',
    'postgresql+psycopg://u:secret-fixture@localhost/db',
    'postgresql+psycopg:///db', 'invalid-private@example.invalid',
])
def test_non_service_url_refuses_before_download(url, tmp_path, monkeypatch, capsys):
    dispatch(monkeypatch, tmp_path)
    monkeypatch.setenv('CIVENSA_TEST_POSTGRES_URL', url)
    monkeypatch.setattr(rehearsal, 'download_verified_run', lambda _: pytest.fail('download started'))
    assert rehearsal.main() == 1
    assert_private_summary(tmp_path, capsys)
    with pytest.raises(live.Refusal, match='127.0.0.1'):
        rehearsal.rehearse(tmp_path / 'absent.dump', {})


@pytest.mark.parametrize('phase', ['download', 'restore', 'context', 'plan', 'apply', 'resume', 'protection'])
def test_private_exception_is_not_reported(phase, tmp_path, monkeypatch, capsys):
    dispatch(monkeypatch, tmp_path)
    def fail(*args):
        raise ValueError('postgresql://private@example.invalid/db secret-fixture-password')
    if phase == 'download':
        monkeypatch.setattr(rehearsal, 'download_verified_run', fail)
    else:
        monkeypatch.setattr(rehearsal, 'download_verified_run', lambda _: (Path('unused'), {}))
        def broken_rehearsal(backup, record):
            record.update(status='PASS', phase=phase)  # Cleanup failure must still fail the job.
            fail()
        monkeypatch.setattr(rehearsal, 'rehearse', broken_rehearsal)
    assert rehearsal.main() == 1
    assert rehearsal.PHASES[phase] in assert_private_summary(tmp_path, capsys)


def test_workflow_secret_and_dispatch_contract():
    workflow = Path('.github/workflows/pp2026-backup-rehearsal.yml').read_text()
    assert 'pull_request:' not in workflow and 'push:' not in workflow
    assert "if: github.event_name == 'workflow_dispatch'" in workflow
    assert 'environment: production' in workflow
    assert 'if: always()' in workflow
    assert 'run: python -m ops.pp2026_rehearsal' in workflow
    assert 'CIVENSA_REHEARSAL_BOOK_CONFIRM: ${{ inputs.book_confirmation }}' in workflow
    assert rehearsal.CONFIRMATION == live.book_config(2026)[1][:12]


def test_resume_plan_must_preserve_rows_and_sequences(monkeypatch):
    parsed = dict(departments=[dict(name='Test Müdürlüğü')])
    result = dict(counts={'departments': 0}, departments=[dict(source_name='Test Müdürlüğü', action='skip')],
                  skipped=[{}], failed=[], validation=[])
    monkeypatch.setattr(live, 'execute', lambda *a, **kw: result)
    snapshots = iter([('before-rows', 'before-sequences'), ('before-rows', 'changed-sequences')])
    monkeypatch.setattr(rehearsal, 'snapshot', lambda _: next(snapshots))
    record = {}
    with pytest.raises(live.Refusal, match='Salt okunur plan satır/sıra değiştirdi'):
        rehearsal.run_loader(None, parsed, {}, record, 'resume', resume=True)
    assert 'writes' not in record['resume']


def test_failed_loader_result_keeps_only_public_names_and_counts(monkeypatch):
    parsed = dict(departments=[dict(name='Test Müdürlüğü')])
    result = dict(counts={'departments': 0}, departments=[dict(source_name='Test Müdürlüğü', action='skip')],
                  skipped=[], failed=[dict(name='Test Müdürlüğü', reason='private@example.invalid secret-fixture')],
                  validation=[{'errors': ['private-value']}])
    def failed_loader(*a, **kw):
        print('postgresql://private@example.invalid/db secret-fixture')
        return result
    monkeypatch.setattr(live, 'execute', failed_loader)
    record = {}
    with pytest.raises(live.Refusal, match='başarısız müdürlük'):
        rehearsal.run_loader(None, parsed, {}, record, 'apply', apply=True)
    assert record['apply']['failed_count'] == 1
    assert record['apply']['failed'] == ['Test Müdürlüğü']
    assert not re.search('private|secret-fixture', json.dumps(record))


def test_failed_loader_detail_publishes_only_structured_grammar(monkeypatch):
    """D-396: structured detail is published; free text never is."""
    parsed = dict(departments=[dict(name='A Müdürlüğü'), dict(name='B Müdürlüğü')])
    result = dict(counts={'departments': 0}, skipped=[], validation=[],
                  departments=[dict(source_name='A Müdürlüğü', action='skip'),
                               dict(source_name='B Müdürlüğü', action='skip')],
                  failed=[dict(name='A Müdürlüğü', reason='private secret-fixture',
                               detail='IntegrityError, SQLSTATE 23505, tablo official_activities, '
                                      'kısıt uq_entry, konum app/first_load_service.py:120'),
                          dict(name='B Müdürlüğü', reason='x',
                               detail='ValueError, konum app/x.py:1 postgresql://private@example.invalid secret-fixture')])
    monkeypatch.setattr(live, 'execute', lambda *a, **kw: result)
    record = {}
    with pytest.raises(live.Refusal, match='başarısız müdürlük'):
        rehearsal.run_loader(None, parsed, {}, record, 'apply', apply=True)
    assert record['apply']['failed_details'] == [
        dict(name='A Müdürlüğü', detail='IntegrityError, SQLSTATE 23505, tablo official_activities, '
                                        'kısıt uq_entry, konum app/first_load_service.py:120'),
        dict(name='B Müdürlüğü', detail='ayrıntı gizlendi')]
    assert not re.search('private|secret-fixture', json.dumps(record))
