"""CIV-025 released permissions: real HTTP login/CSRF against PostgreSQL."""
import json
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func

from app.db import get_db
from app.main import app
from app.models import (AuditLog, Department, User, Submission, SubmissionEvent, Activity,
                        Publication, ReportSection, ReportIndicator, ActivityReportApproval)
from app.security import hash_password
from tests.test_activity_contract import actual_payload

pytestmark = pytest.mark.postgres
PASSWORD = 'Civ025-test-password!'


@pytest.fixture
def actors(db, sample):
    department = sample['department']
    strategy_department = Department(organization_id=department.organization_id, name='Strateji Geliştirme Müdürlüğü')
    other_department = Department(organization_id=department.organization_id, name='Diğer Müdürlük')
    db.add_all([strategy_department, other_department]); db.flush()
    sample['strategy'].department_id = strategy_department.id
    sample['user'].can_submit = False
    users = {'staff': sample['user'], 'strategy_director': sample['strategy']}
    for key, role, did, position in [
        ('director', 'department', department.id, 'director'),
        ('authorized', 'department', department.id, 'staff'),
        ('other', 'department', other_department.id, 'staff'),
        ('strategy_staff', 'strategy', strategy_department.id, 'staff'),
    ]:
        users[key] = User(email=key+'@example.invalid', full_name=key, role=role,
                          department_id=did, position=position, password_hash='unused', can_submit=key=='authorized')
        db.add(users[key])
    for user in users.values():
        user.password_hash = hash_password(PASSWORD)
    db.add(AuditLog(action='civ025_tracking_started', entity_type='system'))
    db.commit()
    return users


@pytest.fixture
def http(db, actors):
    def database():
        try:
            yield db
        finally:
            db.rollback()
    app.dependency_overrides[get_db] = database
    clients = []
    def login(key):
        client = TestClient(app, follow_redirects=False)
        clients.append(client)
        response = client.post('/login', data={'email': actors[key].email, 'password': PASSWORD})
        assert response.status_code == 303, response.text
        page = client.get('/modules')
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        client.headers['X-CSRF-Token'] = token
        return client
    yield login
    for client in clients:
        client.close()
    app.dependency_overrides.clear()


def decision(client, sample, action='approve'):
    return client.post('/api/submissions/1/decision?period_id=1', json={'decision': action, 'note': 'Kaynağı kontrol edip yeniden gönderin.'})


@pytest.mark.parametrize('actor', ['director', 'authorized'])
def test_director_and_authorized_staff_submit(http, sample, actor):
    response = http(actor).post(f"/api/departments/{sample['department'].id}/submit?period_id=1")
    assert response.status_code == 200 and response.json()['revision'] == 1


def test_unauthorized_staff_refused_and_csrf_required(http, db, sample):
    client = http('staff')
    assert client.get('/department/1').status_code == 200
    assert http('strategy_staff').get('/department/1').status_code == 200
    response = client.post('/api/departments/1/submit?period_id=1')
    assert response.status_code == 403
    assert all(word in response.json()['detail'] for word in ['Müdür', 'Personel', 'Gönderim Yetkileri', 'Kullanıcılar'])
    assert db.scalar(select(Submission)).status == 'draft'
    assert db.scalar(select(func.count(SubmissionEvent.id))) == 0
    client = http('director'); client.headers.pop('X-CSRF-Token')
    assert client.post('/api/departments/1/submit?period_id=1').status_code == 403


