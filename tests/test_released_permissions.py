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
    return client.post('/api/submissions/1/decision', json={'decision': action, 'note': 'Kaynağı kontrol edip yeniden gönderin.'})


@pytest.mark.parametrize('actor', ['director', 'authorized'])
def test_director_and_authorized_staff_submit(http, sample, actor):
    response = http(actor).post(f"/api/departments/{sample['department'].id}/submit")
    assert response.status_code == 200 and response.json()['revision'] == 1


def test_unauthorized_staff_refused_and_csrf_required(http, db, sample):
    client = http('staff')
    assert client.get('/department/1').status_code == 200
    assert http('strategy_staff').get('/department/1').status_code == 200
    response = client.post('/api/departments/1/submit')
    assert response.status_code == 403
    assert all(word in response.json()['detail'] for word in ['Müdür', 'Personel', 'Gönderim Yetkileri', 'Kullanıcılar'])
    assert db.scalar(select(Submission)).status == 'draft'
    assert db.scalar(select(func.count(SubmissionEvent.id))) == 0
    client = http('director'); client.headers.pop('X-CSRF-Token')
    assert client.post('/api/departments/1/submit').status_code == 403


@pytest.mark.parametrize('grantor', ['director', 'strategy_staff'])
def test_grant_revoke_scopes_audits_and_existing_session(http, db, actors, grantor):
    staff = http('staff'); authority = http(grantor)
    path = f"/api/users/{actors['staff'].id}/submit-authorization"
    assert authority.post(path, json={'can_submit': True}).status_code == 200
    # A session opened before the grant sees it immediately.
    assert staff.post('/api/departments/1/submit').status_code == 200
    assert decision(http('strategy_director'), None, 'return').status_code == 200
    assert authority.post(path, json={'can_submit': False}).status_code == 200
    assert staff.post('/api/departments/1/submit').status_code == 403
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
    assert http('staff').post('/api/departments/1/submit').status_code == 200
    logs = db.scalars(select(AuditLog).where(AuditLog.action == 'user_position_change').order_by(AuditLog.id)).all()
    assert [(a.entity_id, json.loads(a.details)['old'], json.loads(a.details)['new']) for a in logs] == [
        (actors['director'].id, 'director', 'staff'), (actors['staff'].id, 'staff', 'director')]
    assert all(a.user_id == actors['strategy_staff'].id and a.created_at for a in logs)


def test_director_reactivation_conflict_and_new_staff_default(http, db, actors):
    strategy = http('strategy_staff')
    director_path = f"/api/users/{actors['director'].id}"
    assert strategy.post(director_path+'/active', json={'active': False}).status_code == 200
    assert strategy.post(f"/api/users/{actors['staff'].id}/position", json={'position': 'director'}).status_code == 200
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
    assert http('director').post('/api/departments/1/submit').status_code == 200
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
    assert http('director').post('/api/departments/1/submit').status_code == 200
    blocked = decision(strategy, sample)
    assert blocked.status_code == 403 and 'Görevler ayrılığı' in blocked.json()['detail']
    assert db.scalar(select(Submission)).status == 'submitted'
    assert db.scalar(select(AuditLog).where(AuditLog.action == 'pp_data_change', AuditLog.user_id == actors['strategy_director'].id))
    assert decision(strategy, sample, 'return').status_code == 200
    assert http('director').post('/api/departments/1/submit').status_code == 200
    assert decision(strategy, sample).status_code == 200


def test_prior_editor_still_blocked_after_role_change_and_another_edit(http, db, sample, actors):
    editor = http('strategy_director')
    # Before promotion the same person was a department data editor.
    actors['strategy_director'].role = 'department'
    actors['strategy_director'].department_id = actors['other'].department_id
    actors['strategy_director'].position = 'staff'
    db.commit()
    actors['strategy_director'].department_id = sample['department'].id; db.commit()
    assert editor.post('/api/indicators/1/save', json={'value_2027_target': '3'}).status_code == 200
    assert http('staff').post('/api/indicators/1/save', json={'value_2027_target': '4'}).status_code == 200
    actors['strategy_director'].role = 'strategy'
    actors['strategy_director'].department_id = actors['strategy_staff'].department_id
    actors['strategy_director'].position = 'director'; db.commit()
    assert http('director').post('/api/departments/1/submit').status_code == 200
    assert decision(editor, sample).status_code == 403


def test_deleted_data_keeps_scoped_authorship(http, db, sample, actors):
    staff = http('staff')
    created = staff.post('/api/activities', json={'name': 'Geçici faaliyet', 'subprogram_id': sample['subprogram'].id})
    assert created.status_code == 200, created.text
    assert staff.delete('/api/activities/'+str(created.json()['id'])).status_code == 200
    # Demote original Strategy director and promote the former data editor.
    strategy = http('strategy_director')
    assert strategy.post(f"/api/users/{actors['strategy_director'].id}/position", json={'position': 'staff'}).status_code == 200
    actors['staff'].role = 'strategy'; actors['staff'].department_id = actors['strategy_staff'].department_id; db.commit()
    assert strategy.post(f"/api/users/{actors['staff'].id}/position", json={'position': 'director'}).status_code == 200
    assert http('director').post('/api/departments/1/submit').status_code == 200
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


@pytest.mark.parametrize('edit_kind', ['card', 'finance', 'economics', 'personnel', 'catalogue_unlink'])
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
    elif edit_kind == 'personnel':
        response = staff.post('/api/departments/1/personnel-costs', json={'cost_2027_budget': '25'})
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
    assert strategy.post(f"/api/users/{actors['strategy_director'].id}/position", json={'position': 'staff'}).status_code == 200
    actors['staff'].role = 'strategy'; actors['staff'].department_id = actors['strategy_staff'].department_id; db.commit()
    assert strategy.post(f"/api/users/{actors['staff'].id}/position", json={'position': 'director'}).status_code == 200
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
    assert http('director').post('/api/departments/1/submit').status_code == 200
    assert decision(strategy, sample).status_code == 200


@pytest.mark.parametrize('deleted', [False, True])
def test_pre_migration_audit_blocks_pilot_approval(http, db, sample, actors, deleted):
    db.add(AuditLog(id=-1, user_id=actors['strategy_director'].id, action='activity_mapping',
                    entity_type='activity', entity_id=99999 if deleted else sample['activity'].id))
    db.commit()
    assert http('director').post('/api/departments/1/submit').status_code == 200
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
    assert http('director').post('/api/departments/1/submit').status_code == 200
    response = http('strategy_staff').post('/report-builder/scope', data={'period_id': 1, 'department_id': 1,
        'status': 'required', 'display_name': 'Eşzamanlı değişiklik'})
    assert response.status_code == 409 and 'iade' in response.json()['detail']
    assert decision(http('strategy_director'), sample).status_code == 200
