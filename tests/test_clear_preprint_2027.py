"""CIV-058: migrated, disposable PostgreSQL; no production access."""
from copy import deepcopy
from datetime import datetime
import hashlib
import json

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from scripts import first_load_live as live
from scripts import clear_preprint_2027 as clear
from scripts.first_load_dryrun import local_test_url
from tests.first_load_checkpoint import disposable_release50_database
from app import models as m


@pytest.fixture(scope='module')
def printed():
    return live.verify_book(live.BOOK)


def state(engine):
    """Compare every row, as well as all sequence values; no row data is logged."""
    with engine.connect() as conn:
        tables = list(conn.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")))
        rows = {}
        for table in tables:
            values = sorted(str(row) for row in conn.exec_driver_sql(f'SELECT * FROM public."{table}"'))
            rows[table] = hashlib.sha256(repr(values).encode()).hexdigest()
        seqs = list(conn.execute(text("SELECT sequencename, last_value FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename")))
        return rows, seqs


@pytest.fixture
def target(printed):
    with disposable_release50_database(local_test_url()) as engine:
        with Session(engine) as db:
            org = m.Organization(name='CIV-058 disposable')
            actor = m.User(email='clear@example.invalid', full_name='Strateji Kullanıcısı',
                           password_hash='unused', role='strategy')
            old = m.ReportingPeriod(year=2026, status='active')
            db.add_all([org, actor, old])
            db.flush()
            period = m.ReportingPeriod(year=2027, status='active')
            db.add(period)
            db.flush()
            names = [i['source']['name'] for i in live.department_plan(db, printed, set()) if not i['skip']]
            departments = [m.Department(organization_id=org.id, name=n) for n in names]
            db.add_all(departments)
            db.flush()
            program = m.Program(period_id=period.id, name='Ön baskı programı')
            old_program = m.Program(period_id=old.id, name='2026 korunur')
            db.add_all([program, old_program])
            db.flush()
            sp = m.SubProgram(period_id=period.id, program_id=program.id, name='Ön baskı alt programı')
            old_sp = m.SubProgram(period_id=old.id, program_id=old_program.id, name='2026 korunur')
            db.add_all([sp, old_sp])
            db.flush()
            payload = dict(departments=[], summary={'source_years': [2027]})
            for index, dept in enumerate(departments):
                indicator = dict(name=f'Taslak gösterge {index}', unit='Adet',
                                 values=[dict(year=2027, kind='target', value='2.5', raw_text='2,5', state='verified')])
                activity = dict(name=f'Taslak faaliyet {index}', explanation='Kaynak açıklama',
                                costs=[dict(year=2027, kind='budget', amount='10.25',
                                            funding_type='total', raw_text='10,25'),
                                       dict(year=2028, kind='forecast', amount=None,
                                            funding_type='total', raw_text='', state='needs_review')])
                personnel = [dict(year=2027, kind='budget', amount='100.25', raw_text='100,25'),
                             dict(year=2028, kind='forecast', amount='200.002', raw_text='200,002'),
                             dict(year=2029, kind='forecast', amount=None, raw_text='', state='needs_review')] if index < 31 else []
                db.add_all([m.DepartmentCostValue(
                    period_id=period.id, department_id=dept.id, year=row['year'],
                    value_kind=row['kind'], amount=row['amount'], raw_text=row['raw_text'],
                    category='personnel_sgk', state=row.get('state', 'verified')) for row in personnel])
                payload['departments'].append(dict(name=dept.name, blocks=[dict(
                    program=program.name, subprogram=sp.name, budget_year=2027, indicators=[indicator])],
                    activities=[activity], personnel=personnel))
                ind = m.Indicator(period_id=period.id, department_id=dept.id, subprogram_id=sp.id,
                                  name=indicator['name'], unit='Adet')
                act = m.Activity(period_id=period.id, department_id=dept.id, subprogram_id=sp.id,
                                 name=activity['name'], explanation=activity['explanation'])
                db.add_all([ind, act, m.Submission(period_id=period.id, department_id=dept.id)])
                db.flush()
                db.add(m.IndicatorValue(indicator_id=ind.id, year=2027, value_kind='target',
                                        value='2.5', raw_text='2,5'))
                db.add_all([m.ActivityCostValue(activity_id=act.id, year=2027, value_kind='budget',
                                                amount='10.25', raw_text='10,25'),
                            m.ActivityCostValue(activity_id=act.id, year=2028, value_kind='forecast',
                                                amount=None, raw_text='', state='needs_review')])
            # Cross-period content shares departments and even a value's calendar year.
            ind26 = m.Indicator(period_id=old.id, department_id=departments[0].id,
                                subprogram_id=old_sp.id, name='2026 kalır', unit='Adet')
            act26 = m.Activity(period_id=old.id, department_id=departments[0].id,
                               subprogram_id=old_sp.id, name='2026 kalır')
            db.add_all([ind26, act26])
            db.flush()
            db.add_all([m.IndicatorValue(indicator_id=ind26.id, year=2027, value_kind='forecast', value=77),
                        m.ActivityCostValue(activity_id=act26.id, year=2027, value_kind='forecast', amount=77)])
            old_cost = m.DepartmentCostValue(period_id=old.id, department_id=departments[0].id,
                year=2027, value_kind='forecast', category='personnel_sgk', amount=77, raw_text='77')
            db.add(old_cost)
            db.flush()
            snapshot = dict(departments=[{'department_id': d.id, 'department_name': d.name} for d in departments],
                            created_department_ids=[])
            for bid, status in clear.BATCH_STATES.items():
                stamp = datetime(2026, 9, 21, 14, bid)
                db.add(m.ImportBatch(id=bid, period_id=period.id, filename='preprint.docx',
                    status=status, payload_json=json.dumps(payload, ensure_ascii=False),
                    snapshot_json=json.dumps(snapshot), created_by=actor.id, created_at=stamp,
                    applied_at=stamp if status in {'applied', 'reverted'} else None))
            db.add(m.AuditLog(user_id=actor.id, action='login', entity_type='user',
                             entity_id=actor.id, created_at=datetime(2026, 10, 20)))
            db.execute(text("SELECT setval(pg_get_serial_sequence('import_batches','id'),10,true)"))
            db.commit()
            ids = dict(organization_id=org.id, actor_id=actor.id)
            extra = dict(period_id=period.id, department_id=departments[0].id,
                         subprogram_id=sp.id, old_indicator_id=ind26.id, old_activity_id=act26.id,
                         old_cost_id=old_cost.id)
        yield engine, ids, extra


@pytest.mark.postgres
def test_clear_chain_and_preserved_rows(target, printed):
    engine, ids, extra = target
    before = state(engine)
    plan = clear.execute(engine, **ids)
    assert state(engine) == before
    assert len(plan['departments']) == 33
    before_rows = before[0]
    assert plan['counts'] == dict(indicators=33, indicator_values=33, activities=33,
        activity_cost_values=66, department_cost_values=93, submissions=33, submission_events=0,
        activity_catalogue_links=0, department_scopes=0, subprogram_scopes=0)
    assert [d['counts']['department_cost_values'] for d in plan['departments']] == [3] * 31 + [0] * 2
    with Session(engine) as db:
        audit_before = {a.id: tuple(getattr(a, c.name) for c in m.AuditLog.__table__.columns)
                        for a in db.scalars(select(m.AuditLog))}
        batches_before = {b.id: clear.batch_state(b) for b in db.scalars(select(m.ImportBatch))}
    applied = clear.execute(engine, apply=True, **ids)
    assert applied['counts'] == plan['counts']
    with Session(engine) as db:
        assert db.get(m.Indicator, extra['old_indicator_id']).name == '2026 kalır'
        assert db.get(m.Activity, extra['old_activity_id']).name == '2026 kalır'
        assert db.scalar(select(m.IndicatorValue.value).where(
            m.IndicatorValue.indicator_id == extra['old_indicator_id'])) == 77
        assert db.scalar(select(m.ActivityCostValue.amount).where(
            m.ActivityCostValue.activity_id == extra['old_activity_id'])) == 77
        assert db.get(m.DepartmentCostValue, extra['old_cost_id']).amount == 77
        assert len(db.scalars(select(m.DepartmentCostValue)).all()) == 1
        assert len(db.scalars(select(m.User)).all()) == 1
        assert len(db.scalars(select(m.Department)).all()) == 33
        assert len(db.scalars(select(m.ReportingPeriod)).all()) == 2
        assert len(db.scalars(select(m.Program)).all()) == 2
        assert len(db.scalars(select(m.ImportBatch)).all()) == 8
        assert {b.id: clear.batch_state(b) for b in db.scalars(select(m.ImportBatch))} == batches_before
        assert set(db.scalars(select(m.ImportBatch.status))) == {'superseded'}
        assert len(db.scalars(select(m.AuditLog)).all()) == len(audit_before) + 1
        assert {aid: tuple(getattr(db.get(m.AuditLog, aid), c.name)
                          for c in m.AuditLog.__table__.columns)
                for aid in audit_before} == audit_before
        receipt = db.scalar(select(m.AuditLog).where(m.AuditLog.action == clear.ACTION))
        assert json.loads(receipt.details)['counts'] == plan['counts']
    after = state(engine)
    allowed_changes = set(clear.FIELDS) | {'audit_log', 'import_batches'}
    assert {t: h for t, h in after[0].items() if t not in allowed_changes} == {
        t: h for t, h in before_rows.items() if t not in allowed_changes}
    repeated = clear.execute(engine, apply=True, **ids)
    assert repeated['already_cleared'] and sum(repeated['counts'].values()) == 0
    assert state(engine) == after
    planned = live.execute(engine, printed, **ids)
    assert state(engine) == after
    for field, count in dict(departments=33, cards=61, indicators=256, activities=285, economic_values=1300).items():
        assert planned['counts'][field] == count
    assert planned['skipped'][0]['name'] == live.SKIPPED
    written = live.execute(engine, printed, apply=True, **ids)
    assert not written['failed']
    assert written['counts'] == planned['counts']
    after_load = state(engine)
    repeat_plan = live.execute(engine, printed, resume=True, **ids)
    assert sum(repeat_plan['counts'].values()) == 0
    assert state(engine) == after_load
    with pytest.raises(live.Refusal, match='first_load_department'):
        clear.execute(engine, apply=True, **ids)
    assert state(engine) == after_load


@pytest.mark.postgres
@pytest.mark.parametrize('apply', [False, True])
@pytest.mark.parametrize('guard, message', [
    ('card', 'rapor kartı'), ('economic', 'ekonomik değer'), ('cost', 'personel/SGK'),
    ('publication', 'yayın'), ('submission', 'taslak'), ('audit', 'denetim kaydı'),
    ('deleted_audit', 'denetim kaydı'), ('marker', 'first_load_department'),
    ('untraced', 'izlenemiyor'), ('value', 'izlenemiyor'), ('scope', 'oluşturulma izi'),
    ('event', 'oluşturulma izi'), ('batch', 'envanteri'), ('program', 'program satırı'),
    ('identity', 'izlenemiyor'), ('actor', 'etkin Strateji'), ('organization', 'Tek kurum'),
    ('head', 'şema'), ('template', 'doğrulanmış'),
    ('personnel_amount', 'personel/SGK'), ('personnel_extra', 'personel/SGK'),
    ('personnel_missing', 'personel/SGK'), ('personnel_category', 'kategori'),
    ('personnel_raw', 'personel/SGK'), ('personnel_state', 'personel/SGK'),
    ('personnel_audit', 'denetim kaydı'), ('department_audit', 'denetim kaydı'),
    ('snapshot_name', 'snapshot')])
def test_refusals_preserve_every_row_and_sequence(target, guard, message, apply):
    engine, ids, extra = target
    pid, did, spid = extra['period_id'], extra['department_id'], extra['subprogram_id']
    with Session(engine) as db:
        ind = db.scalar(select(m.Indicator).where(m.Indicator.period_id == pid))
        if guard == 'card':
            db.add(m.ReportCard(period_id=pid, department_id=did, subprogram_id=spid))
        elif guard == 'economic':
            db.add(m.EconomicValue(period_id=pid, department_id=did, year=2027,
                value_kind='budget', category='personnel', program_group='service', funding_type='inside'))
        elif guard == 'cost':
            db.add(m.DepartmentCostValue(period_id=pid, department_id=did, year=2030, value_kind='budget'))
        elif guard.startswith('personnel_') or guard == 'department_audit':
            cost = db.scalar(select(m.DepartmentCostValue).where(
                m.DepartmentCostValue.period_id == pid, m.DepartmentCostValue.department_id == did,
                m.DepartmentCostValue.year == 2027))
            if guard == 'personnel_amount':
                cost.amount += 1
            elif guard == 'personnel_extra':
                db.add(m.DepartmentCostValue(period_id=pid, department_id=did, year=2030,
                    value_kind='forecast', category='personnel_sgk', amount=100))
            elif guard == 'personnel_missing':
                db.delete(cost)
            elif guard == 'personnel_category':
                cost.category = 'other'
            elif guard == 'personnel_raw':
                cost.raw_text = 'Sonradan değiştirilmiş'
            elif guard == 'personnel_state':
                cost.state = 'needs_review'
            else:
                db.add(m.AuditLog(action='personnel_cost_update' if guard == 'personnel_audit' else 'pp_data_change',
                    entity_type='department', entity_id=did, details='period_id=1',
                    created_at=datetime(2026, 10, 20)))
        elif guard == 'snapshot_name':
            batch = db.get(m.ImportBatch, 10)
            snapshot = json.loads(batch.snapshot_json)
            snapshot['departments'][0]['department_name'] = 'Değişmiş müdürlük kimliği'
            batch.snapshot_json = json.dumps(snapshot)
        elif guard == 'publication':
            db.add(m.Publication(period_id=pid, version=1, snapshot_json='{}', sha256='x', created_by=ids['actor_id']))
        elif guard == 'submission':
            db.scalar(select(m.Submission).where(m.Submission.period_id == pid)).status = 'submitted'
        elif guard in {'audit', 'deleted_audit'}:
            db.add(m.AuditLog(action='indicator_update', entity_type='indicator',
                entity_id=ind.id if guard == 'audit' else 99999, created_at=datetime(2026, 10, 20)))
        elif guard == 'marker':
            db.add(m.AuditLog(action=live.MARKER, entity_type='import_batch', entity_id=10))
        elif guard == 'untraced':
            ind.name = 'Plan dışı elle yazılmış gösterge'
        elif guard == 'value':
            db.scalar(select(m.IndicatorValue).where(m.IndicatorValue.indicator_id == ind.id)).value = 999
        elif guard == 'identity':
            identity = m.IndicatorIdentity(indicator_id='reserved', organization_id=ids['organization_id'])
            db.add(identity)
            db.flush()
            ind.persistent_indicator_id = identity.indicator_id
        elif guard == 'scope':
            db.add(m.DepartmentScope(period_id=pid, department_id=did))
        elif guard == 'event':
            sub = db.scalar(select(m.Submission).where(m.Submission.period_id == pid,
                                                       m.Submission.department_id == did))
            db.add(m.SubmissionEvent(period_id=pid, department_id=did, submission_id=sub.id, event_type='draft'))
        elif guard == 'batch':
            db.get(m.ImportBatch, 3).status = 'applied'
        elif guard == 'program':
            db.add(m.Program(period_id=pid, name='Plan dışı program'))
        elif guard == 'actor':
            db.get(m.User, ids['actor_id']).is_active = False
        elif guard == 'organization':
            db.add(m.Organization(name='İkinci kurum'))
        elif guard == 'head':
            db.execute(text("UPDATE alembic_version SET version_num='other'"))
        elif guard == 'template':
            db.get(m.ReportingPeriod, pid).template_status = 'pending'
        db.commit()
    before = state(engine)
    with pytest.raises(live.Refusal, match=message):
        clear.execute(engine, apply=apply, **ids)
    assert state(engine) == before


@pytest.mark.postgres
def test_lock_and_transaction_rollback(target, monkeypatch):
    from sqlalchemy import event
    engine, ids, _ = target
    before = state(engine)
    with engine.connect() as conn:
        conn.execute(text('SELECT pg_advisory_lock(:key)'), {'key': live.LOCK})
        conn.commit()
        try:
            with pytest.raises(live.Refusal, match='Başka ilk yükleme'):
                clear.execute(engine, apply=True, **ids)
        finally:
            conn.execute(text('SELECT pg_advisory_unlock(:key)'), {'key': live.LOCK})
            conn.commit()
    assert state(engine) == before
    def fail(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith('DELETE FROM activities'):
            raise RuntimeError('simulated mid-transaction failure')
    event.listen(engine, 'before_cursor_execute', fail)
    try:
        with pytest.raises(RuntimeError):
            clear.execute(engine, apply=True, **ids)
    finally:
        event.remove(engine, 'before_cursor_execute', fail)
    assert state(engine) == before


@pytest.mark.postgres
def test_cli_plan_is_read_only_and_secret_free(target, monkeypatch, capsys):
    engine, ids, _ = target
    monkeypatch.setenv(live.TARGET_ENV, engine.url.set(query={}).render_as_string(hide_password=False))
    before = state(engine)
    assert live.main(['--clear-preprint', '--organization-id', str(ids['organization_id']),
                      '--actor-id', str(ids['actor_id'])]) == 0
    assert state(engine) == before
    out = capsys.readouterr().out
    assert 'PLAN: Hedefe 0 satır yazıldı.' in out and 'Temizle:' in out
    assert engine.url.render_as_string(hide_password=False) not in out
    result = json.loads('{' + out.split('\n{', 1)[1])
    assert result['counts']['indicators'] == 33


@pytest.mark.parametrize('confirmation', ['', 'yes', live.BOOK_SHA256[:12]])
def test_clear_requires_separate_confirmation(tmp_path, monkeypatch, capsys, confirmation):
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@localhost/never_connect')
    monkeypatch.setattr(live, 'verify_book', lambda _: {})
    monkeypatch.setattr(live, 'verify_backup', lambda _: None)
    monkeypatch.setattr('builtins.input', lambda _: confirmation)
    assert live.main(['--clear-preprint', '--apply', '--backup', str(tmp_path / 'unused.dump'),
                      '--organization-id', '1', '--actor-id', '1']) == 1
    assert 'Temizleme onayı uyuşmuyor' in capsys.readouterr().err


def test_rehearsal_source_integrity_and_local_only(monkeypatch, tmp_path):
    from scripts import rehearse_clear_preprint_2027 as rehearsal
    from scripts.first_load_dryrun import local_test_url
    dump = tmp_path / 'synthetic.dump'
    dump.write_bytes(b'PGDMP-synthetic-source-integrity-test')
    manifest = dict(utc_timestamp='2026-10-20T12:00:00+00:00',
                    file_name=dump.name, file_size_bytes=dump.stat().st_size,
                    sha256=hashlib.sha256(dump.read_bytes()).hexdigest(),
                    alembic_version={'version_num': [live.HEAD]},
                    public_table_row_counts={'organizations': 1})
    dump.with_suffix('.manifest.json').write_text(json.dumps(manifest))
    monkeypatch.setattr(rehearsal, 'require_fresh_backup', lambda _: None)
    assert rehearsal.source_backup(dump) == manifest
    dump.write_bytes(b'PGDMP-tampered')
    with pytest.raises(live.Refusal, match='Yedek doğrulanamadı'):
        rehearsal.source_backup(dump)
    for raw in ('postgresql://unused@remote.example/db',
                'postgresql://unused@localhost/db?hostaddr=remote.example'):
        monkeypatch.setenv('CIVENSA_TEST_POSTGRES_URL', raw)
        with pytest.raises(ValueError):
            local_test_url()


def test_private_rehearsal_child_diagnostics_are_suppressed(monkeypatch, capsys):
    from scripts import rehearse_clear_preprint_2027 as rehearsal
    def child(command, **kwargs):
        import subprocess
        assert kwargs['stdout'] is subprocess.DEVNULL
        assert kwargs['stderr'] is subprocess.DEVNULL
        return subprocess.CompletedProcess(command, 1)
    monkeypatch.setattr(rehearsal.subprocess, 'run', child)
    with pytest.raises(live.Refusal):
        rehearsal.private(['pg_restore', 'sentinel-private-path'], {})
    assert 'sentinel-private-path' not in str(capsys.readouterr())


def test_runbook_blocks_are_independent_bash():
    import re
    import subprocess
    blocks = re.findall(r'```bash\n(.*?)```', (live.ROOT / 'docs/first-load/live-runbook.md').read_text(), re.S)
    assert len(blocks) >= 9
    for block in blocks:
        assert block.startswith("bash <<'BASH'\n")
        result = subprocess.run(['bash', '-n'], input=block, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        if 'CIVENSA_FIRST_LOAD_DATABASE_URL' in block and 'export CIVENSA_FIRST_LOAD_DATABASE_URL' in block:
            assert "read -r -s -p " in block and '</dev/tty' in block
            assert "trap 'unset CIVENSA_FIRST_LOAD_DATABASE_URL' EXIT" in block


@pytest.mark.postgres
def test_proven_2026_edit_is_preserved_and_retained_state_cannot_drift(target, printed):
    engine, ids, extra = target
    with Session(engine) as db:
        db.add_all([m.AuditLog(action='indicator_update', entity_type='indicator',
                              entity_id=extra['old_indicator_id'], created_at=datetime(2026, 10, 20))])
        db.commit()
    clear.execute(engine, apply=True, **ids)
    with Session(engine) as db:
        db.get(m.ImportBatch, 3).payload_json = '{"changed":true}'
        db.commit()
    before = state(engine)
    with pytest.raises(live.Refusal, match='denetim izi değişmiş'):
        live.execute(engine, printed, **ids)
    assert state(engine) == before


@pytest.mark.postgres
def test_earlier_import_catalogue_is_kept_and_late_reapply_audit_is_refused(target):
    engine, ids, extra = target
    with Session(engine) as db:
        batch = db.get(m.ImportBatch, 4)
        payload = json.loads(batch.payload_json)
        for dept in payload['departments']:
            for block in dept['blocks']:
                block['program'] = 'Önceki paket programı'
                block['subprogram'] = 'Önceki paket alt programı'
        batch.payload_json = json.dumps(payload, ensure_ascii=False)
        program = m.Program(period_id=extra['period_id'], name='Önceki paket programı')
        db.add(program)
        db.flush()
        sp = m.SubProgram(period_id=extra['period_id'], program_id=program.id,
                          name='Önceki paket alt programı')
        db.add(sp)
        db.commit()
        saved_sp = sp.id
    before = state(engine)
    clear.execute(engine, **ids)
    assert state(engine) == before
    with Session(engine) as db:
        db.add(m.AuditLog(action='data_import_apply', entity_type='import_batch', entity_id=10,
                         created_at=datetime(2026, 10, 20)))
        db.commit()
    before = state(engine)
    with pytest.raises(live.Refusal, match='denetim kaydı'):
        clear.execute(engine, apply=True, **ids)
    assert state(engine) == before
    with Session(engine) as db:
        assert db.get(m.SubProgram, saved_sp).name == 'Önceki paket alt programı'


@pytest.mark.postgres
def test_backup_freshness_is_rechecked_after_guards_before_first_delete(target):
    engine, ids, _ = target
    before = state(engine)
    calls = []
    def expired():
        calls.append('checked')
        raise live.Refusal('Yedek süresi doldu')
    with pytest.raises(live.Refusal, match='Yedek süresi doldu'):
        clear.execute(engine, apply=True, before_write=expired, **ids)
    assert calls == ['checked']
    assert state(engine) == before


def test_rehearsal_report_write_failure_does_not_expose_paths(monkeypatch, tmp_path, capsys):
    from scripts import rehearse_clear_preprint_2027 as rehearsal
    monkeypatch.setattr(rehearsal, 'rehearse', lambda *args: None)
    out = tmp_path / 'private-sentinel-connection' / 'counts.json'
    assert rehearsal.main(['--backup', str(tmp_path / 'source.dump'),
                           '--out', str(out), '--organization-id', '1', '--actor-id', '1']) == 1
    captured = capsys.readouterr()
    assert 'Sayım raporu yazılamadı' in captured.err
    assert 'private-sentinel-connection' not in captured.out + captured.err
    assert 'Traceback' not in captured.out + captured.err


def test_restore_selects_database_explicitly_and_credentials_stay_in_environment(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from sqlalchemy.engine import make_url
    from scripts import rehearse_clear_preprint_2027 as rehearsal
    engine = SimpleNamespace(url=make_url('postgresql+psycopg://local_user:sentinel_private_password@127.0.0.1:5432/generated_copy'))
    calls = []
    monkeypatch.setattr(rehearsal, 'private', lambda command, env: calls.append((command, env)))
    rehearsal.restore(engine, tmp_path / 'source.dump')
    command, env = calls[0]
    assert command[command.index('--dbname') + 1] == 'generated_copy'
    assert 'sentinel_private_password' not in repr(command)
    assert env['PGDATABASE'] == 'generated_copy'
    assert env['PGHOST'] == env['PGHOSTADDR'] == '127.0.0.1'
    assert env['PGPORT'] == '5432'
    assert env['PGUSER'] == 'local_user'
    assert env['PGPASSWORD'] == 'sentinel_private_password'



def test_personnel_seen_loop_preserves_first_eligible_and_null_zero_distinction():
    rows = [dict(year=2027, kind='budget', amount=None),
            dict(year=2027, kind='budget', amount='0', raw_text='0'),
            dict(year=2027, kind='budget', amount='999', raw_text='999'),
            dict(year=2028, kind='forecast', amount=None, state='needs_review', raw_text='boş'),
            dict(year=2028, kind='forecast', amount='7'),
            dict(year=2029, kind='forecast', amount=None, state='not_applicable', raw_text='-')]
    assert clear.source_personnel(rows) == clear.Counter([
        (2027, 'budget', 'personnel_sgk', '0', '0', 'verified'),
        (2028, 'forecast', 'personnel_sgk', None, 'boş', 'needs_review'),
        (2029, 'forecast', 'personnel_sgk', None, '-', 'not_applicable')])
    assert clear.source_personnel([dict(year=2027, kind='budget', amount='1')]) != (
        clear.source_personnel([dict(year=2027, kind='budget', amount='1.01')]))


@pytest.mark.postgres
def test_legacy_payload_defaults_are_exact_and_batches_remain_unchanged(target):
    engine, ids, extra = target
    with Session(engine) as db:
        for batch in db.scalars(select(m.ImportBatch)):
            payload = json.loads(batch.payload_json)
            for department in payload['departments']:
                for block in department['blocks']:
                    for indicator in block['indicators']:
                        for row in indicator['values']:
                            row.pop('state', None)
                            row.pop('raw_text', None)
                for activity in department['activities']:
                    for row in activity['costs']:
                        if row.get('state', 'verified') == 'verified':
                            row.pop('state', None)
                            row.pop('raw_text', None)
                for row in department['personnel']:
                    if row.get('state', 'verified') == 'verified':
                        row.pop('state', None)
                        row.pop('raw_text', None)
            batch.payload_json = json.dumps(payload, ensure_ascii=False)
            snapshot = json.loads(batch.snapshot_json)
            snapshot.pop('created_department_ids', None)
            batch.snapshot_json = json.dumps(snapshot)
        for row in db.scalars(select(m.IndicatorValue).join(m.Indicator).where(
                m.Indicator.period_id == extra['period_id'])):
            row.raw_text = '2.5'
        for row in db.scalars(select(m.ActivityCostValue).join(m.Activity).where(
                m.Activity.period_id == extra['period_id'], m.ActivityCostValue.state == 'verified')):
            row.raw_text = '10.25'
        for row in db.scalars(select(m.DepartmentCostValue).where(
                m.DepartmentCostValue.period_id == extra['period_id'], m.DepartmentCostValue.state == 'verified')):
            row.raw_text = ''
        db.commit()
    before = state(engine)
    plan = clear.execute(engine, **ids)
    assert plan['counts']['department_cost_values'] == 93
    assert state(engine) == before
    with Session(engine) as db:
        batches = {b.id: clear.batch_state(b) for b in db.scalars(select(m.ImportBatch))}
    clear.execute(engine, apply=True, **ids)
    with Session(engine) as db:
        assert {b.id: clear.batch_state(b) for b in db.scalars(select(m.ImportBatch))} == batches



@pytest.mark.postgres
def test_importer_resolved_name_match_still_requires_snapshot_identity_and_exact_content(target):
    engine, ids, _ = target
    from app.import_service import build_department_plan
    with Session(engine) as db:
        for batch in db.scalars(select(m.ImportBatch)):
            payload = json.loads(batch.payload_json)
            payload['departments'][0]['name'] += 'ü'
            batch.payload_json = json.dumps(payload, ensure_ascii=False)
        plan = build_department_plan(db, payload)
        assert plan['mappings'][0]['action'] == 'match'
        assert plan['mappings'][0]['confidence'] < 1
        db.commit()
    before = state(engine)
    planned = clear.execute(engine, **ids)
    assert planned['counts']['department_cost_values'] == 93
    assert state(engine) == before
    assert clear.execute(engine, apply=True, **ids)['counts'] == planned['counts']



@pytest.mark.postgres
def test_preview_and_reverted_archives_trace_retained_catalogue_only(target):
    engine, ids, extra = target
    with Session(engine) as db:
        for bid in (3, 6):
            batch = db.get(m.ImportBatch, bid)
            payload = json.loads(batch.payload_json)
            for department in payload['departments']:
                for block in department['blocks']:
                    block['program'] = f'Korunan arşiv programı {bid}'
                    block['subprogram'] = f'Korunan arşiv alt programı {bid}'
            batch.payload_json = json.dumps(payload, ensure_ascii=False)
            program = m.Program(period_id=extra['period_id'], name=f'Korunan arşiv programı {bid}')
            db.add(program)
            db.flush()
            db.add(m.SubProgram(period_id=extra['period_id'], program_id=program.id,
                name=f'Korunan arşiv alt programı {bid}'))
        db.commit()
    before = state(engine)
    assert clear.execute(engine, **ids)['counts']['department_cost_values'] == 93
    assert state(engine) == before
    clear.execute(engine, apply=True, **ids)
    with Session(engine) as db:
        assert len(db.scalars(select(m.Program).where(m.Program.period_id == extra['period_id'])).all()) == 3



@pytest.mark.postgres
def test_snapshot_preexisting_catalogue_is_preserved_without_claiming_content_ownership(target):
    engine, ids, extra = target
    with Session(engine) as db:
        program = m.Program(period_id=extra['period_id'], name='Paket öncesi sabit katalog')
        db.add(program)
        db.flush()
        sp = m.SubProgram(period_id=extra['period_id'], program_id=program.id, name='Paket öncesi sabit alt program')
        db.add(sp)
        db.flush()
        batch = db.get(m.ImportBatch, 4)
        snapshot = json.loads(batch.snapshot_json)
        snapshot.update(preexisting_program_ids=[program.id], preexisting_subprogram_ids=[sp.id])
        batch.snapshot_json = json.dumps(snapshot)
        db.commit()
    before = state(engine)
    assert clear.execute(engine, **ids)['counts']['department_cost_values'] == 93
    assert state(engine) == before
    clear.execute(engine, apply=True, **ids)
    after = state(engine)
    for table in ('programs', 'subprograms'):
        assert after[0][table] == before[0][table]



@pytest.mark.postgres
def test_pre_october_archives_replay_recorded_float_migrations_without_ignoring_metadata(target):
    engine, ids, extra = target
    with Session(engine) as db:
        for batch in db.scalars(select(m.ImportBatch)):
            payload = json.loads(batch.payload_json)
            for department in payload['departments']:
                for block in department['blocks']:
                    for indicator in block['indicators']:
                        for row in indicator['values']:
                            row.pop('state', None); row.pop('raw_text', None)
                for activity in department['activities']:
                    for row in activity['costs']:
                        if row['amount'] is None:
                            row['amount'] = '20.25'
                        row.pop('state', None); row.pop('raw_text', None)
                for row in department['personnel']:
                    if row['amount'] is None:
                        row['amount'] = '300.25'
                    row.pop('state', None); row.pop('raw_text', None)
            batch.payload_json = json.dumps(payload, ensure_ascii=False)
        for row in db.scalars(select(m.IndicatorValue).join(m.Indicator).where(
                m.Indicator.period_id == extra['period_id'])):
            row.raw_text = '2.5'
        for row in db.scalars(select(m.ActivityCostValue).join(m.Activity).where(
                m.Activity.period_id == extra['period_id'])):
            row.amount = '10.25' if row.year == 2027 else '20.25'
            row.raw_text = '10.25' if row.year == 2027 else '20.25'
            row.state = 'verified'
        for row in db.scalars(select(m.DepartmentCostValue).where(
                m.DepartmentCostValue.period_id == extra['period_id'])):
            row.raw_text = {2027: '100.25', 2028: '200.002', 2029: '300.25'}[row.year]
            row.state = 'needs_review' if row.year == 2028 else 'verified'
            if row.year == 2029:
                row.amount = '300.25'
        db.commit()
    before = state(engine)
    assert clear.execute(engine, **ids)['counts']['department_cost_values'] == 93
    assert state(engine) == before
    with Session(engine) as db:
        cost = db.scalar(select(m.DepartmentCostValue).where(
            m.DepartmentCostValue.period_id == extra['period_id']))
        cost.raw_text = 'Aynı sayı, sonradan değiştirilmiş metin'
        db.commit()
    changed = state(engine)
    with pytest.raises(live.Refusal, match='raw_text'):
        clear.execute(engine, apply=True, **ids)
    assert state(engine) == changed



@pytest.mark.postgres
def test_rehearsal_retention_fingerprint_detects_2026_damage(target):
    from scripts.rehearse_clear_preprint_2027 import retained_rows
    engine, ids, extra = target
    before = retained_rows(engine)
    clear.execute(engine, apply=True, **ids)
    after = retained_rows(engine)
    assert before['rows'] == after['rows']
    assert before['batches'] == after['batches']
    assert len(after['audit']) == len(before['audit']) + 1
    assert all(after['audit'].get(k) == v for k, v in before['audit'].items())
    with Session(engine) as db:
        db.get(m.DepartmentCostValue, extra['old_cost_id']).amount = 78
        db.commit()
    assert retained_rows(engine)['rows'] != after['rows']
