# CIV-038 — III-A Malî Bilgiler

Depends on CIV-037 / PR #36. Legal basis: 2021 Usul ve Esaslar Yönetmeliği, art. 26(c)(1), EK-1 III-A. D-63 is preserved: years can be opened and draft structures prepared before Mali Hizmetler supplies actual data. No real 2026 financial data is seeded.

## Data model

| Table | Purpose |
| --- | --- |
| `ar_budget_rows` | Year/idare source facts, with separate economic expenditure, programme/subprogramme expenditure and revenue dimensions. Nullable `Numeric(20,2)` amounts; imported year-end amount is preserved separately from the calculation. |
| `ar_financial_policies` | Optional lower/upper realisation thresholds for the organisation/report year. Both default to null. |
| `ar_financial_entries` | Validated, scoped asset/liability, aid, audit and directorate explanation records. Decimal values are serialised as JSON numbers. |
| `ar_financial_statements` | Extensible statement slots; Bilanço and Faaliyet Sonuçları Tablosu are seeded. PDF/XLSX bytes, SHA-256, period/date, figures and required explanations. |
| `ar_financial_imports` | Immutable XLSX preview, source SHA-256, row errors, before/after differences, actor and source report revision. |
| Existing `ar_content_events` / `ar_document_freezes` | Audited changes and complete, hashed snapshots, including numeric financial tokens. |

Migration `c0382027a001` follows `c0372027a001`. It seeds statement slots for existing idare reports, preserves all existing indexes, and adds PostgreSQL/SQLite guards for all new tables. Downgrade refuses to discard any financial record or import history.

## Entry and access

The existing `/activity-sections/reports/{id}?code=III.A.1` through `III.A.4` slots contain the screens. The corresponding APIs live under `/api/activity-sections/reports/{id}/financial`.

Mali Hizmetler users and Strategy maintain idare facts/imports. Only Strategy sets thresholds. Directorates maintain their own budget explanations and aid/audit records, and can mark their aid/audit sections not applicable with a reason. Strategy can edit both scopes; all changes use the existing audit ledger. Birim views filter expenditure facts to the current directorate. Idare totals are calculated from the directorate rows, with unknown-value counts.

The PP reference uses the latest integrity-checked immutable publication for the report year, summing the matching directorate/economic category's **inside-budget** amounts across programme groups. Level-two references remain blank when the PP only contains level-one categories. Live PP draft changes cannot affect the reference. Publication ID and reference values are retained in the frozen AR; no PP value is posted into an actual field.

## Calculations and checks

- Year-end appropriation = initial + added − deducted; gross expenditure / year-end appropriation × 100.
- Net revenue = collections − refunds; net revenue / estimate × 100.
- Any unknown operand keeps the derived value unknown. Zero denominators produce no percentage. Totals disclose unknown source counts; aggregate percentages are withheld when their inputs are incomplete.
- Idare totals are derived from the same directorate facts. Economic/programme amounts are compared for every amount column, per directorate and for the idare. Messages show both values and the difference using Turkish number formatting.
- Parent codes and their children, or programme totals and their subprogrammes, cannot both contribute to one table.
- Imported year-end amounts are checked before apply. Manual inconsistencies remain visible as actionable completeness issues.
- Explanations become required only outside configured thresholds; boundary values are inclusive. Either the central explanation or the directorate's own explanation satisfies the row. Not-applicable status cannot hide errors in populated financial data.
- Missing statement files, periods/dates, explanations, asset amounts, aid amounts and separate internal/external audit entries appear in the CIV-037 completeness view and freeze gate.

## XLSX and files

Each budget screen provides a Turkish XLSX template and the directorate/programme identifiers needed to fill it. Upload creates an immutable preview; it changes no facts. Preview shows row-numbered Turkish errors and added/changed/removed values. Apply requires the exact report revision used by the preview. A new import replaces only that year's previously imported rows of the selected table; manual rows are preserved and conflicting manual keys block apply. Manual corrections retain import provenance and an audited before/after record.

Amounts accept native numeric XLSX cells or Turkish numeric text. Unknown codes/directorates, duplicates, negative disallowed amounts, formulas in numeric fields and corrupt workbooks are rejected. Uploads are limited to 10 MB, expanded XLSX content to 50 MB, and budget sheets to 5,000 rows. Statement uploads are PDF or XLSX; bytes are stored in the database and checked against SHA-256 on download. All request body/file reads finish before locking the report set.

Existing pre-CIV-038 frozen copies remain unchanged; financial controls render only when the snapshot includes financial data. Frozen reports created with CIV-038 retain facts, calculations, source revisions, statements, hashes, explanations, aid and audit entries. Database guards also protect statement file bytes.

## Validation and screenshots

The acceptance suite uses real login/session/CSRF with disposable PostgreSQL 16. Migration tests also cover SQLite. Browser tests use Chromium and exercise actual HTML responses and actions.

- [Entry screen](financial-entry.png)
- [Import preview with row error and changed values](financial-import-preview.png)
- [Completeness with threshold and classification differences](financial-completeness.png)

No live database connection, deployment, bundle generation, workflow flag change, merge or CI polling is part of this task.

Final focused verification: **111 passed** in 83.90 seconds, with one existing Starlette/httpx deprecation warning:

```text
python -m pytest -q --require-postgres tests/test_activity_financial.py tests/test_activity_financial_migration.py tests/test_activity_financial_ui.py tests/test_activity_sections.py tests/test_activity_sections_migration.py tests/test_activity_sections_ui.py tests/test_live_pilot_hardening.py tests/test_migration.py tests/test_contract_migration.py tests/test_release_readiness_migration_head.py
```

`python -m alembic heads` reports only `c0382027a001 (head)`. `git diff --check` is clean. Full-suite execution and CI waiting/polling were excluded as requested.
