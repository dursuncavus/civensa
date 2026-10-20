"""CIV-044: real login/CSRF, PostgreSQL accounts, credentials and retirement."""
import csv
import io
import json
import logging
import re
import secrets

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import MetaData, Table, inspect, select, func
from sqlalchemy.exc import IntegrityError

from app.db import get_db
from app.main import app, ACCOUNT_CSV_HEADERS
from app.models import AuditLog, Department, User
from app.security import hash_password, verify_password

pytestmark = pytest.mark.postgres


@pytest.fixture
def accounts(db, sample):
    credential = secrets.token_urlsafe(24)
    sd = Department(organization_id=sample['department'].organization_id, name='Strateji Geliştirme Müdürlüğü')
    db.add(sd); db.flush()
    sample['strategy'].department_id = sd.id
    sample['strategy'].password_hash = hash_password(credential)
    sample['user'].password_hash = hash_password(credential)
    db.commit()
    clients = []
    def database():
        try:
            yield db
        finally:
            db.rollback()
    app.dependency_overrides[get_db] = database
    def login(email=None, password=None):
        client = TestClient(app, follow_redirects=False)
        clients.append(client)
        response = client.post('/login', data={'email': email or sample['strategy'].email, 'password': password or credential})
        assert response.status_code == 303
        page = client.get(response.headers['location'])
        client.headers['X-CSRF-Token'] = re.search(r'name="csrf-token" content="([^"]+)"', page.text).group(1)
        return client
    yield login, credential
    for client in clients:
        client.close()
    app.dependency_overrides.clear()


def csv_bytes(rows, headers=ACCOUNT_CSV_HEADERS):
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(headers); writer.writerows(rows)
    return ('\ufeff' + output.getvalue()).encode('utf-8')


def row(sample, index=1, duty='Personel'):
    department = sample['department']
    return [department.id, department.name, f'Kişi {index}', f'personal{index}@example.invalid', duty]


def upload(client, rows, action='bulk-import', headers=ACCOUNT_CSV_HEADERS):
    return client.post('/api/users/' + action, files={'file': ('accounts.csv', csv_bytes(rows, headers), 'text/csv')})


def credentials(response):
    assert response.status_code == 200
    assert response.content.startswith(b'\xef\xbb\xbf')
    return list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))


def test_template_includes_existing_directorates_and_has_no_password(accounts, sample):
    client = accounts[0]()
    response = client.get('/api/users/template.csv')
    assert response.status_code == 200 and response.content.startswith(b'\xef\xbb\xbf')
    rows = list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))
    assert rows[0] == ['Müdürlük ID', 'Müdürlük', 'Ad Soyad', 'E-posta', 'Görev']
    assert any(r[:2] == [str(sample['department'].id), sample['department'].name] for r in rows[1:])
    page = client.get('/users')
    assert 'Şablonu indir' in page.text and 'bulkUserFile' in page.text


def test_multi_person_import_credentials_once_and_no_plaintext(db, sample, accounts, caplog):
    caplog.set_level(logging.DEBUG)
    client = accounts[0]()
    rows = [row(sample, 1, 'Müdür'), row(sample, 2), row(sample, 3)]
    preview = upload(client, rows, 'bulk-preview').json()
    assert preview['ok'] and preview['count'] == 3
    assert [r['duty'] for r in preview['rows']] == ['Müdür', 'Personel', 'Personel']
    assert not db.scalar(select(User).where(User.email == rows[0][3]))
    response = upload(client, rows)
    issued = credentials(response)
    assert len(issued) == 3 and len({r['Geçici Parola'] for r in issued}) == 3
    assert 'no-store' in response.headers['cache-control']
    batch = response.headers['x-account-batch']
    users = db.scalars(select(User).where(User.email.in_([r[3] for r in rows])).order_by(User.email)).all()
    assert [u.position for u in users] == ['director', 'staff', 'staff']
    assert all(u.must_change_password and not u.can_submit for u in users)
    for user, item in zip(users, issued):
        password = item['Geçici Parola']
        assert len(password) >= 14 and not set(password).intersection('01IlOo|')
        assert verify_password(password, user.password_hash)
        assert user.password_hash != password
        audit = db.scalar(select(AuditLog).where(AuditLog.action == 'user_position_change', AuditLog.entity_id == user.id))
        assert json.loads(audit.details)['reason'] == 'Toplu hesap oluşturma, CSV ' + batch
    # Check every stored table, including audits and throttle state, for all issued passwords.
    schema = db.get_bind().get_execution_options()['schema_translate_map'][None]
    snapshot = []
    for name in inspect(db.connection()).get_table_names(schema=schema):
        table = Table(name, MetaData(), schema=schema, autoload_with=db.connection())
        snapshot.extend(str(tuple(record)) for record in db.execute(select(table)))
    at_rest = '\n'.join(snapshot)
    assert all(item['Geçici Parola'] not in at_rest and item['Geçici Parola'] not in caplog.text for item in issued)
    for _ in range(2):
        expired = client.get('/api/users/batches/' + batch + '/credentials.csv')
        assert expired.status_code == 410 and 'Parola sıfırla' in expired.text
    replay = upload(client, rows)
    assert replay.status_code == 422 and 'Parola sıfırla' in replay.text
    assert db.scalar(select(func.count(User.id)).where(User.email.in_([r[3] for r in rows]))) == 3


