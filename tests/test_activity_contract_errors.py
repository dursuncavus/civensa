"""CIV-087: legacy route errors remain Turkish, actionable and recoverable."""
from html import unescape
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import func, select

from app.main import app, require_user
from app.models import ActualRevision, ActivityReportRevision, PublicationIndicatorBinding
from app.security import hash_password
from test_activity_contract import publish, new_report, actual_payload, report_editor
from test_activity_evidence import setup, upload
from test_pp_errors_forms import Forms

pytestmark = pytest.mark.postgres


def attempted(response, action):
    forms = [item for item in Forms(response.text).forms if item['action'] == action]
    assert len(forms) == 1, response.text
    return forms[0]['fields']


@pytest.mark.parametrize('path,payload,label', [
    ('/api/activity-reports/revisions', {'publication_id': '1', 'organization_id': 1}, 'Baz program yayını'),
    ('/api/activity-reports/revisions', {'publication_id': 1, 'organization_id': True}, 'Kurum'),
    ('/api/activity-reports/indicators/1/actuals', {'expected_revision': -1, 'value': '1'}, 'Beklenen kayıt sürümü'),
    ('/api/activity-reports/indicators/1/actuals', {'expected_revision': 0, 'value': 1}, 'Gerçekleşme değeri'),
    ('/api/publications/1/indicator-bindings', {'snapshot_indicator_id': 'bad', 'reason': 'Açıklama'}, 'Yayındaki gösterge'),
    ('/api/indicators/no/identity', {'indicator_id': 'x', 'reason': 'Açıklama'}, 'Dönem göstergesi'),
    ('/api/activity-reports/revisions/no', None, 'Rapor revizyonu'),
])
def test_legacy_request_validation_names_turkish_field(client, path, payload, label):
    response = client.get(path) if payload is None else client.post(path, json=payload)
    assert response.status_code == 422, response.text
    body = response.json()
    assert label in body['message'] and body['message'] == body['detail']
    assert 'tam sayı' in body['message'] and 'yeniden gönderin' in body['message']
    assert 'Input should' not in response.text and 'Field required' not in response.text


@pytest.mark.parametrize('html', [False, True])
def test_legacy_missing_records_and_permission_have_recovery_action(client, html):
    headers = {'Accept': 'text/html'} if html else {}
    prefix = '' if html else '/api'
    response = client.get(prefix + '/activity-reports/revisions/999999', headers=headers)
    assert response.status_code == 404
    message = unescape(response.text) if html else response.json()['message']
    assert 'revizyonu bulunamadı' in message and 'kontrol edip yeniden deneyin' in message
    path = '/activity-reports/publications/999999/bindings' if html else '/api/publications/999999/indicator-bindings'
    response = client.get(path, headers=headers) if html else client.post(path, json={'snapshot_indicator_id': 1, 'reason': 'Deneme'})
    assert response.status_code == 403
    message = unescape(response.text) if html else response.json()['message']
    assert 'strateji birimi yetkisi' in message and 'kontrol edip yeniden deneyin' in message


@pytest.mark.parametrize('path', ['/activity-reports', '/api/activity-reports/revisions/1', '/modules'])
@pytest.mark.parametrize('session', ['missing', 'inactive', 'expired'])
def test_session_errors_explain_login_for_html_and_json(client, db, sample, path, session):
    app.dependency_overrides.pop(require_user)
    if session != 'missing':
        password = 'Yerel-test-parolasi-123'
        sample['user'].password_hash = hash_password(password)
        db.commit()
        response = client.post('/login', data={'email': sample['user'].email, 'password': password}, follow_redirects=False)
        assert response.status_code == 303
        if session == 'inactive':
            sample['user'].is_active = False
        else:
            sample['user'].password_hash = hash_password(password + '-yeni')
        db.commit()
    response = client.get(path, headers={'Accept': 'text/html'}, follow_redirects=False)
    expected = 'Oturumunuz doğrulanamadı veya sona erdi. Bu sayfada işlem yapmak için yeniden giriş yapın.'
    if path.startswith('/api/'):
        assert response.status_code == 401
        assert expected in response.json()['message']
    else:
        assert response.status_code == 303
        location = response.headers['location']
        assert parse_qs(urlparse(location).query)['message'] == [expected]
        assert expected in client.get(location).text
    response = client.get(path, headers={'Accept': 'application/json'}, follow_redirects=False)
    assert response.status_code == 401 and expected in response.json()['message']


