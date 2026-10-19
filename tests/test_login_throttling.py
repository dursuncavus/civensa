"""CIV-006: real PostgreSQL login limits, concurrency and additive migration."""
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
import json
import os
import secrets
import subprocess
import sys
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select, text
from sqlalchemy.orm import Session
from starlette.requests import Request

from app import login_throttling as throttle, main
from app.db import get_db
from app.models import AuditLog, LoginAttempt, User
from app.security import hash_password
from tests.test_authorization_foundation import ROOT, foundation_db, people

pytestmark = pytest.mark.postgres
NOW = datetime(2026, 10, 13, 12, tzinfo=UTC)
BASE_REVISION = "f2b7c4d91e08"
REVISION = "a6c006e9b241"


@pytest.fixture
def clock(monkeypatch):
    value = [NOW]
    monkeypatch.setattr(throttle, "server_now", lambda db: value[0])
    return value


@pytest.fixture
def browsers(db, sample):
    credential = secrets.token_urlsafe(24)
    sample["user"].password_hash = hash_password(credential)
    sample["strategy"].password_hash = hash_password(credential)
    db.commit()
    main.app.dependency_overrides[get_db] = lambda: db
    clients = []

    def make(ip="192.0.2.1"):
        client = TestClient(main.app, follow_redirects=False, client=(ip, 12345))
        clients.append(client)
        return client

    yield make, credential
    for client in clients:
        client.close()
    main.app.dependency_overrides.clear()


def submit(browser, email, credential=None, **kwargs):
    return browser.post("/login", data={"email": email, "password": credential or secrets.token_urlsafe(24)}, **kwargs)


def attempts(db):
    return db.scalars(select(LoginAttempt).order_by(LoginAttempt.id)).all()


def lock_audits(db):
    return db.scalars(select(AuditLog).where(AuditLog.action == "login_throttle_lock")).all()


def test_email_locks_at_five_and_correct_password_is_refused(db, sample, browsers, clock):
    make, credential = browsers
    browser = make()
    email = sample["user"].email
    for index in range(5):
        # Case/whitespace variations must share the same identity.
        response = submit(browser, "  " + email.upper() + "  ")
        assert response.status_code == 400
        assert (throttle.LOCK_MESSAGE in response.text) == (index == 4)
    assert len(attempts(db)) == 5
    # A different IP/new client still sees the persisted e-mail lock.
    response = submit(make("192.0.2.2"), email, credential)
    assert response.status_code == 400 and throttle.LOCK_MESSAGE in response.text
    assert not browser.cookies.get("session")
    assert make().get("/modules").status_code != 200
    assert len(attempts(db)) == 5
    audit, = lock_audits(db)
    assert audit.user_id is None and audit.entity_id is None
    details = json.loads(audit.details)
    assert details == {"scope": "email", "key_sha256": throttle.identity_key("email", email),
                       "failure_limit": 5, "locked_until": (NOW + throttle.WINDOW).isoformat()}
    assert email not in audit.details and credential not in audit.details


def test_email_lock_persists_in_a_fresh_database_session(db, sample, browsers, clock):
    make, credential = browsers
    email = sample["user"].email
    for _ in range(5):
        submit(make(), email)
    with Session(db.get_bind()) as fresh:
        request = Request({"type": "http", "method": "POST", "path": "/login",
                           "headers": [], "scheme": "http", "server": ("testserver", 80),
                           "client": ("192.0.2.2", 12345), "session": {}})
        response = main.login(request, email, credential, fresh)
        assert response.status_code == 400 and throttle.LOCK_MESSAGE.encode() in response.body
        assert not request.session
    assert len(attempts(db)) == 5 and len(lock_audits(db)) == 1


def test_email_unlocks_at_exact_expiry_without_extending_lock(db, sample, browsers, clock):
    make, credential = browsers
    browser = make()
    email = sample["user"].email
    for _ in range(4):
        submit(browser, email)
    clock[0] += timedelta(minutes=14)
    submit(browser, email)
    expiry = clock[0] + throttle.WINDOW
    clock[0] = expiry - timedelta(microseconds=1)
    assert submit(browser, email, credential).status_code == 400
    assert len(attempts(db)) == 5 and len(lock_audits(db)) == 1
    clock[0] = expiry
    assert submit(browser, email, credential).status_code == 303


