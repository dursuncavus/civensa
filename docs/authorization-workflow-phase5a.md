# Authorization Workflow Phase 5A — disabled correction foundation

Base: exact fetched `origin/main` `af3c38e13bf215e11f0adbeb3eb82b32a1f3d839`; clean preflight, branch `feature/authorization-workflow-phase5`. Baseline real PostgreSQL: 504 passed, zero skipped. Phase 5B must continue on this same branch only after checkpoint review.

## Immutable request and lifecycle

Migration `375cefa60412` follows `264bdce59301` and adds RevisionRequest, RevisionRequestState, RevisionRequestEvent, RevisionCorrectionCycle and RevisionEditGrant. FieldChangeEvent receives a nullable `revision_request_id` FK on PostgreSQL. Existing rows/hashes/timestamps are not backfilled or rewritten. Downgrade refuses to discard history.

Only an active Directorate editor/director membership for the same organization/department may request against its exact package in the current published ReportRelease. Strategy and unknown legacy roles cannot act as the requester/editor. The request freezes source release/package revision, requester membership, canonical exact field paths, optional proposed values, mandatory reason and optional evidence metadata. Proposed values are informational and never automatically applied. JSON floating-point values are rejected; Decimal/raw-text semantics are preserved.

A requester may cancel only a requested request, with reason. Strategy may reject with reason, or accept after checking the current release and frozen candidate/package/decision/artifact integrity. Accepted requests reserve their requested cell scope; disjoint requests coexist, overlapping accepted/editing requests fail. Request bodies and events are append-only; state is a separate versioned projection requiring immutable audit for every transition. Stale-source operations fail with actionable 409 and retain historical request state; there is no automatic rebase or automatic state mutation on a failed operation. The extensible stale state is not an exposed transition in this checkpoint.

## Scoped grant and correction workspace

Strategy separately grants an accepted request. Immutable grants bind request, source release, correction cycle/package, exact allowlisted cells, active DirectorateMembership IDs, timezone-aware start/end and formal basis. Grants may narrow the request; they cannot expand it. Editing checks DB time (`start <= now < end`), active user/membership, editing request state, valid current source release and CAS package version/hash under locks. Delegation or role switching does not replace the actual editor recorded in history.

The first grant creates one immutable correction cycle and appends a PackageRevision copying the exact CandidatePackage revision that fed the release. Its predecessor points to that source revision. The package projection moves to `returned`; later disjoint grants reuse this branch and do not reset its content. Every edit appends another immutable PackageRevision, with request/grant/source-release provenance and actual actor/membership, old/new values and stable paths in immutable FieldChangeEvent/WorkflowEvent records. Director edits require the existing correction reason. There is no blanket Director self-contribution approval ban; reapproval itself belongs to Phase 5B.

Performance corrections touch only package working copies, never Publication/definitions/bindings. Activity corrections touch only package working copies, never released ActivityReportRevision/ReportIndicator/ActualRevision/freeze. Existing patch allowlists, blank-vs-zero/state checks, verified/evidence rules and calculated deviation semantics remain enforced. Calculated Activity deviation fields are recomputed from frozen definitions rather than trusted from the caller. Full snapshot approval validation remains available in package_service; this checkpoint does not re-enter the approval chain.

## Protection and transaction boundaries

PostgreSQL guards protect immutable request/event/grant/cycle history, original field scope, current release, active membership, legal audited state transitions and overlap reservations. Correction PackageRevision inserts require an effective grant and matching immutable edit audit; SQL changes outside granted paths fail. Derived Activity calculation fields are allowed only with the correct bound calculation. Correction package projection cannot enter the approval chain in Phase 5A. ORM update/delete protection covers new immutable history and the projection; controlled service transitions use audited Core CAS updates.

Organization/release, department/package, request and membership locks serialize source/grant/accept/edit checks. Overlap acceptance is also protected in PostgreSQL, including separate-connection concurrent attempts. Request creation, Strategy decisions and grant opening share a savepoint with their mandatory notifications; edits share a savepoint with audit and revision writes. Callers own outer commit. Request-created notifications go to Strategy; decisions notify requester/director; grants notify all authorized users and the director. No email/SMS or cron expiry is introduced.

The correction service is deliberately PostgreSQL-only: SQLite receives additive schema/immutable-history support but cannot execute the new correction seam without PostgreSQL security checks. Existing SQLite/legacy runtime remains available. Owner/admin privilege hardening remains deployment issue #4; application credentials were not changed.

## Checkpoint limits

New runtime workflow remains disabled. No HTTP routes, UI, PR, deployment or activation. No successor candidate, new release/version 1.1, unchanged-value references, new Activity materialization, correction completion, approval-chain reentry, Strategy ex-officio correction, Phase 5B/6 or policy/deadline features.

Current release checks use the existing release semantic-version ordering. A later release is simulated in a focused stale-base regression without implementing Phase 5B release creation. Published candidate/release/artifact and source Program/Activity historical bytes remain verified after correction package movement. Deployment blockers #4/#5 remain open; migration-test repeat collision remains a separate existing issue.

Validation uses one complete baseline locally, focused Phase 5A and relevant Phase 1–4 regressions during implementation, and exact-commit GitHub CI for the complete suite at checkpoint. No browser UAT is run or claimed for this backend-only change.

Local checkpoint evidence: Phase 5A-specific run 120 passed / zero skipped; relevant Phase 1–4 + Phase 5A run 343 passed / zero skipped; separate approval-parity run 48 passed / zero skipped. After final database lock/audit tightening, 32 focused scope/provenance/concurrency/atomicity checks passed (88 deselected, none skipped). Python compile, JS syntax, both bundle checks, whitespace, single migration head and fresh PostgreSQL/SQLite upgrades passed. Populated Phase 4 preservation is covered in the focused suite. The complete local suite was run only once, as baseline; exact-commit CI supplies final complete-suite validation.
