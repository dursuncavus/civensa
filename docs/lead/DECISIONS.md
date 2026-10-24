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

## D-211 (24 Oct 2026 ~04:05, lead) — lead writes the CIV-087 D-203 fixes itself
DOĞRULANDI: the CIV-087 Codex session kept approval_policy=never after the D-209 change and could not push its fix d722e49 even with full access back on. Instead of a new Codex task at 04:00, the lead pushed fde1dfb to `task/civ-087-turkce-hata`: `/login?reason=session` with server-owned messages only (MEDIUM), anonymous error page without the resubmit form (LOW), file warning on the recovery form (LOW); two existing tests updated and one added (listed in the PR comment, D-167). Not run locally (dependencies not installable here) — CI is the judge. Cross-family review: "@codex review" requested. Merge when CI green on fde1dfb and the review has no P0/P1. d722e49 is abandoned.

## D-212 (24 Oct 2026 ~04:10, lead) — PR #82 (CIV-086) review: not mergeable yet; CIV-088 held
DOĞRULANDI on fb7a88c (CI green, behind 0): MEDIUM — ar-typeset/1 `context` copies release history (reopen actor names, reasons) and workflow data into a file meant for an outside designer (constitution rule 24); LOW — IndexError path in `save_section_keys`. Deploy note: snapshots made before c086 block approval/freeze until resubmitted (BELİRSİZ whether any live AR submissions exist; pre-launch expected). Follow-up given to the owner for the CIV-086 Codex task and posted on #82.
CIV-088 (AR-16) is not dispatched tonight: same files as #82 (D-137) and depends on Strateji's >%85 normalization decision.

## D-213 (24 Oct 2026 ~05:45, lead, scheduled run "Civensa gece kontrol") — #82 accepted; scheduled-run merges blocked by session permission
DOĞRULANDI (GitHub REST 02:40–02:50Z):
- PR #82 (CIV-086) re-review of head 6d6969c: D-212 MEDIUM fixed — `context` and section `values` now use explicit allowlists (`CONTEXT_FIELDS`, `SECTION_FIELDS`); manual provenance has no actor id; `financial_context`/`core_context` checked: no person names or reasons (imports carry id/kind/time/sha only). D-212 LOW fixed — `save_section_keys` rejects stored positions outside the source rows with the Turkish 422, regression test added (`tests/test_ar_typeset_review.py`); the two golden artifacts were regenerated for the removed actor id. Alembic: one head (c086a1b2c3d4 → c084a1b2c3d4). CI green on 6d6969c: test (18,0) and (18,1), run 40047936634. Behind 0, not draft. Lead review: no open HIGH/MEDIUM → MERGE OK.
- PR #84 (CIV-089) head 04975b3: test (18,0), (18,1) and secrets green, behind 0, not draft → MERGE OK per D-197/D-206.
- PR #86 (D-205): Codex re-review of e8f6530 "Didn't find any major issues"; later commits change only DECISIONS.md/STATE.md (workflow unchanged); tests green on 84c52d0 → MERGE OK (rule 18 met).
- The merge call (PUT /pulls/82/merge) was refused by the scheduled session's permission check ("merge without review"), not by GitHub. Per the run rules it was not retried and no other PR was merged. So scheduled runs cannot merge today; the owner merges these in order #82 → #84 → #86. Merging #84/#86 while 1–2 commits behind is accepted for owner merges: their files do not overlap #82 or each other (D-137).
- PR #85 (CIV-087) head fde1dfb (lead-written, D-211): test (18,0) FAILED (run 40047364679, job 120732408316); annotations show only "exit code 1" because CIV-089 annotations are not on phase5 yet. Codex review requested 00:55Z still shows "running" after ~2 h (BELİRSİZ: stuck). Local reproduction not possible (package index unreachable from this sandbox). Not mergeable. Next step after #84 merges: update #85's branch so CI names the failing test, then the lead fixes it (lead-written code) and resolves the overlap with #82 (activity_financial_routes/service, activity_financial.html, civ-062 doc).
- No "@codex" comments posted this run (no Codex-authored head needs a correction). Codex reaction to the earlier fix comments: none (D-208 stands).
- Guard: no "Lead records guard" run appeared on this record PR #87 (base lead/civ-lead-records) within 3 min (DOĞRULANDI). Repo default branch is `main`, which has no guard file; GitHub now takes `pull_request_target` workflows from the default branch (BELİRSİZ: from the lead's knowledge of a GitHub change, not checked here), so the guard may also never run on phase5 PRs after #86 merges. This weakens D-207's "first lead PR after #86 is the guard's live test" — check in the next live session; until then the gate is the lead's own review. #87 was therefore not merged by the run (no green guard); the owner merges #87 before #86.

