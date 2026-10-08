"""Phase 5B1 unchanged-value reference / resolution engine (pure helpers, no DB writes)."""
import ast
import inspect
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from app import activity_revision_reference as ref
from app.activity_revision_reference import (ActivityReferenceError, IndicatorContext, MaterializedRealization,
    SourceProvenance, SourceRealization, UnchangedValueReference, build_reference, canonical_decimal, canonical_json,
    check_reference_eligibility, content_from_actual_revision, content_from_entry, content_from_fields,
    resolve_effective_realization, resolve_successor_realizations, verify_reference,
    verify_source_against_candidate_entry)
from app.activity_contract_service import canonical as contract_canonical, digest as contract_digest

SHA_PUB = 'a' * 64
SHA_CANDIDATE = 'b' * 64
IDENTITY = '6f1c2b8e-0d5a-4c1e-9a7b-1f2e3d4c5b6a'
EVIDENCE = [{'title': 'Kayıt defteri', 'locator': 'Sayfa 3', 'source_revision': '2027-12 kayıt 4'},
            {'title': 'Sistem raporu', 'locator': 'Tablo 2', 'source_revision': 'v7'}]


def definition(**changes):
    data = {'name': 'Hizmet sayısı', 'code': 'G-1', 'unit': 'Adet', 'explanation': 'Ortak açıklama',
            'calculation_method': 'Kaynak yöntemi', 'data_source': 'Kaynak kayıt', 'card_id': 3,
            'subprogram_id': 2, 'department_id': 7, 'year': 2027, 'definition_contract_version': '3.0',
            'targets': [{'year': 2027, 'value_kind': 'target', 'value': '100.000000', 'raw_text': '100',
                         'state': 'verified'}]}
    data.update(changes)
    return contract_canonical(data)


def context(definition_json=None, **changes):
    text = definition_json or definition()
    data = dict(organization_id=1, activity_report_id=5, reporting_period_id=3, report_revision_id=21, report_revision_number=1,
                report_indicator_id=31, persistent_indicator_id=IDENTITY, definition_revision_id=11,
                definition_sha256=contract_digest(text), definition_json=text, publication_id=9,
                publication_sha256=SHA_PUB, contract_version='3.0')
    data.update(changes)
    return IndicatorContext(**data)


def successor_context(definition_json=None, **changes):
    data = dict(report_revision_id=22, report_revision_number=2, report_indicator_id=41)
    data.update(changes)
    return context(definition_json, **data)


def fields(**changes):
    data = dict(value='112.5', state='verified', evidence=[dict(e) for e in EVIDENCE],
                explanation='Hedef aşıldı.',
                deviation={'corrective_action': 'İzle', 'calculation_rule_version': 'difference-v1',
                           'target_definition_revision_id': 11, 'delta': '12.5', 'achievement_percent': None})
    data.update(changes)
    return data


def content(**changes):
    return content_from_fields(**fields(**changes))


def provenance(**changes):
    data = dict(release_id=70, release_major=1, release_minor=0, candidate_id=60,
                candidate_sha256=SHA_CANDIDATE, activity_approval_id=50, actual_revision_id=81)
    data.update(changes)
    return SourceProvenance(**data)


def source(ctx=None, prov=None, cnt=None):
    return SourceRealization(ctx or context(), prov or provenance(), cnt or content())


def codes(result):
    return {m.code for m in result.mismatches}


def expect(code, call, *args, **kwargs):
    with pytest.raises(ActivityReferenceError) as exc:
        call(*args, **kwargs)
    assert exc.value.code == code, (exc.value.code, exc.value.message)
    return exc.value


# 1
def test_unchanged_realization_is_eligible_and_reference_builds():
    result = check_reference_eligibility(source(), successor_context(), content())
    assert result.eligible and result.mismatches == ()
    reference = build_reference(source(), successor_context(), content())
    payload = reference.payload
    assert payload['source']['actual_revision_id'] == 81 and payload['source']['report_indicator_id'] == 31
    assert payload['successor']['report_indicator_id'] == 41
    assert payload['binding']['persistent_indicator_id'] == IDENTITY
    assert payload['content_sha256'] == content().sha256


