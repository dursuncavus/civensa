import io
import json

from PIL import Image
import pytest
from sqlalchemy import func, select

from app.main import app, require_user
from app.models import ActivityEvidenceFile, ActualRevision, ReportSection
from test_activity_evidence import PDF, setup, upload, form_sources
from test_activity_contract import actual_payload
from test_pp_errors_forms import form, Forms
from test_activity_sections import section_client

pytestmark = pytest.mark.postgres


def test_evidence_size_boundary_api_and_form_recovery(client, db, sample):
    _, slot = setup(client, db, sample)
    limit = 10 * 1024 * 1024
    message = 'Kanıt dosyası çok büyük. En fazla 10 MB yüklenebilir. Daha küçük PDF veya XLSX dosyasını yeniden seçip yükleyin.'
    oversized = PDF + b'x' * (limit + 1 - len(PDF))
    response = upload(client, slot, content=oversized)
    assert response.status_code == 422
    assert response.json()['detail']['message'] == message
    assert db.scalar(select(func.count()).select_from(ActivityEvidenceFile)) == 0
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == 1

    sources = actual_payload()['evidence']
    response = client.post(f'/activity-reports/indicators/{slot}/actuals',
        data=form_sources(sources, 1, explanation='Korunacak açıklama', value='7,25'),
        files={'source_file': ('large.pdf', oversized)})
    assert response.status_code == 422 and message in response.text
    assert 'Korunacak açıklama' in response.text and '7,25' in response.text
    assert sources[0]['title'] in response.text and sources[0]['locator'] in response.text
    assert db.scalar(select(func.count()).select_from(ActivityEvidenceFile)) == 0
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == 1

    # Exactly at the limit is accepted; the next revision retains the small upload.
    response = upload(client, slot, content=oversized[:-1])
    assert response.status_code == 200, response.text
    assert len(db.scalar(select(ActivityEvidenceFile)).file_data) == limit
    response = upload(client, slot, revision=2)
    assert response.status_code == 200, response.text
    files = response.json()['evidence'][0]['files']
    assert [file['version'] for file in files] == [1, 2]
    assert client.get(files[0]['download_url']).content == oversized[:-1]
    assert client.get(files[1]['download_url']).content == PDF
    assert db.scalar(select(func.count()).select_from(ActivityEvidenceFile)) == 2
    assert db.scalar(select(func.count()).select_from(ActualRevision)) == 3


@pytest.mark.parametrize('existing', [False, True])
def test_section_image_size_boundary_and_form_recovery(client, db, sample, existing):
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    limit = 5 * 1024 * 1024
    stream = io.BytesIO()
    Image.new('RGB', (2, 2), 'white').save(stream, format='PNG')
    # PNG permits trailing bytes; size guards must count all uploaded bytes.
    image = stream.getvalue()
    image += b'x' * (limit - len(image))
    data = {'period_id': str(sample['period'].id), 'title': 'Korunacak başlık',
            'position': '7', 'placement': 'after', 'kind': 'image', 'content': 'Korunacak açıklama'}
    if existing:
        row = ReportSection(period_id=sample['period'].id, title='Önceki bölüm',
                            kind='text', content_json='{"text":"Önceki içerik"}')
        db.add(row); db.commit()
        data['id'] = str(row.id)
    path = '/report-builder/section'
    response = client.post(path, data=data, files={'image': ('large.png', image + b'x', 'image/png')})
    retained = form(response, path, **({'id': data['id']} if existing else {}))
    assert response.status_code == 422
    assert 'Bölüm görseli çok büyük. En fazla 5 MB yüklenebilir. Daha küçük PNG/JPEG dosyasını yeniden seçip kaydedin.' in response.text
    for field in ('title', 'content', 'position'):
        assert retained['fields'][field] == data[field]
    assert retained['fields']['kind'] == ['image'] and retained['fields']['placement'] == ['after']
    assert 'image' in retained['invalid']
    if existing:
        db.refresh(row)
        assert row.title == 'Önceki bölüm' and row.content_json == '{"text":"Önceki içerik"}'
    else:
        assert db.scalar(select(func.count()).select_from(ReportSection)) == 0
    response = client.post(path, data=data, files={'image': ('image.png', image, 'image/png')}, follow_redirects=False)
    assert response.status_code == 303, response.text
    saved = db.scalar(select(ReportSection))
    saved_content = json.loads(saved.content_json)
    import base64
    assert base64.b64decode(saved_content['data'], validate=True) == image
    assert saved.kind == 'image' and saved_content['caption'] == data['content']
    assert saved.title == data['title'] and saved.position == 7
    assert saved_content['placement'] == data['placement']
    assert db.scalar(select(func.count()).select_from(ReportSection)) == 1


