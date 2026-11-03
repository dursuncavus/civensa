"""CIV-172: synthetic pinned pilot beside a full 2027 load; local PG only."""
import base64
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app import models as m
from app.db import Base
from ops import pp2026_rehearsal as rehearsal
from scripts import clear_pilot_2026 as clear
from scripts import first_load_live as live
from scripts.first_load_dryrun import NAME_MAP, local_test_url
from scripts.rehearse_clear_preprint_2027 import snapshot
from tests.first_load_checkpoint import disposable_first_load_database
from test_first_load_live import backup_files, TtyStub
from test_pp2026_rehearsal import (assert_private_summary, dispatch, dump_backup, pg18_clients)

PRIVATE = 'private-value secret-fixture private@example.invalid'


@pytest.fixture(scope='module')
def books():
    return {year: live.verify_book(live.book_config(year)[0], year=year) for year in (2026, 2027)}


@pytest.fixture(scope='module')
def pilot_base(books):
    with disposable_first_load_database(local_test_url()) as engine:
        with Session(engine, expire_on_commit=False) as db:
            org = m.Organization(name='CIV-172 disposable')
            actor = m.User(email='pilot@example.invalid', full_name=PRIVATE, role='strategy', password_hash='unused')
            db.add_all([org, actor])
            db.flush()
            names = set(json.loads(NAME_MAP.read_text())['map'].values()) | {'Yapı Kontrol Müdürlüğü'}
            db.add_all(m.Department(organization_id=org.id, name=n) for n in sorted(names))
            db.commit()
            ids = dict(organization_id=org.id, actor_id=actor.id)
        loaded = live.execute(engine, books[2027], apply=True, **ids)
        assert not loaded['failed'] and loaded['counts']['indicators'] == 263
        with Session(engine, expire_on_commit=False) as db:
            period = m.ReportingPeriod(year=2026, status='closed', template_status='verified')
            db.add(period)
            db.flush()
            pid = period.id
            dids = list(db.scalars(select(m.Department.id).order_by(m.Department.id)))[:34]
            assert len(dids) == 34
            programs = [m.Program(period_id=pid, name=PRIVATE + str(i)) for i in range(24)]
            db.add_all(programs)
            db.flush()
            subs = [m.SubProgram(period_id=pid, program_id=programs[i % 24].id, name=PRIVATE + str(i))
                    for i in range(40)]
            db.add_all(subs)
            db.flush()
            inds = [m.Indicator(period_id=pid, department_id=dids[i % 34], subprogram_id=subs[i % 40].id,
                                name=PRIVATE + str(i), unit='Adet', status='draft') for i in range(220)]
            acts = [m.Activity(period_id=pid, department_id=dids[i % 34], subprogram_id=subs[i % 40].id,
                               name=PRIVATE + str(i)) for i in range(174)]
            db.add_all(inds + acts)
            db.flush()
            db.add_all(m.IndicatorValue(indicator_id=ind.id, year=2024 + j, value_kind='target',
                                        value=None if j == 0 else '12.345678', raw_text=PRIVATE,
                                        state='needs_review' if j == 0 else 'verified')
                       for i, ind in enumerate(inds) for j in range(5 if i < 210 else 4))
            db.add_all(m.ActivityCostValue(activity_id=act.id, year=2024 + j, value_kind='budget',
                                           amount=None if j == 0 else '123.45', raw_text=PRIVATE)
                       for i, act in enumerate(acts) for j in range(7 if i < 75 else 6))
            db.add_all(m.DepartmentCostValue(period_id=pid, department_id=did, year=2026 + j,
                                             value_kind='budget', amount='100.25', raw_text=PRIVATE)
                       for did in dids[:33] for j in range(3))
            db.add_all(m.Submission(period_id=pid, department_id=did, status='approved' if i < 3 else 'draft')
                       for i, did in enumerate(dids))
            db.add_all(m.ImportBatch(period_id=pid, filename=PRIVATE, status=status, payload_json=PRIVATE,
                                     created_by=ids['actor_id']) for status in ('applied', 'preview'))
            db.add_all(m.AuditLog(user_id=ids['actor_id'], action='data_import_apply',
                                  entity_type='reporting_period', entity_id=pid, details=PRIVATE)
                       for _ in range(136))
            db.commit()
        yield engine, ids, dict(period_id=pid, department_id=dids[0], subprogram_id=subs[0].id,
                                indicator_id=inds[0].id, activity_id=acts[0].id)


