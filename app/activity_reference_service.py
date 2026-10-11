"""S4 disabled backend: reference-aware Activity successor realization and v2 verification.

Row adapters feed the pure activity_revision_reference engine from immutable rows only.
A successor ReportIndicator gets a reference only when the engine proves its content
unchanged against the IMMEDIATE predecessor release (manifest + candidate column, E1);
otherwise it gets a fresh ActualRevision exactly as activity-candidate-1 does.
Callers own the transaction. Readers do not resolve references yet, so
report_workflow_service.ACTIVITY_REFERENCE_SUCCESSORS stays False outside tests.
"""
import json
from sqlalchemy import select
from .models import *
from . import activity_revision_reference as engine, activity_contract_service as contract, package_service as packages

CANDIDATE_V1 = engine.CANDIDATE_SCHEMA_V1
CANDIDATE_V2 = engine.CANDIDATE_SCHEMA_V2
SUCCESSOR_CONTRACTS = {CANDIDATE_V1: 'materialized-successor-1', CANDIDATE_V2: 'reference-successor-1'}
REALIZATION_KEYS = {CANDIDATE_V1: frozenset({'materialized_report_indicator_id', 'materialized_actual_revision_id'}),
                    CANDIDATE_V2: frozenset({'successor_report_indicator_id', 'realization'})}
MATERIALIZED_KEYS = frozenset({'mode', 'actual_revision_id', 'content_sha256'})
REFERENCE_KEYS = frozenset({'mode', 'reference_sha256', 'source_release_id', 'source_actual_revision_id', 'content_sha256'})


def _identifier(value):
    if type(value) is not int or not 0 < value <= 2147483647:packages.conflict()
    return value


def validate_v2_entries(candidate, payload):
    """Shape of the activity-candidate-2 boundary; no lookup happens before this passes."""
    manifest = json.loads(candidate.manifest_json)
    if not isinstance(manifest, dict) or 'predecessor_release_id' not in manifest:packages.conflict()
    if any(key in payload for key in engine.LINEAGE_PAYLOAD_KEYS):packages.conflict()
    for entry in payload['entries']:
        for key in ('successor_report_indicator_id', 'definition_revision_id'):_identifier(entry.get(key))
        realization = entry.get('realization')
        if not isinstance(realization, dict):packages.conflict()
        if realization.get('mode') == engine.MODE_MATERIALIZED and set(realization) == MATERIALIZED_KEYS:
            _identifier(realization['actual_revision_id'])
        elif realization.get('mode') == engine.MODE_REFERENCE and set(realization) == REFERENCE_KEYS:
            _identifier(realization['source_release_id']);_identifier(realization['source_actual_revision_id'])
        else:packages.conflict()


def entry_indicator_id(payload, entry):
    return entry['materialized_report_indicator_id'] if payload['schema_version'] == CANDIDATE_V1 else entry['successor_report_indicator_id']


def indicator_context(db, revision_id, report_indicator_id):
    revision = db.get(ActivityReportRevision, revision_id)
    report = db.get(ActivityReport, revision.report_id) if revision else None
    indicator = db.get(ReportIndicator, report_indicator_id)
    if not report or not indicator or indicator.report_revision_id != revision.id:packages.conflict()
    binding = db.get(PublicationIndicatorBinding, indicator.publication_binding_id)
    definition = db.get(IndicatorDefinitionRevision, binding.definition_revision_id) if binding else None
    identity = db.get(IndicatorIdentity, definition.indicator_id) if definition else None
    if not identity:packages.conflict()
    return engine.IndicatorContext(report.organization_id, report.id, report.period_id, revision.id, revision.revision,
        indicator.id, definition.indicator_id, identity.organization_id, definition.id, definition.sha256,
        definition.definition_json, revision.publication_id, revision.publication_sha256, revision.contract_version)


def candidate_snapshot(candidate):
    return engine.CandidateSnapshot(candidate.id, candidate.organization_id, candidate.period_id, candidate.resource_scope,
        candidate.report_key, candidate.activity_revision_id, candidate.payload_json, candidate.payload_sha256,
        candidate.manifest_json, candidate.sha256, candidate.predecessor_candidate_id)


def release_record(db, release):
    approval = db.get(ActivityReportApproval, release.activity_approval_id)
    if not approval:packages.conflict()
    return engine.ReleaseRecord(release.id, release.organization_id, release.resource_scope, release.report_key,
        release.major, release.minor, release.candidate_id, approval.id, approval.report_revision_id)


def reference_row(db, report_indicator_id):
    rows = db.scalars(select(ActivityRealizationReference).where(ActivityRealizationReference.successor_report_indicator_id == report_indicator_id)).all()
    if len(rows) != 1:packages.conflict()
    return rows[0]


