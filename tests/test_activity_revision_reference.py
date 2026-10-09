"""Phase 5B1 unchanged-value reference / resolution engine v2 (pure helpers, no DB writes)."""
import ast
import inspect
import json
from dataclasses import replace
from decimal import Decimal, Inexact, ROUND_DOWN, localcontext
from pathlib import Path

import pytest

from app import activity_revision_reference as ref
from app.activity_revision_reference import (ActivityReferenceError, CandidateSnapshot, IndicatorContext,
    MaterializedRealization, ReleaseRecord, ReleasedIndicator, SuccessorTarget, UnchangedValueReference,
    build_reference, canonical_decimal, canonical_json, check_reference_eligibility, content_from_actual_revision,
    content_from_entry, content_from_fields, resolve_effective_realization, resolve_successor_realizations,
    verify_reference)
from app.activity_contract_service import canonical as contract_canonical, digest as contract_digest
from app.report_workflow_service import hash_content

SHA_PUB = 'a' * 64
IDENTITY = '6f1c2b8e-0d5a-4c1e-9a7b-1f2e3d4c5b6a'
EVIDENCE = [{'title': 'Kayıt defteri', 'locator': 'Sayfa 3', 'source_revision': '2027-12 kayıt 4'},
            {'title': 'Sistem raporu', 'locator': 'Tablo 2', 'source_revision': 'v7'}]
V1, V2 = ref.CANDIDATE_SCHEMA_V1, ref.CANDIDATE_SCHEMA_V2
# Report revision n is released as v1.(n-1).
REVS = {n: dict(report_revision_id=20 + n, report_revision_number=n, report_indicator_id=21 + 10 * n) for n in (1, 2, 3, 4)}
RELEASES = {n: dict(release_id=69 + n, release_minor=n - 1, candidate_id=59 + n, activity_approval_id=49 + n,
                    actual_revision_id=80 + n) for n in (1, 2, 3)}


def definition(**changes):
    data = {'name': 'Hizmet sayısı', 'code': 'G-1', 'unit': 'Adet', 'explanation': 'Ortak açıklama',
            'calculation_method': 'Kaynak yöntemi', 'data_source': 'Kaynak kayıt', 'card_id': 3,
            'subprogram_id': 2, 'department_id': 7, 'year': 2027, 'definition_contract_version': '3.0',
            'targets': [{'year': 2027, 'value_kind': 'target', 'value': '100.000000', 'raw_text': '100',
                         'state': 'verified'}]}
    data.update(changes)
    return contract_canonical(data)


def ctx(rev=1, definition_json=None, **changes):
    text = definition_json or definition()
    data = dict(organization_id=1, activity_report_id=5, reporting_period_id=3, persistent_indicator_id=IDENTITY,
                identity_organization_id=1, definition_revision_id=11, definition_sha256=contract_digest(text),
                definition_json=text, publication_id=9, publication_sha256=SHA_PUB, contract_version='3.0', **REVS[rev])
    data.update(changes)
    return IndicatorContext(**data)


def fields(x=None, **changes):
    """Default content: value 112.5 against target 100. fields(x) gives value 100+x with delta x."""
    data = dict(value='112.5', state='verified', evidence=[dict(e) for e in EVIDENCE], explanation='Hedef aşıldı.',
                deviation={'corrective_action': 'İzle', 'calculation_rule_version': 'difference-v1',
                           'target_definition_revision_id': 11, 'delta': '12.5', 'achievement_percent': None})
    if x is not None:
        data['value'] = str(100 + x)
        data['deviation'] = dict(data['deviation'], delta=str(x))
    data.update(changes)
    return data


def content(x=None, **changes):
    return content_from_fields(**fields(x, **changes))


def package_entry(data):
    # Package fields as copied by create_package; report_indicator_id / source_actual_revision_id are the
    # draft revision's (stale) ids and must never be used as a reference source.
    return dict(data, report_indicator_id=999, definition_revision_id=11, definition=json.loads(definition()),
                source_actual_revision_id=999)


def v1_entry(rev, data):
    return dict(package_entry(data), materialized_report_indicator_id=REVS[rev]['report_indicator_id'],
                materialized_actual_revision_id=RELEASES[rev]['actual_revision_id'])


def v2_materialized_entry(rev, data):
    return dict(package_entry(data), successor_report_indicator_id=REVS[rev]['report_indicator_id'],
                realization={'mode': 'materialized', 'actual_revision_id': RELEASES[rev]['actual_revision_id'],
                             'content_sha256': content_from_fields(**data).sha256})


def v2_reference_entry(rev, data, reference):
    stored = reference.payload
    return dict(package_entry(data), successor_report_indicator_id=REVS[rev]['report_indicator_id'],
                realization={'mode': 'reference', 'reference_sha256': reference.reference_sha256,
                             'source_release_id': stored['source']['release_id'],
                             'source_actual_revision_id': stored['source']['actual_revision_id'],
                             'predecessor_release_id': stored['predecessor']['release_id'],
                             'content_sha256': content_from_fields(**data).sha256})


