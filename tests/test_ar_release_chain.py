"""CIV-078 idare correction chain through authenticated HTTP and PostgreSQL."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import activity_sections_service as service, ar_unit_workflow_service as workflow
from app.models import ARContentEvent, ARDocumentFreeze, Department, DepartmentScope, ReportingPeriod, User
from ar_unit_workflow_helpers import reviewer, approve_unit
from test_activity_sections import section_client, login, ready_and_freeze, save

pytestmark = pytest.mark.postgres
REASON = 'Kaynak açıklaması ve hizmet sonuçları düzeltilecek.'
WARNING = 'Güncel sürüm gerekçeyle açıldı; düzeltmeden sonra yeni sürüm oluşturun.'


@pytest.fixture
def release(section_client, db):
    client, docs, _, _ = section_client
    token = login(client, 'strategy@example.invalid')
    doc = docs['idare']
    ready_and_freeze(client, token, doc)
    return client, docs, token, doc


def reopen(client, token, doc, reason=REASON, revision=None):
    if revision is None:
        revision = client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    return client.post(f'/api/activity-sections/reports/{doc.id}/reopen',
        headers={'X-CSRF-Token':token}, json={'expected_revision':revision,'reason':reason})


def freeze(client, token, doc):
    revision = client.get(f'/api/activity-sections/reports/{doc.id}').json()['revision']
    return client.post(f'/api/activity-sections/reports/{doc.id}/freeze',
        headers={'X-CSRF-Token':token}, json={'expected_revision':revision})


def downloads(client, doc, version=None):
    result = {}
    for kind in ('docx', 'pdf', 'json'):
        response = client.get(f'/activity-sections/reports/{doc.id}/export.{kind}',
            params={'version':version} if version is not None else {})
        assert response.status_code == 200, response.text
        result[kind] = response.content
    return result


def test_release_cycle_preserves_every_old_download_and_latest_approved_units(release, db, sample):
    client, docs, token, doc = release
    first = service.latest_release(db, doc)
    original = first.payload_json, first.sha256
    old = downloads(client, doc)
    assert old == downloads(client, doc, 1)
    assert service.digest(old['json'].decode()) == first.sha256
    assert reopen(client, token, doc, '  '+REASON+'  ').status_code == 200
    assert not service.frozen(db, doc)
    assert WARNING in client.get(f'/activity-sections/reports/{doc.id}').text
    assert WARNING in client.get('/activity-sections').text
    assert downloads(client, doc, 1) == old
    assert save(client, token, doc, status='ready', blocks=[{'type':'paragraph','text':'Düzeltilmiş sonuçlar'}]).status_code == 200
    # A later approved unit version must be consumed by the next idare release.
    unit = docs['birim:'+str(sample['department'].id)]
    director = reviewer(db, unit)
    workflow.transition(db, director, unit.id, 'reopen', unit.revision, REASON)
    db.commit()
    assert save(client, token, unit, status='ready', blocks=[{'type':'paragraph','text':'Yeni birim sürümü'}]).status_code == 200
    approval = approve_unit(db, unit, sample['user'])
    assert freeze(client, token, doc).status_code == 200
    second = service.latest_release(db, doc)
    assert second.version == 2 and second.sha256 != first.sha256
    manifest = json.loads(second.payload_json)['unit_manifest']
    assert next(m for m in manifest if m['document_id']==unit.id)['approval_id'] == approval.id
    assert downloads(client, doc) == downloads(client, doc, 2)
    # Simulate a later ZIP clock, rather than depending on a sleep boundary.
    with patch('zipfile.time.localtime', return_value=(2035, 4, 5, 6, 7, 8, 0, 1, -1)):
        assert downloads(client, doc, 1) == old
    db.refresh(first)
    assert (first.payload_json, first.sha256) == original
    for url in (f'/activity-sections/reports/{doc.id}', '/activity-sections'):
        html = client.get(url).text
        assert 'Sürüm 2 · Güncel sürüm' in html
        assert 'Önceki sürüm — Sürüm 2 ile değiştirildi' in html
        assert REASON in html and 'TSİ' in html and 'Strateji' in html
        assert WARNING not in html
    # PP-14: reopening alone does not exclude its actor from the next decision.
    assert second.created_by == sample['strategy'].id
    assert reopen(client, token, doc).status_code == 200
    assert freeze(client, token, doc).status_code == 200
    assert service.latest_release(db, doc).version == 3
    assert downloads(client, doc, 1) == old


@pytest.mark.parametrize('reason', ['', ' \n ', None, 42, 'x'*10001])
def test_reopen_requires_bounded_reason(release, db, reason):
    client, _, token, doc = release
    response = reopen(client, token, doc, reason)
    assert response.status_code == 422
    assert 'Gerekçe' in response.text or 'gerekçe' in response.text
    assert service.frozen(db, doc)
    assert not db.scalar(select(ARContentEvent.id).where(ARContentEvent.action=='reopen'))


@pytest.mark.parametrize('change', ['staff', 'inactive_department', 'foreign_organization', 'stale', 'unit', 'not_frozen'])
def test_reopen_refusals(release, db, sample, change):
    client, docs, token, doc = release
    revision = doc.revision
    if change == 'staff':sample['strategy'].position='staff'
    if change == 'inactive_department':sample['department'].is_active=False
    if change == 'foreign_organization':
        from app.models import Organization
        org=Organization(name='Başka kurum');db.add(org);db.flush()
        dep=Department(organization_id=org.id,name='Başka Strateji');db.add(dep);db.flush()
        sample['strategy'].department_id=dep.id
    if change == 'stale':revision-=1
    if change == 'unit':doc=docs['birim:'+str(sample['department'].id)];revision=doc.revision
    if change == 'not_frozen':
        assert reopen(client, token, doc).status_code == 200
        revision=doc.revision
    db.commit()
    response = reopen(client, token, doc, revision=revision)
    assert response.status_code == (403 if change in {'staff','inactive_department','foreign_organization'} else 409), response.text


def test_reopen_csrf_and_non_director_and_unknown_release(release, sample):
    client, _, token, doc = release
    assert client.post(f'/api/activity-sections/reports/{doc.id}/reopen',json={'expected_revision':doc.revision,'reason':REASON}).status_code==403
    for kind in ('docx','pdf','json'):
        assert client.get(f'/activity-sections/reports/{doc.id}/export.{kind}?version=99').status_code==404
    token=login(client,'test@example.invalid')
    assert reopen(client,token,doc).status_code==403
    assert client.get(f'/activity-sections/reports/{doc.id}/export.json?version=1').status_code==403


def test_reopened_default_downloads_render_the_editable_draft(release):
    client, _, token, doc=release
    assert reopen(client,token,doc).status_code==200
    draft=downloads(client,doc)
    payload=json.loads(draft['json'])
    assert payload['frozen'] is False and payload['reopened'] is True
    assert payload['releases'][0]['reopen']['reason']==REASON
    assert isinstance(payload['releases'][0]['created_at'],str)
    assert json.loads(downloads(client,doc,1)['json'])['revision'] < payload['revision']


def test_new_release_keeps_approval_and_completeness_gates(release, db):
    client, _, token, doc = release
    assert reopen(client, token, doc).status_code==200
    missing=Department(organization_id=doc.organization_id,name='Yeni müdürlük');db.add(missing);db.flush()
    scope=DepartmentScope(department_id=missing.id,period_id=doc.period_id,status='required');db.add(scope);db.commit()
    response=freeze(client,token,doc)
    assert response.status_code==409 and 'Yeni müdürlük' in response.text
    scope.status='excluded';db.commit()
    assert save(client,token,doc,status='draft').status_code==200
    assert freeze(client,token,doc).status_code==409
    assert service.latest_release(db,doc).version==1


def test_previous_year_copy_uses_latest_release_even_when_reopened(release, db, sample):
    client, _, token, doc = release
    assert reopen(client,token,doc).status_code==200
    assert save(client,token,doc,status='ready',blocks=[{'type':'paragraph','text':'Son onaylı yıl sonu'}]).status_code==200
    assert freeze(client,token,doc).status_code==200
    latest=service.latest_release(db,doc)
    assert reopen(client,token,doc).status_code==200
    assert save(client,token,doc,status='draft',blocks=[{'type':'paragraph','text':'Henüz onaysız'}]).status_code==200
    period=ReportingPeriod(year=sample['period'].year+1,status='active',template_status='verified');db.add(period);db.commit()
    created=service.create_year(db,sample['strategy'],doc.organization_id,period.id,True)
    new=next(d for d in created if not d.department_id)
    _,content=service.section_pair(db,new,'I.A')
    assert content.copied_from_id==latest.id and content.copied_needs_review
    assert json.loads(content.blocks_json)[0]['text']=='Son onaylı yıl sonu'


@pytest.mark.parametrize('race', ['reopen', 'freeze_reopen'])
def test_concurrent_decisions_accept_one_revision(release, db, sample, race):
    client, _, token, doc = release
    if race=='freeze_reopen':assert reopen(client,token,doc).status_code==200
    ids=doc.id,sample['strategy'].id,doc.revision
    db.commit()
    barrier=Barrier(2)
    def decide(action):
        with Session(db.bind,expire_on_commit=False) as session:
            user=session.get(User,ids[1]);barrier.wait(timeout=10)
            try:
                if action=='reopen':service.reopen_document(session,user,ids[0],ids[2],REASON)
                else:service.freeze_document(session,user,ids[0],ids[2])
                session.commit();return 200
            except HTTPException as error:
                session.rollback();return error.status_code
    actions=['reopen','reopen'] if race=='reopen' else ['freeze','reopen']
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(decide,actions))
    assert sorted(results)==[200,409]


def test_service_cycle_with_real_postgres_content_guards(release, db, sample):
    """Exercise actual trigger guards, in addition to ORM-only HTTP fixtures."""
    import importlib.util
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import text
    client, _, token, doc = release
    schema=db.bind.get_execution_options()['schema_translate_map'][None]
    db.execute(text(f'SET LOCAL search_path TO "{schema}"'))
    root=Path(__file__).resolve().parents[1]/'migrations/versions'
    def module(pattern):
        spec=importlib.util.spec_from_file_location(pattern,next(root.glob(pattern+'*.py')))
        result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
        return result
    with Operations.context(MigrationContext.configure(db.connection())):
        module('c037').install_guards()
        module('c038').install_guards()
        module('c078').postgres_guard(True)
    db.execute(text('CREATE TRIGGER civ029_assurance_frozen BEFORE INSERT OR UPDATE OR DELETE ON ar_assurance_statements FOR EACH ROW EXECUTE FUNCTION civ037_frozen_content()'))
    first=service.latest_release(db,doc)
    before=first.payload_json,first.sha256
    user=sample['strategy']
    service.reopen_document(db,user,doc.id,doc.revision,REASON)
    service.save_section(db,user,doc.id,'I.A',[{'type':'paragraph','text':'Gerçek tetikleyiciyle düzeltme'}],'ready','',doc.revision)
    second=service.freeze_document(db,user,doc.id,doc.revision)
    assert second.version==2
    assert service.frozen(db,doc).id==second.id
    assert (first.payload_json,first.sha256)==before
    # The new freeze also locks all edited rows again in this same transaction.
    from sqlalchemy.exc import DBAPIError
    with pytest.raises(DBAPIError,match='değiştirilemez'):
        with db.begin_nested():
            db.execute(text("UPDATE ar_section_contents SET blocks_json='bad' WHERE document_id=:doc"),{'doc':doc.id})
    db.rollback()


def test_first_freeze_invalidates_a_waiting_reopen_token(section_client,db,sample):
    """A request read while draft cannot reopen a just-created first release."""
    from types import SimpleNamespace
    client,docs,_,_=section_client
    token=login(client,'strategy@example.invalid');doc=docs['idare']
    # Prepare complete content through the shared fixture, withholding only its
    # final freeze so the production decision below creates the first release.
    with patch.object(service,'freeze_document',return_value=SimpleNamespace(id=0,sha256='')):
        ready_and_freeze(client,token,doc)
    expected=doc.revision
    assert freeze(client,token,doc).status_code==200
    response=reopen(client,token,doc,revision=expected)
    assert response.status_code==409
    assert service.frozen(db,doc).version==1