# 2-6
@pytest.mark.parametrize('changes,code', [
    (dict(value='112.6', deviation=dict(fields()['deviation'], delta='12.6')), 'value_changed'),
    (dict(state='needs_review', deviation=dict(fields()['deviation'], delta=None)), 'state_changed'),
    (dict(evidence=EVIDENCE[:1]), 'evidence_changed'),
    (dict(explanation='Hedef aşıldı. '), 'explanation_changed'),
    (dict(deviation=dict(fields()['deviation'], corrective_action='Düzelt')), 'deviation_changed'),
])
def test_changed_content_is_rejected(changes, code):
    result = check_reference_eligibility(source(), successor_context(), content(**changes))
    assert not result.eligible and code in codes(result)
    expect(code, build_reference, source(), successor_context(), content(**changes))


# 7
def test_definition_revision_mismatch_rejected():
    result = check_reference_eligibility(source(), successor_context(definition_revision_id=12), content())
    assert not result.eligible and 'definition_revision_mismatch' in codes(result)


# 8
def test_definition_hash_mismatch_rejected():
    changed = successor_context(definition(name='Yeni ad'))
    result = check_reference_eligibility(source(), changed, content())
    assert not result.eligible and 'definition_hash_mismatch' in codes(result)
    assert 'target_mismatch' not in codes(result)  # same target, only definition text changed


# 9
def test_persistent_identity_mismatch_rejected():
    result = check_reference_eligibility(source(), successor_context(persistent_indicator_id='other-identity'), content())
    assert not result.eligible and 'identity_mismatch' in codes(result)


# 10
@pytest.mark.parametrize('changes', [dict(publication_id=10), dict(publication_sha256='c' * 64)])
def test_program_publication_base_mismatch_rejected(changes):
    result = check_reference_eligibility(source(), successor_context(**changes), content())
    assert not result.eligible and 'program_base_mismatch' in codes(result)


def test_contract_version_mismatch_rejected():
    v2 = definition(definition_contract_version='2.0')
    result = check_reference_eligibility(source(), successor_context(v2, contract_version='2.0'), content())
    assert 'program_base_mismatch' in codes(result)


# 11
def test_target_semantic_mismatch_rejected():
    targets = [{'year': 2027, 'value_kind': 'target', 'value': '101.000000', 'raw_text': '101', 'state': 'verified'}]
    result = check_reference_eligibility(source(), successor_context(definition(targets=targets)), content())
    assert not result.eligible and {'target_mismatch', 'definition_hash_mismatch'} <= codes(result)
    # The proposed delta is no longer difference-v1 consistent for the new target either.
    assert 'deviation_mismatch' in codes(result)


def test_target_raw_text_is_not_target_semantics():
    targets = [{'year': 2027, 'value_kind': 'target', 'value': '100', 'raw_text': '100,0', 'state': 'verified'}]
    assert successor_context(definition(targets=targets)).target_semantics_sha256 == context().target_semantics_sha256


# 12
def test_cross_organization_rejected():
    result = check_reference_eligibility(source(), successor_context(organization_id=2), content())
    assert not result.eligible and 'organization_mismatch' in codes(result)


def test_cross_report_and_non_successor_rejected():
    assert 'report_mismatch' in codes(check_reference_eligibility(source(), successor_context(activity_report_id=6), content()))
    same = check_reference_eligibility(source(), context(), content())
    older = check_reference_eligibility(source(), successor_context(report_revision_number=1), content())
    assert 'not_a_successor' in codes(same) and 'not_a_successor' in codes(older)
    reused_slot = check_reference_eligibility(source(), successor_context(report_indicator_id=31), content())
    assert 'not_a_successor' in codes(reused_slot)


# Red-team invariant: the reporting period must match exactly; cross-period inheritance fails closed.
def test_cross_period_reference_rejected():
    other_period = successor_context(reporting_period_id=4)
    result = check_reference_eligibility(source(), other_period, content())
    assert not result.eligible and 'reporting_period_mismatch' in codes(result)
    expect('reporting_period_mismatch', build_reference, source(), other_period, content())
    other_year = successor_context(definition(year=2028))
    result = check_reference_eligibility(source(), other_year, content())
    assert {'reporting_period_mismatch', 'definition_hash_mismatch'} <= codes(result)
    assert build_reference(source(), successor_context(), content()).payload['source']['reporting_period_id'] == 3