## D-214 (24 Oct 2026 ~17:05, lead, live session) — live session merges; #82 merged
DOĞRULANDI: the live lead session can merge (PUT /pulls/82/merge succeeded, squash 6324c87 into phase5); only the scheduled run is refused. #87 (night record) merged into lead/civ-lead-records. #84 and #86 were behind 1 after #82 → update-branch; merge when green. #85 test (18,0) failure is caused by fde1dfb (124c5aa shard 0 was green); test name not visible until #84's annotations are on phase5. Owner merge list from D-213 is withdrawn — no owner action needed.

## D-215 (24 Oct 2026 ~18:50, lead) — #84 and #86 merged; #85 rebased; CIV-088 dispatched
DOĞRULANDI: #84 squash-merged (green, behind 0). #86 merged while 1 behind (#84's files do not overlap #86's: workflows differ, docs/lead only) — exception to behind-0 recorded here. #85 update-branch failed on conflict with #82; lead merged phase5 locally (5ddd8a9): activity_financial.html keeps CIV-087 attempt retention + CIV-086 figure_stable_key; civ-062 doc takes AR-14 from CIV-086, AR-15 from CIV-087. CIV-088 (AR-16) package written with lead defaults for the open Strateji decision (named constants, easy to change); forbidden files exclude everything #85 touches (D-137).

## D-216 (24 Oct 2026 ~19:00, lead) — CIV-090 (AR-06) dispatched; third slot left empty
AR-06 is the only OPEN AR gap that needs no Strateji/Ali answer. Package keeps draft saves allowed and adds the check at unit submission, files disjoint from #85 and CIV-088 (D-137). The third Codex slot stays empty: the remaining PARTIAL items (AR-01/02/03/04/13/17/18) need Ali/Finance decisions or overlap open work; filling it now would waste quota (constitution rule 16).

## D-217 (24 Oct 2026 ~19:10, lead, live session) — password-file item closed by owner
BEYAN: the owner told the lead to drop the plaintext password files item (log 79) and stop reminding him. Removed from the owner list; the lead does not raise it again. Risk stays with the owner's decision.

## D-218 (24 Oct 2026 ~19:40, lead) — CI blocked by GitHub billing
DOĞRULANDI: #89 head 5d5f9f3 `secrets` job annotation says the job was not started because account payments failed or the spending limit must be increased. Test jobs on #85 (2f02a42) and #90 (7588a9b) have shown in_progress for ~40 min (BELİRSİZ: likely stuck for the same reason). Escalated to the owner (payment = human-only). After the fix the lead re-runs the jobs; no merges until then. #89 earlier failure (fd280ff, `similarities` undefined) sent to Codex; Codex pushed 5d5f9f3.

## D-219 (24 Oct 2026 ~22:35, lead) — CI cost: raise budget now, CIV-091 to cut minutes
DOĞRULANDI (Actions API, October): 237 "Performance program validation" runs; pytest takes 37–43 min per shard, 2 shards per push (~80 job-minutes); other workflows are negligible. Owner screenshot: $52 gross metered, $12 included, Actions budget 100% used. Concurrency cancel and docs path filter already exist, so the cost driver is suite duration × pushes (Codex draft iterations). Decision: owner raises the Actions budget (about $80/month) so work continues; CIV-091 skips tests on draft PRs and cuts suite time without removing tests. Making the repo public (free minutes) is rejected for now: institutional data and security exposure (constitution rule 24).
