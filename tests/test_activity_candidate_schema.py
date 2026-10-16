"""S1: schema dispatch and fail-closed Activity v1 verification on PostgreSQL."""
import json
from decimal import Decimal
import pytest
from sqlalchemy import select
from sqlalchemy.orm.attributes import set_committed_value
from app.models import ActualRevision, ReportIndicator, PublicationIndicatorBinding
from app import report_workflow_service as service
from tests.test_report_workflow import foundation_db, people, package, approved, candidate, rejects

pytestmark = pytest.mark.postgres
activity_only = pytest.mark.parametrize('package', ['activity_report'], indirect=True)


def fetched_payload(candidate, payload):
    # Corrupt only the fetched representation; immutable DB history stays intact.
    raw = service.canonical(payload)
    set_committed_value(candidate, 'payload_json', raw)
    set_committed_value(candidate, 'payload_sha256', service.contract.digest(raw))
    set_committed_value(candidate, 'sha256', service.hash_content(raw, candidate.manifest_json))


def assert_conflict(db, candidate):
    rejects(409, lambda: service.verify(db, candidate))
    rejects(409, lambda: service.verify_materialization(db, candidate))


def test_existing_candidates_verify_unchanged(foundation_db, candidate):
    db = foundation_db; c = candidate
    before = (c.payload_json, c.manifest_json, c.sha256)
    assert service.verify(db, c) == json.loads(c.manifest_json)
    if c.resource_scope == 'activity_report':
        assert json.loads(c.payload_json)['schema_version'] == 'activity-candidate-1'
        service.verify_materialization(db, c)
    assert (c.payload_json, c.manifest_json, c.sha256) == before


@activity_only
@pytest.mark.parametrize('schema', ['activity-candidate-2', 'unknown', None, 1, True, [], {}, ''])
def test_unknown_or_malformed_schema_fails_closed(foundation_db, candidate, schema):
    payload = json.loads(candidate.payload_json); payload['schema_version'] = schema
    fetched_payload(candidate, payload)
    assert_conflict(foundation_db, candidate)


@activity_only
def test_missing_schema_fails_closed(foundation_db, candidate):
    payload = json.loads(candidate.payload_json); del payload['schema_version']
    fetched_payload(candidate, payload)
    assert_conflict(foundation_db, candidate)


@activity_only
@pytest.mark.parametrize('bad', ['missing_entries', 'null_entries', 'object_entries', 'string_entry', 'list_entry',
                                'null_entry', 'missing_actual_id', 'object_actual_id', 'bool_indicator_id',
                                'string_definition_id', 'missing_value', 'object_value', 'missing_explanation',
                                'missing_evidence', 'missing_deviation', 'wrong_revision_type', 'missing_state', 'oversized_actual_id'])
def test_malformed_v1_entries_conflict_in_both_boundaries(foundation_db, candidate, bad):
    payload = json.loads(candidate.payload_json); entry = payload['entries'][0]
    if bad == 'missing_entries':del payload['entries']
    elif bad == 'null_entries':payload['entries'] = None
    elif bad == 'object_entries':payload['entries'] = {}
    elif bad == 'string_entry':payload['entries'] = ['bad']
    elif bad == 'list_entry':payload['entries'] = [[]]
    elif bad == 'null_entry':payload['entries'] = [None]
    elif bad == 'missing_actual_id':del entry['materialized_actual_revision_id']
    elif bad == 'object_actual_id':entry['materialized_actual_revision_id'] = {}
    elif bad == 'oversized_actual_id':entry['materialized_actual_revision_id'] = 10**100
    elif bad == 'bool_indicator_id':entry['materialized_report_indicator_id'] = True
    elif bad == 'string_definition_id':entry['definition_revision_id'] = '1'
    elif bad == 'object_value':entry['value'] = {}
    elif bad == 'wrong_revision_type':payload['report_revision_id'] = []
    else:del entry[bad.removeprefix('missing_')]
    fetched_payload(candidate, payload)
    assert_conflict(foundation_db, candidate)