@pytest.mark.parametrize('grantor', ['director', 'strategy_staff'])
def test_grant_revoke_scopes_audits_and_existing_session(http, db, actors, grantor):
    staff = http('staff'); authority = http(grantor)
    path = f"/api/users/{actors['staff'].id}/submit-authorization"
    assert authority.post(path, json={'can_submit': True}).status_code == 200
    # A session opened before the grant sees it immediately.
    assert staff.post('/api/departments/1/submit?period_id=1').status_code == 200
    assert decision(http('strategy_director'), None, 'return').status_code == 200
    assert authority.post(path, json={'can_submit': False}).status_code == 200
    assert staff.post('/api/departments/1/submit?period_id=1').status_code == 403
    audits = db.scalars(select(AuditLog).where(AuditLog.action == 'user_can_submit_change').order_by(AuditLog.id)).all()
    assert [(a.user_id, a.entity_id, json.loads(a.details)) for a in audits] == [
        (actors[grantor].id, actors['staff'].id, {'field': 'can_submit', 'old': False, 'new': True}),
        (actors[grantor].id, actors['staff'].id, {'field': 'can_submit', 'old': True, 'new': False}),
    ]
    assert all(a.created_at for a in audits)
    other_path = f"/api/users/{actors['other'].id}/submit-authorization"
    assert authority.post(other_path, json={'can_submit': True}).status_code == (403 if grantor == 'director' else 200)


def test_staff_cannot_grant_or_change_position_and_csrf_protects_controls(http, actors):
    path = f"/api/users/{actors['staff'].id}"
    staff = http('staff')
    assert staff.post(path+'/submit-authorization', json={'can_submit': True}).status_code == 403
    assert staff.post(path+'/position', json={'position': 'director'}).status_code == 403
    strategy = http('strategy_director'); strategy.headers.pop('X-CSRF-Token')
    assert strategy.post(path+'/position', json={'position': 'director'}).status_code == 403
    assert strategy.post(path+'/submit-authorization', json={'can_submit': True}).status_code == 403


def test_second_director_refused_then_replacement_audited(http, db, actors):
    strategy = http('strategy_staff')
    path = f"/api/users/{actors['staff'].id}/position"
    refused = strategy.post(path, json={'position': 'director'})
    assert refused.status_code == 409 and 'önce mevcut' in refused.json()['detail']
    assert strategy.post(f"/api/users/{actors['director'].id}/position", json={'position': 'staff'}).status_code == 200
    assert strategy.post(path, json={'position': 'director'}).status_code == 200
    assert http('staff').post('/api/departments/1/submit?period_id=1').status_code == 200
    logs = db.scalars(select(AuditLog).where(AuditLog.action == 'user_position_change').order_by(AuditLog.id)).all()
    assert [(a.entity_id, json.loads(a.details)['old'], json.loads(a.details)['new']) for a in logs] == [
        (actors['director'].id, 'director', 'staff'), (actors['staff'].id, 'staff', 'director')]
    assert all(a.user_id == actors['strategy_staff'].id and a.created_at for a in logs)


def strategy_candidate(db, actors, key='candidate', *, active=True, role='strategy'):
    candidate = User(email=key+'@example.invalid', full_name=key, role=role,
        department_id=actors['strategy_staff'].department_id, position='staff',
        is_active=active, password_hash=hash_password(PASSWORD))
    db.add(candidate); db.commit(); actors[key] = candidate
    return candidate


@pytest.mark.parametrize('actor,position', [('strategy_staff', 'director'), ('strategy_director', 'staff')])
def test_own_position_change_refused(http, db, actors, actor, position):
    target = actors[actor]; old = target.position
    response = http(actor).post(f'/api/users/{target.id}/position', json={'position': position})
    assert response.status_code == 403
    assert all(word in response.json()['detail'] for word in [target.full_name, 'kendi unvanınızı', 'Kullanıcılar'])
    db.refresh(target)
    assert target.position == old
    assert db.scalar(select(func.count(AuditLog.id)).where(AuditLog.action == 'user_position_change')) == 0


def test_strategy_staff_cannot_demote_or_replace_director(http, db, actors):
    candidate = strategy_candidate(db, actors)
    staff = http('strategy_staff'); director = actors['strategy_director']
    for target, position in [(director, 'staff'), (candidate, 'director')]:
        response = staff.post(f'/api/users/{target.id}/position', json={'position': position})
        assert response.status_code == 403
        assert target.email in response.json()['detail'] and 'etkin Strateji Geliştirme Müdürüne' in response.json()['detail']
    # Scope is the Strategy department too, not merely the target's role string.
    department_role = strategy_candidate(db, actors, 'department_role', role='department')
    assert staff.post(f'/api/users/{department_role.id}/position', json={'position': 'director'}).status_code == 403
    response = staff.post('/api/users', json={'email': 'replacement@example.invalid', 'full_name': 'Yerine Atama',
        'role': 'strategy', 'position': 'director', 'password': PASSWORD})
    assert response.status_code == 403
    assert db.scalar(select(User.id).where(User.email == 'replacement@example.invalid')) is None
    db.refresh(director); db.refresh(candidate)
    assert director.position == 'director' and candidate.position == 'staff'
    assert db.scalar(select(func.count(AuditLog.id)).where(AuditLog.action == 'user_position_change')) == 0


