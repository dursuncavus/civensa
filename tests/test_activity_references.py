"""S4: migrated PostgreSQL unchanged-value references, reference-aware successors and v2 verification."""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import select, func, text, event, insert
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.exc import DBAPIError
from app.models import *
from app import report_workflow_service as reports, activity_reference_service as references, activity_revision_reference as engine
from app import authorization_service as auth, revision_workflow_service as corrections
from tests.test_authorization_foundation import foundation_db, ROOT
from tests.test_materialized_successor import people, package, ready, assemble, counts, sealed, assert_sealed
from tests.test_report_workflow import approved, candidate, review, approve, publish, rejects
from tests.test_revision_workflow import released, request, accept, grant, edit
from tests.test_package_workflow import act
from tests.test_returned_attempt_rework import return_attempt, reassemble
pytestmark = pytest.mark.postgres
REFS = ActivityRealizationReference


@pytest.fixture
def on(monkeypatch):
    # The feature stays disabled in the product; only these tests switch the writer on.
    monkeypatch.setattr(reports, 'ACTIVITY_REFERENCE_SUCCESSORS', True)


def ref_count(db):
    return db.scalar(select(func.count(REFS.id)))


def entries(c):
    return json.loads(c.payload_json)['entries']


def split(c):
    """(changed entry 0 = corrected value, unchanged entry 1 = 1.75) of a successor candidate."""
    changed, unchanged = entries(c)
    return changed, unchanged


def actual_ids(db, ri_id):
    return list(db.scalars(select(ActualRevision.id).where(ActualRevision.report_indicator_id == ri_id)))


def row_for(db, ri_id):
    return db.scalar(select(REFS).where(REFS.successor_report_indicator_id == ri_id))


def materialized_actual(c, index):
    e = entries(c)[index]
    return e['materialized_actual_revision_id'] if 'materialized_actual_revision_id' in e else e['realization'].get('actual_revision_id')


def correct_again(db, x, release, value):
    q = request(db, x, release, 'director');accept(db, x, q);g = grant(db, x, q, key='director')
    rev = edit(db, x, g, 'director', value=value, reason='Ardıl sürüm düzeltmesi')
    p = db.get(DirectoratePackage, rev.package_id)
    act(db, x, p, 'submit_to_director', 'director');act(db, x, p, 'director_approve');act(db, x, p, 'strategy_approve', 'strategy')
    return p, q


def published_successor(db, x, release, p):
    c = assemble(db, x, release, p);db.commit();review(db, x, c);approve(db, x, c)
    return c, publish(db, x, c)


def test_feature_disabled_by_default_keeps_v1_exactly(foundation_db, people, released, ready):
    db = foundation_db;x = people;p = ready[0]
    assert reports.ACTIVITY_REFERENCE_SUCCESSORS is False
    c = assemble(db, x, released, p);db.commit()
    payload = json.loads(c.payload_json);manifest = reports.verify(db, c)
    assert payload['schema_version'] == 'activity-candidate-1' and manifest['successor_contract'] == 'materialized-successor-1'
    assert ref_count(db) == 0 and all(len(actual_ids(db, e['materialized_report_indicator_id'])) == 1 for e in payload['entries'])


def test_initial_release_stays_v1_with_writer_on(on, foundation_db, people, released):
    db = foundation_db;c = db.get(ReportCandidate, released.candidate_id)
    assert json.loads(c.payload_json)['schema_version'] == 'activity-candidate-1'
    assert 'predecessor_release_id' not in json.loads(c.manifest_json) and ref_count(db) == 0