@pytest.fixture
def pilot(pilot_base):
    source, ids, extra = pilot_base
    name = 'civ172_test_' + uuid4().hex
    admin = create_engine(local_test_url(), isolation_level='AUTOCOMMIT', poolclass=NullPool)
    with admin.connect() as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{name}" TEMPLATE "{source.url.database}"')
    engine = create_engine(source.url.set(database=name), poolclass=NullPool, hide_parameters=True)
    try:
        yield engine, ids, extra
    finally:
        engine.dispose()
        with admin.connect() as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.dispose()


def apply(engine, ids, tmp_path, **options):
    proof, _ = backup_files(tmp_path)
    return clear.execute(engine, **ids, apply=True, backup=proof,
                         confirmation=clear.CONFIRMATION, **options)


def rows(db, table):
    return sorted([dict(row) for row in db.execute(select(table)).mappings()], key=clear.encoded)


@pytest.mark.postgres
def test_plan_archive_clear_and_2026_load(pilot, books, tmp_path):
    engine, ids, extra = pilot
    before = snapshot(engine)
    plan = clear.execute(engine, **ids)
    assert snapshot(engine) == before
    assert {k: v for k, v in plan['counts'].items() if v} == clear.PINNED
    assert sum(plan['removed_counts'].values()) == 2802
    with Session(engine) as db:
        owned = rehearsal.period_inventory_tables(2026)
        archived = {name: rows(db, owned[name]) for name in plan['removed_counts']}
        retained = {name: rows(db, Base.metadata.tables[name]) for name in ('users', 'departments', 'audit_log')}
    result = apply(engine, ids, tmp_path)
    assert result['counts'] == plan['counts']
    assert result['protected_2027_before'] == result['protected_2027_after'] == plan['protected_2027_before']
    with Session(engine) as db:
        period = db.get(m.ReportingPeriod, extra['period_id'])
        assert (period.status, period.template_status) == ('draft', 'verified')
        for name in ('users', 'departments'):
            assert rows(db, Base.metadata.tables[name]) == retained[name]
        receipt = db.scalar(select(m.AuditLog).where(m.AuditLog.action == clear.ACTION))
        all_audit = rows(db, m.AuditLog.__table__)
        assert [row for row in all_audit if row['id'] != receipt.id] == retained['audit_log']
        details = json.loads(receipt.details)
        raw = gzip.decompress(base64.b64decode(details['archive']))
        assert hashlib.sha256(raw).hexdigest() == details['archive_sha256'] == result['archive_sha256']
        assert json.loads(raw) == json.loads(clear.encoded(archived))
        assert details['removed_counts'] == plan['removed_counts']
        assert details['period_before']['status'] == 'closed'
        for name in plan['removed_counts']:
            assert db.scalar(select(func.count()).select_from(rehearsal.period_inventory_tables(2026)[name])) == 0
    assert PRIVATE not in clear.format_summary(result)
    before_load = snapshot(engine)
    with pytest.raises(live.Refusal, match='sayısı uyuşmuyor'):
        apply(engine, ids, tmp_path)
    assert snapshot(engine) == before_load
    planned = live.execute(engine, books[2026], year=2026, **ids)
    assert snapshot(engine) == before_load
    assert (planned['counts']['cards'], planned['counts']['indicators']) == (105, 226)
    loaded = live.execute(engine, books[2026], year=2026, apply=True, **ids)
    assert not loaded['failed'] and loaded['counts'] == planned['counts']
    assert rehearsal.protected_state(engine)['hash'] == result['protected_2027_before']