@pytest.mark.parametrize('field', ['publication_id', 'organization_id', 'expected_revision'])
def test_failed_create_form_keeps_every_attempted_value(client, db, sample, field):
    pub = publish(client, db, sample)
    fields = {'publication_id': str(pub.id), 'organization_id': str(sample['department'].organization_id),
              'expected_revision': '0', 'revision_reason': '<taslak> & gerekçe'}
    fields[field] = 'bozuk sayı'
    path = '/activity-reports/revisions'
    response = client.post(path, data=fields)
    assert response.status_code == 422
    assert all(attempted(response, path)[key] == value for key, value in fields.items())
    assert '<taslak>' not in response.text and '&lt;taslak&gt;' in response.text
    assert db.scalar(select(func.count()).select_from(ActivityReportRevision)) == 0


def test_failed_binding_form_keeps_identity_reason_and_record(client, db, sample):
    pub = publish(client, db, sample)
    path = f'/activity-reports/publications/{pub.id}/bindings'
    fields = {'snapshot_indicator_id': 'geçersiz', 'indicator_id': 'denenen-kimlik', 'reason': 'Korunacak gerekçe'}
    before = db.scalar(select(func.count()).select_from(PublicationIndicatorBinding))
    response = client.post(path, data=fields)
    assert response.status_code == 422
    assert all(attempted(response, path)[key] == value for key, value in fields.items())
    assert db.scalar(select(func.count()).select_from(PublicationIndicatorBinding)) == before


@pytest.mark.parametrize('value', ['bozuk sayı', '1.25,00', 'NaN', 'Infinity'])
def test_actual_malformed_number_names_field_and_keeps_input(client, db, sample, value):
    report = new_report(client, publish(client, db, sample), sample)
    slot = report['indicators'][0]['report_indicator_id']
    response = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(value=value))
    assert response.status_code == 422
    assert 'Gerçekleşme değeri' in response.json()['message']
    assert 'girin' in response.json()['message']
    path = f'/activity-reports/indicators/{slot}/actuals'
    fields = {'expected_revision': '0', 'value': value, 'state': 'needs_review', 'explanation': 'Korunacak taslak'}
    response = client.post(path, data=fields)
    assert response.status_code == 422
    assert all(attempted(response, path)[key] == (['needs_review'] if key == 'state' else val) for key, val in fields.items())
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == 0


def test_stale_actual_and_upload_keep_attempts_and_do_not_overwrite(client, db, sample):
    _, slot = setup(client, db, sample)
    response = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload())
    assert response.status_code == 409
    assert 'başka bir kullanıcı' in response.json()['message'] and 'Son sürümü açın' in response.json()['message']
    response = upload(client, slot, revision=0)
    assert response.status_code == 409 and 'Son sürümü açın' in response.json()['message']
    path = f'/activity-reports/indicators/{slot}/actuals'
    fields = {'expected_revision': '0', 'value': '98,76', 'state': 'needs_review',
              'explanation': 'Benim taslağım', 'corrective_action': 'İzlenecek işlem'}
    response = client.post(path, data=fields)
    assert response.status_code == 409
    assert all(attempted(response, path)[key] == (['needs_review'] if key == 'state' else val) for key, val in fields.items())
    actual = db.scalar(select(ActualRevision))
    assert actual.revision == 1 and str(actual.value) != '98.76'
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == 1


def test_stale_report_revision_keeps_selected_publication_and_reason(client, db, sample):
    pub = publish(client, db, sample)
    report = new_report(client, pub, sample)
    app.dependency_overrides[require_user] = lambda: report_editor(sample)
    second = publish(client, db, sample)
    path = '/activity-reports/revisions'
    fields = {'publication_id': str(second.id), 'organization_id': str(sample['department'].organization_id),
              'report_id': str(report['report_id']), 'expected_revision': '0', 'revision_reason': 'Denenen gerekçe'}
    response = client.post(path, data=fields)
    assert response.status_code == 409 and 'Son sürümü açıp' in response.text
    assert all(attempted(response, path)[key] == value for key, value in fields.items())
    assert db.scalar(select(func.count()).select_from(ActivityReportRevision)) == 1


def test_upload_validation_and_missing_download_are_turkish(client, db, sample):
    _, slot = setup(client, db, sample)
    path = f'/api/activity-reports/indicators/{slot}/evidence-files'
    response = client.post(path, data={'expected_revision': 'bozuk', 'source_index': 0}, files={'file': ('kanit.pdf', b'%PDF-')})
    assert response.status_code == 422 and 'Beklenen kayıt sürümü' in response.json()['message']
    response = client.get(f'/api/activity-reports/indicators/{slot}/evidence/yok/1')
    assert response.status_code == 404 and 'Kanıt dosyası bulunamadı' in response.json()['message']
    assert 'dosya sürümünü seçin' in response.json()['message']


