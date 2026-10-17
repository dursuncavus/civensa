"""AR-10 acceptance: PostgreSQL and HTTP with actual login/CSRF."""
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.main import app
from app import assurance_service as service
from app.assurance_models import AssuranceStatement
from app.models import ARContentEvent, ARDocumentFreeze
from test_activity_sections import section_client, login, save, ready_and_freeze
from test_assurance_helpers import variables, put, complete_assurances

pytestmark = pytest.mark.postgres


def ekler(client, doc):
    return next(s for s in client.get(f'/api/activity-sections/reports/{doc.id}').json()['sections'] if s['code'] == 'EKLER')


def test_exact_legal_asset_and_all_paragraph_hashes():
    raw = service.ASSET_PATH.read_bytes()
    assert len(raw) == 7507
    assert hashlib.sha256(raw).hexdigest() == '116c9b8c4b3aca362bdd13b4b81cf6155f4903c5d7d592a0a0edc3afc0692c50'
    expected = {'EK-1': '7a094a003f204b17aff08a34a086341b1c76d1b5a69d68346193946f40cbd444',
                'EK-2': '6f0d2973b754518b23d55c7b51c0b2cddc7d4c96f7a000b58cba29a99dd3aeb1',
                'EK-3': 'bbfb818b7036ee63f29b1704fb384d2d78df6f1ce3a03389c30fe914b65d00c4'}
    for statement in json.loads(raw)['statements']:
        assert hashlib.sha256('\n\n'.join(statement['paragraphs']).encode()).hexdigest() == expected[statement['code']]


@pytest.mark.parametrize('email,scope,code,status', [
    ('test@example.invalid', 'own', 'EK-2', 200),
    ('test@example.invalid', 'other', 'EK-2', 403),
    ('strategy@example.invalid', 'own', 'EK-2', 403),
    ('strategy@example.invalid', 'idare', 'EK-1', 200),
    ('strategy@example.invalid', 'idare', 'EK-3', 403),
    ('test@example.invalid', 'idare', 'EK-1', 403),
    ('test@example.invalid', 'idare', 'EK-3', 403),
    ('finance@example.invalid', 'idare', 'EK-3', 200),
    ('finance@example.invalid', 'idare', 'EK-1', 403),
    ('finance@example.invalid', 'own', 'EK-2', 403),
    ('test@example.invalid', 'own', 'EK-1', 422),
    ('strategy@example.invalid', 'idare', 'EK-2', 422),
])
def test_permissions(section_client, sample, email, scope, code, status):
    client, docs, other, _ = section_client
    doc = docs[{'own': f"birim:{sample['department'].id}", 'other': f'birim:{other.id}', 'idare': 'idare'}[scope]]
    token = login(client, email)
    response = client.post(f'/api/activity-sections/reports/{doc.id}/assurances/{code}',
        headers={'X-CSRF-Token': token}, json={'expected_revision': 0, 'variables': variables()})
    assert response.status_code == status, response.text


def test_placement_completeness_and_strategy_read(section_client, db, sample):
    client, docs, _, _ = section_client
    idare, unit = docs['idare'], docs[f"birim:{sample['department'].id}"]
    assert [x['code'] for x in ekler(client, idare)['assurances']] == ['EK-1', 'EK-3']
    assert [x['code'] for x in ekler(client, unit)['assurances']] == ['EK-2']
    assert ekler(client, idare)['status'] == 'empty'
    complete_assurances(client, unit)
    assert ekler(client, unit)['status'] == 'ready'
    complete_assurances(client, idare)
    assert ekler(client, idare)['missing'] == []
    rows = db.scalars(select(AssuranceStatement)).all()
    assert len(rows) == 3
    assert all(r.version_id == service.VERSION_ID and r.file_sha256 == service.FILE_SHA256 for r in rows)
    for doc, code in [(unit, 'EK-2'), (idare, 'EK-1'), (idare, 'EK-3')]:
        page = client.get(f'/activity-sections/reports/{doc.id}/assurances/{code}')
        assert page.status_code == 200 and 'Ayşe Yılmaz' in page.text
    page = client.get(f'/activity-sections/reports/{idare.id}/assurances/EK-3')
    assert 'name="place"' not in page.text  # Strategy reads EK-3, cannot edit.


