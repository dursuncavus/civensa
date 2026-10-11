# Civensa specialist subagents (v2.1)

Native Claude Code subagent definitions (project scope). Claude Code loads every
`*.md` file in this folder that has `name` and `description` frontmatter; this
README has no frontmatter, so it is skipped.

The main Claude session is the **Technical Team Lead** and the **only writer and
integrator**. Every specialist is a read-only reviewer that reports to the lead.
ChatGPT/Nexa remains the external orchestrator and final integration authority.

## Roster

| Agent | Owns | Hands off to |
| --- | --- | --- |
| `civensa-db-guardian` | Alembic migrations, PostgreSQL/SQLite triggers, constraints, DB functions, dialect parity, DB-level immutability | workflow, test, reliability, security |
| `civensa-workflow-reviewer` | Business rules, role × state transitions, approvals, revisions/corrections, return/rework/reopen, delegation, publication gates, state-machine dead ends, audit history semantics | db, test, security, ux |
| `civensa-test-engineer` | Regression and integration test coverage, test design, focused existing tests and minimal probes on its own disposable DB (not the baseline runner) | db, workflow, reliability, others |
| `civensa-architecture-integrator` | Module boundaries, dependency direction, service/model/migration/payload contracts, backwards compatibility, integration seams, duplication | db, workflow, security, reliability, output, test |
| `civensa-security-reviewer` | Authentication, authorization bypass, organization isolation, role escalation, session/cookie/CSRF, upload attack surface, unsafe input, secrets, audit tampering | db, workflow, import, reliability, test |
| `civensa-ux-auditor` | End-to-end journeys per role, dead ends, state visibility, Turkish error messages, destructive-action clarity, broken controls, basic accessibility | workflow, security, output, import |
| `civensa-import-data-specialist` | DOCX/XLSX/XLSM/digital-PDF extraction fidelity, provenance, re-import, department matching, preview/correction, formula/cached values, ARK-01 library evaluation | security, reliability, db, ux, test |
| `civensa-reliability-reviewer` | Races, locking, transaction boundaries, idempotency, retry, partial failure, crash recovery, long-running work, operational readiness | test, db, workflow, security |
| `civensa-report-output-reviewer` | Report correctness, DOCX/PDF/export contracts, source-to-output traceability, revision/version in rendered output, determinism, print risks | architecture, workflow, db, security, test |

### Boundaries that look like overlap

- **Authorization:** `workflow-reviewer` decides whether the rule is the right
  business rule and holds on legitimate and out-of-order workflow paths.
  `security-reviewer` decides whether it can be bypassed (crafted request, IDOR,
  session/CSRF, cross-organization).
- **Locking:** `db-guardian` owns lock behaviour inside triggers/PL/pgSQL;
  `reliability-reviewer` owns application transactions, `FOR UPDATE` use in
  services, retries and cross-session interleavings.
- **Concurrency tests:** `reliability-reviewer` finds the failure scenario;
  `test-engineer` turns it into a regression test and judges existing tests.
- **Error messages:** `workflow-reviewer` checks a rule rejection names the record
  and next step; `ux-auditor` checks wording, placement and the journey around it.
- **Upload files:** `import-data-specialist` owns extraction fidelity and data
  loss; `security-reviewer` owns malicious files (XXE, zip bombs, macros).
- **Report payloads:** `architecture-integrator` owns cross-module payload and
  manifest contracts; `report-output-reviewer` owns what is rendered from them.

## Common rules (every specialist)

- Tools: `Read, Grep, Glob, Bash`. `Write, Edit, NotebookEdit, Agent` are in
  `disallowedTools`. No nested agents.
- Works against the exact SHA or range the lead gives (`git show <sha>:<path>`);
  states the SHA used if none was given.
- States what was **READ** vs actually **EXECUTED**.
- Findings use **VERIFIED / ALREADY SOLVED / INVALID / UNVERIFIED**; VERIFIED
  needs `path:line @ sha`.
- Gives the smallest safe correction, no broad redesign; hands off out-of-scope
  findings to the named specialist.
- Never claims tests or actions that were not performed.
- Runs tests or probes only when its role needs it and the lead's task allows it,
  and only under the **Execution safety** policy below: its own disposable
  database, a disposable copy of the product in a scratch directory outside the
  repository, no bytecode or cache files, exact-PID process control, no full
  suite. Never a shared, production or live database, never a deployed instance.
- `model: inherit`, `maxTurns: 40`.

**Bash is a soft read-only boundary.** It is enforced by each agent's
instructions and by the calling session's permission mode, not by a hard tool
block. Never run the team with `--permission-mode bypassPermissions`. Narrow
Bash allowlists block compound commands and push agents into read-only
reasoning (more UNVERIFIED findings), so prefer the default permission mode with
a read-only task brief.

