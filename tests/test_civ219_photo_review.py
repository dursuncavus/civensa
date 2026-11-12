"""Lead photo regressions; also runnable on SQLite when PostgreSQL is unavailable."""
import os
import re
from html import unescape
from io import BytesIO
from zipfile import ZipFile

import pytest
from pypdf import PdfReader
from sqlalchemy import select, text

from test_civ219_unit_tables import table_report, save_all
from test_activity_sections import section_client, login
from ar_unit_workflow_helpers import ready_unit, reviewer
from app import ar_unit_tables_service as tables, activity_sections_service as sections
from app import ar_unit_workflow_service as workflow, activity_contract_service as contracts
from app.models import ARContentEvent, ARUnitPhoto, Publication
from app.ar_export import build_activity_report_docx, TEMPLATE_PATH
from app.ar_pdf_export import build_activity_report_pdf

pytestmark = pytest.mark.postgres if os.getenv('CIVENSA_TEST_POSTGRES_URL') else []


@pytest.mark.parametrize('copy_status', ['submitted', 'approved'])
def test_remove_photo_preserves_submitted_copy(table_report, db, sample, copy_status):
    client, doc, docs, _ = table_report
    save_all(db, sample, doc)
    ready_unit(db, doc, sample['user'])
    submitted = workflow.transition(db, sample['user'], doc.id, 'submit', doc.revision)
    approver = reviewer(db, doc)
    if copy_status == 'approved':
        submitted = workflow.transition(db, approver, doc.id, 'approve', doc.revision)
    db.commit()
    original = submitted.payload_json
    old_payload = workflow.verified_payload(submitted)
    photo = old_payload['unit_tables']['photos'][0]
    token = login(client, sample['user'].email)
    url = f'/activity-sections/reports/{doc.id}/unit-tables/photos/{photo["id"]}/remove'
    def remove(revision=None, csrf=True):
        return client.post(url, data={'expected_revision': doc.revision if revision is None else revision,
                                     **({'csrf_token': token} if csrf else {})})
    # First exercise the allowed returned path; existing code has no action.
    workflow.transition(db, approver, doc.id, 'return' if copy_status == 'submitted' else 'reopen',
                        doc.revision, 'Yanlış fotoğrafı kaldırın.')
    db.commit()
    revision = doc.revision
    assert remove(csrf=False).status_code == 403
    assert remove(revision - 1).status_code == 409
    assert remove().status_code == 303
    assert doc.revision == revision + 1
    assert tables.unit_data(db, doc)['photos'] == []
    assert db.get(ARUnitPhoto, photo['id']).caption == photo['caption']
    assert db.execute(text('SELECT count(*) FROM ar_unit_photo_removals')).scalar() == 1
    assert db.scalar(select(ARContentEvent).where(ARContentEvent.action == 'unit_photo_remove')).actor_id == sample['user'].id
    assert remove().status_code == 409
    current = tables.with_export_photos(db, sections.report_data(db, sample['user'], doc.id))
    with ZipFile(BytesIO(build_activity_report_docx(current, TEMPLATE_PATH))) as archive:
        assert not any(name.startswith('word/media/') for name in archive.namelist())
    assert photo['caption'] not in ''.join(p.extract_text() for p in PdfReader(BytesIO(build_activity_report_pdf(current))).pages)
    old_export = tables.with_export_photos(db, old_payload)
    with ZipFile(BytesIO(build_activity_report_docx(old_export, TEMPLATE_PATH))) as archive:
        assert any(name.startswith('word/media/') for name in archive.namelist())
    assert photo['caption'] in ''.join(p.extract_text() for p in PdfReader(BytesIO(build_activity_report_pdf(old_export))).pages)
    assert submitted.payload_json == original
    if copy_status == 'approved':
        consolidated = sections.report_data(db, sample['strategy'], docs['idare'].id)
        assert consolidated['unit_tables']['units'][0]['photos'][0]['id'] == photo['id']
        assert tables.with_export_photos(db, consolidated)['unit_tables']['units'][0]['photos'][0]['image_base64']
    # Pre-fix snapshots lack labels; exports resolve them from that snapshot's
    # original book without adding fields to the stored manifest.
    old_payload['unit_tables']['photos'][0].pop('activity')
    assert tables.with_export_photos(db, old_payload)['unit_tables']['photos'][0]['activity'] == 'F.01 Park bakım ve onarım'
    assert 'activity' not in old_payload['unit_tables']['photos'][0]


