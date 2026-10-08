# Phase 5B1 — Activity Report unchanged-value reference contract

Status: IMPLEMENTED + focused-TESTED as an isolated, side-effect-free component
(`app/activity_revision_reference.py`, `tests/test_activity_revision_reference.py`).
NOT integrated: no existing file, migration, model, route or service was changed.
Base: `a919981874a3bfe5b309e659be51007ca67511f6`, branch `task/phase5b1-claude-activity-reference`.

## Purpose

In a Phase 5B1 successor Activity Report revision (corrected PackageRevision → successor
ReportCandidate → successor ReportRelease v1.1 / v1.2), most indicators keep the value that was
already released. The effective realization of every successor ReportIndicator must be exactly one of:

- **A — materialized**: new content the caller writes as a new ActualRevision, or
- **B — reference**: an explicit immutable reference to one historical source ActualRevision.

Never both, never neither. The engine never searches: no "latest ActualRevision", no global
fallback, no name/code identity matching, no automatic rebase, no mutable live-row reads. It imports
only `hashlib`, `json`, `re`, `dataclasses`, `decimal` (asserted by a test).

## Inputs (all built by the caller from immutable rows)

`IndicatorContext` — one ReportIndicator bound to its report revision, definition and Program base:

| field | source row |
|---|---|
| organization_id, activity_report_id | ActivityReport |
| report_revision_id, report_revision_number | ActivityReportRevision.id / .revision |
| report_indicator_id | ReportIndicator.id |
| persistent_indicator_id | IndicatorDefinitionRevision.indicator_id (IndicatorIdentity) |
| definition_revision_id, definition_sha256, definition_json | IndicatorDefinitionRevision (via PublicationIndicatorBinding) |
| publication_id, publication_sha256, contract_version | ActivityReportRevision (pinned base) |

Construction fails closed unless `sha256(definition_json) == definition_sha256`, the definition's
`definition_contract_version` marker matches (absent for 1.0, equal for 2.0/3.0 — mirrors
`activity_contract_service.definition_payload`, `app/activity_contract_service.py:104`), all IDs are
positive ints and targets parse without floats.

`SourceProvenance` — release side of the source: release_id, release_major, release_minor,
candidate_id, candidate_sha256 (ReportCandidate.sha256), activity_approval_id, actual_revision_id.
All required. A legacy approval-only source with no ReportRelease is therefore NOT referenceable in v1.

`SourceRealization(context, provenance, content)` — the explicit historical source. Its content must
itself be difference-v1-consistent with its own definition.

`RealizationContent` — canonical value / state / evidence / explanation / deviation. Build with
`content_from_fields`, `content_from_actual_revision(row)` or `content_from_entry(package_or_candidate_entry)`.

## Content semantics (unchanged from Civensa)

- Value: accepted forms are the `parse_actual` text form (`app/activity_contract_service.py:342`) and
  `Decimal` (Numeric(26, 6) reads, `app/models.py:406`). Floats, booleans, ints, exponents, Turkish
  display text and > 6 decimals are rejected (parity with `parse_actual` is tested). `''`/`None` = blank;
  blank is never zero.
- Canonical value text removes trailing zeros with Decimal arithmetic only: `'12.5'`, `'12.500000'` and
  `Decimal('12.500000')` are one value. Reason: package copies carry Numeric text (`actual_data`
  formats with `'f'`), while the source row was saved from typed text; `verify_materialization`
  already compares values numerically (`app/report_workflow_service.py:203`).
- State rules: verified needs a number and ≥ 1 complete evidence item; missing must be blank;
  needs_review is free. Same limits as `save_actual` / `validate_actual` (30 evidence items,
  50 000 / 10 000 / 10 000 characters).
- Evidence: each item needs non-blank `title`, `locator`, `source_revision`. List order IS significant
  (stored as entered; existing comparisons use list equality). Object key order is not (sorted keys).
- Explanation: compared exactly (no trimming).
- Deviation: must carry `calculation_rule_version = 'difference-v1'`, `target_definition_revision_id`,
  `delta`, `achievement_percent = None`. `delta` is canonicalized like the value. Against a context,
  `target_definition_revision_id` must equal the context definition revision and
  `delta == value − effective_target` (or `None` when unverified / no single verified target), exactly as
  `save_actual` derives it (`app/activity_contract_service.py:388-395`). Other deviation keys are compared
  exactly. `raw_text` is NOT part of the content (display/input text only).
- Canonical JSON: sorted keys, `(',', ':')`, `ensure_ascii=False`, list order kept; byte-identical to
  `activity_contract_service.canonical` for float-free input (tested). Content hash =
  SHA-256 of `{"schema": "civensa.activity-realization-content/v1", value, state, evidence, explanation, deviation}`.

## Eligibility (`check_reference_eligibility(source, successor, proposed)`)

All must hold; every failure is reported (not only the first), each with a stable code and an actionable
Turkish message telling the user to create a new realization instead:

| check | code |
|---|---|
| same organization | organization_mismatch |
| same ActivityReport | report_mismatch |
| successor is a newer revision, different revision/indicator row | not_a_successor |
| same persistent indicator identity | identity_mismatch |
| same IndicatorDefinitionRevision ID | definition_revision_mismatch |
| same definition SHA-256 | definition_hash_mismatch |
| same target semantics (year, kind, state, canonical value, effective target; not raw_text) | target_mismatch |
| same publication id / SHA-256 / contract version | program_base_mismatch |
| value / state / evidence / explanation / deviation unchanged | value_changed, state_changed, evidence_changed, explanation_changed, deviation_changed |
| proposed content valid under the successor definition | deviation_mismatch, deviation_definition_mismatch |

