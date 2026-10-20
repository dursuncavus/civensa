"""CIV-018: Strategy master data over actual login/session/CSRF on PostgreSQL."""
import csv
import re
import html
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi import HTTPException
from sqlalchemy import select, func, inspect, text
from sqlalchemy.orm import Session

from app.models import (AuditLog, Department, DepartmentScope, Program, SubProgram,
                        SubProgramScope, ReportingPeriod, Organization, User, Publication,
                        ReportSection, Submission, SubmissionEvent, ReportCard, Indicator, Activity)
from app.master_data_service import check_department_name, normalized_name
from tests.test_live_pilot_hardening import live_client, login
from tests.test_authorization_foundation import foundation_db

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[1]
REVISION = 'b018a1c2d3e4'
BASE_REVISION = 'a6c006e9b241'


def post(browser, token, url, **data):
    return browser.post(url, data={'csrf_token': token, 'period_id': 1, **data})


def strategy(live_client, sample):
    browser = live_client()
    return browser, login(browser, sample['strategy'].email)


def test_department_lifecycle_and_audit_without_plan_links(db, sample, live_client):
    browser, token = strategy(live_client, sample)
    name = 'İşletme ve İştirakler Müdürlüğü'
    assert post(browser, token, '/structure/departments', organization_id=sample['department'].organization_id, name=name).status_code == 303
    dept = db.scalar(select(Department).where(Department.name == name))
    assert dept.is_active
    assert not db.scalar(select(DepartmentScope.id).where(DepartmentScope.department_id == dept.id))
    assert not db.scalar(select(ReportCard.id).where(ReportCard.department_id == dept.id))
    renamed = 'İşletme ve İştirakler Yeni Müdürlüğü'
    assert post(browser, token, f'/structure/departments/{dept.id}/rename', name=renamed).status_code == 303
    for state in ('0', '1'):
        assert post(browser, token, f'/structure/departments/{dept.id}/active', active=state).status_code == 303
        db.refresh(dept)
        assert dept.is_active == (state == '1')
    logs = db.scalars(select(AuditLog).where(AuditLog.entity_type == 'departments', AuditLog.entity_id == dept.id).order_by(AuditLog.id)).all()
    assert [r.action for r in logs] == ['department_create', 'department_rename', 'department_active', 'department_active']
    assert all(r.user_id == sample['strategy'].id and r.created_at for r in logs)
    assert json.loads(logs[1].details) == {'old': {'name': name}, 'new': {'name': renamed}}
    assert json.loads(logs[2].details)['new']['is_active'] is False


@pytest.mark.parametrize('variant', ['Park Ve Bahçeler Müdürlüğü', '  park  ve\tbahçeler müdürlüğü  ', 'PARK VE BAHÇELER MÜDÜRLÜĞÜ'])
def test_duplicate_names_refused_on_create_and_rename_with_values_kept(db, sample, live_client, variant):
    original = Department(organization_id=sample['department'].organization_id, name='PARK VE BAHÇELER MÜDÜRLÜĞÜ')
    db.add(original); db.commit()
    browser, token = strategy(live_client, sample)
    count = db.scalar(select(func.count(Department.id)))
    for url, extra in [('/structure/departments', {'organization_id': original.organization_id}),
                       (f'/structure/departments/{sample["department"].id}/rename', {})]:
        response = post(browser, token, url, name=variant, **extra)
        assert response.status_code == 409, response.text
        assert '“PARK VE BAHÇELER MÜDÜRLÜĞÜ” kaydıyla aynı' in response.text
        assert 'farklı bir ad girin' in response.text
        form = re.search(r'<form[^>]*action="' + re.escape(url) + r'"[^>]*>(.*?)</form>', response.text, re.S).group(1)
        assert html.unescape(re.search(r'name="name"[^>]*value="([^"]*)"', form).group(1)) == variant
    assert db.scalar(select(func.count(Department.id))) == count
    db.refresh(sample['department'])
    assert sample['department'].name == 'Test Müdürlüğü'


