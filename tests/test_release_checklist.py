"""CIV-067: narrow technical scope and actual, audited PP acceptance."""
import os
import pytest
from sqlalchemy import select

from app.main import app, require_user
from app.models import AuditLog, ReleaseConfirmation, ReportSection, ReportingPeriod, Submission
from app.release_service import MANUAL
from tests.test_release_readiness_migration_head import readiness, migrated_template
from tests.test_publication_gates import prepare

pytestmark = pytest.mark.postgres
URL = '/api/release/confirmations?period_id=1'


def confirm(client, payload, key='D1', **extra):
    return client.post(URL, json=dict(item_id=key, decision='confirmed',
        reason='Kaynak ve kullanıcı kabulü incelendi.', evidence='Kabul tutanağı 2027/1; sorumlu: Ayşe Yılmaz',
        context_sha256=payload['release']['context_sha256'], **extra))


def test_technical_pass_does_not_claim_release_ready(readiness, db, sample):
    prepare(db, sample)
    payload = readiness()
    assert {'status', 'version', 'checks', 'warnings', 'migration', 'checked_at'} <= payload.keys()
    assert payload['scope'] == 'technical' and payload['status'] == 'ready'
    assert all(c['status'] == 'Geçti' for c in payload['release']['automatic'])
    assert payload['release']['status'] == 'Elle onay bekliyor'
    assert set(m['id'] for m in payload['release']['manual']) == set(MANUAL)
    assert payload['release']['live_role_verification']['status'] == 'Doğrulanmadı'
    assert next(m for m in payload['release']['manual'] if m['id'] == 'PP-19')['status'] == 'Doğrulanmadı'
    for item in payload['release']['automatic'] + payload['release']['manual']:
        assert {'status', 'evidence', 'owner', 'source', 'next_step'} <= item.keys()


def test_existing_workflow_approval_names_the_approver_in_evidence(readiness, client, db, sample):
    app.dependency_overrides[require_user] = lambda: sample['user']
    assert client.post('/api/departments/1/submit?period_id=1').status_code == 200
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    assert client.post('/api/submissions/1/decision?period_id=1', json={'decision': 'approve'}).status_code == 200
    evidence = next(c['evidence']['observed'] for c in readiness()['release']['automatic']
        if c['id'] == 'publication:approval:1')
    assert evidence['approval_event_id']
    assert evidence['approver'] == sample['strategy'].full_name
    assert evidence['approver_id'] == sample['strategy'].id
    assert evidence['submission']['status'] == 'approved'


def test_every_manual_gate_required_and_revocation_is_a_new_audited_event(readiness, client, db, sample):
    prepare(db, sample)
    payload = readiness()
    for key in MANUAL:
        assert readiness()['release']['status'] != 'Hazır'
        response = confirm(client, payload, key, actor_name='Sahte isim', actor_id=999, created_at='2000-01-01')
        assert response.status_code == 200, response.text
        event = response.json()
        assert event['actor_name'] == sample['strategy'].full_name
        assert event['actor_id'] == sample['strategy'].id
        assert not event['created_at'].startswith('2000')
        audit = db.scalar(select(AuditLog).where(AuditLog.entity_id == event['id'],
            AuditLog.action == 'release_manual_confirmation'))
        assert audit and event['evidence'] in audit.details
    assert readiness()['release']['status'] == 'Hazır'
    response = client.post(URL, json=dict(item_id='D1', decision='revoked', reason='Yeni bulgu',
        evidence='Kabul tutanağı eki 2', context_sha256=payload['release']['context_sha256']))
    assert response.status_code == 200
    assert readiness()['release']['status'] == 'Elle onay bekliyor'
    events = db.scalars(select(ReleaseConfirmation).where(ReleaseConfirmation.item_id == 'D1')
        .order_by(ReleaseConfirmation.id)).all()
    assert [e.decision for e in events] == ['confirmed', 'revoked']
    assert len(readiness()['release']['history']) == len(MANUAL) + 1


@pytest.mark.parametrize('problem, expected', [
    ('scope', 'kapsam'), ('approval', 'onay eksik'), ('section', 'genel bilgi'),
    ('finance', 'finansman bilgisi eksik'), ('source', 'personel ve SGK gideri eksik'),
    ('economic_zero', 'ekonomik gider hücresi eksik'), ('mismatch', 'uyuşmuyor'),
    ('catalogue_link', 'kataloğu bağlantısı eksik'), ('excluded_with_data', 'kapsam dışı müdürlükte veri var'),
])
def test_readiness_uses_the_publication_gates(readiness, client, db, sample, problem, expected):
    # Use the exact existing regression scenario, then compare read-only evidence.
    from tests.test_publication_gates import test_invalid_package_cannot_publish
    test_invalid_package_cannot_publish(client, db, sample, problem, expected)
    payload = readiness()
    assert payload['release']['status'] == 'Engelli'
    failures = [c for c in payload['release']['automatic'] if c['status'] == 'Engelli']
    assert any(expected in str(c['evidence']) for c in failures)
    assert all(c['next_step'] for c in failures)
    assert db.scalar(select(ReleaseConfirmation)) is None