def candidate(rev, entries, schema=V1, predecessor=None, payload_changes=None, manifest_changes=None, **changes):
    payload = {'schema_version': schema, 'report_revision_id': REVS[rev]['report_revision_id'], 'publication_id': 9,
               'publication_sha256': SHA_PUB, 'contract_version': '3.0', 'entries': entries}
    if schema == V2:
        payload.update(predecessor_release_id=predecessor.release.release_id if predecessor else None,
                       predecessor_candidate_id=predecessor.candidate.candidate_id if predecessor else None,
                       predecessor_candidate_sha256=predecessor.candidate.sha256 if predecessor else None)
    payload.update(payload_changes or {})
    manifest = {'version': 'report-manifest-1', 'organization_id': 1, 'period_id': 3, 'resource_scope': 'activity_report',
                'source_id': 20 + rev, 'required_department_ids': [7], 'packages': []}
    manifest.update(manifest_changes or {})
    raw, mraw = contract_canonical(payload), contract_canonical(manifest)
    data = dict(candidate_id=RELEASES[rev]['candidate_id'], organization_id=1, period_id=3, resource_scope='activity_report',
                report_key='5', activity_revision_id=REVS[rev]['report_revision_id'], payload_json=raw,
                payload_sha256=contract_digest(raw), manifest_json=mraw, sha256=hash_content(raw, mraw))
    data.update(changes)
    return CandidateSnapshot(**data)


def release(rev, **changes):
    data = dict(release_id=RELEASES[rev]['release_id'], organization_id=1, resource_scope='activity_report', report_key='5',
                release_major=1, release_minor=RELEASES[rev]['release_minor'], candidate_id=RELEASES[rev]['candidate_id'],
                activity_approval_id=RELEASES[rev]['activity_approval_id'],
                approval_report_revision_id=REVS[rev]['report_revision_id'])
    data.update(changes)
    return ReleaseRecord(**data)


def target(rev, predecessor=None, context=None, **changes):
    data = {}
    if predecessor is not None:
        data = dict(predecessor_release_id=predecessor.release.release_id,
                    predecessor_candidate_id=predecessor.candidate.candidate_id,
                    predecessor_candidate_sha256=predecessor.candidate.sha256)
    data.update(changes)
    return SuccessorTarget(context or ctx(rev), **data)


def v10(x=None, **changes):
    """v1.0: first release, legacy activity-candidate-1 payload, materialized."""
    data = fields(x, **changes)
    return ReleasedIndicator(ctx(1), release(1), candidate(1, [v1_entry(1, data)]), content_from_fields(**data))


def v11_materialized(x=None, predecessor=None):
    data = fields(x)
    predecessor = predecessor or v10()
    return ReleasedIndicator(ctx(2), release(2), candidate(2, [v2_materialized_entry(2, data)], V2, predecessor),
                             content_from_fields(**data))


def v11_reference():
    """v1.1 kept v1.0's value through a reference R1."""
    first = v10()
    r1 = build_reference(target(2, first), first, first, content())
    released = ReleasedIndicator(ctx(2), release(2), candidate(2, [v2_reference_entry(2, fields(), r1)], V2, first),
                                 content(), reference=r1)
    return released, r1


def codes(result):
    return {m.code for m in result.mismatches}


def expect(code, call, *args, **kwargs):
    with pytest.raises(ActivityReferenceError) as exc:
        call(*args, **kwargs)
    assert exc.value.code == code, (exc.value.code, exc.value.message)
    return exc.value


def rehashed(reference, mutate):
    payload = reference.payload
    mutate(payload)
    text = canonical_json(payload)
    return UnchangedValueReference(text, ref.sha256_hex(text))


# A. immediate predecessor
def test_a_immediate_predecessor_success():
    first = v10()
    successor = target(2, first)
    reference = build_reference(successor, first, first, content())
    stored = reference.payload
    assert stored['schema'] == 'civensa.activity-unchanged-value-reference/v2'
    assert stored['predecessor']['release_id'] == 70 and stored['predecessor']['entry_mode'] == 'materialized'
    assert stored['predecessor']['predecessor_reference_sha256'] is None
    assert stored['predecessor']['materialized_actual_revision_id'] == 81
    assert stored['source']['release_id'] == 70 and stored['source']['actual_revision_id'] == 81
    assert stored['binding']['reporting_period_id'] == 3 and stored['binding']['reporting_year'] == 2027
    result = resolve_effective_realization(successor, reference=reference, predecessor=first, source=first)
    assert result.mode == ref.MODE_REFERENCE and result.actual_revision_id == 81
    assert result.source_release_id == 70 and result.predecessor_release_id == 70 and result.value == Decimal('112.5')


