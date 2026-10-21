"""CIV-063 evidence regressions against disposable PostgreSQL."""
import hashlib
import io
import json
from zipfile import ZipFile
import pytest
from sqlalchemy import select, func
from openpyxl import Workbook
from app.main import app, require_user
from app.models import ActualRevision, ActivityEvidenceFile, ActivityEvidenceFreeze, Department, AuditLog
from app import activity_contract_service as contract
from test_activity_contract import publish, new_report, actual_payload, approve_as_director

pytestmark = pytest.mark.postgres
PDF = b'%PDF-1.7\nimmutable evidence\n%%EOF'


def setup(client, db, sample):
    report = new_report(client, publish(client, db, sample), sample)
    slot = report['indicators'][0]['report_indicator_id']
    app.dependency_overrides[require_user] = lambda: sample['user']
    response = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload())
    assert response.status_code == 200, response.text
    return report, slot


def upload(client, slot, revision=1, content=PDF, filename='kanıt.pdf', index=0):
    return client.post(f'/api/activity-reports/indicators/{slot}/evidence-files',
        data={'expected_revision': revision, 'source_index': index}, files={'file': (filename, content)})


def form_sources(sources, revision, **kwargs):
    return {'expected_revision': str(revision), 'evidence_rows': '1', 'value': '2,75', 'state': 'verified',
        'explanation': 'Deneme açıklaması', 'corrective_action': 'İzle',
        'source_title': [s['title'] for s in sources], 'source_locator': [s['locator'] for s in sources],
        'source_revision': [s['source_revision'] for s in sources], 'source_id': [s.get('source_id', '') for s in sources], **kwargs}


def test_upload_hash_versions_download_audit_and_strategy_read(client, db, sample):
    report, slot = setup(client, db, sample)
    first = upload(client, slot)
    assert first.status_code == 200, first.text
    actual = first.json()
    file1 = actual['evidence'][0]['files'][0]
    assert actual['revision'] == 2 and file1['version'] == 1
    assert file1['sha256'] == hashlib.sha256(PDF).hexdigest()
    row = db.scalar(select(ActivityEvidenceFile))
    assert row.actual_revision_id == actual['id'] and row.report_indicator_id == slot and row.file_data == PDF
    new_bytes = PDF + b'\nversion two'
    second = upload(client, slot, revision=2, content=new_bytes)
    assert second.status_code == 200, second.text
    files = second.json()['evidence'][0]['files']
    assert [f['version'] for f in files] == [1, 2] and files[0] == file1
    for user in (sample['user'], sample['strategy']):
        app.dependency_overrides[require_user] = lambda: user
        for meta, expected in zip(files, (PDF, new_bytes)):
            response = client.get(meta['download_url'])
            assert response.status_code == 200 and response.content == expected
            assert response.headers['x-evidence-sha256'] == hashlib.sha256(expected).hexdigest()
            assert response.headers['x-content-type-options'] == 'nosniff'
    assert upload(client, slot, revision=3).status_code == 403
    actions = db.scalars(select(AuditLog.action)).all()
    assert actions.count('activity_evidence_upload') == 2 and actions.count('activity_evidence_download') == 4
    page = client.get(f"/activity-reports/revisions/{report['revision_id']}")
    assert file1['download_url'] in page.text and file1['sha256'] in page.text


@pytest.mark.parametrize('action', ['update_bytes', 'update_hash', 'delete'])
def test_file_orm_immutability(client, db, sample, action):
    _, slot = setup(client, db, sample)
    assert upload(client, slot).status_code == 200
    row = db.scalar(select(ActivityEvidenceFile))
    if action == 'delete': db.delete(row)
    elif action == 'update_hash': row.sha256 = '0' * 64
    else: row.file_data = b'changed'
    with pytest.raises(ValueError, match='değiştirilemez'): db.commit()
    db.rollback()
    assert row.file_data == PDF and row.sha256 == hashlib.sha256(PDF).hexdigest()


def test_cross_directorate_upload_and_download_refused(client, db, sample):
    _, slot = setup(client, db, sample)
    url = upload(client, slot).json()['evidence'][0]['files'][0]['download_url']
    other = Department(organization_id=sample['department'].organization_id, name='Başka müdürlük')
    db.add(other); db.flush(); sample['user'].department_id = other.id; db.commit()
    for response in (upload(client, slot, revision=2), client.get(url)):
        assert response.status_code == 403 and 'Kendi müdürlüğünüzün' in response.text
    assert db.scalar(select(func.count()).select_from(ActivityEvidenceFile)) == 1