def released_indicator(db, release, report_indicator_id):
    """One indicator exactly as a published release holds it; a reference is passed explicitly."""
    candidate = db.get(ReportCandidate, release.candidate_id)
    if not candidate or db.get(ReportCandidateState, candidate.id).state != 'published':packages.conflict()
    snapshot = candidate_snapshot(candidate)
    entry = snapshot.entry_for(report_indicator_id)
    context = indicator_context(db, candidate.activity_revision_id, report_indicator_id)
    record = release_record(db, release)
    realization = engine.entry_realization(snapshot.payload['schema_version'], entry)
    if realization['mode'] == engine.MODE_MATERIALIZED:
        actual = db.get(ActualRevision, realization['actual_revision_id'])
        if not actual or actual.report_indicator_id != report_indicator_id:packages.conflict()
        return engine.ReleasedIndicator(context, record, snapshot, engine.content_from_actual_revision(actual))
    row = reference_row(db, report_indicator_id)
    actual = db.get(ActualRevision, row.source_actual_revision_id)
    if not actual:packages.conflict()
    return engine.ReleasedIndicator(context, record, snapshot, engine.content_from_actual_revision(actual),
        engine.UnchangedValueReference(row.provenance_json, row.reference_sha256))


def source_indicator(db, predecessor):
    """The terminal materialized source the predecessor's content is flattened to."""
    if predecessor.mode == engine.MODE_MATERIALIZED:return predecessor
    source = predecessor.reference.payload['source']
    release = db.get(ReportRelease, source['release_id'])
    if not release:packages.conflict()
    return released_indicator(db, release, source['report_indicator_id'])


def predecessor_indicator(db, release, previous, key):
    """The immediate predecessor's indicator for one stable package key (draft report_indicator_id)."""
    payload = json.loads(previous.payload_json)
    found = [e for e in payload['entries'] if isinstance(e, dict) and e.get('report_indicator_id') == key]
    if len(found) != 1:return None
    return released_indicator(db, release, entry_indicator_id(payload, found[0]))


def canonical_contents(contents):
    """True when every entry is engine-canonical; otherwise the successor stays activity-candidate-1."""
    try:
        for content in contents:
            for entry in content['entries']:engine.content_from_entry(entry)
    except engine.ActivityReferenceError:return False
    return True


def eligible_reference(db, new, indicator, entry, release, previous, proposed):
    """Reference only when the engine proves equality with the IMMEDIATE predecessor release."""
    try:
        predecessor = predecessor_indicator(db, release, previous, entry['report_indicator_id'])
        if predecessor is None:return None
        source = source_indicator(db, predecessor)
        target = engine.SuccessorTarget(indicator_context(db, new.id, indicator.id), release.id, previous.id, previous.sha256)
        if not engine.check_reference_eligibility(target, predecessor, source, proposed).eligible:return None
        return engine.build_reference(target, predecessor, source, proposed), predecessor
    except engine.ActivityReferenceError:
        # Not provably unchanged: materialize, the always-correct v1 realization.
        return None


def realize(db, actor, new, indicator, entry, release, previous):
    """activity-candidate-2 entry: expanded content plus exactly one realization."""
    proposed = engine.content_from_entry(entry)
    found = eligible_reference(db, new, indicator, entry, release, previous, proposed)
    if found is None:
        actual = ActualRevision(report_indicator_id=indicator.id, revision=1, supersedes_id=None, value=contract.parse_actual(entry['value']),
            raw_text=entry['value'] or '', state=entry['state'], evidence_json=contract.canonical(entry['evidence']),
            explanation=entry['explanation'], deviation_json=contract.canonical(entry['deviation']), created_by=actor.id)
        db.add(actual);db.flush()
        realization = {'mode': engine.MODE_MATERIALIZED, 'actual_revision_id': actual.id, 'content_sha256': proposed.sha256}
    else:
        reference, predecessor = found;stored = reference.payload
        prior = reference_row(db, predecessor.context.report_indicator_id) if predecessor.mode == engine.MODE_REFERENCE else None
        db.add(ActivityRealizationReference(organization_id=stored['successor']['organization_id'],
            activity_report_id=stored['successor']['activity_report_id'], reporting_period_id=stored['successor']['reporting_period_id'],
            successor_report_revision_id=new.id, successor_report_indicator_id=indicator.id,
            predecessor_release_id=stored['predecessor']['release_id'], predecessor_candidate_id=stored['predecessor']['candidate_id'],
            predecessor_report_indicator_id=stored['predecessor']['report_indicator_id'], predecessor_reference_id=prior.id if prior else None,
            source_release_id=stored['source']['release_id'], source_report_indicator_id=stored['source']['report_indicator_id'],
            source_actual_revision_id=stored['source']['actual_revision_id'],
            persistent_indicator_id=stored['binding']['persistent_indicator_id'], definition_revision_id=stored['binding']['definition_revision_id'],
            content_sha256=stored['content_sha256'], provenance_json=reference.provenance_json, reference_sha256=reference.reference_sha256,
            created_by=actor.id))
        db.flush()
        realization = {'mode': engine.MODE_REFERENCE, 'reference_sha256': reference.reference_sha256,
            'source_release_id': stored['source']['release_id'], 'source_actual_revision_id': stored['source']['actual_revision_id'],
            'content_sha256': stored['content_sha256']}
    return dict(entry, successor_report_indicator_id=indicator.id, realization=realization)