@pytest.mark.parametrize('change', ['book', 'approval', 'account'])
def test_changed_context_invalidates_manual_acceptance(readiness, client, db, sample, change):
    prepare(db, sample)
    before = readiness()
    assert confirm(client, before).status_code == 200
    if change == 'book': db.scalar(select(ReportSection)).title = 'Değişen bölüm'
    elif change == 'approval': db.scalar(select(Submission)).status = 'submitted'
    else: sample['user'].can_submit = False
    db.commit()
    after = readiness()
    assert after['release']['context_sha256'] != before['release']['context_sha256']
    assert next(m for m in after['release']['manual'] if m['id'] == 'D1')['evidence'] is None
    assert len(after['release']['history']) == 1
    assert confirm(client, before).status_code == 409


@pytest.mark.parametrize('data', [
    {}, {'item_id': 'database'}, {'item_id': []}, {'decision': []}, {'reason': ''},
    {'evidence': ''}, {'reason': 42}, {'evidence': 'x' * 8001},
])
def test_manual_confirmation_validates_without_writing(readiness, client, db, data):
    payload = readiness()
    body = dict(item_id='D1', decision='confirmed', reason='Gerekçe', evidence='Kanıt',
        context_sha256=payload['release']['context_sha256'])
    if not data: body.pop('reason')
    else: body.update(data)
    response = client.post(URL, json=body)
    assert response.status_code == 422
    assert db.scalar(select(ReleaseConfirmation)) is None


def test_period_authorization_and_no_edit_delete_endpoints(readiness, client, db, sample):
    payload = readiness()
    assert client.post('/api/release/confirmations', json={}).status_code == 422
    db.add(ReportingPeriod(year=2028)); db.commit()
    response = client.post('/api/release/confirmations?period_id=2', json=dict(item_id='D1',
        decision='confirmed', reason='gerekçe', evidence='kanıt', context_sha256=payload['release']['context_sha256']))
    assert response.status_code == 409
    assert confirm(client, payload).status_code == 200
    for method in ['put', 'patch', 'delete']:
        assert getattr(client, method)('/api/release/confirmations/1?period_id=1').status_code in {404, 405}
    app.dependency_overrides[require_user] = lambda: sample['user']
    assert confirm(client, payload).status_code == 403
    assert client.get('/api/release/readiness').status_code == 403


def test_real_csrf_dependency_protects_confirmation(readiness, client, monkeypatch, sample):
    from app import main
    payload = readiness()
    app.dependency_overrides.pop(require_user)
    monkeypatch.setattr(main, 'current_user', lambda request, db: sample['strategy'])
    assert confirm(client, payload).status_code == 403


def test_bad_json_and_conflicting_period_do_not_create_evidence(readiness, client, db):
    payload = readiness()
    assert client.post(URL, content='broken', headers={'content-type': 'application/json'}).status_code == 422
    assert client.post(URL, json=[]).status_code == 422
    assert confirm(client, payload, period_id=2).status_code == 422
    assert db.scalar(select(ReleaseConfirmation)) is None


def test_form_error_keeps_entered_evidence_and_does_not_write(readiness, client, db):
    payload = readiness()
    response = client.post('/release/confirmations?period_id=1', data=dict(item_id='D1',
        decision='confirmed', reason='', evidence='Korunacak tutanak',
        context_sha256=payload['release']['context_sha256']))
    assert response.status_code == 422
    assert 'Korunacak tutanak' in response.text and 'Gerekçe alanı eksik' in response.text
    assert db.scalar(select(ReleaseConfirmation)) is None


@pytest.mark.parametrize('width', [1280, 390])
def test_operations_browser_layout_and_manual_form(readiness, client, db, sample, tmp_path, width):
    from playwright.sync_api import sync_playwright
    prepare(db, sample)
    readiness()
    errors = []
    with sync_playwright() as p:
        options = dict(headless=True, args=['--no-sandbox'])
        if os.getenv('CIVENSA_CHROMIUM_PATH'): options['executable_path'] = os.environ['CIVENSA_CHROMIUM_PATH']
        browser = p.chromium.launch(**options)
        page = browser.new_page(viewport=dict(width=width, height=900))
        def serve(route):
            request = route.request
            response = client.request(request.method, request.url.replace('http://civensa.test', ''),
                content=request.post_data, headers={'content-type': request.headers.get('content-type', '')})
            route.fulfill(status=response.status_code, body=response.content,
                headers={'content-type': response.headers.get('content-type', 'text/html')})
        page.route('http://civensa.test/**', serve)
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://civensa.test/operations?period_id=1')
        assert page.locator('#technical-readiness h2').inner_text() == 'Teknik hazırlık · Geçti'
        assert page.locator('#pp-release-checklist h2').inner_text().endswith('Elle onay bekliyor')
        assert page.locator('[data-check-id="PP-19"]').inner_text().find('Doğrulanmadı') >= 0
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), page.evaluate("[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth).slice(0,20).map(e=>[e.tagName,e.className,e.getBoundingClientRect().right])")
        form = page.locator('.pp-release-form')
        form.locator('[name="reason"]').fill('Tarayıcı kabul denemesi')
        form.locator('[name="evidence"]').fill('Tutanak 1 / Ayşe Yılmaz')
        form.locator('button').click()
        page.wait_for_load_state()
        assert 'Tarayıcı kabul denemesi' in page.locator('[data-check-id="D1"]').inner_text()
        assert 'Geçti' in page.locator('[data-check-id="D1"]').inner_text()
        for selector in ['#technical-readiness', '#pp-release-checklist', '.pp-release-form']:
            assert page.locator(selector).evaluate('(e) => e.scrollWidth <= e.clientWidth')
        page.screenshot(path=str(tmp_path / f'operations-{width}.png'), full_page=True)
        assert not errors
        browser.close()
