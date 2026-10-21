"""AR-11 acceptance on PostgreSQL through real login, CSRF and shared services."""
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import activity_sections_service as sections, ar_unit_workflow_service as workflow
from app.activity_contract_service import digest
from app.models import (ARContentEvent, ARDocumentFreeze, ARSectionContent, ARSectionDefinition,
                        ARUnitWorkflowEvent, User)
from test_activity_sections import section_client, login, save, resource
from ar_unit_workflow_helpers import ready_unit, approve_sources

pytestmark = pytest.mark.postgres


def post(client, token, doc, action, reason='', revision=None):
    if revision is None:
        revision = client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    return client.post(f'/api/activity-sections/reports/{doc.id}/workflow/{action}',
        json={'expected_revision': revision, 'reason': reason}, headers={'X-CSRF-Token': token})


def own(docs, sample):
    return docs['birim:'+str(sample['department'].id)]


def test_submit_return_resubmit_independent_approve_and_complete_audit(section_client, db, sample):
    client, docs, _, _ = section_client; doc = own(docs, sample)
    ready_unit(db, doc, sample['user'])
    token = login(client, sample['user'].email)
    assert post(client, token, doc, 'submit').json()['label'] == 'Gönderildi'
    assert save(client, token, doc).status_code == 409
    assert resource(client, token, doc, 'hardware', []).status_code == 409
    token = login(client, sample['strategy'].email)
    assert post(client, token, doc, 'return', '  ').status_code == 422
    response = post(client, token, doc, 'return', 'Kaynak açıklamasını tamamlayın.')
    assert response.status_code == 200 and response.json()['label'] == 'İade edildi'
    token = login(client, sample['user'].email)
    assert save(client, token, doc, 'I.A', status='ready').status_code == 200
    assert post(client, token, doc, 'submit').status_code == 200
    token = login(client, sample['strategy'].email)
    response = post(client, token, doc, 'approve')
    assert response.status_code == 200 and response.json()['label'] == 'Onaylandı'
    records = db.scalars(select(ARUnitWorkflowEvent).where(ARUnitWorkflowEvent.document_id == doc.id)
                         .order_by(ARUnitWorkflowEvent.id)).all()
    assert [r.action for r in records] == ['submit', 'return', 'submit', 'approve']
    assert [r.actor_id for r in records] == [sample['user'].id, sample['strategy'].id]*2
    assert all(r.actor_name and r.created_at and r.created_at.tzinfo and r.revision > 0 for r in records)
    assert records[1].reason == 'Kaynak açıklamasını tamamlayın.'
    assert records[2].payload_json == records[3].payload_json
    assert records[3].sha256 == digest(records[3].payload_json)
    report = client.get(f'/api/activity-sections/reports/{doc.id}').json()
    assert report['frozen'] and report['sha256'] == records[3].sha256
    assert all(e['created_at'].endswith(' TSİ') for e in report['workflow']['events'])
    assert post(client, token, doc, 'approve').status_code == 409
    for operation in ('update', 'delete'):
        event = db.get(ARUnitWorkflowEvent, records[-1].id)
        if operation == 'update': event.reason = 'Değiştirme'
        else: db.delete(event)
        with pytest.raises(ValueError, match='değiştirilemez'): db.flush()
        db.rollback()


def test_incomplete_submit_names_sections_including_core_and_no_audit(section_client, db, sample):
    client, docs, _, _ = section_client; doc = own(docs, sample)
    token = login(client, sample['user'].email)
    response = post(client, token, doc, 'submit')
    assert response.status_code == 409
    assert 'Misyon ve Vizyon' in response.json()['detail']
    assert 'Alt program hedef ve göstergeleri' in response.json()['detail']
    assert 'EKLER' in response.json()['detail']
    assert response.json()['errors'][0]['field'] == 'sections'
    assert db.scalar(select(func.count()).select_from(ARUnitWorkflowEvent)) == 0