# B. skip-over: v1.0 X=5 -> v1.1 X=6 -> v1.2 X=5 must not reference v1.0
def test_b_skip_over_rejected():
    first = v10(5)
    second = v11_materialized(6, predecessor=first)
    successor = target(3, second)  # lineage: v1.2's immediate predecessor is v1.1
    proposed = content(5)
    skip = check_reference_eligibility(successor, first, first, proposed)
    assert not skip.eligible and 'predecessor_mismatch' in codes(skip)
    expect('predecessor_mismatch', build_reference, successor, first, first, proposed)
    flattened_to_old = check_reference_eligibility(successor, second, first, proposed)
    assert {'lineage_mismatch', 'value_changed'} <= codes(flattened_to_old)
    against_immediate = check_reference_eligibility(successor, second, second, proposed)
    assert codes(against_immediate) == {'value_changed', 'deviation_changed'}
    # A reference forged while pretending v1.0 was the predecessor cannot be resolved under the real lineage.
    forged = build_reference(target(3, first), first, first, proposed)
    expect('predecessor_mismatch', resolve_effective_realization, successor, reference=forged, predecessor=first, source=first)
    # The only valid outcome is a new materialized realization.
    assert resolve_effective_realization(successor, materialized=MaterializedRealization(51, proposed)).mode == 'materialized'


def test_b_rematerialized_equal_value_cannot_flatten_past_predecessor():
    # v1.1 re-entered the same value as a NEW ActualRevision; v1.2 may only reference v1.1's row, not v1.0's.
    first = v10(5)
    second = v11_materialized(5, predecessor=first)
    successor = target(3, second)
    result = check_reference_eligibility(successor, second, first, content(5))
    assert codes(result) == {'lineage_mismatch'}
    reference = build_reference(successor, second, second, content(5))
    assert reference.payload['source']['release_id'] == 71 and reference.payload['source']['actual_revision_id'] == 82


# C. predecessor-is-reference chain stays flattened to the v1.0 ActualRevision
def test_c_predecessor_reference_chain_flattens_to_materialized_source():
    first = v10()
    second, r1 = v11_reference()
    assert second.mode == 'reference' and second.flattened_source() == first.flattened_source()
    successor = target(3, second)
    r2 = build_reference(successor, second, first, content())
    stored = r2.payload
    assert stored['source']['release_id'] == 70 and stored['source']['actual_revision_id'] == 81
    assert stored['predecessor']['release_id'] == 71 and stored['predecessor']['entry_mode'] == 'reference'
    assert stored['predecessor']['predecessor_reference_sha256'] == r1.reference_sha256
    assert stored['predecessor']['materialized_actual_revision_id'] is None
    result = resolve_effective_realization(successor, reference=r2, predecessor=second, source=first)
    assert (result.actual_revision_id, result.source_release_id, result.predecessor_release_id) == (81, 70, 71)
    assert result.content_sha256 == first.content.sha256
    # The source must be the terminal materialized row, not the intermediate reference.
    expect('source_not_materialized', build_reference, successor, second, second, content())


def test_c_release_must_be_newer_than_its_references_predecessor():
    first = v10()
    _, r1 = v11_reference()
    expect('predecessor_reference_mismatch', ReleasedIndicator, ctx(2), release(2, release_minor=0),
           candidate(2, [v2_reference_entry(2, fields(), r1)], V2, first), content(), reference=r1)


# D. wrong predecessor release
def test_d_wrong_predecessor_release_rejected():
    first = v10()
    second, _ = v11_reference()
    r2 = build_reference(target(3, second), second, first, content())
    expect('predecessor_mismatch', build_reference, target(3, second, predecessor_release_id=79), second, first, content())
    expect('predecessor_mismatch', verify_reference, r2, successor=target(3, second, predecessor_release_id=79),
           predecessor=second, source=first)
    # A later release appears: the old reference cannot silently move forward to a successor whose predecessor is newer.
    later = ReleasedIndicator(ctx(3), release(3), candidate(3, [v2_materialized_entry(3, fields())], V2, second), content())
    expect('predecessor_mismatch', resolve_effective_realization, target(4, later), reference=r2, predecessor=second, source=first)
    tampered = rehashed(r2, lambda p: p['predecessor'].update(release_id=79))
    expect('predecessor_mismatch', verify_reference, tampered, successor=target(3, second), predecessor=second, source=first)


# E. wrong predecessor candidate / candidate hash
def test_e_wrong_predecessor_candidate_rejected():
    first = v10()
    expect('predecessor_mismatch', build_reference, target(2, first, predecessor_candidate_id=68), first, first, content())
    expect('predecessor_mismatch', build_reference, target(2, first, predecessor_candidate_sha256='c' * 64),
           first, first, content())
    good = candidate(1, [v1_entry(1, fields())])
    payload = json.loads(good.payload_json)
    payload['entries'][0]['materialized_actual_revision_id'] = 99
    raw = contract_canonical(payload)
    expect('candidate_integrity', replace, good, payload_json=raw)  # payload changed, payload hash kept
    expect('candidate_integrity', replace, good, payload_json=raw, payload_sha256=contract_digest(raw))  # candidate hash kept
    expect('candidate_integrity', replace, good, sha256='d' * 64)


