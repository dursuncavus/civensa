"""CIV-174: approved 2027 + 2026 books, real migrations, HTTP and CSRF."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models import (AuditLog, Department, ImportBatch,
                        Indicator, OfficialActivity, Publication, ReportingPeriod, User)
from app.program_service import approved_book_provenance, publication_checks
from app.security import hash_password
from app.numbers import format_number
from scripts import first_load_live as live
from scripts.first_load_dryrun import inspect_import, local_test_url
from tests.first_load_checkpoint import disposable_first_load_database as disposable_database
from test_sidebar_ui import browser
import test_2026_screen_walk as existing_walk

pytestmark = pytest.mark.postgres
PASSWORD = 'Civ174-local-test-only!'


@pytest.fixture(scope='module')
def approved_books():
    parsed = live.verify_book(live.book_config(2026)[0], year=2026)
    with disposable_database(local_test_url()) as engine, Session(engine, expire_on_commit=False) as db:
        result = inspect_import(db, deepcopy(parsed), live.book_config(2026)[0].name, year=2026)
        assert not result['apply_error']
        assert result['protected_2027_before'] == result['protected_2027_after']
        assert len(result['catalogue']['unlinked']) == 174
        strategy = db.scalar(select(User).where(User.role == 'strategy'))
        strategy.department_id = db.scalar(select(Department.id).where(Department.name == 'Strateji Geliştirme Müdürlüğü'))
        strategy.position = 'director'
        strategy.password_hash = hash_password(PASSWORD)
        department = db.scalar(select(Department).where(Department.name == 'Plan Proje Müdürlüğü'))
        db.add(User(email='civ174@example.invalid', full_name='2026 birim kullanıcısı', role='department',
            department_id=department.id, position='director', can_submit=True, password_hash=hash_password(PASSWORD)))
        db.commit()
        yield engine


@pytest.fixture
def walk(approved_books):
    with approved_books.connect() as connection:
        transaction = connection.begin()
        with Session(connection, expire_on_commit=False, join_transaction_mode='create_savepoint') as db:
            app.dependency_overrides[get_db] = lambda: db
            client = TestClient(app, follow_redirects=False)
            strategy = db.scalar(select(User).where(User.role == 'strategy'))
            user = db.scalar(select(User).where(User.email == 'civ174@example.invalid'))
            def login(actor):
                client.cookies.clear()
                response = client.post('/login', data={'email':actor.email, 'password':PASSWORD})
                assert response.status_code == 303
                return re.search(r'name="csrf_token" value="([^"]+)"', client.get('/modules').text).group(1)
            token = login(strategy)
            try:
                yield db, client, strategy, user, login, token
            finally:
                client.close()
                app.dependency_overrides.clear()
        transaction.rollback()


def period(db, year=2026):
    return db.scalar(select(ReportingPeriod).where(ReportingPeriod.year == year))


def publish(client, token, pid, reason='Meclis kararı, 16.10.2025'):
    return client.post('/report-builder/publish-approved-book', data={
        'csrf_token':token, 'period_id':pid, 'approval_reference':reason})


def displayed_check_messages(db, pid, checks):
    from app.program_service import period_departments
    from app.structure_service import period_name
    names = {department.name:period_name(db, pid, department)
             for department in period_departments(db, pid)}
    messages = {}
    for check in checks:
        check_messages = list(check['errors']) + list(check.get('warnings', []))
        for system_name, display_name in sorted(names.items(), key=lambda item: -len(item[0])):
            if system_name != display_name:
                check_messages = [message.replace(system_name, display_name) for message in check_messages]
        messages.setdefault(check['id'].split(':', 1)[0], []).extend(check_messages)
    return messages


def publication_count(db):
    return db.scalar(select(func.count()).select_from(Publication))


@pytest.mark.parametrize('year', [2026, 2027])
def test_publish_approved_book_seals_warnings_and_provenance(walk, year):
    db, client, strategy, user, login, token = walk
    pid = period(db, year).id
    provenance = approved_book_provenance(db, pid)
    assert provenance is not None
    before = publication_checks(db, pid)
    assert 'action="/report-builder/publish-approved-book"' in client.get('/report-builder', params={'period_id':pid}).text
    response = publish(client, token, pid)
    assert response.status_code == 303, response.text[:1200]
    pub = db.scalar(select(Publication).where(Publication.period_id == pid))
    payload = json.loads(pub.snapshot_json)
    assert pub.version == 1
    assert hashlib.sha256(pub.snapshot_json.encode()).hexdigest() == pub.sha256
    assert payload['basis'] == 'approved_book'
    assert payload['book_sha256'] == live.book_config(year)[1]
    assert payload['load_reference'] == provenance['load_reference']
    assert payload['approval_reference'] == 'Meclis kararı, 16.10.2025'
    warnings = payload['kaynak_kitap_uyarilari']
    assert sum(item['error_count'] + item['warning_count'] for item in warnings) == sum(
        len(check['errors']) + len(check.get('warnings', [])) for check in before)
    messages_by_family = displayed_check_messages(db, pid, before)
    expected = {}
    for check in before:
        family = check['id'].split(':', 1)[0]
        summary = expected.setdefault(family, dict(check_count=0, error_count=0, warning_count=0, messages=set()))
        summary['check_count'] += 1
        summary['error_count'] += len(check['errors'])
        summary['warning_count'] += len(check.get('warnings', []))
    for family, summary in expected.items():
        summary['messages'].update(messages_by_family.get(family, []))
    assert warnings == [dict(check_family=family, check_count=summary['check_count'],
        error_count=summary['error_count'], warning_count=summary['warning_count'],
        unique_message_count=len(summary['messages']), examples=sorted(summary['messages'])[:20])
        for family, summary in sorted(expected.items())]
    assert db.scalar(select(AuditLog.id).where(AuditLog.action == 'publication_approved_book', AuditLog.entity_id == pub.id))
    page = client.get('/report-builder', params={'period_id':pid})
    assert f"Kaynak kitap uyarıları: {format_number(sum(item['error_count'] + item['warning_count'] for item in warnings))}" in page.text
    assert 'action="/report-builder/publish-approved-book"' not in page.text
    # Repeated submission must never produce v2, bindings, definitions or audit.
    before_rows = owned_counts(db)
    assert publish(client, token, pid).status_code == 409
    assert owned_counts(db) == before_rows


def test_2026_approved_book_warning_payload_is_compact_and_sealed(walk, monkeypatch):
    db, client, strategy, user, login, token = walk
    pid = period(db, 2026).id
    checks = publication_checks(db, pid)
    messages_by_family = displayed_check_messages(db, pid, checks)
    messages = sorted(message for family_messages in messages_by_family.values() for message in family_messages)
    assert len(messages) == 66_409
    response = publish(client, token, pid)
    assert response.status_code == 303, response.text[:1200]
    publication = db.scalar(select(Publication).where(Publication.period_id == pid))
    payload = json.loads(publication.snapshot_json)
    warning_payload = json.dumps(payload['kaynak_kitap_uyarilari'], ensure_ascii=False,
                                  sort_keys=True, separators=(',', ':')).encode()
    assert len(warning_payload) < 100_000
    assert hashlib.sha256(json.dumps(messages, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == (
        payload['kaynak_kitap_uyarilari_sha256'])
    audit = db.scalar(select(AuditLog).where(
        AuditLog.action == 'publication_approved_book', AuditLog.entity_id == publication.id))
    assert json.loads(audit.details)['warning_count'] == 66_409
    snapshot = publication.snapshot_json
    db.expire(publication, ['snapshot_json'])
    from app import publication_history as history_module
    loads = history_module.loads
    def reject_snapshot_load(value, *args, **kwargs):
        assert value != snapshot, 'report builder parsed Publication.snapshot_json'
        return loads(value, *args, **kwargs)
    monkeypatch.setattr(history_module, 'loads', reject_snapshot_load)
    page = client.get('/report-builder', params={'period_id':pid})
    assert page.status_code == 200
    assert 'Onay dayanağı: Meclis kararı, 16.10.2025' in page.text
    assert f'Kaynak kitap uyarıları: {format_number(66_409)}' in page.text


def owned_counts(db):
    from app.models import IndicatorDefinitionRevision, IndicatorIdentity, PublicationIndicatorBinding
    return [db.scalar(select(func.count()).select_from(model)) for model in
            (Publication, IndicatorIdentity, IndicatorDefinitionRevision, PublicationIndicatorBinding, AuditLog)]


@pytest.mark.parametrize('year', [2026, 2027])
def test_normal_publish_preserves_exact_rejection(walk, year):
    db, client, strategy, user, login, token = walk
    pid = period(db, year).id
    errors = [error for check in publication_checks(db, pid) for error in check['errors']]
    from app.program_service import period_departments
    from app.structure_service import period_name
    names = {d.name:period_name(db,pid,d) for d in period_departments(db,pid)}
    for system, display in sorted(names.items(), key=lambda item:-len(item[0])):
        if system != display:
            errors = [error.replace(system, display) for error in errors]
    expected = 'Nihai yayın oluşturulamadı: ' + ' '.join(errors) + ' İlgili müdürlük kayıtlarını, kapsamı ve onayları tamamlayıp yeniden deneyin.'
    response = client.post('/report-builder/publish', headers={'accept':'application/json'},
                           data={'csrf_token':token, 'period_id':pid})
    assert response.status_code == 422
    assert response.json()['detail'] == expected
    assert publication_count(db) == 0


@pytest.mark.parametrize('failure', ['department', 'csrf', 'empty', 'missing', 'wrong_sha', 'partial', 'edited', 'edited_2027', 'catalogue', 'section', 'program', 'value', 'scope', 'catalogue_edit', 'reverted_edit', 'reverted_catalogue', 'reverted_activity'])
def test_refused_without_publication_side_effects(walk, failure):
    db, client, strategy, user, login, token = walk
    pid = period(db, 2027 if failure == 'edited_2027' else 2026).id
    status = 409
    if failure == 'department':
        token = login(user)
        status = 403
        assert client.get('/report-builder', params={'period_id':pid}).status_code == 403
    elif failure == 'csrf':
        token = 'wrong-token'
        status = 403
    elif failure == 'empty':
        status = 422
    elif failure in {'missing', 'wrong_sha', 'partial'}:
        audit = db.scalar(select(AuditLog).join(ImportBatch, ImportBatch.id == AuditLog.entity_id).where(
            AuditLog.action == 'first_load_department', ImportBatch.period_id == pid))
        if failure == 'wrong_sha':
            proof = json.loads(audit.details); proof['book_sha256'] = '0' * 64
            audit.details = json.dumps(proof)
        elif failure == 'partial':
            batch = db.get(ImportBatch, audit.entity_id); batch.status = 'reverted'
        else:
            db.delete(audit)
    elif failure in {'edited', 'edited_2027', 'reverted_edit'}:
        indicator = db.scalar(select(Indicator).where(Indicator.period_id == pid))
        original = indicator.name
        indicator.name += ' değişti'
        if failure == 'reverted_edit':
            indicator.name = original
            db.add(AuditLog(user_id=strategy.id, action='indicator_update', entity_type='indicator', entity_id=indicator.id))
    elif failure == 'catalogue':
        # No catalogue must fail even when its normal gate would be only a warning.
        from app.models import ActivityCatalogueLink, ActivityResponsibility
        ids = select(OfficialActivity.id).where(OfficialActivity.period_id == pid)
        db.execute(ActivityCatalogueLink.__table__.delete().where(ActivityCatalogueLink.official_activity_id.in_(ids)))
        db.execute(ActivityResponsibility.__table__.delete().where(ActivityResponsibility.official_activity_id.in_(ids)))
        db.execute(OfficialActivity.__table__.delete().where(OfficialActivity.period_id == pid))
    elif failure in {'reverted_catalogue', 'reverted_activity'}:
        from app.models import Activity
        model = OfficialActivity if failure == 'reverted_catalogue' else Activity
        item = db.scalar(select(model).where(model.period_id == pid))
        db.add(AuditLog(user_id=strategy.id,
            action='catalogue_create' if failure == 'reverted_catalogue' else 'finance_save',
            entity_type='official_activity' if failure == 'reverted_catalogue' else 'activity', entity_id=item.id))
    elif failure == 'catalogue_edit':
        item = db.scalar(select(OfficialActivity).where(OfficialActivity.period_id == pid)); item.name += ' değişti'
    elif failure == 'section':
        from app.models import ReportSection
        db.add(ReportSection(period_id=pid, title='Sonradan eklenen bölüm', kind='text'))
    elif failure == 'program':
        from app.models import Program
        item = db.scalar(select(Program).where(Program.period_id == pid)); item.name += ' değişti'
    elif failure == 'scope':
        from app.models import DepartmentScope
        item = db.scalar(select(DepartmentScope).where(DepartmentScope.period_id == pid)); item.reason = 'Değişiklik'
    elif failure == 'value':
        from app.models import IndicatorValue
        item = db.scalar(select(IndicatorValue).join(Indicator).where(Indicator.period_id == pid)); item.raw_text = 'değişti'
    db.commit()
    before = owned_counts(db)
    if failure not in {'department', 'csrf', 'empty'}:
        assert 'action="/report-builder/publish-approved-book"' not in client.get('/report-builder', params={'period_id':pid}).text
    response = publish(client, token, pid, '  ' if failure == 'empty' else 'Meclis kararı, 16.10.2025')
    assert response.status_code == status, response.text[:1200]
    assert owned_counts(db) == before
    if status == 409:
        assert 'normal yayın yolunu kullanın' in response.text


def test_published_2026_actuals_workflow_and_word(walk):
    db, client, strategy, user, login, token = walk
    pid = period(db).id
    response = publish(client, token, pid)
    assert response.status_code == 303, response.text[:1200]
    pub = db.scalar(select(Publication).where(Publication.period_id == pid))
    frozen = pub.snapshot_json, pub.sha256
    department = db.get(Department, user.department_id)
    # Existing revision creation is Strategy-only; preserve that authorization.
    response = client.post('/activity-reports/revisions', data={'csrf_token':token,
        'publication_id':pub.id, 'organization_id':department.organization_id})
    assert response.status_code == 303, response.text[:1200]
    response = client.post('/activity-sections/years', data={'csrf_token':token,
        'period_id':pid, 'organization_id':department.organization_id})
    assert response.status_code == 303, response.text[:1200]
    existing_walk.test_actual_entry_submit_and_strategy_review(walk)
    db.refresh(pub)
    assert (pub.snapshot_json, pub.sha256) == frozen


@pytest.mark.parametrize('width', [390, 1280])
def test_approved_book_button_and_history_screens(walk, browser, width):
    from playwright.sync_api import expect
    db, client, strategy, user, login, token = walk
    pid = period(db).id
    with browser.new_context(viewport={'width':width, 'height':900}) as context:
        failures = []
        def serve(route):
            request = route.request
            response = client.request(request.method, request.url, content=request.post_data_buffer,
                # Resolve redirect chains locally: Playwright routes only the first URL.
                headers={'content-type':request.headers.get('content-type','')}, follow_redirects=True)
            if response.status_code >= 400:
                failures.append((request.method, request.url, response.status_code, response.text[:1000]))
            headers = dict(response.headers); headers.pop('set-cookie', None)
            route.fulfill(status=response.status_code, headers=headers, body=response.content)
        context.route('http://testserver/**', serve)
        page = context.new_page()
        # Full first-load reconciliation is much larger than the small UI seeds.
        page.set_default_timeout(120_000)
        page.set_default_navigation_timeout(120_000)
        page.goto(f'http://testserver/report-builder?period_id={pid}')
        form = page.locator('#approved-book-publication')
        expect(form).to_be_visible()
        form.scroll_into_view_if_needed()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        folder = os.getenv('CIVENSA_UI_SCREENSHOTS')
        if folder:
            Path(folder).mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(Path(folder) / f'button-{width}.png'))
        page.get_by_label('Onay dayanağı', exact=True).fill('Meclis kararı, 16.10.2025')
        form.get_by_role('button', name='Onaylı kitaptan yayınla', exact=True).click()
        expect(page.locator('#approved-book-publication')).to_have_count(0)
        assert not failures, failures
        history = page.locator('#publication-history')
        history.scroll_into_view_if_needed()
        expect(history).to_contain_text('Onaylı kitaptan yayın')
        expect(history).to_contain_text('Kaynak kitap uyarıları: 66.409')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        if folder:
            page.screenshot(path=str(Path(folder) / f'history-{width}.png'))
