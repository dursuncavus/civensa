"""Contract regression tests: pinned targets, explicit identity, immutable history."""
import hashlib
import json
from decimal import Decimal
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func, update
from app.models import (Publication, Indicator, IndicatorValue, IndicatorIdentity, ReportSection,
    Submission, ActualRevision, ActivityReportRevision, IndicatorDefinitionRevision, PublicationIndicatorBinding,
    ReportingPeriod, Department, User, Organization, ActivityReport, ActivityReportApproval)
from app.main import app, require_user
from app import activity_contract_service as service
from app.serialization import json_dumps


def publish(client, db, sample):
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    db.scalar(select(Submission)).status = 'approved'
    if not db.scalar(select(ReportSection)):
        db.add(ReportSection(period_id=sample['period'].id, title='Genel Bilgiler', kind='text', content_json='{}'))
    db.commit()
    response = client.post('/report-builder/publish', data={'period_id': sample['period'].id}, follow_redirects=False)
    assert response.status_code == 303, response.text
    return db.scalar(select(Publication).order_by(Publication.version.desc()))


def new_report(client, pub, sample, **kwargs):
    data = {'publication_id': pub.id, 'organization_id': sample['department'].organization_id, **kwargs}
    response = client.post('/api/activity-reports/revisions', json=data)
    assert response.status_code == 200, response.text
    return client.get(f"/api/activity-reports/revisions/{response.json()['revision_id']}").json()


def actual_payload(**kwargs):
    return {'expected_revision': 0, 'value': '2.750001', 'state': 'verified',
        'evidence': [{'title': 'Kayıt defteri', 'locator': 'Sayfa 3', 'source_revision': '2027-12 kayıt 4'}],
        'explanation': 'Kaynağa göre hizmet arttı.', 'deviation': {'corrective_action': 'İzle'}, **kwargs}


def test_pinned_target_and_rebase_keeps_both_reports(client, db, sample):
    first = publish(client, db, sample)
    report = new_report(client, first, sample)
    identity_id = report['indicators'][0]['indicator_id']
    slot = report['indicators'][0]['report_indicator_id']
    actual = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload()).json()
    assert actual['deviation']['delta'] == '1.000001'
    target = db.scalar(select(IndicatorValue).where(IndicatorValue.value_kind == 'target'))
    target.value = Decimal('4.25'); sample['indicator'].name = 'Yeni gösterge adı'; sample['indicator'].code = 'Yeni kod'
    db.commit()
    second = publish(client, db, sample)
    unchanged = client.get(f"/api/activity-reports/revisions/{report['revision_id']}").json()
    assert unchanged['publication_id'] == first.id and unchanged['newer_publication_available']
    assert unchanged['indicators'][0]['definition']['name'] == 'Hizmet sayısı'
    assert Decimal(unchanged['indicators'][0]['definition']['targets'][0]['value']) == Decimal('1.75')
    revised = new_report(client, second, sample, report_id=report['report_id'], expected_revision=1)
    assert revised['revision'] == 2 and revised['previous_revision_id'] == report['revision_id']
    assert revised['indicators'][0]['indicator_id'] == identity_id
    assert revised['indicators'][0]['definition_revision_id'] != report['indicators'][0]['definition_revision_id']
    assert revised['indicators'][0]['actuals'] == []
    assert revised['differences'][0]['before']['name'] == 'Hizmet sayısı'
    assert revised['differences'][0]['after']['name'] == 'Yeni gösterge adı'
    old = client.get(f"/api/activity-reports/revisions/{report['revision_id']}").json()
    assert old['indicators'][0]['actuals'][0]['evidence'][0]['locator'] == 'Sayfa 3'
    assert client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(expected_revision=1)).status_code == 409
    page = client.get(f"/activity-reports/revisions/{revised['revision_id']}")
    assert page.status_code == 200 and 'Önceki baza göre farklar' in page.text
    assert 'Yeni gösterge adı' in page.text and 'Hizmet sayısı' in page.text


