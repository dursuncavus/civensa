import io
import json

from PIL import Image
import pytest
from sqlalchemy import func, select

from app.main import app, require_user
from app.models import ActivityEvidenceFile, ActualRevision, ReportSection
from test_activity_evidence import PDF, setup, upload, form_sources
from test_activity_contract import actual_payload
from test_pp_errors_forms import form

pytestmark = pytest.mark.postgres


def test_evidence_size_boundary_api_and_form_recovery(client, db, sample):
    _, slot = setup(client, db, sample)
    limit = 10 * 1024 * 1024
    message = 'Dosya çok büyük. En fazla 10 MB yüklenebilir.'
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
    assert client.get(response.json()['evidence'][0]['files'][-1]['download_url']).content == PDF


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
    assert 'Dosya çok büyük. En fazla 5 MB yüklenebilir.' in response.text
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
    assert saved.kind == 'image' and json.loads(saved.content_json)['caption'] == data['content']
