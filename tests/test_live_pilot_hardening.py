"""A1-P0 live pilot hardening: A1-F4, A1-F9, A1-F10 and A1-F11a regressions."""
import ast
import csv
import io
import json
import re
import socket
import threading
import time
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

from app.csv_safety import csv_text, csv_row, csv_cell_matches
from app.models import Activity, AuditLog, Department, IndicatorValue, Submission, SubmissionEvent, User
from app.security import hash_password

BACKENDS = ['sqlite', pytest.param('postgres', marks=pytest.mark.postgres)]
PASSWORD = 'Eski-Parola-2027'
NEW_PASSWORD = 'Yeni-Parola-2027!'
CSRF_RE = re.compile(r'name="csrf_token" value="([^"]+)"')


@pytest.fixture
def live_client(db, sample):
    """Real login, session and CSRF: only the database dependency is replaced."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import get_db

    def database():
        yield db
    app.dependency_overrides[get_db] = database
    for item in db.scalars(select(User)).all():
        item.password_hash = hash_password(PASSWORD)
    db.commit()
    clients = []

    def make():
        client = TestClient(app, follow_redirects=False)
        clients.append(client)
        return client
    yield make
    for client in clients:
        client.close()
    app.dependency_overrides.clear()


def login(client, email, password=PASSWORD, *, expected_path="/modules"):
    response = client.post('/login', data={'email': email, 'password': password})
    assert response.status_code == 303 and response.headers['location'] == expected_path, response.text
    page = client.get(expected_path)
    assert page.status_code == 200
    return CSRF_RE.search(page.text).group(1)


def replay(make, cookie):
    """A client holding a copy of a captured cookie (a rejected request clears the original jar)."""
    client = make()
    client.cookies.set('session', cookie)
    return client


def add_user(db, sample, email):
    user = User(email=email, full_name='İkinci Kullanıcı', role='department',
                department_id=sample['department'].id, password_hash=hash_password(PASSWORD))
    db.add(user); db.commit()
    return user


def indicator_value(db):
    db.expire_all()
    return db.scalar(select(IndicatorValue).where(IndicatorValue.year == 2027, IndicatorValue.value_kind == 'target')).value


# --------------------------------------------------------------------------- A1-F9 CSV

@pytest.mark.parametrize('prefix', ['=', '+', '-', '@', '\t', '\r'])
def test_csv_text_neutralises_every_formula_prefix(prefix):
    value = prefix + 'HYPERLINK("http://evil.invalid","x")'
    assert csv_text(value) == "'" + value


@pytest.mark.parametrize('value', ['Park bakımı', 'Çevre, Şehircilik "Müdürlüğü"', 'satır 1\nsatır 2',
                                   "'zaten tırnaklı", ' =boşlukla başlıyor', '2027-01-01 10:00:00', '', 'İĞÜŞÖÇığüşöç'])
def test_csv_text_leaves_ordinary_text_unchanged(value):
    assert csv_text(value) == value


@pytest.mark.parametrize('value,expected', [
    ('a;=1+1', "a;'=1+1"), ('Park; -bakım', "Park;' -bakım"), ('x;"@SUM(A1)"', 'x;\'"@SUM(A1)"'),
    ('Kırsal; yol; bakım', 'Kırsal; yol; bakım'), ('=a;+b', "'=a;'+b"),
    ('Park bakımı\n=HYPERLINK("http://evil.invalid")', 'Park bakımı\n\'=HYPERLINK("http://evil.invalid")'),
    ('a\r\n-x', "a\r\n'-x"), ('satır 1\nsatır 2', 'satır 1\nsatır 2')])
def test_csv_text_guards_cells_a_semicolon_locale_would_split(value, expected):
    """tr-TR Excel splits on ';' and on line breaks: no resulting part may start a formula."""
    guarded = csv_text(value)
    assert guarded == expected
    assert not any(part.lstrip(' "').startswith(('=', '+', '-', '@', '\t'))
                   for part in re.split(r'[;\r\n]', guarded))


def test_csv_row_keeps_typed_numbers_numeric_and_guards_text():
    row = csv_row([-5, Decimal('-12.50'), -0.25, 0, '-5', None, '=1+1'])
    assert row == [-5, Decimal('-12.50'), -0.25, 0, "'-5", '', "'=1+1"]
    out = io.StringIO(); csv.writer(out).writerow(row)
    assert out.getvalue() == "-5,-12.50,-0.25,0,'-5,,'=1+1\r\n"


def test_csv_writer_quoting_round_trips_guarded_text():
    cells = csv_row(['=a,"b"\nc', 'Şişli, "Kâğıthane"', '@SUM(A1)'])
    out = io.StringIO(); csv.writer(out).writerow(cells)
    assert next(csv.reader(io.StringIO(out.getvalue()))) == ["'=a,\"b\"\nc", 'Şişli, "Kâğıthane"', "'@SUM(A1)"]


def test_csv_cell_matches_accepts_raw_and_guarded_form_only():
    assert csv_cell_matches('-Park', '-Park') and csv_cell_matches("'-Park", '-Park')
    assert csv_cell_matches(' Park ', 'Park')
    assert not csv_cell_matches("'Park", 'Park') and not csv_cell_matches('Bahçe', 'Park')


def test_every_csv_writer_in_app_uses_the_shared_guard():
    """Every csv writer row in the live application must pass through csv_row()."""
    app_dir = Path(__file__).resolve().parent.parent / 'app'
    unguarded, writers = [], 0
    for path in sorted(app_dir.glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {'writerow', 'writerows'}:
                writers += 1
                arg = node.args[0] if node.args else None
                if not (isinstance(arg, ast.Call) and getattr(arg.func, 'id', '') == 'csv_row'):
                    unguarded.append(f'{path.name}:{node.lineno}')
            if isinstance(node, ast.Attribute) and node.attr == 'DictWriter':
                unguarded.append(f'{path.name}:{node.lineno} DictWriter')
    assert writers >= 6 and not unguarded, unguarded


def read_csv(response):
    assert response.status_code == 200 and response.headers['content-type'].startswith('text/csv')
    return list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))


@pytest.mark.parametrize('backend', BACKENDS)
def test_mapping_export_is_guarded_and_still_reimports(backend, live_client, db, sample):
    activity = db.get(Activity, sample['activity'].id)
    activity.name = '=HYPERLINK("http://evil.invalid","Tıkla")'
    activity.subprogram_id = None
    db.get(Department, sample['department'].id).name = '-Sağlık İşleri'
    db.commit()
    strategy = live_client(); csrf = login(strategy, sample['strategy'].email)
    rows = read_csv(strategy.get('/api/activity-mappings/export.csv'))
    assert rows[1][0] == "'-Sağlık İşleri" and rows[1][1] == str(activity.id)
    assert rows[1][2] == "'" + activity.name
    # The guarded file is filled in and re-imported unchanged: names still match.
    rows[1][6] = f"{sample['subprogram'].program.name} / {sample['subprogram'].name}"
    out = io.StringIO(); csv.writer(out).writerows(rows)
    response = strategy.post('/api/activity-mappings/import-preview?period_id=1', headers={'X-CSRF-Token': csrf},
                             files={'file': ('kuyruk.csv', out.getvalue().encode('utf-8'), 'text/csv')})
    assert response.status_code == 200, response.text
    assert response.json()['ok'] and response.json()['count'] == 1, response.json()


@pytest.mark.parametrize('backend', BACKENDS)
def test_mapping_import_accepts_a_guarded_selection_only(backend, live_client, db, sample):
    program = sample['subprogram'].program
    program.name = '=Program'
    db.get(Activity, sample['activity'].id).subprogram_id = None
    db.commit()
    strategy = live_client(); csrf = login(strategy, sample['strategy'].email)
    rows = read_csv(strategy.get('/api/activity-mappings/export.csv'))

    def preview(selection):
        rows[1][6] = selection
        out = io.StringIO(); csv.writer(out).writerows(rows)
        return strategy.post('/api/activity-mappings/import-preview?period_id=1', headers={'X-CSRF-Token': csrf},
                             files={'file': ('kuyruk.csv', out.getvalue().encode('utf-8'), 'text/csv')}).json()
    guarded = f"'=Program / {sample['subprogram'].name}"
    assert preview(guarded)['ok'] and preview(guarded)['count'] == 1
    assert preview(guarded[1:])['count'] == 1  # the raw form keeps working
    rejected = preview("''=Program / " + sample['subprogram'].name)
    assert not rejected['ok'] and 'Seçilen Program / Alt Program' in rejected['errors'][0]


@pytest.mark.parametrize('backend', BACKENDS)
def test_account_csv_round_trip_with_a_guarded_department_name(backend, live_client, db, sample):
    db.get(Department, sample['department'].id).name = '+Fen İşleri'
    db.get(User, sample['user'].id).is_active = False
    db.commit()
    strategy = live_client(); csrf = login(strategy, sample['strategy'].email)
    rows = read_csv(strategy.get('/api/users/missing-departments.csv'))

    def preview(department_name):
        rows[1][1:5] = [department_name, 'Yeni Kullanıcı', 'yeni@example.invalid', 'Personel']
        out = io.StringIO(); csv.writer(out).writerows(rows)
        return strategy.post('/api/users/bulk-preview', headers={'X-CSRF-Token': csrf},
                             files={'file': ('hesaplar.csv', out.getvalue().encode('utf-8'), 'text/csv')}).json()
    assert rows[1][1] == "'+Fen İşleri"
    assert preview("'+Fen İşleri")['count'] == 1 and preview('+Fen İşleri')['count'] == 1
    rejected = preview("'Fen İşleri")
    assert rejected['count'] == 0 and 'Müdürlük adı şablonla eşleşmiyor' in rejected['errors'][0]


@pytest.mark.parametrize('backend', BACKENDS)
def test_missing_department_and_audit_exports_are_guarded(backend, live_client, db, sample):
    db.get(Department, sample['department'].id).name = '+Fen İşleri'
    db.get(User, sample['user'].id).is_active = False
    db.add(AuditLog(user_id=sample['user'].id, action='@komut', entity_type='\tsekme', entity_id=7,
                    details='=cmd|" /C calc"!A0'))
    db.commit()
    strategy = live_client(); login(strategy, sample['strategy'].email)
    rows = read_csv(strategy.get('/api/users/missing-departments.csv'))
    assert rows[1][:2] == [str(sample['department'].id), "'+Fen İşleri"]
    rows = read_csv(strategy.get('/api/audit/export.csv?action=%40komut'))
    assert len(rows) == 2
    assert rows[1][2:] == ["'@komut", "'\tsekme", '7', "'=cmd|\" /C calc\"!A0"]


# --------------------------------------------------------------------------- A1-F10 sessions

@pytest.mark.parametrize('backend', BACKENDS)
def test_password_reset_rejects_every_old_session_of_that_user_only(backend, live_client, db, sample):
    victim, other = sample['user'], add_user(db, sample, 'ikinci@example.invalid')
    old_a = live_client(); csrf_a = login(old_a, victim.email); cookie_a = old_a.cookies.get('session')
    old_b = live_client(); csrf_b = login(old_b, other.email)
    strategy = live_client(); csrf_s = login(strategy, sample['strategy'].email)
    before = indicator_value(db)

    response = strategy.post(f'/api/users/{victim.id}/reset-password', headers={'X-CSRF-Token': csrf_s},
                             json={'password': NEW_PASSWORD})
    assert response.status_code == 200, response.text

    # 3. Old cookie of A: authenticated GET is rejected as unauthenticated (401, not a CSRF 403).
    assert replay(live_client, cookie_a).get('/modules').status_code == 401
    # 4. Old cookie of A with its once-valid CSRF token cannot write.
    response = replay(live_client, cookie_a).post(f'/api/indicators/{sample["indicator"].id}/save?period_id=1',
                                                  headers={'X-CSRF-Token': csrf_a}, json={'value_2027_target': '9'})
    assert response.status_code == 401
    assert indicator_value(db) == before
    # 5. A fresh login with the new password works; the old password no longer does.
    second = live_client(); csrf_a_second = login(second, victim.email, NEW_PASSWORD, expected_path='/change-password')
    assert second.get('/modules').status_code == 303
    personal = NEW_PASSWORD + '-personal'
    assert second.post('/api/me/change-password', headers={'X-CSRF-Token': csrf_a_second}, json={
        'current_password': NEW_PASSWORD, 'new_password': personal, 'confirmation': personal}).status_code == 200
    assert second.get('/modules').status_code == 200
    response = second.post(f'/api/indicators/{sample["indicator"].id}/save?period_id=1',
                           headers={'X-CSRF-Token': csrf_a_second}, json={'value_2027_target': '9'})
    assert response.status_code == 200, response.text
    assert indicator_value(db) == Decimal('9')
    assert live_client().post('/login', data={'email': victim.email, 'password': PASSWORD}).status_code == 400
    # 6. Another user's session is untouched, for reads and writes.
    assert old_b.get('/modules').status_code == 200
    response = old_b.post('/api/me/change-password', headers={'X-CSRF-Token': csrf_b},
                          json={'current_password': 'yanlis', 'new_password': 'x', 'confirmation': 'x'})
    assert response.status_code == 422 and response.json()['detail'] == 'Mevcut parola hatalı.'
    # The strategy user who performed the reset keeps working.
    assert strategy.get('/modules').status_code == 200
    # The landing page agrees with require_user, and the dead session can still be closed with its token.
    assert replay(live_client, cookie_a).get('/').headers['location'] == '/login'
    assert replay(live_client, cookie_a).post('/logout').status_code == 403
    assert replay(live_client, cookie_a).post('/logout', data={'csrf_token': csrf_a}).status_code == 303


@pytest.mark.parametrize('backend', BACKENDS)
def test_self_password_change_keeps_acting_session_and_kills_the_others(backend, live_client, db, sample):
    acting = live_client(); csrf = login(acting, sample['user'].email)
    elsewhere = live_client(); csrf_elsewhere = login(elsewhere, sample['user'].email)
    cookie_elsewhere = elsewhere.cookies.get('session')
    response = acting.post('/api/me/change-password', headers={'X-CSRF-Token': csrf}, json={
        'current_password': PASSWORD, 'new_password': NEW_PASSWORD, 'confirmation': NEW_PASSWORD})
    assert response.status_code == 200, response.text
    assert acting.get('/modules').status_code == 200
    assert acting.post(f'/api/indicators/{sample["indicator"].id}/save?period_id=1', headers={'X-CSRF-Token': csrf},
                       json={'value_2027_target': '4'}).status_code == 200
    assert replay(live_client, cookie_elsewhere).get('/modules').status_code == 401
    assert replay(live_client, cookie_elsewhere).post(f'/api/indicators/{sample["indicator"].id}/save?period_id=1', headers={'X-CSRF-Token': csrf_elsewhere},
                          json={'value_2027_target': '5'}).status_code == 401
    assert indicator_value(db) == Decimal('4')
    assert login(live_client(), sample['user'].email, NEW_PASSWORD)


@pytest.mark.parametrize('backend', BACKENDS)
def test_deactivated_user_stays_rejected(backend, live_client, db, sample):
    victim = live_client(); csrf_victim = login(victim, sample['user'].email); cookie = victim.cookies.get('session')
    strategy = live_client(); csrf = login(strategy, sample['strategy'].email)
    response = strategy.post(f'/api/users/{sample["user"].id}/active', headers={'X-CSRF-Token': csrf}, json={'active': False})
    assert response.status_code == 200
    assert replay(live_client, cookie).get('/modules').status_code == 401
    assert replay(live_client, cookie).post(f'/api/indicators/{sample["indicator"].id}/save?period_id=1', headers={'X-CSRF-Token': csrf_victim},
                                            json={'value_2027_target': '7'}).status_code == 401
    assert indicator_value(db) == Decimal('1.75')
    assert live_client().post('/login', data={'email': sample['user'].email, 'password': PASSWORD}).status_code == 400


@pytest.mark.parametrize('backend', BACKENDS)
def test_reset_to_the_same_password_and_self_reset_still_end_sessions(backend, live_client, db, sample):
    """Every reset re-salts the hash; an admin resetting their own account loses that session too."""
    victim = live_client(); login(victim, sample['user'].email); cookie = victim.cookies.get('session')
    strategy = live_client(); csrf = login(strategy, sample['strategy'].email); own = strategy.cookies.get('session')
    assert strategy.post(f'/api/users/{sample["user"].id}/reset-password', headers={'X-CSRF-Token': csrf},
                         json={'password': PASSWORD}).status_code == 200
    assert replay(live_client, cookie).get('/modules').status_code == 401
    assert strategy.post(f'/api/users/{sample["strategy"].id}/reset-password', headers={'X-CSRF-Token': csrf},
                         json={'password': NEW_PASSWORD}).status_code == 200
    assert replay(live_client, own).get('/modules').status_code == 401
    assert login(live_client(), sample['strategy'].email, NEW_PASSWORD, expected_path='/change-password')


@pytest.mark.postgres
def test_admin_reset_during_a_pending_self_change_wins(db, sample):
    """A self change authenticated before an admin reset must not overwrite it (pre-review REL-2)."""
    import asyncio
    from sqlalchemy.orm import Session
    from fastapi import HTTPException
    from app.main import change_own_password
    from app.security import verify_password
    victim_id = sample['user'].id
    db.get(User, victim_id).password_hash = hash_password(PASSWORD); db.commit()
    admin_password = 'Admin-Sifirladi-2027'

    class PendingBody:
        """The body arrives only after the admin's reset has committed."""
        session = {'user_id': victim_id, 'password_fp': 'x', 'csrf_token': 'x'}

        async def json(self):
            with Session(db.get_bind()) as admin:
                admin.get(User, victim_id).password_hash = hash_password(admin_password)
                admin.commit()
            return {'current_password': PASSWORD, 'new_password': NEW_PASSWORD, 'confirmation': NEW_PASSWORD}

    with Session(db.get_bind()) as request_db:
        stale_user = request_db.get(User, victim_id)  # what require_user loaded before the body wait
        request = PendingBody()
        with pytest.raises(HTTPException) as error:
            asyncio.run(change_own_password(request, request_db, stale_user))
        assert error.value.status_code == 409
        assert request.session['password_fp'] == 'x'  # the pending session was not re-stamped
    db.expire_all()
    stored = db.get(User, victim_id).password_hash
    assert verify_password(admin_password, stored) and not verify_password(NEW_PASSWORD, stored)


