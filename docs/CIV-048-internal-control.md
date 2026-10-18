# CIV-048 — İç Kontrol plan catalogue

The institution's internal-control catalogue is independent of reporting periods,
PP, Activity Reports, budget operations and account administration. The current
single-institution application has one active IC plan across all years.

## Schema and version history

Migration `c048a1b2c3d4`, directly after `c044a1b2c3d4`, adds only `ic_*` tables:
`ic_plans`, `ic_standards`, `ic_conditions`, `ic_actions`, `ic_action_parties`,
`ic_unit_aliases`, `ic_imports`, `ic_import_audits`. It seeds 18 standard codes
and their five components, without imposing general-condition counts.

Imports retain a filename, SHA-256 and parsed text JSON, never the workbook or
binary evidence. Every dry-run, commit and activation has append-only actor,
time, hash, counts and checklist history. A condition retains its version-local
standard title; the optional `Standart Başlığı` column supplies source titles.
The shared standard catalogue receives its first imported title. Later titles
remain available in each plan's conditions without rewriting earlier versions.

Every committed version is immutable, including drafts. Re-import creates a new
draft linked through `supersedes_id`; no previous rows are deleted. This stricter
append-only interpretation preserves IDs for monitoring and satisfies both draft
correction and active-plan replacement. The new version is activated explicitly.
Activation serializes through organization row locks and a partial unique index;
it archives the previous active plan in the same transaction. ORM guards reject
history edits; migrated PostgreSQL and SQLite tables additionally reject SQL
updates/deletes and insertion into already committed versions.

Downgrade moves Alembic back to `c044a1b2c3d4` while retaining IC tables, data and
guards. This follows repository policy against data-discarding downgrades. The
previous application ignores these additive tables. Re-upgrade is idempotent.

## Screens and routes

| Route | Access and behavior |
| --- | --- |
| `GET /internal-control` | Strategy upload and version list; directorates redirect to their actions |
| `GET /internal-control/template.xlsx` | Strategy template: Plan, Bilgi, Yönerge |
| `POST /internal-control/imports` | Strategy, 15 MB upload limit, dry-run audit and redirect |
| `GET /internal-control/imports/{id}` | Strategy checklist, unique unmatched names and mapping forms |
| `GET /internal-control/imports/{id}/validation.xlsx` | Strategy checklist export |
| `POST /internal-control/imports/{id}/mappings` | Strategy department/body alias and fresh dry-run |
| `POST /internal-control/imports/{id}/validate` | Strategy fresh audited validation |
| `POST /internal-control/imports/{id}/commit` | Strategy atomic draft creation; optional `supersedes_id` |
| `GET /internal-control/plans/{id}` | Strategy component → standard → condition → action view |
| `POST /internal-control/plans/{id}/activate` | Strategy activation |
| `GET /internal-control/our-actions` | Directorate active-plan actions, separate responsibility/cooperation lists |

The catalogue supports component, standard, responsible department and text
filters. Counts cover the whole plan. An all-departments party stays one marker
in storage, and contributes once to each department's displayed count and list.
Bodies are not expanded to directorates. Directorate queries filter on the server;
readers cannot open the institution catalogue, imports, reports or mutations.
Authorization uses `authorization_service.require_internal_control_access`,
existing session authentication and CSRF handling.

## Workbook rules

The first 13 column names match the task template exactly. Columns may be reordered
by their exact headers. `Standart Başlığı` is an optional additional column, because
the original 13 columns have no field for the source standard title. No standard
titles are invented. `Bilgi` contains title, start/end year, version and optional
approval date. The sheet limit is 20,000 data rows.

Blocking checks: invalid XLSX/OOXML, missing sheets or missing/renamed/duplicate
headers, unknown standard, component/standard or condition/standard mismatch,
duplicate normalized action code, no responsible party, unmatched unit,
missing action text or action code, invalid action-code syntax, empty condition
text, missing/invalid metadata or year range, ambiguous approval date and row
limit. Invalid workbooks receive an actionable checklist instead of partial data.

Warnings: a date/period cannot become an exact date, repeated condition text,
current-state text or standard title differs (first row retained with a traceable
warning), or action prefix differs from the condition. Raw values and all source
rows survive. An isolated year is valid but has no invented day/month. Continuous
due dates set `is_continuous`. Full dates accept ISO, `gg.aa.yyyy` and `gg/aa/yyyy`.
A condition with empty action columns creates no action.

Unit matching normalizes names using the existing department helper. Numbered,
newline and semicolon-separated owners/cooperators are supported. Known bodies
include Üst Yönetim, İç Kontrol İzleme ve Yönlendirme Kurulu and Çalışma Grubu.
Other bodies and unmatched department spellings need explicit reusable mapping.
Unmatched names appear once each. Exported strings are literal cells, including
values starting with `=`, so reports do not create executable Excel formulas.
Commit always validates the stored source again using current aliases.

## CIV-049 integration points and current limits

- Monitoring should reference stable `ic_actions.id` and retain `plan_id`.
- Extend `ensure_replaceable(db, previous)` to reject replacement once monitoring
  reports exist. Callers already lock the predecessor plan before this hook.
- Add six-month monitoring, directorate submission/review and report generation
  above the immutable catalogue; use append-only monitoring revision/event models.
- Evidence remains in EBYS. CIV-049 should store a text reference only.
- This part does not infer general conditions, owners or missing dates, and does
  not import arbitrary legacy municipal workbook layouts. Use the Civensa template.
- Aliases are immutable. Correcting an incorrectly chosen alias needs a later
  audited alias-revision workflow; this part creates new aliases only.