@pytest.mark.postgres
@pytest.mark.parametrize('applying', [False, True])
@pytest.mark.parametrize('guard, message', [
    ('count', 'indicator_values.*beklenen 1090, bulunan 1089'),
    ('indicator-state', 'indicators.draft'), ('submission-state', 'submissions.approved'),
    ('batch-state', 'import_batches.applied'), ('period-state', 'closed/verified'),
    ('template-state', 'closed/verified'),
    ('head', 'şema'), ('audit', 'audit_log.*beklenen 136, bulunan 137'),
    ('actor', 'etkin Strateji'), ('organization', 'Tek kurum'),
])
def test_fingerprint_refusals_write_nothing(pilot, tmp_path, guard, message, applying):
    engine, ids, extra = pilot
    with Session(engine) as db:
        if guard == 'count':
            db.delete(db.scalar(select(m.IndicatorValue).where(m.IndicatorValue.indicator_id == extra['indicator_id'])))
        elif guard == 'indicator-state':
            db.get(m.Indicator, extra['indicator_id']).status = 'verified'
        elif guard == 'submission-state':
            db.scalar(select(m.Submission).where(m.Submission.period_id == extra['period_id'],
                                                  m.Submission.status == 'approved')).status = 'draft'
        elif guard == 'batch-state':
            db.scalar(select(m.ImportBatch).where(m.ImportBatch.period_id == extra['period_id'],
                                                   m.ImportBatch.status == 'applied')).status = 'preview'
        elif guard == 'period-state':
            db.get(m.ReportingPeriod, extra['period_id']).status = 'draft'
        elif guard == 'template-state':
            db.get(m.ReportingPeriod, extra['period_id']).template_status = 'unverified'
        elif guard == 'head':
            db.execute(text("UPDATE alembic_version SET version_num='wrong'"))
        elif guard == 'audit':
            db.add(m.AuditLog(action='login', entity_type='reporting_period', entity_id=extra['period_id']))
        elif guard == 'actor':
            db.get(m.User, ids['actor_id']).is_active = False
        elif guard == 'organization':
            db.add(m.Organization(name='Unexpected'))
        db.commit()
    before = snapshot(engine)
    with pytest.raises(live.Refusal, match=message):
        apply(engine, ids, tmp_path) if applying else clear.execute(engine, **ids)
    assert snapshot(engine) == before


@pytest.mark.postgres
@pytest.mark.parametrize('table', ['report_cards', 'economic_values', 'official_activities',
                                  'department_scopes', 'activity_reports', 'publications',
                                  'ar_documents', 'submission_events', 'template_snapshots'])
def test_hard_refusal_tables(pilot, tmp_path, table):
    engine, ids, extra = pilot
    pid, did, sid = extra['period_id'], extra['department_id'], extra['subprogram_id']
    with Session(engine) as db:
        objects = {
            'report_cards': lambda: m.ReportCard(period_id=pid, department_id=did, subprogram_id=sid),
            'economic_values': lambda: m.EconomicValue(period_id=pid, department_id=did, year=2026,
                value_kind='budget', category='personnel', program_group='total', funding_type='inside'),
            'official_activities': lambda: m.OfficialActivity(period_id=pid, program_name=PRIVATE,
                subprogram_name=PRIVATE, code='CIV172', name=PRIVATE),
            'department_scopes': lambda: m.DepartmentScope(period_id=pid, department_id=did),
            'activity_reports': lambda: m.ActivityReport(organization_id=ids['organization_id'], period_id=pid),
            'publications': lambda: m.Publication(period_id=pid, version=1, snapshot_json='{}',
                sha256='a' * 64, created_by=ids['actor_id']),
            'ar_documents': lambda: m.ARDocument(organization_id=ids['organization_id'], period_id=pid,
                scope='idare', definition_version=1, created_by=ids['actor_id']),
            'submission_events': lambda: m.SubmissionEvent(period_id=pid, department_id=did,
                submission_id=db.scalar(select(m.Submission.id).where(m.Submission.period_id == pid)), event_type='approved'),
            'template_snapshots': lambda: m.TemplateSnapshot(period_id=pid, filename=PRIVATE, file_type='docx'),
        }
        db.add(objects[table]())
        db.commit()
    before = snapshot(engine)
    for applying in (False, True):
        with pytest.raises(live.Refusal, match=table + '.*beklenen 0, bulunan 1'):
            apply(engine, ids, tmp_path) if applying else clear.execute(engine, **ids)
        assert snapshot(engine) == before


