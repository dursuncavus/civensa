# Phase 5B1 — Activity Report unchanged-value reference contract (engine v2 / S4)

Status: S4 integrated as a DISABLED backend slice on `feature/activity-reference-s4`.
The three engine files were imported deliberately from `ec2d431`
(`task/phase5b1-claude-activity-reference`, not cherry-picked) and adapted for E1 (lineage from the
manifest + `ReportCandidate.predecessor_candidate_id`, never duplicated in the payload).
S4 adds persistence (`activity_realization_references`, migration `e69c04e721a5`), the
reference-aware successor writer and the `activity-candidate-2` verifier
(`app/activity_reference_service.py`). The writer is OFF
(`report_workflow_service.ACTIVITY_REFERENCE_SUCCESSORS = False`) until readers resolve references.
The v1 reference schema of `8427b7d` / `a4e8a7a` is replaced and must not be used.

## Purpose

In a Phase 5B1 successor Activity Report revision (v1.1, v1.2, …) the effective realization of every
successor ReportIndicator is exactly one of:

- **A — materialized**: new content the host writes as a new ActualRevision, or
- **B — reference**: an immutable reference that is **flattened** to the terminal materialized source
  ActualRevision and **bound to the immediate predecessor release**.

Never both, never neither. The engine never searches: no "latest ActualRevision", no global fallback,
no name/code identity, no automatic rebase. It imports only `hashlib`, `json`, `re`, `dataclasses`,
`decimal` (asserted by a test).

## Inputs (built by the host from immutable rows)

| object | fields | host source |
|---|---|---|
| `IndicatorContext` | organization_id, activity_report_id, reporting_period_id, report_revision_id, report_revision_number, report_indicator_id, persistent_indicator_id, identity_organization_id, definition_revision_id, definition_sha256, definition_json, publication_id, publication_sha256, contract_version | ActivityReport, ActivityReportRevision, ReportIndicator, PublicationIndicatorBinding, IndicatorDefinitionRevision, IndicatorIdentity |
| `ReleaseRecord` | release_id, organization_id, resource_scope, report_key, release_major, release_minor, candidate_id, activity_approval_id, approval_report_revision_id | ReportRelease + ActivityReportApproval.report_revision_id |
| `CandidateSnapshot` | candidate_id, organization_id, period_id, resource_scope, report_key, activity_revision_id, payload_json, payload_sha256, manifest_json, sha256, predecessor_candidate_id | ReportCandidate (E1: `predecessor_candidate_id` column) |
| `ReleasedIndicator` | context, release, candidate, content, reference (only for a reference entry) | one indicator as a published release holds it |
| `SuccessorTarget` | context, predecessor_release_id, predecessor_candidate_id, predecessor_candidate_sha256 (all None for a first release) | successor ReportIndicator + host succession lineage |
| `RealizationContent` | canonical value, state, evidence, explanation, deviation | `content_from_fields`, `content_from_actual_revision(row)`, `content_from_entry(entry)` |

### Pure provenance checks (no DB)

`IndicatorContext`: positive int IDs; `sha256(definition_json) == definition_sha256`; definition has an
integer `year` (`reporting_year`) and the right `definition_contract_version` marker
(`app/activity_contract_service.py:104`); `identity_organization_id == organization_id`.

`CandidateSnapshot`: `sha256(payload_json) == payload_sha256` and
`sha256(canonical({'manifest', 'payload'})) == sha256`, i.e. `report_workflow_service.hash_content`
(`app/report_workflow_service.py:14`; byte parity tested). Manifest `report-manifest-1` names the
same organization, period and `activity_report` scope. Payload `schema_version` is
`activity-candidate-1` or `activity-candidate-2`, and its `report_revision_id` equals
`activity_revision_id`. E1: successor lineage is read from the hash-covered manifest
(`predecessor_release_id`, `predecessor_candidate_sha256`) and the `predecessor_candidate_id` column;
a manifest with `predecessor_release_id` requires all three. A v2 payload requires a successor manifest
and must NOT contain any lineage key (`LINEAGE_PAYLOAD_KEYS`).