def test_strategy_director_appoints_successor_and_handover_is_audited(http, db, actors):
    candidate = strategy_candidate(db, actors, active=False)
    director = http('strategy_director'); staff = http('strategy_staff')
    path = f'/api/users/{candidate.id}'
    assert director.post(path+'/position', json={'position': 'director'}).status_code == 200
    assert staff.post(path+'/active', json={'active': True}).status_code == 403
    # Preserve one active director and the self-position ban: the incumbent leaves
    # by deactivating their own account, then a different staff member bootstraps.
    previous = actors['strategy_director']
    assert director.post(f'/api/users/{previous.id}/active', json={'active': False}).status_code == 200
    assert director.get('/modules').status_code == 401
    assert staff.post(path+'/active', json={'active': True}).status_code == 200
    successor = http('candidate')
    assert successor.post(f'/api/users/{previous.id}/position', json={'position': 'staff'}).status_code == 200
    db.refresh(previous); db.refresh(candidate)
    assert previous.position == 'staff' and not previous.is_active
    assert candidate.position == 'director' and candidate.is_active
    logs = db.scalars(select(AuditLog).where(AuditLog.action.in_(['user_position_change', 'user_is_active_change'])).order_by(AuditLog.id)).all()
    assert [(a.user_id, a.entity_id, json.loads(a.details)['old'], json.loads(a.details)['new']) for a in logs] == [
        (previous.id, candidate.id, 'staff', 'director'),
        (previous.id, previous.id, True, False),
        (actors['strategy_staff'].id, candidate.id, False, True),
        (candidate.id, previous.id, 'director', 'staff'),
    ]
    assert 'bootstrap' in json.loads(logs[2].details)['reason']
    assert all(a.created_at for a in logs)


def test_bootstrap_requires_no_active_director_other_target_active_actor_and_csrf(http, db, actors):
    candidate = strategy_candidate(db, actors)
    staff = http('strategy_staff'); director = http('strategy_director')
    path = f'/api/users/{candidate.id}/position'
    assert staff.post(path, json={'position': 'director'}).status_code == 403
    actors['strategy_director'].is_active = False; db.commit()
    assert director.post(path, json={'position': 'director'}).status_code == 401
    assert staff.post(f"/api/users/{actors['strategy_staff'].id}/position", json={'position': 'director'}).status_code == 403
    token = staff.headers.pop('X-CSRF-Token')
    assert staff.post(path, json={'position': 'director'}).status_code == 403
    staff.headers['X-CSRF-Token'] = token
    candidate.is_active = False; db.commit()
    assert staff.post(path, json={'position': 'director'}).status_code == 403
    candidate.is_active = True; db.commit()
    assert staff.post(path, json={'position': 'director'}).status_code == 200
    audit = db.scalar(select(AuditLog).where(AuditLog.action == 'user_position_change'))
    details = json.loads(audit.details)
    assert audit.user_id == actors['strategy_staff'].id and audit.entity_id == candidate.id and audit.created_at
    assert details['old'] == 'staff' and details['new'] == 'director'
    assert 'etkin Strateji Geliştirme Müdürü bulunmadığı' in details['reason'] and 'bootstrap' in details['reason']
    # The exception closes immediately after the appointment.
    assert staff.post(path, json={'position': 'staff'}).status_code == 403