@pytest.mark.postgres
def test_cross_period_fk_refuses_before_cascade(pilot, tmp_path):
    engine, ids, extra = pilot
    with Session(engine) as db:
        act = db.scalar(select(m.Activity).where(m.Activity.period_id != extra['period_id']))
        act.subprogram_id = extra['subprogram_id']
        db.commit()
    before = snapshot(engine)
    with pytest.raises(live.Refusal, match='activities dönem dışı bağlantı'):
        apply(engine, ids, tmp_path)
    assert snapshot(engine) == before


@pytest.mark.postgres
def test_deep_actual_evidence_approval_graph_is_never_removed(pilot, tmp_path):
    engine, ids, extra = pilot
    with Session(engine) as db:
        pub = m.Publication(period_id=extra['period_id'], version=1, snapshot_json='{}',
                            sha256='a' * 64, created_by=ids['actor_id'])
        identity = m.IndicatorIdentity(indicator_id='civ172-identity', organization_id=ids['organization_id'])
        report = m.ActivityReport(organization_id=ids['organization_id'], period_id=extra['period_id'],
                                  current_revision=1)
        db.add_all([pub, identity, report])
        db.flush()
        definition = m.IndicatorDefinitionRevision(indicator_id=identity.indicator_id, revision=1,
            period_id=extra['period_id'], definition_json='{}', sha256='b' * 64, created_by=ids['actor_id'])
        revision = m.ActivityReportRevision(report_id=report.id, revision=1, publication_id=pub.id,
            publication_sha256=pub.sha256, created_by=ids['actor_id'])
        db.add_all([definition, revision])
        db.flush()
        binding = m.PublicationIndicatorBinding(publication_id=pub.id, snapshot_indicator_id=extra['indicator_id'],
            definition_revision_id=definition.id, department_id=extra['department_id'], created_by=ids['actor_id'], reason=PRIVATE)
        db.add(binding)
        db.flush()
        indicator = m.ReportIndicator(report_revision_id=revision.id, publication_binding_id=binding.id)
        db.add(indicator)
        db.flush()
        actual = m.ActualRevision(report_indicator_id=indicator.id, revision=1, state='needs_review',
            evidence_json='[]', explanation=PRIVATE, deviation_json='{}', created_by=ids['actor_id'])
        db.add(actual)
        db.flush()
        db.add_all([m.ActivityReportApproval(report_revision_id=revision.id, created_by=ids['actor_id']),
            m.ActivityEvidenceFile(actual_revision_id=actual.id, report_indicator_id=indicator.id,
                source_id='civ172', version=1, filename=PRIVATE, sha256='c' * 64,
                file_data=PRIVATE.encode(), created_by=ids['actor_id'])])
        db.commit()
        for name in ('actual_revisions', 'activity_evidence_files', 'activity_report_approvals',
                     'activity_report_revisions', 'publication_indicator_bindings'):
            assert db.scalar(select(func.count()).select_from(rehearsal.period_inventory_tables(2026)[name])) == 1
    before = snapshot(engine)
    for applying in (False, True):
        with pytest.raises(live.Refusal, match='activity_evidence_files.*beklenen 0, bulunan 1'):
            apply(engine, ids, tmp_path) if applying else clear.execute(engine, **ids)
        assert snapshot(engine) == before


