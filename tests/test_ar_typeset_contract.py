"""CIV-086 / D-190 contract, identity retention and immutable-source acceptance."""
import copy
import json
from decimal import Decimal
from pathlib import Path

import pytest
from lxml import html
from sqlalchemy import select, update

from app import activity_sections_service as service, activity_financial_service as financial
from app.ar_typeset_contract import build_contract, canonical_bytes, sha256
from app.ar_typeset_keys import section_keys
from app.ar_typeset_source import LEGACY_MESSAGE
from app.models import (ARResourceRow, ARFinancialEntry, ARSectionContent, ARDocumentFreeze,
                        ARStatementFigureKey, Organization)
from test_activity_sections import section_client, login, resource, save, ready_and_freeze
from test_ar_release_chain import reopen, freeze
from ar_unit_workflow_helpers import ready_unit, approve_unit

pytestmark = pytest.mark.postgres


def typeset(client, doc, **params):
    return client.get(f'/activity-sections/reports/{doc.id}/typeset.json', params=params)


def check_manifest(contract):
    manifest = contract['manifest']
    before = copy.deepcopy(contract)
    del before['manifest']['contract_sha256']
    assert sha256(before) == manifest['contract_sha256']
    all_items = [contract['document']]
    for kind in ('sections', 'tables', 'rows', 'activities', 'indicators'):
        assert contract[kind] == sorted(contract[kind], key=lambda row: row['id'])
        all_items.extend(contract[kind])
    assert len({row['id'] for row in all_items}) == len(all_items)
    assert manifest['items'] == {item['id']: sha256(item) for item in all_items}
    known = set(manifest['items'])
    assert all(set(table['row_ids']) <= known for table in contract['tables'])


def post_section(client, token, doc, blocks, keys=None):
    data = dict(expected_revision=doc.revision, blocks=blocks, status='draft', reason='')
    if keys is not None:
        data['table_keys'] = keys
    return client.post(f'/api/activity-sections/reports/{doc.id}/sections/I.A',
                       headers={'X-CSRF-Token': token}, json=data)


def test_resource_rows_keep_keys_and_primary_keys_including_decimal_scale(section_client, db, sample):
    client, docs, _, _ = section_client
    doc = docs['birim:' + str(sample['department'].id)]
    token = login(client, 'strategy@example.invalid')
    rows = [{'name': 'Hizmet binası', 'category': 'Hizmet', 'address': 'Merkez', 'area': 12500.23, 'ownership': 'mülk'}]
    assert resource(client, token, doc, 'buildings', rows).status_code == 200
    record = db.scalar(select(ARResourceRow).where(ARResourceRow.document_id == doc.id))
    identity = record.id, record.stable_key
    assert resource(client, token, doc, 'buildings', rows).status_code == 200
    assert (record.id, record.stable_key) == identity
    assert list(db.scalars(select(ARResourceRow.id).where(ARResourceRow.document_id == doc.id))) == [identity[0]]
    rows[0].update(stable_key=record.stable_key, area=0)
    assert resource(client, token, doc, 'buildings', rows).status_code == 200
    db.refresh(record)
    assert (record.id, record.stable_key) == identity and record.area == 0
    # An inserted duplicate cannot steal an explicitly keyed existing row.
    assert resource(client, token, doc, 'buildings', [{k: v for k, v in rows[0].items() if k != 'stable_key'}, rows[0]]).status_code == 200
    records = list(db.scalars(select(ARResourceRow).where(ARResourceRow.document_id == doc.id).order_by(ARResourceRow.position)))
    assert len(records) == 2 and records[0].stable_key != records[1].stable_key
    assert records[1].stable_key == identity[1]
    old_keys={row.stable_key for row in records}
    assert resource(client,token,doc,'buildings',[{**rows[0],'stable_key':''}]).status_code==200
    new_row=db.scalar(select(ARResourceRow).where(ARResourceRow.document_id==doc.id))
    assert new_row.stable_key not in old_keys