# F. wrong predecessor reference hash
def test_f_wrong_predecessor_reference_hash_rejected():
    first = v10()
    second, r1 = v11_reference()
    other = build_reference(target(2, first, context=ctx(2, report_indicator_id=42)), first, first, content())
    bad_entry = v2_reference_entry(2, fields(), r1)
    bad_entry['realization']['reference_sha256'] = 'e' * 64
    expect('predecessor_reference_mismatch', ReleasedIndicator, ctx(2), release(2),
           candidate(2, [bad_entry], V2, first), content(), reference=r1)
    expect('predecessor_reference_mismatch', ReleasedIndicator, ctx(2), release(2),
           candidate(2, [v2_reference_entry(2, fields(), r1)], V2, first), content(), reference=other)
    r2 = build_reference(target(3, second), second, first, content())
    tampered = rehashed(r2, lambda p: p['predecessor'].update(predecessor_reference_sha256='e' * 64))
    expect('predecessor_mismatch', verify_reference, tampered, successor=target(3, second), predecessor=second, source=first)


# G. fabricated source provenance (detectable without DB)
def test_g_fabricated_source_provenance_rejected():
    data = fields()
    good = candidate(1, [v1_entry(1, data)])
    expect('release_provenance_mismatch', ReleasedIndicator, ctx(1), release(1, candidate_id=68), good, content())
    expect('release_provenance_mismatch', ReleasedIndicator, ctx(1), release(1, approval_report_revision_id=29), good, content())
    expect('release_provenance_mismatch', ReleasedIndicator, ctx(1), release(1, report_key='6'), good, content())
    expect('release_provenance_mismatch', ReleasedIndicator, ctx(1), release(1, organization_id=2), good, content())
    expect('release_provenance_mismatch', candidate, 1, [v1_entry(1, data)], manifest_changes={'period_id': 4})
    expect('release_provenance_mismatch', candidate, 1, [v1_entry(1, data)], manifest_changes={'resource_scope': 'performance_program'})
    expect('release_provenance_mismatch', release, 1, resource_scope='performance_program')
    expect('release_provenance_mismatch', ReleasedIndicator, ctx(1, report_indicator_id=32), release(1), good, content())
    expect('release_provenance_mismatch', ReleasedIndicator, ctx(1), release(1),
           candidate(1, [v1_entry(1, data), v1_entry(1, data)]), content())  # duplicated key is ambiguous
    expect('release_provenance_mismatch', ReleasedIndicator, ctx(1), release(1),
           candidate(1, [v1_entry(1, data)], payload_changes={'publication_sha256': 'c' * 64}), content())
    expect('source_content_mismatch', ReleasedIndicator, ctx(1), release(1), good, content(explanation='Başka'))
    # Mode and actual id come from the hashed payload, not from the caller.
    second, r1 = v11_reference()
    expect('ambiguous_realization', ReleasedIndicator, ctx(1), release(1), good, content(), reference=r1)
    expect('reference_missing', ReleasedIndicator, ctx(2), release(2), second.candidate, content())
    assert v10().flattened_source()['actual_revision_id'] == 81


# H-J. cross-period / cross-org / cross-report
@pytest.mark.parametrize('changes,code', [
    (dict(reporting_period_id=4), 'reporting_period_mismatch'),
    (dict(definition_json=definition(year=2028)), 'reporting_period_mismatch'),
    (dict(organization_id=2, identity_organization_id=2), 'organization_mismatch'),
    (dict(activity_report_id=6), 'report_mismatch'),
])
def test_h_i_j_cross_scope_rejected(changes, code):
    first = v10()
    successor = target(2, first, context=ctx(2, **changes))
    result = check_reference_eligibility(successor, first, first, content())
    assert not result.eligible and code in codes(result)
    expect(code, build_reference, successor, first, first, content())


def test_h_cross_period_injection_rejected():
    first = v10()
    reference = build_reference(target(2, first), first, first, content())
    for section, code in (('successor', 'incomplete_provenance'), ('binding', 'incomplete_provenance')):
        # successor/binding period disagree -> internal invariant
        expect(code, rehashed, reference, lambda p, s=section: p[s].update(reporting_period_id=4))
    both = rehashed(reference, lambda p: (p['successor'].update(reporting_period_id=4), p['binding'].update(reporting_period_id=4)))
    expect('successor_mismatch', verify_reference, both, successor=target(2, first), predecessor=first, source=first)
    year = rehashed(reference, lambda p: p['binding'].update(reporting_year=2028))
    expect('binding_mismatch', verify_reference, year, successor=target(2, first), predecessor=first, source=first)
    expect('release_provenance_mismatch', ReleasedIndicator, ctx(1, reporting_period_id=4), release(1),
           candidate(1, [v1_entry(1, fields())]), content())


def test_i_identity_must_belong_to_the_organization():
    expect('identity_organization_mismatch', ctx, 1, identity_organization_id=2)


# Changed content and other binding changes
@pytest.mark.parametrize('changes,code', [
    (dict(value='112.6', deviation=dict(fields()['deviation'], delta='12.6')), 'value_changed'),
    (dict(state='needs_review', deviation=dict(fields()['deviation'], delta=None)), 'state_changed'),
    (dict(evidence=EVIDENCE[:1]), 'evidence_changed'),
    (dict(explanation='Hedef aşıldı. '), 'explanation_changed'),
    (dict(deviation=dict(fields()['deviation'], corrective_action='Düzelt')), 'deviation_changed'),
])
def test_changed_content_rejected(changes, code):
    first = v10()
    result = check_reference_eligibility(target(2, first), first, first, content(**changes))
    assert not result.eligible and code in codes(result)
    expect(code, build_reference, target(2, first), first, first, content(**changes))