@pytest.mark.parametrize('left,right', [('İŞLETME', 'işletme'), ('IŞIK', 'ışık'), ('IŞIK', 'Işık'), ('I\u0307ŞLETME', 'işletme')])
def test_turkish_normalization(left, right):
    assert normalized_name(left) == normalized_name(right)
    assert normalized_name('I') != normalized_name('i')


def test_deactivate_keeps_history_blocks_all_new_account_and_scope_paths(db, sample, live_client):
    browser, token = strategy(live_client, sample)
    did = sample['department'].id
    future = ReportingPeriod(year=2028); db.add(future); db.commit()
    before = {m: db.scalar(select(func.count()).select_from(m)) for m in (Indicator, Activity, ReportCard, User, DepartmentScope)}
    assert post(browser, token, f'/structure/departments/{did}/active', active='0').status_code == 303
    db.refresh(sample['department']); assert not sample['department'].is_active
    account = {'email': 'new@example.invalid', 'full_name': 'Yeni Kullanıcı', 'role': 'department', 'password': 'test-only-password', 'department_id': did}
    result = browser.post('/api/users', headers={'X-CSRF-Token': token}, json=account)
    assert result.status_code == 422 and 'pasif' in result.text and 'Kurum Yapısı' in result.text
    for url in ['/structure/scopes', '/report-builder/scope']:
        response = post(browser, token, url, period_id=future.id, department_id=did, status='required')
        assert response.status_code == 422 and 'pasif' in response.text
        if url == '/structure/scopes':
            assert re.search(r'<option value="' + str(did) + r'" selected>', response.text)
    sample['user'].is_active = False; db.commit()
    from app.main import ACCOUNT_CSV_HEADERS
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(ACCOUNT_CSV_HEADERS)
    writer.writerow([did, sample['department'].name, 'Yeni Kullanıcı', 'new@example.invalid', 'Personel'])
    for url in ['/api/users/bulk-preview', '/api/users/bulk-import']:
        response = browser.post(url, headers={'X-CSRF-Token': token}, files={'file': ('accounts.csv', output.getvalue().encode())})
        assert 'pasif' in response.text
        assert not response.json().get('ok', False)
    assert sample['department'].name not in browser.get('/api/users/missing-departments.csv').text
    for m, count in before.items(): assert db.scalar(select(func.count()).select_from(m)) == count
    assert post(browser, token, f'/structure/departments/{did}/active', active='1').status_code == 303
    assert browser.post('/api/users', headers={'X-CSRF-Token': token}, json=account).status_code == 200
    assert post(browser, token, '/structure/scopes', period_id=future.id, department_id=did, status='required').status_code == 303


NEW_ROUTES = [
    ('GET', '/structure'), ('GET', '/structure?period_id=bad'),
    ('POST', '/structure/departments'), ('POST', '/structure/departments/1/rename'),
    ('POST', '/structure/departments/1/active'), ('POST', '/structure/programs'),
    ('POST', '/structure/programs/1'), ('POST', '/structure/subprograms'),
    ('POST', '/structure/subprograms/1'), ('POST', '/structure/subprograms/1/responsibilities'),
    ('POST', '/structure/scopes'), ('POST', '/periods/create'),
]


@pytest.mark.parametrize('method,url', NEW_ROUTES)
def test_directorate_gets_turkish_403_on_every_new_route(db, sample, live_client, method, url):
    browser = live_client(); token = login(browser, sample['user'].email)
    response = browser.get(url) if method == 'GET' else post(browser, token, url)
    assert response.status_code == 403, response.text
    assert 'yalnızca Strateji Geliştirme' in response.text
    assert 'iletişime geçin' in response.text
    assert 'href="/structure"' not in browser.get('/modules').text


@pytest.mark.parametrize('method,url', NEW_ROUTES)
def test_new_routes_require_session_and_csrf(db, sample, live_client, method, url):
    browser = live_client()
    response = browser.request(method, url, params={'period_id': 1})
    assert response.status_code == 401
    if method == 'POST':
        login(browser, sample['strategy'].email)
        response = browser.post(url, data={'csrf_token': 'wrong'})
        assert response.status_code == 403 and 'Güvenlik doğrulaması' in response.text