def test_failures_use_a_rolling_window(db, sample, browsers, clock):
    make, credential = browsers
    browser = make()
    email = sample["user"].email
    for _ in range(4):
        submit(browser, email)
    clock[0] += throttle.WINDOW
    response = submit(browser, email)
    assert response.status_code == 400 and throttle.LOCK_MESSAGE not in response.text
    assert not lock_audits(db)
    assert submit(browser, email, credential).status_code == 303


def test_success_resets_only_email_count(db, sample, browsers, clock):
    make, credential = browsers
    browser = make()
    email = sample["user"].email
    for _ in range(4):
        submit(browser, email)
    assert submit(browser, email, credential).status_code == 303
    assert all(row.email_cleared for row in attempts(db))
    for _ in range(4):
        response = submit(browser, email)
        assert throttle.LOCK_MESSAGE not in response.text
    submit(browser, email)
    assert len(attempts(db)) == 9
    assert len(lock_audits(db)) == 1


def test_ip_limit_is_disabled_by_default_but_ip_keys_are_recorded(db, sample, browsers, clock, monkeypatch):
    monkeypatch.delenv("CIVENSA_LOGIN_IP_LIMIT", raising=False)
    make, credential = browsers
    browser = make()
    for index in range(25):
        response = submit(browser, f"unknown-{index}@example.invalid")
        assert response.status_code == 400 and throttle.LOCK_MESSAGE not in response.text
    assert submit(browser, sample["strategy"].email, credential).status_code == 303
    assert len(attempts(db)) == 25
    assert not lock_audits(db)
    assert {row.ip_key for row in attempts(db)} == {throttle.identity_key("ip", "192.0.2.1")}


def test_ip_limit_survives_success_and_blocks_other_email(db, sample, browsers, clock, monkeypatch):
    monkeypatch.setenv("CIVENSA_LOGIN_IP_LIMIT", "20")
    make, credential = browsers
    browser = make()
    email = sample["user"].email
    for index in range(19):
        response = submit(browser, f"unknown-{index}@example.invalid")
        assert throttle.LOCK_MESSAGE not in response.text
    assert submit(browser, email, credential).status_code == 303
    response = submit(browser, "twentieth@example.invalid")
    assert response.status_code == 400 and throttle.LOCK_MESSAGE in response.text
    assert submit(browser, email, credential).status_code == 400
    assert len(attempts(db)) == 20
    assert [json.loads(row.details)["scope"] for row in lock_audits(db)] == ["ip"]
    # The IP lock does not affect another address; it expires after 15 minutes.
    assert submit(make("192.0.2.2"), email, credential).status_code == 303
    clock[0] += throttle.WINDOW
    assert submit(browser, email, credential).status_code == 303


@pytest.mark.parametrize("identity", ["known", "unknown", "inactive"])
def test_all_identities_share_failure_status_timing_work_and_limits(db, sample, browsers, clock, monkeypatch, identity):
    make, credential = browsers
    browser = make()
    user = sample["user"]
    email = user.email if identity != "unknown" else "absent@example.invalid"
    if identity == "inactive":
        user.is_active = False
        db.commit()
    checked = []
    original = main.verify_password

    def verify(candidate, stored):
        checked.append(stored)
        return original(candidate, stored)

    monkeypatch.setattr(main, "verify_password", verify)
    for index in range(5):
        response = submit(browser, email)
        assert response.status_code == 400
        assert (throttle.LOCK_MESSAGE in response.text) == (index == 4)
    response = submit(browser, email, credential)
    assert response.status_code == 400 and throttle.LOCK_MESSAGE in response.text
    assert len(checked) == 6
    assert all(stored.startswith("pbkdf2_sha256$") for stored in checked)
    assert checked[-1] == throttle.DUMMY_PASSWORD_HASH
    assert len(attempts(db)) == 5 and len(lock_audits(db)) == 1


def test_forwarded_header_cannot_change_ip_bucket(db, browsers, clock, monkeypatch):
    monkeypatch.setenv("CIVENSA_LOGIN_IP_LIMIT", "20")
    make, _ = browsers
    browser = make()
    for index in range(20):
        submit(browser, f"absent-{index}@example.invalid", headers={"X-Forwarded-For": f"198.51.100.{index}"})
    response = submit(browser, "another@example.invalid", headers={"X-Forwarded-For": "203.0.113.1"})
    assert response.status_code == 400 and throttle.LOCK_MESSAGE in response.text
    assert {row.ip_key for row in attempts(db)} == {throttle.identity_key("ip", "192.0.2.1")}