def test_free_tables_and_rows_keep_distinct_keys_across_saves_and_reordering(section_client, db, sample):
    client, docs, _, _ = section_client
    doc = docs['birim:' + str(sample['department'].id)]
    token = login(client, 'strategy@example.invalid')
    blocks = [{'type': 'table', 'rows': [['Hizmet', '5'], ['Hizmet', '5']]}] * 2
    assert post_section(client, token, doc, blocks).status_code == 200
    _, content = service.section_pair(db, doc, 'I.A')
    keys = section_keys(db, content)
    assert len({k['stable_key'] for k in keys}) == 2
    assert all(len(set(k['rows'])) == 2 for k in keys)
    assert post_section(client, token, doc, blocks).status_code == 200
    assert section_keys(db, content) == keys
    changed = copy.deepcopy(blocks)
    changed[0]['rows'][0][1] = '6'
    assert post_section(client, token, doc, changed, keys).status_code == 200
    assert section_keys(db, content) == keys
    swapped = [{**keys[1], 'position': 0}, {**keys[0], 'position': 1}]
    assert post_section(client, token, doc, changed[::-1], swapped).status_code == 200
    assert section_keys(db, content) == swapped
    swapped[1]['rows'][0] = swapped[0]['rows'][0]
    assert post_section(client, token, doc, changed[::-1], swapped).status_code == 422
    remaining=[{**keys[1],'position':0}]
    assert post_section(client,token,doc,[blocks[1]],remaining).status_code==200
    assert section_keys(db,content)==remaining


def test_resource_and_financial_keys_cannot_move_between_parents(section_client, db, sample):
    client, docs, other, _ = section_client
    token = login(client, 'strategy@example.invalid')
    own = docs['birim:' + str(sample['department'].id)]
    foreign = docs['birim:' + str(other.id)]
    assert resource(client, token, foreign, 'hardware', [{'category': 'Bilgisayar', 'count': 1}]).status_code == 200
    key = db.scalar(select(ARResourceRow.stable_key).where(ARResourceRow.document_id == foreign.id))
    assert resource(client, token, own, 'hardware', [{'category': 'Bilgisayar', 'count': 1, 'stable_key': key}]).status_code == 422
    assert resource(client, token, foreign, 'hardware', [{'category': 'Bilgisayar', 'count': 1, 'stable_key': key}] * 2).status_code == 422


def test_financial_and_statement_figure_keys_survive_edits(section_client, db, sample):
    client, docs, _, _ = section_client
    doc = docs['idare']
    actor = sample['strategy']
    rows = [{'label': 'Varlık', 'amount': '12.500,23', 'previous': '0', 'explanation': 'Kaynak'}]
    financial.save_entries(db, actor, doc.id, 'assets', rows, doc.revision); db.commit()
    record = db.scalar(select(ARFinancialEntry).where(ARFinancialEntry.document_id == doc.id))
    identity = record.id, record.stable_key
    financial.save_entries(db, actor, doc.id, 'assets', rows, doc.revision); db.commit()
    assert (record.id, record.stable_key) == identity
    rows[0].update(stable_key=record.stable_key, amount='0')
    financial.save_entries(db, actor, doc.id, 'assets', rows, doc.revision); db.commit()
    assert (record.id, record.stable_key) == identity
    financial.save_entries(db,actor,doc.id,'assets',[{**rows[0],'stable_key':''}],doc.revision);db.commit()
    assert db.scalar(select(ARFinancialEntry.stable_key).where(ARFinancialEntry.document_id==doc.id))!=identity[1]
    statement = {'name': 'Bilanço', 'period': '2027', 'explanation': 'Kaynak',
                 'figures': [{'label': 'Toplam', 'amount': '12.500,23'}, {'label': 'Toplam', 'amount': '0'}]}
    financial.save_statement(db, actor, doc.id, statement, doc.revision); db.commit()
    figures = list(db.scalars(select(ARStatementFigureKey).order_by(ARStatementFigureKey.position)))
    identities = [r.stable_key for r in figures]
    assert len(set(identities)) == 2
    financial.save_statement(db, actor, doc.id, statement, doc.revision); db.commit()
    assert list(db.scalars(select(ARStatementFigureKey.stable_key).order_by(ARStatementFigureKey.position))) == identities
    statement['figures'][0].update(stable_key=identities[0], amount='0')
    statement['figures'][1]['stable_key'] = identities[1]
    financial.save_statement(db, actor, doc.id, statement, doc.revision); db.commit()
    assert list(db.scalars(select(ARStatementFigureKey.stable_key).order_by(ARStatementFigureKey.position))) == identities
    for figure in statement['figures']:figure['stable_key']=''
    financial.save_statement(db,actor,doc.id,statement,doc.revision);db.commit()
    assert set(db.scalars(select(ARStatementFigureKey.stable_key))).isdisjoint(identities)
    contract = typeset(client, doc).json()
    check_manifest(contract)
    assert next(t for t in contract['tables'] if t['kind'] == 'statement')['row_ids']