def test_reset_landing_right_after_a_self_change_still_ends_that_session(live_client, db, sample, monkeypatch):
    """The acting session is stamped with the hash it wrote, not with whatever is stored a moment later."""
    from sqlalchemy import update
    acting = live_client(); csrf = login(acting, sample['user'].email)
    real_commit, armed = db.commit, [True]

    def commit_then_admin_reset():
        real_commit()
        if armed[0]:
            armed[0] = False
            db.execute(update(User).where(User.id == sample['user'].id).values(password_hash=hash_password('Admin-Sifirladi-2027')))
            real_commit()
    monkeypatch.setattr(db, 'commit', commit_then_admin_reset)
    response = acting.post('/api/me/change-password', headers={'X-CSRF-Token': csrf}, json={
        'current_password': PASSWORD, 'new_password': NEW_PASSWORD, 'confirmation': NEW_PASSWORD})
    monkeypatch.setattr(db, 'commit', real_commit)
    assert response.status_code == 200 and not armed[0]
    assert acting.get('/modules').status_code == 401
    assert login(live_client(), sample['user'].email, 'Admin-Sifirladi-2027')


def test_failed_password_change_keeps_other_sessions(live_client, db, sample):
    acting = live_client(); csrf = login(acting, sample['user'].email)
    other = live_client(); login(other, sample['user'].email)
    response = acting.post('/api/me/change-password', headers={'X-CSRF-Token': csrf}, json={
        'current_password': 'yanlis-parola', 'new_password': NEW_PASSWORD, 'confirmation': NEW_PASSWORD})
    assert response.status_code == 422
    assert other.get('/modules').status_code == 200 and acting.get('/modules').status_code == 200


