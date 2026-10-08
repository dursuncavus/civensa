# Confirmed Activity Report acceptance fixes

Starting checkpoint: ab0aa8ff413035f1a262987c5dfae68841e321e7 on feature/performance-activity-contract.

## Behavior

- New publications use definition contract **3.0**. A nonblank Indicator explanation overrides the shared ReportCard explanation; otherwise the validated frozen card supplies it. Calculation method/source inheritance remains unchanged. Contract 1.0 and 2.0 builders preserve their old interpretations. No historical JSON, hash, binding, definition, or timestamp is rewritten. No schema migration is required.
- Verified actuals now require at least one complete evidence record at write time. Source-free review/missing records retain their existing rules. Source validation is distinct from report approval and the UI explicitly explains this.
- HTML validation failures render the same report and affected indicator with attempted value, state, source fields, explanation and corrective action preserved. Inline alerts identify the indicator and provide next steps; invalid fields are identified for assistive technology and focused. Numeric format errors include a Turkish example.
- Creating a second report for the same institution/year gives an explicit instruction to open the existing report and create a revision. The check runs under the existing period lock, preserving concurrent creation behavior.
- Approval collects all blocking indicators/reasons before inserting the approval record. HTML shows links to affected indicators; JSON returns a message and structured blocker list. This is an intentional additive error-detail shape change for approval failures (string becomes object).
- Revision history displays the entrant's name; approved report detail displays the approver and approval time. Stable user IDs remain in the API/audit records. Names are resolved from the current user record. Stored timestamps remain UTC, with presentation converted to Europe/Istanbul and explicitly labeled Turkey time/UTC+03:00.
- Strategy/Directorate permissions are unchanged.

## Validation

Complete suite with disposable PostgreSQL available and `--require-postgres`: **228 passed, 0 skipped**. Includes contract v1/v2 checkpoint compatibility, v3 explanation precedence/inheritance/diffs, frozen history stability, evidence rules, all form fields and valid states preserved on failure, aggregate/atomic approval blockers, same-year error wording, audit names and timezone/day rollover. Existing exact numeric, correction-reason, concurrency and immutability regressions remain passing.

Python compile, JavaScript syntax, source-bundle consistency and Git diff checks passed. Bundle regenerated from source. Existing httpx/Starlette deprecation warning remains. The populated-DB migration repeat-run issue remains separate; the full run used a fresh disposable database.

## Live desktop browser retest

Actual normal login/forms used with isolated PostgreSQL data, Strategy and two Directorate accounts:

- Shared explanation displayed on new report; later card explanation changes and own indicator override appeared in revision differences.
- Source-free verified value was rejected with add-source/select-review guidance. The value, explanation, action and selected state stayed present.
- Source-free review saved normally; subsequent `abc` failed inline while preserving all source fields, explanation, action and review state. Corrected sourced verified entry saved.
- Empty report approval displayed all seven indicator blockers in one page, with working links. Complete sourced report approval succeeded.
- Same-year duplicate report produced the specific institution/year explanation and revision instruction.
- History displayed entrant names and Turkey-local time. Approved header displayed approver/time; input fields were removed.
- Approved correction still required a reason; changing publications created empty actuals and clear explanation/method/source/target diffs. Old approved report retained its six original shared explanations and was read-only.

No High or Blocker remains in the scoped Activity Report fixes. No merge/deployment performed.

## Remaining issues

- **Medium / global deployment gate:** overlapping logout/password controls remain deliberately separate. Required before deployment: https://github.com/dursuncavus/civensa/issues/5 . Do not deploy until fixed and browser-verified.
- **Medium:** saving one indicator still reloads the page and discards unsaved edits in other indicator forms. The submitted form's validation recovery is fixed; cross-form draft persistence is separate.
- **Medium:** latest actual/value/state remains inside collapsed history, which lists oldest first.
- **Low:** report list lacks current/historical and approval-status badges.
- **Low:** newer-publication warning does not identify the newest version or provide a nearby comparison action.

Deployment DB-role hardening remains tracked separately in issue #4. No credentials or deployment permissions changed.
