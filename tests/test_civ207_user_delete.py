"""CIV-207: an account can be deleted only while nothing refers to it."""
import json

from sqlalchemy import select

from app.models import AuditLog, Notification, User
from app.authorization_models import NotificationRecipient
import pytest


@pytest.fixture
def strategy_client(client, sample):
    from app.main import app, require_user
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    return client


def _new_user(db, sample, email='silinecek@example.invalid'):
    u = User(email=email, full_name='Silinecek Sentetik', role='department', position='staff',
             department_id=sample['department'].id, password_hash='unused', is_active=True)
    db.add(u); db.commit()
    return u


def test_unused_account_is_listed_and_deleted_with_an_audit_row(strategy_client, db, sample):
    u = _new_user(db, sample)
    note = Notification(role='department', department_id=sample['department'].id, event_type='x', message='m')
    db.add(note); db.flush()
    db.add(NotificationRecipient(notification_id=note.id, user_id=u.id)); db.commit()
    uid = u.id
    assert uid in strategy_client.get('/api/users/deletable').json()['ids']
    r = strategy_client.post(f'/api/users/{uid}/delete')
    assert r.status_code == 200, r.text
    db.expire_all()
    assert db.get(User, uid) is None
    assert not db.scalars(select(NotificationRecipient).where(NotificationRecipient.user_id == uid)).all()
    row = db.scalars(select(AuditLog).where(AuditLog.action == 'user_delete', AuditLog.entity_id == uid)).one()
    assert json.loads(row.details)['email'] == 'silinecek@example.invalid'


def test_account_with_any_record_cannot_be_deleted(strategy_client, db, sample):
    u = _new_user(db, sample)
    db.add(AuditLog(user_id=u.id, action='login', entity_type='user', entity_id=u.id)); db.commit()
    assert u.id not in strategy_client.get('/api/users/deletable').json()['ids']
    r = strategy_client.post(f'/api/users/{u.id}/delete')
    assert r.status_code == 409
    assert 'Devre dışı bırak' in r.json()['detail']
    db.expire_all()
    assert db.get(User, u.id) is not None


def test_cannot_delete_self(strategy_client, db, sample):
    me = sample['strategy']
    assert me.id not in strategy_client.get('/api/users/deletable').json()['ids']
    assert strategy_client.post(f'/api/users/{me.id}/delete').status_code == 409


def test_department_users_cannot_delete(client, db, sample):
    u = _new_user(db, sample, 'baska@example.invalid')
    assert client.post(f'/api/users/{u.id}/delete').status_code in (401, 403)
    db.expire_all()
    assert db.get(User, u.id) is not None