`ReleasedIndicator`: release.candidate_id = candidate id; release, candidate and context share
organization and report key; candidate period = context reporting period;
`candidate.activity_revision_id = release.approval_report_revision_id = context.report_revision_id`;
payload publication/base equals the context. The indicator's entry is found by explicit key
(`materialized_report_indicator_id` in v1, `successor_report_indicator_id` in v2) and must occur exactly
once with the same `definition_revision_id`. The supplied content must equal the entry content.
**Entry mode and materialized ActualRevision ID come from the hash-verified payload, never from the
caller.** A materialized entry must not carry a reference; a reference entry must carry its
`UnchangedValueReference`, whose hash, successor section, binding, content hash, source ids and
predecessor id must equal the entry's realization record and the candidate's manifest/column lineage. That
predecessor must have an older release version.

What the engine cannot prove without DB access, and the host must: that the supplied rows are the ones
stored (IDs/hashes really belong to those rows), that the declared predecessor is the current release
in the succession lineage, and that the approval row exists and belongs to that revision.

## Content semantics (unchanged except numeric hardening)

- Value: `parse_actual` text form **restricted to ASCII digits** (`[0-9]`, `re.ASCII`), or `Decimal`.
  Arabic-Indic, Persian, Devanagari and full-width digits are rejected (the repository's `parse_actual`
  still uses Unicode `\d`, `app/activity_contract_service.py:348`; changing it is outside S2). Floats,
  booleans, ints, exponents, Turkish display text, NaN/Inf and > 6 decimals are rejected. `''`/`None` =
  blank; blank is never zero.
- All Decimal arithmetic (`abs`, `quantize`, `normalize`, difference-v1 subtraction) runs in an explicit
  local context (prec 50, ROUND_HALF_EVEN, traps InvalidOperation/DivisionByZero/Overflow). Results do not
  depend on the ambient decimal context (tested with prec 1/3/28, ROUND_DOWN, Inexact trapped).
- Canonical value text removes trailing zeros: `'12.5'`, `'12.500000'`, `Decimal('12.500000')` are one value.
- State rules, evidence rules (order significant, key order not), exact explanation, difference-v1
  deviation checks and size limits as in `save_actual` / `validate_actual`.
- **`raw_text` is not part of content identity** (unchanged decision; tested).
- Content hash = SHA-256 of canonical `{"schema": "civensa.activity-realization-content/v1", value, state, evidence, explanation, deviation}`.

## Eligibility: immediate predecessor only

`check_reference_eligibility(successor, predecessor, source, proposed)` reports every mismatch:

| rule | code |
|---|---|
| successor declares a predecessor (first release can only materialize) | predecessor_missing |
| supplied predecessor release / candidate id / candidate sha = successor's declared immediate predecessor | predecessor_mismatch |
| source entry is materialized (terminal row) | source_not_materialized |
| predecessor's flattened source = source (materialized predecessor ⇒ source is the predecessor itself) | lineage_mismatch |
| predecessor content = source content | lineage_mismatch |
| predecessor release newer than source release, same report key | release_order_invalid |
| same organization / ActivityReport / reporting period id / reporting year / persistent identity / definition revision / definition hash / target semantics / publication id+sha / contract version, against **both** predecessor and source | organization_mismatch, report_mismatch, reporting_period_mismatch, identity_mismatch, definition_revision_mismatch, definition_hash_mismatch, target_mismatch, program_base_mismatch |
| successor is a newer revision with its own revision and indicator rows | not_a_successor |
| proposed value / state / evidence / explanation / deviation = **immediate predecessor's** effective content | value_changed, state_changed, evidence_changed, explanation_changed, deviation_changed |
| proposed content valid for the successor definition | deviation_mismatch, deviation_definition_mismatch |