def test_actual_revisions_keep_evidence_explanation_deviation(client, db, sample):
    report = new_report(client, publish(client, db, sample), sample)
    slot = report['indicators'][0]['report_indicator_id']
    first = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload()).json()
    evidence = [{'title': 'Yeni kaynak', 'locator': 'Sayfa 6', 'source_revision': 'Düzeltme 2'}]
    second = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(
        expected_revision=1, value='0', evidence=evidence, explanation='Düzeltildi')).json()
    assert second['revision'] == 2 and second['supersedes_id'] == first['id']
    history = client.get(f"/api/activity-reports/revisions/{report['revision_id']}").json()['indicators'][0]['actuals']
    assert history[0]['explanation'] != history[1]['explanation']
    assert history[0]['evidence'][0]['title'] == 'Kayıt defteri'
    assert history[1]['evidence'] == evidence and Decimal(history[1]['value']) == 0
    response = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(expected_revision=1))
    assert response.status_code == 409 and 'başka bir kullanıcı' in response.json()['detail']
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == 2


@pytest.mark.parametrize('patch', [
    {'value': 2.1}, {'value': 'NaN'}, {'value': '1.1234567'}, {'value': '100000000000000000000'},
    {'value': None}, {'state': 'missing', 'value': '0'}, {'evidence': [{'title': 'Eksik'}]},
    {'expected_revision': True},
])
def test_invalid_actual_is_rejected_without_new_revision(client, db, sample, patch):
    report = new_report(client, publish(client, db, sample), sample)
    slot = report['indicators'][0]['report_indicator_id']
    response = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(**patch))
    assert response.status_code == 422, response.text
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == 0


def test_missing_is_not_zero_and_zero_target_has_no_percentage(client, db, sample):
    db.scalar(select(IndicatorValue)).value = Decimal(0); db.commit()
    report = new_report(client, publish(client, db, sample), sample)
    slot = report['indicators'][0]['report_indicator_id']
    response = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(value=None, state='missing'))
    assert response.status_code == 200 and response.json()['value'] is None and response.json()['deviation']['delta'] is None
    response = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(expected_revision=1, value='0'))
    assert response.status_code == 200 and Decimal(response.json()['value']) == 0
    assert response.json()['deviation']['achievement_percent'] is None


def test_approval_gate_and_same_base_correction(client, db, sample):
    pub = publish(client, db, sample); report = new_report(client, pub, sample)
    slot = report['indicators'][0]['report_indicator_id']
    url = f"/api/activity-reports/revisions/{report['revision_id']}/approve"
    assert client.post(url).status_code == 409
    client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(evidence=[]))
    assert client.post(url).status_code == 409
    client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(expected_revision=1, explanation=''))
    assert client.post(url).status_code == 409
    client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(expected_revision=2))
    assert client.post(url).status_code == 200
    assert client.post(url).status_code == 409
    assert client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(expected_revision=3)).status_code == 409
    revised = new_report(client, pub, sample, report_id=report['report_id'], expected_revision=1,
                         revision_reason='Kaynak düzeltmesi')
    assert revised['revision'] == 2 and not revised['approved'] and not revised['differences']
    assert revised['indicators'][0]['actuals'] == []
    assert client.get(f"/api/activity-reports/revisions/{report['revision_id']}").json()['approved']


def test_period_copy_preserves_identity_without_copying_definition(client, db, sample):
    publish(client, db, sample)
    identity_id = sample['indicator'].persistent_indicator_id
    response = client.post('/api/periods', json={'year': 2028, 'base_period_id': sample['period'].id})
    assert response.status_code == 200, response.text
    copied = db.scalar(select(Indicator).where(Indicator.period_id == response.json()['id']))
    assert copied.id != sample['indicator'].id and copied.persistent_indicator_id == identity_id
    assert db.scalar(select(func.count()).select_from(IndicatorDefinitionRevision)) == 1


def test_similar_names_do_not_merge_identities(client, db, sample):
    row = Indicator(period_id=sample['period'].id, department_id=sample['department'].id,
                    subprogram_id=sample['subprogram'].id, name=sample['indicator'].name, unit='Adet')
    db.add(row); db.flush()
    one = service.ensure_identity(db, sample['indicator']); two = service.ensure_identity(db, row); db.commit()
    assert one != two


