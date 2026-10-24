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

## D-206 (24 Oct 2026 ~03:35, lead) — PR #84 no longer draft; branch updated
DOĞRULANDI: #84 draft=false (marked ready by owner or Codex), head f6bfc39 all checks green (test 18/0, 18/1, secrets), proof links in PR text (D-197 met), but behind phase5 by 4 → lead called update-branch; new head 04975b3, CI rerunning. Merge when green and behind 0. D-204 is closed (no owner action needed). Also DOĞRULANDI: the lead session can mark PRs ready via REST `POST /pulls/{n}/ccr/ready_for_review`, so owner un-draft clicks are no longer needed.
Scheduled task "Civensa gece kontrol" prompt updated to read docs/lead/ and to carry out the D-205 Drive archive steps once #86 is merged.

## D-207 (24 Oct 2026 ~03:45, lead) — guard runs from the trusted base revision
Codex review of #86 (P1, on b5231a4) accepted: under `pull_request` a PR runs its own copy of the guard and could rewrite it to pass. Fix: `lead-docs-guard.yml` now uses `pull_request_target` (base branch's copy, no checkout, metadata only, branch name passed through env) and also rejects fork PRs.
DOĞRULANDI: branch protection is not available on this private repo without GitHub Pro (REST 403), so no check can block a merge; the guard is a signal and the real gate is that only the lead merges into phase5 and never merges a red PR. Not worth paying for Pro for this alone.
Side effect: `pull_request_target` runs the base branch's file, which does not exist on phase5 until #86 merges, so #86 itself shows no guard run; the first lead PR after #86 is the guard's live test. "@codex review" requested again on the new head before merge.

## D-208 (24 Oct 2026 ~03:50, lead) — "@codex" PR comments cannot deliver fixes; fix follow-ups go through the owner
DOĞRULANDI: on #85 the Codex bot answered the lead's fix request with "create an environment for this repo" (no Codex cloud environment exists), and head 124c5aa only changed the CSRF text; `/login?message=` reflection (D-203 MEDIUM) is still in app/main.py:213/562. "@codex review" comments do work (reviews on #85, #86).
Decision: until a Codex cloud environment exists, the lead writes fix follow-ups in English and the owner pastes them into that task's own Codex conversation. Partly supersedes D-202 ("lead sends follow-ups as @codex PR comments" → reviews only). Whether to set up a Codex cloud environment: BELİRSİZ, to be checked against how the owner runs Codex today; not escalated now.

## D-209 (24 Oct 2026 ~03:50, lead) — lead mistake: turned off Codex full access mid-task
What failed: the lead told the owner to turn off "Tam erişim" in the running CIV-087 task; the session approval policy became "never" and Codex could not push d722e49 or update PR #85; switching to "Onay iste" did not help on retry (DOĞRULANDI, owner screenshots 03:47/03:49).
Why: the lead gave a settings instruction for a running task without knowing how the Codex app applies permission changes mid-session (constitution rule 7/8).
Correct approach: full access back on for this task until the push is done. Prevention: no permission changes on a running Codex task; a permission setup is decided once, tested on a new task in daytime, then recorded.

## D-210 (24 Oct 2026 03:52, owner) — Codex keeps "Tam erişim"
BEYAN: owner decided full access stays on for Codex tasks. Closes STATE owner item 1. Remaining risk accepted by owner: Codex can act freely on the owner's machine; mitigations stay as they are (no secrets in repo, plaintext password files to be moved — owner item 2, lead reviews every PR).