@pytest.mark.parametrize('changes,code', [
    (dict(definition_revision_id=12), 'definition_revision_mismatch'),
    (dict(definition_json=definition(name='Yeni ad')), 'definition_hash_mismatch'),
    (dict(persistent_indicator_id='other-identity'), 'identity_mismatch'),
    (dict(publication_id=10), 'program_base_mismatch'),
    (dict(publication_sha256='c' * 64), 'program_base_mismatch'),
    (dict(definition_json=definition(definition_contract_version='2.0'), contract_version='2.0'), 'program_base_mismatch'),
    (dict(definition_json=definition(targets=[{'year': 2027, 'value_kind': 'target', 'value': '101', 'raw_text': '101',
                                               'state': 'verified'}])), 'target_mismatch'),
    (dict(report_revision_number=1), 'not_a_successor'),
    (dict(report_indicator_id=31), 'not_a_successor'),
])
def test_binding_changes_rejected(changes, code):
    first = v10()
    result = check_reference_eligibility(target(2, first, context=ctx(2, **changes)), first, first, content())
    assert not result.eligible and code in codes(result)


def test_target_raw_text_is_not_target_semantics():
    targets = [{'year': 2027, 'value_kind': 'target', 'value': '100', 'raw_text': '100,0', 'state': 'verified'}]
    assert ctx(2, definition(targets=targets)).target_semantics_sha256 == ctx(1).target_semantics_sha256


def test_first_release_target_cannot_reference():
    first = v10()
    expect('predecessor_missing', build_reference, target(2), first, first, content())


# K. Unicode digits
@pytest.mark.parametrize('text', ['١٢', '１２', '12.５', '٣.٥', '۱۲', '१२', '12 ', '١'])
def test_k_unicode_digits_rejected(text):
    expect('invalid_decimal', canonical_decimal, text)
    expect('invalid_decimal', content, value=text)


def test_k_unicode_digits_rejected_in_targets_and_delta():
    expect('invalid_decimal', ctx, 1, definition(targets=[{'year': 2027, 'value_kind': 'target', 'value': '１００',
                                                          'raw_text': '100', 'state': 'verified'}]))
    expect('invalid_decimal', content, deviation=dict(fields()['deviation'], delta='١٢.٥'))


# L. ambient Decimal context
def test_l_ambient_decimal_context_cannot_change_results():
    baseline = (canonical_decimal('9999999999999999999.999999'), canonical_decimal(Decimal('12.500000')), content().sha256,
                build_reference(target(2, v10()), v10(), v10(), content()).reference_sha256)
    big = dict(value='9999999999999999999.999999',
               deviation=dict(fields()['deviation'], delta='9999999999999999899.999999'))
    for prec, rounding in ((3, ROUND_DOWN), (1, ROUND_DOWN), (28, ROUND_DOWN)):
        with localcontext() as ambient:
            ambient.prec, ambient.rounding = prec, rounding
            ambient.traps[Inexact] = True  # any implicit inexact arithmetic would raise here
            assert (canonical_decimal('9999999999999999999.999999'), canonical_decimal(Decimal('12.500000')), content().sha256,
                    build_reference(target(2, v10()), v10(), v10(), content()).reference_sha256) == baseline
            assert content(**big).value == '9999999999999999999.999999'  # delta check runs in the local context


# M. blank vs zero
def test_m_blank_and_zero_remain_distinct():
    blank = content(value=None, state='missing', evidence=[], deviation=dict(fields()['deviation'], delta=None))
    empty = content(value='', state='missing', evidence=[], deviation=dict(fields()['deviation'], delta=None))
    zero = content(value='0', state='needs_review', evidence=[], deviation=dict(fields()['deviation'], delta=None))
    assert blank.value is None and empty == blank and zero.value == '0' and blank.sha256 != zero.sha256
    expect('missing_with_value', content, value='0', state='missing', evidence=[], deviation=dict(fields()['deviation'], delta=None))
    expect('verified_without_value', content, value=None, deviation=dict(fields()['deviation'], delta=None))
    expect('verified_without_value', content, value='', deviation=dict(fields()['deviation'], delta=None))
    zero_fields = dict(value='0', state='needs_review', evidence=[], deviation=dict(fields()['deviation'], delta=None))
    first = ReleasedIndicator(ctx(1), release(1), candidate(1, [v1_entry(1, fields(**zero_fields))]), content(**zero_fields))
    proposed_blank = content(value=None, state='needs_review', evidence=[], deviation=dict(fields()['deviation'], delta=None))
    assert 'value_changed' in codes(check_reference_eligibility(target(2, first), first, first, proposed_blank))


