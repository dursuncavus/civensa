"""CIV-166: central finance warnings never block a directorate submission."""
import json
from datetime import datetime, UTC
from io import BytesIO
from zipfile import ZipFile

from pypdf import PdfReader

import pytest

from app import activity_sections_service as sections
from app import ar_unit_workflow_service as workflow
from app.activity_contract_service import digest
from app.ar_typeset_source import compatible
from app.models import ARUnitWorkflowEvent
from ar_unit_workflow_helpers import ready_unit, approve_sources, reviewer
from test_activity_sections import section_client, login, save
from test_activity_financial import expenditure, programme, post as financial_post
from test_ar_unit_workflow import own, post

pytestmark = pytest.mark.postgres
SUFFIX = (" Bu tutarlar Mali Hizmetler Müdürlüğü'ne aittir; birim raporunun gönderimini "
          "engellemez, Mali Hizmetler'e bildirin.")


def prepare(section_client, db, sample, expense=None, program=None):
    client, docs, _, _ = section_client
    doc = own(docs, sample)
    ready_unit(db, doc, sample['user'])
    token = login(client, sample['strategy'].email)
    for kind, row in [('expenditure', expense), ('programme', program)]:
        assert financial_post(client, token, docs['idare'], '/budget/' + kind,
                              rows=[] if row is None else [row]).status_code == 200
    assert save(client, token, doc, 'III.A.1', status='ready').status_code == 200
    token = login(client, sample['user'].email)
    return client, docs, doc, token


@pytest.mark.parametrize('case', ['missing', 'blank', 'mismatch', 'entered_final', 'negative'])
def test_finance_owned_items_warn_and_submit(section_client, db, sample, case):
    expense = expenditure(sample['department'].id)
    program = programme(sample)
    updates = {'blank': {'carried': None}, 'mismatch': {'actual': 9500},
               'entered_final': {'entered_final': 12500.23}, 'negative': {'deducted': 13000}}
    if case == 'missing':
        expense = program = None
    else:
        expense.update(updates[case])
    client, docs, doc, token = prepare(section_client, db, sample, expense, program)
    report = client.get(f'/api/activity-sections/reports/{doc.id}').json()
    financial = report['financial']
    warnings = financial['warnings']['III.A.1']
    assert financial['missing']['III.A.1'] == []
    assert set(financial['warnings']) == {'III.A.1', 'III.A.2', 'III.A.3', 'III.A.4'}
    assert warnings and all(line.endswith(SUFFIX) for line in warnings)
    expected = {'missing': 'gider satırları eksik', 'blank': 'Ertesi Yıla Devreden Ödenek boş',
                'mismatch': 'ekonomik kod toplamı 9.500, program toplamı 10.000, fark -500',
                'entered_final': 'hesaplanan 12.550,23, bildirilen 12.500,23, fark -50',
                'negative': 'Yıl sonu ödeneği -399,77 negatif'}[case]
    assert any(expected in line for line in warnings)
    if case == 'missing':
        assert len(warnings) == 4 and sum('gider tablosu boş' in line for line in warnings) == 2
    section = next(s for s in report['sections'] if s['code'] == 'III.A.1')
    assert section['missing'] == [] and section['warnings'] == warnings
    assert all('warnings' in s for s in report['sections'])
    response = post(client, token, doc, 'submit')
    assert response.status_code == 200, response.text
    record = db.get(ARUnitWorkflowEvent, response.json()['event_id'])
    stored, checksum = record.payload_json, record.sha256
    # Later central edits cannot alter the submitted warning count or payload.
    central_token = login(client, sample['strategy'].email)
    assert financial_post(client, central_token, docs['idare'], '/budget/expenditure', rows=[]).status_code == 200
    login(client, sample['user'].email)
    page = client.get(f'/activity-sections/reports/{doc.id}')
    assert (f'Birim faaliyet raporu gönderildi. Mali Hizmetler verisinde {len(warnings)} uyarı var; '
            'Strateji ve Mali Hizmetler bilgilendirilmelidir.') in page.text
    approver = reviewer(db, doc); db.commit()
    token = login(client, approver.email)
    assert post(client, token, doc, 'approve').status_code == 200
    assert workflow.latest(db, doc).payload_json == stored
    assert workflow.latest(db, doc).sha256 == checksum == digest(stored)


