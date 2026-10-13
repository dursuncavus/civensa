# Authorization Workflow A1-P1.1 — pre-activation recovery paths (disabled)

Base: `feature/authorization-workflow-phase5` at `65c5832428b68b2f74a5f21145a6020427511cc7` (A1-P1). Migration `f2b7c4d91e08` on `c5e8a1f0b247`; downgrade refuses to discard it. `ACTIVITY_REFERENCE_SUCCESSORS` stays False. No routes, UI or activation. Legacy Activity writers stay blocked for any report with a candidate or release (A1-P1 R1).

## Candidate lineage fields

| Chain | `predecessor_candidate_id` | Reworked attempt | Release link |
|---|---|---|---|
| Initial Activity chain (Phase 4) | the previous, returned attempt | manifest `reworks_candidate_id` / `reworks_candidate_sha256` (required for every new rework since A1-P1.1; optional on older rows) | none |
| Successor chain (S3B/S3C-2/S4) | the published predecessor's candidate | manifest `reworks_candidate_id` / `reworks_candidate_sha256` | manifest `predecessor_release_id` |

`reworks_*` has one meaning in both chains: the returned attempt this candidate reworks. Both keys are inside the candidate hash. On PostgreSQL `uq_activity_successor_rework` (despite its name) allows at most one rework per returned attempt in both chains; on SQLite the same property comes from the `activity_initial_rework_lineage` trigger (the predecessor must be the latest, returned candidate). A first candidate has sequence 1, no predecessor and no `reworks_*` key. One Activity revision belongs to at most one candidate (`uq_report_candidate_activity_revision`).

## R10 — returning an unpublished first candidate after final approval

The current active, non-Strategy final authority may return an Activity candidate from `final_approved` with a reason while no release exists for that report. Performance Program candidates never leave `final_approved` this way. The final_approve decision and its ActivityReportApproval freeze stay as immutable history; the returned candidate is terminal.

Rework is explicit:
1. Strategy reopens each package of the returned attempt with `strategy_reopen` and a reason (only while that attempt is the report's latest candidate, no release exists and the report revision is still the attempt's materialization). The event records `initial_rework_candidate_id/sha256`; the package gets an append-only exact-copy revision and moves to `returned`.
2. The department corrects the package; director and Strategy re-approve it through the normal transitions.
3. Strategy assembles a NEW candidate from the same source revision with `predecessor_candidate_id` = the returned attempt. It materializes a fresh ActivityReportRevision directly after the attempt's, records `reworks_*`, and needs a fresh final approval (a decision or release can only carry the freeze of its own candidate's revision).

Only one rework lineage exists: no package can be opened on a candidate's own (materialized) revision; `create_package` refuses it with a 409 that names the candidate. Before A1-P1.1 the returned candidate's revision could carry new packages (Phase 4); such packages, if any exist before the upgrade, can no longer be assembled and the attempt's own packages must be reopened instead.

The final_approved return of a first candidate and its rework are PostgreSQL-only (on other databases `final_decision` refuses the return with a 409), so a return can never leave a report that cannot be reworked.

PostgreSQL enforces:
- the lineage on insert (period, source, departments, package set and the next materialized revision of the attempt);
- at commit (deferred), that a new initial candidate has its state, its `candidate_assembled` event, exactly the package bindings of its manifest and one package per required department, and that a first candidate materializes the revision right after its source;
- on each binding, that it is the package's current `strategy_approved` revision named in the manifest;
- for a candidate-bound initial package, that it leaves `strategy_approved` (or changes its revision or report revision) only through the audited reopen, that a returned package only gains append-only revisions, and that every other state change carries its exact package decision on the prior revision;
- the reopen provenance on the package decision, the return predicate on the state change, and the freeze binding on decisions and releases.

SQLite has the lineage (period, source, departments, materialization chain), unique revision, terminal-state, exact-return (current active non-Strategy authority of the same organization, `final_return` event, non-blank reason) and release-freeze triggers; package reopen stays PostgreSQL-only. The SQLite exact-return trigger exempts successor candidates, which SQLite refuses anyway.

## TE-1 — direct cycle reopen for a new accepted request

When a correction package is `strategy_approved` in a current-release cycle and a NEW request (Q2) is accepted but not yet granted, Strategy calls `revision_workflow_service.reopen_cycle` with a reason. No dummy candidate is created. The request-side `correction_cycle_reopened` event records the cycle, package, previous and resulting revision/hash and any other request's grant that is still in force (`resumed_grant_ids`); the package-side `strategy_reopen` decision references that event and Q2. The package gets an exact-copy revision (not a semantic correction) and moves to `returned`; Q2 then receives its own new grant through `open_grant`.

The reopen is refused for a non-Strategy actor, without a reason, for any request that is not `accepted` or already granted, for a superseded release, while a live successor exists, while another accepted/editing request claims an overlapping cell, and when the package is not `strategy_approved`. Closed requests and their grants are never touched. A grant can only join a `returned` package. The reopen notice goes to the directors, the requester and the participants of every resumed grant.