def test_financial_statement_limit_api_and_form_retains_values(section_client, db):
    from app.models import ARFinancialStatement, ARContentEvent
    from test_activity_sections import login
    client, docs, _, _ = section_client
    doc = docs['idare']
    token = login(client, 'finance@example.invalid')
    api = f'/api/activity-sections/reports/{doc.id}/financial/statements'
    path = api.removeprefix('/api')
    revision = client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    metadata = {'name': 'Denenen malî tablo', 'period': '2027', 'statement_date': '2027-12-31',
                'explanation': 'Korunacak malî açıklama', 'figures': [{'label': 'Nakit', 'amount': 12.5}]}
    limit = 10 * 1024**2
    content = PDF + b'x' * (limit - len(PDF))
    before = db.scalar(select(func.count()).select_from(ARContentEvent))
    statement_count = db.scalar(select(func.count()).select_from(ARFinancialStatement))
    response = client.post(api, headers={'X-CSRF-Token': token},
        data={'expected_revision': revision, 'metadata': json.dumps(metadata)}, files={'file': ('tablo.pdf', content + b'x')})
    message = 'Malî tablo dosyası çok büyük. En fazla 10 MB yüklenebilir. Daha küçük PDF veya XLSX dosyasını yeniden seçip yükleyin.'
    assert response.status_code == 422 and response.json()['detail'] == message
    data = {k: v for k, v in metadata.items() if k != 'figures'}
    data.update(expected_revision=str(revision), csrf_token=token, figure_label_0='Nakit', figure_amount_0='12,50')
    response = client.post(path, data=data, files={'file': ('tablo.pdf', content + b'x')})
    assert response.status_code == 422 and message in response.text
    recovered = [item['fields'] for item in Forms(response.text).forms if item['action'] == path]
    assert any(all(item.get(key) == value for key, value in data.items()) for item in recovered)
    assert db.scalar(select(func.count()).select_from(ARFinancialStatement)) == statement_count
    assert db.scalar(select(func.count()).select_from(ARContentEvent)) == before
    assert client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision'] == revision
    response = client.post(api, headers={'X-CSRF-Token': token},
        data={'expected_revision': revision, 'metadata': json.dumps(metadata)}, files={'file': ('tablo.pdf', content)})
    assert response.status_code == 200, response.text
    saved = db.scalar(select(ARFinancialStatement).where(ARFinancialStatement.name == metadata['name']))
    assert saved.file_data == content and saved.explanation == metadata['explanation']
    assert client.get(api + f'/{saved.id}/file').content == content


@pytest.mark.parametrize('size,expected', [(1024**2, 303), (1024**2 + 1, 422)])
def test_configured_pp_image_limit_is_used_by_route(client, db, sample, monkeypatch, size, expected):
    monkeypatch.setenv('CIVENSA_PP_IMAGE_MAX_MB', '1')
    app.dependency_overrides[require_user] = lambda: sample['strategy']
    stream = io.BytesIO()
    Image.new('RGB', (1, 1), 'white').save(stream, format='PNG')
    image = stream.getvalue()
    data = {'period_id': sample['period'].id, 'title': 'Görsel', 'kind': 'image', 'position': '1', 'placement': 'after'}
    response = client.post('/report-builder/section', data=data,
        files={'image': ('gorsel.png', image + b'x' * (size - len(image)), 'image/png')}, follow_redirects=False)
    assert response.status_code == expected, response.text
    if expected == 422:
        assert 'En fazla 1 MB' in response.text and 'PNG/JPEG dosyasını yeniden seçip' in response.text
    assert db.scalar(select(func.count()).select_from(ReportSection)) == (1 if expected == 303 else 0)


def test_failed_statement_update_keeps_summary_values_and_original_file(section_client, db):
    from app.models import ARFinancialStatement
    from test_activity_sections import login
    client, docs, _, _ = section_client
    doc = docs['idare']
    token = login(client, 'finance@example.invalid')
    api = f'/api/activity-sections/reports/{doc.id}/financial/statements'
    revision = client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    metadata = {'name': 'Bilanço', 'period': '2027', 'explanation': 'Önceki açıklama'}
    response = client.post(api, headers={'X-CSRF-Token': token},
        data={'metadata': json.dumps(metadata), 'expected_revision': revision}, files={'file': ('eski.pdf', PDF)})
    assert response.status_code == 200, response.text
    saved = db.scalar(select(ARFinancialStatement).where(ARFinancialStatement.name == metadata['name']))
    before = (saved.filename, saved.file_data, saved.sha256, saved.explanation)
    path = api.removeprefix('/api')
    data = {'csrf_token': token, 'expected_revision': str(response.json()['revision']), 'name': 'Bilanço',
            'period': 'Denenen dönem', 'statement_date': '2027-12-30', 'explanation': 'Denenen açıklama',
            'figure_label_0': 'Denenen nakit', 'figure_amount_0': '12.500,23',
            'figure_label_2': 'Diğer nakit', 'figure_amount_2': '0'}
    response = client.post(path, data=data, files={'file': ('bos.pdf', b'')})
    assert response.status_code == 422
    assert 'Malî tablo dosyası boş.' in response.text and 'dosyasını yeniden seçip yükleyin' in response.text
    recovered = [item['fields'] for item in Forms(response.text).forms if item['action'] == path]
    assert any(all(item.get(key) == value for key, value in data.items()) for item in recovered)
    db.refresh(saved)
    assert (saved.filename, saved.file_data, saved.sha256, saved.explanation) == before
    assert client.get(api + f'/{saved.id}/file').content == PDF
