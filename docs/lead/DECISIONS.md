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

## D-220 (24 Oct 2026 ~23:15, lead) — public repo: prepare first (CIV-092); #90 merged; #85 fixed
BEYAN: owner says the report data is public and approves preparing the repo for public visibility (free Actions minutes). DOĞRULANDI blocker: daily live-database backups are uploaded unencrypted as Actions artifacts (90-day retention, 16 present); public visibility would expose accounts and password hashes. Workflows are otherwise fork-safe (guard never checks out PR code; backup secrets only on schedule/dispatch); a quick regex scan of 391 commits found no real credential (full gitleaks history scan is part of CIV-092). Decision: CIV-092 encrypts backups with age and adds a full-history scan + readiness report; deleting the old artifacts and flipping visibility each need a separate owner confirmation. GitHub Pro rejected (+1,000 min only).
#90 (CIV-090) reviewed by the lead, CI green on 7588a9b, merged while 4 behind (base drift docs/lead only — same exception as D-215); LOW notes posted on the PR. #85: shard 0 failure was the storage inventory test (CIV-086 stable_key columns unclassified); lead added them as non-base64 text (87b0b45) and asked "@codex review".

## D-221 (25 Oct 2026 ~00:30, lead) — UI redesign: AI makes the screen map, owner designs
Owner asked whether to give the interface redesign to an idle AI. The owner is project manager and designer of the redesign (BEYAN); design decisions stay with him, Claude advises and implements. The mechanical part he asked for earlier — every screen with what each element is and where it leads — goes to the free Codex slot as CIV-093, adapting the existing CIV-054 screenshot script. #89 (CIV-088) merged after a rerun of one flaky browser test (`test_word_preview_displays_sections_and_applies_and_reverts_in_browser`, unrelated files); #85 branch updated, merges when green.

## D-222 (25 Oct 2026 ~02:30, lead) — #95, #85, #96 merged
DOĞRULANDI: #95 (CIV-091) merged on 4fa013d (green; behind 2, docs/lead only — D-215 exception): pytest per push ~80 → ~34 job-minutes, draft PRs start no test job. #85 (CIV-087) merged on eceb565 (green, behind 0, "@codex review" on 87b0b45 found no major issues). #96 (CIV-092) merged on 624e242 (green, behind 0); lead review no P0/P1. Encryption only applies once the workflows reach `main` (schedule runs from the default branch); secrets must exist first or backups fail closed — public-switch steps listed in STATE. Full-history gitleaks findings (fake test password, field name) are covered by #85's allowlist, now merged.

## D-223 (25 Oct 2026 ~02:55, lead) — #101, #100 merged; age secrets set; step 2 changed to default-branch switch (proposed)
DOĞRULANDI: #101 (CIV-094) reviewed by the lead (gate never 500s on a missing anchor; listing cache key = load_baseline filters org/scope/department/year; no threshold/message change), branch updated, CI green on 06c2f56, behind 0 → merged (95685f4). #100 (CIV-093 UI screen map) reviewed (screenshot script only changes local tooling on disposable PostgreSQL; synthetic "Örnek Belediyesi" data; ~34 MB PNGs accepted as the owner's redesign reference), branch updated, CI green on a62283e, behind 0 → merged (f24df1e).
BEYAN + owner screenshot: public-repo step 1 done — `BACKUP_AGE_RECIPIENT` and `BACKUP_AGE_IDENTITY` set as Actions secrets ("Set Actions secret" ✓ for both, 25 Oct ~02:09); the private key is stored in the owner's Passwords app. The lead cannot list Actions secrets through the session proxy (403), so this rests on the owner's screenshot.
DOĞRULANDI: the guard never runs — `lead-docs-guard.yml` does not exist on the default branch `main` (pull_request_target reads the default branch). Main is 174 commits behind phase5 (3 merge commits only on main).
Risk found: merging phase5 → main (old step 2) may be a 174-commit live deploy if Render deploys from `main` (BELİRSİZ; Render settings are owner-only). PROPOSED (not accepted until the owner confirms): replace step 2 with switching the repository default branch to `feature/authorization-workflow-phase5`. Schedules (encrypted backups) and the guard then run from phase5 without touching main or Render; reversible. Owner first reports the Render service's deploy branch.
Codex/Gemini/DeepSeek stay idle until Ali's answers (sent Mon 26 Oct): the remaining PARTIAL AR items (AR-01/02/03/04/13/17/18) all depend on them (rule 16, as D-216).

