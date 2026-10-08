# Civensa v3.0.0

## Release highlights

- Safe Word import with preview, guarded apply, and reversible batches.
- Atomic activity mapping in the UI and through CSV roundtrip.
- Reversible mapping CSV batches with stale-state protection.
- Bulk department account CSV preview/apply and rollback for unused accounts.
- Account activation, immediate session revocation, and audited password reset.
- Department progress classification with missing-account visibility.
- Strategy-only operational dashboard, database latency, audit history, and CSV audit export.
- Automated Alembic schema upgrades with legacy pilot database baselining.
- Machine-readable release readiness gate for schema and data integrity.
- Production/QA regression coverage for roles, CSRF, empty-cost semantics, imports, mappings, accounts, audit, and persistence.

Operational warnings such as missing real department accounts or activities awaiting authoritative human mapping remain visible but do not masquerade as system-integrity failures.
