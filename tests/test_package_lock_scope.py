"""Real PostgreSQL lock boundaries for ordinary packages and corrections."""
import pytest
from sqlalchemy import event, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from app.models import DirectoratePackage, Organization, User
from app import package_service as packages
from tests.test_correction_reapproval import correction
from tests.test_revision_workflow import foundation_db, people, package, approved, candidate, released
from tests.test_package_workflow import act

pytestmark = pytest.mark.postgres


def prepare(db, x, p, action):
    if action in {'director_approve', 'strategy_approve'}:
        act(db, x, p, 'submit_to_director', 'user')
    if action == 'strategy_approve':
        act(db, x, p, 'director_approve')


def operate(db, actor, pid, action, version, sha):
    if action == 'edit_draft':
        p = db.get(DirectoratePackage, pid)
        path = ['cards', 0, 'goal'] if p.resource_scope == 'performance_program' else ['entries', 0, 'explanation']
        return packages.edit_package(db, actor, pid, version, sha,
                                     [{'path': path, 'value': 'Kaynakla doğrulanan açıklama'}])
    return packages.transition(db, actor, pid, action, version, sha)


@pytest.mark.parametrize('action', ['edit_draft', 'submit_to_director', 'director_approve', 'strategy_approve'])
def test_ordinary_operations_keep_phase3_lock_path(foundation_db, people, package, action):
    db = foundation_db; x = people; p = package
    prepare(db, x, p, action)
    pid, org = p.id, p.organization_id
    version, sha = p.version, packages.revision(db, p).sha256
    uid = x['strategy' if action == 'strategy_approve' else 'director' if action == 'director_approve' else 'user'].id
    db.commit()
    locks = []
    def record(conn, cursor, statement, parameters, context, many):
        if 'FOR UPDATE' in statement.upper():
            locks.append(statement.lower())
    engine = db.get_bind()
    # NO KEY UPDATE conflicts with explicit FOR UPDATE but permits the existing
    # foreign-key KEY SHARE taken when immutable audit rows are inserted.
    with Session(engine) as blocker:
        blocker.execute(select(Organization).where(Organization.id == org).with_for_update(key_share=True))
        event.listen(engine, 'before_cursor_execute', record)
        try:
            with Session(engine, expire_on_commit=False) as worker:
                worker.execute(text("SET LOCAL lock_timeout = '300ms'"))
                operate(worker, worker.get(User, uid), pid, action, version, sha)
                worker.commit()
        finally:
            event.remove(engine, 'before_cursor_execute', record)
            blocker.rollback()
    assert not any('from organizations' in sql for sql in locks)
    expected = ['departments', 'directorate_packages', 'users',
                'reporting_periods' if p.resource_scope == 'performance_program' else 'activity_reports']
    path = [next(table for table in expected if f'from {table}' in sql) for sql in locks]
    # Ordinary field edits also re-lock the department inside atomic_change.
    assert path == expected + (['departments'] if action == 'edit_draft' else [])
    db.expire_all()
    assert p.version == version + 1
    assert p.state == {'edit_draft': 'draft', 'submit_to_director': 'director_review',
                       'director_approve': 'strategy_review', 'strategy_approve': 'strategy_approved'}[action]


@pytest.mark.parametrize('action', ['submit_to_director', 'director_approve', 'strategy_approve'])
def test_correction_locks_organization_before_department(foundation_db, people, released, action):
    db = foundation_db; x = people
    p, rev, grant, request = correction(db, x, released)
    prepare(db, x, p, action)
    pid, org, version, sha = p.id, p.organization_id, p.version, rev.sha256
    uid = x['strategy' if action == 'strategy_approve' else 'director' if action == 'director_approve' else 'user'].id
    db.commit()
    locks = []
    def record(conn, cursor, statement, parameters, context, many):
        if 'FOR UPDATE' in statement.upper():
            locks.append(statement.lower())
    engine = db.get_bind()
    with Session(engine) as blocker:
        blocker.execute(select(Organization).where(Organization.id == org).with_for_update(key_share=True))
        event.listen(engine, 'before_cursor_execute', record)
        try:
            with Session(engine) as worker:
                worker.execute(text("SET LOCAL lock_timeout = '300ms'"))
                with pytest.raises(DBAPIError) as caught:
                    operate(worker, worker.get(User, uid), pid, action, version, sha)
                assert caught.value.orig.sqlstate == '55P03'
                worker.rollback()
        finally:
            event.remove(engine, 'before_cursor_execute', record)
            blocker.rollback()
    assert len(locks) == 1 and 'from organizations' in locks[0]
    db.expire_all()
    assert p.version == version
    # Once the organization lock is released, the same exact operation succeeds.
    operate(db, db.get(User, uid), pid, action, version, sha)
    db.commit()
    assert p.version == version + 1


def test_correction_submission_vs_grant_edit_serializes(foundation_db, people, released):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from app import revision_workflow_service as corrections, authorization_service as auth
    from tests.test_revision_workflow import address
    db = foundation_db; x = people
    p, rev, grant, request = correction(db, x, released)
    pid, uid, gid = p.id, x['user'].id, grant.id
    version, sha, path = p.version, rev.sha256, address(released)
    db.commit()
    barrier = Barrier(2)
    def run(action):
        with Session(db.get_bind(), expire_on_commit=False) as worker:
            worker.execute(text("SET LOCAL lock_timeout = '3s'"))
            actor = worker.get(User, uid)
            barrier.wait(timeout=5)
            try:
                if action == 'edit':
                    corrections.edit_under_grant(worker, actor, gid, version, sha,
                                                 [{'path': path, 'value': '3.25'}])
                else:
                    packages.transition(worker, actor, pid, 'submit_to_director', version, sha)
                worker.commit()
                return 1
            except auth.HTTPException as exc:
                worker.rollback()
                return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(run, ['edit', 'submit'])) == [1, 409]
    db.expire_all()
    assert p.version == version + 1 and p.state in {'returned', 'director_review'}