def test_cross_period_reference_injection_rejected():
    src = source()
    reference = build_reference(src, successor_context(), content())
    # A source claiming another period cannot satisfy a reference bound to period 3.
    foreign = source(ctx=context(reporting_period_id=4))
    expect('reporting_period_mismatch', resolve_effective_realization, successor_context(),
           reference=reference, source=foreign)
    # Re-hashed provenance that rewrites either side's period is rejected against the real inputs.
    for section in ('source', 'successor'):
        payload = reference.payload
        payload[section]['reporting_period_id'] = 4
        text = canonical_json(payload)
        forged = UnchangedValueReference(text, ref.sha256_hex(text))
        code = 'source_provenance_mismatch' if section == 'source' else 'successor_mismatch'
        expect(code, resolve_effective_realization, successor_context(), reference=forged, source=src)
    payload = reference.payload
    payload['binding']['reporting_year'] = 2028
    text = canonical_json(payload)
    expect('binding_mismatch', verify_reference, UnchangedValueReference(text, ref.sha256_hex(text)),
           source=src, successor=successor_context())


def test_definition_without_reporting_year_fails_closed():
    no_year = contract_canonical({k: v for k, v in json.loads(definition()).items() if k != 'year'})
    expect('definition_integrity', context, no_year)
    expect('incomplete_provenance', context, reporting_period_id=None)


# 13
def test_materialized_only_resolution_succeeds():
    new = content(value='0', evidence=EVIDENCE[:1], deviation=dict(fields()['deviation'], delta='-100'))
    result = resolve_effective_realization(successor_context(), materialized=MaterializedRealization(41, new, 90))
    assert result.mode == ref.MODE_MATERIALIZED and result.reference_sha256 is None
    assert result.value == Decimal('0') and result.state == 'verified' and result.evidence == EVIDENCE[:1]
    assert result.actual_revision_id == 90 and result.content_sha256 == new.sha256


def test_materialized_for_other_indicator_or_wrong_delta_rejected():
    expect('successor_mismatch', resolve_effective_realization, successor_context(),
           materialized=MaterializedRealization(42, content()))
    wrong = content(deviation=dict(fields()['deviation'], delta='12.4'))
    expect('deviation_mismatch', resolve_effective_realization, successor_context(),
           materialized=MaterializedRealization(41, wrong))
    stale = content(deviation=dict(fields()['deviation'], target_definition_revision_id=10))
    expect('deviation_definition_mismatch', resolve_effective_realization, successor_context(),
           materialized=MaterializedRealization(41, stale))


# 14
def test_reference_only_resolution_succeeds():
    src = source()
    reference = build_reference(src, successor_context(), content())
    result = resolve_effective_realization(successor_context(), reference=reference, source=src)
    assert result.mode == ref.MODE_REFERENCE and result.reference_sha256 == reference.reference_sha256
    assert result.actual_revision_id == 81 and result.source_report_indicator_id == 31 and result.source_release_id == 70
    assert (result.value, result.state, result.evidence, result.explanation) == (
        Decimal('112.5'), 'verified', EVIDENCE, 'Hedef aşıldı.')
    assert result.deviation['delta'] == '12.5'


# 15
def test_both_materialized_and_reference_rejected():
    src = source()
    reference = build_reference(src, successor_context(), content())
    expect('ambiguous_realization', resolve_effective_realization, successor_context(),
           materialized=MaterializedRealization(41, content()), reference=reference, source=src)
    expect('ambiguous_realization', resolve_effective_realization, successor_context(),
           materialized=MaterializedRealization(41, content()), source=src)


# 16
def test_neither_rejected():
    expect('missing_realization', resolve_effective_realization, successor_context())
    expect('reference_missing', resolve_effective_realization, successor_context(), source=source())
    expect('reference_source_missing', resolve_effective_realization, successor_context(),
           reference=build_reference(source(), successor_context(), content()))


