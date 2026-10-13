# Civensa — rules for coding agents

These rules apply to every task in this repository. The task text you receive is the authority for scope; these rules apply unless the task explicitly says otherwise.

## Product
Civensa is an institutional reporting platform for Turkish municipalities (performance programme and activity reports). Users are municipal staff with limited technical skill. Data reliability and understandable errors are core features.

## Branches
- `feature/authorization-workflow-phase5`: canonical development branch. Most work starts here.
- `main`: integration branch. `staging`: what the live pilot runs.
- Start from the branch named in the task. Create a new branch named `task/civ-###-short-name`.
- Open a pull request into the branch named in the task. Title starts with the task ID (for example `CIV-007 — ...`).
- Never merge, never push to `main`, `staging` or the phase 5 branch directly, never deploy.

## Hard rules
- Never connect to the live database. Use disposable local PostgreSQL only.
- Never delete data, branches or files outside the task scope.
- `ACTIVITY_REFERENCE_SUCCESSORS` in `app/report_workflow_service.py` must stay `False` unless the task explicitly says otherwise.
- Legacy Activity Report write paths stay closed for any report that has a ReportCandidate or ReportRelease. Do not reopen them.
- Migrations: exactly one Alembic head; never edit an existing migration; new migrations must not discard data on downgrade.
- Never print secrets, connection strings or passwords in code, logs or pull requests.

## Data rules
- Blank/null is not zero. Keep them distinct.
- Never silently reconcile conflicting values; make the reason traceable.
- Turkish number display: 12.500 and 12.500,23. Do not confuse display with storage.
- User-facing text is Turkish. Do not translate existing Turkish strings. Error messages must say what happened, which field/record is affected, and what the user should do.

## Tests
- Run tests against PostgreSQL: set `CIVENSA_TEST_POSTGRES_URL` to a disposable PostgreSQL 16+ database and run `python -m pytest -q --require-postgres` (focused tests first; the full suite when the task asks).
- Prefer a small failing regression test before fixing a confirmed bug.
- A change is not done until the pull request's CI is green.

## Reporting back
In the pull request description list: files changed, tests run with results, what could not be verified, and assumptions. Do not claim anything you did not actually run.
