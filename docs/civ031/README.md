# CIV-031 — Bütçe Aktarma

This is the documented D-34 exception for approved PP data. A Strategy director,
or the holder of a current `approved_data_correction` delegation from that
Strategy director, can apply a referenced budget instruction without returning
the affected submissions. Approval states remain unchanged. Each affected
submission receives a `budget_reallocation` history event and a new revision
counter; existing PP package projections receive an administrative history event.
Immutable historical package snapshots and AR write restrictions remain intact.

## Data and interpretation

- `ReportingPeriod` has `year`, `status` and `template_status`; it has no council
  adoption field. `active` is a reporting-period state, not evidence of council
  adoption. Strategy explicitly selects before/after adoption for each operation.
- Before adoption, the required reference is **Başkanlık talimatı**. After
  adoption, multiple directorates require **Meclis kararı**. For one directorate,
  Strategy declares second-level functional-class transfer (**Encümen kararı**)
  or other transfer (**Başkan onayı**). There is no functional-class identifier
  on these budget rows; `program_group` is not treated as a functional class.
  Date, number and reason are mandatory, including for compensating operations.
- `AuthorityDelegation` previously had no authority kind. The additive column
  defaults existing grants to `director_approval`; new correction grants use
  `approved_data_correction`. Approval eligibility and migrated database guards
  exclude correction-only grants. Existing director/editor membership, time,
  account activity, grantor position and revocation checks still apply. The
  existing one-overlapping-grant-per-department reservation remains in force.
- Percentage input uses the directorate's **whole economic inside total** as its
  denominator, including protected lines. Conversion rounds half up to cents
  and is displayed before application. Distribution uses only eligible amounts.
- Personnel/SGK are stored as `personnel`/`sgk`; numeric `01`/`02` category prefixes
  are also protected. Contract-bound activities are protected independently.
  Further exclusions are recorded separately for each leg. Multiple legs for
  the same directorate require disjoint eligible cells/activities.
- Outside funding is off by default. When enabled, the directorate's effective
  internal percentage is applied to its selected economic outside total. That
  exact external TL delta is distributed separately across eligible economic
  and activity outside values. This preserves an existing cross-table difference
  even when eligible bases differ. The wizard explains this calculation and
  displays internal and external changes separately.
- Every distribution uses Decimal largest remainders with stable value-ID ties.
  Existing total rows are recomputed from inside + outside. Missing values are
  never assumed to be zero; inconsistent stored splits must be verified first.
- CIV-011 source amounts and source text are retained. An audited cumulative
  `budget_reallocation_delta` in source-resolution metadata separates the
  authorized adjustment from the original source comparison. Existing unresolved
  source differences retain their amount and remain visible; subsequent ordinary
  edits still require the existing explicit source-resolution process.

## Transaction and history

Preview and eligibility endpoints write nothing. A signed, actor-bound preview
expires after 30 minutes and binds the request, exclusions and complete relevant
scope hash. Application reads the whole HTTP body before acquiring any lock,
locks the organization/departments and relevant rows in deterministic order,
rechecks authority and compares the snapshot. All values, operation/line records,
package history and directorate notifications commit together.

`BudgetOperation` and `BudgetOperationLine` are append-only in the ORM and in
PostgreSQL/SQLite triggers. Reversal records a new operation with inverse legs
and `reverses_id`; every affected amount and provenance field must still match
the original result. A subsequent operation touching a value also blocks reversal,
even if that value was later restored. Reversal restores exact prior metadata as
well as cents. It has its own mandatory reference and reason.

The contract-bound flag has a separate own-directorate/Strategy endpoint and
before/after actor audit. It does not change a submission's approval status.
Only the synchronous, authorized budget/flag services bypass the ordinary
approved-data edit hook; ordinary edit and approval separation remain enforced.

The branch is rebased onto CIV-027 (`28be116`). The single migration is
`c031b1a2c3d4`, with parent `c0272027a001`; the PR still targets
`feature/authorization-workflow-phase5`. Downgrade retains all values, new
columns, history and immutability guards; re-upgrade is idempotent.

Directorate labels in the wizard, detail, notifications, audit and Turkish
errors use `structure_service.period_name` for the selected reporting period.
Changing the wizard period refreshes the selection labels. The signed preview
also includes the period profiles so structure changes invalidate old previews.

A period profile's `active_to` date is inclusive. After that date, new increases
(including compensating increases) are refused with the closure date and the
receivers recorded in the uncancelled structure decision. The operation date is
the database clock's current calendar date in Europe/Istanbul. A global inactive
flag caused by closure does not prevent reductions of that period's approved
budget. Existing ordinary inactive-department restrictions still apply when
there is no period closure profile.

## Screenshots

Synthetic data, local PostgreSQL and real Chromium/login/CSRF:

![Wizard preview](wizard-preview.png)

![Operation detail](operation-detail.png)

## Local verification

The new HTTP, concurrency, migration and browser tests are
`tests/test_budget_reallocation*.py`. Migrated acceptance runs separately from
metadata-created schemas, so application behavior is exercised with the real
PostgreSQL guards. Migration coverage includes populated SQLite/PostgreSQL
upgrade, immutable SQL history, lossless downgrade/re-upgrade and a single head.

Run with `CIVENSA_TEST_POSTGRES_URL` pointing to a **disposable local PostgreSQL
18 database**, `CIVENSA_CHROMIUM_PATH` pointing to Chromium when needed, and
`python -m pytest -q --require-postgres`. Set `CIVENSA_UI_SCREENSHOTS` to this
folder to regenerate the two screenshots. `test_migration.py` seeds the public
schema and requires a fresh disposable database for each repeated run.

The PR description records the actual focused and required regression results.
No live database, deployment or source bundle is involved. CI is intentionally
not polled, as requested for this task.

Fix round 1 runs the CIV-031 tests, structure-change tests, programme and
source-conflict tests, released-permission tests, package-approval parity,
workflow concurrency, live-pilot hardening and every migration test on local
PostgreSQL 18.6. The PR description records the final counts and results.

Fix round 1 result: **264 passed** across the complete requested selection,
including all 30 CIV-031 tests and every migration test. The initial focused
CIV-031 run also passed **30 tests**. Validation used PostgreSQL **18.6**;
SQLite migration variants and Chromium interaction checks are included.
The only warning was the existing Starlette TestClient/httpx deprecation.
