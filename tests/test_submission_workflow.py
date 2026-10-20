from decimal import Decimal
from sqlalchemy import select, func
from app.models import Submission, SubmissionEvent, Notification, IndicatorValue, DepartmentCostValue
from app.main import app, require_user


def actor(sample, role):
    app.dependency_overrides[require_user] = lambda: sample[role]


def events(db):
    return db.scalars(select(SubmissionEvent).order_by(SubmissionEvent.id)).all()


def test_return_correct_resubmit_approve(client, db, sample):
    sub = db.scalar(select(Submission))
    path = f'/api/submissions/{sub.id}/decision?period_id=1'
    assert client.post('/api/departments/1/submit?period_id=1').json() == {'ok': True, 'revision': 1, 'period_id': 1, 'year': 2027, 'redirect_url': '/department/1?period_id=1'}
    db.refresh(sub)
    assert sub.status == 'submitted' and sub.submitted_at is not None
    original_snapshot = events(db)[0].snapshot_json
    assert client.post('/api/departments/1/submit?period_id=1').status_code == 409
    assert client.post('/api/indicators/1/save?period_id=1', json={'value_2027_target': '9'}).status_code == 409
    assert client.post(path, json={'decision': 'approve'}).status_code == 403
    actor(sample, 'strategy')
    assert client.post(path, json={'decision': 'return', 'note': '   '}).status_code == 422
    assert len(events(db)) == 1
    assert client.post(path, json={'decision': 'return', 'note': 'Hedefi düzeltin.'}).status_code == 200
    db.refresh(sub)
    assert sub.status == 'returned' and sub.return_note == 'Hedefi düzeltin.'
    assert sub.reviewed_at is not None and sub.revision == 1
    actor(sample, 'user')
    assert client.post('/api/indicators/1/save?period_id=1', json={'value_2027_target': '2,5'}).status_code == 200
    assert client.post('/api/departments/1/submit?period_id=1').json() == {'ok': True, 'revision': 2, 'period_id': 1, 'year': 2027, 'redirect_url': '/department/1?period_id=1'}
    db.refresh(sub)
    assert sub.status == 'submitted' and sub.return_note == ''
    assert events(db)[0].snapshot_json == original_snapshot
    assert events(db)[2].snapshot_json != original_snapshot
    actor(sample, 'strategy')
    assert client.post(path, json={'decision': 'approve'}).json() == {'ok': True, 'status': 'approved'}
    assert client.post(path, json={'decision': 'return', 'note': 'Tekrar'}).status_code == 409
    actor(sample, 'user')
    assert client.post('/api/departments/1/submit?period_id=1').status_code == 409
    assert client.post('/api/indicators/1/save?period_id=1', json={'value_2027_target': '9'}).status_code == 409
    db.expire_all()
    assert db.scalar(select(IndicatorValue)).value == Decimal('2.5')
    history = events(db)
    assert [(e.event_type, e.revision, e.actor_user_id) for e in history] == [
        ('submitted', 1, sample['user'].id), ('return', 1, sample['strategy'].id),
        ('submitted', 2, sample['user'].id), ('approve', 2, sample['strategy'].id),
    ]
    assert history[1].note == 'Hedefi düzeltin.'
    notices = db.scalars(select(Notification).order_by(Notification.id)).all()
    assert [(n.event_type, n.role, n.department_id) for n in notices] == [
        ('submission_submitted', 'strategy', None), ('submission_return', 'department', 1),
        ('submission_submitted', 'strategy', None), ('submission_approve', 'department', 1),
    ]


def test_invalid_submission_has_no_workflow_side_effects(client, db, sample):
    db.scalar(select(DepartmentCostValue)).state = 'needs_review'; db.commit()
    response = client.post('/api/departments/1/submit?period_id=1')
    assert response.status_code == 422 and response.json()['errors']
    db.expire_all()
    sub = db.scalar(select(Submission))
    assert sub.status == 'draft' and sub.revision == 0 and sub.submitted_at is None
    assert not events(db)
    assert db.scalar(select(func.count()).select_from(Notification)) == 0


def test_approval_revalidates_current_data(client, db, sample):
    assert client.post('/api/departments/1/submit?period_id=1').status_code == 200
    db.scalar(select(DepartmentCostValue)).state = 'needs_review'; db.commit()
    actor(sample, 'strategy')
    response = client.post('/api/submissions/1/decision?period_id=1', json={'decision': 'approve'})
    assert response.status_code == 409 and isinstance(response.json()['detail'], list)
    db.expire_all()
    assert db.scalar(select(Submission)).status == 'submitted'
    assert len(events(db)) == 1
    assert db.scalar(select(func.count()).select_from(Notification)) == 1