@pytest.mark.parametrize('code,email', [('EK-1', 'strategy@example.invalid'), ('EK-2', 'test@example.invalid'), ('EK-3', 'finance@example.invalid')])
def test_predecessor_exact_phrase_periods_and_audit(section_client, db, sample, code, email):
    client, docs, _, _ = section_client
    doc = docs[f"birim:{sample['department'].id}"] if code == 'EK-2' else docs['idare']
    token = login(client, email)
    assert put(client, token, doc, code, variables(two=True)).status_code == 200
    item = next(x for x in ekler(client, doc)['assurances'] if x['code'] == code)
    rendered = service.view(item)
    legal = next(x for x in service.asset()['statements'] if x['code'] == code)
    assert rendered['signature'] == '' and rendered['name'] == 'Mehmet Kaya'
    actions = db.scalars(select(ARContentEvent.action).where(ARContentEvent.document_id == doc.id)).all()
    assert 'assurance_signatories' in actions
    if code != 'EK-3':
        expected = legal['paragraphs'][3][:-1] + ' ve ' + legal['predecessor_phrase'] + ' ile desteklenmektedir.'
        assert rendered['paragraphs'][3] == expected
        assert rendered['paragraphs'][:3] == legal['paragraphs'][:3]
        assert rendered['paragraphs'][4:] == legal['paragraphs'][4:]
        assert 'assurance_predecessor' in actions
    else:
        assert rendered['paragraphs'] == legal['paragraphs']
        assert 'assurance_predecessor' not in actions
    assert put(client, token, doc, code).status_code == 200
    single = next(x for x in ekler(client, doc)['assurances'] if x['code'] == code)
    assert service.view(single)['paragraphs'] == legal['paragraphs']


def test_same_person_two_periods_does_not_insert_phrase(section_client):
    client, docs, _, _ = section_client
    token = login(client, 'strategy@example.invalid')
    values = variables(two=True)
    values['signatories'][1].update(person_ref='PERSON-1', name='Ayşe Yılmaz')
    assert put(client, token, docs['idare'], 'EK-1', values).status_code == 200
    assert not service.view(ekler(client, docs['idare'])['assurances'][0])['predecessor_inserted']


@pytest.mark.parametrize('field', ['body', 'paragraphs', 'title', 'footnotes', 'signature', 'predecessor_phrase', 'version_id', 'file_sha256'])
def test_locked_fields_rejected_at_api(section_client, db, field):
    client, docs, _, _ = section_client
    token = login(client, 'strategy@example.invalid')
    response = put(client, token, docs['idare'], 'EK-1', **{field: 'changed'})
    assert response.status_code == 422 and 'değiştirilemez' in response.text
    values = variables(); values[field] = 'changed'
    assert put(client, token, docs['idare'], 'EK-1', values).status_code == 422
    assert db.scalar(select(func.count()).select_from(AssuranceStatement)) == 0


def test_legacy_ekler_writes_and_csrf_and_stale_revision(section_client):
    client, docs, _, _ = section_client
    doc = docs['idare']; token = login(client, 'strategy@example.invalid')
    assert save(client, token, doc, 'EKLER', status='not_applicable', reason='Yok').status_code == 422
    response = client.post(f'/activity-sections/reports/{doc.id}/sections/EKLER', data={
        'csrf_token': token, 'expected_revision': 0, 'text': 'Tampered', 'status': 'ready'})
    assert response.status_code == 422 and 'değiştirilemez' in response.text
    url = f'/api/activity-sections/reports/{doc.id}/assurances/EK-1'
    assert client.post(url, json={'expected_revision': 0, 'variables': variables()}).status_code == 403
    assert put(client, token, doc, 'EK-1').status_code == 200
    assert client.post(url, headers={'X-CSRF-Token': token},
        json={'expected_revision': 0, 'variables': variables(two=True)}).status_code == 409