def test_legacy_binding_is_explicit_and_snapshot_unchanged(client, db, sample):
    from app.program_service import book_snapshot
    raw = json_dumps(book_snapshot(db, sample['period'].id))
    pub = Publication(period_id=sample['period'].id, version=1, snapshot_json=raw,
                      sha256=hashlib.sha256(raw.encode()).hexdigest(), created_by=sample['strategy'].id)
    db.add(pub); db.commit(); app.dependency_overrides[require_user] = lambda: sample['strategy']
    data = {'publication_id': pub.id, 'organization_id': sample['department'].organization_id}
    response = client.post('/api/activity-reports/revisions', json=data)
    assert response.status_code == 409 and 'açık gösterge kimliği' in response.json()['detail']
    response = client.post(f'/api/publications/{pub.id}/indicator-bindings', json={
        'snapshot_indicator_id': sample['indicator'].id, 'reason': 'Bağımsız tarihsel kayıt'})
    assert response.status_code == 200, response.text
    report = new_report(client, pub, sample)
    assert report['indicators'][0]['indicator_id']
    assert pub.snapshot_json == raw and pub.sha256 == hashlib.sha256(raw.encode()).hexdigest()
    assert client.post(f'/api/publications/{pub.id}/indicator-bindings', json={
        'snapshot_indicator_id': sample['indicator'].id, 'reason': 'Tekrar'}).status_code == 409


def test_bad_hash_and_wrong_year_rebase(client, db, sample):
    pub = publish(client, db, sample); report = new_report(client, pub, sample)
    period = ReportingPeriod(year=2028); db.add(period); db.flush()
    bad = Publication(period_id=period.id, version=1, snapshot_json='{}', sha256='0' * 64, created_by=sample['strategy'].id)
    db.add(bad); db.commit()
    response = client.post('/api/activity-reports/revisions', json={'publication_id': bad.id,
        'organization_id': sample['department'].organization_id, 'report_id': report['report_id'], 'expected_revision': 1})
    assert response.status_code == 409 and 'bütünlüğü' in response.json()['detail']
    assert db.scalar(select(func.count()).select_from(ActivityReportRevision)) == 1


def test_department_access_and_cross_organization_isolation(client, db, sample):
    report = new_report(client, publish(client, db, sample), sample)
    org = Organization(name='Diğer kurum'); db.add(org); db.flush()
    other = Department(organization_id=org.id, name='Diğer müdürlük'); db.add(other); db.flush()
    sample['user'].department_id = other.id; db.commit()
    app.dependency_overrides[require_user] = lambda: sample['user']
    assert client.get(f"/api/activity-reports/revisions/{report['revision_id']}").status_code == 403
    assert client.post(f"/api/activity-reports/indicators/{report['indicators'][0]['report_indicator_id']}/actuals", json=actual_payload()).status_code == 403
    assert client.post('/api/activity-reports/revisions', json={'publication_id': report['publication_id'], 'organization_id': org.id}).status_code == 403
    sample['user'].department_id = None
    assert 'Müdürlük atamanız' in client.get('/activity-reports').json()['detail']


@pytest.mark.parametrize('model,field', [(IndicatorDefinitionRevision, 'definition_json'),
    (PublicationIndicatorBinding, 'reason'), (ActivityReportRevision, 'diff_json'), (ActualRevision, 'explanation')])
def test_orm_cannot_overwrite_history(client, db, sample, model, field):
    report = new_report(client, publish(client, db, sample), sample)
    client.post(f"/api/activity-reports/indicators/{report['indicators'][0]['report_indicator_id']}/actuals", json=actual_payload())
    row = db.scalar(select(model)); before = getattr(row, field); setattr(row, field, 'Yeniden yaz')
    with pytest.raises(ValueError, match='değiştirilemez'):
        db.commit()
    db.rollback(); assert getattr(row, field) == before


