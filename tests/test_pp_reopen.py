"""CIV-072: reasoned reopening uses the ordinary PP correction/review cycle."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
import os
from pathlib import Path
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi import HTTPException
from playwright.sync_api import expect, sync_playwright
from sqlalchemy import event, func, select, text
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app
from app.models import (AuditLog, BudgetOperation, Department, DepartmentScope, Notification, Organization,
                        Publication, ReportSection, Submission, SubmissionEvent, User)
from app.program_service import department_snapshot
from app.serialization import json_dumps
from tests.test_released_permissions import actors, http
from tests.test_budget_reallocation import budget, preview, apply as apply_budget

pytestmark = pytest.mark.postgres
REASON = 'Gösterge hedefini kaynak belgeye göre düzeltin.'


@pytest.fixture
def approved(db, sample):
    sub = db.scalar(select(Submission))
    sub.status = 'approved'
    sub.revision = 1
    db.commit()
    return sub


def reopen(client, sub, reason=REASON):
    return client.post(f'/api/submissions/{sub.id}/reopen?period_id={sub.period_id}',
                       json={'reason': reason})


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_reopen_records_approved_snapshot_reason_notification_and_audit(db, sample, approved, http, actors):
    strategy = http('strategy_director')
    before = json_dumps(department_snapshot(db, approved.period_id, approved.department_id), ensure_ascii=False)
    response = reopen(strategy, approved, '  ' + REASON + '  ')
    assert response.status_code == 200, response.text
    assert response.json() == {'ok': True, 'status': 'returned'}
    db.refresh(approved)
    assert (approved.status, approved.return_note, approved.revision) == ('returned', REASON, 1)
    ev = db.scalar(select(SubmissionEvent))
    assert (ev.event_type, ev.note, ev.snapshot_json) == ('reopen', REASON, before)
    assert (ev.actor_user_id, ev.department_id, ev.period_id, ev.revision) == (
        actors['strategy_director'].id, approved.department_id, approved.period_id, 1)
    notice = db.scalar(select(Notification))
    assert (notice.role, notice.department_id, notice.event_type) == ('department', approved.department_id, 'submission_reopen')
    assert REASON in notice.message
    assert notice.link == f'/department/{approved.department_id}?period_id={approved.period_id}'
    audit = db.scalar(select(AuditLog).where(AuditLog.action == 'submission_reopen'))
    assert (audit.user_id, audit.entity_type, audit.entity_id) == (ev.actor_user_id, 'submission', approved.id)
    assert json.loads(audit.details) == {'revision': 1, 'reason': REASON}
    assert count(db, SubmissionEvent) == count(db, Notification) == 1
    page = http('director').get(notice.link)
    assert 'Düzeltme için açıldı' in page.text
    assert 'Bilinmeyen işlem (reopen)' not in page.text


@pytest.mark.parametrize('reason', ['', ' \n\t ', None, False, 123, [], {}])
def test_reason_must_be_nonblank_text(db, approved, http, reason):
    response = reopen(http('strategy_director'), approved, reason)
    assert response.status_code == 422, response.text
    assert response.json()['errors'][0]['field'] == 'reason'
    assert 'Gerekçe' in response.json()['detail']
    assert_no_reopen(db, approved)


def assert_no_reopen(db, sub):
    db.refresh(sub)
    assert sub.status == 'approved'
    assert count(db, SubmissionEvent) == count(db, Notification) == 0
    assert not db.scalar(select(AuditLog.id).where(AuditLog.action == 'submission_reopen'))


@pytest.mark.parametrize('status', ['draft', 'submitted', 'returned'])
def test_only_approved_packages_can_reopen(db, approved, http, status):
    approved.status = status
    db.commit()
    response = reopen(http('strategy_director'), approved)
    assert response.status_code == 409
    assert 'Yalnızca onaylanmış paket' in response.json()['detail']
    db.refresh(approved)
    assert approved.status == status
    assert count(db, SubmissionEvent) == count(db, Notification) == 0


@pytest.mark.parametrize('actor', ['strategy_staff', 'director', 'staff', 'other'])
def test_only_strategy_director_can_reopen(db, approved, http, actor):
    response = reopen(http(actor), approved)
    assert response.status_code == 403, response.text
    assert_no_reopen(db, approved)


def test_inactive_session_cannot_reopen(db, approved, http, actors):
    strategy = http('strategy_director')
    actors['strategy_director'].is_active = False
    db.commit()
    assert reopen(strategy, approved).status_code == 403
    assert_no_reopen(db, approved)


def test_other_organization_director_cannot_reopen(db, approved, http, actors):
    strategy = http('strategy_director')
    org = Organization(name='Başka Belediye')
    db.add(org); db.flush()
    dep = Department(name='Strateji Geliştirme Müdürlüğü', organization_id=org.id)
    db.add(dep); db.flush()
    actors['strategy_director'].department_id = dep.id
    db.commit()
    assert reopen(strategy, approved).status_code == 403
    assert_no_reopen(db, approved)


@pytest.mark.parametrize('period_status', ['closed', 'draft'])
def test_period_status(db, sample, approved, http, period_status):
    sample['period'].status = period_status
    db.commit()
    response = reopen(http('strategy_director'), approved)
    assert response.status_code == (409 if period_status == 'closed' else 200), response.text
    if period_status == 'closed':
        assert 'kapalı' in response.json()['detail']
        assert_no_reopen(db, approved)


def test_period_context_and_csrf_are_required(db, approved, http):
    strategy = http('strategy_director')
    path = f'/api/submissions/{approved.id}/reopen'
    assert strategy.post(path, json={'reason': REASON}).status_code == 422
    assert strategy.post(path + '?period_id=99999', json={'reason': REASON}).status_code == 404
    strategy.headers.pop('X-CSRF-Token')
    assert reopen(strategy, approved).status_code == 403
    assert_no_reopen(db, approved)


def test_full_cycle_preserves_publication_and_creates_next_version(db, sample, approved, http):
    strategy, department = http('strategy_director'), http('director')
    db.add(ReportSection(period_id=approved.period_id, title='Genel Bilgiler', kind='text',
                         content_json='{"text":"Onaylı içerik"}'))
    db.commit()
    for dep in db.scalars(select(Department).where(Department.id != approved.department_id)):
        db.add(DepartmentScope(period_id=approved.period_id, department_id=dep.id, status='excluded', reason='Bu test döneminde PP verisi yok.'))
    db.commit()
    publish = lambda: strategy.post('/report-builder/publish', data={'period_id': approved.period_id})
    response = publish()
    assert response.status_code == 303, response.text
    old = db.scalar(select(Publication))
    before = (old.version, old.snapshot_json, old.sha256)
    response = strategy.post('/api/activity-reports/revisions', json={
        'publication_id': old.id, 'organization_id': sample['department'].organization_id})
    assert response.status_code == 200, response.text
    report_path = f'/api/activity-reports/revisions/{response.json()["revision_id"]}'
    report_before = strategy.get(report_path).json()
    assert reopen(strategy, approved).status_code == 200
    assert publish().status_code == 422
    db.refresh(old)
    assert (old.version, old.snapshot_json, old.sha256) == before
    assert count(db, Publication) == 1
    assert department.post(f'/api/indicators/{sample["indicator"].id}/save?period_id={approved.period_id}',
                           json={'value_2027_target': '2,5'}).status_code == 200
    response = department.post(f'/api/departments/{approved.department_id}/submit?period_id={approved.period_id}')
    assert response.status_code == 200, response.text
    assert response.json()['revision'] == 2
    path = f'/api/submissions/{approved.id}/decision?period_id={approved.period_id}'
    assert strategy.post(path, json={'decision': 'approve'}).status_code == 200
    response = publish()
    assert response.status_code == 303, response.text
    db.expire_all()
    versions = db.scalars(select(Publication).order_by(Publication.version)).all()
    assert len(versions) == 2 and versions[1].version == before[0] + 1
    assert (versions[0].version, versions[0].snapshot_json, versions[0].sha256) == before
    assert versions[1].snapshot_json != before[1] and versions[1].sha256 != before[2]
    assert [(ev.event_type, ev.revision) for ev in db.scalars(select(SubmissionEvent).order_by(SubmissionEvent.id))] == [
        ('reopen', 1), ('submitted', 2), ('approve', 2)]
    assert '2.5' in versions[1].snapshot_json
    report_after = strategy.get(report_path).json()
    assert report_after['publication_id'] == old.id
    assert report_after['indicators'] == report_before['indicators']
    assert report_after['newer_publication_available']


def test_independence_uses_latest_reopen_boundary(db, sample, approved, http, actors):
    strategy, department = http('strategy_director'), http('director')
    # An old edit predates the correction cycle and must not block its approval.
    db.add(AuditLog(user_id=actors['strategy_director'].id, action='pp_data_change',
                    entity_type='department', entity_id=approved.department_id,
                    details=f'period_id={approved.period_id}', created_at=sample_time()))
    db.commit()
    assert reopen(strategy, approved).status_code == 200
    # Real Strategy scope edit is tracked by the ordinary authorship hook.
    assert strategy.post('/report-builder/scope', data={'period_id': approved.period_id,
        'department_id': approved.department_id, 'status': 'required', 'display_name': 'Düzeltilmiş Müdürlük'}).status_code == 303
    assert department.post(f'/api/departments/{approved.department_id}/submit?period_id={approved.period_id}').status_code == 200
    path = f'/api/submissions/{approved.id}/decision?period_id={approved.period_id}'
    response = strategy.post(path, json={'decision': 'approve'})
    assert response.status_code == 403 and 'Görevler ayrılığı' in response.json()['detail']
    # An ordinary return starts another cycle; prior edits no longer exclude the actor.
    assert strategy.post(path, json={'decision': 'return', 'note': REASON}).status_code == 200
    assert department.post(f'/api/departments/{approved.department_id}/submit?period_id={approved.period_id}').status_code == 200
    assert strategy.post(path, json={'decision': 'approve'}).status_code == 200
    # The latest reopen must also supersede the earlier return boundary.
    assert reopen(strategy, approved).status_code == 200
    assert department.post(f'/api/departments/{approved.department_id}/submit?period_id={approved.period_id}').status_code == 200
    assert strategy.post(path, json={'decision': 'approve'}).status_code == 200


def test_reopen_excludes_edits_before_its_boundary(db, sample, approved, http, actors):
    strategy, department = http('strategy_director'), http('director')
    before = sample_time()
    db.add(SubmissionEvent(submission_id=approved.id, department_id=approved.department_id,
        period_id=approved.period_id, actor_user_id=actors['strategy_director'].id,
        event_type='return', revision=1, note='Önceki iade', created_at=before))
    db.add(AuditLog(user_id=actors['strategy_director'].id, action='pp_data_change',
        entity_type='department', entity_id=approved.department_id,
        details=f'period_id={approved.period_id}', created_at=before + timedelta(hours=1)))
    db.commit()
    assert reopen(strategy, approved).status_code == 200
    assert department.post(f'/api/departments/{approved.department_id}/submit?period_id={approved.period_id}').status_code == 200
    response = strategy.post(f'/api/submissions/{approved.id}/decision?period_id={approved.period_id}',
                             json={'decision': 'approve'})
    assert response.status_code == 200, response.text


def sample_time():
    from datetime import datetime, UTC
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)


def test_budget_preview_before_reopen_cannot_apply(db, sample, budget, http):
    strategy = http('strategy_director')
    planned = preview(strategy, budget)
    sub = db.scalar(select(Submission).where(Submission.department_id == sample['department'].id))
    assert reopen(strategy, sub).status_code == 200
    response = apply_budget(strategy, planned)
    assert response.status_code == 409, response.text
    assert 'önizlemesindeki müdürlük verileri değişti' in response.json()['detail']
    fresh = strategy.post('/api/budget-reallocations/preview', json=budget)
    assert fresh.status_code == 422 and 'onaylı değil' in fresh.json()['detail']
    assert count(db, BudgetOperation) == 0


@pytest.mark.parametrize('failed_model', [SubmissionEvent, Notification, AuditLog])
def test_reopen_is_one_transaction(db, approved, http, failed_model):
    strategy = http('strategy_director')
    def fail(mapper, connection, target):
        if failed_model is not AuditLog or target.action == 'submission_reopen':
            raise RuntimeError('injected persistence failure')
    event.listen(failed_model, 'before_insert', fail)
    try:
        with pytest.raises(RuntimeError, match='injected persistence failure'):
            reopen(strategy, approved)
    finally:
        event.remove(failed_model, 'before_insert', fail)
        db.rollback()
    assert_no_reopen(db, approved)


def test_concurrent_reopen_has_one_event(db, sample, approved, monkeypatch):
    from app import pp_reopen_routes as routes
    reopen_submission = routes.reopen_submission
    original_check, original_snapshot = routes.check_reopen, routes.department_snapshot
    checked = threading.local()
    both_checked = threading.Barrier(2)
    def check(*args):
        result = original_check(*args)
        if not getattr(checked, 'initial', False):
            checked.initial = True
            both_checked.wait(timeout=10)
        return result
    def snapshot(*args):
        # Winner holds both locks. Prove the other request is actually waiting
        # on the department lock before allowing the winner to commit.
        wait_for_department_lock(db.get_bind())
        return original_snapshot(*args)
    monkeypatch.setattr(routes, 'check_reopen', check)
    monkeypatch.setattr(routes, 'department_snapshot', snapshot)
    sid, pid, actor_id = approved.id, approved.period_id, sample['strategy'].id
    entered = threading.Barrier(2)
    class Request:
        query_params = {'period_id': str(pid)}
        async def json(self):
            entered.wait(timeout=10)  # Both bodies are consumed before any locks.
            return {'reason': REASON}
    def call():
        with Session(db.get_bind(), expire_on_commit=False) as session:
            try:
                return asyncio.run(reopen_submission(sid, Request(), session, session.get(User, actor_id)))
            except HTTPException as error:
                session.rollback()
                return {'status': error.status_code}
    db.rollback()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(call) for _ in range(2)]
        results = [future.result(timeout=20) for future in futures]
    assert sum(result.get('ok') is True for result in results) == 1
    assert sum(result.get('status') == 409 for result in results) == 1
    db.expire_all()
    assert count(db, SubmissionEvent) == count(db, Notification) == 1
    assert count(db, AuditLog) == 1


def wait_for_department_lock(bind):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        with bind.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
            if connection.scalar(text("SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND wait_event_type = 'Lock' "
                    "AND query LIKE '%departments%FOR UPDATE%'")):
                return
        threading.Event().wait(0.02)
    pytest.fail('Reopen did not wait for the held department lock')


@pytest.mark.parametrize('changed', ['status', 'period', 'authority'])
def test_reopen_rechecks_after_department_lock_wait(db, sample, approved, changed):
    from app.pp_reopen_routes import reopen_submission
    sid, pid, did, uid = approved.id, approved.period_id, approved.department_id, sample['strategy'].id
    class Request:
        query_params = {'period_id': str(pid)}
        async def json(self):
            return {'reason': REASON}
    def call():
        with Session(db.get_bind(), expire_on_commit=False) as session:
            try:
                return asyncio.run(reopen_submission(sid, Request(), session, session.get(User, uid)))
            except HTTPException as error:
                session.rollback()
                return error.status_code
    db.rollback()
    with Session(db.get_bind()) as blocker, ThreadPoolExecutor(max_workers=1) as pool:
        blocker.scalar(select(Department).where(Department.id == did).with_for_update())
        future = pool.submit(call)
        try:
            wait_for_department_lock(db.get_bind())
            if changed == 'status':
                blocker.get(Submission, sid).status = 'returned'
            elif changed == 'period':
                from app.models import ReportingPeriod
                blocker.get(ReportingPeriod, pid).status = 'closed'
            else:
                blocker.get(User, uid).is_active = False
            blocker.commit()
        finally:
            blocker.rollback()
        assert future.result(timeout=15) == (403 if changed == 'authority' else 409)
    db.expire_all()
    assert count(db, SubmissionEvent) == count(db, Notification) == 0
    assert not db.scalar(select(AuditLog.id).where(AuditLog.action == 'submission_reopen'))


@pytest.fixture
def review_http(db, http):
    # Serve the real authenticated app to Chromium with a Session per request.
    selected = [http('strategy_director')]
    previous = app.dependency_overrides[get_db]
    def database():
        with Session(db.get_bind(), expire_on_commit=False) as session:
            yield session
    app.dependency_overrides[get_db] = database
    class Handler(BaseHTTPRequestHandler):
        def serve(self):
            body = self.rfile.read(int(self.headers.get('content-length', '0')))
            response = selected[0].request(self.command, self.path, content=body,
                headers={'content-type': self.headers.get('content-type', ''),
                         'X-CSRF-Token': self.headers.get('X-CSRF-Token', '')}, follow_redirects=False)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in {'content-length', 'transfer-encoding', 'connection', 'set-cookie'}:
                    self.send_header(key, value)
            self.send_header('Content-Length', str(len(response.content)))
            self.end_headers(); self.wfile.write(response.content)
        do_GET = do_POST = serve
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', selected
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)
        app.dependency_overrides[get_db] = previous


def test_browser_reopen_visibility_and_turkish_error(db, sample, approved, http, review_http):
    base, selected = review_http
    with sync_playwright() as pw:
        options = {'headless': True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'):
            options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        with pw.chromium.launch(**options) as browser, browser.new_page(viewport={'width': 1440, 'height': 1000}) as page:
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(base + f'/review?period_id={approved.period_id}')
            control = page.get_by_role('button', name='Onaylı paketi düzeltme için aç', exact=True)
            expect(control).to_be_visible()
            reason = page.get_by_label('Düzeltme gerekçesi', exact=True)
            reason.fill('   ')
            control.click()
            assert not errors, errors
            expect(page.locator('[data-reopen-form] .return-note')).to_contain_text('Gerekçe zorunlu')
            expect(reason).to_have_value('   ')
            page.goto(base + f'/review?period_id={approved.period_id}')
            reason.fill(REASON)
            if os.getenv('CIVENSA_UI_SCREENSHOTS'):
                folder = Path(os.environ['CIVENSA_UI_SCREENSHOTS']); folder.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(folder / 'civ-072-review-reopen.png'), full_page=True)
            # Exercise the actual successful control as well as the error path.
            control.click()
            expect(control).to_have_count(0)
            expect(page.get_by_text('Düzeltme için açıldı', exact=True)).to_be_visible()
            db.refresh(approved)
            assert approved.status == 'returned'
            for status in ['draft', 'submitted', 'returned']:
                approved.status = status; db.commit()
                page.reload()
                expect(control).to_have_count(0)
            approved.status = 'approved'
            sample['period'].status = 'closed'; db.commit()
            page.reload()
            expect(control).to_have_count(0)
            sample['period'].status = 'active'; db.commit()
            selected[0] = http('strategy_staff')
            page.reload()
            expect(control).to_have_count(0)
            selected[0] = http('director')
            page.reload()
            expect(control).to_have_count(0)
            assert not errors