def test_html_hidden_keys_survive_resource_section_and_financial_saves(section_client, db, sample):
    client, docs, _, _ = section_client
    own = docs['birim:' + str(sample['department'].id)]
    token = login(client, 'strategy@example.invalid')
    assert resource(client, token, own, 'hardware', [{'category': 'Bilgisayar', 'count': 5}]).status_code == 200
    key = db.scalar(select(ARResourceRow.stable_key).where(ARResourceRow.document_id == own.id))
    page = html.fromstring(client.get(f'/activity-sections/reports/{own.id}?code=I.C.3').text)
    field = page.xpath('//form[contains(@action,"/resources/hardware")]//input[@name="stable_key_0"]')[0]
    assert field.get('value') == key
    response = client.post(f'/activity-sections/reports/{own.id}/resources/hardware', data={
        'csrf_token': token, 'expected_revision': own.revision, 'include_0': 'on', 'category_0': 'Bilgisayar',
        'count_0': '6', 'stable_key_0': key})
    assert response.status_code == 303
    assert db.scalar(select(ARResourceRow.stable_key).where(ARResourceRow.document_id == own.id)) == key
    blocks = [{'type': 'table', 'rows': [['Başlık', 'Tutar'], ['Hizmet', '5']]}]
    assert post_section(client, token, own, blocks).status_code == 200
    _, content = service.section_pair(db, own, 'I.A')
    keys = section_keys(db, content)
    page = html.fromstring(client.get(f'/activity-sections/reports/{own.id}?code=I.A').text)
    hidden = page.xpath('//input[@name="table_keys"]')[0].get('value')
    response = client.post(f'/activity-sections/reports/{own.id}/sections/I.A', data={
        'csrf_token': token, 'expected_revision': own.revision, 'text': '| Başlık | Tutar |\n| Yeni | 1 |\n| Hizmet | 6 |',
        'status': 'draft', 'reason': '', 'table_keys': hidden})
    assert response.status_code == 303, response.text
    updated = section_keys(db, content)
    assert updated[0]['stable_key'] == keys[0]['stable_key']
    # Equal header retains its key; new and changed rows carry distinct identities.
    assert updated[0]['rows'][0] == keys[0]['rows'][0]
    assert len(set(updated[0]['rows'])) == 3
    assert updated[0]['rows'][2] == keys[0]['rows'][1]
    doc = docs['idare']
    financial.save_entries(db, sample['strategy'], doc.id, 'assets', [
        {'label': 'Varlık', 'amount': '1', 'previous': '0', 'explanation': 'Kaynak'}], doc.revision); db.commit()
    record = db.scalar(select(ARFinancialEntry).where(ARFinancialEntry.document_id == doc.id))
    page = html.fromstring(client.get(f'/activity-sections/reports/{doc.id}?code=III.A.2').text)
    assert page.xpath('//form[contains(@action,"/entries/assets")]//input[@name="stable_key_0"]')[0].get('value') == record.stable_key


@pytest.mark.parametrize('scope', ['birim', 'idare'])
def test_old_keyless_release_refused_without_changing_any_original_download(section_client, db, sample, scope):
    from test_ar_release_chain import downloads
    client, docs, _, _ = section_client
    doc = docs['idare' if scope == 'idare' else 'birim:' + str(sample['department'].id)]
    token = login(client, 'strategy@example.invalid')
    ready_and_freeze(client, token, doc, legacy=True)
    release = service.latest_release(db, doc)
    before = release.payload_json, release.sha256
    originals = downloads(client, doc, 1)
    response = typeset(client, doc, version=1)
    assert response.status_code == 409 and response.json()['detail'] == LEGACY_MESSAGE
    assert downloads(client, doc, 1) == originals
    assert (release.payload_json, release.sha256) == before