@pytest.mark.postgres
def test_backup_rechecked_after_guards_before_any_write(pilot, tmp_path, monkeypatch):
    engine, ids, _ = pilot
    before = snapshot(engine)
    verify = live.verify_backup
    calls = []
    def expire(proof):
        calls.append(proof)
        if len(calls) == 2:
            raise live.Refusal('Yedek doğrulanamadı: 60 dakika')
        verify(proof)
    monkeypatch.setattr(live, 'verify_backup', expire)
    with pytest.raises(live.Refusal, match='60 dakika'):
        apply(engine, ids, tmp_path)
    assert len(calls) == 2 and snapshot(engine) == before


@pytest.mark.postgres
def test_cli_plan_and_tty_apply_print_only_counts(pilot, tmp_path, monkeypatch, capsys):
    engine, ids, _ = pilot
    proof, _ = backup_files(tmp_path)
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@127.0.0.1/never_connect')
    monkeypatch.setattr('sqlalchemy.create_engine', lambda *a, **kw: engine)
    tty = TtyStub(clear.CONFIRMATION + '\n')
    monkeypatch.setattr(live, 'open_tty', lambda: tty)
    args = ['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id'])]
    before = snapshot(engine)
    assert clear.main(args) == 0
    assert snapshot(engine) == before
    assert 'Hedefe 0 satır yazıldı' in capsys.readouterr().out
    assert clear.main(args + ['--apply', '--backup', str(proof)]) == 0
    output = capsys.readouterr()
    assert 'Arşiv SHA256:' in output.out and '2027 korunuyor: EVET' in output.out
    assert 'secret-fixture' not in output.out + output.err and output.err == ''
    assert clear.CONFIRMATION in tty.output.getvalue()


@pytest.mark.postgres
def test_changed_2027_hash_rolls_back_every_row(pilot, tmp_path):
    engine, ids, extra = pilot
    with engine.begin() as conn:
        conn.exec_driver_sql('''CREATE FUNCTION civ172_mutate() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN UPDATE indicators SET name='changed' WHERE period_id IN
          (SELECT id FROM reporting_periods WHERE year=2027); RETURN OLD; END $$''')
        conn.exec_driver_sql('CREATE TRIGGER civ172_mutate AFTER DELETE ON programs FOR EACH ROW EXECUTE FUNCTION civ172_mutate()')
    before = snapshot(engine)
    with pytest.raises(live.Refusal, match='2027 dönem hash'):
        apply(engine, ids, tmp_path)
    assert snapshot(engine)[0] == before[0]  # PostgreSQL sequences are nontransactional.


@pytest.mark.postgres
def test_shared_advisory_lock_refuses_without_writes(pilot, tmp_path):
    engine, ids, _ = pilot
    before = snapshot(engine)
    with engine.begin() as conn:
        conn.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': live.LOCK})
        with pytest.raises(live.Refusal, match='Başka ilk yükleme'):
            apply(engine, ids, tmp_path)
    assert snapshot(engine) == before


@pytest.mark.postgres
@pytest.mark.parametrize('proof_kind', ['missing', 'stale', 'wrong-confirmation'])
def test_apply_requires_backup_and_exact_confirmation(pilot, tmp_path, proof_kind):
    engine, ids, _ = pilot
    proof, _ = backup_files(tmp_path, age=3601 if proof_kind == 'stale' else 0)
    before = snapshot(engine)
    with pytest.raises(live.Refusal):
        clear.execute(engine, **ids, apply=True, backup=None if proof_kind == 'missing' else proof,
                      confirmation='wrong' if proof_kind == 'wrong-confirmation' else clear.CONFIRMATION)
    assert snapshot(engine) == before