def _same_content(actual, entry):
    return (actual.value == contract.parse_actual(entry['value']) and actual.state == entry['state']
        and json.loads(actual.evidence_json) == entry['evidence'] and actual.explanation == entry['explanation']
        and json.loads(actual.deviation_json) == entry['deviation'])


def _row_matches(row, reference, revision):
    stored = reference.payload
    return ((row.organization_id, row.activity_report_id, row.reporting_period_id, row.successor_report_revision_id,
             row.successor_report_indicator_id, row.predecessor_release_id, row.predecessor_candidate_id,
             row.predecessor_report_indicator_id, row.source_release_id, row.source_report_indicator_id,
             row.source_actual_revision_id, row.persistent_indicator_id, row.definition_revision_id, row.content_sha256)
        == (stored['successor']['organization_id'], stored['successor']['activity_report_id'], stored['successor']['reporting_period_id'],
            revision.id, stored['successor']['report_indicator_id'], stored['predecessor']['release_id'],
            stored['predecessor']['candidate_id'], stored['predecessor']['report_indicator_id'], stored['source']['release_id'],
            stored['source']['report_indicator_id'], stored['source']['actual_revision_id'], stored['binding']['persistent_indicator_id'],
            stored['binding']['definition_revision_id'], stored['content_sha256']))


def verify_v2(db, candidate, payload):
    """Re-resolve every entry from stored IDs only; a reference is re-verified through the engine."""
    manifest = json.loads(candidate.manifest_json)
    revision = db.get(ActivityReportRevision, candidate.activity_revision_id)
    if payload['report_revision_id'] != revision.id:packages.conflict()
    items = db.scalars(select(ReportIndicator).where(ReportIndicator.report_revision_id == revision.id)).all()
    ids = [e['successor_report_indicator_id'] for e in payload['entries']]
    if len(ids) != len(set(ids)) or set(ids) != {i.id for i in items}:packages.conflict()
    release = db.get(ReportRelease, manifest['predecessor_release_id'])
    previous = db.get(ReportCandidate, release.candidate_id) if release else None
    if not previous or candidate.predecessor_candidate_id != previous.id:packages.conflict()
    for entry in payload['entries']:
        indicator = db.get(ReportIndicator, entry['successor_report_indicator_id'])
        binding = db.get(PublicationIndicatorBinding, indicator.publication_binding_id)
        if binding.definition_revision_id != entry['definition_revision_id']:packages.conflict()
        actuals = db.scalars(select(ActualRevision).where(ActualRevision.report_indicator_id == indicator.id)).all()
        rows = db.scalars(select(ActivityRealizationReference).where(ActivityRealizationReference.successor_report_indicator_id == indicator.id)).all()
        realization = entry['realization'];content = engine.content_from_entry(entry)
        if realization['content_sha256'] != content.sha256:packages.conflict()
        if realization['mode'] == engine.MODE_MATERIALIZED:
            if rows or len(actuals) != 1 or actuals[0].id != realization['actual_revision_id'] or not _same_content(actuals[0], entry):packages.conflict()
            if engine.content_from_actual_revision(actuals[0]).sha256 != content.sha256:packages.conflict()
            continue
        if actuals or len(rows) != 1:packages.conflict()
        row = rows[0];reference = engine.UnchangedValueReference(row.provenance_json, row.reference_sha256)
        if not _row_matches(row, reference, revision) or row.predecessor_release_id != release.id:packages.conflict()
        predecessor = predecessor_indicator(db, release, previous, entry['report_indicator_id'])
        if predecessor is None:packages.conflict()
        prior = reference_row(db, predecessor.context.report_indicator_id) if predecessor.mode == engine.MODE_REFERENCE else None
        if row.predecessor_reference_id != (prior.id if prior else None):packages.conflict()
        target = engine.SuccessorTarget(indicator_context(db, revision.id, indicator.id), release.id,
            candidate.predecessor_candidate_id, manifest['predecessor_candidate_sha256'])
        effective = engine.resolve_effective_realization(target, reference=reference, predecessor=predecessor,
            source=source_indicator(db, predecessor))
        # Canonical equality (L3: raw_text and decimal spelling are not content identity).
        if (effective.content_sha256 != content.sha256 or effective.reference_sha256 != realization['reference_sha256']
            or effective.actual_revision_id != realization['source_actual_revision_id'] or effective.source_release_id != realization['source_release_id']
            or effective.predecessor_release_id != release.id):packages.conflict()
