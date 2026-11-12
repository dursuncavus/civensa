"""CIV-158: approved source, real migration schema and writes only in disposable local PostgreSQL."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from scripts import first_load_live as live
from scripts.first_load_dryrun import local_test_url
from tests.first_load_checkpoint import disposable_first_load_database
from app.models import (Activity, AuditLog, Department, EconomicValue, ImportBatch,
                        Indicator, IndicatorValue, Organization, ReportingPeriod, Submission, User)


@pytest.fixture(scope='module')
def printed():
    return live.verify_book(live.BOOK)


@pytest.fixture
def target():
    with disposable_first_load_database(local_test_url()) as engine:
        with Session(engine) as db:
            org = Organization(name='Yerel ilk yükleme testi')
            actor = User(email='strategy@example.invalid', full_name='Strateji test',
                         role='strategy', password_hash='unused')
            db.add_all([org, actor])
            db.commit()
            ids = dict(organization_id=org.id, actor_id=actor.id)
        yield engine, ids


def backup_files(tmp_path, *, age=0):
    dump = tmp_path / 'civensa-neon-test.dump'
    dump.write_bytes(b'PGDMP-disposable-guard-fixture')
    manifest = dict(utc_timestamp=(datetime.now(timezone.utc) - timedelta(seconds=age)).isoformat(),
                    file_name=dump.name, file_size_bytes=dump.stat().st_size,
                    sha256=hashlib.sha256(dump.read_bytes()).hexdigest(),
                    alembic_version={'version_num': [live.HEAD]}, public_table_row_counts={'organizations': 1})
    dump.with_suffix('.manifest.json').write_text(json.dumps(manifest))
    return dump, manifest


class TtyStub:
    def __init__(self, response=''):
        self.input = io.StringIO(response)
        self.output = io.StringIO()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass

    def write(self, text):
        return self.output.write(text)

    def flush(self):
        self.output.flush()

    def readline(self):
        return self.input.readline()


def state(engine):
    """Every public table and sequence: plan must not even advance sequences."""
    with engine.connect() as conn:
        tables = list(conn.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")))
        rows = {table: conn.exec_driver_sql(f'SELECT count(*) FROM public."{table}"').scalar() for table in tables}
        sequences = list(conn.execute(text("SELECT sequencename, last_value FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename")))
        return rows, sequences


@pytest.mark.postgres
def test_printed_plan_apply_repeat_resume_preserves_corrections(target, printed):
    engine, ids = target
    before = state(engine)
    plan = live.execute(engine, printed, **ids)
    assert state(engine) == before
    assert dict(plan['counts']) == dict(departments=34, created_departments=34, cards=64,
                                       indicators=263, activities=290, economic_values=1340)
    assert plan['skipped'] == []
    applied = live.execute(engine, printed, apply=True, **ids)
    assert not applied['failed']
    assert applied['counts'] == plan['counts']
    assert applied['departments'] == plan['departments']
    assert len(applied['validation']) == 34
    assert any(v['errors'] for v in applied['validation'])
    business_validation = next(v for v in applied['validation']
                               if v['name'] == 'İşletme ve İştirakler Müdürlüğü')
    assert business_validation['errors']  # D-324: diagnostic, still saved as draft.
    after = state(engine)
    with pytest.raises(live.Refusal, match='2027 PP verisi zaten var'):
        live.execute(engine, printed, apply=True, **ids)
    assert state(engine) == after
    with Session(engine) as db:
        assert set(db.scalars(select(Submission.status))) == {'draft'}
        assert db.scalar(select(Department.id).where(Department.name == 'İşletme ve İştirakler Müdürlüğü')) is not None
        review = db.scalar(select(IndicatorValue).where(IndicatorValue.state == 'needs_review'))
        assert review is not None
        review_id = review.id
        # A real owner correction is preserved verbatim during resume.
        indicator = db.get(Indicator, review.indicator_id)
        indicator.explanation = 'Strateji tarafından denetimle düzeltilen açıklama'
        db.commit()
        saved = (indicator.id, indicator.explanation)
    after_correction = state(engine)
    resumed = live.execute(engine, printed, apply=True, resume=True, **ids)
    assert sum(resumed['counts'].values()) == 0
    assert len(resumed['skipped']) == 34
    assert all(d['action'] == 'skip' for d in resumed['departments'])
    assert state(engine) == after_correction
    with Session(engine) as db:
        assert db.get(Indicator, saved[0]).explanation == saved[1]
        assert len(list(db.scalars(select(AuditLog).where(AuditLog.action == live.MARKER)))) == 34
        assert db.scalar(select(IndicatorValue).where(IndicatorValue.id == review_id)).state == 'needs_review'


@pytest.mark.postgres
def test_cli_plan_on_c086_schema_writes_nothing(target, monkeypatch, capsys):
    engine, ids = target
    monkeypatch.setenv(live.TARGET_ENV, engine.url.set(query={}).render_as_string(hide_password=False))
    before = state(engine)
    assert live.main(['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id'])]) == 0
    assert state(engine) == before
    output = capsys.readouterr().out
    assert 'PLAN: Hedefe 0 satır yazıldı.' in output
    assert 'İşletme ve İştirakler Müdürlüğü' in output
    assert '1340' in output
    assert engine.url.render_as_string(hide_password=False) not in output


@pytest.mark.postgres
def test_plan_lists_department_actions_without_writes(target, printed, monkeypatch, capsys):
    engine, ids = target
    data = deepcopy(printed)
    data['departments'] = data['departments'][:4] + [data['departments'][-1]]
    sources = data['departments']
    with Session(engine) as db:
        exact = [Department(organization_id=ids['organization_id'], name=sources[i]['name']) for i in (0, 2)]
        renamed = Department(organization_id=ids['organization_id'], name=sources[1]['name'] + ' Yeni')
        db.add_all([*exact, renamed])
        db.commit()
        exact_ids = [d.id for d in exact]
    before = state(engine)
    plan = live.execute(engine, data, **ids)
    assert state(engine) == before
    actions = plan['departments']
    assert len(actions) == len(sources)
    assert actions[0] == dict(source_name=sources[0]['name'], action='match',
                             department_id=exact_ids[0], name=sources[0]['name'])
    assert actions[1]['source_name'] == sources[1]['name']
    assert actions[1]['action'] == 'skip'
    assert 'Tekil kesin müdürlük eşleşmesi yok' in actions[1]['reason']
    assert actions[2] == dict(source_name=sources[2]['name'], action='match',
                             department_id=exact_ids[1], name=sources[2]['name'])
    assert actions[3] == dict(source_name=sources[3]['name'], action='create', name=sources[3]['name'])
    assert sources[4]['name'] == 'İşletme ve İştirakler Müdürlüğü'
    assert actions[4] == dict(source_name=sources[4]['name'], action='create', name=sources[4]['name'])
    monkeypatch.setattr(live, 'verify_book', lambda path: data)
    monkeypatch.setenv(live.TARGET_ENV, engine.url.set(query={}).render_as_string(hide_password=False))
    assert live.main(['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id'])]) == 0
    assert state(engine) == before
    text_output, json_output = capsys.readouterr().out.split('\n{', 1)
    assert f"Eşleştir: {sources[0]['name']} → {sources[0]['name']} (müdürlük #{exact_ids[0]})" in text_output
    assert f"Oluştur: {sources[3]['name']} → {sources[3]['name']}" in text_output
    assert f"Atla: {sources[1]['name']} · " in text_output
    assert f"Oluştur: {sources[4]['name']} → {sources[4]['name']}" in text_output
    assert json.loads('{' + json_output.split('\nÖZET\n', 1)[0])['departments'] == actions


@pytest.mark.postgres
def test_cli_apply_and_needs_attention_after_real_department_edit(target, printed, tmp_path, monkeypatch):
    import asyncio
    from app.main import department_progress_overview, save_indicator
    engine, ids = target
    data = deepcopy(printed)
    data['departments'] = data['departments'][:1]  # Sağlık: validation errors and review cells.
    monkeypatch.setattr(live, 'verify_book', lambda path: data)
    monkeypatch.setenv(live.TARGET_ENV, engine.url.set(query={}).render_as_string(hide_password=False))
    monkeypatch.setattr(live, 'open_tty', lambda: TtyStub(live.BOOK_SHA256[:12] + '\n'))
    dump, _ = backup_files(tmp_path)
    assert live.main(['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id']),
                      '--apply', '--backup', str(dump)]) == 0
    with Session(engine) as db:
        period = db.scalar(select(ReportingPeriod))
        department = db.scalar(select(Department))
        user = User(email='department@example.invalid', full_name='Müdürlük test', role='department',
                    department_id=department.id, password_hash='unused')
        db.add(user)
        db.commit()
        assert db.scalar(select(Submission.status)) == 'draft'
        assert db.scalar(select(EconomicValue.id).where(EconomicValue.state == 'needs_review')) is not None
        review_states = list(db.execute(select(IndicatorValue.id, IndicatorValue.state).where(IndicatorValue.state == 'needs_review')))
        indicator = db.scalar(select(Indicator).where(Indicator.department_id == department.id))
        assert department_progress_overview(db, period)['rows'][0]['state'] == 'not_started'
        class Request:
            async def json(self):
                return {'explanation': 'Müdürlük tarafından kaydedilen açıklama'}
        # Exercise the existing save/audit path, never fabricate a department audit.
        assert asyncio.run(save_indicator(indicator.id, Request(), db, user))['ok']
        progress = department_progress_overview(db, period)['rows'][0]
        assert progress['state'] == 'needs_attention'
        assert progress['warning_count'] > 0
        assert list(db.execute(select(IndicatorValue.id, IndicatorValue.state).where(IndicatorValue.state == 'needs_review'))) == review_states


@pytest.mark.postgres
def test_concurrent_loader_guard(target, printed):
    engine, ids = target
    before = state(engine)
    with engine.connect() as connection:
        connection.execute(text('SELECT pg_advisory_lock(:key)'), {'key': live.LOCK})
        connection.commit()
        try:
            with pytest.raises(live.Refusal, match='Başka ilk yükleme'):
                live.execute(engine, printed, apply=True, **ids)
        finally:
            connection.execute(text('SELECT pg_advisory_unlock(:key)'), {'key': live.LOCK})
            connection.commit()
    assert state(engine) == before


@pytest.mark.postgres
@pytest.mark.parametrize('guard', ['head', 'old_head', 'multiple_heads', 'actor', 'inactive_actor', 'organization', 'period', 'template', 'unknown_data'])
def test_database_guards_refuse_without_writes(target, printed, guard):
    engine, ids = target
    with Session(engine) as db:
        if guard == 'head':
            db.execute(text("UPDATE alembic_version SET version_num='wrong_head'"))
        elif guard == 'old_head':
            db.execute(text("UPDATE alembic_version SET version_num='c048a1b2c3d4'"))
        elif guard == 'multiple_heads':
            db.execute(text("INSERT INTO alembic_version VALUES ('other_head')"))
        elif guard == 'actor':
            db.get(User, ids['actor_id']).role = 'department'
        elif guard == 'inactive_actor':
            db.get(User, ids['actor_id']).is_active = False
        elif guard == 'organization':
            ids['organization_id'] += 999
        else:
            p = ReportingPeriod(year=2027, status='published' if guard == 'period' else 'draft',
                                template_status='pending' if guard == 'template' else 'verified')
            db.add(p)
            if guard == 'unknown_data':
                from app.models import Program
                db.flush()
                db.add(Program(period_id=p.id, name='Önceden girilmiş veri'))
        db.commit()
    before = state(engine)
    with pytest.raises(live.Refusal):
        live.execute(engine, printed, apply=True, resume=True, **ids)
    assert state(engine) == before


@pytest.mark.postgres
def test_department_failure_rolls_back_alone_and_resume_retries_only_failure(target, printed, monkeypatch):
    engine, ids = target
    from app import first_load_service
    original = first_load_service.apply_first_load_batch
    data = deepcopy(printed)
    data['departments'] = data['departments'][:2]
    def fail_after_writes(db, batch, actor):
        result = original(db, batch, actor)
        if data['departments'][0]['name'] in batch.payload_json:
            raise ValueError('Yerel test: hizmet paketi reddetti')
        return result
    monkeypatch.setattr(first_load_service, 'apply_first_load_batch', fail_after_writes)
    result = live.execute(engine, data, apply=True, **ids)
    assert result['counts']['departments'] == 1
    assert [f['name'] for f in result['failed']] == [data['departments'][0]['name']]
    assert result['departments'][0] == dict(source_name=data['departments'][0]['name'], action='skip',
                                           reason=result['failed'][0]['reason'])
    with Session(engine) as db:
        assert db.scalar(select(Department.id).where(Department.name == data['departments'][0]['name'])) is None
        assert len(list(db.scalars(select(ImportBatch)))) == 1
        assert len(list(db.scalars(select(AuditLog).where(AuditLog.action == live.MARKER)))) == 1
    monkeypatch.setattr(first_load_service, 'apply_first_load_batch', original)
    retry = live.execute(engine, data, apply=True, resume=True, **ids)
    assert retry['counts']['departments'] == 1
    assert not retry['failed']
    with Session(engine) as db:
        assert len(list(db.scalars(select(ImportBatch)))) == 2


@pytest.mark.postgres
def test_locked_submission_is_skipped_and_existing_draft_remains_draft(target, printed):
    engine, ids = target
    data = deepcopy(printed)
    data['departments'] = data['departments'][:2]
    with Session(engine) as db:
        period = ReportingPeriod(year=2027, status='draft', template_status='verified')
        db.add(period)
        db.flush()
        for index, source in enumerate(data['departments']):
            department = Department(organization_id=ids['organization_id'], name=source['name'])
            db.add(department)
            db.flush()
            db.add(Submission(period_id=period.id, department_id=department.id,
                              status='approved' if index == 0 else 'returned'))
        db.commit()
    result = live.execute(engine, data, apply=True, **ids)
    assert len(result['failed']) == 1
    assert result['counts']['departments'] == 1
    with Session(engine) as db:
        assert list(db.scalars(select(Submission.status).order_by(Submission.id))) == ['approved', 'draft']


@pytest.mark.parametrize('damage', ['missing', 'manifest', 'stale', 'future', 'checksum', 'size', 'name', 'head', 'format'])
def test_backup_guard(tmp_path, damage):
    dump, manifest = backup_files(tmp_path)
    if damage == 'missing':
        dump.unlink()
    elif damage == 'manifest':
        dump.with_suffix('.manifest.json').unlink()
    elif damage in {'stale', 'future'}:
        manifest['utc_timestamp'] = (datetime.now(timezone.utc) + timedelta(minutes=1 if damage == 'future' else -61)).isoformat()
    elif damage == 'checksum':
        manifest['sha256'] = 'bad'
    elif damage == 'size':
        manifest['file_size_bytes'] += 1
    elif damage == 'name':
        manifest['file_name'] = 'other.dump'
    elif damage == 'head':
        manifest['alembic_version']['version_num'] = ['other_head']
    elif damage == 'format':
        dump.write_bytes(b'wrong-format')
        manifest.update(file_size_bytes=dump.stat().st_size, sha256=hashlib.sha256(dump.read_bytes()).hexdigest())
    if damage != 'manifest':
        dump.with_suffix('.manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(live.Refusal, match='Yedek doğrulanamadı'):
        live.verify_backup(dump)


def test_fresh_backup_and_book_checksum(tmp_path):
    dump, _ = backup_files(tmp_path)
    # ZIP tools may preserve an old file mtime; the recovery point is in the manifest.
    os.utime(dump, (0, 0))
    live.verify_backup(dump)
    wrong_book = tmp_path / 'book.idml'
    wrong_book.write_bytes(b'edited')
    with pytest.raises(live.Refusal, match='Kitap SHA256'):
        live.verify_book(wrong_book)


@pytest.mark.parametrize('url', ['', 'sqlite:///file.db', 'postgresql://secret@remote/db',
    'postgresql://secret@remote-pooler.example/db?sslmode=require',
    'postgresql://secret@localhost/db?host=remote', 'postgresql://secret@localhost/db?service=foo',
    'postgresql://secret@localhost/db?sslmode=disable', 'postgresql://[broken'])
def test_target_guard(monkeypatch, url):
    monkeypatch.setenv(live.TARGET_ENV, url)
    with pytest.raises(live.Refusal) as error:
        live.target_url()
    assert 'secret' not in str(error.value)


def test_neon_channel_binding_require_is_accepted(monkeypatch):
    monkeypatch.setenv(live.TARGET_ENV,
                      'postgresql://unused@neon.example/db?sslmode=require&channel_binding=require')
    assert dict(live.target_url().query) == dict(sslmode='require', channel_binding='require')


@pytest.mark.parametrize('query', ['channel_binding=disable', 'channel_binding=prefer', 'channel_binding=',
                                 'channel_binding=require&application_name=extra'])
def test_neon_channel_binding_other_values_and_extra_keys_are_refused(monkeypatch, query):
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@neon.example/db?sslmode=require&' + query)
    with pytest.raises(live.Refusal):
        live.target_url()


@pytest.mark.parametrize('confirmation', ['', 'incorrect', '261cd17fd0be', live.BOOK_SHA256])
def test_cli_apply_requires_typed_prefix_before_connection(tmp_path, monkeypatch, capsys, confirmation):
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@localhost/never_connect')
    monkeypatch.setattr(live, 'verify_book', lambda path: {})
    monkeypatch.setattr(live, 'open_tty', lambda: TtyStub(confirmation + '\n'))
    dump, _ = backup_files(tmp_path)
    assert live.main(['--organization-id', '1', '--actor-id', '1', '--apply', '--backup', str(dump)]) == 1
    assert 'SHA256 onayı uyuşmuyor' in capsys.readouterr().err


def test_cli_apply_requires_backup(monkeypatch, capsys):
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@localhost/never_connect')
    monkeypatch.setattr(live, 'verify_book', lambda path: {})
    assert live.main(['--organization-id', '1', '--actor-id', '1', '--apply']) == 1
    assert '--backup gerekli' in capsys.readouterr().err


def test_cli_does_not_fall_back_to_application_environment(monkeypatch, capsys):
    monkeypatch.delenv(live.TARGET_ENV, raising=False)
    assert live.main(['--organization-id', '1', '--actor-id', '1']) == 1
    assert live.TARGET_ENV in capsys.readouterr().err


def test_secret_cli_argument_is_rejected_without_echo(capsys):
    with pytest.raises(SystemExit):
        live.main(['--organization-id', '1', '--actor-id', '1', '--database-url', 'secret-connection'])
    assert 'secret-connection' not in capsys.readouterr().err


def test_live_pin_equals_current_migration_head():
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    script = ScriptDirectory.from_config(Config(str(live.ROOT / 'alembic.ini')))
    assert script.get_heads() == ['c219a1b2c3d4']
    assert script.get_heads() == [live.HEAD]


def test_approved_source_pin_and_old_book_refusal():
    assert live.BOOK.name == '2027-performans-programi_SONN_duzeltilmis.idml'
    assert live.BOOK_SHA256 == '66d9d692bd9c324f6d4f492eca4d75721f28c80e248a971a2a331adf1170bf6f'
    with pytest.raises(live.Refusal, match='Kitap SHA256'):
        live.verify_book(live.BOOK.with_name('2027-performans-programi_16102026_duzeltilmis 2.idml'))


def test_cli_refuses_old_book_before_connection(monkeypatch, capsys):
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@localhost/never_connect')
    def connection_forbidden(*args, **kwargs):
        pytest.fail('Old book must be refused before an engine is created')
    monkeypatch.setattr('sqlalchemy.create_engine', connection_forbidden)
    old_book = live.BOOK.with_name('2027-performans-programi_16102026_duzeltilmis 2.idml')
    assert live.main(['--organization-id', '1', '--actor-id', '1', '--book', str(old_book)]) == 1
    assert 'Kitap SHA256 uyuşmuyor' in capsys.readouterr().err


@pytest.mark.postgres
def test_tty_confirmation_prompt_not_on_stdout_and_wrong_refuses_zero_rows(target, printed, tmp_path, monkeypatch, capsys):
    import sys
    engine, ids = target
    data = deepcopy(printed)
    data['departments'] = data['departments'][:1]
    monkeypatch.setattr(live, 'verify_book', lambda path, **kw: data)
    monkeypatch.setenv(live.TARGET_ENV, engine.url.set(query={}).render_as_string(hide_password=False))
    monkeypatch.setattr(sys, 'stdin', io.StringIO(live.BOOK_SHA256[:12] + '\n'))
    dump, _ = backup_files(tmp_path)
    before = state(engine)

    wrong_tty = TtyStub('yanlis-onay\n')
    monkeypatch.setattr(live, 'open_tty', lambda: wrong_tty)
    assert live.main(['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id']),
                      '--apply', '--backup', str(dump)]) == 1
    assert state(engine) == before
    captured = capsys.readouterr()
    assert f'Yazma onayı: kitap SHA256 ilk 12 karakterini yazın ({live.BOOK_SHA256[:12]}): ' == wrong_tty.output.getvalue()
    assert 'Yazma onayı:' not in captured.out
    assert captured.out == ''
    assert 'Kitap SHA256 onayı uyuşmuyor; 0 satır yazıldı.' in captured.err

    eof_tty = TtyStub('')
    monkeypatch.setattr(live, 'open_tty', lambda: eof_tty)
    assert live.main(['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id']),
                      '--apply', '--backup', str(dump)]) == 1
    assert state(engine) == before
    captured = capsys.readouterr()
    assert 'Yazma onayı: ' in eof_tty.output.getvalue()
    assert 'Yazma onayı alınamadı; 0 satır yazıldı.' in captured.err

    ok_tty = TtyStub(live.BOOK_SHA256[:12] + '\n')
    monkeypatch.setattr(live, 'open_tty', lambda: ok_tty)
    assert live.main(['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id']),
                      '--apply', '--backup', str(dump)]) == 0
    captured = capsys.readouterr()
    assert f'Yazma onayı: kitap SHA256 ilk 12 karakterini yazın ({live.BOOK_SHA256[:12]}): ' == ok_tty.output.getvalue()
    assert 'Yazma onayı:' not in captured.out
    assert 'UYGULAMA SONUCU:' in captured.out


@pytest.mark.postgres
def test_no_tty_available_refuses_with_turkish_message_and_zero_rows(target, printed, tmp_path, monkeypatch, capsys):
    import sys
    engine, ids = target
    monkeypatch.setattr(live, 'verify_book', lambda path, **kw: printed)
    monkeypatch.setenv(live.TARGET_ENV, engine.url.set(query={}).render_as_string(hide_password=False))
    monkeypatch.setattr(sys, 'stdin', io.StringIO(live.BOOK_SHA256[:12] + '\n'))
    def raise_no_tty():
        raise OSError('no controlling terminal')
    monkeypatch.setattr(live, 'open_tty', raise_no_tty)
    dump, _ = backup_files(tmp_path)
    before = state(engine)
    assert live.main(['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id']),
                      '--apply', '--backup', str(dump)]) == 1
    assert state(engine) == before
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err.strip().splitlines()[-1] == (
        'DURDU: Onay için etkileşimli terminal gerekli; komutu tee/grep olmadan doğrudan çalıştırın. 0 satır yazıldı.'
    )


def test_no_tty_refuses_before_connection_and_never_reads_stdin(tmp_path, monkeypatch, capsys):
    import sys
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@localhost/never_connect')
    monkeypatch.setattr(live, 'verify_book', lambda path, **kw: {})
    monkeypatch.setattr(sys, 'stdin', io.StringIO(live.BOOK_SHA256[:12] + '\n'))
    monkeypatch.setattr('sqlalchemy.create_engine', lambda *a, **k: pytest.fail('must not connect without tty'))
    def raise_no_tty():
        raise OSError('no controlling terminal')
    monkeypatch.setattr(live, 'open_tty', raise_no_tty)
    dump, _ = backup_files(tmp_path)
    assert live.main(['--organization-id', '1', '--actor-id', '1', '--apply', '--backup', str(dump)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ''
    assert 'Onay için etkileşimli terminal gerekli; komutu tee/grep olmadan doğrudan çalıştırın. 0 satır yazıldı.' in captured.err


def test_summary_block_before_and_after_json_for_2027_and_2026(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@localhost/never_connect')
    monkeypatch.setattr(live, 'verify_book', lambda path, **kw: {})
    monkeypatch.setattr('sqlalchemy.create_engine', lambda *a, **k: SimpleNamespace(dispose=lambda: None))
    fake_2026 = dict(
        mode='uygula',
        counts=dict(departments=33, created_departments=0, cards=105, indicators=226, activities=182, economic_values=1155),
        departments=[dict(source_name=f'Müdürlük {i}', action='match', department_id=i, name=f'Müdürlük {i}') for i in range(1, 34)],
        skipped=[],
        failed=[],
        validation=[],
        protected_2027_before='same-hash',
        protected_2027_after='same-hash',
    )
    monkeypatch.setattr(live, 'execute', lambda *a, **k: fake_2026)
    tty = TtyStub(live.book_config(2026)[1][:12] + '\n')
    monkeypatch.setattr(live, 'open_tty', lambda: tty)
    dump, _ = backup_files(tmp_path)
    assert live.main(['--year', '2026', '--organization-id', '1', '--actor-id', '1',
                      '--apply', '--backup', str(dump)]) == 0
    captured = capsys.readouterr()
    assert f"Yazma onayı: kitap SHA256 ilk 12 karakterini yazın ({live.book_config(2026)[1][:12]}): " == tty.output.getvalue()
    assert 'Yazma onayı:' not in captured.out
    before_json, rest = captured.out.split('\n{\n', 1)
    json_body, after_json = rest.split('\n}\n', 1)
    parsed_result = json.loads('{\n' + json_body + '\n}')
    assert parsed_result['counts'] == fake_2026['counts']
    summary_before = 'ÖZET\n' + before_json.split('ÖZET\n', 1)[1]
    summary_after = after_json.strip()
    assert summary_before == summary_after
    assert len(summary_before.splitlines()) <= 15
    assert 'Mod: UYGULAMA' in summary_before
    assert 'Yıl: 2026' in summary_before
    assert live.book_config(2026)[1][:12] in summary_before
    assert 'eşleşen: 33' in summary_before and 'oluşturulan: 0' in summary_before
    for total_val in ('33', '105', '226', '182', '1155'):
        assert total_val in summary_before
    assert 'Reddedilen: 0' in summary_before
    assert '2027 korunuyor: EVET' in summary_before


@pytest.mark.postgres
def test_progress_lines_and_summary_on_real_plan_and_apply(target, printed, tmp_path, monkeypatch, capsys):
    import re
    engine, ids = target
    data = deepcopy(printed)
    data['departments'] = data['departments'][:2]
    names = [d['name'] for d in data['departments']]
    monkeypatch.setattr(live, 'verify_book', lambda path, **kw: data)
    monkeypatch.setenv(live.TARGET_ENV, engine.url.set(query={}).render_as_string(hide_password=False))

    assert live.main(['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id'])]) == 0
    plan_captured = capsys.readouterr()
    plan_err_lines = [line for line in plan_captured.err.strip().splitlines() if line.strip()]
    assert len(plan_err_lines) == 8
    assert re.fullmatch(rf'\[1/2\] {re.escape(names[0])} · oluştur · \d+\.\d sn', plan_err_lines[-2])
    assert re.fullmatch(rf'\[2/2\] {re.escape(names[1])} · oluştur · \d+\.\d sn', plan_err_lines[-1])
    assert '[1/2]' not in plan_captured.out and 'Aşama:' not in plan_captured.out
    before_json, rest = plan_captured.out.split('\n{\n', 1)
    json_body, after_json = rest.split('\n}\n', 1)
    plan_result = json.loads('{\n' + json_body + '\n}')
    plan_summary = after_json.strip()
    assert before_json.endswith(plan_summary)
    assert plan_summary.startswith('ÖZET\n')
    assert 'Mod: PLAN' in plan_summary and str(plan_result['counts']['indicators']) in plan_summary

    tty = TtyStub(live.BOOK_SHA256[:12] + '\n')
    monkeypatch.setattr(live, 'open_tty', lambda: tty)
    dump, _ = backup_files(tmp_path)
    assert live.main(['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id']),
                      '--apply', '--backup', str(dump)]) == 0
    apply_captured = capsys.readouterr()
    apply_err_lines = [line for line in apply_captured.err.strip().splitlines() if line.strip()]
    assert len(apply_err_lines) == 10
    assert re.fullmatch(rf'\[1/2\] {re.escape(names[0])} · yüklendi · \d+\.\d sn', apply_err_lines[-2])
    assert re.fullmatch(rf'\[2/2\] {re.escape(names[1])} · yüklendi · \d+\.\d sn', apply_err_lines[-1])
    assert '[1/2]' not in apply_captured.out and 'Aşama:' not in apply_captured.out
    before_json, rest = apply_captured.out.split('\n{\n', 1)
    _, after_json = rest.split('\n}\n', 1)
    apply_summary = after_json.strip()
    assert before_json.endswith(apply_summary)
    assert 'Mod: UYGULAMA' in apply_summary


def _assert_matched_phase_lines(err_lines, expected_phases):
    import re
    phase_lines = [line for line in err_lines if line.startswith('Aşama: ')]
    assert len(phase_lines) == 2 * len(expected_phases)
    for index, name in enumerate(expected_phases):
        start_line = phase_lines[2 * index]
        end_line = phase_lines[2 * index + 1]
        assert start_line == f'Aşama: {name} …'
        assert start_line.endswith('…')
        assert re.fullmatch(rf'Aşama: {re.escape(name)} · tamam · \d+\.\d sn', end_line)


@pytest.mark.postgres
def test_plan_phase_start_lines_appear_before_work_returns_and_match_end_lines(target, printed, monkeypatch):
    import sys
    engine, ids = target
    data = deepcopy(printed)
    data['departments'] = data['departments'][:2]
    monkeypatch.setenv(live.TARGET_ENV, engine.url.set(query={}).render_as_string(hide_password=False))

    events = []
    real_stderr = sys.stderr

    class RecordingStderr:
        def __init__(self):
            self.buffer = ''
            self.flushed_lines = []

        def write(self, text):
            self.buffer += text
            return real_stderr.write(text)

        def flush(self):
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                if line:
                    self.flushed_lines.append(line)
                    events.append(('stderr', line))
            real_stderr.flush()

    recorder = RecordingStderr()
    monkeypatch.setattr(sys, 'stderr', recorder)
    stdout_buf = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', stdout_buf)

    real_context = live.context
    real_department_plan = live.department_plan

    def stub_verify_book(path, **kwargs):
        # At the time verify_book runs, the start line must already be flushed on stderr,
        # and the completion line must not yet exist.
        assert recorder.flushed_lines[-1] == 'Aşama: kitap doğrulama …'
        assert not any('kitap doğrulama · tamam' in line for line in recorder.flushed_lines)
        events.append(('call', 'verify_book'))
        return data

    def stub_context(db, organization_id, actor_id, resume, **kwargs):
        assert recorder.flushed_lines[-1] == 'Aşama: veritabanı/şema denetimi …'
        assert any(line.startswith('Aşama: kitap doğrulama · tamam · ') for line in recorder.flushed_lines)
        assert not any('veritabanı/şema denetimi · tamam' in line for line in recorder.flushed_lines)
        events.append(('call', 'context'))
        return real_context(db, organization_id, actor_id, resume, **kwargs)

    def stub_department_plan(db, parsed, completed, **kwargs):
        assert recorder.flushed_lines[-1] == 'Aşama: müdürlük planı …'
        assert any(line.startswith('Aşama: veritabanı/şema denetimi · tamam · ') for line in recorder.flushed_lines)
        assert not any('müdürlük planı · tamam' in line for line in recorder.flushed_lines)
        assert not any(line.startswith('[1/') for line in recorder.flushed_lines)
        events.append(('call', 'department_plan'))
        return real_department_plan(db, parsed, completed, **kwargs)

    monkeypatch.setattr(live, 'verify_book', stub_verify_book)
    monkeypatch.setattr(live, 'context', stub_context)
    monkeypatch.setattr(live, 'department_plan', stub_department_plan)

    assert live.main(['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id'])]) == 0
    assert 'Aşama:' not in stdout_buf.getvalue()
    _assert_matched_phase_lines(
        recorder.flushed_lines,
        ['kitap doğrulama', 'veritabanı/şema denetimi', 'müdürlük planı'],
    )
    kinds_and_names = [
        (kind, val if kind == 'call' else ('start:' + val.split('Aşama: ')[1].split(' …')[0]
         if val.endswith('…') else ('end:' + val.split('Aşama: ')[1].split(' · tamam')[0]
         if ' · tamam · ' in val else 'progress')))
        for kind, val in events
    ]
    assert kinds_and_names == [
        ('stderr', 'start:kitap doğrulama'),
        ('call', 'verify_book'),
        ('stderr', 'end:kitap doğrulama'),
        ('stderr', 'start:veritabanı/şema denetimi'),
        ('call', 'context'),
        ('stderr', 'end:veritabanı/şema denetimi'),
        ('stderr', 'start:müdürlük planı'),
        ('call', 'department_plan'),
        ('stderr', 'end:müdürlük planı'),
        ('stderr', 'progress'),
        ('stderr', 'progress'),
    ]


@pytest.mark.postgres
def test_plan_and_apply_2027_and_2026_phase_lines_and_unchanged_stdout(target, printed, tmp_path, monkeypatch, capsys):
    from scripts.first_load_dryrun import NAME_MAP
    engine, ids = target
    names = set(json.loads(NAME_MAP.read_text())['map'].values()) | {'Yapı Kontrol Müdürlüğü'}
    with Session(engine) as db:
        db.add_all(Department(organization_id=ids['organization_id'], name=n) for n in sorted(names))
        db.commit()
    monkeypatch.setenv(live.TARGET_ENV, engine.url.set(query={}).render_as_string(hide_password=False))

    # 1. Full 2027 plan (all 34 directorates from the committed book)
    real_verify_book = live.verify_book
    monkeypatch.setattr(live, 'verify_book', lambda path, **kw: deepcopy(printed))
    expected_2027_plan = live.execute(engine, deepcopy(printed), **ids, year=2027)
    assert dict(expected_2027_plan['counts']) == dict(
        departments=34, created_departments=1, cards=64, indicators=263, activities=290, economic_values=1340
    )
    capsys.readouterr()

    assert live.main(['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id'])]) == 0
    cap_2027_plan = capsys.readouterr()
    assert 'Aşama:' not in cap_2027_plan.out
    _assert_matched_phase_lines(
        cap_2027_plan.err.strip().splitlines(),
        ['kitap doğrulama', 'veritabanı/şema denetimi', 'müdürlük planı'],
    )
    before_json, rest = cap_2027_plan.out.split('\n{\n', 1)
    json_body, after_json = rest.split('\n}\n', 1)
    assert json.loads('{\n' + json_body + '\n}') == expected_2027_plan
    expected_2027_summary = live.format_summary(expected_2027_plan, year=2027, apply=False)
    assert after_json.strip() == expected_2027_summary
    assert before_json.endswith(expected_2027_summary)

    # 2. Load 1 department of 2027, then test full 2026 plan (33 directorates) and 2026 apply
    data_2027 = deepcopy(printed)
    data_2027['departments'] = data_2027['departments'][:1]
    monkeypatch.setattr(live, 'verify_book', lambda path, **kw: deepcopy(data_2027))
    tty_2027 = TtyStub(live.BOOK_SHA256[:12] + '\n')
    monkeypatch.setattr(live, 'open_tty', lambda: tty_2027)
    dump, _ = backup_files(tmp_path)
    assert live.main(['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id']),
                      '--apply', '--backup', str(dump)]) == 0
    cap_2027_apply = capsys.readouterr()
    assert 'Aşama:' not in cap_2027_apply.out
    _assert_matched_phase_lines(
        cap_2027_apply.err.strip().splitlines(),
        ['kitap doğrulama', 'yedek doğrulama', 'veritabanı/şema denetimi', 'müdürlük planı'],
    )

    book_2026_parsed = real_verify_book(live.book_config(2026)[0], year=2026)
    monkeypatch.setattr(live, 'verify_book', lambda path, **kw: deepcopy(book_2026_parsed))
    expected_2026_plan = live.execute(engine, deepcopy(book_2026_parsed), **ids, year=2026)
    assert dict(expected_2026_plan['counts']) == dict(
        departments=33, created_departments=0, cards=105, indicators=226, activities=182, economic_values=1270
    )
    capsys.readouterr()

    assert live.main(['--year', '2026', '--organization-id', str(ids['organization_id']),
                      '--actor-id', str(ids['actor_id'])]) == 0
    cap_2026_plan = capsys.readouterr()
    assert 'Aşama:' not in cap_2026_plan.out
    _assert_matched_phase_lines(
        cap_2026_plan.err.strip().splitlines(),
        ['kitap doğrulama', 'veritabanı/şema denetimi', 'müdürlük planı'],
    )
    before_json, rest = cap_2026_plan.out.split('\n{\n', 1)
    json_body, after_json = rest.split('\n}\n', 1)
    assert json.loads('{\n' + json_body + '\n}') == expected_2026_plan
    expected_2026_summary = live.format_summary(expected_2026_plan, year=2026, apply=False)
    assert after_json.strip() == expected_2026_summary
    assert before_json.endswith(expected_2026_summary)
    assert '2027 korunuyor: EVET' in expected_2026_summary

    data_2026 = deepcopy(book_2026_parsed)
    data_2026['departments'] = data_2026['departments'][:2]
    data_2026['catalogue_descriptions'] = [
        d for d in data_2026['catalogue_descriptions']
        if d['department'] in {dept['name'] for dept in data_2026['departments']}
    ]
    monkeypatch.setattr(live, 'verify_book', lambda path, **kw: deepcopy(data_2026))
    tty_2026 = TtyStub(live.book_config(2026)[1][:12] + '\n')
    monkeypatch.setattr(live, 'open_tty', lambda: tty_2026)
    dump_2026, _ = backup_files(tmp_path)
    assert live.main(['--year', '2026', '--organization-id', str(ids['organization_id']),
                      '--actor-id', str(ids['actor_id']), '--apply', '--backup', str(dump_2026)]) == 0
    cap_2026_apply = capsys.readouterr()
    assert 'Aşama:' not in cap_2026_apply.out
    _assert_matched_phase_lines(
        cap_2026_apply.err.strip().splitlines(),
        [
            'kitap doğrulama',
            'yedek doğrulama',
            'veritabanı/şema denetimi',
            'müdürlük planı',
            '2027 koruma özeti hesabı',
            '2027 koruma özeti hesabı',
        ],
    )