def test_bootstrap_new_director_creation_is_audited(http, db, actors):
    actors['strategy_director'].is_active = False; db.commit()
    response = http('strategy_staff').post('/api/users', json={'email': 'initial@example.invalid', 'full_name': 'İlk Müdür',
        'role': 'strategy', 'position': 'director', 'password': PASSWORD})
    assert response.status_code == 200, response.text
    audit = db.scalar(select(AuditLog).where(AuditLog.action == 'user_position_change', AuditLog.entity_id == response.json()['id']))
    assert audit.user_id == actors['strategy_staff'].id and audit.created_at
    details = json.loads(audit.details)
    assert details['old'] is None and details['new'] == 'director' and 'bootstrap' in details['reason']


def test_strategy_director_account_cannot_be_taken_over_or_removed_by_staff(http, db, actors):
    director = actors['strategy_director']; old_hash = director.password_hash
    batch = 'a' * 16
    db.add(AuditLog(action='user_bulk_create_item', entity_type='user', entity_id=director.id, details=f'batch={batch};department_id={director.department_id}'))
    db.commit()
    staff = http('strategy_staff')
    for path, data in [(f'/api/users/{director.id}/active', {'active': False}),
                       (f'/api/users/{director.id}/reset-password', {'password': PASSWORD+'new'}),
                       (f'/api/users/batches/{batch}/revert', {})]:
        response = staff.post(path, json=data)
        assert response.status_code == 403 and director.email in response.json()['detail']
    db.refresh(director)
    assert director.is_active and director.position == 'director' and director.password_hash == old_hash


@pytest.mark.parametrize('route', ['position', 'create', 'activate'])
def test_concurrent_strategy_bootstrap_has_one_authorized_winner(http, db, actors, route):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.orm import Session
    candidates = [strategy_candidate(db, actors, key) for key in ('candidate1', 'candidate2')]
    if route == 'activate':
        for candidate in candidates:
            candidate.position = 'director'
            candidate.is_active = False
    actors['strategy_director'].is_active = False; db.commit()
    clients = [http('strategy_staff'), http('strategy_staff')]
    ids = [candidate.id for candidate in candidates]; bind = db.get_bind()
    db.commit()
    def independent_database():
        with Session(bind) as session:
            yield session
    app.dependency_overrides[get_db] = independent_database
    barrier = Barrier(2)
    def appoint(index):
        barrier.wait(timeout=5)
        if route == 'create':
            return clients[index].post('/api/users', json={'email': f'newcandidate{index}@example.invalid',
                'full_name': 'Yeni Müdür', 'role': 'strategy', 'position': 'director', 'password': PASSWORD}).status_code
        if route == 'activate':
            return clients[index].post(f'/api/users/{ids[index]}/active', json={'active': True}).status_code
        return clients[index].post(f'/api/users/{ids[index]}/position', json={'position': 'director'}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(appoint, range(2))) == [200, 403]
    db.expire_all()
    assert db.scalar(select(func.count(User.id)).where(User.role == 'strategy', User.position == 'director', User.is_active.is_(True))) == 1
    logs = db.scalars(select(AuditLog).where(AuditLog.action == ('user_is_active_change' if route == 'activate' else 'user_position_change'))).all()
    assert len(logs) == 1 and 'bootstrap' in json.loads(logs[0].details)['reason']


def test_director_reactivation_conflict_and_new_staff_default(http, db, actors):
    strategy = http('strategy_staff')
    director_path = f"/api/users/{actors['director'].id}"
    assert strategy.post(director_path+'/active', json={'active': False}).status_code == 200
    assert http('strategy_staff').post(f"/api/users/{actors['staff'].id}/position", json={'position': 'director'}).status_code == 200
    assert strategy.post(director_path+'/active', json={'active': True}).status_code == 409
    duplicate = strategy.post('/api/users', json={'email': 'duplicate@example.invalid', 'full_name': 'İkinci Müdür',
        'role': 'department', 'department_id': actors['staff'].department_id, 'position': 'director', 'password': PASSWORD})
    assert duplicate.status_code == 409 and 'önce mevcut' in duplicate.json()['detail']
    for role in ('department', 'strategy'):
        response = strategy.post('/api/users', json={'email': role+'new@example.invalid', 'full_name': 'Yeni Personel',
            'role': role, 'department_id': actors['staff'].department_id, 'password': PASSWORD})
        assert response.status_code == 200, response.text
        user = db.get(User, response.json()['id'])
        assert user.position == 'staff' and not user.can_submit and user.department_id
        if role == 'strategy':
            assert user.department_id == actors['strategy_staff'].department_id


