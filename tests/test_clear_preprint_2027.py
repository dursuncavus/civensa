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
from scripts.first_load_dryrun import disposable_database, local_test_url
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
    with disposable_database(local_test_url()) as engine:
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
                                 values=[dict(year=2027, kind='target', value='2.5', raw_text='2,5')])
                activity = dict(name=f'Taslak faaliyet {index}', explanation='Kaynak açıklama',
                                costs=[dict(year=2027, kind='budget', amount='10.25',
                                            funding_type='total', raw_text='10,25'),
                                       dict(year=2028, kind='forecast', amount=None,
                                            funding_type='total', raw_text='', state='needs_review')])
                payload['departments'].append(dict(name=dept.name, blocks=[dict(
                    program=program.name, subprogram=sp.name, budget_year=2027, indicators=[indicator])],
                    activities=[activity], personnel=[]))
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
            snapshot = dict(departments=[{'department_id': d.id} for d in departments],
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
                         subprogram_id=sp.id, old_indicator_id=ind26.id, old_activity_id=act26.id)
        yield engine, ids, extra


@pytest.mark.postgres
def test_clear_chain_and_preserved_rows(target, printed):
    engine, ids, extra = target
    before = state(engine)
    plan = clear.execute(engine, **ids)
    assert state(engine) == before
    assert len(plan['departments']) == 33
    assert plan['counts'] == dict(indicators=33, indicator_values=33, activities=33,
        activity_cost_values=66, submissions=33, submission_events=0,
        activity_catalogue_links=0, department_scopes=0, subprogram_scopes=0)
    applied = clear.execute(engine, apply=True, **ids)
    assert applied['counts'] == plan['counts']
    with Session(engine) as db:
        assert db.get(m.Indicator, extra['old_indicator_id']).name == '2026 kalır'
        assert db.get(m.Activity, extra['old_activity_id']).name == '2026 kalır'
        assert len(db.scalars(select(m.User)).all()) == 1
        assert len(db.scalars(select(m.Department)).all()) == 33
        assert len(db.scalars(select(m.ReportingPeriod)).all()) == 2
        assert len(db.scalars(select(m.Program)).all()) == 2
        assert len(db.scalars(select(m.ImportBatch)).all()) == 8
        assert set(db.scalars(select(m.ImportBatch.status))) == {'superseded'}
        assert len(db.scalars(select(m.AuditLog)).all()) == 2
        receipt = db.scalar(select(m.AuditLog).where(m.AuditLog.action == clear.ACTION))
        assert json.loads(receipt.details)['counts'] == plan['counts']
    after = state(engine)
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
    ('card', 'rapor kartı'), ('economic', 'ekonomik değer'), ('cost', 'müdürlük maliyet'),
    ('publication', 'yayın'), ('submission', 'taslak'), ('audit', 'denetim kaydı'),
    ('deleted_audit', 'denetim kaydı'), ('marker', 'first_load_department'),
    ('untraced', 'izlenemiyor'), ('value', 'izlenemiyor'), ('scope', 'oluşturulma izi'),
    ('event', 'oluşturulma izi'), ('batch', 'envanteri'), ('program', 'program satırı'),
    ('identity', 'izlenemiyor'), ('actor', 'etkin Strateji'), ('organization', 'Tek kurum'),
    ('head', 'şema'), ('template', 'doğrulanmış')])
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
            db.add(m.DepartmentCostValue(period_id=pid, department_id=did, year=2027, value_kind='budget'))
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