def test_approved_snapshot_manifest_and_refused_upload_keeps_downloads(client, db, sample):
    report, slot = setup(client, db, sample)
    actual = upload(client, slot).json()
    assert approve_as_director(client, sample, f"/api/activity-reports/revisions/{report['revision_id']}/approve").status_code == 200
    frozen = db.scalar(select(ActivityEvidenceFreeze))
    assert frozen.sha256 == contract.digest(frozen.manifest_json)
    manifest = json.loads(frozen.manifest_json)
    assert manifest[0]['actual_revision_id'] == actual['id'] and manifest[0]['sources'] == actual['evidence']
    snapshot = client.get(f"/api/activity-reports/revisions/{report['revision_id']}").json()
    assert snapshot['evidence_manifest'] == manifest
    response = upload(client, slot, revision=2)
    assert response.status_code == 409 and 'Onaylı rapor' in response.text
    assert client.get(actual['evidence'][0]['files'][0]['download_url']).content == PDF
    frozen.manifest_json = '[]'
    with pytest.raises(ValueError, match='değiştirilemez'): db.commit()
    db.rollback()


def test_normal_form_add_edit_remove_keeps_attachments_and_history(client, db, sample):
    report, slot = setup(client, db, sample)
    first = upload(client, slot).json()
    sources = first['evidence'] + [{'title': 'İkinci kaynak', 'locator': 's.6', 'source_revision': '2027/2'}]
    sources[0]['title'] = 'Düzeltilen kaynak'
    url = f'/activity-reports/indicators/{slot}/actuals'
    response = client.post(url, data=form_sources(sources, 2), follow_redirects=False)
    assert response.status_code == 303, response.text
    latest = db.scalar(select(ActualRevision).order_by(ActualRevision.id.desc()))
    saved = json.loads(latest.evidence_json)
    assert saved[0]['title'] == sources[0]['title'] and saved[0]['files'] == first['evidence'][0]['files']
    assert saved[1]['title'] == sources[1]['title']
    page = client.get(f"/activity-reports/revisions/{report['revision_id']}")
    assert page.text.count('name="source_title"') == 3  # Two rows and add-row template.
    assert 'API üzerinden' not in page.text and 'data-add-evidence' in page.text
    response = client.post(url, data=form_sources(saved[1:], 3), follow_redirects=False)
    assert response.status_code == 303
    latest = db.scalar(select(ActualRevision).order_by(ActualRevision.id.desc()))
    assert json.loads(latest.evidence_json) == saved[1:]
    assert client.get(saved[0]['files'][0]['download_url']).content == PDF


@pytest.mark.parametrize('invalid', ['value', 'metadata', 'file', 'conflict'])
def test_error_retains_every_entered_row_and_fields(client, db, sample, invalid):
    _, slot = setup(client, db, sample)
    sources = upload(client, slot).json()['evidence']
    sources += [{'title': 'Girilen ikinci kaynak', 'locator': 'Girilen konum', 'source_revision': 'Girilen sürüm'}]
    sources[0]['title'] = 'Girilen ilk kaynak'
    data = form_sources(sources, 1 if invalid == 'conflict' else 2,
        value='hatalı sayı' if invalid == 'value' else '3,25', explanation='Girilen açıklama', corrective_action='Girilen işlem')
    if invalid == 'metadata': data['source_locator'][1] = ''
    files = [('source_file', ('', b'')), ('source_file', ('hatalı.exe', b'invalid'))] if invalid == 'file' else None
    response = client.post(f'/activity-reports/indicators/{slot}/actuals', data=data, files=files)
    assert response.status_code == (409 if invalid == 'conflict' else 422), response.text
    for value in ('Girilen ilk kaynak', 'Girilen ikinci kaynak', 'Girilen sürüm', 'Girilen açıklama', 'Girilen işlem', 'aria-invalid="true"'):
        assert value in response.text
    assert sources[0]['files'][0]['sha256'] in response.text
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == 2


@pytest.mark.parametrize('filename,content', [('empty.pdf', b''), ('huge.pdf', b'%PDF-' + b'a' * (10*1024*1024)),
    ('bad.exe', PDF), ('bad.pdf', b'not a PDF'), ('bad.xlsx', b'PKnot zip')])
def test_size_and_type_limits(client, db, sample, filename, content):
    _, slot = setup(client, db, sample)
    response = upload(client, slot, filename=filename, content=content)
    assert response.status_code == 422, response.text
    assert db.scalar(select(func.count()).select_from(ActivityEvidenceFile)) == 0
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == 1