def test_session_cookie_never_carries_the_password_hash(live_client, db, sample):
    import base64
    client = live_client(); login(client, sample['user'].email)
    payload = json.loads(base64.b64decode(client.cookies.get('session').split('.')[0]))
    stored = db.get(User, sample['user'].id).password_hash
    assert set(payload) == {'user_id', 'password_fp', 'csrf_token'}
    salt, digest = stored.split('$')[1:]
    assert all(secret not in json.dumps(payload) for secret in (stored, salt, digest))


def test_session_with_a_tampered_fingerprint_is_rejected(live_client, db, sample):
    import base64
    from itsdangerous import TimestampSigner
    from app.config import session_secret
    client = live_client(); login(client, sample['user'].email)
    payload = json.loads(base64.b64decode(client.cookies.get('session').split('.')[0]))
    payload['password_fp'] = '0' * 32
    client.cookies.set('session', TimestampSigner(session_secret()).sign(base64.b64encode(json.dumps(payload).encode())).decode())
    assert client.get('/modules').status_code == 401


def test_session_issued_without_password_fingerprint_is_rejected(live_client, db, sample):
    """Cookies issued before this change (no fingerprint) must not stay valid."""
    import base64
    from itsdangerous import TimestampSigner
    from app.config import session_secret
    client = live_client(); login(client, sample['user'].email)
    payload = base64.b64encode(json.dumps({'user_id': sample['user'].id, 'csrf_token': 'x'}).encode())
    client.cookies.set('session', TimestampSigner(session_secret()).sign(payload).decode())
    assert client.get('/modules').status_code == 401