def test_programme_subprogramme_scope_assignment_is_period_bound(db, sample, live_client):
    browser, token = strategy(live_client, sample)
    pid = sample['period'].id
    future = ReportingPeriod(year=2028); dept = Department(organization_id=sample['department'].organization_id, name='Yeni Müdürlüğü')
    db.add_all([future, dept]); db.commit()
    assert post(browser, token, '/structure/programs', period_id=pid, name='Çevre').status_code == 303
    program = db.scalar(select(Program).where(Program.name == 'Çevre'))
    assert post(browser, token, f'/structure/programs/{program.id}', period_id=pid, name='Yaşanabilir Çevre').status_code == 303
    assert post(browser, token, '/structure/subprograms', period_id=pid, program_id=program.id, name='Parklar', rationale='İlk gerekçe', goal='İlk hedef').status_code == 303
    sp = db.scalar(select(SubProgram).where(SubProgram.name == 'Parklar'))
    assert post(browser, token, f'/structure/subprograms/{sp.id}', period_id=pid, name='Yeşil Alanlar', rationale='Yeni gerekçe', goal='Yeni hedef').status_code == 303
    response = post(browser, token, f'/structure/subprograms/{sp.id}/responsibilities', period_id=pid, department_ids=[dept.id, sample['department'].id])
    assert response.status_code == 303, response.text
    links = db.scalars(select(DepartmentScope).join(SubProgramScope, SubProgramScope.scope_id == DepartmentScope.id).where(SubProgramScope.subprogram_id == sp.id)).all()
    assert {s.department_id for s in links} == {dept.id, sample['department'].id}
    assert all(s.period_id == pid and s.status == 'required' for s in links)
    assert not db.scalar(select(DepartmentScope.id).where(DepartmentScope.period_id == future.id))
    db.refresh(sp); assert (sp.name, sp.rationale, sp.goal) == ('Yeşil Alanlar', 'Yeni gerekçe', 'Yeni hedef')
    assert 'Yeşil Alanlar' in browser.get(f'/structure?period_id={pid}').text
    assert 'Yeşil Alanlar' not in browser.get(f'/structure?period_id={future.id}').text
    for url, data in [(f'/structure/programs/{program.id}', {'name': 'Wrong'}),
                      (f'/structure/subprograms/{sp.id}', {'name': 'Wrong'}),
                      ('/structure/subprograms', {'name': 'Wrong', 'program_id': program.id}),
                      (f'/structure/subprograms/{sp.id}/responsibilities', {'department_ids': [dept.id]})]:
        assert post(browser, token, url, period_id=future.id, **data).status_code == 422
    assert post(browser, token, '/structure/scopes', period_id=pid, department_id=dept.id, status='excluded', reason='Test').status_code == 422
    assert post(browser, token, f'/structure/subprograms/{sp.id}/responsibilities', period_id=pid).status_code == 303
    assert not db.scalar(select(SubProgramScope.scope_id).where(SubProgramScope.subprogram_id == sp.id))
    assert post(browser, token, '/structure/scopes', period_id=pid, department_id=dept.id, status='excluded', reason='Sorumluluk yok').status_code == 303
    for action in ['program_create', 'program_update', 'subprogram_create', 'subprogram_update', 'subprogram_responsibilities', 'structure_scope_save']:
        logs = db.scalars(select(AuditLog).where(AuditLog.action == action)).all()
        assert logs and all(r.user_id == sample['strategy'].id and r.created_at and set(json.loads(r.details)) == {'old', 'new'} for r in logs)


