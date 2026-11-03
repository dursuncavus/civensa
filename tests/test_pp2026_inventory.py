"""CIV-171: read-only inventory from a restored synthetic pilot period."""
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
import json

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app import models as m
from ops import pp2026_rehearsal as rehearsal
from scripts.rehearse_clear_preprint_2027 import snapshot
from test_first_load_live import target
from test_pp2026_rehearsal import (assert_private_summary, dispatch, dump_backup,
                                   pg18_clients)


PRIVATE = 'CIV171-private-name-email@example.invalid https://private.invalid/marker'
AMOUNT = Decimal('987654321.12')
FIRST = datetime(2026, 3, 4, 9, 17)
LAST = datetime(2026, 4, 5, 16, 42)


def pilot(engine, ids, role=None):
    with Session(engine) as db:
        strategy = db.get(m.User, ids['actor_id'])
        strategy.full_name = PRIVATE
        period = m.ReportingPeriod(year=2026, status='closed', template_status='verified')
        other = m.ReportingPeriod(year=2027, status='active')
        department = m.Department(organization_id=ids['organization_id'], name=PRIVATE)
        db.add_all([period, other, department])
        db.flush()
        batch = m.ImportBatch(period_id=period.id, filename=PRIVATE, status='applied',
                              created_by=strategy.id, created_at=FIRST, applied_at=LAST,
                              payload_json=json.dumps({'private': PRIVATE}))
        program = m.Program(period_id=period.id, name=PRIVATE)
        db.add_all([batch, program])
        db.flush()
        subprogram = m.SubProgram(period_id=period.id, program_id=program.id, name=PRIVATE)
        db.add(subprogram)
        db.flush()
        indicator = m.Indicator(period_id=period.id, department_id=department.id,
                                subprogram_id=subprogram.id, name=PRIVATE, unit='CIV171-private-unit')
        submission = m.Submission(period_id=period.id, department_id=department.id,
                                  status='draft', return_note=PRIVATE)
        db.add_all([indicator, submission])
        db.flush()
        db.add(m.IndicatorValue(indicator_id=indicator.id, year=2026, value_kind='target',
                                 value=AMOUNT, raw_text=PRIVATE, state='verified'))
        # A strategy importer and importer-generated catalogue audits are not
        # proof of manual input; overlapping entity IDs in 2027 must not leak in.
        db.add_all([
            m.AuditLog(user_id=strategy.id, action='first_load_department', entity_type='import_batch',
                       entity_id=batch.id, details=PRIVATE, created_at=FIRST),
            m.AuditLog(user_id=strategy.id, action='catalogue_create', entity_type='programs',
                       entity_id=program.id, details=json.dumps({'source': {'kind': 'first_load'},
                                                               'values': PRIVATE}), created_at=FIRST),
            m.AuditLog(user_id=strategy.id, action='indicator_update', entity_type='reporting_period',
                       entity_id=other.id, details=PRIVATE, created_at=LAST),
        ])
        if role:
            actor = m.User(email='CIV171-private-user@example.invalid', full_name=PRIVATE,
                           role=role, password_hash=PRIVATE, department_id=department.id)
            db.add(actor)
            db.flush()
            db.add_all([
                m.IndicatorValue(indicator_id=indicator.id, year=2026, value_kind='actual',
                                 value=AMOUNT, raw_text=PRIVATE, state='verified'),
                m.SubmissionEvent(submission_id=submission.id, department_id=department.id,
                                  period_id=period.id, actor_user_id=actor.id, event_type='submitted',
                                  note=PRIVATE, snapshot_json=json.dumps({'private': PRIVATE}), created_at=LAST),
                m.AuditLog(user_id=actor.id, action='indicator_update', entity_type='indicator',
                           entity_id=indicator.id, details=PRIVATE, created_at=LAST),
                m.AuditLog(user_id=actor.id, action=PRIVATE, entity_type='indicator_values',
                           entity_id=1, details=PRIVATE, created_at=LAST),
            ])
        db.commit()


@pytest.mark.postgres
@pytest.mark.parametrize('role,answer', [(None, 'HAYIR'), ('department', 'EVET'),
                                         ('strategy', 'EVET'), ('admin', 'HAYIR'),
                                         ('CIV171-private-role', 'HAYIR')])