## Execution safety (team policy v2.1)

Canonical copy. Every agent file embeds this section verbatim, because a
specialist sees only its own definition, not this README. Change all ten copies
together.
"Read-only" means read-only on the **repository** and on **shared data**. It does not forbid focused probes on your own disposable copies and databases.

You MUST NOT:
- modify tracked repository files, or create any file (including `__pycache__`, `.pyc`, `.pytest_cache`, logs or database files) inside the repository checkout or a product snapshot the lead gave you;
- modify agent definitions during a review;
- commit, push, create or delete branches, merge, rebase, checkout/switch, reset, stash, open PRs or deploy;
- connect to or modify a shared, live or production database, the lead's database or another specialist's database.

You MAY, when the lead's task allows running:
- create scratch files only under your own scratch directory outside the repository (`SCR=$(mktemp -d)`);
- copy the product at the given SHA there (`git -C <repo> archive <sha> | tar -x -C "$SCR/run"`) and run probes in that copy;
- create your own disposable database and insert, update, delete, drop and recreate data or schemas inside it.

Disposable database:
- One per specialist per run, with a unique name such as `civensa_<your-role>_$RANDOM$RANDOM`. Use a database the lead assigned to you alone, create your own on the disposable PostgreSQL server the lead named, or use a throwaway SQLite file in `$SCR`.
- A `CIVENSA_TEST_POSTGRES_URL` found in the environment is not yours unless the lead says it is exclusive to you: create your own database on that server and point `CIVENSA_TEST_POSTGRES_URL` at it for your own commands only.
- Prefer a whole database to a schema: repository migration tests use the `public` schema.
- Drop or recreate only your own database or schema, and only after your own processes using it have stopped. Name it in your report.

Python and pytest:
- Prefix every Python command with `PYTHONDONTWRITEBYTECODE=1` and call `python -B`; give pytest `-p no:cacheprovider`. Run probes and tests with the working directory in `$SCR/run`, never in the repository or a snapshot; a static parser that only reads repository files still uses `-B`.
- `python -I -B` suits standalone scripts. Keep `-B` with `-I`, because `-I` ignores `PYTHONDONTWRITEBYTECODE`. Do not use `-I` for pytest in the copy: it drops the working directory from `sys.path`, so `import app` fails.

Processes:
- Forbidden: `pkill`, `killall`, `kill` by name or pattern, `kill 0`, `kill -1`, process-group kills, `fuser -k`, and `ps ... | grep ... | xargs kill`.
- Start each background process as `cmd >"$SCR/<name>.log" 2>&1 & echo $! >"$SCR/<name>.pid"`. Stop it only with `kill <that pid>`, after `ps -o pid,args -p <pid>` shows your own command. Never stop the lead's, another specialist's or an unknown process, even if it blocks you; report the conflict instead.

Test scope:
- Never run the complete repository test suite (for example `pytest` with no path, `pytest tests/`, or every PostgreSQL test) unless the lead explicitly delegates that exact run. The lead owns the full baseline.
- Run the smallest focused test (`file::test`) or probe that proves or disproves one claim, wrapped in `timeout` (default `timeout 600`).

Turns and report:
- Your turn budget is limited (`maxTurns: 40`). Keep at least the last 8 turns for consolidating evidence and writing the report.
- Before any long-running command ask: is it needed to prove this finding, or should the lead own it? If the lead should own it, list it under `Hand-offs`.
- When near the limit, stop exploring and write the report. A report with UNVERIFIED items is worth more than one more speculative probe.
- Mark the evidence for each finding as READ (code read at the SHA, `path:line`) and/or EXECUTED (exact command, working directory, disposable database name and dialect, result line). Before reporting, confirm that `git -C <repo> status --porcelain --ignored` shows nothing you created.

## Team-lead behaviour

1. **Pick the smallest relevant set.** Never invoke every agent by default.
   Project rules prefer at most 3 concurrent specialists.
2. **Brief each one** with: exact SHA/range, the question, files or areas in
   scope, whether running tests/probes is allowed, where scratch files go, and
   (when running is allowed) the disposable database assigned to it alone or
   the disposable PostgreSQL server on which it creates its own.
3. **Reconcile, do not average.** When specialists disagree, state both
   positions, check the evidence yourself at the SHA, and record why one wins.
   Never silently pick one opinion.
4. **Specialist passes do not replace the lead's own critical review.** In the
   first blind validation (S3C-2) the specialists found B1 but all missed the
   workflow-semantics blocker B2. The lead must still read the change and test
   the hardest rule personally.