@pytest.mark.parametrize('action', ['approve', 'return'])
def test_strategy_staff_cannot_decide_director_can(http, db, sample, action):
    assert http('director').post('/api/departments/1/submit?period_id=1').status_code == 200
    response = decision(http('strategy_staff'), sample, action)
    assert response.status_code == 403 and 'Strateji Geliştirme Müdürü' in response.json()['detail']
    assert db.scalar(select(Submission)).status == 'submitted'
    response = decision(http('strategy_director'), sample, action)
    assert response.status_code == 200, response.text
    assert db.scalar(select(Submission)).status == ('approved' if action == 'approve' else 'returned')


def test_strategy_director_edit_blocks_approval_until_return(http, db, sample, actors):
    strategy = http('strategy_director')
    # Existing Strategy data-write route; no new ex-officio correction path.
    assert strategy.post('/report-builder/scope', data={'period_id': sample['period'].id,
        'department_id': sample['department'].id, 'status': 'required', 'display_name': 'Güncel Müdürlük'}).status_code == 303
    assert http('director').post('/api/departments/1/submit?period_id=1').status_code == 200
    blocked = decision(strategy, sample)
    assert blocked.status_code == 403 and 'Görevler ayrılığı' in blocked.json()['detail']
    assert db.scalar(select(Submission)).status == 'submitted'
    assert db.scalar(select(AuditLog).where(AuditLog.action == 'pp_data_change', AuditLog.user_id == actors['strategy_director'].id))
    assert decision(strategy, sample, 'return').status_code == 200
    assert http('director').post('/api/departments/1/submit?period_id=1').status_code == 200
    assert decision(strategy, sample).status_code == 200


def test_prior_editor_still_blocked_after_role_change_and_another_edit(http, db, sample, actors):
    editor = http('strategy_director')
    # Before promotion the same person was a department data editor.
    actors['strategy_director'].role = 'department'
    actors['strategy_director'].department_id = actors['other'].department_id
    actors['strategy_director'].position = 'staff'
    db.commit()
    actors['strategy_director'].department_id = sample['department'].id; db.commit()
    assert editor.post('/api/indicators/1/save?period_id=1', json={'value_2027_target': '3'}).status_code == 200
    assert http('staff').post('/api/indicators/1/save?period_id=1', json={'value_2027_target': '4'}).status_code == 200
    actors['strategy_director'].role = 'strategy'
    actors['strategy_director'].department_id = actors['strategy_staff'].department_id
    actors['strategy_director'].position = 'director'; db.commit()
    assert http('director').post('/api/departments/1/submit?period_id=1').status_code == 200
    assert decision(editor, sample).status_code == 403


def test_deleted_data_keeps_scoped_authorship(http, db, sample, actors):
    staff = http('staff')
    created = staff.post('/api/activities?period_id=1', json={'name': 'Geçici faaliyet', 'subprogram_id': sample['subprogram'].id})
    assert created.status_code == 200, created.text
    assert staff.delete('/api/activities/'+str(created.json()['id'])+'?period_id=1').status_code == 200
    # Demote original Strategy director and promote the former data editor.
    strategy = http('strategy_director')
    assert strategy.post(f"/api/users/{actors['strategy_director'].id}/active", json={'active': False}).status_code == 200
    actors['staff'].role = 'strategy'; actors['staff'].department_id = actors['strategy_staff'].department_id; db.commit()
    assert http('strategy_staff').post(f"/api/users/{actors['staff'].id}/position", json={'position': 'director'}).status_code == 200
    assert http('director').post('/api/departments/1/submit?period_id=1').status_code == 200
    assert decision(staff, sample).status_code == 403