@pytest.mark.parametrize('problem', ['two_directors', 'existing_director', 'duplicate_email', 'database_email',
    'inactive', 'missing', 'name', 'duty', 'empty_name', 'too_many', 'extra_cell', 'missing_cell', 'empty'])
def test_preview_and_import_share_validation_and_are_atomic(db, sample, accounts, problem):
    rows = [row(sample, 1, 'Müdür'), row(sample, 2)]
    if problem == 'two_directors': rows[1][-1] = 'Müdür'
    elif problem == 'existing_director':
        sample['user'].position = 'director'; db.commit()
    elif problem == 'duplicate_email': rows[1][3] = rows[0][3].upper()
    elif problem == 'database_email': rows[1][3] = sample['user'].email.upper()
    elif problem == 'inactive': sample['department'].is_active = False; db.commit()
    elif problem == 'missing': rows[1][0] = 99999
    elif problem == 'name': rows[1][1] = 'Yanlış müdürlük'
    elif problem == 'duty': rows[1][-1] = 'Başkan'
    elif problem == 'empty_name': rows[1][2] = ''
    elif problem == 'too_many': rows = [row(sample, n) for n in range(201)]
    elif problem == 'extra_cell': rows[1].append('fazla')
    elif problem == 'missing_cell': rows[1].pop()
    elif problem == 'empty': rows = []
    client = accounts[0]()
    before = db.scalar(select(func.count(User.id)))
    preview = upload(client, rows, 'bulk-preview').json()
    result = upload(client, rows)
    assert not preview['ok'] and result.status_code == 422
    assert result.json()['detail']['errors'] == preview['errors']
    assert all(re.match(r'Satır \d+: [^:]+: .+ — .+', message) for message in preview['errors'])
    if problem == 'existing_director': assert sample['user'].full_name in result.text
    assert db.scalar(select(func.count(User.id))) == before
    assert not db.scalar(select(AuditLog.id).where(AuditLog.action == 'user_bulk_create'))


@pytest.mark.parametrize('header', ['Geçici Parola', 'Parola', 'Şifre', 'ŞİFRE', 'password', 'PASSWORD', 'sifre'])
def test_password_column_rejected_with_actionable_error(sample, accounts, header):
    client = accounts[0]()
    for action in ['bulk-preview', 'bulk-import']:
        response = upload(client, [row(sample) + ['']], action, ACCOUNT_CSV_HEADERS + [header])
        assert 'Parola sütunu kabul edilmez' in response.text and 'kaldırın' in response.text
        assert response.status_code == (200 if action == 'bulk-preview' else 422)