@pytest.mark.parametrize('missing_password', [False, True])
def test_failed_login_keeps_email_and_explains_next_step(client, sample, missing_password):
    email = sample['user'].email
    data = {'email': email}
    if not missing_password:
        data['password'] = 'Gizli-yanlis-parola'
    response = client.post('/login', data=data)
    assert response.status_code == (422 if missing_password else 400)
    assert f'name="email" value="{email}"' in response.text
    assert 'Giriş formundaki e-posta veya parola' in response.text and 'yeniden giriş yapın' in response.text
    assert 'Gizli-yanlis-parola' not in response.text


def test_malformed_json_and_html_path_validation_are_turkish(client):
    response = client.post('/api/activity-reports/revisions', content='{', headers={'Content-Type': 'application/json'})
    assert response.status_code == 422 and 'İstek içeriği' in response.json()['message']
    assert 'yeniden gönderin' in response.json()['message']
    response = client.get('/activity-reports/revisions/bozuk', headers={'Accept': 'text/html'})
    assert response.status_code == 422 and 'Rapor revizyonu' in response.text and 'yeniden gönderin' in response.text
    assert 'Input should' not in response.text


def test_csrf_denial_preserves_attempted_text(client, db, sample):
    app.dependency_overrides.pop(require_user)
    password = 'Yerel-test-parolasi-123'
    sample['user'].password_hash = hash_password(password)
    db.commit()
    assert client.post('/login', data={'email': sample['user'].email, 'password': password}, follow_redirects=False).status_code == 303
    path = '/activity-reports/revisions'
    fields = {'publication_id': '123', 'organization_id': '456', 'revision_reason': 'Korunacak taslak'}
    response = client.post(path, data=fields, headers={'Accept': 'text/html'})
    assert response.status_code == 403
    assert 'formun güvenlik doğrulaması' in response.text and 'yenileyip tekrar deneyin' in response.text
    assert all(attempted(response, path)[key] == value for key, value in fields.items())


def test_closed_revision_keeps_failed_actual_form_values(client, db, sample):
    from test_activity_contract import approve_as_director
    report, slot = setup(client, db, sample)
    response = approve_as_director(client, sample, f"/api/activity-reports/revisions/{report['revision_id']}/approve")
    assert response.status_code == 200, response.text
    path = f'/activity-reports/indicators/{slot}/actuals'
    fields = {'expected_revision': '1', 'value': '7,25', 'state': 'needs_review', 'explanation': 'Korunacak son taslak'}
    response = client.post(path, data=fields)
    assert response.status_code == 409 and 'Yeni rapor revizyonu oluşturun' in response.text
    assert all(attempted(response, path)[key] == value for key, value in fields.items())
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == 1


@pytest.mark.parametrize('api', [False, True])
def test_expired_temporary_password_session_reaches_auth_check_on_legacy_router(client, db, sample, api):
    app.dependency_overrides.pop(require_user)
    password = 'Gecici-yerel-test-123'
    sample['user'].password_hash = hash_password(password)
    sample['user'].must_change_password = True
    db.commit()
    assert client.post('/login', data={'email': sample['user'].email, 'password': password}, follow_redirects=False).status_code == 303
    path = '/api/activity-reports/revisions/1' if api else '/activity-reports'
    headers = {'Accept': 'application/json' if api else 'text/html'}
    response = client.get(path, headers=headers, follow_redirects=False)
    assert response.status_code == 303 and response.headers['location'] == '/change-password'
    sample['user'].password_hash = hash_password(password + '-degisti')
    db.commit()
    response = client.get(path, headers=headers, follow_redirects=False)
    if api:
        assert response.status_code == 401 and 'yeniden giriş yapın' in response.json()['message']
    else:
        assert response.status_code == 303 and response.headers['location'].startswith('/login?message=')


@pytest.mark.parametrize('state,label', [('assembling', 'Hazırlanıyor'), ('final_review', 'Nihai incelemede'), ('final_approved', 'Nihai onaylı')])
def test_legacy_workflow_conflict_translates_internal_state(client, monkeypatch, state, label):
    from fastapi import HTTPException
    from app import activity_contract_service as contract
    def managed(*args, **kwargs):
        raise HTTPException(409, f'Bu Faaliyet Raporu aday iş akışı tarafından yönetiliyor (#1 numaralı rapor adayı ({state})). Güncel rapor adayını açın.')
    monkeypatch.setattr(contract, 'report_data', managed)
    response = client.get('/api/activity-reports/revisions/1')
    assert response.status_code == 409
    assert label in response.json()['message'] and 'Güncel rapor adayını açın' in response.json()['message']
    assert state not in response.json()['message']