Skip-over is closed by three independent rules: the predecessor must be the declared immediate one;
content is compared with that predecessor; the source must be exactly that predecessor's flattened source.
For v1.0 X=5 → v1.1 X=6 → v1.2 X=5: passing v1.0 as predecessor fails `predecessor_mismatch`; passing
v1.1 with v1.0 as source fails `lineage_mismatch` + `value_changed`; v1.1 with itself as source fails
`value_changed`. If v1.1 re-entered X=5 as a new ActualRevision, v1.2 may reference v1.1's row only.

Chain: v1.1 references v1.0 (R1). v1.2 unchanged from v1.1 gets R2 with `source` = v1.0's ActualRevision
(flattened, one-hop reads) and `predecessor` = v1.1 with `entry_mode = reference` and
`predecessor_reference_sha256 = R1`. A reference cannot move forward: when v1.2 exists, a v1.3 successor
declares v1.2, so R2 (bound to v1.1) fails `predecessor_mismatch`.

## Reference schema v2

`UnchangedValueReference(provenance_json, reference_sha256)`, `reference_sha256 = sha256(provenance_json)`:

```json
{"schema": "civensa.activity-unchanged-value-reference/v2",
 "calculation_rule_version": "difference-v1",
 "successor":   {"organization_id", "activity_report_id", "reporting_period_id",
                 "report_revision_id", "report_revision_number", "report_indicator_id"},
 "predecessor": {"release_id", "release_major", "release_minor", "candidate_id", "candidate_sha256",
                 "activity_approval_id", "report_revision_id", "report_revision_number", "report_indicator_id",
                 "entry_mode", "materialized_actual_revision_id|null", "predecessor_reference_sha256|null",
                 "content_sha256"},
 "source":      {"release_id", "release_major", "release_minor", "candidate_id", "candidate_sha256",
                 "activity_approval_id", "report_revision_id", "report_revision_number", "report_indicator_id",
                 "actual_revision_id"},
 "binding":     {"organization_id", "activity_report_id", "reporting_period_id", "reporting_year",
                 "persistent_indicator_id", "definition_revision_id", "definition_sha256",
                 "target_semantics_sha256", "publication_id", "publication_sha256", "contract_version"},
 "content_sha256": "<source content hash>"}
```

Loading fails closed on missing/extra/null keys, wrong types, invalid hashes, non-canonical JSON, hash
mismatch, and these internal invariants: successor org/report/period = binding; predecessor content hash =
content hash; successor revision number > predecessor ≥ source; `entry_mode = materialized` ⇒ no
predecessor reference hash, predecessor release/candidate/approval/revision/indicator = source and
`materialized_actual_revision_id = source.actual_revision_id`; `entry_mode = reference` ⇒ predecessor
reference hash set, no materialized id, different and newer release than the source.

`verify_reference(reference, successor=, predecessor=, source=)` re-checks hash and structure, re-runs the
lineage and context rules, and requires every section to equal what the supplied objects imply.

## Resolution

`resolve_effective_realization(successor, materialized=…, reference=…, predecessor=…, source=…)`:

| input | result |
|---|---|
| materialized only (same indicator, difference-v1 valid) | mode `materialized` |
| reference + predecessor + source, verified | mode `reference`; content and `actual_revision_id` = flattened source; `predecessor_release_id` set |
| materialized + anything else | `ambiguous_realization` |
| predecessor/source without reference | `reference_missing` |
| reference without predecessor or source | `reference_source_missing` |
| nothing | `missing_realization` |

`resolve_successor_realizations(targets, materialized={ri: …}, references={ri: (reference, predecessor, source)})`
resolves each required indicator exactly once (gaps, overlaps, duplicates, unknown ids fail).

Errors: `ActivityReferenceError(ValueError)` with `.code`, `.message` (Turkish), `.field`, `.details`.

## `activity-candidate-2` (S4; written only behind the disabled flag)

