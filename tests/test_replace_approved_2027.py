"""CIV-214: real books, migrated disposable PostgreSQL, atomic replacement."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from uuid import uuid4
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from scripts import first_load_live as live
from scripts import replace_approved_2027 as replace
from scripts.first_load_dryrun import disposable_database, local_test_url
from tests.test_first_load_live import backup_files, state, TtyStub
from app.models import (Activity, AuditLog, Department, ImportBatch, Indicator, IndicatorValue,
                        Organization, Publication, ReportingPeriod, Submission, User)
from app.first_load_service import period_rows_hash, load_all_models


@pytest.fixture(scope='module')
def books():
    return replace.verify_old_book(), live.verify_book(live.BOOK)


@pytest.fixture(scope='module')
def compatible_books(books):
    # Transaction-mechanics fixture with an unchanged catalogue. The real pinned
    # corrected book (catalogue differences, D-466) has its own tests below.
    corrected = deepcopy(books[0])
    for source in corrected['departments']:
        if source['name'] == 'Özel Kalem Müdürlüğü':
            source['activities'] = [a for a in source['activities'] if not a['name'].startswith('0006')]
    corrected['departments'][0]['blocks'][0]['indicators'][0]['values'][0]['value'] = '987'
    return books[0], corrected


@pytest.fixture(scope='module')
def baseline(books):
    with disposable_database(local_test_url()) as engine:
        load_all_models()
        with Session(engine) as db:
            db.add_all([Organization(id=1, name='CIV-214 yerel prova'),
                User(id=1, email='civ214@example.invalid', full_name='Yerel Strateji', role='strategy', password_hash='unused'),
                ReportingPeriod(id=1, year=2026), ReportingPeriod(id=2, year=2027), ReportingPeriod(id=3, year=2028)])
            db.commit()
        with patch.object(live, 'BOOK', replace.OLD_BOOK), patch.object(live, 'BOOK_SHA256', replace.OLD_SHA256):
            loaded = live.execute(engine, books[0], organization_id=1, actor_id=1, apply=True)
            assert loaded['failed'] == []
        # Meaningful old-period rows, including historical value years. No live
        # state or seed dump enters the rehearsal.
        with Session(engine) as db:
            did = db.scalar(select(Department.id).order_by(Department.id))
            from app.models import Program, SubProgram, ActivityCostValue, DepartmentCostValue
            for pid, year in ((1, 2026), (3, 2028)):
                p = Program(period_id=pid, name=f'Korunan {year}')
                db.add(p); db.flush()
                sp = SubProgram(period_id=pid, program_id=p.id, name='Korunan alt program')
                db.add(sp); db.flush()
                ind = Indicator(period_id=pid, department_id=did, subprogram_id=sp.id, name='Korunan gösterge', unit='Adet')
                act = Activity(period_id=pid, department_id=did, subprogram_id=sp.id, name='Korunan faaliyet')
                db.add_all([ind, act]); db.flush()
                db.add_all([IndicatorValue(indicator_id=ind.id, year=year-1, value_kind='target', value=None, raw_text='-', state='needs_review'),
                    ActivityCostValue(activity_id=act.id, year=year, value_kind='budget', amount=0, raw_text='0'),
                    DepartmentCostValue(period_id=pid, department_id=did, year=year, value_kind='budget', amount=123)])
            db.commit()
        yield engine


@pytest.fixture
def target(baseline):
    # Clone the closed, migrated local baseline. Each refusal gets an independent
    # database without reparsing/reloading both full books for every case.
    name = 'civ214_' + uuid4().hex
    admin = create_engine(local_test_url(), isolation_level='AUTOCOMMIT', poolclass=NullPool,
                          connect_args={'hostaddr': '127.0.0.1', 'connect_timeout': 5})
    with admin.connect() as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{name}" TEMPLATE "{baseline.url.database}"')
    engine = create_engine(baseline.url.set(database=name), poolclass=NullPool)
    try:
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as conn:
            conn.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.dispose()


@pytest.fixture
def approved(monkeypatch, tmp_path):
    dump, _ = backup_files(tmp_path)
    monkeypatch.setattr(live, 'open_tty', lambda: TtyStub(replace.CONFIRMATION + '\n'))
    return dump


def execute(engine, books, **kwargs):
    return replace.execute(engine, *books, organization_id=1, actor_id=1, **kwargs)


def row_state(engine):
    """Hash every public row; IDs/timestamps stay for exact rollback evidence."""
    with engine.connect() as conn:
        names = conn.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")).all()
        return {name: replace.digest(sorted([dict(r) for r in conn.exec_driver_sql(f'SELECT * FROM "{name}"').mappings()], key=replace.encoded)) for name in names}


def test_pins_and_schema_head():
    from scripts.book_to_load_docx import FIRST_LOAD_BOOKS
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    assert live.book_config() == (live.BOOK, FIRST_LOAD_BOOKS[2027][1])
    assert live.BOOK.name == '2027-performans-programi_SONN_duzeltilmis.idml'
    assert hashlib.sha256(live.BOOK.read_bytes()).hexdigest() == live.BOOK_SHA256
    assert hashlib.sha256(replace.OLD_BOOK.read_bytes()).hexdigest() == replace.OLD_SHA256
    assert ScriptDirectory.from_config(Config(str(live.ROOT / 'alembic.ini'))).get_heads() == [live.HEAD]


def test_compatible_catalogue_atomic_rehearsal(target, compatible_books, approved, capsys):
    books = compatible_books
    before, sequences = row_state(target), state(target)
    planned = execute(target, books)
    assert row_state(target) == before
    assert state(target) == sequences  # read-only plan does not advance sequences
    assert planned['refusals'] == []
    assert planned['counts']['activities'] == dict(old=291, new=290)
    with Session(target) as db:
        protected = {year: period_rows_hash(db, year) for year in (2026, 2028)}
    applied = execute(target, books, apply=True, backup=approved)
    assert applied['mode'] == 'approved-load-replace-apply'
    with Session(target) as db:
        actual = replace.signatures({name: replace.owned_rows(db, 2)[name] for name in replace.CONTENT})
        assert {year: period_rows_hash(db, year) for year in protected} == protected
        logs = db.scalars(select(AuditLog).where(AuditLog.action == replace.ACTION)).all()
        assert len(logs) == 1
        receipt = json.loads(logs[0].details)
        assert receipt['old_sha256'] == replace.OLD_SHA256
        assert receipt['new_sha256'] == live.BOOK_SHA256
        assert receipt['counts'] == planned['counts']
        after = replace.catalogue_state(db, 2)
        assert receipt['decision'] == 'D-466'
        assert receipt['catalogue_after'] == after
        assert receipt['catalogue_before'] == planned['catalogue_before']
        assert {k: v['count'] for k, v in after.items()} == {k: v['count'] for k, v in planned['catalogue_before'].items()}
        from app.program_service import approved_book_provenance
        assert approved_book_provenance(db, 2)['book_sha256'] == live.BOOK_SHA256
        assert len(live.completed_departments(db, 2)) == 34
    resume_before = row_state(target)
    resume = live.execute(target, books[1], organization_id=1, actor_id=1, resume=True)
    assert len(resume['skipped']) == 34
    assert row_state(target) == resume_before
    # Independent fresh fixture load, through the existing operator loader.
    with disposable_database(local_test_url()) as fresh:
        with Session(fresh) as db:
            db.add_all([Organization(id=1, name='Taze SONN'),
                User(id=1, email='fresh@example.invalid', full_name='Strateji', role='strategy', password_hash='unused'),
                ReportingPeriod(id=1, year=2026), ReportingPeriod(id=2, year=2027)])
            # Keep shared department IDs identical; their structure is untouched.
            with Session(target) as original:
                for d in original.scalars(select(Department)):
                    db.add(Department(id=d.id, organization_id=1, name=d.name))
            db.commit()
        loaded = live.execute(fresh, books[1], organization_id=1, actor_id=1, apply=True)
        assert not loaded['failed']
        with Session(fresh) as db:
            fresh_rows = replace.owned_rows(db, 2)
            expected = replace.signatures({name: fresh_rows[name] for name in replace.CONTENT})
        assert actual == expected  # full row-content multisets, ignoring generated IDs
    output = capsys.readouterr().out
    assert 'activities: 291 → 290' in output
    assert 'Reddedilen: 0' in output
    # A second apply must refuse, never clear corrected data.
    before = row_state(target)
    assert execute(target, books, apply=True, backup=approved)['refusals']
    assert row_state(target) == before
    with Session(target) as db:
        receipt_log = db.scalar(select(AuditLog).where(AuditLog.action == replace.ACTION))
        receipt = json.loads(receipt_log.details)
        receipt['old_batch_ids'].pop()
        receipt_log.details = json.dumps(receipt)
        db.commit()
        assert approved_book_provenance(db, 2) is None
        with pytest.raises(live.Refusal, match='geçmişi uyuşmuyor'):
            live.completed_departments(db, 2)


@pytest.mark.parametrize('kind', ['indicator', 'card', 'activity', 'activity_cost', 'economic', 'personnel',
                                 'link', 'scope', 'mapping', 'manual_mapping', 'publication', 'approved_publication', 'submission', 'event', 'audit',
                                 'report', 'ic', 'cross_period', 'batch', 'missing_marker'])
def test_refusals_write_zero_rows(target, compatible_books, approved, kind):
    books = compatible_books
    from app.models import (ActivityCostValue, EconomicValue, DepartmentCostValue, ReportCard,
        ActivityCatalogueLink, DepartmentScope, SubmissionEvent, ActivityReport)
    with Session(target) as db:
        did = db.scalar(select(Submission.department_id).where(Submission.period_id == 2))
        if kind == 'indicator':
            row = db.scalar(select(IndicatorValue).join(Indicator).where(Indicator.period_id == 2))
            row.value = Decimal('123456789')
        elif kind == 'card':
            db.scalar(select(ReportCard).where(ReportCard.period_id == 2)).goal = 'Sonradan değişti'
        elif kind == 'activity':
            db.scalar(select(Activity).where(Activity.period_id == 2)).contract_bound = True
        elif kind == 'activity_cost':
            db.scalar(select(ActivityCostValue).join(Activity).where(Activity.period_id == 2)).source_resolution_json = '{"manual":true}'
        elif kind == 'economic':
            db.scalar(select(EconomicValue).where(EconomicValue.period_id == 2)).raw_text = 'Sonradan değişti'
        elif kind == 'personnel':
            db.scalar(select(DepartmentCostValue).where(DepartmentCostValue.period_id == 2)).amount = 42
        elif kind == 'link':
            row = db.scalar(select(ActivityCatalogueLink).join(Activity).where(Activity.period_id == 2))
            db.delete(row)
        elif kind == 'scope':
            db.add(DepartmentScope(period_id=2, department_id=did))
        elif kind in {'mapping', 'manual_mapping'}:
            db.add(AuditLog(user_id=1, action='activity_mapping_csv' if kind == 'mapping' else 'activity_mapping', entity_type='mapping_batch', entity_id=42, details='{}'))
        elif kind in {'publication', 'approved_publication'}:
            publication = Publication(period_id=2, version=1, snapshot_json='{}', sha256='a'*64, created_by=1)
            db.add(publication); db.flush()
            if kind == 'approved_publication':
                db.add(AuditLog(user_id=1, action='publication_approved_book', entity_type='publication', entity_id=publication.id))
        elif kind == 'submission':
            db.scalar(select(Submission).where(Submission.period_id == 2)).status = 'submitted'
        elif kind == 'event':
            sub = db.scalar(select(Submission).where(Submission.period_id == 2))
            db.add(SubmissionEvent(period_id=2, department_id=sub.department_id, submission_id=sub.id, event_type='submitted'))
        elif kind == 'audit':
            iid = db.scalar(select(Indicator.id).where(Indicator.period_id == 2))
            db.add(AuditLog(user_id=1, action='indicator_update', entity_type='indicator', entity_id=iid, details='{}'))
        elif kind == 'report':
            db.add(ActivityReport(organization_id=1, period_id=2))
        elif kind == 'ic':
            # IC period IDs belong to a separate domain; year owns this record.
            from app.internal_control_models import ICPlan, ICImport
            imp = ICImport(source_filename='yerel.xlsx', source_sha256='a'*64, source_json='{}', created_by=1)
            db.add(imp); db.flush()
            plan = ICPlan(title='Yerel', start_year=2027, end_year=2028, version_label='1', status='draft', source_filename='yerel.xlsx', source_sha256='a'*64, import_id=imp.id, created_by=1)
            db.add(plan)
        elif kind == 'cross_period':
            # A 2026 row pointing to a 2027 parent must block, never be cascaded.
            act = db.scalar(select(Activity).where(Activity.period_id == 1))
            card = db.scalar(select(ReportCard).where(ReportCard.period_id == 2))
            act.card_id = card.id
        elif kind == 'batch':
            db.add(ImportBatch(period_id=2, filename='manual.docx', payload_json='{}', created_by=1))
        elif kind == 'missing_marker':
            log = db.scalar(select(AuditLog).where(AuditLog.action == live.MARKER))
            db.delete(log)
        db.commit()
    before, counts = row_state(target), state(target)
    result = execute(target, books, apply=True, backup=approved)
    assert result['refusals'], kind
    assert row_state(target) == before
    assert state(target) == counts


@pytest.mark.parametrize('guard', ['missing', 'stale', 'wrong_phrase', 'non_tty', 'expired_at_prompt'])
def test_operator_guards(target, compatible_books, approved, monkeypatch, guard):
    books = compatible_books
    backup = approved
    if guard == 'missing':
        backup = None
    elif guard == 'stale':
        path = backup.with_suffix('.manifest.json')
        data = json.loads(path.read_text())
        data['utc_timestamp'] = (datetime.now(timezone.utc)-timedelta(hours=2)).isoformat()
        path.write_text(json.dumps(data))
    elif guard == 'wrong_phrase':
        monkeypatch.setattr(live, 'open_tty', lambda: TtyStub('wrong\n'))
    elif guard == 'non_tty':
        def no_tty():
            raise OSError('no controlling terminal')
        monkeypatch.setattr(live, 'open_tty', no_tty)
    else:
        def expired(prompt):
            path = backup.with_suffix('.manifest.json')
            data = json.loads(path.read_text())
            data['utc_timestamp'] = (datetime.now(timezone.utc)-timedelta(hours=2)).isoformat()
            path.write_text(json.dumps(data))
            return replace.CONFIRMATION
        monkeypatch.setattr(live, 'read_confirmation', expired)
    before, counts = row_state(target), state(target)
    with pytest.raises(live.Refusal):
        execute(target, books, apply=True, backup=backup)
    assert row_state(target) == before
    assert state(target) == counts


def test_catalogue_difference_and_all_refusals_listed(target, compatible_books, approved):
    books = compatible_books
    new = deepcopy(books[1])
    new['departments'][0]['blocks'][0]['activity_memberships'][0]['name'] += ' değişiklik'
    with Session(target) as db:
        db.add_all([AuditLog(user_id=1, action='activity_mapping_csv_apply', entity_type='mapping_batch', entity_id=42),
            Publication(period_id=2, version=1, snapshot_json='{}', sha256='b'*64, created_by=1)])
        db.commit()
    before = row_state(target)
    result = execute(target, (books[0], new), apply=True, backup=approved)
    assert result['catalogue_differences']
    assert any('publications' in reason for reason in result['refusals'])
    assert any('denetim' in reason for reason in result['refusals'])
    assert row_state(target) == before


def test_mid_load_failure_restores_onayli(target, compatible_books, approved, monkeypatch):
    books = compatible_books
    import app.first_load_service as service
    original = service.apply_first_load_batch
    calls = []
    def fail(db, batch, actor):
        result = original(db, batch, actor)
        calls.append(batch.id)
        if len(calls) == 3:
            raise RuntimeError('injected after third department writes')
        return result
    monkeypatch.setattr(service, 'apply_first_load_batch', fail)
    before = row_state(target)
    with pytest.raises(RuntimeError):
        execute(target, books, apply=True, backup=approved)
    assert len(calls) == 3
    assert row_state(target) == before


def test_safe_parser_never_echoes_url(capsys):
    with pytest.raises(SystemExit):
        replace.main(['--organization-id', '1', '--actor-id', '1', '--url', 'secret-connection'])
    assert 'secret-connection' not in capsys.readouterr().err


def test_real_corrected_book_replaces_catalogue_atomically(target, books, approved, capsys):
    """D-466: the real final book, including its 2027 catalogue changes."""
    before, sequences = row_state(target), state(target)
    planned = execute(target, books)
    assert planned['refusals'] == [], planned['refusals']
    assert {d['table'] for d in planned['catalogue_differences']} == {
        'subprograms', 'official_activities', 'activity_responsibilities'}
    assert planned['counts']['activities'] == dict(old=291, new=290)
    assert row_state(target) == before
    assert state(target) == sequences
    output = capsys.readouterr().out
    assert 'Katalog farkı · Resmî faaliyet' in output
    assert '0006.Sosyal Güvenlik Kurumuna' in output
    assert 'ortalama 11[0] adet' in output and 'ortalama 11[9] adet' in output  # Makine İkmal 110 → 119
    with Session(target) as db:
        protected = {year: period_rows_hash(db, year) for year in (2026, 2028)}
    applied = execute(target, books, apply=True, backup=approved)
    assert applied['mode'] == 'approved-load-replace-apply'
    with Session(target) as db:
        assert {year: period_rows_hash(db, year) for year in protected} == protected
        actual = replace.signatures({name: replace.owned_rows(db, 2)[name] for name in replace.CONTENT})
        receipt = json.loads(db.scalar(select(AuditLog.details).where(AuditLog.action == replace.ACTION)))
        assert receipt['catalogue_after'] == replace.catalogue_state(db, 2)
        assert receipt['catalogue_after']['subprograms']['count'] == receipt['catalogue_before']['subprograms']['count']
        from app.program_service import approved_book_provenance
        assert approved_book_provenance(db, 2)['book_sha256'] == live.BOOK_SHA256
        assert len(live.completed_departments(db, 2)) == 34
    # Equal to an independent fresh first load of the corrected book.
    with disposable_database(local_test_url()) as fresh:
        with Session(fresh) as db:
            db.add_all([Organization(id=1, name='Taze düzeltilmiş'),
                User(id=1, email='fresh@example.invalid', full_name='Strateji', role='strategy', password_hash='unused'),
                ReportingPeriod(id=1, year=2026), ReportingPeriod(id=2, year=2027)])
            with Session(target) as original:
                for d in original.scalars(select(Department)):
                    db.add(Department(id=d.id, organization_id=1, name=d.name))
            db.commit()
        assert not live.execute(fresh, books[1], organization_id=1, actor_id=1, apply=True)['failed']
        with Session(fresh) as db:
            fresh_rows = replace.owned_rows(db, 2)
            assert actual == replace.signatures({name: fresh_rows[name] for name in replace.CONTENT})


@pytest.mark.parametrize('kind', ['link_from_2028', 'subprogram_from_2028', 'responsibility_to_2028'])
def test_cross_period_catalogue_reference_refuses(target, books, approved, kind):
    """D-466 guard: a 2027 catalogue row shared with another period blocks, 0 rows written."""
    from app.models import ActivityCatalogueLink, OfficialActivity, SubProgram, ActivityResponsibility
    with Session(target) as db:
        official = db.scalar(select(OfficialActivity).where(OfficialActivity.period_id == 2))
        other = db.scalar(select(Activity).where(Activity.period_id == 3))
        if kind == 'link_from_2028':
            db.add(ActivityCatalogueLink(activity_id=other.id, official_activity_id=official.id))
        elif kind == 'subprogram_from_2028':
            other.subprogram_id = db.scalar(select(SubProgram.id).where(SubProgram.period_id == 2))
        else:
            foreign = OfficialActivity(period_id=3, program_code='', program_name='Korunan 2028',
                subprogram_code='', subprogram_name='Korunan alt program', code='9999', name='9999 Korunan')
            db.add(foreign); db.flush()
            # A 2027 link that points at a 2028 catalogue entry.
            act = db.scalar(select(Activity).where(Activity.period_id == 2))
            db.add(ActivityCatalogueLink(activity_id=act.id, official_activity_id=foreign.id))
        db.commit()
    before, counts = row_state(target), state(target)
    result = execute(target, books, apply=True, backup=approved)
    assert any('dönemler arası bağ' in reason for reason in result['refusals']), result['refusals']
    assert result['mode'] == 'approved-load-replace-plan'
    assert row_state(target) == before
    assert state(target) == counts


def test_existing_advisory_lock_refuses(target, compatible_books, approved):
    before = row_state(target)
    with target.connect() as blocker:
        blocker.execute(text('SELECT pg_advisory_lock(:key)'), {'key': live.LOCK})
        try:
            with pytest.raises(live.Refusal, match='Başka ilk yükleme'):
                execute(target, compatible_books, apply=True, backup=approved)
        finally:
            blocker.execute(text('SELECT pg_advisory_unlock(:key)'), {'key': live.LOCK})
    assert row_state(target) == before


def test_real_sonn_fresh_load_equals_signatures_and_keeps_unreadable_cells(books):
    from app.import_service import department_key
    with disposable_database(local_test_url()) as engine:
        with Session(engine) as db:
            db.add_all([Organization(id=1, name='Taze gerçek SONN'),
                User(id=1, email='sonn@example.invalid', full_name='Strateji', role='strategy', password_hash='unused'),
                ReportingPeriod(id=1, year=2026), ReportingPeriod(id=2, year=2027)])
            db.commit()
        loaded = live.execute(engine, books[1], organization_id=1, actor_id=1, apply=True)
        assert not loaded['failed']
        with Session(engine) as db:
            mapping = {department_key(d.name): d.id for d in db.scalars(select(Department))}
            actual = replace.owned_rows(db, 2)
            expected = replace.source_rows(books[1], mapping)
            assert replace.signatures({n: actual[n] for n in replace.CONTENT}) == replace.signatures(expected)
            values = [row for name in ('economic_values', 'activity_cost_values', 'department_cost_values') for row in actual[name]]
            # Final book (D-465): the dot-decimal Makine İkmal cells are fixed.
            assert not [r for r in values if r['raw_text'] in {'21.303.126.00', '19.292.188.00', '3.010.938.00'}]
            fixed = [r for r in values if r['raw_text'] == '22.303.126,00']
            assert fixed and all(r['amount'] == Decimal('22303126.00') for r in fixed)
            from app.program_service import approved_book_provenance
            assert approved_book_provenance(db, 2)['book_sha256'] == live.BOOK_SHA256


def test_read_only_audits_allow_plan(target, compatible_books):
    with Session(target) as db:
        did = db.scalar(select(Department.id))
        db.add_all([AuditLog(user_id=1, action=action, entity_type=entity_type, entity_id=identity)
            for action, entity_type, identity in (
                ('login', 'user', 1), ('operations_backup_export', 'database', None),
                ('department_export_docx', 'department', did),
                ('activity_evidence_download', 'activity_evidence_file', 99999))])
        db.commit()
    before = row_state(target)
    assert execute(target, compatible_books)['refusals'] == []
    assert row_state(target) == before


# CIV-217: live 2027 kept an older catalogue through the D-135 preprint clear, and
# the 30 Oct load only filled blank subprogramme texts. The plan lists both and the
# apply replaces them; a referenced or missing catalogue row still blocks.

def _corrected_subprograms(target, books):
    from app.import_service import department_key
    with Session(target) as db:
        mapping = {department_key(d.name): d.id for d in db.scalars(select(Department))}
    rows = replace.source_rows(books[1], mapping)
    programs = {r['id']: r['name'] for r in rows['programs']}
    return {(programs[r['program_id']], r['name']): r for r in rows['subprograms']}


def test_leftover_catalogue_and_stale_texts_are_listed_and_replaced(target, books, approved, capsys):
    from app.models import Program, SubProgram
    with Session(target) as db:
        old_program = Program(period_id=2, name='ESKİ ÖN BASKI PROGRAMI')
        db.add(old_program); db.flush()
        old_child = SubProgram(period_id=2, program_id=old_program.id, name='Eski alt program')
        kept = db.scalar(select(SubProgram).where(SubProgram.period_id == 2).order_by(SubProgram.id))
        sibling = SubProgram(period_id=2, program_id=kept.program_id, name='Ön baskıda kalan alt program')
        db.add_all([old_child, sibling]); db.flush()
        identity = (kept.program.name, kept.name)
        kept.rationale = 'GEREKÇE: ön baskı metni'
        leftover_ids = {('programs', old_program.id), ('subprograms', old_child.id), ('subprograms', sibling.id)}
        kept_id, old_program_id = kept.id, old_program.id
        db.commit()
    before = row_state(target)
    planned = execute(target, books)
    assert planned['refusals'] == [], planned['refusals']
    assert {(r['table'], r['id']) for r in planned['leftover_catalogue']} == leftover_ids
    assert [(r['id'], r['field'], r['live']) for r in planned['stale_catalogue_texts']] == [
        (kept_id, 'rationale', 'GEREKÇE: ön baskı metni')]
    assert row_state(target) == before
    output = capsys.readouterr().out
    assert 'Kullanılmayan eski katalog · 1 program, 2 alt program silinecek' in output
    assert 'ESKİ ÖN BASKI PROGRAMI' in output and 'Eski alt program metni · 1 alan' in output
    applied = execute(target, books, apply=True, backup=approved)
    assert applied['mode'] == 'approved-load-replace-apply'
    corrected = _corrected_subprograms(target, books)
    with Session(target) as db:
        assert db.get(Program, old_program_id) is None
        assert db.scalar(select(Program).where(Program.period_id == 2, Program.name == 'ESKİ ÖN BASKI PROGRAMI')) is None
        live_subprograms = {(s.program.name, s.name): s for s in db.scalars(select(SubProgram).where(SubProgram.period_id == 2))}
        assert set(live_subprograms) == set(corrected)
        assert all(live_subprograms[k].rationale == corrected[k]['rationale'] and live_subprograms[k].goal == corrected[k]['goal']
                   for k in corrected)
        assert live_subprograms[identity].rationale != 'GEREKÇE: ön baskı metni'
        receipt = json.loads(db.scalar(select(AuditLog.details).where(AuditLog.action == replace.ACTION)))
        assert {(r['table'], r['id']) for r in receipt['leftover_catalogue']} == leftover_ids
        assert receipt['stale_catalogue_texts'] == [dict(id=kept_id, field='rationale')]
        from app.program_service import approved_book_provenance
        assert approved_book_provenance(db, 2)['book_sha256'] == live.BOOK_SHA256


@pytest.mark.parametrize('kind', ['referenced_leftover', 'missing_onayli'])
def test_catalogue_review_refusals_write_zero_rows(target, books, approved, kind):
    from app.models import Program, SubProgram
    with Session(target) as db:
        indicator = db.scalar(select(Indicator).where(Indicator.period_id == 2).order_by(Indicator.id))
        if kind == 'referenced_leftover':
            stray = SubProgram(period_id=2, program_id=indicator.subprogram.program_id, name='Bağlı eski alt program')
            db.add(stray); db.flush()
            indicator.subprogram_id = stray.id
            expected = 'ONAYLI kitapta yok ama başka kayıtlar ona bağlı'
        else:
            program = db.scalar(select(Program).where(Program.period_id == 2).order_by(Program.id))
            program.name += ' (yeniden adlandırıldı)'
            expected = 'ONAYLI katalog satırı canlıda eksik'
        db.commit()
    before, counts = row_state(target), state(target)
    result = execute(target, books, apply=True, backup=approved)
    assert result['mode'] == 'approved-load-replace-plan'
    assert any(expected in reason for reason in result['refusals']), result['refusals']
    assert row_state(target) == before
    assert state(target) == counts


def test_other_period_and_account_audits_allow_plan(target, compatible_books):
    from app.models import Program
    with Session(target) as db:
        did = db.scalar(select(Department.id))
        program_2026 = db.scalar(select(Program.id).where(Program.period_id == 1))
        activity_2026 = db.scalar(select(Activity.id).where(Activity.period_id == 1))
        db.add_all([AuditLog(user_id=1, action=action, entity_type=entity_type, entity_id=identity, details=details)
            for action, entity_type, identity, details in (
                ('catalogue_create', 'program', program_2026, None),
                ('catalogue_link', 'activity', activity_2026, None),
                ('pp_data_change', 'department', did, 'period_id=1'),
                ('user_create', 'user', 1, None), ('user_bulk_create', 'user_batch', 7, None),
                ('user_permission_change', 'user', 1, None))])
        db.commit()
    before = row_state(target)
    assert execute(target, compatible_books)['refusals'] == []
    assert row_state(target) == before


@pytest.mark.parametrize('details', ['period_id=2', None, 'period_id=1; period_id=2'])
def test_2027_or_unclear_pp_change_audit_refuses(target, compatible_books, details):
    with Session(target) as db:
        db.add(AuditLog(user_id=1, action='pp_data_change', entity_type='department',
                        entity_id=db.scalar(select(Department.id)), details=details))
        db.commit()
    assert any('denetim kaydı' in reason for reason in execute(target, compatible_books)['refusals'])


def test_old_code_load_without_recomputable_provenance_still_plans(target, books, approved):
    """The 30 Oct live load predates later migrations; its applied_hash cannot be recomputed today."""
    from app.models import ImportBatch
    from app.program_service import approved_book_provenance
    with Session(target) as db:
        batch = db.scalar(select(ImportBatch).where(ImportBatch.period_id == 2, ImportBatch.status == 'applied')
                          .order_by(ImportBatch.id))
        batch.applied_hash = '0' * 64
        db.commit()
        assert approved_book_provenance(db, 2) is None
    planned = execute(target, books)
    assert planned['refusals'] == [], planned['refusals']
    applied = execute(target, books, apply=True, backup=approved)
    assert applied['mode'] == 'approved-load-replace-apply'
    with Session(target) as db:
        assert approved_book_provenance(db, 2)['book_sha256'] == live.BOOK_SHA256