def test_cleanup_runs_even_on_locked_login_and_preserves_audit(db, sample, browsers, clock):
    make, credential = browsers
    browser = make()
    email = sample["user"].email
    for _ in range(5):
        submit(browser, email)
    db.add_all([
        LoginAttempt(email_key="old", ip_key="old", failed_at=NOW - throttle.RETENTION - timedelta(microseconds=1)),
        LoginAttempt(email_key="boundary", ip_key="boundary", failed_at=NOW - throttle.RETENTION),
    ])
    db.commit()
    assert submit(browser, email, credential).status_code == 400
    assert len(attempts(db)) == 6
    assert "old" not in {row.email_key for row in attempts(db)}
    assert len(lock_audits(db)) == 1


@pytest.mark.parametrize("scope,prior", [("email", 0), ("email", 3), ("email", 4), ("ip", 18), ("ip", 19)])
def test_concurrent_failures_count_once_per_attempt(db, sample, browsers, clock, scope, prior, monkeypatch):
    if scope == "ip":
        monkeypatch.setenv("CIVENSA_LOGIN_IP_LIMIT", "20")
    make, _ = browsers
    browser = make()
    email = sample["user"].email
    for index in range(prior):
        submit(browser, email if scope == "email" else f"prior-{index}@example.invalid")
    # End the reader's transaction before two independent connections enter.
    db.commit()
    barrier = Barrier(2)

    def fail(index):
        with Session(db.get_bind()) as worker:
            request = Request({"type": "http", "method": "POST", "path": "/login",
                               "headers": [], "scheme": "http", "server": ("testserver", 80),
                               "client": ("192.0.2.1" if scope == "ip" else f"192.0.2.{index + 2}", 12345),
                               "session": {}})
            barrier.wait(timeout=10)
            response = main.login(request, email if scope == "email" else f"worker-{index}@example.invalid",
                                  secrets.token_urlsafe(24), worker)
            return response.status_code, throttle.LOCK_MESSAGE.encode() in response.body

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(fail, range(2)))
    db.expire_all()
    limit = throttle.EMAIL_LIMIT if scope == "email" else 20
    assert all(status == 400 for status, _ in results)
    assert len(attempts(db)) == min(prior + 2, limit)
    assert len(lock_audits(db)) == int(prior + 2 >= limit)
    assert sum(locked for _, locked in results) == (2 if prior + 1 == limit else int(prior + 2 >= limit))


@pytest.mark.parametrize("foundation_db", [BASE_REVISION], indirect=True)
def test_one_additive_migration_and_downgrade_preserves_other_tables(foundation_db):
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    db = foundation_db
    scripts = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    assert len(scripts.get_heads()) == 1
    assert REVISION in {r.revision for r in scripts.iterate_revisions('head', BASE_REVISION)}
    assert scripts.get_revision(REVISION).down_revision == BASE_REVISION
    before_tables = set(inspect(db.bind).get_table_names())
    # Seed the exact historical schema, before CIV-025's User columns exist.
    db.execute(text("INSERT INTO users (email, full_name, role, password_hash, is_active) "
                    "VALUES ('migration@example.invalid', 'Strateji', 'strategy', 'unused', true)"))
    db.commit()
    before_users = db.execute(select(User.id, User.email, User.password_hash)).all()
    db.add(AuditLog(action="migration_probe", entity_type="test", details="Korunacak kayıt"))
    db.commit()
    before_audits = db.execute(select(AuditLog.id, AuditLog.details)).all()
    db.commit()
    env = {**os.environ, "DATABASE_URL": db.bind.url.render_as_string(hide_password=False)}

    def migrate(action, revision):
        result = subprocess.run([sys.executable, "-m", "alembic", action, revision], cwd=ROOT,
                                env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr

    # Exercise this historical migration independently of later additions.
    migrate("upgrade", REVISION)
    assert set(inspect(db.bind).get_table_names()) == before_tables | {"login_attempts"}
    assert {index["name"] for index in inspect(db.bind).get_indexes("login_attempts")} == {
        "ix_login_attempts_email_time", "ix_login_attempts_ip_time", "ix_login_attempts_failed_at"}
    db.add(LoginAttempt(email_key="test", ip_key="test", failed_at=NOW))
    db.commit()
    migrate("downgrade", BASE_REVISION)
    assert set(inspect(db.bind).get_table_names()) == before_tables
    assert db.execute(select(User.id, User.email, User.password_hash)).all() == before_users
    assert db.execute(select(AuditLog.id, AuditLog.details)).all() == before_audits
    db.commit()
    migrate("upgrade", REVISION)
    assert db.scalar(select(func.count(LoginAttempt.id))) == 0