# N. both / neither
def test_n_both_and_neither_rejected():
    first = v10()
    successor = target(2, first)
    reference = build_reference(successor, first, first, content())
    new = MaterializedRealization(41, content())
    expect('ambiguous_realization', resolve_effective_realization, successor, materialized=new, reference=reference,
           predecessor=first, source=first)
    expect('ambiguous_realization', resolve_effective_realization, successor, materialized=new, predecessor=first)
    expect('missing_realization', resolve_effective_realization, successor)
    expect('reference_missing', resolve_effective_realization, successor, predecessor=first, source=first)
    expect('reference_source_missing', resolve_effective_realization, successor, reference=reference)
    expect('reference_source_missing', resolve_effective_realization, successor, reference=reference, predecessor=first)


# O. canonical reference hash tamper
def test_o_reference_hash_tamper_rejected():
    first = v10()
    reference = build_reference(target(2, first), first, first, content())
    expect('reference_hash_invalid', UnchangedValueReference, reference.provenance_json, 'f' * 64)
    payload = reference.payload
    payload['successor']['report_indicator_id'] = 42
    expect('reference_hash_invalid', UnchangedValueReference, canonical_json(payload), reference.reference_sha256)
    expect('reference_not_canonical', UnchangedValueReference, json.dumps(reference.payload), 'a' * 64)
    altered = UnchangedValueReference(reference.provenance_json, reference.reference_sha256)
    object.__setattr__(altered, 'reference_sha256', 'e' * 64)
    expect('reference_hash_invalid', verify_reference, altered, successor=target(2, first), predecessor=first, source=first)
    # Consistently re-hashed forgery: materialized predecessor must equal the source -> structural failure.
    expect('incomplete_provenance', rehashed, reference, lambda p: p['source'].update(actual_revision_id=82))


@pytest.mark.parametrize('section,key', [('source', 'actual_revision_id'), ('source', 'candidate_sha256'),
    ('predecessor', 'release_id'), ('predecessor', 'entry_mode'), ('predecessor', 'predecessor_reference_sha256'),
    ('predecessor', 'materialized_actual_revision_id'),
    ('successor', 'report_indicator_id'), ('binding', 'definition_sha256'), ('binding', 'reporting_period_id'),
    ('binding', 'reporting_year'), ('binding', 'persistent_indicator_id'), (None, 'content_sha256')])
def test_incomplete_reference_provenance_fails_closed(section, key):
    first = v10()
    reference = build_reference(target(2, first), first, first, content())
    expect('incomplete_provenance', rehashed, reference, lambda p: (p[section] if section else p).pop(key))


def test_extra_or_null_reference_fields_fail_closed():
    first = v10()
    reference = build_reference(target(2, first), first, first, content())
    expect('incomplete_provenance', rehashed, reference, lambda p: p['source'].update(latest_actual_revision_id=1))
    expect('incomplete_provenance', rehashed, reference, lambda p: p['binding'].update(definition_revision_id=None))
    expect('incomplete_provenance', rehashed, reference, lambda p: p['predecessor'].update(entry_mode='latest'))


def test_reference_bound_to_other_successor_rejected():
    first = v10()
    reference = build_reference(target(2, first), first, first, content())
    expect('successor_mismatch', resolve_effective_realization, target(2, first, context=ctx(2, report_indicator_id=42)),
           reference=reference, predecessor=first, source=first)


def test_tampered_source_value_rejected():
    first = v10()
    reference = build_reference(target(2, first), first, first, content())
    expect('source_content_mismatch', ReleasedIndicator, ctx(1), release(1), first.candidate, content(-12))
    expect('deviation_mismatch', ReleasedIndicator, ctx(1), release(1), first.candidate, content(value='112.4'))


# Materialized path
def test_materialized_only_resolution_succeeds():
    new = content(value='0', evidence=EVIDENCE[:1], deviation=dict(fields()['deviation'], delta='-100'))
    result = resolve_effective_realization(target(1), materialized=MaterializedRealization(31, new, 90))
    assert result.mode == ref.MODE_MATERIALIZED and result.reference_sha256 is None and result.predecessor_release_id is None
    assert result.value == Decimal('0') and result.evidence == EVIDENCE[:1] and result.actual_revision_id == 90


def test_materialized_for_other_indicator_or_wrong_delta_rejected():
    expect('successor_mismatch', resolve_effective_realization, target(2), materialized=MaterializedRealization(42, content()))
    expect('deviation_mismatch', resolve_effective_realization, target(2),
           materialized=MaterializedRealization(41, content(deviation=dict(fields()['deviation'], delta='12.4'))))
    expect('deviation_definition_mismatch', resolve_effective_realization, target(2), materialized=MaterializedRealization(
        41, content(deviation=dict(fields()['deviation'], target_definition_revision_id=10))))


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
    code = module_source.split('"""', 2)[2]
    for token in ('select(', 'order_by', '.query', 'with_for_update', "['actuals'][-1]"):
        assert token not in code, token
    expect('missing_realization', resolve_successor_realizations, [target(2, v10())])