@pytest.mark.parametrize('status', ['draft', 'submitted', 'approved', 'frozen'])
def test_photo_removal_scope_and_state(table_report, db, sample, status):
    client, doc, _, _ = table_report
    save_all(db, sample, doc)
    photo = tables.unit_data(db, doc)['photos'][0]
    url = f'/activity-sections/reports/{doc.id}/unit-tables/photos/{photo["id"]}/remove'
    for email in ('park@example.invalid', sample['strategy'].email):
        token = login(client, email)
        assert client.post(url, data={'csrf_token': token, 'expected_revision': doc.revision}).status_code == 403
    token = login(client, sample['user'].email)
    if status in {'submitted', 'approved'}:
        ready_unit(db, doc, sample['user'])
        workflow.transition(db, sample['user'], doc.id, 'submit', doc.revision)
        if status == 'approved':
            workflow.transition(db, reviewer(db, doc), doc.id, 'approve', doc.revision)
    elif status == 'frozen':
        from app.models import ARDocumentFreeze
        raw = sections.numeric_canonical(sections.report_data(db, sample['user'], doc.id))
        db.add(ARDocumentFreeze(document_id=doc.id, payload_json=raw, sha256=contracts.digest(raw),
                                created_by=sample['strategy'].id))
    db.commit()
    result = client.post(url, data={'csrf_token': token, 'expected_revision': doc.revision})
    assert result.status_code == (303 if status == 'draft' else 409)
    if status == 'draft':
        from app.models import ARUnitPhotoRemoval
        record = db.scalar(select(ARUnitPhotoRemoval))
        assert record.created_at is not None and record.created_by == sample['user'].id
        with pytest.raises(ValueError):
            record.created_by = sample['strategy'].id
            db.flush()
        db.rollback()
        with pytest.raises(ValueError):
            db.delete(record)
            db.flush()
        db.rollback()


def test_removal_migration_chain():
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    scripts = ScriptDirectory.from_config(Config('alembic.ini'))
    assert scripts.get_heads() == ['c219b1c2d3e4']
    assert scripts.get_revision('c219b1c2d3e4').down_revision == 'c219a1b2c3d4'


def test_remove_photo_checks_photo_document_and_bad_revision(table_report, db, sample):
    client, doc, docs, other = table_report
    save_all(db, sample, doc)
    photo = tables.unit_data(db, doc)['photos'][0]
    token = login(client, sample['user'].email)
    url = f'/activity-sections/reports/{doc.id}/unit-tables/photos/99999/remove'
    assert client.post(url, data={'csrf_token': token, 'expected_revision': 'bad'}).status_code == 422
    assert client.post(url, data={'csrf_token': token, 'expected_revision': doc.revision}).status_code == 404
    token = login(client, 'park@example.invalid')
    other_doc = docs[f'birim:{other.id}']
    result = client.post(f'/activity-sections/reports/{other_doc.id}/unit-tables/photos/{photo["id"]}/remove',
        data={'csrf_token': token, 'expected_revision': other_doc.revision})
    assert result.status_code == 404
    assert len(tables.unit_data(db, doc)['photos']) == 1