def test_ui_errors_and_safe_text(client, db, sample):
    report = new_report(client, publish(client, db, sample), sample)
    slot = report['indicators'][0]['report_indicator_id']
    response = client.post(f'/activity-reports/indicators/{slot}/actuals', data={
        'expected_revision': 0, 'value': '1,5', 'state': 'verified', 'source_title': 'Eksik kaynak'})
    assert response.status_code == 422 and 'kaynak adı, konumu' in response.text
    response = client.post(f'/activity-reports/indicators/{slot}/actuals', data={
        'expected_revision': 0, 'value': '1,5', 'state': 'verified', 'source_title': '<script>bad</script>',
        'source_locator': 's.1', 'source_revision': 'Kayıt 1', 'explanation': '<b>metin</b>'}, follow_redirects=False)
    assert response.status_code == 303
    page = client.get(f"/activity-reports/revisions/{report['revision_id']}")
    assert page.status_code == 200 and '&lt;script&gt;bad&lt;/script&gt;' in page.text
    assert '<script>bad</script>' not in page.text and '&lt;b&gt;metin&lt;/b&gt;' in page.text
    assert client.get('/activity-reports').status_code == 200


def test_same_department_can_write_but_not_approve(client, db, sample):
    report = new_report(client, publish(client, db, sample), sample)
    app.dependency_overrides[require_user] = lambda: sample['user']
    slot = report['indicators'][0]['report_indicator_id']
    assert client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload()).status_code == 200
    assert client.post(f"/api/activity-reports/revisions/{report['revision_id']}/approve").status_code == 403
    assert len(client.get(f"/api/activity-reports/revisions/{report['revision_id']}").json()['indicators']) == 1


@pytest.mark.postgres
@pytest.mark.parametrize('operation', ['actual', 'rebase'])
def test_concurrent_contract_write_applied_once(db, sample, monkeypatch, operation):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    from sqlalchemy.orm import Session
    user = sample['strategy']
    payload, definitions = service.freeze_program_payload(db, sample['period'].id, user)
    raw = service.canonical(payload)
    pub = Publication(period_id=sample['period'].id, version=1, snapshot_json=raw, sha256=service.digest(raw), created_by=user.id)
    db.add(pub); db.flush(); service.attach_publication_definitions(db, pub, definitions, user)
    revision = service.create_report_revision(db, user, pub.id, sample['department'].organization_id)
    db.commit()
    from app.models import ReportIndicator
    slot_id = db.scalar(select(ReportIndicator.id))
    first_lock = threading.Event(); second_entered = threading.Event()
    original = service.lock_report
    count = [0]; guard = threading.Lock()
    def held_lock(session, report):
        with guard:
            count[0] += 1; first = count[0] == 1
        if not first:
            second_entered.set()
        original(session, report)
        if first:
            first_lock.set(); second_entered.wait(timeout=1)
    monkeypatch.setattr(service, 'lock_report', held_lock)
    if operation == 'rebase':
        # Different publication; same explicit identities.
        next_pub = Publication(period_id=pub.period_id, version=2, snapshot_json=raw, sha256=service.digest(raw), created_by=user.id)
        db.add(next_pub); db.flush(); service.attach_publication_definitions(db, next_pub, definitions, user); db.commit()
    def call():
        with Session(db.get_bind(), expire_on_commit=False) as session:
            try:
                if operation == 'actual':
                    service.save_actual(session, user, slot_id, **actual_payload())
                else:
                    service.create_report_revision(session, user, next_pub.id, sample['department'].organization_id,
                        report_id=revision.report_id, expected_revision=1)
                session.commit(); return 200
            except HTTPException as error:
                session.rollback(); return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(call); assert first_lock.wait(timeout=5)
        second = pool.submit(call)
        assert sorted([first.result(timeout=10), second.result(timeout=10)]) == [200, 409]
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == (1 if operation == 'actual' else 0)
    assert db.scalar(select(func.count()).select_from(ActivityReportRevision)) == (1 if operation == 'actual' else 2)