def test_unchanged_becomes_reference_changed_is_materialized(on, foundation_db, people, released, ready):
    db = foundation_db;x = people;p, corrected, q, g = ready;before = sealed(db)
    previous = db.get(ReportCandidate, released.candidate_id)
    c = assemble(db, x, released, p);db.commit()
    payload = json.loads(c.payload_json);manifest = reports.verify(db, c)
    assert payload['schema_version'] == 'activity-candidate-2' and manifest['successor_contract'] == 'reference-successor-1'
    # E1: lineage lives only in the manifest and the candidate column.
    assert not set(engine.LINEAGE_PAYLOAD_KEYS) & set(payload)
    assert (manifest['predecessor_release_id'], manifest['predecessor_candidate_sha256'], c.predecessor_candidate_id) == (released.id, previous.sha256, previous.id)
    changed, unchanged = split(c)
    # v2 entries keep the expanded content.
    assert (changed['value'], unchanged['value']) == ('2.50', '1.75')
    assert all({'value', 'state', 'evidence', 'explanation', 'deviation'} <= set(e) for e in (changed, unchanged))
    assert changed['realization']['mode'] == 'materialized'
    assert actual_ids(db, changed['successor_report_indicator_id']) == [changed['realization']['actual_revision_id']]
    assert row_for(db, changed['successor_report_indicator_id']) is None
    a = db.get(ActualRevision, changed['realization']['actual_revision_id'])
    assert a.id not in before[ActualRevision] and a.value == reports.contract.parse_actual('2.50')
    # The unchanged indicator has a reference and NO ActualRevision (XOR).
    assert unchanged['realization']['mode'] == 'reference' and actual_ids(db, unchanged['successor_report_indicator_id']) == []
    row = row_for(db, unchanged['successor_report_indicator_id'])
    source_actual = materialized_actual(previous, 1)
    assert (row.predecessor_release_id, row.predecessor_candidate_id, row.source_release_id) == (released.id, previous.id, released.id)
    assert row.predecessor_reference_id is None and row.source_actual_revision_id == source_actual
    assert row.source_report_indicator_id == row.predecessor_report_indicator_id == entries(previous)[1]['materialized_report_indicator_id']
    assert (row.successor_report_revision_id, row.reference_sha256) == (c.activity_revision_id, unchanged['realization']['reference_sha256'])
    assert unchanged['realization'] == {'mode': 'reference', 'reference_sha256': row.reference_sha256, 'source_release_id': released.id,
        'source_actual_revision_id': source_actual, 'content_sha256': row.content_sha256}
    stored = json.loads(row.provenance_json)
    assert stored['predecessor']['release_id'] == released.id and stored['source']['actual_revision_id'] == source_actual
    assert row.created_at is not None and row.created_by == x['strategy'].id
    assert_sealed(db, before)
    review(db, x, c);approve(db, x, c);first = publish(db, x, c)
    assert (first.major, first.minor) == (1, 1) and db.get(RevisionRequestState, q.id).state == 'applied'
    reports.verify_artifact(db, first);reports.verify(db, c)


def test_payload_equals_reference_rows(on, foundation_db, people, released, ready):
    db = foundation_db;x = people;c = assemble(db, x, released, ready[0]);db.commit()
    rows = db.scalars(select(REFS).where(REFS.successor_report_revision_id == c.activity_revision_id)).all()
    by_ri = {e['successor_report_indicator_id']: e for e in entries(c)}
    referenced = {ri for ri, e in by_ri.items() if e['realization']['mode'] == 'reference'}
    assert {r.successor_report_indicator_id for r in rows} == referenced and len(rows) == 1
    for r in rows:
        realization = by_ri[r.successor_report_indicator_id]['realization']
        assert (realization['reference_sha256'], realization['source_release_id'], realization['source_actual_revision_id'], realization['content_sha256']) \
            == (r.reference_sha256, r.source_release_id, r.source_actual_revision_id, r.content_sha256)
        stored = json.loads(r.provenance_json)
        assert stored['successor']['report_indicator_id'] == r.successor_report_indicator_id
        assert engine.sha256_hex(r.provenance_json) == r.reference_sha256


def test_engine_resolves_persisted_rows(on, foundation_db, people, released, ready):
    """Engine under migrated foundation_db: real rows in, persisted reference resolved, no lookup."""
    db = foundation_db;x = people;c = assemble(db, x, released, ready[0]);db.commit()
    previous = db.get(ReportCandidate, released.candidate_id);manifest = json.loads(c.manifest_json)
    changed, unchanged = split(c)
    predecessor = references.predecessor_indicator(db, released, previous, unchanged['report_indicator_id'])
    target = engine.SuccessorTarget(references.indicator_context(db, c.activity_revision_id, unchanged['successor_report_indicator_id']),
        manifest['predecessor_release_id'], c.predecessor_candidate_id, manifest['predecessor_candidate_sha256'])
    row = row_for(db, unchanged['successor_report_indicator_id'])
    effective = engine.resolve_effective_realization(target, reference=engine.UnchangedValueReference(row.provenance_json, row.reference_sha256),
        predecessor=predecessor, source=references.source_indicator(db, predecessor))
    assert effective.mode == 'reference' and effective.actual_revision_id == materialized_actual(previous, 1)
    assert effective.content.sha256 == engine.content_from_entry(unchanged).sha256 and effective.value == engine.Decimal('1.75')
    # The changed indicator is ineligible against the same immediate predecessor.
    other = references.predecessor_indicator(db, released, previous, changed['report_indicator_id'])
    t2 = engine.SuccessorTarget(references.indicator_context(db, c.activity_revision_id, changed['successor_report_indicator_id']),
        released.id, previous.id, previous.sha256)
    result = engine.check_reference_eligibility(t2, other, other, engine.content_from_entry(changed))
    assert not result.eligible and 'value_changed' in {m.code for m in result.mismatches}