def test_frozen_bytes_ids_manifest_and_live_independence(section_client, db, sample, monkeypatch):
    client, docs, _, _ = section_client
    doc = docs['idare']
    own = docs['birim:' + str(sample['department'].id)]
    token = login(client, 'strategy@example.invalid')
    assert resource(client, token, own, 'hardware', [{'category': 'Donmuş bilgisayar', 'count': 5}]).status_code == 200
    ready_and_freeze(client, token, doc)
    release = service.latest_release(db, doc)
    first = typeset(client, doc, version=1)
    assert first.status_code == 200, first.text
    contract = first.json()
    check_manifest(contract)
    assert contract['source_sha256'] == release.sha256
    assert contract['release_version'] == 1 and contract['generated_at'].endswith('+03:00')
    assert first.content == canonical_bytes(contract) == typeset(client, doc, version=1).content
    assert first.headers['cache-control'] == 'private, no-store'
    assert first.headers['x-content-type-options'] == 'nosniff'
    assert reopen(client, token, doc).status_code == 200
    assert freeze(client, token, doc).status_code == 200
    second = typeset(client, doc, version=2).json()
    assert contract['manifest']['items'].keys() == second['manifest']['items'].keys()
    assert contract['manifest']['items'] == second['manifest']['items']
    assert typeset(client, doc, version=1).content == first.content
    db.execute(update(Organization).where(Organization.id == doc.organization_id).values(name='Canlı değişiklik'))
    db.commit()
    def forbidden(*args, **kwargs):
        raise AssertionError('A frozen contract must never resolve live report facts')
    monkeypatch.setattr(service, 'report_data', forbidden)
    monkeypatch.setattr(service, 'resources', forbidden)
    monkeypatch.setattr(service, 'core_summary', forbidden)
    monkeypatch.setattr(service, 'lock_documents', forbidden)
    monkeypatch.setattr(financial, 'financial_data', forbidden)
    assert typeset(client, doc, version=1).content == first.content


def test_one_indicator_value_changes_only_its_item_hash(section_client, db, sample):
    client, docs, _, _ = section_client
    doc = docs['idare']
    token = login(client, 'strategy@example.invalid')
    ready_and_freeze(client, token, doc)
    payload = json.loads(service.latest_release(db, doc).payload_json, parse_float=Decimal)
    before = build_contract(payload)
    assert before['indicators']
    changed = copy.deepcopy(payload)
    changed['core']['indicators'][0]['actual'] += Decimal('1.000001')
    after = build_contract(changed)
    old = before['manifest']['items']; new = after['manifest']['items']
    assert old.keys() == new.keys()
    key=payload['_typeset']['indicators'][0]
    changed_id=f"ar:{doc.id}:indicator:{key['document_id']}:{key['indicator_id']}"
    assert [key for key in old if old[key] != new[key]] == [changed_id]
    assert before['manifest']['contract_sha256'] != after['manifest']['contract_sha256']
    check_manifest(after)


def test_draft_decimals_null_zero_and_repeated_export_are_exact(section_client, db, sample):
    client, docs, _, _ = section_client
    doc = docs['birim:' + str(sample['department'].id)]
    token = login(client, 'strategy@example.invalid')
    assert resource(client, token, doc, 'buildings', [
        {'name': 'Bina', 'category': 'Hizmet', 'address': 'Merkez', 'area': 12500.23, 'ownership': 'mülk'},
        {'name': 'Boş', 'category': 'Hizmet', 'address': '', 'area': None, 'ownership': 'mülk'},
        {'name': 'Sıfır', 'category': 'Hizmet', 'address': '', 'area': 0, 'ownership': 'mülk'}]).status_code == 200
    first = typeset(client, doc)
    assert first.status_code == 200, first.text
    assert first.content == typeset(client, doc).content
    contract = first.json()
    assert contract['schema_version'] == 'ar-typeset/1'
    assert contract['release_version'] == 'draft' and contract['source_sha256'] is None
    values = [row['values']['area'] for row in contract['rows'] if isinstance(row['values'], dict) and 'area' in row['values']]
    assert {'exact': '12500.23', 'display': '12.500,23'} in values
    assert {'exact': None, 'display': '—'} in values
    assert {'exact': '0.00', 'display': '0,00'} in values
    check_manifest(contract)


@pytest.mark.parametrize('email,scope,expected', [
    ('test@example.invalid','own',200),('test@example.invalid','other',403),('test@example.invalid','idare',403),
    ('strategy@example.invalid','own',200),('strategy@example.invalid','other',200),('strategy@example.invalid','idare',200)])
