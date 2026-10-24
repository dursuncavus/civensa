# CIVENSA — DECISIONS LOG

Append-only. Newest entry at the bottom. Never rewrite an old entry; a later decision may supersede it and must say which one.
Entry format: `D-### (date, who) — decision. Reason. Supersedes: …` with facts tagged DOĞRULANDI / TARİHSEL / BEYAN / BELİRSİZ.

## History before D-205
Decisions D-001 to D-204 are in Google Drive, `AI-Work-System/projects/civensa`, documents "CIVENSA_DECISIONS_LOG" … "CIVENSA_DECISIONS_LOG 84" (TARİHSEL, read-only archive). Read them only when an old decision is questioned.

Still in force and needed day to day (summaries; the Drive entry is the full text):
- D-137 — parallel tasks must not touch the same files; each package lists forbidden files.
- D-167 — a PR must name every existing test it changes and why.
- D-177 — plan conversion is a live-session item with the owner (time set by owner).
- D-191 — DeepSeek may be an optional first-pass reviewer for large PRs.
- D-194 — DeepSeek is backup lead with limited authority (`BACKUP_LEAD.md`).
- D-196 — tool acceptance criteria (`HIERARCHY.md` §8); gitleaks blocking, actionlint warning; no new MCP servers or document libraries; ruff/mypy deferred. Its item K5 ("Drive canonical") is superseded by D-205.
- D-197 — PR #84 code accepted; merge when both test shards are green on the head and proof links + measured minutes are in the PR text.
- D-198 — terminal dispatch setup (local CLIs + scripts) rejected. Its reason (3) "repo state files = second source of truth" is superseded by D-205: the repo becomes the only source, Drive is archive.
- D-199 / D-201 — DeepSeek on standby; channel = its Mac workspace (CLAUDE-BRIEF.md, GUNCEL-DURUM.md, YEDEK-KAYIT.md); no Composio, no separate Google account.
- D-202 — hierarchy v1.3: lead merges into phase5 under conditions, sends "@codex" PR comments, scheduled run "Civensa gece kontrol".
- D-203 — PR #85 (CIV-087) not mergeable: MEDIUM login `?message=` reflection; LOW anonymous error-page form, resubmit drops files; test(18,0) failed. Follow-ups posted as "@codex" comments.
- D-204 — PR #84 is draft; lead cannot un-draft via REST; owner marks it ready.

---

## D-205 (24 Oct 2026 03:24, owner approved; designed by lead) — lead records move from Drive into the repository
Decision: Civensa project rules, hierarchy, backup-lead brief, current state, decisions log and new task packages live in `docs/lead/` on `feature/authorization-workflow-phase5`. Drive keeps the global constitution and the read-only archive.
Reason (DOĞRULANDI 24 Oct): Drive documents cannot be edited in place through the lead's tools, so every update created a new document — the decisions log reached 84 separate files and the state 77 versions; each session spent effort searching for the newest one and risked reading an old one. In git, one file per record, every change visible and reversible, and Codex reads the same files. Suggested by the owner's contact Erhan Meydan (BEYAN, 23 Oct); the parts kept are shared repository + file-based records; terminal CLIs and "lead reads only 5-line summaries" are not adopted (D-198 stands; reviewing diffs found the D-203 MEDIUM that a summary would have hidden).
Safeguards: only `lead/...` branches may change `docs/lead/**` or `AGENTS.md` (CI guard); AGENTS.md tells coding agents not to edit them; no secrets in these files.
Supersedes: D-196 K5, D-198 reason (3), hierarchy v1.3 §6 "Drive wins". Rule docs bumped: HIERARCHY v1.4, PROJECT_RULES v1.3, BACKUP_LEAD v2.
Rule 35 sync still open: civensa-lead skill text, scheduled task prompt, DeepSeek mirror — see STATE.md queue item 8.