@activity_only
@pytest.mark.parametrize('raw', ['{', 'null', '[]', '"bad"'])
def test_malformed_payload_json_conflicts(foundation_db, candidate, raw):
    set_committed_value(candidate, 'payload_json', raw)
    assert_conflict(foundation_db, candidate)


@activity_only
@pytest.mark.parametrize('field', ['value', 'state', 'evidence', 'explanation', 'deviation', 'definition',
                                  'definition_revision_id', 'report_indicator_id', 'reference_actual_revision_id'])
def test_exact_package_comparison_rejects_unstripped_changes(foundation_db, candidate, field):
    payload = json.loads(candidate.payload_json); entry = payload['entries'][0]
    entry[field] = (entry[field] + 999 if field in {'definition_revision_id', 'report_indicator_id'}
                    else {'delta': '999'} if field == 'deviation'
                    else {} if field == 'definition'
                    else [] if field == 'evidence'
                    else 999 if field == 'reference_actual_revision_id'
                    else 'tampered')
    fetched_payload(candidate, payload)
    rejects(409, lambda: service.verify(foundation_db, candidate))


@activity_only
@pytest.mark.parametrize('field', ['materialized_report_indicator_id', 'materialized_actual_revision_id'])
def test_stripped_realization_ids_still_require_exact_materialization(foundation_db, candidate, field):
    payload = json.loads(candidate.payload_json); payload['entries'][0][field] += 999
    fetched_payload(candidate, payload)
    assert_conflict(foundation_db, candidate)


@activity_only
@pytest.mark.parametrize('rule', ['report_revision', 'indicator_set', 'actual_count', 'actual_owner', 'value',
                                 'state', 'evidence', 'explanation', 'deviation', 'definition_binding'])
def test_v1_materialization_rules_remain_enforced(foundation_db, candidate, rule, monkeypatch):
    db = foundation_db; c = candidate; payload = json.loads(c.payload_json); entry = payload['entries'][0]
    actual = db.get(ActualRevision, entry['materialized_actual_revision_id'])
    if rule == 'report_revision':payload['report_revision_id'] += 999; fetched_payload(c, payload)
    elif rule in {'indicator_set', 'actual_count'}:
        original = db.scalars
        def scalars(statement, *args, **kwargs):
            if rule == 'indicator_set' and 'FROM report_indicators' in str(statement):return FakeRows([])
            if rule == 'actual_count' and 'FROM actual_revisions' in str(statement):return FakeRows([actual, actual])
            return original(statement, *args, **kwargs)
        monkeypatch.setattr(db, 'scalars', scalars)
    elif rule == 'actual_owner':set_committed_value(actual, 'report_indicator_id', actual.report_indicator_id + 999)
    elif rule == 'definition_binding':
        indicator = db.get(ReportIndicator, entry['materialized_report_indicator_id'])
        binding = db.get(PublicationIndicatorBinding, indicator.publication_binding_id)
        set_committed_value(binding, 'definition_revision_id', binding.definition_revision_id + 999)
    else:
        field = {'evidence': 'evidence_json', 'deviation': 'deviation_json'}.get(rule, rule)
        value = Decimal('999') if rule == 'value' else '[]' if rule == 'evidence' else '{}' if rule == 'deviation' else 'tampered'
        set_committed_value(actual, field, value)
    rejects(409, lambda: service.verify_materialization(db, c))


class FakeRows:
    def __init__(self, rows):self.rows = rows
    def all(self):return self.rows


@pytest.mark.parametrize('package', ['performance_program'], indirect=True)
def test_program_verification_does_not_use_activity_schema(foundation_db, candidate, monkeypatch):
    def forbidden(*args):raise AssertionError('Activity verification reached for Program')
    monkeypatch.setattr(service, 'activity_candidate_payload', forbidden)
    monkeypatch.setattr(service, 'activity_realization_keys', forbidden)
    monkeypatch.setattr(service, 'verify_materialization', forbidden)
    assert service.verify(foundation_db, candidate) == json.loads(candidate.manifest_json)