def test_self_approval_refused_and_cycle_boundary_matches_pp(section_client, db, sample):
    client, docs, _, _ = section_client; doc = own(docs, sample)
    ready_unit(db, doc, sample['user'])
    token = login(client, sample['strategy'].email)
    assert save(client, token, doc, 'I.A', status='ready').status_code == 200
    token = login(client, sample['user'].email)
    assert post(client, token, doc, 'submit').status_code == 200
    token = login(client, sample['strategy'].email)
    response = post(client, token, doc, 'approve')
    assert response.status_code == 403 and 'Görevler ayrılığı' in response.json()['detail']
    # An edit by another actor does not erase an earlier editor in this cycle.
    assert post(client, token, doc, 'return', 'Bağımsız inceleme için düzeltin.').status_code == 200
    token = login(client, sample['user'].email)
    assert save(client, token, doc, 'I.B', status='ready').status_code == 200
    assert post(client, token, doc, 'submit').status_code == 200
    token = login(client, sample['strategy'].email)
    assert post(client, token, doc, 'approve').status_code == 200
    assert post(client, token, doc, 'reopen', '').status_code == 422
    assert post(client, token, doc, 'reopen', 'Yeni yıl içi bilgi').status_code == 200
    assert save(client, token, doc, 'I.A', status='ready').status_code == 200
    token = login(client, sample['user'].email)
    assert save(client, token, doc, 'I.B', status='ready').status_code == 200
    assert post(client, token, doc, 'submit').status_code == 200
    token = login(client, sample['strategy'].email)
    assert post(client, token, doc, 'approve').status_code == 403


def test_idare_uses_latest_approved_snapshot_after_reopen_edits_and_resubmit(section_client, db, sample):
    client, docs, _, _ = section_client; doc = own(docs, sample); idare = docs['idare']
    ready_unit(db, doc, sample['user'])
    token = login(client, sample['user'].email)
    assert resource(client, token, doc, 'hardware', [{'category':'PC','count':5}, {'category':'Yazıcı','count':None},
                                                  {'category':'Diğer','count':0}]).status_code == 200
    assert save(client, token, doc, 'I.C.3', status='ready').status_code == 200
    assert post(client, token, doc, 'submit').status_code == 200
    token = login(client, sample['strategy'].email)
    approval = post(client, token, doc, 'approve').json()
    before = client.get(f'/api/activity-sections/reports/{idare.id}').json()
    assert before['resources']['hardware']['totals']['count'] == {'value':5,'missing':1}
    assert before['unit_manifest'][0]['approval_id'] == approval['event_id']
    assert post(client, token, doc, 'reopen', 'Kaynak sayısını güncelleyin.').status_code == 200
    token = login(client, sample['user'].email)
    assert resource(client, token, doc, 'hardware', [{'category':'PC','count':99}]).status_code == 200
    assert save(client, token, doc, 'I.C.3', status='ready').status_code == 200
    assert post(client, token, doc, 'submit').status_code == 200
    during = client.get(f'/api/activity-sections/reports/{idare.id}').json()
    assert during['resources'] == before['resources']
    assert during['core'] == before['core']
    assert during['unit_manifest'] == before['unit_manifest']
    assert 'unit_snapshots' not in during
    token = login(client, sample['strategy'].email)
    second = post(client, token, doc, 'approve').json()
    after = client.get(f'/api/activity-sections/reports/{idare.id}').json()
    assert after['resources']['hardware']['totals']['count']['value'] == 99
    assert len(after['unit_manifest']) == 1 and after['unit_manifest'][0]['approval_id'] == second['event_id']
    first = db.get(ARUnitWorkflowEvent, approval['event_id'])
    assert first.sha256 == approval['sha256'] and digest(first.payload_json) == first.sha256


