# Authorization workflow — Phase 3 backend checkpoint

Base: `origin/main` at `aea134927d62d61b2f45d3bebe8275696b14fe30`, verified after fetch with a clean working tree. Complete PostgreSQL baseline: 275 passed, zero skipped. Branch: `feature/authorization-workflow-phase3`.

## Scope and rollout boundary

This implements the Directorate → Director → Strategy package backend for Performance Program and Activity Report. There are no new HTTP routes, screens, activation CLI or production permission changes. The foundation's database-enforced disabled configuration remains unchanged, and runtime `can()` continues to deny new workflow actions. Existing legacy routes and workflow remain active. Internal service entry points use centralized `package_eligibility()` with database-derived scope/state; they are not a replacement for the runtime rollout gate. A later reviewed rollout must connect and authorize routes explicitly.

No Phase 4–6 features are implemented: no final executive approval/release, publication artifact sealing, Revision Requests, edit grants, Strategy ex-officio editing, deadline enforcement, policy UI or email/SMS.

## Package content and provenance

Additive migration `153acbd48290`, following `0429caba7123`, adds three tables:

- `directorate_packages`: scoped source identity and current state/version/revision projection.
- `package_revisions`: immutable working-copy content, SHA-256, predecessor, real creator and reason.
- `package_decisions`: immutable action, reviewed revision/hash, linked immutable WorkflowEvent and optional delegation ID.

Performance packages initially capture the real department snapshot, including cards, indicators/targets, activities/costs, department costs and economics. Activity packages capture the selected current unapproved report revision, publication/hash, immutable definition bindings and latest actual source IDs. Working-copy changes do not overwrite live legacy rows, ActualRevision history or definition revisions. This deliberate separation permits backend testing without changing current production behavior. Later publication/report assembly must consume approved package snapshots explicitly; this checkpoint does not silently write them back into legacy data.

Every edit creates another immutable revision. Scope, identities, publication references and definition bindings cannot be edited. An explicit return/reopen creates a new editable revision with its predecessor and reason; the submitted snapshot remains intact. Corrections carry forward the package content explicitly through that predecessor relationship, not by altering or creating a legacy report revision.

Numeric values remain exact decimal text in JSON. Blank and zero remain distinct; actual verified state requires complete evidence. Calculated actual deviation uses the existing difference-v1 semantics. Existing Turkish presentation is unchanged; no new display is introduced.

## Decisions and Director contribution

Editable `draft`/`returned` packages submit to `director_review`; only the appointed Director or currently valid delegate can approve/send to `strategy_review`, or return with a reason. A Director needing a correction first reopens the submitted package with a reason, then edits the new revision, resubmits and may approve their own exact corrected snapshot. No self-contribution ban exists.

Director changes produce FieldChangeEvent records with old/new field values and an immutable WorkflowEvent actor/membership snapshot, timestamp, reason and revision/hash context. `package_detail()` exposes this history to Strategy without a role switch. Delegate approval does not obscure the original contributor.

Strategy may approve `strategy_review` → `strategy_approved` or return with a reason. A Strategy return creates a new editable revision. Resubmission requires fresh Director and Strategy decisions. This is an intermediate package approval, not an ActivityReportApproval or final executive/publication approval.

## Concurrency and atomicity

Mutations lock department, package and relevant users, refresh state, and verify expected version/hash. A guarded version increment provides a second CAS check. Source report currentness/approval and period editability are rechecked. Decisions use a fresh database timestamp after validation to re-evaluate delegation; the same timestamp selects the recorded delegation. Expired/revoked delegates cannot decide; inactive/removed delegates fail closed. Unknown actions/roles and cross-department private access deny.

Mutation + revision/decision + WorkflowEvent/FieldChangeEvent + mandatory recipient notification run in one savepoint; caller owns the outer commit. Audit or notification failure rolls back the complete change. Database triggers prevent snapshot/decision update/delete, protect source identity and verify decision hash/event bindings. UTC database timestamps remain unchanged in historical tables.

## Validation and limitations

Focused tests cover both package types, Director contribution, reasoned returns, repeat approvals, delegation expiry/revocation/inactivation, private access, conflicts, real competing transactions, audit/notification rollback, immutable DB records and populated Phase 2 → Phase 3 upgrades. The complete suite retains legacy v1/v2/v3/publication/Activity Report/ActualRevision immutability regressions. Complete PostgreSQL result: **336 passed, zero skipped**, including 61 Phase 3 cases. The only test warning is the pre-existing Starlette/httpx deprecation. Python compilation, JavaScript syntax, bundle/source consistency and diff checks passed. Exact-commit CI is reported with the checkpoint.

No browser UAT is claimed because no usable workflow screens were introduced. Deployment blockers #4 (runtime database privileges) and #5 (sidebar overlap) remain outside this task. No PR, merge or deployment is authorized. Future rollout/integration and Phase 4–6 behavior require separate approval.

## Approval validation parity correction

Director approval/send and Strategy approval now independently validate the exact locked PackageRevision content/hash before any state change, decision, audit event or notification. Internal Editor submission remains a review step.

Performance Program live validation and package validation share `_validate_department_records()`, preserving the existing business checks and messages. `department_package_snapshot()` additionally freezes subprogram/catalogue/responsibility facts under `validation_context`; the publication/book snapshot format is unchanged. `validate_department_snapshot()` uses only frozen content, hydrates exact Decimal values, and checks required fields, targets, relationships and all existing financial rules. Old package snapshots lacking frozen relationship context fail closed; they are neither reinterpreted from live rows nor rewritten. Explicit recapture into a new audited revision will require a separately reviewed recovery path before rollout if such pre-fix packages exist. No production workflow routes have been enabled.

Activity approval requires every bound department entry to be verified, numeric and fully evidenced, using the immutable report bindings and definition revisions. It recomputes difference-v1 deviation from the bound definition, rejects mismatched calculated fields, and requires an explanation for a non-zero delta. Client calculated values cannot bypass this check. No live ActualRevision values are used, and `approve_report()` remains unchanged.

Failures return a 409 response identifying the exact package revision/hash and actionable blockers. Validation does not mutate historical content, hashes or approvals. This correction adds no migration, model, permission or Phase 4 feature.