def test_inactive_responsibilities_cannot_be_new_but_existing_remain(db, sample, live_client):
    browser, token = strategy(live_client, sample)
    pid = sample['period'].id; did = sample['department'].id; spid = sample['subprogram'].id
    url = f'/structure/subprograms/{spid}/responsibilities'
    assert post(browser, token, f'/structure/departments/{did}/active', active='0').status_code == 303
    response = post(browser, token, url, period_id=pid, department_ids=[did])
    assert response.status_code == 422
    assert re.search(r'name="department_ids" value="' + str(did) + r'" checked', response.text)
    assert 'Pasif · yeni atama yapılamaz' in response.text
    assert post(browser, token, f'/structure/departments/{did}/active', active='1').status_code == 303
    assert post(browser, token, url, period_id=pid, department_ids=[did]).status_code == 303
    assert post(browser, token, f'/structure/departments/{did}/active', active='0').status_code == 303
    assert post(browser, token, url, period_id=pid, department_ids=[did]).status_code == 303
    assert 'Pasif · mevcut sorumluluk' in browser.get('/structure').text


def test_rename_leaves_publication_and_approved_snapshot_names_frozen(db, sample, live_client):
    browser, token = strategy(live_client, sample)
    submission = db.scalar(select(Submission)); submission.status = 'submitted'; submission.revision = 1
    db.add(ReportSection(period_id=sample['period'].id, title='Genel Bilgiler', content_json='{"text":"Onaylı içerik"}')); db.commit()
    response = browser.post(f'/api/submissions/{submission.id}/decision?period_id=1', headers={'X-CSRF-Token': token}, json={'decision': 'approve'})
    assert response.status_code == 200, response.text
    approved = db.scalar(select(SubmissionEvent).where(SubmissionEvent.event_type == 'approve'))
    assert approved
    assert post(browser, token, '/report-builder/publish', period_id=sample['period'].id).status_code == 303
    pub = db.scalar(select(Publication)); before = pub.snapshot_json; approved_before = approved.snapshot_json
    # Fixture for the next editable working revision: CIV-025 locks approved
    # content. Editing this copy must still leave both frozen snapshots intact.
    submission.status = 'returned'; submission.revision += 1; db.commit()
    for url, data in [
        (f'/structure/departments/{sample["department"].id}/rename', {'name': 'Yeni Müdürlük'}),
        (f'/structure/programs/{sample["subprogram"].program_id}', {'period_id': sample['period'].id, 'name': 'Yeni Program'}),
        (f'/structure/subprograms/{sample["subprogram"].id}', {'period_id': sample['period'].id, 'name': 'Yeni Alt Program', 'goal': 'Yeni hedef', 'rationale': 'Yeni gerekçe'}),
    ]:
        assert post(browser, token, url, **data).status_code == 303
    db.expire_all()
    assert pub.snapshot_json == before and approved.snapshot_json == approved_before
    result = browser.get(f'/publications/{pub.id}.json')
    assert result.status_code == 200 and result.text == before
    for name in ['Test Müdürlüğü', 'Test Programı', 'Test Alt Programı']:
        assert name in before and name in approved_before
    assert 'Yeni Alt Program' not in result.text


@pytest.mark.parametrize('year', ['2027', 'bad', '2019', '2101', '2027.5', ''])
def test_period_form_has_same_validation_as_api(db, live_client, sample, year):
    if year == '2027':
        # Existing-period clash is the same for API and form.
        expected = 409
    else: expected = 422
    browser, token = strategy(live_client, sample)
    form = post(browser, token, '/periods/create', year=year)
    api = browser.post('/api/periods', headers={'X-CSRF-Token': token}, json={'year': year})
    assert form.status_code == api.status_code == expected
    assert api.json()['detail'] in form.text
    assert f'value="{year}"' in form.text


