# History-preserving staging / performance integration

## Preflight and provenance

Remote refs were fetched and verified exactly before any branch was created:

| Ref | SHA |
| --- | --- |
| origin/main | f6e18af58dfeab925faf8235514e2a3c44834f22 |
| origin/staging | b3a4ad1f8f2435aae6ddc8716d468ddff915ba66 |
| origin/feature/performance-activity-contract | 7342a0ff6782531992a7d9e0546e83ca73ad9259 |

The working tree was clean. Existing local heads were recorded:
`main` a18adcf253ca0a0afda559e6b471b32c873e60de (not GitHub main),
`checkpoint/performance-baseline-2026-10-06` and `work/performance-program-qwen`
e2deb12ae70a9ac75568adf00af2c1f4ec8d9c0e, and the feature head above.
No existing local branch was moved. The new integration branch starts at the
verified staging head; its pending merge uses the verified feature head with
`--no-commit --no-ff --allow-unrelated-histories`.

The October 1 staging clone failed authentication. The fallback reconstructed
release source from a bundle and ran git init, creating independent root
2eaad87eebeabe1baf300b5af92d8da9986acd39. Source extraction retained files but not
parent history. Staging retains the original main ancestry (main is its ancestor).
This deliberate two-parent merge connects both histories without rewriting them.
The final PR must also be merged with a merge commit, not squash/rebase, so those
parents remain reachable from main. Future work must start from updated GitHub
main after final approval, not the stale local branch named main.

## Complete-tree reconciliation

Comparison classified all tracked blobs: staging-only 27, feature-only 24,
shared identical 55, shared different 19. Every add/add conflict was inspected
against the audited classification and resolved; there are no unresolved conflicts.

- **Application and behavior:** all feature app files, templates, seeds, imports,
  number handling, immutable contract semantics, roles, and audit behavior are
  retained exactly. No obsolete business logic or old invented demo values restored.
  All feature-only application/docs/tests remain; the 19 shared changed files use
  the feature versions before runtime packaging is rebuilt. No architecture redesign.
- **Migrations:** identical staging chain through e5a0b1c2d3e4 retained, followed by
  feature f6b1c2d3e4f5 and a7c2d3e4f5a6. No migrations or historical data rewritten.
- **Requirements:** pinned feature/staging requirements and dev requirements are
  identical and retained. No dependency upgrades.
- **Dockerfile:** replaced old Python 3.13 / app-only layout with Python 3.12 (CI
  parity), full app, migrations, alembic.ini and sitecustomize.py. Uses existing
  application startup migrations via python -m uvicorn. Removed baked-in session
  secret; demo seed remains off. PYTHONPATH=/app ensures provider normalization
  also loads for command entry points. .dockerignore uses an allowlist to exclude
  local DBs, secrets, caches, Git history and QA fixtures from build context.
  Runtime/admin role separation remains deployment issue #4; startup behavior is
  unchanged, and no deployment credentials were changed.
- **sitecustomize.py:** staging helper retained byte-for-byte. app/db.py and
  migrations/env.py consume DATABASE_URL directly; psycopg 3 is installed, not
  psycopg2. Provider postgres:// and postgresql:// URLs therefore require this
  helper. Explicit psycopg URLs remain unchanged. New subprocess tests verify
  all three schemes in source and extracted deployment bundle without contacting
  any external database. README documents PYTHONPATH for source/CLI entry points.
- **Bundle tooling:** deterministic feature builder retained, with the runtime
  helper added to the bundle. All eight parts/manifest rebuilt from current source.
  Staging check_bundle.py had a v3 assertion; qa_bundle_check.py had a literal
  invalid newline escape and v2.2 assertion. Replaced these obsolete gates with
  one maintained manifest/hash/exact-source/ZIP/Python-syntax check and a compatible
  qa_bundle_check.py entry point; no stale version assertion remains.
- **Manual QA/release scripts:** all 13 regression scripts plus smoke_test.py are
  preserved byte-for-byte under tools/legacy-qa with explicit historical/non-release
  status. They assume old pilot accounts, login redirects, periods and migration
  versions, and some mutate data/passwords. They were not executed against a live
  service. Current pytest fixtures supersede these as the supported release gate.
- **Old deploy copy:** removed the partial deploy/app copy and unpinned deployment
  requirements from the active tree. No tracked consumer references deploy/.
  These files were stale and do not contain the full current application/migrations;
  restoring them would create a second application authority. They remain preserved
  in the staging parent history. Use current root source/container/bundle only.
- **Release documentation:** original v3 and v3.5 notes retained together with
  existing v4/v4.1/v4.2 notes and RELEASE_V5.md. README now documents supported
  runtime/validation, intentional history bridge and deployment blockers.
- **Environment and ignores:** .env.example is placeholder-only, documents production
  secret/cookie requirements without embedding a default production credential.
  Added .DS_Store, *.py[cod], local .env.* exclusions (example explicitly included).
