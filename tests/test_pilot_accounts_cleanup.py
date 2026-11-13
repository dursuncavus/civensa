"""CIV-222: pinned pilot account cleanup; local PG only."""
import json

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models as m
from scripts import pilot_accounts_cleanup as cleanup
from scripts.first_load_dryrun import local_test_url
from tests.first_load_checkpoint import disposable_first_load_database


def seed(engine, *, extra=False, used_delete=False):
    pinned = {}
    with Session(engine) as db:
        org = m.Organization(name='CIV-222 disposable')
        db.add(org)
        db.flush()
        dept = m.Department(organization_id=org.id, name='Bilgi İşlem Müdürlüğü')
        strat = m.Department(organization_id=org.id, name='Strateji Geliştirme Müdürlüğü')
        db.add_all([dept, strat])
        db.flush()
        for uid in range(1, 41):
            email = f'user{uid}@civensa.local'
            strategy = uid in cleanup.KEEP
            db.add(m.User(id=uid, email=email, full_name=f'Kişi {uid}', password_hash='x',
                          role='strategy' if strategy else 'department',
                          department_id=strat.id if strategy else dept.id,
                          position='director' if uid in (36, 39) else 'staff',
                          is_active=uid not in (37, 38)))
            if uid not in (37, 38):
                pinned[uid] = cleanup.email_hash(email)
        if extra:
            db.add(m.User(id=41, email='new@civensa.local', full_name='Yeni', password_hash='x', role='department',
                          department_id=dept.id))
        db.flush()
        for uid in range(2, 36):
            db.add(m.AuditLog(user_id=uid, action='login', entity_type='user', entity_id=uid))
        if used_delete:
            db.add(m.AuditLog(user_id=39, action='login', entity_type='user', entity_id=39))
        db.commit()
    return pinned


@pytest.fixture
def engine(monkeypatch):
    with disposable_first_load_database(local_test_url()) as engine:
        yield engine


def run(engine, monkeypatch, pinned, **kw):
    monkeypatch.setattr(cleanup, 'PINNED', pinned)
    return cleanup.execute(engine, actor_id=1, **kw)


def state(engine):
    with Session(engine) as db:
        users = {u.id: u.is_active for u in db.scalars(select(m.User))}
        actions = dict(db.execute(select(m.AuditLog.action, func.count()).group_by(m.AuditLog.action)).all())
    return users, actions


def test_plan_writes_nothing_and_apply_deletes_four_and_deactivates_34(engine, monkeypatch):
    pinned = seed(engine)
    before = state(engine)
    plan = run(engine, monkeypatch, pinned)
    assert state(engine) == before
    assert len(plan['delete']) == 2 and len(plan['deactivate']) == 34
    assert 'Hedefe 0 satır yazıldı' in cleanup.format_summary(plan)

    run(engine, monkeypatch, pinned, apply=True, confirmation=cleanup.CONFIRMATION)
    users, actions = state(engine)
    assert set(users) == set(range(1, 39))
    assert not users[37] and not users[38]
    assert users[1] and users[36]
    assert not any(users[u] for u in range(2, 36))
    assert actions['user_delete'] == 2 and actions['user_deactivate'] == 34 and actions[cleanup.ACTION] == 1
    with Session(engine) as db:
        detail = json.loads(db.scalar(select(m.AuditLog.details).where(m.AuditLog.action == 'user_delete',
                                                                        m.AuditLog.entity_id == 39)))
    assert detail['email'] == 'user39@civensa.local' and 'password_hash' not in detail


def test_unexpected_account_refuses_without_writing(engine, monkeypatch):
    pinned = seed(engine, extra=True)
    before = state(engine)
    with pytest.raises(cleanup.live.Refusal, match='Hesap listesi'):
        run(engine, monkeypatch, pinned, apply=True, confirmation=cleanup.CONFIRMATION)
    assert state(engine) == before


def test_changed_email_refuses(engine, monkeypatch):
    pinned = seed(engine)
    pinned[12] = '0' * 16
    with pytest.raises(cleanup.live.Refusal, match='Hesap 12'):
        run(engine, monkeypatch, pinned)


def test_delete_candidate_with_records_refuses(engine, monkeypatch):
    pinned = seed(engine, used_delete=True)
    before = state(engine)
    with pytest.raises(cleanup.live.Refusal, match='kaydı olan'):
        run(engine, monkeypatch, pinned, apply=True, confirmation=cleanup.CONFIRMATION)
    assert state(engine) == before


def test_wrong_phrase_and_wrong_actor_refuse(engine, monkeypatch):
    pinned = seed(engine)
    with pytest.raises(cleanup.live.Refusal, match='Onay'):
        run(engine, monkeypatch, pinned, apply=True, confirmation='evet')
    monkeypatch.setattr(cleanup, 'PINNED', pinned)
    with pytest.raises(cleanup.live.Refusal, match='actor-id'):
        cleanup.execute(engine, actor_id=12)