def test_period_identity_link_is_explicit_and_cannot_be_reassigned(client, db, sample):
    pub = publish(client, db, sample)
    identity_id = sample['indicator'].persistent_indicator_id
    period = ReportingPeriod(year=2029); db.add(period); db.flush()
    row = Indicator(period_id=period.id, department_id=sample['department'].id,
        subprogram_id=sample['subprogram'].id, name='Farklı ad', unit='Adet')
    db.add(row); db.commit()
    response = client.post(f'/api/indicators/{row.id}/identity', json={'indicator_id': identity_id, 'reason': 'Açık kaynak ilişkisinde aynı kavram'})
    assert response.status_code == 200 and row.persistent_indicator_id == identity_id
    from app.models import AuditLog
    assert db.scalar(select(AuditLog).where(AuditLog.action == 'period_indicator_identity')).details == 'Açık kaynak ilişkisinde aynı kavram'
    other = IndicatorIdentity(indicator_id='00000000-0000-0000-0000-000000000000', organization_id=sample['department'].organization_id)
    db.add(other); db.commit()
    assert client.post(f'/api/indicators/{row.id}/identity', json={'indicator_id': other.indicator_id, 'reason': 'Değiştir'}).status_code == 409
    row.persistent_indicator_id = other.indicator_id
    with pytest.raises(ValueError, match='kimliği değiştirilemez'):
        db.commit()
    db.rollback()


def test_rebase_rejects_valid_publication_from_another_year(client, db, sample):
    pub = publish(client, db, sample); report = new_report(client, pub, sample)
    period = ReportingPeriod(year=2029); db.add(period); db.flush()
    payload = json.loads(pub.snapshot_json); payload['period'] = 2029
    raw = service.canonical(payload)
    wrong_year = Publication(period_id=period.id, version=1, snapshot_json=raw, sha256=service.digest(raw), created_by=sample['strategy'].id)
    db.add(wrong_year); db.commit()
    response = client.post('/api/activity-reports/revisions', json={'publication_id': wrong_year.id,
        'organization_id': sample['department'].organization_id, 'report_id': report['report_id'], 'expected_revision': 1})
    assert response.status_code == 422 and 'aynı yıl' in response.json()['detail']


def test_contract_api_requires_session_and_csrf(db, sample):
    import base64
    from itsdangerous import TimestampSigner
    from fastapi.testclient import TestClient
    from app.db import get_db
    from app.config import session_secret
    def database(): yield db
    app.dependency_overrides[get_db] = database
    try:
        with TestClient(app) as session_client:
            body = {'publication_id': 999, 'organization_id': sample['department'].organization_id}
            assert session_client.post('/api/activity-reports/revisions', json=body).status_code == 401
            cookie = TimestampSigner(session_secret()).sign(base64.b64encode(json.dumps({'user_id': sample['strategy'].id, 'csrf_token': 'test-token'}).encode())).decode()
            session_client.cookies.set('session', cookie)
            assert session_client.post('/api/activity-reports/revisions', json=body).status_code == 403
            assert session_client.post('/api/activity-reports/revisions', json=body, headers={'X-CSRF-Token': 'test-token'}).status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_restore_preserves_explicit_indicator_identity(db, sample):
    from app.import_service import _serialize_department_state, _delete_department_period_data, _restore_department_state
    identity_id = service.ensure_identity(db, sample['indicator']); db.commit()
    state = _serialize_department_state(db, sample['department'].id, sample['period'].id)
    _delete_department_period_data(db, sample['department'].id, sample['period'].id)
    submission = db.scalar(select(Submission)); db.delete(submission); db.flush()
    _restore_department_state(db, state, sample['period'].id); db.commit()
    assert db.get(Indicator, state['indicators'][0]['id']).persistent_indicator_id == identity_id


def test_manual_form_cannot_drop_multiple_evidence_sources(client, db, sample):
    report = new_report(client, publish(client, db, sample), sample)
    slot = report['indicators'][0]['report_indicator_id']
    evidence = actual_payload()['evidence'] + [{'title': 'İkinci kaynak', 'locator': 's.4', 'source_revision': 'Kayıt2'}]
    assert client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(evidence=evidence)).status_code == 200
    response = client.post(f'/activity-reports/indicators/{slot}/actuals', data={'expected_revision': 1, 'value': '1,5', 'state': 'verified'})
    assert response.status_code == 422 and 'birden fazla kanıt' in response.text
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == 1