@pytest.mark.parametrize('guard', ['no-tty', 'wrong', 'eof', 'missing', 'stale', 'pause'])
def test_cli_refuses_before_connection(tmp_path, monkeypatch, capsys, guard):
    proof, _ = backup_files(tmp_path, age=3601 if guard == 'stale' else 0)
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@127.0.0.1/never_connect')
    monkeypatch.setattr('sqlalchemy.create_engine', lambda *a, **kw: pytest.fail('connected'))
    def tty():
        if guard == 'no-tty':
            raise OSError('secret-fixture')
        if guard == 'pause':
            manifest = json.loads(proof.with_suffix('.manifest.json').read_text())
            manifest['utc_timestamp'] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
            proof.with_suffix('.manifest.json').write_text(json.dumps(manifest))
        return TtyStub('' if guard == 'eof' else (clear.CONFIRMATION if guard == 'pause' else 'wrong') + '\n')
    monkeypatch.setattr(live, 'open_tty', tty)
    args = ['--organization-id', '1', '--actor-id', '1', '--apply']
    if guard != 'missing':
        args += ['--backup', str(proof)]
    assert clear.main(args) == 1
    output = capsys.readouterr()
    assert output.out == '' and 'DURDU:' in output.err and 'secret-fixture' not in output.err


@pytest.mark.postgres
@pytest.mark.parametrize('enabled', [False, True])
def test_disposable_backup_rehearsal_chain(pilot, books, pg18_clients, tmp_path, monkeypatch, capsys, enabled):
    engine, ids, _ = pilot
    before = snapshot(engine)
    proof = dump_backup(engine, tmp_path)
    dispatch(monkeypatch, tmp_path)
    # The workflow shares its private TMPDIR with containerized PG clients.
    # Pytest may have cached another tempfile directory before this dispatch.
    monkeypatch.setenv('TMPDIR', str(tmp_path))
    monkeypatch.setattr('tempfile.tempdir', None)
    monkeypatch.setenv('CIVENSA_REHEARSAL_CLEAR_CONFIRM', clear.CONFIRMATION if enabled else '')
    monkeypatch.setattr(rehearsal, 'download_verified_run', lambda _: (proof, {}))
    result = rehearsal.main()
    report = assert_private_summary(tmp_path, capsys)
    assert result == (0 if enabled else 1), report
    assert snapshot(engine) == before
    if enabled:
        assert 'PASS' in report and 'Arşiv SHA256:' in report and '| indicators | 220 | 220 |' in report
    else:
        assert '2026 dönemi dolu' in report and '0 satır yazıldı' in report


def test_wrong_workflow_clear_input_refuses_before_download(tmp_path, monkeypatch, capsys):
    dispatch(monkeypatch, tmp_path)
    monkeypatch.setenv('CIVENSA_REHEARSAL_CLEAR_CONFIRM', PRIVATE)
    monkeypatch.setattr(rehearsal, 'download_verified_run', lambda _: pytest.fail('downloaded'))
    assert rehearsal.main() == 1
    assert 'temizleme onayı uyuşmuyor' in assert_private_summary(tmp_path, capsys)


def test_workflow_passes_clear_input_as_environment():
    workflow = Path('.github/workflows/pp2026-backup-rehearsal.yml').read_text()
    assert 'clear_confirmation:' in workflow
    assert 'CIVENSA_REHEARSAL_CLEAR_CONFIRM: ${{ inputs.clear_confirmation }}' in workflow


def test_loader_refusal_after_clear_does_not_use_old_occupied_counts(monkeypatch):
    record = {'source_2026': {'counts': {'programs': 24}}, 'clear-apply': {}}
    monkeypatch.setattr(rehearsal, 'snapshot', lambda _: 'unchanged')
    def refuse(*args, **kwargs):
        raise live.Refusal('Plan reddedildi')
    monkeypatch.setattr(live, 'execute', refuse)
    with pytest.raises(live.Refusal, match='Plan reddedildi'):
        rehearsal.run_loader(None, {'departments': []}, {}, record, 'plan')
    assert 'message' not in record