def make_report(http, db, sample, creator='strategy_staff'):
    # Build a valid legacy publication; report creation itself goes through HTTP.
    from app import activity_contract_service as service
    author = db.scalar(select(User).where(User.email == 'strategy_staff@example.invalid'))
    payload, definitions = service.freeze_program_payload(db, sample['period'].id, author)
    raw = service.canonical(payload)
    publication = Publication(period_id=sample['period'].id, version=1, snapshot_json=raw,
                              sha256=service.digest(raw), created_by=author.id)
    db.add(publication); db.flush(); service.attach_publication_definitions(db, publication, definitions, author); db.commit()
    response = http(creator).post('/api/activity-reports/revisions', json={'publication_id': publication.id,
        'organization_id': sample['department'].organization_id})
    assert response.status_code == 200, response.text
    revision = response.json()['revision_id']
    slot = db.scalar(select(ReportIndicator).where(ReportIndicator.report_revision_id == revision)).id
    return revision, slot


@pytest.mark.parametrize('form', [False, True])
def test_legacy_report_only_independent_strategy_director(http, db, sample, form):
    revision, slot = make_report(http, db, sample)
    assert http('staff').post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload()).status_code == 200
    path = ('' if form else '/api')+f'/activity-reports/revisions/{revision}/approve'
    assert http('strategy_staff').post(path).status_code == 403
    assert http('strategy_director').post(path).status_code == (303 if form else 200)
    assert db.scalar(select(func.count(ActivityReportApproval.id))) == 1


@pytest.mark.parametrize('authorship', ['creator', 'earlier_actual'])
@pytest.mark.parametrize('form', [False, True])
def test_legacy_report_any_authorship_blocks_approval(http, db, sample, authorship, form):
    revision, slot = make_report(http, db, sample, 'strategy_director' if authorship == 'creator' else 'strategy_staff')
    writer = http('strategy_director' if authorship == 'earlier_actual' else 'staff')
    assert writer.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload()).status_code == 200
    assert http('staff').post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(expected_revision=1)).status_code == 200
    path = ('' if form else '/api')+f'/activity-reports/revisions/{revision}/approve'
    response = http('strategy_director').post(path)
    assert response.status_code == 403 and 'Görevler ayrılığı' in response.text
    assert db.scalar(select(func.count(ActivityReportApproval.id))) == 0


def test_authorization_screens_show_scope_and_controls(http, actors):
    page = http('director').get('/submit-authorizations')
    assert page.status_code == 200 and actors['staff'].email in page.text
    assert actors['other'].email not in page.text and 'Yetki ver' in page.text and 'Yetkiyi kaldır' in page.text
    assert http('staff').get('/submit-authorizations').status_code == 403
    page = http('strategy_staff').get('/users')
    assert page.status_code == 200
    assert all(text in page.text for text in ['Unvanı kaydet', 'Personel', 'Müdür', 'PP gönderim yetkisi'])