def test_missing_unit_blocks_idare_freeze_and_names_each_department(section_client, db, sample):
    client, docs, other, finance = section_client; idare = docs['idare']
    token = login(client, sample['strategy'].email)
    result = client.post(f'/api/activity-sections/reports/{idare.id}/freeze',
        json={'expected_revision':idare.revision}, headers={'X-CSRF-Token':token})
    assert result.status_code == 409
    assert result.json()['errors'][0]['field'] == 'unit_versions'
    for name in (sample['department'].name, other.name, finance.name): assert name in result.json()['detail']
    assert db.scalar(select(func.count()).select_from(ARDocumentFreeze)) == 0
    assert len(client.get(f'/api/activity-sections/reports/{idare.id}').json()['missing_units']) == 3


def test_only_one_concurrent_approve_return_wins(section_client, db, sample):
    _, docs, _, _ = section_client; doc = own(docs, sample)
    ready_unit(db, doc, sample['user'])
    workflow.transition(db, sample['user'], doc.id, 'submit', doc.revision); db.commit()
    revision, doc_id, user_id, engine = doc.revision, doc.id, sample['strategy'].id, db.get_bind()
    barrier = Barrier(2)
    def decide(action):
        with Session(engine) as session:
            user = session.get(User, user_id)
            barrier.wait(timeout=10)
            try:
                record = workflow.transition(session, user, doc_id, action, revision, 'Eşzamanlı inceleme gerekçesi')
                session.commit()
                return record.action
            except HTTPException as error:
                session.rollback()
                return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(decide, ['approve', 'return']))
    assert results.count(409) == 1 and len(set(results) & {'approve', 'return'}) == 1
    assert db.scalar(select(func.count()).select_from(ARUnitWorkflowEvent)) == 2


@pytest.mark.parametrize('action', ['submit','return','approve','reopen'])
def test_cross_department_and_unprivileged_roles_cannot_transition(section_client, db, sample, action):
    client, docs, other, _ = section_client; doc = own(docs, sample)
    token = login(client, 'park@example.invalid')
    assert post(client, token, doc, action, 'Yetkisiz deneme', revision=doc.revision).status_code == 403
    assert post(client, token, docs['idare'], action, 'Yanlış rapor').status_code == 422
    assert db.scalar(select(func.count()).select_from(ARUnitWorkflowEvent)) == 0


def test_invalid_revision_csrf_and_html_reason_retention(section_client, db, sample):
    client, docs, _, _ = section_client; doc = own(docs, sample)
    token = login(client, sample['strategy'].email)
    url = f'/api/activity-sections/reports/{doc.id}/workflow/return'
    assert client.post(url, json={'expected_revision':0, 'reason':'Gerekçe'}).status_code == 403
    response = client.post(url, headers={'X-CSRF-Token':token}, json={'expected_revision':True})
    assert response.status_code == 422 and 'tam sayı' in response.json()['detail']
    reason = '<script>Geçersiz sürümde korunan gerekçe</script>'
    response = client.post(f'/activity-sections/reports/{doc.id}/workflow/return',
        data={'csrf_token':token,'expected_revision':'bozuk','reason':reason})
    assert response.status_code == 422 and '&lt;script&gt;' in response.text
    assert '<script>Geçersiz' not in response.text


def test_core_source_editor_cannot_approve_the_submitted_unit(section_client, db, sample):
    from app.models import ActualRevision, ReportIndicator
    client, docs, _, _ = section_client; doc = own(docs, sample)
    ready_unit(db, doc, sample['user'])
    item = db.scalar(select(ReportIndicator))
    old = db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id == item.id))
    db.add(ActualRevision(report_indicator_id=item.id, revision=2, supersedes_id=old.id,
        value=2, state='verified', evidence_json=old.evidence_json, explanation='Strateji kaynak düzeltmesi',
        deviation_json=old.deviation_json, created_by=sample['strategy'].id)); db.commit()
    token = login(client, sample['user'].email)
    assert post(client, token, doc, 'submit').status_code == 200
    token = login(client, sample['strategy'].email)
    assert post(client, token, doc, 'approve').status_code == 403