def test_batch_resolution_requires_exactly_one_input_per_indicator():
    first = v10()
    reference = build_reference(target(2, first), first, first, content())
    second = target(2, first, context=ctx(2, report_indicator_id=42))
    resolved = resolve_successor_realizations([target(2, first), second],
        materialized={42: MaterializedRealization(42, content())}, references={41: (reference, first, first)})
    assert resolved[41].mode == ref.MODE_REFERENCE and resolved[42].mode == ref.MODE_MATERIALIZED
    expect('missing_realization', resolve_successor_realizations, [target(2, first), second],
           references={41: (reference, first, first)})
    expect('ambiguous_realization', resolve_successor_realizations, [target(2, first)],
           materialized={41: MaterializedRealization(41, content())}, references={41: (reference, first, first)})
    expect('unknown_indicator', resolve_successor_realizations, [target(2, first)],
           materialized={41: MaterializedRealization(41, content()), 99: MaterializedRealization(99, content())})
    expect('invalid_input', resolve_successor_realizations, [target(2, first), target(2, first)])
    expect('incomplete_provenance', resolve_successor_realizations, [target(2, first)], references={41: (reference, first)})


# Numeric / canonical semantics
def test_decimal_values_remain_exact():
    assert canonical_decimal('0.000001') == '0.000001'
    assert canonical_decimal('12.500000') == canonical_decimal(Decimal('12.500000')) == canonical_decimal('12.5') == '12.5'
    assert canonical_decimal('9999999999999999999.999999') == '9999999999999999999.999999'
    assert canonical_decimal('-0.000000') == canonical_decimal('0') == '0'
    assert canonical_decimal('100') == canonical_decimal(Decimal('1E+2')) == '100'
    for bad in (2.1, True, 1, '1.1234567', '1e5', 'NaN', 'Infinity', '12,5', ' 1', '100000000000000000000',
                Decimal('NaN'), Decimal('Infinity'), Decimal('-Infinity'), Decimal('0.0000001')):
        expect('invalid_decimal', canonical_decimal, bad)
    expect('float_not_allowed', content, deviation=dict(fields()['deviation'], extra=0.5))


def test_decimal_parsing_parity_with_parse_actual_for_ascii():
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


def test_evidence_mutation_changes_canonical_hash_and_inputs_are_copied():
    data = fields()
    original = content_from_fields(**data)
    before = original.sha256
    data['evidence'][0]['locator'] = 'Sayfa 4'
    assert original.sha256 == before and original.evidence == EVIDENCE
    mutated = content_from_fields(**data)
    assert mutated.sha256 != before
    first = v10()
    assert 'evidence_changed' in codes(check_reference_eligibility(target(2, first), first, first, mutated))
    original.evidence[0]['locator'] = 'X'
    assert original.sha256 == before


def test_deterministic_canonical_serialization():
    payload = {'b': [3, {'z': 'ş', 'a': None}], 'a': Decimal('1.50')}
    assert canonical_json(payload) == '{"a":"1.50","b":[3,{"a":null,"z":"ş"}]}'
    for sample in ({'name': 'Gösterge', 'targets': [{'value': '1.750000', 'state': 'verified'}], 'year': 2027},
                   EVIDENCE, fields()['deviation']):
        assert canonical_json(sample) == contract_canonical(sample)
    reordered = content(deviation=dict(reversed(list(fields()['deviation'].items()))),
                        evidence=[dict(reversed(list(e.items()))) for e in EVIDENCE])
    assert reordered.canonical_json() == content().canonical_json()


def test_deterministic_reference_hash():
    first = v10()
    one = build_reference(target(2, first), first, first, content())
    two = build_reference(target(2, v10()), v10(), v10(), content())
    assert one == two and one.reference_sha256 == ref.sha256_hex(one.provenance_json)
    verify_reference(UnchangedValueReference(one.provenance_json, one.reference_sha256),
                     successor=target(2, first), predecessor=first, source=first)


def test_order_sensitive_content_follows_civensa_semantics():
    first = v10()
    swapped = content(evidence=list(reversed(EVIDENCE)))
    assert swapped.sha256 != content().sha256
    assert 'evidence_changed' in codes(check_reference_eligibility(target(2, first), first, first, swapped))
    assert content(evidence=[dict(reversed(list(e.items()))) for e in EVIDENCE]).sha256 == content().sha256
    scaled = content(value='112.500000', deviation=dict(fields()['deviation'], delta='12.500000'))
    assert scaled == content() and check_reference_eligibility(target(2, first), first, first, scaled).eligible


def test_raw_text_is_not_content_identity():
    first = v10()
    entry = dict(v1_entry(1, fields()), raw_text='112,50')
    with_raw = ReleasedIndicator(ctx(1), release(1), candidate(1, [entry]), content())
    assert with_raw.content.sha256 == first.content.sha256
    assert 'raw_text' not in content().canonical_payload()

    class Row:
        value, raw_text, state = Decimal('112.500000'), '112,5', 'verified'
        evidence_json, explanation = contract_canonical(EVIDENCE), 'Hedef aşıldı.'
        deviation_json = contract_canonical(fields()['deviation'])
    other = Row()
    other.raw_text = '112.5000'
    assert content_from_actual_revision(Row()) == content_from_actual_revision(other) == content()