@pytest.mark.parametrize('edit_kind', ['card', 'finance', 'economics', 'economic_verify', 'personnel', 'catalogue_unlink'])
def test_pp_edit_paths_retain_authorship(http, db, sample, actors, edit_kind):
    staff = http('staff')
    if edit_kind == 'card':
        response = staff.post('/program/1/cards', data={'period_id': 1, 'id': sample['card'].id,
            'subprogram_id': sample['subprogram'].id, 'goal': 'Yeni hedef'})
    elif edit_kind == 'finance':
        response = staff.post(f"/program/1/finance/{sample['activity'].id}", data={'period_id': 1, 'cost_2027_budget_inside': '130'})
    elif edit_kind == 'economics':
        response = staff.post('/program/1/economic', data={'period_id': 1, 'year': 2027,
            'value_kind': 'budget', 'category': 'goods_services', 'program_group': 'service', 'funding_type': 'inside', 'amount': '130'})
    elif edit_kind == 'economic_verify':
        from app.models import EconomicValue
        row = db.scalar(select(EconomicValue).where(EconomicValue.department_id == 1,
            EconomicValue.year == 2027, EconomicValue.category == 'goods_services',
            EconomicValue.funding_type == 'inside'))
        row.state = 'needs_review'; row.raw_text = '130'; db.commit()
        response = staff.post(f'/program/1/verify-money/economic/{row.id}?period_id=1',
            data={'amount': '130', 'program_group': 'service'})
    elif edit_kind == 'personnel':
        response = staff.post('/api/departments/1/personnel-costs?period_id=1', json={'cost_2027_budget': '25'})
    else:
        response = staff.post('/program/1/catalogue-link', data={'period_id': 1, 'activity_id': sample['activity'].id})
    assert response.status_code in (200, 303), response.text
    assert db.scalar(select(AuditLog.id).where(AuditLog.action == 'pp_data_change', AuditLog.user_id == actors['staff'].id))
    # Restore validity through a different HTTP actor; authorship must survive.
    if edit_kind == 'catalogue_unlink':
        assert http('authorized').post('/program/1/catalogue-link', data={'period_id': 1,
            'activity_id': sample['activity'].id, 'official_ids': sample['official'].id}).status_code == 303
    if edit_kind == 'card':
        assert http('authorized').post('/program/1/cards', data={'period_id': 1, 'id': sample['card'].id,
            'subprogram_id': sample['subprogram'].id, 'goal': 'Birinci hedef', 'rationale': 'Kaynak gerekçesi',
            'responsible': 'Test Belediyesi', 'explanation': 'Ortak açıklama', 'calculation_method': 'Kaynak yöntemi',
            'data_source': 'Kaynak kayıt'}).status_code == 303
    strategy = http('strategy_director')
    assert strategy.post(f"/api/users/{actors['strategy_director'].id}/active", json={'active': False}).status_code == 200
    actors['staff'].role = 'strategy'; actors['staff'].department_id = actors['strategy_staff'].department_id; db.commit()
    assert http('strategy_staff').post(f"/api/users/{actors['staff'].id}/position", json={'position': 'director'}).status_code == 200
    # The SoD check precedes financial revalidation; invalid totals cannot hide it.
    sub = db.scalar(select(Submission)); sub.status = 'submitted'; db.commit()
    response = decision(staff, sample)
    assert response.status_code == 403 and 'Görevler ayrılığı' in response.json()['detail']


def test_noop_and_other_department_edits_do_not_block_approval(http, db, sample, actors):
    strategy = http('strategy_director')
    assert strategy.post('/report-builder/scope', data={'period_id': 1, 'department_id': actors['other'].department_id,
        'status': 'excluded', 'reason': 'Kapsam dışında'}).status_code == 303
    # Existing scope has exactly these values, so this is not an edit.
    assert strategy.post('/report-builder/scope', data={'period_id': 1, 'department_id': 1,
        'status': 'required', 'position': 0, 'display_name': '', 'reason': ''}).status_code == 303
    assert http('director').post('/api/departments/1/submit?period_id=1').status_code == 200
    assert decision(strategy, sample).status_code == 200


@pytest.mark.parametrize('deleted', [False, True])
def test_pre_migration_audit_blocks_pilot_approval(http, db, sample, actors, deleted):
    db.add(AuditLog(id=-1, user_id=actors['strategy_director'].id, action='activity_mapping',
                    entity_type='activity', entity_id=99999 if deleted else sample['activity'].id))
    db.commit()
    assert http('director').post('/api/departments/1/submit?period_id=1').status_code == 200
    assert decision(http('strategy_director'), sample).status_code == 403


def test_concurrent_director_assignments_have_one_winner(http, db, actors):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.orm import Session
    strategy = http('strategy_staff')
    assert strategy.post(f"/api/users/{actors['director'].id}/position", json={'position': 'staff'}).status_code == 200
    clients = [http('strategy_staff'), http('strategy_staff')]
    target_ids = [actors['staff'].id, actors['authorized'].id]
    bind = db.get_bind()
    def independent_database():
        with Session(bind) as session:
            yield session
    app.dependency_overrides[get_db] = independent_database
    barrier = Barrier(2)
    def assign(index):
        barrier.wait(timeout=5)
        return clients[index].post(f'/api/users/{target_ids[index]}/position', json={'position': 'director'}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(assign, range(2))) == [200, 409]
    db.expire_all()
    assert db.scalar(select(func.count(User.id)).where(User.department_id == actors['staff'].department_id,
        User.position == 'director', User.is_active.is_(True))) == 1