# --------------------------------------------------------------------------- A1-F11a logout CSRF

@pytest.mark.parametrize('backend', BACKENDS)
def test_logout_requires_the_session_csrf_token(backend, live_client, db, sample):
    client = live_client(); csrf = login(client, sample['user'].email)
    assert client.post('/logout').status_code == 403
    assert client.post('/logout', data={'csrf_token': 'yanlis'}).status_code == 403
    assert client.post('/logout', headers={'X-CSRF-Token': 'yanlis'}).status_code == 403
    assert client.get('/logout').status_code == 405
    assert client.get('/modules').status_code == 200
    # The sidebar form posts the token as a form field.
    response = client.post('/logout', data={'csrf_token': csrf})
    assert response.status_code == 303 and response.headers['location'] == '/login'
    assert client.get('/modules').status_code == 401
    # Header form (fetch) also works, and login stays usable afterwards.
    csrf = login(client, sample['user'].email)
    assert client.post('/logout', headers={'X-CSRF-Token': csrf}).status_code == 303
    assert client.get('/modules').status_code == 401
    assert login(client, sample['user'].email)


def test_logout_without_a_session_just_redirects(live_client):
    response = live_client().post('/logout')
    assert response.status_code == 303 and response.headers['location'] == '/login'


# --------------------------------------------------------------------------- A1-F4 concurrency (PostgreSQL)