# 17
def test_tampered_reference_hash_rejected():
    reference = build_reference(source(), successor_context(), content())
    expect('reference_hash_invalid', UnchangedValueReference, reference.provenance_json, 'f' * 64)
    payload = reference.payload
    payload['source']['actual_revision_id'] = 82
    forged_text = canonical_json(payload)
    expect('reference_hash_invalid', UnchangedValueReference, forged_text, reference.reference_sha256)
    # A re-hashed forgery is internally consistent but does not bind the supplied source.
    forged = UnchangedValueReference(forged_text, ref.sha256_hex(forged_text))
    expect('source_provenance_mismatch', verify_reference, forged, source=source(), successor=successor_context())
    # Post-construction attribute tampering is re-checked at verification time.
    altered = UnchangedValueReference(reference.provenance_json, reference.reference_sha256)
    object.__setattr__(altered, 'reference_sha256', 'e' * 64)
    expect('reference_hash_invalid', verify_reference, altered, source=source(), successor=successor_context())


def test_reference_bound_to_other_successor_rejected():
    reference = build_reference(source(), successor_context(), content())
    expect('successor_mismatch', resolve_effective_realization, successor_context(report_indicator_id=42),
           reference=reference, source=source())


# 18
def test_tampered_source_value_rejected():
    reference = build_reference(source(), successor_context(), content())
    tampered = content(value='112.4', deviation=dict(fields()['deviation'], delta='12.4'))
    expect('source_content_mismatch', resolve_effective_realization, successor_context(),
           reference=reference, source=source(cnt=tampered))
    # A value edit without a consistent difference-v1 delta cannot even form a source.
    expect('deviation_mismatch', SourceRealization, context(), provenance(), content(value='112.4'))
    expect('source_provenance_mismatch', resolve_effective_realization, successor_context(),
           reference=reference, source=source(prov=provenance(actual_revision_id=82)))