def test_late_appointment_failure_rolls_back_accounts_and_audits(db, sample, accounts, monkeypatch):
    from fastapi import HTTPException
    from app import main
    client = accounts[0]()
    original, calls = main.prepare_user_creation, []
    def appointment(db, actor, target):
        calls.append(target.email)
        if len(calls) == 2:
            raise HTTPException(409, 'Müdür ataması değişti. Kullanıcılar listesini yenileyin.')
        return original(db, actor, target)
    monkeypatch.setattr(main, 'prepare_user_creation', appointment)
    response = upload(client, [row(sample, 1), row(sample, 2, 'Müdür')])
    assert response.status_code == 409 and len(calls) == 2
    assert not db.scalar(select(User.id).where(User.email.like('personal%@example.invalid')))
    assert not db.scalar(select(AuditLog.id).where(AuditLog.action.in_(['user_bulk_create_item', 'user_bulk_create'])))


def test_staff_can_join_directorate_with_an_active_director(db, sample, accounts):
    sample['user'].position = 'director'; db.commit()
    client = accounts[0]()
    response = upload(client, [row(sample, 1), row(sample, 2)])
    assert len(credentials(response)) == 2
    assert db.scalar(select(func.count(User.id)).where(User.department_id == sample['department'].id,
                                                      User.position == 'director', User.is_active.is_(True))) == 1


def test_first_login_blocks_navigation_and_writes_until_personal_password(db, sample, accounts):
    client = accounts[0]()
    issued = credentials(upload(client, [row(sample)]))[0]
    person = accounts[0](issued['E-posta'], issued['Geçici Parola'])
    other_session = accounts[0](issued['E-posta'], issued['Geçici Parola'])
    for path in ['/', '/login', '/modules', '/dashboard', '/users', '/department/1', '/api/notifications',
                 '/activity-sections', '/health', '/docs', '/redoc', '/openapi.json', '/unknown-page']:
        response = person.get(path)
        assert response.status_code == 303 and response.headers['location'] == '/change-password'
    blocked = person.post('/api/departments/1/submit?period_id=1')
    assert blocked.status_code == 303 and blocked.headers['location'] == '/change-password'
    page = person.get('/change-password')
    assert page.status_code == 200 and 'Devam etmek için kendi parolanızı belirleyin.' in page.text
    assert person.get('/static/personal_accounts.js').status_code == 200
    temporary = issued['Geçici Parola']
    def change(current, new, confirmation=None):
        return person.post('/api/me/change-password', json={'current_password': current, 'new_password': new,
                                                           'confirmation': confirmation or new})
    assert change(temporary, temporary).status_code == 422
    assert change(temporary, 'short1234').status_code == 422
    assert change(temporary, secrets.token_hex(5) + 'a').status_code == 422  # 11 characters: below the 12 minimum.
    assert change('wrong', secrets.token_urlsafe(18)).status_code == 422
    personal = secrets.token_hex(6)  # Exactly the existing 12-character boundary.
    assert change(temporary, personal, 'different').status_code == 422
    token = person.headers.pop('X-CSRF-Token')
    assert change(temporary, personal).status_code == 403
    person.headers['X-CSRF-Token'] = token
    assert change(temporary, personal).status_code == 200
    target = db.scalar(select(User).where(User.email == issued['E-posta']))
    db.refresh(target)
    assert not target.must_change_password and verify_password(personal, target.password_hash)
    assert person.get('/modules').status_code == 200
    assert other_session.get('/modules').status_code == 401
    assert accounts[0](issued['E-posta'], personal).get('/modules').status_code == 200


def test_single_create_reset_and_logout(db, sample, accounts):
    strategy = accounts[0]()
    temporary = secrets.token_urlsafe(18)
    result = strategy.post('/api/users', json={'email': 'single@example.invalid', 'full_name': 'Tek Kişi',
        'role': 'department', 'department_id': sample['department'].id, 'position': 'staff', 'password': temporary})
    assert result.status_code == 200
    target = db.get(User, result.json()['id'])
    assert target.must_change_password
    person = accounts[0](target.email, temporary)
    assert person.post('/logout').status_code == 303
    assert person.get('/change-password').status_code == 401
    # Reset an established account; existing sessions are revoked, new login is forced to change.
    established = accounts[0](sample['user'].email)
    new_temp = secrets.token_urlsafe(18)
    response = strategy.post(f"/api/users/{sample['user'].id}/reset-password", json={'password': new_temp})
    assert response.status_code == 200
    db.refresh(sample['user']); assert sample['user'].must_change_password
    assert established.get('/modules').status_code == 401
    assert accounts[0](sample['user'].email, new_temp).get('/modules').status_code == 303