def test_context_rejects_definition_integrity_failures():
    expect('definition_integrity', ctx, 1, definition_sha256='d' * 64)
    expect('definition_integrity', ctx, 1, definition(definition_contract_version='2.0'))
    no_year = contract_canonical({k: v for k, v in json.loads(definition()).items() if k != 'year'})
    expect('definition_integrity', ctx, 1, no_year)
    v1_definition = contract_canonical({k: v for k, v in json.loads(definition()).items() if k != 'definition_contract_version'})
    assert ctx(1, v1_definition, contract_version='1.0').effective_target == Decimal('100')
    float_target = contract_canonical(dict(json.loads(definition()), targets=[
        {'year': 2027, 'value_kind': 'target', 'value': 100.0, 'raw_text': '100', 'state': 'verified'}]))
    expect('invalid_decimal', ctx, 1, float_target)
    expect('incomplete_provenance', ctx, 1, reporting_period_id=None)


def test_unverified_target_has_no_delta():
    targets = [{'year': 2027, 'value_kind': 'target', 'value': None, 'raw_text': '', 'state': 'missing'}]
    context = ctx(2, definition(targets=targets))
    assert context.effective_target is None
    resolve_effective_realization(target(2, context=context), materialized=MaterializedRealization(
        41, content(deviation=dict(fields()['deviation'], delta=None))))
    expect('deviation_mismatch', resolve_effective_realization, target(2, context=context),
           materialized=MaterializedRealization(41, content()))
    expect('invalid_deviation', content, state='needs_review')


def test_candidate_v2_predecessor_fields_are_all_or_none():
    expect('release_provenance_mismatch', candidate, 2, [v2_materialized_entry(2, fields())], V2, v10(),
           payload_changes={'predecessor_candidate_id': None})
    expect('release_provenance_mismatch', candidate, 2, [v2_materialized_entry(2, fields())], V2, v10(),
           payload_changes={'schema_version': 'activity-candidate-9'})


# Repository rows (SQLite and PostgreSQL): real context and ActualRevision; synthetic release/candidate.
def test_real_actual_revision_matches_package_copy(db, sample):
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
    assert entry['value'] != '2.75' and Decimal(entry['value']) == Decimal('2.75')
    assert content_from_entry(entry) == content_from_actual_revision(stored)

    revision = db.get(ActivityReportRevision, item.report_revision_id)
    binding = db.get(PublicationIndicatorBinding, item.publication_binding_id)
    definition_row = db.get(IndicatorDefinitionRevision, binding.definition_revision_id)
    activity = db.get(ActivityReport, revision.report_id)
    identity = db.get(IndicatorIdentity, definition_row.indicator_id)
    real = IndicatorContext(organization_id=activity.organization_id, activity_report_id=activity.id,
        reporting_period_id=activity.period_id, report_revision_id=revision.id, report_revision_number=revision.revision,
        report_indicator_id=item.id, persistent_indicator_id=definition_row.indicator_id,
        identity_organization_id=identity.organization_id, definition_revision_id=definition_row.id,
        definition_sha256=definition_row.sha256, definition_json=definition_row.definition_json,
        publication_id=revision.publication_id, publication_sha256=revision.publication_sha256,
        contract_version=revision.contract_version)
    assert real.effective_target == Decimal('1.75')
    payload = {'schema_version': V1, 'report_revision_id': revision.id, 'publication_id': revision.publication_id,
               'publication_sha256': revision.publication_sha256, 'contract_version': revision.contract_version,
               'entries': [dict(entry, report_indicator_id=item.id, materialized_report_indicator_id=item.id,
                                materialized_actual_revision_id=stored.id)]}
    manifest = {'version': 'report-manifest-1', 'organization_id': activity.organization_id, 'period_id': activity.period_id,
                'resource_scope': 'activity_report', 'source_id': revision.id, 'required_department_ids': [], 'packages': []}
    raw, mraw = service.canonical(payload), service.canonical(manifest)
    snapshot = CandidateSnapshot(candidate_id=900, organization_id=activity.organization_id, period_id=activity.period_id,
        resource_scope='activity_report', report_key=str(revision.id), activity_revision_id=revision.id, payload_json=raw,
        payload_sha256=service.digest(raw), manifest_json=mraw, sha256=hash_content(raw, mraw))
    released = ReleasedIndicator(real, ReleaseRecord(release_id=901, organization_id=activity.organization_id,
        resource_scope='activity_report', report_key=str(revision.id), release_major=1, release_minor=0, candidate_id=900,
        activity_approval_id=902, approval_report_revision_id=revision.id), snapshot, content_from_actual_revision(stored))
    successor = SuccessorTarget(replace(real, report_revision_id=revision.id + 1000, report_revision_number=revision.revision + 1,
        report_indicator_id=item.id + 1000), predecessor_release_id=901, predecessor_candidate_id=900,
        predecessor_candidate_sha256=snapshot.sha256)
    reference = build_reference(successor, released, released, content_from_entry(entry))
    resolved = resolve_effective_realization(successor, reference=reference, predecessor=released, source=released)
    assert resolved.value == Decimal('2.75') and resolved.actual_revision_id == stored.id
    assert db.scalar(select(ActualRevision.id).where(ActualRevision.id != stored.id)) is None  # engine wrote nothing
