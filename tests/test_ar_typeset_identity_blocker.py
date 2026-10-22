"""CIV-086 stop-condition evidence, not acceptance of an ar-typeset/1 contract.

Replace these characterization checks when the historical-identity policy is
decided. They demonstrate why a frozen-only adapter cannot supply the promised
identities for all currently valid reports.
"""
import json
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app import activity_sections_service as service
from app.models import ARResourceRow, IndicatorDefinitionRevision
from ar_unit_workflow_helpers import ensure_core_ready
from test_activity_sections import section_client, login, resource, ready_and_freeze

pytestmark = pytest.mark.postgres
ARTIFACT = Path(__file__).parent / 'artifacts/civ086/identity-loss.json'


def test_distinct_resource_identities_have_identical_frozen_projection(section_client, db, sample):
    client, docs, _, _ = section_client
    doc = docs['birim:' + str(sample['department'].id)]
    token = login(client, 'strategy@example.invalid')
    example = json.loads(ARTIFACT.read_text())
    rows = example['accepted_resource_input']
    assert resource(client, token, doc, 'hardware', rows).status_code == 200
    stored = db.scalars(select(ARResourceRow).where(ARResourceRow.document_id == doc.id,
        ARResourceRow.table_kind == 'hardware').order_by(ARResourceRow.id)).all()
    assert len(stored) == 2 and stored[0].id != stored[1].id
    # Even before freezing, the serializer has erased the distinguishing PKs.
    assert service.row_data(stored[0]) == service.row_data(stored[1])
    projected = [service.row_data(row) for row in stored]
    assert service.numeric_canonical(projected) == service.numeric_canonical(projected[::-1])
    ready_and_freeze(client, token, doc, legacy=True)
    response = client.get(f'/activity-sections/reports/{doc.id}/export.json?version=1')
    assert response.status_code == 200
    frozen_rows = response.json()['resources']['hardware']['rows']
    assert frozen_rows[0] == frozen_rows[1]
    assert not {'id', 'row_id', 'row_key'} & frozen_rows[0].keys()


def test_identical_resource_save_replaces_existing_primary_keys(section_client, db, sample):
    client, docs, _, _ = section_client
    doc = docs['birim:' + str(sample['department'].id)]
    token = login(client, 'strategy@example.invalid')
    rows = json.loads(ARTIFACT.read_text())['accepted_resource_input']
    def identities():
        return set(db.scalars(select(ARResourceRow.id).where(
            ARResourceRow.document_id == doc.id, ARResourceRow.table_kind == 'hardware')))
    assert resource(client, token, doc, 'hardware', rows).status_code == 200
    before = identities()
    assert resource(client, token, doc, 'hardware', rows).status_code == 200
    after = identities()
    assert len(before) == len(after) == 2 and before.isdisjoint(after)


def test_free_text_tables_have_no_persisted_identity():
    blocks = json.loads(ARTIFACT.read_text())['accepted_section_blocks']
    assert service.validate_blocks(blocks) == blocks
    assert blocks[0] == blocks[1]
    assert blocks[0]['rows'][0] == blocks[0]['rows'][1]
    # There is no existing table/row key to expose through a new export.
    with pytest.raises(HTTPException, match='biçimi geçersiz'):
        service.validate_blocks([{**blocks[0], 'id': 'table:example'}])


def test_core_projection_omits_existing_persistent_indicator_identity(section_client, db, sample):
    _, docs, _, _ = section_client
    doc = docs['birim:' + str(sample['department'].id)]
    ensure_core_ready(db, doc, sample['user'])
    definition = db.scalar(select(IndicatorDefinitionRevision))
    assert definition.indicator_id
    indicator = service.core_summary(db, doc)['indicators'][0]
    assert indicator['name'] == json.loads(definition.definition_json)['name']
    assert not {'id', 'indicator_id', 'persistent_indicator_id', 'publication_binding_id'} & indicator.keys()