## D-224 (25 Oct 2026 ~10:30, lead, live session) — UI redesign: Claude designs, owner approves (amends D-221)
BEYAN: the owner asked the lead to pick an AI to do the UI design, research first, minimalist/calm/low-fatigue. Amends D-221: the AI produces the design, the owner approves and corrects (still project manager).
Decision: Claude (Opus) designs in a separate conversation "CV Tasarım 1" on the Claude Design canvas (Design System + Design artifacts). Rejected: Google Stitch / Figma Make (prompt-to-screen tools without the repo, roles and 97-screen context → inconsistent screens). Figma account DOĞRULANDI connected (Full seat, Starter) — export later only if wanted. No local setup on the Mac (adds maintenance, no gain; rule 16). Gemini reviews the first three screens once (different model family). Codex implements module by module after each design approval; order must not delay the 1 Jan 2027 PP target.
Research brief (sourced, evidence vs model judgment separated): artifact "CV Tasarım Araştırması" https://claude.ai/artifact/RAhu2JYfbRMsFdarmnBLG5 — light theme default, high contrast, one accent colour, one topic per page, "what is left" at the top, Fira Sans, numbers right-aligned with tabular figures, WCAG 2.2 AA target (Circular 2025/10 scope for an internal system BELİRSİZ).

## D-225 (25 Oct 2026 ~10:20, lead, live session) — design production moves to Codex (amends D-224)
BEYAN: the owner approved the D-224 principles and asked whether the design work would burn Claude's weekly quota. Lead assessment: yes — iterating full screens on the Claude Design canvas is token-heavy, and Claude's quota is needed for lead work (Ali's answers due Mon 26 Oct → same-day reviews and packages). The lead cannot see remaining Claude quota (BELİRSİZ). ChatGPT Pro is the largest paid quota and Codex is idle until Ali's answers (rule 16: use the idle, already-paid resource).
Decision: Claude keeps the taste decisions in compact form (exact tokens + principles in the package); Codex (CIV-095) builds the design system and three screens as a static HTML/CSS prototype in the repo — already in the form later implementation needs, and without touching app code. Lead reviews via screenshots (different model family, rule 18); owner approves. "CV Tasarım 1" Claude conversation is not opened for now; Claude Design canvas stays an option for single-screen explorations only.

## D-226 (25 Oct 2026 ~10:25, lead, live session) — Claude quota is tight; short sessions until reset
BEYAN (owner screen, handover CV Lider 17): weekly Claude usage 21%, at this rate it ends Friday evening 30 Oct; October extra-usage charge $40.30 of $45. Decision: live lead sessions stay short (do the task, short record, close); Claude's quota goes to PR reviews, Ali's answers (Mon 26 Oct) and Codex packages; design production stays on Codex (D-225). If the quota runs out, DeepSeek acts as backup lead per BACKUP_LEAD.md. No PR open (DOĞRULANDI 10:25); backup log has no entries (DOĞRULANDI).

## D-227 (25 Oct 2026 ~10:30, lead, live session) — Render deploy branch known; default-branch switch recommended
BEYAN + owner screenshots (Render dashboard, 25 Oct 10:28): six services (civensa-pilot, civensa-qa, civensa-smoke, civensa-smoke3, civensa-db-probe, civensa-test). civensa-pilot (Free instance, Frankfurt) is the most recently updated; repo dursuncavus/civensa, branch `main`, **Auto-Deploy Off**, PR previews Off, live commit 6b4d834. DOĞRULANDI (REST): 6b4d834 is the current head of `main` (20 Oct).
Assessment: a push to `main` does not deploy civensa-pilot by itself (auto-deploy off); a deploy needs a manual click. The D-223 default-branch switch to phase5 still wins: it leaves `main` = live code untouched, makes schedules (encrypted backups) and the guard run, and is reversible. Waits for owner confirmation (repository setting, escalation list). civensa-qa branch not checked (not needed: the switch does not change `main`). Test services: whether any costs money — BELİRSİZ, check later on the Billing page.

## D-228 (25 Oct 2026 ~10:35, owner approved, owner clicked) — repository default branch switched to phase5
Owner approved the D-223 proposal (10:31). The lead's REST call was refused by the session proxy ("Repository settings writes are not permitted"), so the owner switched it in GitHub settings. Lead mistake: told the owner "I will switch it" before testing the permission (constitution rule 7) — next time test first, then promise. DOĞRULANDI 10:34: default_branch = feature/authorization-workflow-phase5; workflows active incl. "Lead records guard" and "Daily verified database backup". `main` (= live 6b4d834) unchanged. Public-repo step 3: verify the next scheduled encrypted backup run, no manual dispatch.

## D-229 (25 Oct 2026 ~10:55, owner approved; lead reviewed) — CIV-095 design approved, three fixes before merge
DOĞRULANDI (lead review of PR #109 head 5c06b92, screenshots 1440/390): only docs/design/prototype/** changed; follows D-224 principles; 104/104 old elements mapped; contrast script 33/33 pass; CI security green. BEYAN: owner approved the look ("gayet iyi görünüyor", 10:51).
Fixes (sent to the CIV-095 Codex task via the owner, D-208): MEDIUM — 012 "Bölüm denetim geçmişi" shows raw JSON to users; replace with a plain Turkish change summary, raw data behind a collapsed technical disclosure. LOW — emoji ⚠️ and text glyphs (‹ ○ ✓) as icons → one inline SVG icon set using currentColor. LOW — components page textarea focus state shows a red border; focus must be the accent only.
Merge after the fixes when CI is green and behind 0. Next: CIV-096 applies the design system to the real base layout and screen 034 first.

## D-230 (25 Oct 2026 ~11:10, lead, live session CV Lider 19) — #109 not merged yet; CIV-096 package ready; backup run was plaintext
DOĞRULANDI (REST, 11:05): PR #109 head is still 5c06b92 — the D-229 fixes have not reached the PR; behind phase5 by 10 (lead record PRs). Not merged. Lead does not update the branch now, so Codex's push is not rejected; update-branch after the fix commit lands.
DOĞRULANDI: the only scheduled "Daily verified database backup" run today (25 Oct 05:07 UTC, run 40164385570) ran from `main` (6b4d834) before the default-branch switch; main's workflow has no age encryption → artifact `civensa-db-backup-20261025-0507Z` (680 KB, expires 23 Jan 2027) is PLAINTEXT. Add it to public-repo step 4 (delete old plaintext artifacts). phase5's workflow encrypts (setup-age, BACKUP_AGE_RECIPIENT, uploads only *.age), cron 00:30 UTC; GitHub ran today's schedule ~4.5 h late. Step 3 stays open: first encrypted run expected 26 Oct, verified by the 08:41 night check or the next live session.
CIV-096 package written (docs/lead/tasks/CIV-096.md): apply the design system to base.html shell + screen 034/033; other 53 templates untouched but must pass the CIV-093 capture checks inside the new shell. Dispatch only after #109 is merged (it builds on docs/design/prototype/).
STATE.md "Next decision" was stale (said D-227 after D-229 existed) — corrected.

## D-231 (25 Oct 2026 ~11:45, lead, live session CV Lider 19) — #109 merged; CIV-096 dispatched
DOĞRULANDI: PR #109 fix commit 1c339b1 checked — 012 audit history shows a plain Turkish summary ("Durum: Boş → Taslak", "İçerik: 1 paragraf eklendi") with raw data in a collapsed "Teknik ayrıntı"; no emoji/text-glyph icons left (inline SVG, currentColor); textarea focus = accent outline only. Only docs/design/prototype/** changed. Lead updated the branch (head ab9f7ec), CI green, behind 0 → merged (03d2ccc). CIV-095 done.
CIV-096 (docs/lead/tasks/CIV-096.md) given to the owner for a new Codex task (Codex idle, BEYAN 11:32).

## D-232 (25 Oct 2026 ~11:45, lead, live session CV Lider 19) — lead mistake: dispatch format and handover
BEYAN (owner, 11:38): no handover note was given for the next session; the CIV-096 dispatch named the model vaguely ("the model you used for CIV-095"); the task title was outside the paste block.
What failed: HIERARCHY dispatch rule (PLATFORM → PROJECT → TITLE → TEXT, model and reasoning level) was applied loosely. Why: the lead did not verify the current Codex model name and skipped the handover because the session closed early.
Correct approach (applies from now, every dispatch and every session end): (1) each dispatch states platform, the exact verified model name and the effort level; (2) the title is the first line INSIDE the paste block; (3) every live session ends with a paste-ready handover note for the next session (title + text in one block, model and effort for the lead session).
DOĞRULANDI (OpenAI ChatGPT & Codex changelog, read 25 Oct): GPT-6.1 Sol is the default Codex model; GPT-5.5 retired from Codex on 14 Oct 2026. Codex dispatches use GPT-6.1 Sol; effort per task (CIV-096: High).
