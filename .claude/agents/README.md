# Civensa specialist subagents

Native Claude Code subagent definitions (project scope). Claude Code loads every
`*.md` file in this folder that has `name` and `description` frontmatter; this
README has no frontmatter, so it is skipped.

| Agent | Scope | Tools |
| --- | --- | --- |
| `civensa-db-guardian` | Alembic migrations, PostgreSQL/SQLite triggers, constraints, DB invariants | Read, Grep, Glob, Bash (no Write/Edit) |
| `civensa-workflow-reviewer` | Authorization, approvals, revisions, business rules, audit history | Read, Grep, Glob, Bash (no Write/Edit) |
| `civensa-test-engineer` | PostgreSQL integration tests, concurrency, regression coverage | Read, Grep, Glob, Bash (no Write/Edit) |

All three are read-only reviewers. Bash is allowed so they can read code at an
exact SHA (`git show`) and run tests against a disposable database; the
"read-only Bash" rule is enforced by their instructions and by the calling
session's permission mode, not by a hard tool block.

## Use

In a Claude Code session started in a checkout that contains this folder:

```
Use civensa-db-guardian, civensa-workflow-reviewer and civensa-test-engineer
in parallel to review <base>..<head>; then consolidate their findings.
```

or `@agent-civensa-db-guardian review migration <rev> at <sha>`.

The lead (the main Claude session) consolidates the three reports. Findings use
VERIFIED / ALREADY SOLVED / INVALID / UNVERIFIED, and VERIFIED needs
`path:line @ sha`.

## Notes

- `model: inherit` runs each agent on the calling session's model.
- New definition directories are picked up only at session start; edits to
  existing files hot-reload.
- Granting write access (for example to the test engineer) is a separate,
  explicit decision; it is not part of this setup.
