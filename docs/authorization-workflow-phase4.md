# Authorization Workflow Phase 4 — disabled backend

Base: exact `origin/main` `1b25f3e52ad72ebd746001ab1cf5626ec4d031d0`, fetched and verified with a clean checkout. Branch `feature/authorization-workflow-phase4` was created from that ref. Baseline PostgreSQL suite: 384 passed, zero skipped.

## Scope and model

Migration `264bdce59301`, following `153acbd48290`, adds six tables: ReportCandidate, ReportCandidateState, CandidatePackage, ReportDecision, ReportRelease and ReportArtifact. Content/history and state projection are separate. Immutable records have ORM and PostgreSQL update/delete protection; state changes require legal transitions, a version increment and matching immutable audit context. PostgreSQL insert guards verify hashes, decision bindings and release targets. Existing history is not backfilled or rewritten; downgrade refuses to discard it.

The workflow remains database-disabled. Runtime `can()` denies new actions; no HTTP routes, UI, activation flag or administrative UI was added. Internal backend authorization is centralized and rechecked after locks. Legacy flows remain active. No Phase 5/6, correction requests/grants, ex-officio changes, deadline/policy UI or external messaging is implemented.

## Assembly and provenance

Only Strategy assembles a candidate. Each selected package must be current, strategy_approved, in the same organization/period/report, independently snapshot-validated and linked to its exact immutable Strategy decision/event. Duplicate or missing departments fail closed. Program assembly requires explicit scope for all organization departments and an approved package for each declaration, including zero/excluded declarations; no unreviewed department content is substituted. Activity scope is the exact department set of the selected report revision's immutable bindings. The required scope is frozen in the manifest.

Program content uses the canonical schema 5.0 with definition contract 3.0 for new definitions. Department/card/indicator/finance content comes exclusively from package JSON; `validation_context` is excluded from publication payload. Strategy-owned general sections and complete catalogue metadata are captured once at assembly, with linked catalogue facts checked against package provenance. Explicit period-row identity links prepare immutable IndicatorDefinitionRevision records before final review; no name/code matching occurs. Existing definition contracts v1/v2/v3 are unchanged.

Activity assembly creates a dedicated unapproved ActivityReportRevision, ReportIndicator and ActualRevision set using only package values/evidence/explanations/deviation. Source and materialized IDs are explicit in candidate JSON; manifest binds package revisions/hashes and source report revision. The real assembly actor is recorded, with original contributions traceable through package history. There is no latest-Actual fallback or silent old-actual inheritance. Additional inserts into the materialized set are sealed at the database level as soon as its candidate exists; ActivityReportApproval is still absent until final approval.

Candidate sequence and predecessor references are serialized per organization. An assembling candidate can request final review; a returned candidate is terminal and immutable. A successor requires an explicit predecessor and separately assembled candidate. It does not edit/reopen packages or introduce the Phase 5 correction process.

## Final approval and release

Normal states: assembling → final_review → final_approved → published. Final return: final_review → returned_to_strategy with a mandatory reason. Only the current active formal FinalAuthorityAssignment permits final decisions. Strategy is not automatically Final Approver. A separately formally assigned Directorate user may decide. Actor, assignment, exact candidate hash, reason, database timestamp and mandatory notifications are immutable/audited.

If the assignment changes after approval, release fails closed. The new current authority can approve the same unchanged candidate again while its projection remains final_approved; prior decisions remain untouched. For Activity Reports, the original immutable data-freeze row remains and the new ReportDecision supplies current authority semantics. A person acting as current Final Approver cannot also perform release, including a formally assigned Strategy account.

Only Strategy releases. Program release creates Publication from the exact candidate publication JSON/hash and its prepared definitions/bindings; no live-row rebuilding occurs. Activity release references the exact candidate ActivityReportApproval, created only during final approval. ReportRelease binds exactly one target and semantic version 1.0. Row locks/CAS and unique constraints prevent duplicate publication/release; a retry with current published version returns the same verified release. Stale expected versions conflict.

## Sealed artifact and transactions

The sealed artifact is canonical UTF-8 JSON stored directly in ReportArtifact, with release ID, payload/provenance, immutable object version, serialization version, exact SHA-256 and byte size. Candidate SHA covers payload plus manifest; Program Publication SHA covers the canonical payload bytes specifically. Verification checks artifact content against the release and candidate, not only against its own hash.

No PDF or external object-storage reference is invented. A durable deterministic PDF/storage integration is deferred. Later rendering is not the sealed original unless bytes/hash match.

Each assembly, decision and release uses a savepoint containing all business mutation, immutable audit, mandatory recipient notification and freeze/release/artifact writes; callers own outer commit. Authority assignment changes serialize on the organization lock. Final decisions/publication reauthorize under locks, using database timestamped history. Real PostgreSQL tests use separate connections and barriers for concurrency. SQLite is not claimed as concurrency evidence.

## Validation and remaining limits

Only focused Phase 4 tests run during implementation, followed by one complete final PostgreSQL suite. Results and exact-commit GitHub CI are reported at checkpoint. Populated Phase 3 upgrades are tested, along with historical rows, legacy behavior, ORM/DB immutability, source snapshot consistency, authority replacement and transaction rollback.

No browser UAT is performed or claimed: there are no new screens. Deployment blockers #4 (database role privileges) and #5 (sidebar overlap) remain outside scope. The approved design is represented by the earlier design chat's authority/freeze/history rules and the explicit current Phase 4 work order; the original cloud-only Markdown file is not copied into this checkout. No PR, merge or deployment is authorized.

## Phase 4 review blockers

Final Authority viewing/decisions depend only on an active user and the current active organization assignment, regardless of legacy `User.role` (including executive accounts). Strategy viewing is separate; assembly, review request and release remain Strategy-only. Current Final Authority cannot release even with legacy Strategy role. The disabled runtime adapter and legacy permissions are unchanged.

Current `strategy_approved` package state/current revision are assembly gates only. Frozen candidate verification uses its exact immutable revision/hash, Strategy decision/event and stable package organization/period/department/resource/source identity, plus snapshot business validation. Later package state/revision movement does not invalidate frozen candidates or released artifacts. Decision events are independently checked against the bound revision/hash and package identity. Tests simulate later audited projection movement without adding any Phase 5 transition.