def test_deviation_explanation_stays_blocking(section_client, db, sample):
    client, docs, doc, _ = prepare(section_client, db, sample,
        expenditure(sample['department'].id, actual=100), programme(sample, actual=100))
    token = login(client, sample['strategy'].email)
    assert financial_post(client, token, docs['idare'], '/policy', lower_rate=80, upper_rate=110).status_code == 200
    token = login(client, sample['user'].email)
    report = client.get(f'/api/activity-sections/reports/{doc.id}').json()
    assert all('Sapma açıklaması gerekli' in line for line in report['financial']['missing']['III.A.1'])
    assert len(report['financial']['missing']['III.A.1']) == 2
    assert report['financial']['warnings']['III.A.1'] == []
    response = post(client, token, doc, 'submit')
    assert response.status_code == 409 and 'Bütçe Uygulama Sonuçları' in response.json()['detail']
    rows = [{'row_key': table['rows'][0]['row_key'], 'explanation': 'Test: ihale ertelendi.'}
            for table in report['financial']['tables'].values()]
    assert financial_post(client, token, doc, '/entries/explanations', rows=rows).status_code == 200
    token = login(client, sample['strategy'].email)
    assert save(client, token, doc, 'III.A.1', status='ready').status_code == 200
    token = login(client, sample['user'].email)
    assert post(client, token, doc, 'submit').status_code == 200


def test_idare_mismatch_still_blocks_freeze(section_client, db, sample):
    client, docs, _, _ = section_client
    approve_sources(db, docs['idare'])
    token = login(client, sample['strategy'].email)
    # Make all other sections applicable and ready so the failure is III.A.1 alone.
    for definition in sections.definitions(db, docs['idare']):
        if definition.code not in {sections.CORE, 'EKLER', 'III.A.1'}:
            assert save(client, token, docs['idare'], definition.code, status='not_applicable',
                        reason='Test: kapsam dışında.').status_code == 200
    from test_assurance_helpers import complete_assurances
    complete_assurances(client, docs['idare'])
    for kind, row in [('expenditure', expenditure(sample['department'].id)),
                      ('programme', programme(sample, actual=9500))]:
        assert financial_post(client, token, docs['idare'], '/budget/' + kind, rows=[row]).status_code == 200
    assert save(client, token, docs['idare'], 'III.A.1', status='ready').status_code == 200
    report = client.get(f'/api/activity-sections/reports/{docs["idare"].id}').json()
    assert not any(report['financial']['warnings'].values())
    assert any('fark 500' in line for line in report['financial']['missing']['III.A.1'])
    assert all(not line.endswith(SUFFIX) for line in report['financial']['missing']['III.A.1'])
    response = client.post(f'/api/activity-sections/reports/{docs["idare"].id}/freeze',
        json={'expected_revision': report['revision']}, headers={'X-CSRF-Token': token})
    assert response.status_code == 409 and response.json()['errors'][0]['field'] == 'sections'
    assert 'Bütçe Uygulama Sonuçları' in response.json()['detail']


def test_old_payload_without_warnings_verifies_renders_and_approves_unchanged(section_client, db, sample):
    client, docs, _, _ = section_client
    doc = own(docs, sample)
    ready_unit(db, doc, sample['user'])
    payload = sections.report_data(db, sample['user'], doc.id, use_freeze=False, include_typeset=True)
    payload.pop('workflow')
    payload['financial'].pop('warnings', None)
    for section in payload['sections']:
        section.pop('warnings', None)
    payload['source_editor_ids'] = []
    stored = sections.numeric_canonical(payload)
    checksum = digest(stored)
    # Create an old-format submitted event directly; never mutate an immutable event.
    record = ARUnitWorkflowEvent(document_id=doc.id, revision=doc.revision, action='submit',
        from_status='draft', to_status='submitted', actor_id=sample['user'].id,
        actor_name=sample['user'].full_name, created_at=datetime.now(UTC),
        payload_json=stored, sha256=checksum)
    db.add(record); db.commit()
    assert compatible(workflow.verified_payload(record))
    login(client, sample['user'].email)
    assert client.get(f'/activity-sections/reports/{doc.id}?code=III.A.1').status_code == 200
    assert client.get('/activity-sections?section=III.A.1').status_code == 200
    token = login(client, sample['strategy'].email)
    assert post(client, token, doc, 'approve').status_code == 200
    db.refresh(record)
    approval = workflow.latest(db, doc)
    assert record.payload_json == approval.payload_json == stored
    assert record.sha256 == approval.sha256 == checksum
    assert 'warnings' not in json.loads(approval.payload_json)['financial']


def test_warning_text_is_absent_from_word_and_pdf_output(section_client, db, sample):
    client, _, doc, _ = prepare(section_client, db, sample,
        expenditure(sample['department'].id, entered_final=12500.23), programme(sample))
    base = f'/activity-sections/reports/{doc.id}'
    word = client.get(base + '/export.docx')
    pdf = client.get(base + '/export.pdf')
    assert word.status_code == pdf.status_code == 200
    with ZipFile(BytesIO(word.content)) as archive:
        word_text = archive.read('word/document.xml').decode()
    pdf_text = '\n'.join(page.extract_text() for page in PdfReader(BytesIO(pdf.content)).pages)
    for output in (word_text, pdf_text):
        assert 'gönderimini engellemez' not in output
        assert 'Uyarılar (gönderimi engellemez)' not in output