def test_restored_pilot_inventory_keeps_refusal_private_and_read_only(
        role, answer, target, pg18_clients, tmp_path, monkeypatch, capsys):
    engine, ids = target
    pilot(engine, ids, role)
    original = snapshot(engine)
    dump = dump_backup(engine, tmp_path)
    dispatch(monkeypatch, tmp_path)
    monkeypatch.setattr(rehearsal, 'download_verified_run', lambda _: (dump, {}))
    actual_empty = rehearsal.empty_database
    observed = {}

    @contextmanager
    def inspect_copy(url):
        with actual_empty(url) as restored:
            try:
                yield restored
            finally:
                observed['unchanged'] = snapshot(restored) == original
    monkeypatch.setattr(rehearsal, 'empty_database', inspect_copy)
    actual_inventory = rehearsal.period_inventory

    def capture(restored):
        result = actual_inventory(restored)
        observed['inventory'] = result
        return result
    monkeypatch.setattr(rehearsal, 'period_inventory', capture)
    capsys.readouterr()
    assert rehearsal.main() == 1
    assert observed['unchanged'] and snapshot(engine) == original
    inventory = observed['inventory']
    assert inventory['counts']['indicator_values'] == (2 if role else 1)
    assert inventory['counts']['import_batches'] == 1
    assert inventory['counts']['submission_events'] == (1 if role else 0)
    assert inventory['counts']['audit_log'] == (4 if role else 2)
    assert list(inventory['counts']) == sorted(inventory['counts'])
    report = assert_private_summary(tmp_path, capsys)
    assert '2026 PP yedek provası: FAIL' in report
    assert '2026 dönemi dolu' in report and '0 satır yazıldı' in report
    assert report.index('### 2026 dönemi envanteri') < report.index('| Aşama |')
    assert f'Kullanıcı girişi var mı: {answer}' in report
    assert 'Sıfır satırlı tablolar: ' in report
    assert 'actual_revisions' in report
    assert 'year=2026; value_kind=target; state=verified' in report
    assert 'status=applied; rol=strategy; sayı=1' in report
    assert 'created_at_ilk=2026-03-04 09:00 UTC' in report
    assert 'applied_at_son=2026-04-05 16:00 UTC' in report
    if role:
        expected_role = role if role in {'department', 'strategy', 'admin'} else 'other'
        assert f'event_type=submitted; rol={expected_role}; sayı=1' in report
        assert 'action=diğer;' in report
    for marker in (PRIVATE, 'CIV171-private', '987654321', '987.654.321', '@', 'https://'):
        assert marker not in report
    # All retained inventory fields are public aggregates too.
    assert PRIVATE not in json.dumps(inventory)