def test_financial_unit_contributions_and_core_are_pinned_while_drafts_change(section_client, db, sample):
    from app import activity_financial_service as finance
    from app.models import ActualRevision, ReportIndicator
    client, docs, _, _ = section_client; doc = own(docs, sample); idare = docs['idare']
    ready_unit(db, doc, sample['user'])
    aid = {'name':'Belediyeler Birliği','aid_type':'Nakdî','amount':0,'basis':'Meclis kararı','explanation':'İlk açıklama'}
    finance.save_entries(db, sample['user'], doc.id, 'aid', [aid], doc.revision); db.commit()
    token = login(client, sample['user'].email)
    assert save(client, token, doc, 'III.A.4', status='ready').status_code == 200
    assert post(client, token, doc, 'submit').status_code == 200
    token = login(client, sample['strategy'].email)
    assert post(client, token, doc, 'approve').status_code == 200
    before = client.get(f'/api/activity-sections/reports/{idare.id}').json()
    assert before['financial']['entries']['aid_directorates'][0]['explanation'] == 'İlk açıklama'
    assert before['core']['indicators'][0]['actual'] == 0
    assert post(client, token, doc, 'reopen', 'Birim verilerini düzeltin.').status_code == 200
    finance.save_entries(db, sample['user'], doc.id, 'aid', [{**aid, 'explanation':'Taslak açıklama'}], doc.revision)
    item = db.scalar(select(ReportIndicator)); old = db.scalar(select(ActualRevision))
    db.add(ActualRevision(report_indicator_id=item.id, revision=2, supersedes_id=old.id, value=99,
        state='verified', evidence_json=old.evidence_json, explanation='Yeni kaynak', deviation_json=old.deviation_json,
        created_by=sample['user'].id)); db.commit()
    after = client.get(f'/api/activity-sections/reports/{idare.id}').json()
    assert after['financial']['entries']['aid_directorates'] == before['financial']['entries']['aid_directorates']
    assert after['core'] == before['core']


def test_submit_authority_is_required_for_own_department(section_client, db, sample):
    client, docs, _, _ = section_client; doc = own(docs, sample)
    sample['user'].can_submit = False; db.commit()
    token = login(client, sample['user'].email)
    assert post(client, token, doc, 'submit').status_code == 403
    assert db.scalar(select(func.count()).select_from(ARUnitWorkflowEvent)) == 0


def test_copy_previous_uses_the_latest_approved_unit_version(section_client, db, sample):
    from app.models import ReportingPeriod, DepartmentScope, ARDocument
    from ar_unit_workflow_helpers import approve_unit
    _, docs, _, _ = section_client; doc = own(docs, sample)
    ready_unit(db, doc, sample['user'])
    approval = approve_unit(db, doc, sample['user'])
    workflow.transition(db, sample['strategy'], doc.id, 'reopen', doc.revision, 'Yeni taslak')
    sections.save_section(db, sample['user'], doc.id, 'I.A', [{'type':'paragraph','text':'Onaysız yeni taslak'}],
        'ready', '', doc.revision); db.commit()
    period = ReportingPeriod(year=2028, status='draft'); db.add(period); db.flush()
    db.add(DepartmentScope(period_id=period.id, department_id=doc.department_id, status='required')); db.commit()
    sections.create_year(db, sample['strategy'], doc.organization_id, period.id, copy_previous=True); db.commit()
    copied = db.scalar(select(ARDocument).where(ARDocument.period_id == period.id, ARDocument.department_id == doc.department_id))
    content = db.scalar(select(ARSectionContent).join(ARSectionDefinition).where(
        ARSectionContent.document_id == copied.id, ARSectionDefinition.code == 'I.A'))
    assert content.copied_from_approval_id == approval.id
    assert content.copied_from_id is None and content.copied_needs_review and content.status == 'draft'
    assert json.loads(content.blocks_json)[0]['text'] == 'Yıllık değerlendirme'
