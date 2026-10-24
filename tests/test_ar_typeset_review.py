"""Lead review regressions: designer metadata and corrupt persisted row positions."""
import copy
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select

from app import activity_sections_service as service
from app.ar_typeset_contract import build_contract, canonical_bytes, verify_contract
from app.ar_typeset_keys import section_keys
from app.models import ARSectionRowKey
from test_activity_sections import section_client, login
from test_ar_typeset_contract import post_section


@pytest.mark.parametrize('scope', ['idare', 'birim'])
def test_designer_contract_excludes_named_editors_reopen_and_workflow_metadata(scope):
    folder = Path(__file__).parent / 'artifacts/civ086'
    source_bytes = (folder / 'synthetic-source.json').read_bytes()
    payload = json.loads(source_bytes, parse_float=Decimal)
    assert canonical_bytes(build_contract(payload, release_version=1,
        source_sha256=hashlib.sha256(source_bytes).hexdigest())) == (folder / 'release-1.typeset.json').read_bytes()
    names = ['Nermin Örnek Editör', 'Deniz Örnek Onaycı', 'Ekin Örnek Açan']
    actor_ids = [9150000000001, 9150000000002, 9150000000003]
    reasons = ['Özel yeniden açma gerekçesi', 'Özel birim iade gerekçesi', 'Özel bölüm gerekçesi']
    payload.update(scope=scope, department_id=2 if scope == 'birim' else None,
        title='Faaliyet Raporu', status='draft', source_editor_ids=actor_ids,
        edited_by=actor_ids[0], editor_name=names[0], reason=reasons[0],
        reopened=True, releases=[{'id': 83, 'version': 1, 'reopen': {
            'actor_id': actor_ids[2], 'actor_name': names[2], 'reason': reasons[0]}}],
        workflow={'status': 'returned', 'reason': reasons[1], 'events': [{
            'action': 'return', 'actor_id': actor_ids[1], 'actor_name': names[1], 'reason': reasons[1]}]},
        unit_manifest=[{'document_id': 2, 'actor_id': actor_ids[1], 'actor_name': names[1]}],
        future_audit_metadata={'person_name': names[2], 'reason': reasons[0]})
    for section in payload['sections']:
        section.update(edited_by=actor_ids[0], editor_name=names[0], reason=reasons[2],
            future_audit_metadata={'person_name': names[2], 'actor_id': actor_ids[2]})
    before = copy.deepcopy(payload)
    contract = build_contract(payload)
    raw = canonical_bytes(contract)
    for secret in [*names, *map(str, actor_ids), *reasons, 'Sentetik Strateji']:
        assert secret.encode('utf-8') not in raw
    for field in ('releases', 'reopened', 'reopen', 'workflow', 'source_editor_ids',
                  'edited_by', 'editor_name', 'actor_id', 'actor_name', 'reason', 'future_audit_metadata'):
        assert ('"' + field + '":').encode() not in raw
    assert contract['context']['title'] == 'Faaliyet Raporu'
    assert contract['context']['status'] == 'draft'
    assert contract['context']['scope'] == scope
    assert contract['context']['year'] == 2027
    assert contract['context']['organization'] == payload['organization']
    assert next(s for s in contract['sections'] if s['code'] == 'I.A')['provenance'] == {'kind': 'manual'}
    assert next(s for s in contract['sections'] if s['code'] == 'II.A')['provenance'] == {
        'kind': 'previous_year_copy', 'copied_from_id': 7}
    assert verify_contract(contract)
    assert payload == before  # Filtering must not rewrite the source snapshot.


@pytest.mark.postgres
@pytest.mark.parametrize('position', [-1, 1])
def test_stored_section_row_position_outside_source_rows_returns_turkish_422(section_client, db, sample, position):
    client, docs, _, _ = section_client
    doc = docs['birim:' + str(sample['department'].id)]
    token = login(client, 'strategy@example.invalid')
    blocks = [{'type': 'table', 'rows': [['Hizmet', '5']]}]
    assert post_section(client, token, doc, blocks).status_code == 200
    _, content = service.section_pair(db, doc, 'I.A')
    keys = section_keys(db, content)
    row = db.scalar(select(ARSectionRowKey).where(ARSectionRowKey.document_id == doc.id))
    row.position = position
    db.commit()
    revision = doc.revision
    response = post_section(client, token, doc, blocks, keys)
    assert response.status_code == 422
    assert response.json()['detail'] == ('Tablo veya satır anahtarı bu kayda ait değil ya da yinelenmiş. '
        'Sayfayı yenileyip kendi raporunuzdaki satırı düzenleyin.')
    db.refresh(content)
    db.refresh(doc)
    assert json.loads(content.blocks_json) == blocks and doc.revision == revision
    assert section_keys(db, content) == keys