def test_empty_installation_dashboard_and_first_period_creation(db):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import get_db
    from app.security import hash_password
    org = Organization(name='Yeni Belediyesi')
    user = User(email='setup@example.invalid', full_name='Strateji', role='strategy', password_hash=hash_password('setup-test-only'))
    db.add_all([org, user]); db.commit()
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app, follow_redirects=False) as browser:
            token = login(browser, user.email, 'setup-test-only')
            response = browser.get('/dashboard')
            assert response.status_code == 200 and 'İlk dönemi oluştur' in response.text and '/periods/create' in response.text
            assert 'Henüz raporlama dönemi yok' in browser.get('/structure').text
            assert post(browser, token, '/periods/create', year='2027').status_code == 303
            p = db.scalar(select(ReportingPeriod))
            assert (p.year, p.status, p.template_status) == (2027, 'draft', 'pending')
            assert browser.get('/dashboard').status_code == 200
            assert '2027' in browser.get('/structure').text
            assert json.loads(db.scalar(select(AuditLog).where(AuditLog.action == 'period_create')).details)['new']['year'] == 2027
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize('foundation_db', [BASE_REVISION], indirect=True)
def test_migration_with_case_duplicates_warning_and_non_destructive_downgrade(foundation_db):
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    db = foundation_db
    # Raw SQL seeds the actual old schema: the model already has the new column.
    db.execute(text("INSERT INTO organizations (id,name) VALUES (1,'Pilot Belediyesi')"))
    for did, name in enumerate(['PARK VE BAHÇELER MÜDÜRLÜĞÜ', 'Park Ve Bahçeler Müdürlüğü'], 1):
        db.execute(text('INSERT INTO departments (id,organization_id,name) VALUES (:id,1,:name)'), {'id': did, 'name': name})
    db.commit()
    env = {**os.environ, 'DATABASE_URL': db.bind.url.render_as_string(hide_password=False)}
    def migrate(action, revision):
        result = subprocess.run([sys.executable, '-m', 'alembic', action, revision], cwd=ROOT, env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    migrate('upgrade', 'head')
    scripts = ScriptDirectory.from_config(Config(str(ROOT / 'alembic.ini')))
    assert db.execute(text('SELECT version_num FROM alembic_version')).scalar() == scripts.get_current_head()
    departments = db.scalars(select(Department).order_by(Department.id)).all()
    assert [d.name for d in departments] == ['PARK VE BAHÇELER MÜDÜRLÜĞÜ', 'Park Ve Bahçeler Müdürlüğü']
    assert all(d.is_active for d in departments)
    from app.main import app
    from app.db import get_db
    from app.security import hash_password
    from fastapi.testclient import TestClient
    user = User(email='pilot@example.invalid', role='strategy', full_name='Strateji', password_hash=hash_password('pilot-test-only'))
    p = ReportingPeriod(year=2027)
    db.add_all([user, p]); db.commit()
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app, follow_redirects=False) as browser:
            token = login(browser, user.email, 'pilot-test-only')
            page = browser.get('/structure')
            assert page.status_code == 200
            warning = re.search(r'<section class="structure-warning">(.*?)</section>', page.text, re.S).group(1)
            assert 'Aynı müdürlük olabilecek kayıtlar' in warning
            assert all(d.name in warning for d in departments)
            assert post(browser, token, '/structure/departments/2/active', active='0').status_code == 303
    finally: app.dependency_overrides.clear()
    pr = Program(period_id=p.id, name='Program'); db.add(pr); db.flush()
    sp = SubProgram(period_id=p.id, program_id=pr.id, name='Alt'); scope = DepartmentScope(period_id=p.id, department_id=1)
    db.add_all([sp, scope]); db.flush(); db.add(SubProgramScope(subprogram_id=sp.id, scope_id=scope.id)); db.commit()
    migrate('downgrade', BASE_REVISION)
    assert not db.get(Department, 2).is_active
    assert db.scalar(select(func.count(SubProgramScope.scope_id))) == 1
    db.commit(); migrate('upgrade', 'head')
    assert db.scalar(select(func.count(SubProgramScope.scope_id))) == 1
    assert not db.get(Department, 2).is_active


def test_concurrent_equivalent_department_creation_is_serialized(db, sample):
    oid = sample['department'].organization_id
    db.commit(); gate = Barrier(2)
    def create(name):
        with Session(db.get_bind()) as worker:
            gate.wait(timeout=10)
            try:
                check_department_name(worker, oid, name)
                worker.add(Department(organization_id=oid, name=name)); worker.commit()
                return 201
            except HTTPException as exc:
                worker.rollback(); return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(create, ['PARK VE BAHÇELER MÜDÜRLÜĞÜ', 'Park Ve Bahçeler Müdürlüğü'])) == [201, 409]
    assert db.scalar(select(func.count(Department.id))) == 2