def test_rework_references_published_predecessor_never_returned_attempt(on, foundation_db, people, released, ready):
    db = foundation_db;x = people;p = ready[0]
    a = assemble(db, x, released, p);db.commit();review(db, x, a);return_attempt(db, x, a)
    assert json.loads(a.payload_json)['schema_version'] == 'activity-candidate-2'
    a_rows = {r.id for r in db.scalars(select(REFS))}
    b = reassemble(db, x, released, p);m = json.loads(b.manifest_json)
    assert m['reworks_candidate_id'] == a.id and m['predecessor_release_id'] == released.id
    assert b.predecessor_candidate_id == released.candidate_id != a.id
    assert db.get(ActivityReportRevision, b.activity_revision_id).previous_revision_id == a.activity_revision_id
    b_rows = db.scalars(select(REFS).where(REFS.successor_report_revision_id == b.activity_revision_id)).all()
    assert len(b_rows) == 1 and not {r.id for r in b_rows} & a_rows
    for r in db.scalars(select(REFS)):
        assert (r.predecessor_release_id, r.predecessor_candidate_id, r.source_release_id) == (released.id, released.candidate_id, released.id)
        assert r.predecessor_candidate_id != a.id
    # A has no release, so it can be neither a predecessor nor a source.
    assert db.scalar(select(ReportRelease.id).where(ReportRelease.candidate_id == a.id)) is None
    changed_a, changed_b = split(a)[0], split(b)[0]
    assert changed_b['realization']['mode'] == 'materialized' and changed_b['realization']['actual_revision_id'] != changed_a['realization']['actual_revision_id']
    assert actual_ids(db, changed_b['successor_report_indicator_id']) == [changed_b['realization']['actual_revision_id']]
    review(db, x, b);approve(db, x, b);r = publish(db, x, b)
    assert (r.major, r.minor) == (1, 1);reports.verify(db, b);reports.verify(db, a)


def test_three_release_chain_flattens_to_original_source(on, foundation_db, people, released, ready):
    db = foundation_db;x = people;p = ready[0]
    c11, v11 = published_successor(db, x, released, p)
    p, q = correct_again(db, x, v11, '3.50')
    c12, v12 = published_successor(db, x, v11, p)
    assert (v12.major, v12.minor) == (1, 2)
    v10 = db.get(ReportCandidate, released.candidate_id)
    changed, unchanged = split(c12)
    assert changed['value'] == '3.50' and changed['realization']['mode'] == 'materialized'
    row12 = row_for(db, unchanged['successor_report_indicator_id']);row11 = row_for(db, split(c11)[1]['successor_report_indicator_id'])
    # Bound to the IMMEDIATE predecessor 1.1, flattened to the original 1.0 materialized ActualRevision.
    assert (row12.predecessor_release_id, row12.predecessor_candidate_id, row12.predecessor_reference_id) == (v11.id, c11.id, row11.id)
    assert (row12.source_release_id, row12.source_actual_revision_id) == (released.id, materialized_actual(v10, 1))
    assert row12.source_actual_revision_id == row11.source_actual_revision_id and row12.content_sha256 == row11.content_sha256
    stored = json.loads(row12.provenance_json)
    assert stored['predecessor']['entry_mode'] == 'reference' and stored['predecessor']['predecessor_reference_sha256'] == row11.reference_sha256
    assert actual_ids(db, unchanged['successor_report_indicator_id']) == []
    for c in (v10, c11, c12):reports.verify(db, c)
    for r in (released, v11, v12):reports.verify_artifact(db, r)
    assert db.get(RevisionRequestState, q.id).state == 'applied'