@pytest.mark.postgres
def test_inventory_uses_database_read_only_transaction(target):
    engine, ids = target
    pilot(engine, ids)
    transactions = []

    def after(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith('SET TRANSACTION READ ONLY'):
            cursor.execute('SHOW transaction_read_only')
            transactions.append(cursor.fetchone()[0])
    event.listen(engine, 'after_cursor_execute', after)
    try:
        rehearsal.period_inventory(engine)
    finally:
        event.remove(engine, 'after_cursor_execute', after)
    assert transactions == ['on']


@pytest.mark.postgres
def test_deep_report_evidence_and_both_link_parents_are_counted_once(db, sample):
    """Actual/evidence records sit beyond two hops; unrelated years stay out."""
    sample['period'].year = 2026
    db.flush()
    author = sample['user']
    pub = m.Publication(period_id=sample['period'].id, version=1, snapshot_json=PRIVATE,
                        sha256='a' * 64, created_by=sample['strategy'].id, created_at=FIRST)
    identity = m.IndicatorIdentity(indicator_id='inventory-identity',
                                   organization_id=sample['department'].organization_id)
    report = m.ActivityReport(organization_id=sample['department'].organization_id,
                              period_id=sample['period'].id)
    db.add_all([pub, identity, report])
    db.flush()
    definition = m.IndicatorDefinitionRevision(indicator_id=identity.indicator_id, revision=1,
        period_id=sample['period'].id, definition_json=PRIVATE, sha256='b' * 64,
        created_by=sample['strategy'].id, created_at=FIRST)
    revision = m.ActivityReportRevision(report_id=report.id, revision=1,
        publication_id=pub.id, publication_sha256=pub.sha256, created_by=author.id,
        diff_json=PRIVATE, revision_reason=PRIVATE, created_at=LAST)
    db.add_all([definition, revision])
    db.flush()
    binding = m.PublicationIndicatorBinding(publication_id=pub.id,
        snapshot_indicator_id=sample['indicator'].id, definition_revision_id=definition.id,
        department_id=sample['department'].id, created_by=author.id, reason=PRIVATE, created_at=LAST)
    db.add(binding)
    db.flush()
    indicator = m.ReportIndicator(report_revision_id=revision.id, publication_binding_id=binding.id)
    db.add(indicator)
    db.flush()
    actual = m.ActualRevision(report_indicator_id=indicator.id, revision=1, value=AMOUNT,
        raw_text=PRIVATE, state='needs_review', evidence_json=PRIVATE, explanation=PRIVATE,
        deviation_json=PRIVATE, created_by=author.id, created_at=LAST)
    db.add(actual)
    db.flush()
    db.add_all([
        m.ActivityReportApproval(report_revision_id=revision.id, created_by=sample['strategy'].id, created_at=LAST),
        m.ActivityEvidenceFile(actual_revision_id=actual.id, report_indicator_id=indicator.id,
            source_id='inventory-source', version=1, filename=PRIVATE, sha256='c' * 64,
            file_data=PRIVATE.encode(), created_by=author.id, created_at=LAST),
        m.AuditLog(user_id=author.id, action='actual_revision_create', entity_type='actual_revision',
                   entity_id=actual.id, details=PRIVATE, created_at=LAST),
        m.IndicatorValue(indicator_id=sample['indicator'].id, year=7654321, value_kind='CIV171-private-kind',
                         state='CIV171-private-state', raw_text=PRIVATE, value=AMOUNT),
        m.ReportingPeriod(year=2031, status='draft'),
    ])
    db.commit()
    inventory = rehearsal.period_inventory(db.get_bind())
    for name in ('actual_revisions', 'activity_evidence_files', 'report_indicators',
                 'activity_report_revisions', 'publication_indicator_bindings',
                 'activity_report_approvals', 'activity_catalogue_links', 'audit_log'):
        assert inventory['counts'][name] == 1
    assert inventory['counts']['reporting_periods'] == 1
    assert inventory['human'] is True
    assert inventory['groups']['actual_revisions'] == [{
        'state': 'needs_review', 'rol': 'department', 'sayı': 1,
        'created_at_ilk': '2026-04-05 16:00 UTC', 'created_at_son': '2026-04-05 16:00 UTC'}]
    output = '\n'.join(rehearsal.inventory_lines(inventory))
    assert 'year=diğer; value_kind=diğer; state=diğer' in output
    for marker in (PRIVATE, 'CIV171-private', '987654321', '7654321', 'inventory-identity'):
        assert marker not in output


@pytest.mark.postgres
@pytest.mark.parametrize('source,answer', [(None, True), ({'kind': 'first_load'}, False)])
def test_catalogue_audit_distinguishes_manual_and_import_origin(db, sample, source, answer):
    sample['period'].year = 2026
    db.add_all([
        m.AuditLog(user_id=sample['strategy'].id, action='catalogue_create',
            entity_type='official_activity', entity_id=sample['official'].id,
            details=json.dumps({'source': source, 'values': PRIVATE}), created_at=FIRST),
        m.AuditLog(user_id=sample['strategy'].id, action='catalogue_create',
            entity_type='official_activity', entity_id=sample['official'].id,
            details=json.dumps({'source': source, 'values': PRIVATE}), created_at=LAST),
    ])
    db.commit()
    inventory = rehearsal.period_inventory(db.get_bind())
    assert inventory['human'] is answer
    assert inventory['groups']['audit_log'] == [{
        'action': 'catalogue_create', 'rol': 'strategy', 'sayı': 2,
        'created_at_ilk': '2026-03-04 09:00 UTC', 'created_at_son': '2026-04-05 16:00 UTC'}]


def test_inventory_failure_is_reported_without_private_exception(tmp_path, monkeypatch, capsys):
    from pathlib import Path
    dispatch(monkeypatch, tmp_path)
    monkeypatch.setattr(rehearsal, 'download_verified_run', lambda _: (Path('unused'), {}))

    def broken(backup, record):
        record['phase'] = 'inventory'
        raise ValueError(PRIVATE)
    monkeypatch.setattr(rehearsal, 'rehearse', broken)
    assert rehearsal.main() == 1
    report = assert_private_summary(tmp_path, capsys)
    assert rehearsal.PHASES['inventory'] in report
    assert '### 2026 dönemi envanteri' in report
    assert 'Envanter alınamadı' in report


@pytest.mark.postgres
@pytest.mark.parametrize('action,answer', [
    ('CIV171-private-action', True), ('first_load_department', False),
    ('data_import_apply', False), ('activity_mapping_csv', False),
])
def test_audit_attribution_is_independent_of_private_action_label(db, sample, action, answer):
    sample['period'].year = 2026
    db.add(m.AuditLog(user_id=sample['user'].id, action=action,
        entity_type='indicator', entity_id=sample['indicator'].id, details=PRIVATE, created_at=FIRST))
    db.commit()
    inventory = rehearsal.period_inventory(db.get_bind())
    assert inventory['human'] is answer
    output = '\n'.join(rehearsal.inventory_lines(inventory))
    assert 'CIV171-private-action' not in output
    assert PRIVATE not in output