5. **Only the lead writes.** Specialists never edit files, commit, push, open PRs,
   merge or deploy.
6. **The lead owns the full suite.** The complete PostgreSQL baseline/full-suite
   run belongs to the lead, in the lead's own database and process. A specialist
   runs it only when the lead explicitly delegates that exact run. Never give two
   concurrent runs the same database.

### Routing table

| Task type | Specialists |
| --- | --- |
| Migration / triggers | db-guardian + test-engineer |
| Workflow / approval | workflow-reviewer + test-engineer |
| Cross-module feature | architecture-integrator + the relevant domain specialist + test-engineer |
| Security-sensitive feature | security-reviewer + workflow-reviewer and/or db-guardian |
| Import | import-data-specialist + security-reviewer + test-engineer |
| Complex reliability / concurrency | reliability-reviewer + db-guardian + test-engineer |
| User-facing workflow | ux-auditor + workflow-reviewer |
| Report generation | report-output-reviewer + architecture-integrator + test-engineer |

Small, single-area changes may need one specialist or none. When a task matches
several rows, take the union, rank the specialists by the concrete risks in the
change, and run them in waves of at most 3. Every wave of Phase 1 finishes before
Phase 3 starts. A specialist whose row the task explicitly matches (for example
report-output-reviewer when the task changes what a report shows) is deferred to
a later wave, not dropped.

### Phases for difficult tasks

1. **Independent review:** the selected specialists review the same exact
   SHA/range independently (in parallel, blind to each other).
2. **Reconciliation:** the lead reconciles disagreements explicitly.
3. **Implementation:** the lead alone implements, on the branch it was given.
4. **Post-review:** the relevant specialists review the final diff.
5. **Handoff:** the lead returns one consolidated handoff to Nexa (branch, SHAs,
   what was run, findings with statuses, open decisions).

## Use

In a Claude Code session started in a checkout that contains this folder:

```
Use civensa-import-data-specialist, civensa-security-reviewer and
civensa-test-engineer in parallel to review <base>..<head>; running probes on a
throwaway SQLite file is allowed. Then reconcile their findings.
```

or `@agent-civensa-db-guardian review migration <rev> at <sha>`.

To check which definitions a session loaded, ask it headlessly from the checkout,
for example `claude -p "Without calling tools, list every subagent type whose name
starts with civensa-" --max-turns 1`. (In Claude Code 2.1.296, `claude agents`
lists running sessions, not definitions.)

## Notes

- A new `.claude/agents` directory, or new files in it, may only be picked up at
  session start; edits to existing files hot-reload. If the team is not visible,
  start a fresh session (or headless `claude -p`) from a checkout of this branch.
- For a blind/independent review run from a cloud project session, unset
  `CLAUDE_COWORK_MEMORY_PATH_OVERRIDE` and `CLAUDE_MEMORY_STORES` so the agents
  do not read project memory.
- `model: inherit` runs each agent on the calling session's model; cost scales
  with the number of specialists, so routing small is also a cost control.
- Tool exposure depends on the Claude Code build. In headless Claude Code 2.1.296
  in the cloud container, a spawned specialist reported only `Read` and `Bash`
  (that build exposes no separate Grep/Glob tools; search runs through Bash
  `grep`/`git grep`). The denied tools were absent, as intended.
- Granting write access to any specialist (for example the test engineer) is a
  separate, explicit decision. Nexa decision 2026-10-10: `civensa-test-engineer`
  stays read-only.

## Changelog

- **v2.1 (2026-10-11), after the A1 adversarial audit.** Process hardening only;
  roster, domain ownership, routing, `model: inherit`, `maxTurns: 40` and the
  3-concurrent-wave rule are unchanged. Added the identical **Execution safety**
  section to all 9 agents: explicit read-only definition (repository and shared
  data, not disposable probes), one disposable DB per specialist per run,
  `PYTHONDONTWRITEBYTECODE=1` + `python -B` + `-p no:cacheprovider`, no
  `pkill`/`killall`/pattern kills (exact PID only), no full suite without explicit
  lead delegation, and a reserved report budget. Role-specific corrections:
  `workflow-reviewer` may run focused disposable-DB probes and must label READ vs
  EXECUTED evidence (its v2 line "never change ... a database" blocked probes in
  A1); `test-engineer` is not the baseline runner (it ran the full suite, used
  `pkill -f` and lost its report in A1); `db-guardian` may mutate its own
  disposable DB but must not write bytecode into a snapshot (it did in A1).
  Nexa decision 2026-10-11 (A1 closure, D5) approved these rules.
- **v2 (2026-10-10):** 9 read-only specialists, routing table, phases.
- **v1 (2026-10-10):** db-guardian, workflow-reviewer, test-engineer.