def test_skip_over_rejected_by_writer_engine_and_database(on, foundation_db, people, released, ready):
    db = foundation_db;x = people;p = ready[0]
    c11, v11 = published_successor(db, x, released, p)
    p, q = correct_again(db, x, v11, '3.50')
    with pytest.raises(auth.HTTPException) as stale:assemble(db, x, released, p)
    assert stale.value.status_code == 409 and 'Güncel yayın sürümü değişti' in str(stale.value.detail)  # writer: 1.0 is superseded
    v10 = db.get(ReportCandidate, released.candidate_id);key = entries(v10)[1]['report_indicator_id']
    old = references.predecessor_indicator(db, released, v10, key);mid = references.predecessor_indicator(db, v11, c11, key)
    # Engine: content equal to 1.0, but the immediate predecessor is 1.1.
    result = engine.check_reference_eligibility(engine.SuccessorTarget(
        engine.IndicatorContext(**{**mid.context.__dict__, 'report_revision_id': 10**6, 'report_revision_number': mid.context.report_revision_number + 1,
                                   'report_indicator_id': 10**6}), v11.id, c11.id, c11.sha256), old, old, old.content)
    assert not result.eligible and 'predecessor_mismatch' in {m.code for m in result.mismatches}
    before = counts(db), ref_count(db)

    def skip(connection, t):
        # Database: a self-consistent row that binds 1.0 directly, skipping 1.1.
        t.predecessor_release_id = released.id;t.predecessor_candidate_id = v10.id;t.predecessor_reference_id = None
        t.predecessor_report_indicator_id = old.context.report_indicator_id
        rehash(t, lambda s: s.update(predecessor=old.predecessor_section(), source=old.flattened_source()))
    assert 'current immediate predecessor' in str(forge(db, x, v11, p, skip))

    def unlink(connection, t):t.predecessor_reference_id = None
    # A referencing predecessor cannot be presented as materialized.
    assert 'must flatten to the predecessor reference source' in str(forge(db, x, v11, p, unlink))
    assert (counts(db), ref_count(db)) == before


def test_superseded_predecessor_publish_has_no_writes(on, foundation_db, people, released, ready):
    db = foundation_db;x = people;c = assemble(db, x, released, ready[0]);db.commit();review(db, x, c);approve(db, x, c)
    original = db.scalar
    def scalar(statement, *a, **kw):
        if 'report_releases.major DESC' in str(statement):return released.id + 999
        return original(statement, *a, **kw)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(db, 'scalar', scalar);before = counts(db), ref_count(db)
        rejects(409, lambda: publish(db, x, c))
    assert (counts(db), ref_count(db)) == before
    assert db.scalar(select(ReportRelease).where(ReportRelease.candidate_id == c.id)) is None


def forge(db, x, released, p, mutate, model=REFS, when='before_insert'):
    def hook(mapper, connection, target):mutate(connection, target)
    event.listen(model, when, hook)
    try:
        with pytest.raises(DBAPIError) as caught:assemble(db, x, released, p)
    finally:event.remove(model, when, hook)
    db.rollback();return caught.value


def rehash(target, change):
    stored = json.loads(target.provenance_json);change(stored)
    target.provenance_json = engine.canonical_json(stored);target.reference_sha256 = engine.sha256_hex(target.provenance_json)


@pytest.mark.parametrize('bad', ['reference_sha', 'provenance_text', 'json_source_actual', 'column_source_actual', 'predecessor_candidate',
                                 'predecessor_release', 'definition', 'persistent_id', 'content', 'actor', 'scope', 'source_release'])
def test_provenance_forgery_rejected_by_database(on, foundation_db, people, released, ready, bad):
    db = foundation_db;x = people;p = ready[0];before = counts(db), ref_count(db)
    other_actual = materialized_actual(db.get(ReportCandidate, released.candidate_id), 0)

    def mutate(connection, t):
        if bad == 'reference_sha':t.reference_sha256 = '0' * 64
        elif bad == 'provenance_text':t.provenance_json = t.provenance_json.replace('"schema"', '"schema" ', 1)
        elif bad == 'json_source_actual':rehash(t, lambda s: s['source'].update(actual_revision_id=other_actual))
        elif bad == 'column_source_actual':t.source_actual_revision_id = other_actual
        elif bad == 'predecessor_candidate':t.predecessor_candidate_id = t.predecessor_candidate_id + 999
        elif bad == 'predecessor_release':t.predecessor_release_id = t.predecessor_release_id + 999
        elif bad == 'definition':t.definition_revision_id = t.definition_revision_id + 999
        elif bad == 'persistent_id':
            connection.execute(insert(IndicatorIdentity).values(indicator_id='forged-identity', organization_id=t.organization_id))
            t.persistent_indicator_id = 'forged-identity'
        elif bad == 'content':
            t.content_sha256 = '1' * 64
            rehash(t, lambda s: (s.update(content_sha256='1' * 64), s['predecessor'].update(content_sha256='1' * 64)))
        elif bad == 'actor':t.created_by = x['user'].id
        elif bad == 'scope':t.successor_report_revision_id = db.get(ReportCandidate, released.candidate_id).activity_revision_id
        else:t.source_release_id = t.source_release_id + 999
    expected = {'reference_sha': 'provenance mismatch', 'provenance_text': 'provenance mismatch', 'json_source_actual': 'provenance mismatch',
        'column_source_actual': 'source must be the materialized predecessor', 'source_release': 'source must be the materialized predecessor',
        'predecessor_candidate': 'current immediate predecessor', 'predecessor_release': 'current immediate predecessor',
        'definition': 'definition binding mismatch', 'persistent_id': 'definition binding mismatch',
        # content_sha256 cannot be recomputed in SQL; the successor guard compares the entry with the source actual.
        'content': 'not unchanged source content', 'actor': 'active Strategy actor', 'scope': 'successor scope mismatch'}[bad]
    assert expected in str(forge(db, x, released, p, mutate))
    assert (counts(db), ref_count(db)) == before


