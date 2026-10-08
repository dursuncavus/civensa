# Authorization workflow foundation — phases 1–2

Base: canonical `origin/main` at `e03698fb447792dd607ce0e0d7b5adda2cb61e76`. The existing checkout was clean and the complete PostgreSQL baseline passed: 231 tests, zero skipped. No repository history was recreated.

## Scope and compatibility

Migration `0429caba7123` follows `a7c2d3e4f5a6`. It adds eleven tables: configuration, directorate memberships and membership events, delegation grants/revocations/events, final authority assignments/events, workflow events, field change events and notification recipients. It adds `notifications.delivery_mode`, defaulting existing records to `legacy`. Existing publication, definition-contract, Activity Report and approval data is neither rewritten nor backfilled with inferred authorities.

The new workflow remains disabled, enforced by a configuration constraint. `can()` permits only the explicit legacy action adapter; new-action `eligibility()` is a preview foundation, not runtime authorization. Existing business routes keep their current permissions. No phases 3–6 state machine, final candidate, revision request, deadline, email or new workflow UI is implemented.

## Authority and immutable history

Each directorate has at most two editor slots and one Director slot. Active membership uniqueness also prevents assigning the same person to multiple directorate slots. Assignments require an explicit formal basis; names and legacy roles do not infer an appointment. Missing Director appointments block new submission eligibility.

A Director may edit data and subsequently approve/send the package. There is no self-contribution prohibition. Field change history preserves old/new values, the immutable actor snapshot, context, source, reason and database timestamp. Strategy's independent second review belongs to the subsequent workflow implementation.

Only the original Director may grant delegation to an existing active editor. During an active interval, the delegate is the sole approval authority; the delegate cannot re-delegate. PostgreSQL database time governs eligibility, and a native range exclusion constraint prevents overlapping active grants, including concurrent inserts. Revocation appends immutable records and releases the reservation without changing the original interval. An inactive/removed delegate fails closed; the original Director does not silently regain authority before revocation or expiry.

Final authority requires a separate formal assignment. Strategy is not automatically Final Approver. Eligibility compares the final approval's assignment ID with the current assignment; a changed assignment cannot reuse the preceding approval. Actual final approval/publication transitions are not implemented in these phases.

Append-only history is protected by ORM hooks and database triggers. Identity-bearing authority projections can only be deactivated with accompanying immutable history. Downgrade deliberately refuses to discard authorization history.

## Transaction boundary and bootstrap

`atomic_change()` flushes business mutation, mandatory audit and internal notifications inside one savepoint; the caller owns the outer commit. A failure in any mandatory component rolls back all of them. Decimal values retain their exact representation; floating-point audit values are rejected. Ex-officio changes require a Strategy actor, a reason and a notification to the appointed Director.

Future callers must authorize and lock/revalidate the actual resource before invoking the foundation helper. Preview state and resource context must be server-derived, never trusted from request fields. These helpers are not exposed as new HTTP assignment or workflow endpoints.

`tools/authorization_bootstrap.py` is a narrowly scoped offline tool for a formally authorized operator who already controls the application environment/database. It requires `CIVENSA_AUTH_BOOTSTRAP=1`, an existing active operator ID and a formal basis. It records membership assignment/deactivation or final authority assignment with history. The environment flag is an intentional execution guard, not authentication. There is no Strategy self-assignment web UI. No production assignments were performed.

## Notification compatibility

New recipient-bound notifications are visible only to explicitly recorded recipients. Read state is per user and concurrent marking is idempotent. Legacy notifications retain existing role/department visibility. Historical shared `is_read` flags are preserved but are not attributed to individual users: without a recipient receipt, a legacy message appears unread. This can resurface old messages; it avoids fabricating who read them. The legacy operational aggregate counter remains a shared historical metric.

## Validation

Complete PostgreSQL suite: **275 passed, zero skipped**, including 44 authorization regressions. The only warning is the existing Starlette/httpx deprecation warning. Tests cover populated-database additive upgrade (including repeat upgrade), historical snapshot/hash preservation, concurrency, delegation, correction-compatible Director history, immutable records, transactional rollback, final assignment eligibility and recipient isolation. Python compilation, JavaScript syntax, bundle/source consistency and whitespace checks passed.

No browser acceptance test of a new workflow is claimed: these phases introduce no new workflow screens. No deployment, main merge or phase 3–6 implementation is authorized by this changeset. GitHub exact-commit CI is reported separately after push.