def test_photo_activity_label_on_screen_word_pdf(table_report, db, sample):
    client, doc, _, _ = table_report
    save_all(db, sample, doc)
    login(client, sample['user'].email)
    page = client.get(f'/activity-sections/reports/{doc.id}/unit-tables').text
    label = 'F.01 Park bakım ve onarım'
    assert label in unescape(re.search(r'<figcaption>(.*?)</figcaption>', page, re.S)[1])
    payload = tables.with_export_photos(db, sections.report_data(db, sample['user'], doc.id))
    with ZipFile(BytesIO(build_activity_report_docx(payload, TEMPLATE_PATH))) as archive:
        from xml.etree import ElementTree as ET
        root = ET.fromstring(archive.read('word/document.xml'))
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        captions = [''.join(p.itertext()) for p in root.findall('.//w:p', ns)]
        assert any('Fotoğraf 1' in p and label in p for p in captions)
    pdf = PdfReader(BytesIO(build_activity_report_pdf(payload)))
    assert any('Fotoğraf 1 · Sentetik park bakım çalışması · ' + label in p.extract_text() for p in pdf.pages)


def test_pre_fix_submitted_photo_has_activity_label_on_screen(table_report, db, sample, monkeypatch):
    client, doc, _, _ = table_report
    save_all(db, sample, doc)
    ready_unit(db, doc, sample['user'])
    current_unit_data = tables.unit_data
    def old_format(db, doc):
        data = current_unit_data(db, doc)
        for photo in data['photos']:
            photo.pop('activity')
        return data
    with monkeypatch.context() as patch:
        patch.setattr(tables, 'unit_data', old_format)
        submitted = workflow.transition(db, sample['user'], doc.id, 'submit', doc.revision)
        db.commit()
    before = submitted.payload_json
    login(client, sample['user'].email)
    page = client.get(f'/activity-sections/reports/{doc.id}/unit-tables').text
    assert 'F.01 Park bakım ve onarım' in unescape(re.search(r'<figcaption>(.*?)</figcaption>', page, re.S)[1])
    assert submitted.payload_json == before


def test_orphan_photo_visible_and_blocks_submit_until_removed(table_report, db, sample):
    client, doc, _, _ = table_report
    save_all(db, sample, doc)
    original = db.scalar(select(Publication).where(Publication.period_id == doc.period_id))
    import json
    updated = json.loads(original.snapshot_json)
    updated['departments'][0]['activities'] = []
    raw = contracts.canonical(updated)
    db.add(Publication(period_id=doc.period_id, version=2, snapshot_json=raw,
        sha256=contracts.digest(raw), created_by=sample['strategy'].id))
    db.commit()
    ready_unit(db, doc, sample['user'])
    tables.save(db, sample['user'], doc.id, '7', doc.revision, [])
    tables.save(db, sample['user'], doc.id, '8', doc.revision, [], True)
    db.commit()
    payload = sections.report_data(db, sample['user'], doc.id)
    assert len(payload['unit_tables']['photos']) == 1
    token = login(client, sample['user'].email)
    warning = 'Bu fotoğrafın faaliyeti güncel kitapta yok; kaldırın veya yeniden yükleyin.'
    page = client.get(f'/activity-sections/reports/{doc.id}/unit-tables').text
    assert warning in unescape(re.search(r'<section[^>]*id="photos".*?</section>', page, re.S)[0])
    assert 'F.01 Park bakım ve onarım' in unescape(re.search(r'<figcaption>(.*?)</figcaption>', page, re.S)[1])
    result = client.post(f'/api/activity-sections/reports/{doc.id}/workflow/submit',
        json={'expected_revision': doc.revision}, headers={'X-CSRF-Token': token})
    assert result.status_code == 409
    assert result.json()['blockers'] == tables.blockers(payload)
    assert len(result.json()['blockers']) == 1
    assert result.json()['blockers'][0]['link'].endswith('#photos')
    photo = payload['unit_tables']['photos'][0]
    assert client.post(f'/activity-sections/reports/{doc.id}/unit-tables/photos/{photo["id"]}/remove',
        data={'expected_revision': doc.revision, 'csrf_token': token}).status_code == 303
    assert client.post(f'/api/activity-sections/reports/{doc.id}/workflow/submit',
        json={'expected_revision': doc.revision}, headers={'X-CSRF-Token': token}).status_code == 200