def test_changed_content_cannot_become_reference(on, foundation_db, people, released, ready):
    """applied => materialized: a forced reference for corrected content is rejected by the database."""
    db = foundation_db;x = people;p, rev, q, g = ready;before = counts(db), ref_count(db)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(engine, 'check_reference_eligibility', lambda *a: engine.Eligibility(True, ()))
        patch.setattr(engine, 'require_reference_eligibility', lambda *a: engine.Eligibility(True, ()))
        with pytest.raises(DBAPIError, match='not unchanged source content'):assemble(db, x, released, p)
    db.rollback();assert (counts(db), ref_count(db)) == before
    c, first = published_successor(db, x, released, p)
    changed, unchanged = split(c)
    assert db.get(RevisionRequestState, q.id).state == 'applied'
    # The applied correction's field is a fresh ActualRevision; only the untouched field is a reference.
    assert changed['realization']['mode'] == 'materialized' and row_for(db, changed['successor_report_indicator_id']) is None
    assert unchanged['realization']['mode'] == 'reference'


def test_xor_and_uniqueness_enforced_by_database(on, foundation_db, people, released, ready):
    db = foundation_db;x = people;p = ready[0];before = counts(db), ref_count(db)

    def actual_on_reference(connection, t):
        connection.execute(insert(ActualRevision).values(report_indicator_id=t.successor_report_indicator_id, revision=1, value=None,
            raw_text='', state='missing', evidence_json='[]', explanation='', deviation_json='{}', created_by=x['strategy'].id))
    assert 'realized by a reference' in str(forge(db, x, released, p, actual_on_reference, when='after_insert'))

    def reference_on_actual(connection, t):
        rid = connection.scalar(select(ReportIndicator.id).where(ReportIndicator.report_revision_id == t.successor_report_revision_id,
            ReportIndicator.id != t.successor_report_indicator_id))
        t.successor_report_indicator_id = rid
    assert 'already materialized' in str(forge(db, x, released, p, reference_on_actual))

    def duplicate(connection, t):
        values = {c.name: getattr(t, c.name) for c in REFS.__table__.columns if c.name not in ('id', 'created_at')}
        connection.execute(insert(REFS).values(**values))
    error = forge(db, x, released, p, duplicate, when='after_insert')
    assert error.orig.sqlstate == '23505' and 'Key (successor_report_indicator_id)' in str(error)  # unique_violation
    assert (counts(db), ref_count(db)) == before
    constraints = dict(db.execute(text("SELECT conname,pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='activity_realization_references'::regclass")).all())
    assert any('UNIQUE (successor_report_indicator_id)' in d for d in constraints.values())
    assert any('UNIQUE (reference_sha256)' in d for d in constraints.values()) and 'ck_activity_reference_chain' in constraints