@pytest.mark.parametrize('kind', ['missing_name', 'bad_date', 'week_date', 'outside_year', 'overlap', 'identity_conflict', 'unjustified'])
def test_variable_validation_atomic(section_client, db, kind):
    client, docs, _, _ = section_client
    token = login(client, 'strategy@example.invalid'); values = variables(two=True)
    if kind == 'missing_name': values['signatories'][0]['name'] = ''
    if kind == 'bad_date': values['date'] = '2028-02-30'
    if kind == 'week_date': values['date'] = '2028-W01-1'
    if kind == 'outside_year': values['signatories'][0]['start_date'] = '2026-01-01'
    if kind == 'overlap': values['signatories'][1]['start_date'] = '2027-06-30'
    if kind == 'identity_conflict': values['signatories'][1]['person_ref'] = 'person-1'
    if kind == 'unjustified': values['reservations'] = [{'text': 'Eksik kayıt', 'justification': ' '}]
    response = put(client, token, docs['idare'], 'EK-1', values)
    assert response.status_code == 422, response.text
    assert db.scalar(select(func.count()).select_from(AssuranceStatement)) == 0
    assert not db.scalars(select(ARContentEvent).where(ARContentEvent.action.like('assurance_%'))).all()


def test_reservations_required_justification_and_empty_render(section_client, db):
    client, docs, _, _ = section_client
    doc = docs['idare']; token = login(client, 'strategy@example.invalid')
    values = variables(); values['reservations'] = [{'text': '<script>Eksik</script>', 'justification': 'Arşiv kaydı bulunamadı.'}]
    assert put(client, token, doc, 'EK-1', values).status_code == 200
    page = client.get(f'/activity-sections/reports/{doc.id}?code=EKLER')
    assert '&lt;script&gt;Eksik&lt;/script&gt;' in page.text and '<script>Eksik</script>' not in page.text
    assert 'Arşiv kaydı bulunamadı.' in page.text
    assert db.scalar(select(ARContentEvent).where(ARContentEvent.action == 'assurance_reservations'))
    assert put(client, token, doc, 'EK-1').status_code == 200
    assert service.view(ekler(client, doc)['assurances'][0])['variables']['reservations'] == []
    token = login(client, 'finance@example.invalid')
    assert put(client, token, doc, 'EK-3', values).status_code == 422
    assert put(client, token, doc, 'EK-3').status_code == 200
    page = client.get(f'/activity-sections/reports/{doc.id}/assurances/EK-3')
    assert 'name="reservation_' not in page.text and 'Çekinceler' not in page.text


def test_missing_variables_and_unrecorded_period_prevent_ready(section_client):
    client, docs, _, _ = section_client
    doc = docs['idare']; token = login(client, 'strategy@example.invalid')
    values = variables(); values['place'] = ''; values['signatories'][0]['start_date'] = '2027-02-01'
    assert put(client, token, doc, 'EK-1', values).status_code == 200
    slot = ekler(client, doc)
    assert slot['status'] == 'draft'
    assert any('Yer' in m for m in slot['missing']) and any('tamamını' in m for m in slot['missing'])
    # Complete every other section so EKLER is the sole freeze blocker.
    report = client.get(f'/api/activity-sections/reports/{doc.id}').json()
    for section in report['sections']:
        if section['code'] not in {'EKLER', 'III.B.2.i'}:
            financial_na = bool(report['financial']['missing'].get(section['code']))
            assert save(client, token, doc, section['code'],
                status='not_applicable' if financial_na else 'ready',
                reason='Bu testin örnek raporunda malî veri bulunmuyor.' if financial_na else '').status_code == 200
    revision = client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    response = client.post(f'/api/activity-sections/reports/{doc.id}/freeze',
        headers={'X-CSRF-Token': token}, json={'expected_revision': revision})
    assert response.status_code == 409
    assert response.json()['detail'] == 'İçerik onaylanmadı. Şu bölümleri tamamlayın: EKLER'


def test_freeze_contains_only_version_hash_and_variables_and_locks_edits(section_client, db):
    client, docs, _, _ = section_client
    doc = docs['idare']; token = login(client, 'strategy@example.invalid')
    ready_and_freeze(client, token, doc)
    freeze = db.scalar(select(ARDocumentFreeze).where(ARDocumentFreeze.document_id == doc.id))
    slot = next(s for s in json.loads(freeze.payload_json)['sections'] if s['code'] == 'EKLER')
    assert slot['status'] == 'ready' and not slot['missing']
    assert {x['code'] for x in slot['assurances']} == {'EK-1', 'EK-3'}
    for item in slot['assurances']:
        assert item['version_id'] == service.VERSION_ID and item['file_sha256'] == service.FILE_SHA256
        assert item['variables'] == variables()
        assert 'paragraphs' not in item and 'body' not in item
    assert put(client, token, doc, 'EK-1', variables(two=True)).status_code == 409
    page = client.get(f'/activity-sections/reports/{doc.id}?code=EKLER')
    assert 'Üst yönetici olarak;' in page.text and 'Malî hizmetler birim yöneticisi olarak,' in page.text
    assert freeze.sha256 == hashlib.sha256(freeze.payload_json.encode()).hexdigest()