def test_contract_download_permissions_match_word_pdf(section_client, sample, email, scope, expected):
    client, docs, other, _ = section_client
    login(client, email)
    doc = docs['idare' if scope == 'idare' else 'birim:' + str(other.id if scope == 'other' else sample['department'].id)]
    assert typeset(client, doc).status_code == expected
    if expected == 200:
        assert 'Dizgi verisi (JSON)' in client.get(f'/activity-sections/reports/{doc.id}').text
    else:
        assert f'/reports/{doc.id}/typeset.json' not in client.get('/activity-sections').text


def test_approved_unit_history_uses_pinned_keys(section_client, db, sample):
    client, docs, _, _ = section_client
    doc = docs['birim:' + str(sample['department'].id)]
    ready_unit(db, doc, sample['user'])
    keys_blocks = [{'type':'table','rows':[['Kaynak','Değer'],['Ölçüm','5']]}]
    service.save_section(db, sample['user'], doc.id, 'I.A', keys_blocks, 'ready', '', doc.revision)
    db.commit()
    approval = approve_unit(db, doc, sample['user'])
    response = typeset(client, doc, approval_id=approval.id)
    assert response.status_code == 200, response.text
    assert response.json()['source_sha256'] == approval.sha256
    assert response.json()['release_version'] == approval.revision
    check_manifest(response.json())
    assert any(table['kind'] == 'section' for table in response.json()['tables'])
    assert f'approval_id={approval.id}' in client.get(f'/activity-sections/reports/{doc.id}').text