def test_seal_after_candidate_and_immutable_history(on, foundation_db, people, released, ready):
    db = foundation_db;x = people;c = assemble(db, x, released, ready[0]);db.commit()
    changed, unchanged = split(c);row = row_for(db, unchanged['successor_report_indicator_id']);before = counts(db), ref_count(db)
    values = {col.name: getattr(row, col.name) for col in REFS.__table__.columns if col.name not in ('id', 'created_at')}
    with pytest.raises(DBAPIError, match='sealed'):
        with db.begin_nested():db.execute(insert(REFS).values(**dict(values, successor_report_indicator_id=changed['successor_report_indicator_id'])))
    with pytest.raises(DBAPIError, match='realized by a reference'):
        with db.begin_nested():
            db.execute(insert(ActualRevision).values(report_indicator_id=row.successor_report_indicator_id, revision=1, value=None, raw_text='',
                state='missing', evidence_json='[]', explanation='', deviation_json='{}', created_by=x['strategy'].id))
    for statement in ('UPDATE activity_realization_references SET content_sha256=content_sha256', 'DELETE FROM activity_realization_references'):
        with pytest.raises(DBAPIError, match='civensa_auth_immutable'):
            with db.begin_nested():db.execute(text(statement))
    with pytest.raises(ValueError):
        row.content_sha256 = '2' * 64;db.flush()
    db.rollback();assert (counts(db), ref_count(db)) == before
    triggers = set(db.scalars(text("SELECT tgname FROM pg_trigger WHERE tgrelid='activity_realization_references'::regclass AND NOT tgisinternal")))
    assert {'immutable_activity_realization_references', 'timestamp_activity_realization_references', 'activity_reference_guard'} <= triggers
    reports.verify(db, db.get(ReportCandidate, c.id))


@pytest.mark.parametrize('bad', ['mode', 'reference_sha', 'source_release', 'source_actual', 'content_sha', 'lineage_in_payload',
                                 'extra_key', 'missing_successor', 'drop_reference_to_v1_keys'])
def test_v2_verification_fails_closed_on_tampered_payload(on, foundation_db, people, released, ready, bad):
    db = foundation_db;x = people;c = assemble(db, x, released, ready[0]);db.commit()
    payload = json.loads(c.payload_json);entry = payload['entries'][1];realization = entry['realization']
    if bad == 'mode':realization['mode'] = 'materialized'
    elif bad == 'reference_sha':realization['reference_sha256'] = '0' * 64
    elif bad == 'source_release':realization['source_release_id'] += 999
    elif bad == 'source_actual':realization['source_actual_revision_id'] = materialized_actual(db.get(ReportCandidate, released.candidate_id), 0)
    elif bad == 'content_sha':realization['content_sha256'] = '0' * 64
    elif bad == 'lineage_in_payload':payload['predecessor_release_id'] = released.id
    elif bad == 'extra_key':realization['predecessor_release_id'] = released.id
    elif bad == 'missing_successor':del entry['successor_report_indicator_id']
    else:
        entry.pop('realization');entry['materialized_report_indicator_id'] = entry.pop('successor_report_indicator_id')
        entry['materialized_actual_revision_id'] = 1
    raw = reports.canonical(payload)
    set_committed_value(c, 'payload_json', raw);set_committed_value(c, 'payload_sha256', reports.contract.digest(raw))
    set_committed_value(c, 'sha256', reports.hash_content(raw, c.manifest_json))
    rejects(409, lambda: reports.verify(db, c))


def test_v2_reference_needs_its_row(on, foundation_db, people, released, ready, monkeypatch):
    db = foundation_db;x = people;c = assemble(db, x, released, ready[0]);db.commit()
    original = db.scalars
    def scalars(statement, *a, **kw):
        if 'FROM activity_realization_references' in str(statement):return original(select(REFS).where(REFS.id < 0), *a, **kw)
        return original(statement, *a, **kw)
    monkeypatch.setattr(db, 'scalars', scalars)
    rejects(409, lambda: reports.verify(db, c))


def test_non_canonical_content_falls_back_to_v1(on, foundation_db, people, released, ready, monkeypatch):
    db = foundation_db;x = people;monkeypatch.setattr(references, 'canonical_contents', lambda contents: False)
    c = assemble(db, x, released, ready[0]);db.commit()
    assert json.loads(c.payload_json)['schema_version'] == 'activity-candidate-1' and ref_count(db) == 0
    assert reports.verify(db, c)['successor_contract'] == 'materialized-successor-1'