def test_no_async_route_awaits_while_holding_a_row_lock():
    """Static guard: no await after a with_for_update() written in the async handler itself.

    It does not see locks taken by UPDATE/flush or inside called services; those must also be
    taken only after the request body has been read."""
    app_dir = Path(__file__).resolve().parent.parent / 'app'
    offenders = []
    for path in sorted(app_dir.glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for function in ast.walk(tree):
            if not isinstance(function, ast.AsyncFunctionDef):
                continue
            locks = [node.lineno for node in ast.walk(function) if isinstance(node, ast.Attribute) and node.attr == 'with_for_update']
            awaits = [node.lineno for node in ast.walk(function) if isinstance(node, ast.Await)]
            if locks and any(line > min(locks) for line in awaits):
                offenders.append(f'{path.name}:{function.name}')
    assert not offenders, offenders


def test_decision_checks_keep_their_order_and_reject_bad_bodies(client, db, sample):
    from app.main import app, require_user
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    sub = db.scalar(select(Submission))
    path = f'/api/submissions/{sub.id}/decision?period_id=1'
    assert client.post('/api/submissions/999/decision?period_id=1', json={'decision': 'approve'}).status_code == 404
    assert client.post('/api/submissions/999/decision?period_id=1', content=b'{bozuk', headers={'Content-Type': 'application/json'}).status_code == 404
    assert client.post(path, content=b'{bozuk', headers={'Content-Type': 'application/json'}).status_code == 409  # draft
    sub.status = 'submitted'; db.commit()
    assert client.post(path, content=b'{bozuk', headers={'Content-Type': 'application/json'}).status_code == 422
    assert client.post(path, json=['approve']).status_code == 422
    assert client.post(path, json={'decision': 'sil'}).status_code == 422
    assert client.post(path, json={'decision': 'return', 'note': '  '}).status_code == 422
    db.expire_all()
    assert db.get(Submission, sub.id).status == 'submitted'
    assert not db.scalars(select(SubmissionEvent)).all()


def _free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def _health_seconds(port, timeout=3.0):
    started = time.perf_counter()
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=timeout) as conn:
            conn.sendall(b'GET /health HTTP/1.1\r\nHost: test\r\nConnection: close\r\n\r\n')
            status = conn.recv(64).split(b'\r\n')[0]
        return status, time.perf_counter() - started
    except OSError as exc:
        return type(exc).__name__.encode(), time.perf_counter() - started