- **CI:** existing feature workflow retained exactly, including Python 3.12,
  PostgreSQL 16 and mandatory --require-postgres; no existing gate removed.

## Automated validation before merge commit

- Complete existing suite plus 3 provider-runtime regressions: **231 passed,
  0 failed, 0 skipped**, 24.75 seconds, one existing Starlette/httpx deprecation warning.
- Fresh disposable PostgreSQL database; --require-postgres enabled. PostgreSQL-marked
  contract/concurrency/migration tests ran; existing SQLite unit fixtures remain
  as designed. The known repeated-run populated-DB collision was not repaired.
- Fresh UI PostgreSQL database migrated through all six revisions to a7c2d3e4f5a6;
  application startup also completed against that database.
- Python compilation: app, migrations, tools, tests, runtime helper and both checkers.
- JavaScript syntax: app/static/app.js passed node --check.
- Both bundle check entry points passed, 56 files, SHA-256
  628a7e2af30e2fad5f82c83125e59be821ece209fec9bb00fce8ac94ec8bda27.
- Working/index whitespace checks passed; application and CI files compared
  byte-for-byte to feature; historical QA scripts compared byte-for-byte to staging.
- Dockerfile/content/startup reviewed, but Docker CLI is unavailable on this host:
  no actual container build/run is claimed. Source and bundled provider startup
  behavior is tested; a container smoke test remains a pre-deployment check.

GitHub CI for the final branch commit is reported on the PR after push; this
pre-commit document does not claim a future CI result.

## Live browser UAT on reconciled tree

Executed against localhost:8767 and a fresh, disposable PostgreSQL database.
Three prepared test accounts: Strategy, Park Directorate, Temizlik Directorate.
Published program fixtures v1/v2 were prepared via the publication service; report
creation, actual entry, approval and correction were exercised through the UI.
This is not a production smoke test or a complete program-publication workflow test.

| Flow | Observed result |
| --- | --- |
| Strategy and both Directorate logins | Correct module selection and role navigation |
| Performance Program dashboard / department / card | Opened normally; shared explanation, method/source and Turkish targets visible; review fields disabled where expected |
| Create Activity Report from v1 | v1/year/report revision clearly displayed |
| Approve incomplete report | All seven indicator blockers shown together; no approval |
| Directorate scope | Park sees six own indicators; Temizlik sees only its one; no approval controls |
| Blank versus zero | Blank saved as Eksik, then zero as İncelenmeli in separate history records |
| Evidence / verified | Verified without evidence rejected with actionable source-or-review instruction |
| Invalid value abc | Turkish numeric instruction; value, state, source fields, explanation/action preserved |
| Actual evidence and history | Sourced actual saved; prior blank/zero retained; entering user and Turkey timestamp shown |
| Numbers | 12.500, 12.500,23, 1,75, 0, -12.500,23, 12.345.678.901.234.567.890,123456; deviation 12.498,48; source values remain Decimal |
| Same-year duplicate | Explicit existing-report/new-revision guidance |
| Strategy approval | Completed after all seven sourced actuals; approver and Turkey timestamp visible; actual edit forms absent |
| New publication after approval | Understandable warning; old report remains on v1 and original target/definition |
| Correction reason | Empty submission blocked by browser required-field message; reasoned correction creates revision 2 on v2 |
| Publication differences | Explanation, calculation method, source and target old/new values displayed |
| New revision | All seven actual fields blank; explicit no-copy message |
| Old revision/history | Original v1 values, evidence, definition and approver readable; no editable actual forms |
| Directorate after approval | Only own indicators; old approved report has zero actual edit forms |

Supplementary authenticated HTTP probes (separate from browser observations):
foreign Directorate write rejected 403; old approved revision write rejected 409.
Automated regression tests also cover backend immutability and missing-reason API rules.
Browser screenshots saved locally in /tmp/civensa-integration-uat-20261008.

No new integration-related High/Blocker issue was found. Activity Report flows are
acceptable for PR review. Existing sidebar overlap is still reproducible and is
explicitly excluded from deployment readiness under issue #5.

Remaining Medium UX: latest actual is behind collapsed history on read-only pages;
saving one indicator can discard unsaved edits in another indicator's form.
Remaining Low UX: report list lacks approval badges; newer-publication warning has
no direct revision action. No permissions were changed; role separation decision
remains with Strategy Development.

## Remaining risks / deployment blockers

- [#4](https://github.com/dursuncavus/civensa/issues/4): runtime DB role ownership /
  TRUNCATE / schema privileges; separate privileged migration/admin role required.
- [#5](https://github.com/dursuncavus/civensa/issues/5): sidebar logout overlaps
  password-change control; required before deployment. Not fixed in this integration.
- docs/issues/postgres-migration-test-repeat.md remains open separately.
- Real container smoke test not performed (Docker CLI unavailable).
- Final main PR must preserve merge ancestry; squash/rebase would defeat this bridge.

No force push, rebase, squash, existing-branch deletion, deployment, or main PR
merge is part of this task.