def test_real_2027_preview_matches_base_and_preserves_master_data(db, sample, live_client):
    """Keep the base's applicable preview and warnings without applying the import.

    Preview must preserve row counts and every existing master/report value,
    including CIV-018 lifecycle, rationale/goal and scope responsibilities.
    """
    source = ROOT / 'tests/fixtures/pp2027_source_no_media.docx'
    assert source.exists(), 'Real 2027 fixture must be present'
    browser, token = strategy(live_client, sample)
    db.add(Department(organization_id=sample['department'].organization_id,
                      name='İşletme ve İştirakler Müdürlüğü', is_active=False))
    sample['subprogram'].rationale = 'Kurum Yapısı gerekçesi'
    sample['subprogram'].goal = 'Kurum Yapısı hedefi'
    scope = db.scalar(select(DepartmentScope).where(
        DepartmentScope.period_id == sample['period'].id,
        DepartmentScope.department_id == sample['department'].id))
    db.add(SubProgramScope(subprogram_id=sample['subprogram'].id, scope_id=scope.id))
    db.commit()
    models = (Department, Program, SubProgram, Indicator, Activity,
              DepartmentScope, SubProgramScope)
    before = {m: db.scalar(select(func.count()).select_from(m)) for m in models}

    def stored_rows(model):
        table = model.__table__
        return db.execute(select(*table.columns).order_by(*table.primary_key.columns)).all()

    values_before = {model: stored_rows(model) for model in models}
    preview = browser.post(f'/api/periods/{sample["period"].id}/data-import-preview',
        headers={'X-CSRF-Token': token}, files={'file': (source.name, source.read_bytes(),
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document')})
    assert preview.status_code == 200, preview.text
    payload = preview.json()
    # Observed with the same sample/login/CSRF on the base branch at c29a13c,
    # which includes CIV-010's restored real-source import support.
    assert payload['can_apply'] is True
    assert payload['warnings'] == [
        "'Park Ve Bahçeler Müdürlüğü' başlığı 'Park ve Bahçeler Müdürlüğü' ile aynı müdürlük olarak birleştirildi.",
        "'AFET İŞLERİ VE RİSK YÖNETİMİ MÜDÜRLÜĞÜ' başlığı 'Afet İşleri Ve Risk Yönetimi Müdürlüğü' ile aynı müdürlük olarak birleştirildi.",
        "'DESTEK HİZMETLERİ MÜDÜRLÜĞÜ' başlığı 'Destek Hizmetleri Müdürlüğü' ile aynı müdürlük olarak birleştirildi.",
    ]
    for model, count in before.items():
        assert db.scalar(select(func.count()).select_from(model)) == count
        assert stored_rows(model) == values_before[model]


def test_hierarchy_validation_keeps_attempted_fields_and_prevents_duplicates(db, sample, live_client):
    browser, token = strategy(live_client, sample)
    pid = sample['period'].id
    for url, fields in [
        ('/structure/programs', {'name': 'TEST PROGRAMI'}),
        ('/structure/subprograms', {'program_id': sample['subprogram'].program_id, 'name': 'TEST ALT PROGRAMI', 'rationale': 'Deneme gerekçesi', 'goal': 'Deneme hedefi'}),
    ]:
        result = post(browser, token, url, period_id=pid, **fields)
        assert result.status_code == 409 and 'farklı bir ad girin' in result.text
        form = re.search(r'<form[^>]*action="' + re.escape(url) + r'"[^>]*>(.*?)</form>', result.text, re.S).group(1)
        for value in fields.values(): assert str(value) in html.unescape(form)
    for url, fields in [('/structure/departments', {'organization_id': sample['department'].organization_id, 'name': ' '}),
                        ('/structure/programs', {'period_id': pid, 'name': 'x' * 251}),
                        ('/structure/scopes', {'period_id': pid, 'department_id': sample['department'].id, 'status': 'excluded', 'reason': ''})]:
        response = post(browser, token, url, **fields)
        assert response.status_code == 422 and 'Değişiklik kaydedilemedi' in response.text


@pytest.mark.parametrize('url', ['/structure/departments/bad/rename', '/structure/departments/bad/active',
                                '/structure/programs/bad', '/structure/subprograms/bad',
                                '/structure/subprograms/bad/responsibilities'])
def test_invalid_record_ids_show_turkish_form_errors(db, sample, live_client, url):
    browser, token = strategy(live_client, sample)
    response = post(browser, token, url, period_id=sample['period'].id, name='Deneme', active='0')
    assert response.status_code == 422
    assert 'geçersiz' in response.text and 'mevcut bir kayıt seçin' in response.text


def test_existing_scope_route_records_old_new_and_respects_subprogramme_assignments(db, sample, live_client):
    browser, token = strategy(live_client, sample)
    pid = sample['period'].id; did = sample['department'].id
    assert post(browser, token, '/report-builder/scope', period_id=pid, department_id=did, status='required', position='7', display_name='Dönem Müdürlüğü', reason='Yeni kapsam açıklaması').status_code == 303
    log = db.scalar(select(AuditLog).where(AuditLog.action == 'scope_save'))
    assert json.loads(log.details)['new'] == {'status': 'required', 'position': 7, 'display_name': 'Dönem Müdürlüğü', 'reason': 'Yeni kapsam açıklaması'}
    assert json.loads(log.details)['old']['display_name'] == ''
    assert post(browser, token, f'/structure/subprograms/{sample["subprogram"].id}/responsibilities', period_id=pid, department_ids=[did]).status_code == 303
    result = post(browser, token, '/report-builder/scope', period_id=pid, department_id=did, status='excluded', reason='Test')
    assert result.status_code == 422 and 'sorumluluğu kaldırıp' in result.text


def test_inactive_history_stays_visible_but_does_not_require_new_period_scope(db, sample, live_client):
    from app.models import OfficialActivity
    from app.program_service import book_snapshot
    browser, token = strategy(live_client, sample)
    pid = sample['period'].id; did = sample['department'].id
    active = Department(organization_id=sample['department'].organization_id, name='Etkin Müdürlüğü')
    db.add(active); db.commit()
    assert post(browser, token, f'/structure/departments/{did}/active', active='0').status_code == 303
    sample['user'].is_active = False; db.commit()
    progress = browser.get('/api/progress').json()
    assert progress['summary']['missing_accounts'] == 1  # Only the active new department.
    assert any(r['department_id'] == did and not r['is_active'] for r in progress['rows'])
    assert 'Pasif müdürlük' in browser.get('/dashboard').text
    # History is still available in the original period, including live previews.
    assert did in {d['department_id'] for d in book_snapshot(db, pid)['departments']}
    before = {model: db.scalar(select(func.count()).select_from(model).where(model.period_id == pid)) for model in (ReportCard, Indicator, Activity, DepartmentScope, Submission)}
    response = browser.post('/api/periods', headers={'X-CSRF-Token': token}, json={'year': 2028, 'base_period_id': pid})
    assert response.status_code == 200, response.text
    new_pid = response.json()['id']
    for model, count in before.items():
        assert db.scalar(select(func.count()).select_from(model).where(model.period_id == pid)) == count
        assert not db.scalar(select(model.id).where(model.period_id == new_pid, model.department_id == did))
    assert did not in {d['department_id'] for d in book_snapshot(db, new_pid)['departments']}
    assert post(browser, token, '/structure/scopes', period_id=new_pid, department_id=active.id, status='excluded', reason='Yeni dönem veri kapsamı yok').status_code == 303
    db.add_all([ReportSection(period_id=new_pid, title='Genel Bilgiler', content_json='{"text":"Yeni dönem"}'),
                OfficialActivity(period_id=new_pid, program_name='Katalog', subprogram_name='Alt', code='1', name='Faaliyet')]); db.commit()
    # Publication never demands a forbidden new scope for an inactive department.
    response = post(browser, token, '/report-builder/publish', period_id=new_pid)
    assert response.status_code == 303, response.text
    payload = json.loads(db.scalar(select(Publication).where(Publication.period_id == new_pid)).snapshot_json)
    assert did not in {d['department_id'] for d in payload['departments']}
