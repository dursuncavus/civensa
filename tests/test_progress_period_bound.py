"""CIV-177: progress audits belong to the selected reporting period."""
from datetime import datetime

import pytest
from sqlalchemy import event, select

from app.main import app, department_progress_overview, require_user
from app.models import (
    AuditLog, DepartmentScope, ReportingPeriod, Submission, User,
)

pytestmark = pytest.mark.postgres


@pytest.fixture
def other_period(db, sample):
    period = ReportingPeriod(year=2026, status='draft')
    db.add(period)
    db.flush()
    db.add_all([
        DepartmentScope(period_id=period.id, department_id=sample['department'].id, status='required'),
        Submission(period_id=period.id, department_id=sample['department'].id, status='draft'),
    ])
    db.commit()
    return period


def progress(db, period):
    return department_progress_overview(db, period)['rows'][0]


def assert_not_started(db, period):
    result = progress(db, period)
    assert result['state'] == 'not_started'
    assert result['label'] == 'Başlamadı'
    assert result['progress_percent'] == 0
    assert result['last_activity_at'] is None


@pytest.mark.parametrize('action', [
    'indicator_update', 'personnel_cost_update', 'department_submit',
    'activity_create', 'activity_update',
])
def test_each_progress_action_is_period_bound(db, sample, other_period, action):
    submission = db.scalar(select(Submission).where(Submission.period_id == sample['period'].id))
    entity_type, entity_id = {
        'indicator_update': ('indicator', sample['indicator'].id),
        'personnel_cost_update': ('department', sample['department'].id),
        'department_submit': ('submission', submission.id),
        'activity_create': ('activity', sample['activity'].id),
        'activity_update': ('activity', sample['activity'].id),
    }[action]
    timestamp = datetime(2026, 9, 21, 12, 30)
    db.add(AuditLog(user_id=sample['user'].id, action=action,
        entity_type=entity_type, entity_id=entity_id, created_at=timestamp,
        details=f"period_id={sample['period'].id}" if action == 'personnel_cost_update' else ''))
    db.commit()
    assert_not_started(db, other_period)
    result = progress(db, sample['period'])
    assert result['state'] == 'ready'
    assert result['last_activity_at'] == timestamp.isoformat()


def test_real_edits_and_submit_do_not_start_another_period(client, db, sample, other_period):
    period = sample['period']
    department_id = sample['department'].id
    assert client.post(f"/api/indicators/{sample['indicator'].id}/save?period_id={period.id}",
        json={'explanation': 'Dönem A düzenlemesi'}).status_code == 200
    assert client.post(f'/api/departments/{department_id}/personnel-costs?period_id={period.id}',
        json={'cost_2027_budget': '20,00'}).status_code == 200
    personnel_audit = db.scalar(select(AuditLog).where(AuditLog.action == 'personnel_cost_update'))
    assert personnel_audit.details == f'period_id={period.id}'
    assert progress(db, period)['state'] == 'ready'
    assert_not_started(db, other_period)
    assert client.post(f'/api/departments/{department_id}/submit?period_id={period.id}').status_code == 200
    submitted = db.scalar(select(AuditLog).where(AuditLog.action == 'department_submit'))
    result = progress(db, period)
    assert result['state'] == 'submitted'
    assert result['last_activity_at'] == submitted.created_at.isoformat()
    assert_not_started(db, other_period)

    app.dependency_overrides[require_user] = lambda: sample['strategy']
    response = client.get(f'/dashboard?period_id={other_period.id}')
    assert response.status_code == 200
    table = response.text.split('id="mudurluk-ilerleme"', 1)[1].split('<table>', 1)[1].split('</table>', 1)[0]
    assert 'Başlamadı' in table
    assert '<td>—</td>' in table


@pytest.mark.parametrize('details', ['', 'period_id=999', 'period_id=10'])
def test_unscoped_or_other_personnel_audits_start_no_period(db, sample, other_period, details):
    audit = AuditLog(user_id=sample['user'].id, action='personnel_cost_update',
        entity_type='department', entity_id=sample['department'].id, details=details)
    db.add(audit)
    db.commit()
    original = (audit.id, audit.details, audit.created_at)
    for period in (sample['period'], other_period):
        assert_not_started(db, period)
    db.refresh(audit)
    assert (audit.id, audit.details, audit.created_at) == original


def test_audit_sql_filters_actions_users_and_period_entities(db, sample, other_period):
    inactive = User(email='inactive@example.invalid', full_name='Pasif', role='department',
        password_hash='unused', department_id=sample['department'].id, is_active=False)
    unassigned = User(email='unassigned@example.invalid', full_name='Atanmamış', role='department',
        password_hash='unused')
    db.add_all([inactive, unassigned])
    db.flush()
    for actor in (sample['user'], sample['strategy'], inactive, unassigned):
        for action, entity_type, entity_id, details in [
            ('indicator_update', 'indicator', sample['indicator'].id, ''),
            ('personnel_cost_update', 'department', sample['department'].id, ''),
            ('personnel_cost_update', 'department', sample['department'].id, f"period_id={other_period.id}0"),
            ('department_submit', 'submission', db.scalar(select(Submission.id).where(
                Submission.period_id == sample['period'].id)), ''),
            ('activity_update', 'activity', sample['activity'].id, ''),
            ('login', 'user', actor.id, ''),
        ]:
            db.add(AuditLog(user_id=actor.id, action=action, entity_type=entity_type,
                entity_id=entity_id, details=details))
    db.commit()
    db.expunge_all()
    queries, loaded = [], []

    def capture_sql(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith('SELECT') and 'audit_log' in statement:
            queries.append(statement.lower())

    def capture_load(session, instance):
        if isinstance(instance, AuditLog):
            loaded.append(instance)

    event.listen(db.get_bind(), 'before_cursor_execute', capture_sql)
    event.listen(db, 'loaded_as_persistent', capture_load)
    try:
        assert_not_started(db, other_period)
    finally:
        event.remove(db.get_bind(), 'before_cursor_execute', capture_sql)
        event.remove(db, 'loaded_as_persistent', capture_load)
    assert len(queries) == 1
    query = queries[0]
    assert 'audit_log.action in (' in query
    assert 'audit_log.user_id in (' in query
    assert 'audit_log.entity_id in (' in query
    assert 'audit_log.details =' in query
    assert not loaded, 'Unrelated audits must be excluded by SQL, before ORM loading'