@pytest.mark.parametrize('corruption', ['modified', 'missing'])
def test_integrity_blocks_freeze_and_shows_turkish_completeness(section_client, tmp_path, monkeypatch, corruption):
    client, docs, _, _ = section_client
    doc = docs['idare']; complete_assurances(client, doc)
    token = login(client, 'strategy@example.invalid')
    path = tmp_path / 'assurance_statements_2025.json'
    if corruption == 'modified': path.write_bytes(service.ASSET_PATH.read_bytes() + b' ')
    monkeypatch.setattr(service, 'ASSET_PATH', path)
    page = client.get('/activity-sections?section=EKLER')
    assert page.status_code == 200 and service.INTEGRITY_ERROR in page.text
    assert ekler(client, doc)['status'] == 'draft'
    revision = client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    assert client.post(f'/api/activity-sections/reports/{doc.id}/freeze',
        headers={'X-CSRF-Token': token}, json={'expected_revision': revision}).status_code == 409
    assert put(client, token, doc, 'EK-1').status_code == 409
    page = client.get(f'/activity-sections/reports/{doc.id}?code=EKLER')
    assert 'Üst yönetici olarak;' not in page.text


def test_startup_integrity_failure_remains_latched_until_restart(tmp_path, monkeypatch):
    path = tmp_path / 'asset.json'; raw = service.ASSET_PATH.read_bytes()
    path.write_bytes(b'broken')
    monkeypatch.setattr(service, 'ASSET_PATH', path)
    monkeypatch.setattr(service, '_startup_error', '')
    with TestClient(app):
        assert app.state.assurance_integrity_error == service.INTEGRITY_ERROR
        path.write_bytes(raw)
        assert service.integrity_error() == service.INTEGRITY_ERROR
    with TestClient(app):
        assert app.state.assurance_integrity_error == ''
        assert service.integrity_error() == ''


def test_html_form_saves_variables_and_preserves_invalid_input(section_client):
    client, docs, _, _ = section_client
    doc = docs['idare']; token = login(client, 'strategy@example.invalid')
    url = f'/activity-sections/reports/{doc.id}/assurances/EK-1'
    values = variables()
    form = {'csrf_token': token, 'expected_revision': '0', 'place': 'Ankara', 'date': values['date'],
            **{f'{k}_0': v for k, v in values['signatories'][0].items()},
            'reservation_text_0': 'Kayıt eksik', 'reservation_justification_0': ''}
    assert client.post(url, data={**form, 'body': 'Tamper'}).status_code == 422
    response = client.post(url, data=form)
    assert response.status_code == 422 and 'Kayıt eksik' in response.text and 'gerekçe' in response.text
    form['reservation_justification_0'] = 'Arşiv araştırması sürüyor.'
    assert client.post(url, data=form).status_code == 303
    response = client.get(url)
    assert response.status_code == 200 and 'Arşiv araştırması sürüyor.' in response.text
    assert 'name="body"' not in response.text and 'name="signature"' not in response.text


def test_frozen_view_rechecks_asset_and_keeps_frozen_metadata(section_client, db, tmp_path, monkeypatch):
    client, docs, _, _ = section_client
    doc = docs['idare']; token = login(client, 'strategy@example.invalid')
    ready_and_freeze(client, token, doc)
    freeze = db.scalar(select(ARDocumentFreeze).where(ARDocumentFreeze.document_id == doc.id))
    original = freeze.payload_json
    monkeypatch.setattr(service, 'ASSET_PATH', tmp_path / 'missing.json')
    page = client.get(f'/activity-sections/reports/{doc.id}?code=EKLER')
    assert service.INTEGRITY_ERROR in page.text and 'Üst yönetici olarak;' not in page.text
    assert ekler(client, doc)['status'] != 'ready'
    assert freeze.payload_json == original