def test_checked_in_synthetic_samples_csv_and_hashes(tmp_path):
    import csv
    import hashlib
    import io
    import subprocess
    import sys
    from app.ar_typeset_contract import verify_contract
    folder = Path(__file__).parent / 'artifacts/civ086'
    first = json.loads((folder/'release-1.typeset.json').read_text())
    second = json.loads((folder/'release-2-one-indicator.typeset.json').read_text())
    check_manifest(first); check_manifest(second)
    assert verify_contract(first) and verify_contract(second)
    assert first['manifest']['items'].keys() == second['manifest']['items'].keys()
    changed = [key for key, value in first['manifest']['items'].items() if second['manifest']['items'][key] != value]
    assert changed == [first['indicators'][0]['id']]
    assert first['indicators'][0]['values']['actual'] == {'exact':'12500.230000','display':'12.500,230000'}
    assert first['indicators'][0]['values']['deviation']['delta']['exact'] == '0.000000'
    assert first['indicators'][0]['values']['deviation']['achievement_percent'] == {'exact':None,'display':'—'}
    assert first['activities'] and any(t['kind']=='activity_costs' for t in first['tables'])
    assert any(row.get('provenance',{}).get('kind')=='xlsx_import' for row in first['rows'])
    assert any(section.get('provenance',{}).get('kind')=='previous_year_copy' for section in first['sections'])
    source = (folder/'synthetic-source.json').read_bytes()
    assert hashlib.sha256(source).hexdigest() == first['source_sha256']
    result = subprocess.run([sys.executable,str(Path(__file__).parents[1]/'tools/ar_typeset_csv.py'),
        str(folder/'release-1.typeset.json'),str(tmp_path/'csv')],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    index=json.loads((tmp_path/'csv/tablolar.json').read_text())
    text=(tmp_path/'csv'/index['ar:1:budget:expenditure']['file']).read_text(encoding='utf-8-sig')
    rows=list(csv.DictReader(io.StringIO(text)))
    assert rows[0]['actual.exact']=='12500.23' and rows[0]['actual.display']=='12.500,23'
    assert rows[0]['id'].startswith('ar:1:budget:expenditure:row:')
    first['indicators'][0]['values']['actual']['exact']='999'
    assert not verify_contract(first)


def test_pinned_activity_ids_and_decimal_targets_come_from_bound_publication(section_client, db, sample):
    from app import activity_contract_service as contract_service
    from app.models import Publication, ReportIndicator, Submission, ReportSection, DepartmentScope
    from test_activity_contract import actual_payload
    client,docs,other,finance=section_client
    token=login(client,'strategy@example.invalid')
    db.scalar(select(Submission)).status='approved'
    db.add(ReportSection(period_id=sample['period'].id,title='Genel Bilgiler',kind='text',content_json='{}'))
    for dep in (other,finance):
        scope=db.scalar(select(DepartmentScope).where(DepartmentScope.department_id==dep.id))
        scope.status='excluded';scope.reason='Sentetik yayın kapsamı dışında'
    db.commit()
    assert client.post('/report-builder/publish',data={'csrf_token':token,'period_id':sample['period'].id}).status_code==303
    publication=db.scalar(select(Publication))
    revision=contract_service.create_report_revision(db,sample['strategy'],publication.id,sample['department'].organization_id)
    db.commit()
    indicator=db.scalar(select(ReportIndicator).where(ReportIndicator.report_revision_id==revision.id))
    response=client.post(f'/api/activity-reports/indicators/{indicator.id}/actuals',headers={'X-CSRF-Token':token},json=actual_payload())
    assert response.status_code==200,response.text
    own=docs['birim:'+str(sample['department'].id)]
    response=typeset(client,own)
    assert response.status_code==200,response.text
    contract=response.json();check_manifest(contract)
    assert contract['activities'][0]['id'].endswith(':'+str(sample['activity'].id))
    assert contract['activities'][0]['values']['publication_id']==publication.id
    assert contract['indicators'][0]['values']['actual']['exact']=='2.750001'
    assert contract['indicators'][0]['values']['targets'][0]['value']['exact']=='1.750000'
    assert contract['indicators'][0]['values']['deviation']['delta']['exact']=='1.000001'


def test_download_button_in_browser(section_client, sample, tmp_path):
    import os
    from playwright.sync_api import sync_playwright
    client,docs,_,_=section_client
    doc=docs['birim:'+str(sample['department'].id)]
    login(client,'test@example.invalid')
    with sync_playwright() as playwright:
        options={'headless':True}
        if os.getenv('CIVENSA_CHROMIUM_PATH'):
            options['executable_path']=os.environ['CIVENSA_CHROMIUM_PATH']
        browser=playwright.chromium.launch(**options)
        context=browser.new_context(accept_downloads=True)
        def serve(route):
            request=route.request
            response=client.request(request.method,request.url,content=request.post_data_buffer,
                headers={'content-type':request.headers.get('content-type','')},follow_redirects=False)
            headers=dict(response.headers);headers.pop('set-cookie',None)
            route.fulfill(status=response.status_code,headers=headers,body=response.content)
        context.route('http://testserver/**',serve)
        page=context.new_page()
        page.goto(f'http://testserver/activity-sections/reports/{doc.id}')
        with page.expect_download() as captured:
            page.get_by_role('link',name='Dizgi verisi (JSON)',exact=True).click()
        download=captured.value
        assert download.suggested_filename==f'faaliyet-raporu-{doc.id}-dizgi.json'
        target=tmp_path/'typeset.json';download.save_as(target)
        check_manifest(json.loads(target.read_text()))
        context.close();browser.close()


def test_key_metadata_does_not_change_legacy_report_shape(section_client, db, sample):
    client,docs,_,_=section_client
    doc=docs['birim:'+str(sample['department'].id)]
    token=login(client,'test@example.invalid')
    assert resource(client,token,doc,'hardware',[{'category':'Bilgisayar','count':1}]).status_code==200
    regular=client.get(f'/api/activity-sections/reports/{doc.id}').json()
    assert '_typeset' not in regular
    assert 'stable_key' not in regular['resources']['hardware']['rows'][0]
    keys=client.get(f'/api/activity-sections/reports/{doc.id}/typeset-keys')
    assert keys.status_code==200,keys.text
    assert keys.json()['resources']['hardware'][0]['stable_key']==db.scalar(select(ARResourceRow.stable_key).where(ARResourceRow.document_id==doc.id))


def test_indicator_correction_through_unit_approval_changes_only_indicator_hash(section_client, db, sample):
    from app import ar_unit_workflow_service as workflow
    from app.models import ActualRevision, ReportIndicator, PublicationIndicatorBinding
    from ar_unit_workflow_helpers import reviewer
    client,docs,_,_=section_client
    unit=docs['birim:'+str(sample['department'].id)]
    doc=docs['idare']
    token=login(client,'strategy@example.invalid')
    assert resource(client,token,unit,'hardware',[{'category':'Bilgisayar','count':5}]).status_code==200
    ready_and_freeze(client,token,doc)
    first=typeset(client,doc,version=1).json()
    payload=json.loads(service.latest_release(db,doc).payload_json)
    identity=next(key for key in payload['_typeset']['indicators'] if key['document_id']==unit.id)
    expected=f"ar:{doc.id}:indicator:{unit.id}:{identity['indicator_id']}"
    workflow.transition(db,reviewer(db,unit),unit.id,'reopen',unit.revision,'Gösterge gerçekleşmesi düzeltilecek.')
    db.commit()
    indicator=db.scalar(select(ReportIndicator).join(PublicationIndicatorBinding,
        PublicationIndicatorBinding.id==ReportIndicator.publication_binding_id).where(
        PublicationIndicatorBinding.department_id==unit.department_id))
    previous=db.scalar(select(ActualRevision).where(ActualRevision.report_indicator_id==indicator.id)
        .order_by(ActualRevision.revision.desc()).limit(1))
    db.add(ActualRevision(report_indicator_id=indicator.id,revision=previous.revision+1,supersedes_id=previous.id,
        value=previous.value+Decimal('1.000001'),raw_text='1,000001',state=previous.state,
        evidence_json=previous.evidence_json,explanation=previous.explanation,deviation_json=previous.deviation_json,
        created_by=sample['user'].id))
    db.commit()
    approve_unit(db,unit,sample['user'])
    assert reopen(client,token,doc).status_code==200
    assert freeze(client,token,doc).status_code==200
    second=typeset(client,doc,version=2).json()
    old=first['manifest']['items'];new=second['manifest']['items']
    assert old.keys()==new.keys()
    assert [key for key in old if old[key]!=new[key]]==[expected]
    assert first['manifest']['contract_sha256']!=second['manifest']['contract_sha256']
    assert typeset(client,doc,version=1).json()==first


def test_waiting_draft_download_rechecks_a_release_created_before_source_lock(section_client, db, sample, monkeypatch):
    client,docs,_,_=section_client
    doc=docs['idare']
    token=login(client,'strategy@example.invalid')
    ready_and_freeze(client,token,doc)
    assert reopen(client,token,doc).status_code==200
    original_lock=service.lock_documents
    published=[]
    def release_wins_lock(session, current):
        original_lock(session,current)
        if not published:
            published.append(True)
            service.freeze_document(session,sample['strategy'],current.id,current.revision)
    monkeypatch.setattr(service,'lock_documents',release_wins_lock)
    response=typeset(client,doc)
    assert response.status_code==200,response.text
    assert response.json()['release_version']==2
    assert response.json()['frozen'] is True
    assert response.json()['source_sha256']==service.latest_release(db,doc).sha256


def test_explicit_new_free_rows_do_not_reuse_deleted_row_keys(section_client, db, sample):
    client,docs,_,_=section_client
    doc=docs['birim:'+str(sample['department'].id)]
    token=login(client,'strategy@example.invalid')
    blocks=[{'type':'table','rows':[['A','5'],['A','5']]}]
    assert post_section(client,token,doc,blocks).status_code==200
    _,content=service.section_pair(db,doc,'I.A')
    keys=section_keys(db,content)
    old=list(keys[0]['rows'])
    keys[0]['rows'][0]=None
    assert post_section(client,token,doc,blocks,keys).status_code==200
    updated=section_keys(db,content)
    assert updated[0]['rows'][0] not in old
    assert updated[0]['rows'][1]==old[1]
    malformed=[{**updated[0],'rows':1}]
    assert post_section(client,token,doc,blocks,malformed).status_code==422


def test_csv_keeps_negative_decimal_scale_and_guards_untrusted_text():
    import csv
    import io
    from app.ar_typeset_csv import table_csv
    contract={'tables':[{'id':'t','row_ids':['r']}],'rows':[{'id':'r','values':{
        'name':'=SUM(A1)','amount':{'exact':'-12500.230000','display':'-12.500,230000'},
        'small':{'exact':'0.00000000','display':'0,00000000'}}}], 'indicators':[], 'activities':[]}
    output=table_csv(contract,'t').decode('utf-8-sig')
    row=next(csv.DictReader(io.StringIO(output)))
    assert row['id']=='r' and row['name']=="'=SUM(A1)"
    assert row['amount.exact']=='-12500.230000' and row['amount.display']=='-12.500,230000'
    assert row['small.exact']=='0.00000000'
