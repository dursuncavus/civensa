# CIV-018 — Strategy master data and first-period setup

Strategy can maintain departments, period programmes/subprogrammes, rationale/goal and responsible departments from **Kurum Yapısı** in the Strategy sidebar. A dashboard with no reporting periods renders an **İlk dönemi oluştur** form, using the same validated creation function as `/api/periods`.

## Decisions and data preservation

- Department names are compared within their institution after Unicode NFC, Turkish `İ/i` and `I/ı` case conversion, and whitespace collapse. Institution row locks serialize application create/rename requests. Existing matching records are named in Turkish validation errors.
- Existing duplicate departments appear under **Aynı müdürlük olabilecek kayıtlar**. They are neither merged nor rewritten.
- Departments can exist with no strategic-plan link or period scope. Disabling a department preserves accounts, scopes, report data and history. New accounts (single/CSV), reactivated accounts, new scopes and new subprogramme responsibilities require an active department. Existing inactive scope/responsibility history remains available.
- Role/department changes use account closure and a new account, as explained on the users screen. No account reassignment feature was added.
- `SubProgramScope` connects a subprogramme to the existing `DepartmentScope`; no second department/period scope model was introduced. Responsibility assignment creates missing required scopes atomically, and zero/excluded scopes require an explicit change before assignment. Removing a responsibility preserves the department scope and records old/new assignment IDs in the audit log.
- Each new master-data mutation commits its audit entry, actor, database record timestamp and old/new JSON values in the same transaction. Renames never rewrite publication JSON or approved submission snapshots; HTTP regression tests compare their exact frozen contents.

## Migration

`b018a1c2d3e4` follows `a6c006e9b241`, leaving exactly one Alembic head. It adds `departments.is_active` with an active default and the `subprogram_scopes` association table. Department name uniqueness is enforced in the application; no database unique name constraint was added.

A migrated PostgreSQL test seeds the exact old schema with both `PARK VE BAHÇELER MÜDÜRLÜĞÜ` and `Park Ve Bahçeler Müdürlüğü`, upgrades, logs in and verifies both names in the warning panel. Downgrade to the previous head retains the additive schema, inactive state and responsibility data. Re-upgrade is idempotent.

Model-based historical migration fixtures add the lifecycle column solely to accommodate the current ORM; the CIV-018 migration test deliberately bypasses that fixture adapter and seeds raw old-schema rows.

## Screens

Synthetic, disposable PostgreSQL data; actual application templates, Chromium, login and CSRF.

![Institution structure and legacy duplicate warning](civ-018/institution-structure.png)

![Duplicate error retains attempted name](civ-018/duplicate-name-error.png)

![Subprogramme responsibility through period scope](civ-018/subprogramme-responsibility.png)

![First reporting period](civ-018/first-period.png)

## Local validation

All pytest commands used `--require-postgres` and a disposable PostgreSQL **16.2** server. The full suite is left to PR CI, as requested.

- Focused master-data, Word-import, programme, login-throttling, migration-head/readiness and publication-gate tests: **141 passed, 4 xfailed**. The xfails are existing Word-import regressions.
- Final master-data HTTP/CSRF, lifecycle, Turkish normalization, concurrency, old-schema migration/downgrade, frozen-name and real-source safety tests: **52 passed**.
- Final Chromium form/error retention, responsibility persistence and first-period flow tests: **2 passed**.
- Historical authorization and login-throttling migration compatibility checks: **2 passed**.
- `python -m compileall -q app`, `node --check app/static/app.js`, `git diff --check`: passed.

The browser tests can generate the screenshots again with `CIVENSA_UI_SCREENSHOTS` set to an output directory. Locally they use installed Chromium through `CIVENSA_CHROMIUM_PATH=/usr/bin/chromium`; CI uses its normal Playwright browser installation.

## Existing real 2027 source limitation

The supplied document is tracked on the base branch at `tests/pp2027_source_no_media.docx`, rather than `tests/fixtures/pp2027_source_no_media.docx`. The existing parser recognizes 64 indicator tables and 33 activity tables but produces **0 departments and 0 indicators**, with missing-label/unsupported-layout errors. A successful real-document import therefore cannot be claimed on this base branch.

The added real-source regression exercises preview/apply with actual login and CSRF: preview remains non-applicable, apply is rejected, and existing master/report data is unchanged. This preserves current safety behavior. The importer files were left untouched as required; successful official-layout ingestion remains dependent on the separate import work.

No live database, deployment, rollout flag, indicator/activity JavaScript save function or generated bundle was changed. Assumption: the installation already has its institution and Strategy account, as in the audited bootstrap scenario.