def _read_response(conn, timeout):
    conn.settimeout(timeout)
    data = b''
    try:
        while b'\r\n\r\n' not in data:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        head, _, body = data.partition(b'\r\n\r\n')
        length = int(re.search(rb'content-length: (\d+)', head, re.I).group(1))
        while len(body) < length:
            body += conn.recv(4096)
        return int(head.split(b' ')[1]), json.loads(body)
    except (OSError, AttributeError) as exc:
        return None, type(exc).__name__


@pytest.mark.postgres
def test_decision_body_wait_never_freezes_the_server(db, sample):
    """T1 sends headers and holds its body; T2 decides the same submission; /health must stay live."""
    import httpx
    import uvicorn
    from app.main import app
    from app.db import get_db

    tag = 'civensa-a1f4-' + uuid.uuid4().hex[:8]
    bind = db.get_bind()
    # Request sessions get their own pool, tagged so cleanup can end exactly these backends.
    request_engine = create_engine(bind.url, connect_args={'application_name': tag}).execution_options(
        schema_translate_map=bind.get_execution_options()['schema_translate_map'])
    factory = sessionmaker(bind=request_engine, autoflush=False, autocommit=False)

    def database():
        session = factory()
        try:
            yield session
        finally:
            session.close()
    sub = db.scalar(select(Submission)); sub.status = 'submitted'; sub.revision = 1
    db.get(User, sample['strategy'].id).password_hash = hash_password(PASSWORD)
    db.commit()
    app.dependency_overrides[get_db] = database
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, lifespan='off', log_level='warning'))
    thread = threading.Thread(target=server.run, daemon=True); thread.start()
    t1 = t2 = None
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.05)
        assert server.started
        with httpx.Client(base_url=f'http://127.0.0.1:{port}', follow_redirects=False) as browser:
            assert browser.post('/login', data={'email': sample['strategy'].email, 'password': PASSWORD}).status_code == 303
            csrf = CSRF_RE.search(browser.get('/modules').text).group(1)
            cookie = '; '.join(f'{k}={v}' for k, v in browser.cookies.items())
        assert _health_seconds(port)[0] == b'HTTP/1.1 200 OK'

        def request_head(body):
            return (f'POST /api/submissions/{sub.id}/decision?period_id=1 HTTP/1.1\r\nHost: test\r\nCookie: {cookie}\r\n'
                    f'X-CSRF-Token: {csrf}\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n'
                    'Connection: close\r\n\r\n').encode()
        body_t1 = json.dumps({'decision': 'approve'}).encode()
        body_t2 = json.dumps({'decision': 'return', 'note': 'Eş zamanlı iade'}).encode()
        t1 = socket.create_connection(('127.0.0.1', port)); t1.sendall(request_head(body_t1))   # body withheld
        # Barrier: T1 has authenticated (old code: and locked the row) and is now waiting for its body.
        for _ in range(100):
            waiting = db.execute(text("SELECT count(*) FROM pg_stat_activity WHERE application_name = :tag "
                                      "AND state = 'idle in transaction'"), {'tag': tag}).scalar()
            db.rollback()
            if waiting:
                break
            time.sleep(0.05)
        assert waiting == 1
        time.sleep(0.1)
        t2 = socket.create_connection(('127.0.0.1', port)); t2.sendall(request_head(body_t2) + body_t2)
        t2_status, t2_body = _read_response(t2, timeout=5)
        during, during_s = _health_seconds(port)
        t1.sendall(body_t1)
        t1_status, t1_body = _read_response(t1, timeout=5)
        after, after_s = _health_seconds(port)
        print(f'A1-F4 proof: T2={t2_status} {t2_body} | health during T1 body wait={during} {during_s:.3f}s | '
              f'T1={t1_status} {t1_body} | health after={after} {after_s:.3f}s')
        assert during == b'HTTP/1.1 200 OK' and during_s < 1.0
        assert (t2_status, t2_body) == (200, {'ok': True, 'status': 'returned'})
        assert t1_status == 409 and t1_body['detail'] == 'Yalnızca incelemedeki paket için karar verilebilir.'
        assert after == b'HTTP/1.1 200 OK' and after_s < 1.0
        db.expire_all()
        assert db.get(Submission, sub.id).status == 'returned'
        decisions = db.scalars(select(SubmissionEvent.event_type).where(
            SubmissionEvent.submission_id == sub.id, SubmissionEvent.event_type.in_(['approve', 'return']))).all()
        assert decisions == ['return']
        assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action.like('submission_%'))) == 1
    finally:
        for conn in (t1, t2):
            if conn:
                conn.close()
        # If the server is wedged (regression), end only this test's own backends so shutdown can proceed.
        db.rollback()
        db.execute(text('SELECT pg_terminate_backend(pid) FROM pg_stat_activity '
                        'WHERE application_name = :tag AND pid <> pg_backend_pid()'), {'tag': tag})
        db.commit()
        server.should_exit = True
        thread.join(timeout=10)
        app.dependency_overrides.clear()
        request_engine.dispose()