def test_concurrent_reference_successor_one_winner_no_orphans(on, foundation_db, people, released, ready):
    db = foundation_db;x = people;p = ready[0]
    uid = x['strategy'].id;rid = released.id;org = released.organization_id;report = int(released.report_key);pid = p.id
    before = counts(db), ref_count(db);db.commit();barrier = Barrier(2)
    def run(_):
        with Session(db.get_bind(), expire_on_commit=False) as worker:
            actor = worker.get(User, uid);barrier.wait(timeout=5)
            try:
                reports.assemble_activity_successor(worker, actor, org, report, rid, [pid]);worker.commit();return 1
            except auth.HTTPException as exc:worker.rollback();return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(run, range(2))) == [1, 409]
    db.expire_all();after = counts(db), ref_count(db)
    assert after[0][0] == before[0][0] + 1 and after[0][5] == before[0][5] + 2 and after[0][6] == before[0][6] + 1
    assert after[1] == before[1] + 1 and after[0][1:4] == before[0][1:4]
    c = db.scalar(select(ReportCandidate).order_by(ReportCandidate.id.desc()));reports.verify(db, c)


@pytest.mark.parametrize('foundation_db', ['3942a5669b80'], indirect=True)
@pytest.mark.parametrize('writer', [False, True])
def test_populated_upgrade_then_v1_and_v2_successors(foundation_db, people, released, ready, writer, monkeypatch):
    db = foundation_db;x = people;p = ready[0];before = sealed(db);db.commit();url = db.bind.url.render_as_string(hide_password=False)
    # The S3C-2 repair below S4 still refuses to be discarded.
    down = subprocess.run([sys.executable, '-m', 'alembic', 'downgrade', '-1'], cwd=ROOT, env={**os.environ, 'DATABASE_URL': url}, capture_output=True, text=True)
    assert down.returncode != 0 and 'Package decision guards and closed_no_change survival cannot be discarded' in down.stderr
    for _ in range(2):
        run = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=ROOT, env={**os.environ, 'DATABASE_URL': url}, capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
    down = subprocess.run([sys.executable, '-m', 'alembic', 'downgrade', '-1'], cwd=ROOT, env={**os.environ, 'DATABASE_URL': url}, capture_output=True, text=True)
    # A1-P1: the newest revision (c5e8a1f0b247) refuses first; S4 history below it stays unreachable.
    assert down.returncode != 0 and 'A1-P1 workflow activation guards cannot be discarded' in down.stderr
    db.expire_all();assert_sealed(db, before)
    assert db.execute(text('SELECT version_num FROM alembic_version')).scalar_one() == 'c5e8a1f0b247'
    reports.verify(db, db.get(ReportCandidate, released.candidate_id))
    monkeypatch.setattr(reports, 'ACTIVITY_REFERENCE_SUCCESSORS', writer)
    c, r = published_successor(db, x, released, p)
    assert json.loads(c.payload_json)['schema_version'] == ('activity-candidate-2' if writer else 'activity-candidate-1')
    assert ref_count(db) == (1 if writer else 0) and (r.major, r.minor) == (1, 1)
    assert_sealed(db, before)


def correct_entry(db, x, release, index, value):
    """Correct one field of an explicit entry under a Strategy-granted request, then re-approve."""
    q = corrections.create_request(db, x['director'], release.id, x['department'].id, [{'path': ['entries', index, 'value']}],
                                   'Kaynak cetveli düzeltmesi', [{'reference': '2027/2'}]);db.commit()
    accept(db, x, q);g = grant(db, x, q, key='director')
    cycle = db.get(RevisionCorrectionCycle, g.cycle_id);p = db.get(DirectoratePackage, cycle.package_id);rev = corrections.packages.revision(db, p)
    corrections.edit_under_grant(db, x['director'], g.id, p.version, rev.sha256, [{'path': ['entries', index, 'value'], 'value': value}], 'Düzeltme');db.commit()
    act(db, x, p, 'submit_to_director', 'director');act(db, x, p, 'director_approve');act(db, x, p, 'strategy_approve', 'strategy')
    return p


def test_reference_to_materialized_predecessor_in_later_release(on, foundation_db, people, released, ready):
    """1.1 materializes indicator 0; 1.2 changes only indicator 1, so indicator 0 references 1.1 itself."""
    db = foundation_db;x = people
    c11, v11 = published_successor(db, x, released, ready[0])
    p = correct_entry(db, x, v11, 1, '1.90')
    c12, v12 = published_successor(db, x, v11, p)
    first, second = split(c12)
    assert first['realization']['mode'] == 'reference' and second['realization']['mode'] == 'materialized' and second['value'] == '1.90'
    row = row_for(db, first['successor_report_indicator_id'])
    assert (row.predecessor_release_id, row.source_release_id, row.predecessor_reference_id) == (v11.id, v11.id, None)
    assert row.source_actual_revision_id == materialized_actual(c11, 0) == split(c11)[0]['realization']['actual_revision_id']
    for c in (c11, c12):reports.verify(db, c)