def test_bulk_retirement_reason_audit_and_permission_atomicity(db, sample, accounts):
    strategy = accounts[0]()
    shared = sample['user']
    shared_session = accounts[0](shared.email)
    staff = User(email='strategy-staff@example.invalid', full_name='Strateji Personeli', role='strategy',
                 department_id=sample['strategy'].department_id, password_hash=hash_password(accounts[1]))
    db.add(staff); db.commit()
    staff_client = accounts[0](staff.email)
    ids = [shared.id, sample['strategy'].id]
    for reason in ['', '   ']:
        assert strategy.post('/api/users/bulk-deactivate', json={'user_ids': ids, 'reason': reason}).status_code == 422
    result = staff_client.post('/api/users/bulk-deactivate', json={'user_ids': ids, 'reason': 'Kişisel hesaplara geçiş'})
    assert result.status_code == 403 and sample['strategy'].email in result.text
    db.refresh(shared); assert shared.is_active
    shared.position = 'director'; db.commit()
    reason = 'Kişisel hesaplara geçildi; ortak hesap emekliye ayrıldı.'
    result = strategy.post('/api/users/bulk-deactivate', json={'user_ids': [shared.id, staff.id], 'reason': reason})
    assert result.status_code == 200 and result.json()['deactivated'] == 2
    for target in [shared, staff]:
        db.refresh(target); assert not target.is_active and db.get(User, target.id)
        audit = db.scalar(select(AuditLog).where(AuditLog.action == 'user_is_active_change', AuditLog.entity_id == target.id))
        assert json.loads(audit.details) == {'field': 'is_active', 'old': True, 'new': False, 'reason': reason}
    assert shared_session.get('/modules').status_code == 401
    # Directorate's retired director frees the unique director slot, without deletion.
    assert upload(strategy, [row(sample, 1, 'Müdür')]).status_code == 200


def test_revert_preserves_users_and_audits_and_refuses_used_batch(db, sample, accounts):
    client = accounts[0]()
    response = upload(client, [row(sample, 1, 'Müdür'), row(sample, 2)])
    credentials(response)
    batch = response.headers['x-account-batch']
    targets = db.scalars(select(User).where(User.email.like('personal%@example.invalid'))).all()
    result = client.post(f'/api/users/batches/{batch}/revert')
    assert result.status_code == 200 and result.json()['reverted'] == 2
    for target in targets:
        db.refresh(target); assert not target.is_active
        assert db.scalar(select(AuditLog.id).where(AuditLog.entity_id == target.id, AuditLog.action == 'user_bulk_create_item'))
    response = upload(client, [row(sample, 3), row(sample, 4)])
    issued = credentials(response)
    accounts[0](issued[0]['E-posta'], issued[0]['Geçici Parola'])
    result = client.post('/api/users/batches/' + response.headers['x-account-batch'] + '/revert')
    assert result.status_code == 409
    assert all(db.scalar(select(User.is_active).where(User.email == item['E-posta'])) for item in issued)


def test_department_and_csrf_cannot_administer_accounts(db, sample, accounts):
    department = accounts[0](sample['user'].email)
    for action in ['bulk-preview', 'bulk-import']:
        assert upload(department, [row(sample)], action).status_code == 403
    assert department.post('/api/users/bulk-deactivate', json={'user_ids': [sample['strategy'].id], 'reason': 'Gerekçe'}).status_code == 403
    strategy = accounts[0](); strategy.headers.pop('X-CSRF-Token')
    assert upload(strategy, [row(sample)]).status_code == 403
    assert strategy.post('/api/users/bulk-deactivate', json={'user_ids': [sample['user'].id], 'reason': 'Gerekçe'}).status_code == 403


def test_database_director_constraint_stays_enforced(db, sample, accounts):
    sample['user'].position = 'director'; db.commit()
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(User(email='second-director@example.invalid', full_name='İkinci Müdür', role='department',
                        department_id=sample['department'].id, position='director', password_hash='unused'))
            db.flush()