# 19
def test_no_latest_or_global_fallback_exists():
    module_source = Path(ref.__file__).read_text(encoding='utf-8')
    imported = set()
    for node in ast.walk(ast.parse(module_source)):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split('.')[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add(('.' * node.level) + (node.module or ''))
    assert imported <= {'hashlib', 'json', 're', 'dataclasses', 'decimal'}, imported
    for name, function in inspect.getmembers(ref, inspect.isfunction):
        if function.__module__ == ref.__name__:
            assert not {'db', 'session', 'query'} & set(inspect.signature(function).parameters), name
    for token in ('select(', 'order_by', '.query', 'latest', 'with_for_update'):
        assert token not in module_source.split('"""', 2)[2], token
    # Without explicit input nothing is "found", even when a matching source exists.
    expect('missing_realization', resolve_successor_realizations, [successor_context()])


def test_batch_resolution_requires_exactly_one_input_per_indicator():
    src = source()
    reference = build_reference(src, successor_context(), content())
    second = successor_context(report_indicator_id=42)
    resolved = resolve_successor_realizations([successor_context(), second],
        materialized={42: MaterializedRealization(42, content())}, references={41: (reference, src)})
    assert resolved[41].mode == ref.MODE_REFERENCE and resolved[42].mode == ref.MODE_MATERIALIZED
    expect('missing_realization', resolve_successor_realizations, [successor_context(), second],
           references={41: (reference, src)})
    expect('ambiguous_realization', resolve_successor_realizations, [successor_context()],
           materialized={41: MaterializedRealization(41, content())}, references={41: (reference, src)})
    expect('unknown_indicator', resolve_successor_realizations, [successor_context()],
           materialized={41: MaterializedRealization(41, content()), 99: MaterializedRealization(99, content())})
    expect('invalid_input', resolve_successor_realizations, [successor_context(), successor_context()],
           materialized={41: MaterializedRealization(41, content())})


# 20
def test_blank_and_zero_remain_distinct():
    blank = content(value=None, state='missing', evidence=[], deviation=dict(fields()['deviation'], delta=None))
    empty = content(value='', state='missing', evidence=[], deviation=dict(fields()['deviation'], delta=None))
    zero = content(value='0', state='needs_review', evidence=[], deviation=dict(fields()['deviation'], delta=None))
    assert blank.value is None and empty == blank and zero.value == '0'
    assert blank.sha256 != content(value='0', state='verified', deviation=dict(fields()['deviation'], delta='-100')).sha256
    expect('missing_with_value', content, value='0', state='missing', evidence=[],
           deviation=dict(fields()['deviation'], delta=None))
    expect('verified_without_value', content, value=None, deviation=dict(fields()['deviation'], delta=None))
    expect('verified_without_value', content, value='', deviation=dict(fields()['deviation'], delta=None))
    src = source(cnt=zero)
    proposed_blank = content(value=None, state='needs_review', evidence=[], deviation=dict(fields()['deviation'], delta=None))
    assert 'value_changed' in codes(check_reference_eligibility(src, successor_context(), proposed_blank))


# 21
def test_decimal_values_remain_exact():
    assert canonical_decimal('0.000001') == '0.000001'
    assert canonical_decimal('12.500000') == canonical_decimal(Decimal('12.500000')) == canonical_decimal('12.5') == '12.5'
    assert canonical_decimal('9999999999999999999.999999') == '9999999999999999999.999999'
    assert canonical_decimal('12.500') == '12.5'
    assert canonical_decimal('-0.000000') == canonical_decimal('0') == '0'
    assert canonical_decimal('100') == canonical_decimal(Decimal('1E+2')) == '100'
    for bad in (2.1, True, 1, '1.1234567', '1e5', 'NaN', '12,5', '12.500,5', ' 1', '100000000000000000000',
                Decimal('NaN'), Decimal('Infinity'), Decimal('0.0000001')):
        expect('invalid_decimal', canonical_decimal, bad)
    # 0.1 + 0.2 style float drift can never enter: floats are rejected outright, even in free-form content.
    expect('float_not_allowed', content, deviation=dict(fields()['deviation'], extra=0.5))
    value = content(value='0.300001', deviation=dict(fields()['deviation'], delta='-99.699999'))
    assert value.decimal_value == Decimal('0.300001')


def test_decimal_parsing_parity_with_parse_actual():
    from fastapi import HTTPException
    from app.activity_contract_service import parse_actual
    for text in ('', '0', '-0', '1', '+1', '12.5', '12.500000', '0.000001', '1.1234567', '1e3', '12,5', 'abc',
                 '99999999999999999999', '100000000000000000000', ' 1', '1.', '.5'):
        try:
            expected = parse_actual(text)
        except HTTPException:
            expected = 'reject'
        try:
            actual = canonical_decimal(text)
            actual = None if actual is None else Decimal(actual)
        except ActivityReferenceError:
            actual = 'reject'
        assert actual == expected, text


# 22
def test_evidence_mutation_changes_canonical_hash_and_inputs_are_copied():
    data = fields()
    original = content_from_fields(**data)
    before = original.sha256
    data['evidence'][0]['locator'] = 'Sayfa 4'
    assert original.sha256 == before and original.evidence == EVIDENCE  # no aliasing of caller data
    mutated = content_from_fields(**data)
    assert mutated.sha256 != before
    assert 'evidence_changed' in codes(check_reference_eligibility(source(), successor_context(), mutated))
    original.evidence[0]['locator'] = 'X'
    assert original.sha256 == before


# 23
def test_deterministic_canonical_serialization():
    payload = {'b': [3, {'z': 'ş', 'a': None}], 'a': Decimal('1.50')}
    assert canonical_json(payload) == '{"a":"1.50","b":[3,{"a":null,"z":"ş"}]}'
    for sample in ({'name': 'Gösterge', 'targets': [{'value': '1.750000', 'state': 'verified'}], 'year': 2027},
                   EVIDENCE, fields()['deviation']):
        assert canonical_json(sample) == contract_canonical(sample)  # byte parity with repository canonical()
    reordered = content(deviation=dict(reversed(list(fields()['deviation'].items()))),
                        evidence=[dict(reversed(list(e.items()))) for e in EVIDENCE])
    assert reordered.canonical_json() == content().canonical_json()
    assert content().canonical_json() == content().canonical_json()


# 24
def test_deterministic_reference_hash():
    first = build_reference(source(), successor_context(), content())
    second = build_reference(source(), successor_context(), content())
    assert first == second and first.reference_sha256 == ref.sha256_hex(first.provenance_json)
    other = build_reference(source(prov=provenance(actual_revision_id=82)), successor_context(), content())
    assert other.reference_sha256 != first.reference_sha256
    reloaded = UnchangedValueReference(first.provenance_json, first.reference_sha256)
    verify_reference(reloaded, source=source(), successor=successor_context())


# 25
def test_order_sensitive_content_follows_civensa_semantics():
    # Evidence list order is stored as entered and compared exactly (verify_materialization uses list equality).
    swapped = content(evidence=list(reversed(EVIDENCE)))
    assert swapped.sha256 != content().sha256
    assert 'evidence_changed' in codes(check_reference_eligibility(source(), successor_context(), swapped))
    # Object key order is not significant (canonical JSON sorts keys).
    keys = content(evidence=[dict(reversed(list(e.items()))) for e in EVIDENCE])
    assert keys.sha256 == content().sha256
    # Equal Decimal values in different scales are one realization ('12.5' vs Numeric(26, 6) '12.500000').
    scaled = content(value='112.500000', deviation=dict(fields()['deviation'], delta='12.500000'))
    assert scaled == content() and check_reference_eligibility(source(), successor_context(), scaled).eligible


# 26
@pytest.mark.parametrize('section,key', [('source', 'actual_revision_id'), ('source', 'candidate_sha256'),
    ('source', 'release_id'), ('successor', 'report_indicator_id'), ('binding', 'definition_sha256'),
    ('binding', 'persistent_indicator_id'), ('binding', 'publication_sha256'), (None, 'content_sha256'),
    ('source', 'reporting_period_id'), ('successor', 'reporting_period_id'), ('binding', 'reporting_year')])
def test_incomplete_reference_provenance_fails_closed(section, key):
    payload = build_reference(source(), successor_context(), content()).payload
    (payload[section] if section else payload).pop(key)
    text = canonical_json(payload)
    expect('incomplete_provenance', UnchangedValueReference, text, ref.sha256_hex(text))


@pytest.mark.parametrize('changes', [dict(actual_revision_id=None), dict(release_id=0), dict(candidate_sha256='x'),
                                     dict(activity_approval_id=True), dict(release_minor=-1)])
def test_incomplete_source_provenance_fails_closed(changes):
    expect('incomplete_provenance', provenance, **changes)


def test_extra_or_null_reference_fields_fail_closed():
    payload = build_reference(source(), successor_context(), content()).payload
    payload['source']['latest_actual_revision_id'] = 1
    text = canonical_json(payload)
    expect('incomplete_provenance', UnchangedValueReference, text, ref.sha256_hex(text))
    payload = build_reference(source(), successor_context(), content()).payload
    payload['binding']['definition_revision_id'] = None
    text = canonical_json(payload)
    expect('incomplete_provenance', UnchangedValueReference, text, ref.sha256_hex(text))
    expect('reference_not_canonical', UnchangedValueReference, json.dumps(build_reference(
        source(), successor_context(), content()).payload), 'a' * 64)


# Repository-contract cases.
def test_context_rejects_definition_integrity_failures():
    expect('definition_integrity', context, definition_sha256='d' * 64)
    expect('definition_integrity', context, definition(definition_contract_version='2.0'))
    v1 = contract_canonical({k: v for k, v in json.loads(definition()).items() if k != 'definition_contract_version'})
    assert context(v1, contract_version='1.0').effective_target == Decimal('100')
    expect('definition_integrity', context, v1)
    float_target = contract_canonical(dict(json.loads(definition()), targets=[
        {'year': 2027, 'value_kind': 'target', 'value': 100.0, 'raw_text': '100', 'state': 'verified'}]))
    expect('invalid_decimal', context, float_target)


def test_unverified_or_ambiguous_target_has_no_delta():
    targets = [{'year': 2027, 'value_kind': 'target', 'value': None, 'raw_text': '', 'state': 'missing'}]
    ctx = successor_context(definition(targets=targets))
    assert ctx.effective_target is None
    resolve_effective_realization(ctx, materialized=MaterializedRealization(41, content(
        deviation=dict(fields()['deviation'], delta=None))))
    expect('deviation_mismatch', resolve_effective_realization, ctx, materialized=MaterializedRealization(41, content()))
    expect('invalid_deviation', content, state='needs_review')  # unverified value must carry no delta


def test_source_must_match_released_candidate_entry():
    src = source()
    entry = dict(fields(), report_indicator_id=31, definition_revision_id=11, materialized_report_indicator_id=31,
                 materialized_actual_revision_id=81)
    verify_source_against_candidate_entry(src, entry)
    expect('source_provenance_mismatch', verify_source_against_candidate_entry, src,
           dict(entry, materialized_actual_revision_id=80))
    expect('source_content_mismatch', verify_source_against_candidate_entry, src, dict(entry, explanation='Başka'))


def test_real_actual_revision_matches_package_copy(db, sample):
    """Real repository rows: an unchanged package copy (Numeric(26, 6) text, recomputed delta) equals its source."""
    _real_rows_case(db, sample)


@pytest.mark.postgres
def test_real_actual_revision_matches_package_copy_postgres(db, sample):
    _real_rows_case(db, sample)


def _real_rows_case(db, sample):
    from fastapi.testclient import TestClient
    from sqlalchemy import select
    from app.main import app, require_user
    from app.db import get_db
    from app.models import (ActivityReport, ActivityReportRevision, ActualRevision, IndicatorDefinitionRevision,
        IndicatorIdentity, PublicationIndicatorBinding, ReportIndicator)
    from app import activity_contract_service as service
    from app.package_service import validate_actual
    from tests.test_activity_contract import publish, new_report

    def database():
        yield db
    app.dependency_overrides[get_db] = database
    app.dependency_overrides[require_user] = lambda: sample['user']
    client = TestClient(app)
    try:
        pub = publish(client, db, sample)
        report = new_report(client, pub, sample)
    finally:
        client.close(); app.dependency_overrides.clear()
    item = db.get(ReportIndicator, report['indicators'][0]['report_indicator_id'])
    stored = service.save_actual(db, sample['user'], item.id, 0, '2.75', 'verified', EVIDENCE, 'Arttı.', {'note': 'İzle'})
    db.flush(); db.expire_all()
    stored = db.get(ActualRevision, stored.id)
    assert Decimal(json.loads(stored.deviation_json)['delta']) == Decimal('1')
    data = service.report_data(db, sample['strategy'], item.report_revision_id)['indicators'][0]
    latest = data['actuals'][-1]
    entry = {'definition_revision_id': data['definition_revision_id'], 'definition': data['definition'],
             'value': latest['value'], 'state': latest['state'], 'evidence': latest['evidence'],
             'explanation': latest['explanation'], 'deviation': latest['deviation']}
    validate_actual(entry)  # exactly what create_package does to an unchanged copy
    assert entry['value'] != '2.75' and Decimal(entry['value']) == Decimal('2.75')  # stored scale differs from typed text
    assert content_from_entry(entry) == content_from_actual_revision(stored)

    revision = db.get(ActivityReportRevision, item.report_revision_id)
    binding = db.get(PublicationIndicatorBinding, item.publication_binding_id)
    definition_row = db.get(IndicatorDefinitionRevision, binding.definition_revision_id)
    activity = db.get(ActivityReport, revision.report_id)
    assert db.get(IndicatorIdentity, definition_row.indicator_id).organization_id == activity.organization_id
    real = IndicatorContext(organization_id=activity.organization_id, activity_report_id=activity.id,
        reporting_period_id=activity.period_id,
        report_revision_id=revision.id, report_revision_number=revision.revision, report_indicator_id=item.id,
        persistent_indicator_id=definition_row.indicator_id, definition_revision_id=definition_row.id,
        definition_sha256=definition_row.sha256, definition_json=definition_row.definition_json,
        publication_id=revision.publication_id, publication_sha256=revision.publication_sha256,
        contract_version=revision.contract_version)
    assert real.effective_target == Decimal('1.75')
    real_source = SourceRealization(real, provenance(actual_revision_id=stored.id), content_from_actual_revision(stored))
    successor = replace(real, report_revision_id=revision.id + 1000, report_revision_number=revision.revision + 1,
                        report_indicator_id=item.id + 1000)
    reference = build_reference(real_source, successor, content_from_entry(entry))
    resolved = resolve_effective_realization(successor, reference=reference, source=real_source)
    assert resolved.value == Decimal('2.75') and resolved.actual_revision_id == stored.id
    assert db.scalar(select(ActualRevision.id).where(ActualRevision.id != stored.id)) is None  # no writes by engine