Manifest: `successor_contract = "reference-successor-1"` (v1 keeps `"materialized-successor-1"`).
Payload: no lineage keys. Each entry keeps the expanded package content (value, state, evidence,
explanation, deviation, definition, `report_indicator_id`, …) and adds `successor_report_indicator_id`
and exactly one realization:
`{"mode": "materialized", "actual_revision_id", "content_sha256"}` or
`{"mode": "reference", "reference_sha256", "source_release_id", "source_actual_revision_id", "content_sha256"}`.
Package comparison strips only `successor_report_indicator_id` and `realization`.

## Host integration (S4)

1. Writer (`activity_reference_service.realize`, inside the S3C-2 assembly transaction and lock order):
   every successor ReportIndicator is always created. The predecessor is the manifest release
   (`current_source`), matched by the stable package key `report_indicator_id`; a returned attempt is
   never a predecessor or source. Unchanged content proven by the engine becomes a reference row;
   anything else (changed, ineligible, or not provable) gets a fresh ActualRevision. If any entry is not
   engine-canonical the whole successor stays `activity-candidate-1`. A package entry's
   `source_actual_revision_id` (`app/package_service.py:155-163`) is never used as a source. Initial
   1.0 releases are always v1.
2. `activity_realization_references`: append-only, server timestamp, `UNIQUE(successor_report_indicator_id)`,
   `UNIQUE(reference_sha256)`, chain CHECK, and on PostgreSQL `civensa_activity_reference_guard`:
   successor scope + current revision, seal (no candidate yet), XOR (no ActualRevision), current immediate
   predecessor release, predecessor entry exactly once, materialized-predecessor or reference-chain source,
   published older source with exactly one ActualRevision, definition/identity binding, provenance hash and
   every JSON section equal to the rows, active Strategy actor. `civensa_activity_reference_actual_xor`
   rejects an ActualRevision on a referenced indicator. SQLite: immutable + refusal triggers only (no batch).
3. `civensa_activity_successor_guard` (8ca1 body, widened): accepts only
   (`activity-candidate-1`, `materialized-successor-1`) or (`activity-candidate-2`, `reference-successor-1`);
   v2 entries must cover the revision exactly, materialized entries own exactly their one ActualRevision, and
   reference entries must match their row and equal the source ActualRevision content. A non-v2 candidate
   may not own reference rows.
4. `verify_materialization` dispatches on `schema_version`; v1 behaviour unchanged; v2 re-resolves every
   reference through the engine from stored IDs only.
5. Readers/approval/UI do not resolve references yet (later slice); the writer stays disabled until they do.

## Not verified / open

- Engine unit tests use synthetic release/candidate objects; real migrated rows are exercised in
  `tests/test_activity_references.py` (PostgreSQL 16, alembic head).
- `content_sha256` is a canonical-JSON hash the database cannot recompute; the DB instead compares the
  successor entry with the source ActualRevision at candidate insertion (numeric value/delta, exact text,
  jsonb evidence/deviation), and the Python verifier re-checks the hash.
- Two lineage checks (`predecessor content = source content`, `release_order_invalid` across releases) are
  defence in depth: other rules already reject every case found, so mutation tests cannot isolate them.
- "Applied => materialized" holds for every net-changed canonical field. A field left net-unchanged
  inside an applied request (or differing only in decimal spelling, L3) becomes a reference; S3C-2's
  net-change rule already treats such edits as no change. Product to confirm before readers are enabled.
- Writer fallback: an `ActivityReferenceError` or ineligibility materializes; a structural integrity
  failure of the predecessor rows (HTTP 409 conflict) aborts the assembly (fail closed).
- Concurrency: the successor guard takes the organization lock before its reference-ownership check, and
  the XOR trigger takes `FOR SHARE` on the report indicator the reference guard locks `FOR UPDATE`.
- Nexa approved L1 (flatten + bind immediate predecessor), L2 (dedicated immutable table), L3 (raw_text
  outside content identity; historical raw_text stays at its immutable source) and E1 on 2026-10-10.