def test_office_zip_validation_and_valid_xlsx(client, db, sample):
    _, slot = setup(client, db, sample)
    stream = io.BytesIO()
    with ZipFile(stream, 'w') as z:
        z.writestr('[Content_Types].xml', '<xml/>'); z.writestr('../escape', 'invalid')
    assert upload(client, slot, filename='unsafe.xlsx', content=stream.getvalue()).status_code == 422
    wb = Workbook(); wb.active.append(['Kanıt']); stream = io.BytesIO(); wb.save(stream); wb.close()
    response = upload(client, slot, filename='source.xlsx', content=stream.getvalue())
    assert response.status_code == 200, response.text
    assert client.get(response.json()['evidence'][0]['files'][0]['download_url']).content == stream.getvalue()


def test_atomic_multipart_form_upload_and_failed_replacement(client, db, sample):
    report, slot = setup(client, db, sample)
    sources = actual_payload()['evidence']
    response = client.post(f'/activity-reports/indicators/{slot}/actuals', data=form_sources(sources, 1),
        files={'source_file': ('first.pdf', PDF)}, follow_redirects=False)
    assert response.status_code == 303, response.text
    latest = db.scalar(select(ActualRevision).order_by(ActualRevision.id.desc()))
    sources = json.loads(latest.evidence_json)
    assert sources[0]['files'][0]['sha256'] == hashlib.sha256(PDF).hexdigest()
    response = client.post(f'/activity-reports/indicators/{slot}/actuals', data=form_sources(sources, 2, value='invalid'),
        files={'source_file': ('second.pdf', PDF)})
    assert response.status_code == 422 and 'second.pdf' in response.text
    assert db.scalar(select(func.count()).select_from(ActivityEvidenceFile)) == 1


def test_client_cannot_forge_or_transfer_attachment_manifest(client, db, sample):
    from app.models import ReportIndicator
    from app import activity_evidence_service as evidence
    from fastapi import HTTPException
    _, slot = setup(client, db, sample)
    first = upload(client, slot).json()
    sources = first['evidence']
    original_hash = sources[0]['files'][0]['sha256']
    sources[0]['files'][0]['sha256'] = '0' * 64
    response = client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(expected_revision=2, evidence=sources))
    assert response.status_code == 200
    assert response.json()['evidence'][0]['files'][0]['sha256'] == original_hash
    with pytest.raises(HTTPException) as caught:
        evidence.verify_sources(db, db.get(ReportIndicator, slot), sources)
    assert caught.value.status_code == 409
    sources[0].pop('source_id')
    assert client.post(f'/api/activity-reports/indicators/{slot}/actuals', json=actual_payload(expected_revision=3, evidence=sources)).status_code == 422


def test_concurrent_uploads_serialize_realisation_and_version(client, db, sample):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.orm import Session
    from fastapi import HTTPException
    _, slot = setup(client, db, sample)
    barrier = Barrier(2)
    original_payload = actual_payload(expected_revision=1)
    def upload_once():
        with Session(db.get_bind(), expire_on_commit=False) as session:
            barrier.wait(timeout=10)
            try:
                contract.save_actual(session, sample['user'], slot, **original_payload, uploads={0: (PDF, 'source.pdf')})
                session.commit(); return 200
            except HTTPException as error:
                session.rollback(); return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: upload_once(), range(2)))
    assert sorted(results) == [200, 409]
    assert db.scalar(select(func.count()).select_from(ActivityEvidenceFile)) == 1


@pytest.mark.parametrize('scope', ['birim', 'idare'])
def test_frozen_section_snapshot_refuses_new_evidence_files(client, db, sample, scope):
    from app.models import ARDocument, ARDocumentFreeze
    report, slot = setup(client, db, sample)
    actual = upload(client, slot).json()
    doc = ARDocument(organization_id=sample['department'].organization_id, period_id=sample['period'].id,
        department_id=sample['department'].id if scope == 'birim' else None,
        scope=f"birim:{sample['department'].id}" if scope == 'birim' else 'idare',
        definition_version=1, revision=0, created_by=sample['strategy'].id)
    db.add(doc); db.flush()
    raw = contract.canonical({'core': {'revision_id': report['revision_id'], 'indicators': [{'evidence': actual['evidence']}]}})
    db.add(ARDocumentFreeze(document_id=doc.id, payload_json=raw, sha256=contract.digest(raw), created_by=sample['strategy'].id)); db.commit()
    response = upload(client, slot, revision=2)
    assert response.status_code == 409 and 'dondurulmuş rapor' in response.text
    assert client.get(actual['evidence'][0]['files'][0]['download_url']).content == PDF
    assert db.scalar(select(func.count()).select_from(ActivityEvidenceFile)) == 1