Target semantics are also covered by the definition hash; the separate check is defence in depth and
gives a clearer message.

## Reference provenance (`build_reference` → `UnchangedValueReference`)

`UnchangedValueReference(provenance_json, reference_sha256)`, `reference_sha256 = sha256(provenance_json)`,
`provenance_json` canonical:

```json
{"schema": "civensa.activity-unchanged-value-reference/v1",
 "calculation_rule_version": "difference-v1",
 "successor": {"organization_id", "activity_report_id", "report_revision_id", "report_revision_number", "report_indicator_id"},
 "source": {"activity_report_id", "report_revision_id", "report_revision_number", "report_indicator_id",
            "actual_revision_id", "release_id", "release_major", "release_minor",
            "candidate_id", "candidate_sha256", "activity_approval_id"},
 "binding": {"organization_id", "persistent_indicator_id", "definition_revision_id", "definition_sha256",
             "target_semantics_sha256", "publication_id", "publication_sha256", "contract_version"},
 "content_sha256": "<source content hash>"}
```

Loading (`UnchangedValueReference(...)`) fails closed on missing/extra/null keys, wrong types, invalid
hashes, non-canonical JSON or hash mismatch. `verify_reference(reference, source=..., successor=...)`
re-checks the hash, re-runs the context checks and requires every section to equal what the supplied
source and successor imply.

## Resolution

`resolve_effective_realization(successor, materialized=..., reference=..., source=...)` returns
`EffectiveRealization(mode, content, content_sha256, actual_revision_id, reference_sha256, source_report_indicator_id, source_release_id)`
with `value / state / evidence / explanation / deviation` accessors.

| input | result |
|---|---|
| materialized only (same report_indicator_id, difference-v1 valid) | mode `materialized` |
| reference + source, verified | mode `reference`, content = source content |
| materialized + reference or source | `ambiguous_realization` |
| source without reference | `reference_missing` |
| reference without source | `reference_source_missing` |
| neither | `missing_realization` |

`resolve_successor_realizations(contexts, materialized={ri_id: ...}, references={ri_id: (reference, source)})`
resolves every required successor indicator exactly once and rejects gaps, overlaps, duplicates and
unknown indicators.

`verify_source_against_candidate_entry(source, entry)` checks the source against the released
ReportCandidate payload entry (`materialized_report_indicator_id`, `materialized_actual_revision_id`,
`definition_revision_id`, content), i.e. the `activity-candidate-1` entries written by
`report_workflow_service.materialize` (`app/report_workflow_service.py:173`).

Errors: `ActivityReferenceError(ValueError)` with `.code`, `.message` (Turkish), `.field`, `.details`.
The caller maps them to HTTP (suggested: invalid input/content 422, provenance/hash/mismatch 409).

## Integration API for Codex / Nexa (PROPOSED — not implemented)

1. Successor materialization (Phase 5B1 equivalent of `materialize`): for each successor ReportIndicator,
   build `IndicatorContext` for the successor and, when a reference is wanted, a `SourceRealization` from
   the source release: ReportRelease → ReportCandidate (payload entry) → ReportIndicator → ActualRevision.
   Call `verify_source_against_candidate_entry` first. The source ActualRevision must be the
   `materialized_actual_revision_id` of that entry, never "the latest actual" (note: the Phase 3
   `create_package` copy uses `item['actuals'][-1]`, `app/package_service.py:148`; that pattern must not be
   reused for references).
2. Unchanged entry → `build_reference(source, successor, content_from_entry(entry))`; persist it.
   Changed entry, or any `ActivityReferenceError` → write a new ActualRevision (path A). Do not fall back silently.
3. Any reader (approval blockers, candidate verification, export, Final Approver view) resolves via
   `resolve_effective_realization` / `resolve_successor_realizations`, then applies the existing approval
   rules (`approve_report`, `activity_package_approval_blockers`) to the effective content. The engine does
   not decide approvability.
4. Proposed persistence (needs a migration — out of scope here): append-only `revision_value_references`
   with `successor_report_indicator_id` (unique), `source_report_indicator_id`, `source_actual_revision_id`,
   `source_release_id`, `definition_revision_id`, `provenance_json`, `reference_sha256`, `created_by`,
   `created_at`; ORM/PG immutability guards like other history tables; a DB-level guard that a successor
   ReportIndicator has an ActualRevision XOR a reference; indexed ID columns must equal the JSON.
5. `verify_materialization` currently requires exactly one ActualRevision per materialized indicator
   (`app/report_workflow_service.py:203`). It must learn the reference branch; the candidate payload
   schema (`activity-candidate-1`) needs a reference entry form (e.g. `reference_sha256` instead of
   `materialized_actual_revision_id`). This is a Phase 5B1 integration decision.

## Not verified / open

- No integration exists; the real 5B1 flow (Director/Strategy re-review, successor candidate, release
  v1.1) was not run. One focused test builds a real context from repository rows (SQLite and PostgreSQL 16).
- Floats anywhere in legacy evidence/deviation JSON make that source non-referenceable (fail closed → new record).
- `raw_text` exclusion from content identity is a design decision to confirm.
- Whether a reference may cross ActivityReports (currently rejected) and whether legacy approval-only
  sources should ever be referenceable (currently rejected) need product confirmation.
- The complete Civensa suite was not run (by instruction).