def test_revert_to_older_value_is_materialized(on, foundation_db, people, released, ready):
    """Equal to 1.0 but different from the immediate predecessor 1.1: never a reference."""
    db = foundation_db;x = people
    original = entries(db.get(ReportCandidate, released.candidate_id))[0]['value']
    c11, v11 = published_successor(db, x, released, ready[0])
    assert split(c11)[0]['value'] != original
    p = correct_entry(db, x, v11, 0, original)
    c12, v12 = published_successor(db, x, v11, p)
    reverted = split(c12)[0]
    assert reverted['value'] == original and reverted['realization']['mode'] == 'materialized'
    assert row_for(db, reverted['successor_report_indicator_id']) is None
    assert actual_ids(db, reverted['successor_report_indicator_id']) == [reverted['realization']['actual_revision_id']]


def test_returned_attempt_forged_as_predecessor_rejected_by_database(on, foundation_db, people, released, ready):
    db = foundation_db;x = people;p = ready[0]
    a = assemble(db, x, released, p);db.commit();review(db, x, a);return_attempt(db, x, a);before = counts(db), ref_count(db)
    def to_attempt(connection, t):t.predecessor_candidate_id = a.id
    assert 'current immediate predecessor' in str(forge(db, x, released, p, to_attempt))
    assert (counts(db), ref_count(db)) == before


def mutate_json(t, attr, change):
    data = json.loads(getattr(t, attr));change(data);setattr(t, attr, reports.canonical(data))


@pytest.mark.parametrize('bad', ['contract', 'relabel_v1', 'no_lineage', 'drop_entry', 'duplicate_entry', 'unknown_mode',
                                 'materialized_wrong_actual', 'reference_as_materialized', 'lineage_in_payload', 'reference_sha'])
def test_successor_guard_rejects_bad_v2_candidates(on, foundation_db, people, released, ready, bad):
    """The widened civensa_activity_successor_guard itself, below the Python verifier."""
    db = foundation_db;x = people;p = ready[0];before = counts(db), ref_count(db)

    def mutate(connection, t):
        e = lambda d: d['entries']
        if bad == 'contract':mutate_json(t, 'manifest_json', lambda m: m.update(successor_contract='materialized-successor-1'))
        elif bad == 'relabel_v1':mutate_json(t, 'payload_json', lambda d: d.update(schema_version='activity-candidate-1'))
        elif bad == 'no_lineage':mutate_json(t, 'manifest_json', lambda m: m.pop('predecessor_release_id'))
        elif bad == 'drop_entry':mutate_json(t, 'payload_json', lambda d: e(d).pop())
        elif bad == 'duplicate_entry':mutate_json(t, 'payload_json', lambda d: e(d).__setitem__(1, e(d)[0]))
        elif bad == 'unknown_mode':mutate_json(t, 'payload_json', lambda d: e(d)[1]['realization'].update(mode='inherited'))
        elif bad == 'materialized_wrong_actual':
            mutate_json(t, 'payload_json', lambda d: e(d)[0]['realization'].update(actual_revision_id=materialized_actual(db.get(ReportCandidate, released.candidate_id), 0)))
        elif bad == 'reference_as_materialized':
            mutate_json(t, 'payload_json', lambda d: e(d)[1].update(realization={'mode': 'materialized',
                'actual_revision_id': e(d)[0]['realization']['actual_revision_id'], 'content_sha256': e(d)[1]['realization']['content_sha256']}))
        elif bad == 'lineage_in_payload':mutate_json(t, 'payload_json', lambda d: d.update(predecessor_release_id=released.id))
        else:mutate_json(t, 'payload_json', lambda d: e(d)[1]['realization'].update(reference_sha256='0' * 64))
    expected = {'contract': 'Invalid/current materialized successor predecessor', 'relabel_v1': 'Only a reference successor may own',
        # The older initial-candidate guard fires first; the S4 lineage check is defence in depth.
        'no_lineage': 'Published Activity requires explicit successor assembly', 'drop_entry': 'does not cover', 'duplicate_entry': 'does not cover',
        'unknown_mode': 'Unknown successor realization', 'materialized_wrong_actual': 'Materialized successor entry mismatch',
        'reference_as_materialized': 'Materialized successor entry mismatch', 'lineage_in_payload': 'does not cover',
        'reference_sha': 'not unchanged source content'}[bad]
    assert expected in str(forge(db, x, released, p, mutate, model=ReportCandidate))
    assert (counts(db), ref_count(db)) == before