def test_submitted_data_cannot_change_after_approval_check(http, db, sample):
    assert http('director').post('/api/departments/1/submit?period_id=1').status_code == 200
    response = http('strategy_staff').post('/report-builder/scope', data={'period_id': 1, 'department_id': 1,
        'status': 'required', 'display_name': 'Eşzamanlı değişiklik'})
    assert response.status_code == 409 and 'iade' in response.json()['detail']
    assert decision(http('strategy_director'), sample).status_code == 200


def test_economic_import_tracks_department_period_and_blocks_self_approval(http, db, sample, actors):
    from test_pp_import_submit_ready import source_document
    from app.models import EconomicValue

    period = sample['period']; period.template_status = 'verified'
    db.commit()
    strategy = http('strategy_director')
    preview = strategy.post(f'/api/periods/{period.id}/data-import-preview',
        files={'file': ('economic.docx', source_document())})
    assert preview.status_code == 200 and preview.json()['can_apply'], preview.text
    batch_id = preview.json()['batch_id']
    applied = strategy.post(f'/api/import-batches/{batch_id}/apply')
    assert applied.status_code == 200 and applied.json()['economic_values'] == 30, applied.text
    economic = db.scalar(select(EconomicValue).where(EconomicValue.source_table_number.is_not(None)))
    did = economic.department_id
    audit = db.scalar(select(AuditLog).where(AuditLog.action == 'pp_data_change',
        AuditLog.user_id == actors['strategy_director'].id, AuditLog.entity_id == did,
        AuditLog.details == f'period_id={period.id}'))
    assert audit is not None
    submission = db.scalar(select(Submission).where(Submission.department_id == did, Submission.period_id == period.id))
    submission.status = 'submitted'; db.commit()
    response = strategy.post(f'/api/submissions/{submission.id}/decision?period_id=1', json={'decision': 'approve'})
    assert response.status_code == 403 and 'Görevler ayrılığı' in response.json()['detail']
    # Imported economic review uses the same department scope and package lock.
    actors['authorized'].department_id = did; db.commit()
    writer = http('authorized')
    path = f'/program/{did}/verify-money/economic/{economic.id}?period_id=1'
    assert strategy.post(path, data={'amount': '100', 'program_group': 'service'}).status_code == 403
    assert writer.post(path, data={'amount': '100', 'program_group': 'service'}).status_code == 409
    submission.status = 'returned'; db.commit()
    assert writer.post(path, data={'amount': '100', 'program_group': 'service'}).status_code == 303
    assert db.scalar(select(AuditLog.id).where(AuditLog.action == 'pp_data_change',
        AuditLog.user_id == actors['authorized'].id, AuditLog.entity_id == did,
        AuditLog.details == f'period_id={period.id}'))


def test_economic_verification_reads_body_before_package_lock(http, db, sample, monkeypatch):
    from sqlalchemy import event
    from starlette.requests import Request
    from app.models import EconomicValue

    writer = http('staff')
    row = db.scalar(select(EconomicValue).where(EconomicValue.year == 2027,
        EconomicValue.category == 'goods_services', EconomicValue.funding_type == 'inside'))
    order = []
    original_form = Request.form

    def read_form(request, *args, **kwargs):
        order.append('body')
        return original_form(request, *args, **kwargs)

    def observe_lock(execution):
        if getattr(execution.statement, '_for_update_arg', None) is not None:
            order.append('lock')

    monkeypatch.setattr(Request, 'form', read_form)
    event.listen(db, 'do_orm_execute', observe_lock)
    try:
        response = writer.post(f'/program/1/verify-money/economic/{row.id}?period_id=1',
            data={'amount': '130', 'program_group': 'service'})
        assert response.status_code == 303, response.text
        assert 'body' in order and 'lock' in order
        assert max(i for i, step in enumerate(order) if step == 'body') < order.index('lock')
    finally:
        event.remove(db, 'do_orm_execute', observe_lock)
