# CIVENSA — CURRENT STATE

Updated: 26 Oct 2026, ~08:45 Istanbul (scheduled run "Civensa gece kontrol", D-256).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.4 · `PROJECT_RULES.md` v1.3 · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries, last modified 23 Oct (DOĞRULANDI 26 Oct 05:45).
Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Next session — start here (D-253)
Owner opens a new chat with one line: `CV Lider 25 · Claude Opus 5.5 · civensa-lead`. The lead reads this section first and works from it.
0. URGENT (D-256): GitHub Actions does not start any workflow since 25 Oct 21:43Z (startup_failure) — the daily live-database backup (db-backup.yml) did NOT run on 26 Oct 05:10Z (last good backup 25 Oct 05:07Z). Owner checks https://github.com/settings/billing (Actions minutes / spending limit / payment); lead diagnoses first in the live session. Until fixed no PR can get CI, so nothing can be merged under the rules.
1. PR #132 (CIV-102) is reviewed OK, CI green, behind 0 (D-255); the scheduled run's merge was refused by the permission check. Owner merges https://github.com/dursuncavus/civensa/pull/132 (or the live session does after re-checking behind 0), then approves the look and the listed text changes.
2. Mon 26 Oct — Ali Abi answers: read Gmail thread "CIVENSA-CEVAPLAR v1"; record decisions; write Codex packages the same day (data/logic fixes come before UI work, D-243). Gemini research/review only if a CRITICAL decision needs it.
3. Mon 26 Oct — Copilot (D-246/D-248): owner opens https://github.com/settings/copilot ; trial if offered, otherwise Copilot Pro ($10/month). After purchase the lead: verifies and has the owner set the additional-usage budget to $0 (verify the settings path first); writes .github/workflows/copilot-setup-steps.yml (single job copilot-setup-steps: PostgreSQL service, Python deps, Playwright Chromium; must be on the default branch) + "@codex review" + owner-approved merge; updates HIERARCHY.md (Copilot moves from "outside the chain" to a worker for fix rounds, with the gap and acceptance check — owner approval, rule 17). "Require approval for workflow runs" stays ON until public-repo step 7.
4. Mon 26 Oct — public repo step 3: check the first scheduled phase5 backup run uploads only .age artifacts (night check 08:41 or live session). Then step 4 only with owner approval.
5. When CIV-102 is merged and Ali's work allows: next UI task per D-243 is 010/009 EK-1 section index; per D-252 bundle related screens and the D-251 LOW items into one task.
6. Next IDs: task CIV-103, decision D-257.

## Claude quota (BEYAN, owner screen 25 Oct ~10:15)
- Weekly usage 21% on 25 Oct morning; at that rate it runs out Friday evening (30 Oct). October extra-usage charge: $40.30 of $45 limit.
- Rule until reset (D-226): short live sessions — reviews, Ali answers and packages first; no design iterations on Claude.
- Claude Pro ends 3 Nov 2026 (BEYAN). iOS subscription cancelled; owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov DeepSeek runs as backup lead (BACKUP_LEAD.md).

Dispatch format (D-232, D-249): platform + environment ("Bulut → civensa") + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block. Session end: one-line handover (D-253) after this file is rewritten.
Evidence rule (D-252): one-screen changes → targeted tests + changed-state screenshots + contrast; all-screen capture only when shared files change, committed as a short count summary.

## Open pull requests (DOĞRULANDI 26 Oct ~05:45)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| #132 | CIV-102 login + password (D-254) | reviewed OK, CI green on 02fafab, behind 0 (D-255) | merge (owner or live session), owner look/text approval |
Merged this session: #126 CIV-100 → b8e063f (D-250); #129 CIV-101 → b1fcaad (D-251).

## Open — owner
- Public repo (D-220/D-222/D-223), in order, each with owner confirmation:
  1. DONE 25 Oct — age secrets set, private key in owner's Passwords app.
  2. DONE 25 Oct (D-228) — default branch is `feature/authorization-workflow-phase5`. `main` and civensa-pilot untouched (Auto-Deploy off, D-227).
  3. One encrypted backup run verified — the 26 Oct 05:10Z scheduled run failed to start (D-256); waits for Actions to work again; no manual dispatch (live database = escalation).
  4. Delete old plaintext backup artifacts (includes civensa-db-backup-20261025-0507Z, D-230) — only after step 3 (D-233), owner approval.
  5. Full-history gitleaks (workflow_dispatch) — must be clean.
  6. Switch repo to public.
  7. (D-247) Move NEON_BACKUP_DATABASE_URL and BACKUP_AGE_IDENTITY into a "production" environment limited to phase5; owner enters values; owner approval. After this the Copilot workflow-approval requirement may be switched off.
- Look approvals: CIV-101 (#129) look + 31 header changes (D-251); CIV-102 when its PR is ready.
- UI redesign (D-224/D-225): 033/034, 024, 012 on the design system; CIV-100/101 polish; CIV-102 login/password next.
- (closed) Merges by the lead in live sessions (D-214); Codex "Tam erişim" ON (D-210); plaintext password files not tracked (D-217).

## Open queue — lead / scheduled run "Civensa gece kontrol" (05:41, 08:41)
1. Scheduled-run merges are refused by the session permission check (D-213, again D-255 on #132) — scheduled runs review and record; live sessions or the owner merge.
2. Ask-Ali list (13 items) artifact "Ali Abi Soruları" https://claude.ai/artifact/KVuaFCeKzTv9kQGpwRWiz8 ; ChatGPT e-mails it from the owner's Gmail Mon 26 Oct; answers in "CIVENSA-CEVAPLAR v1" format.
3. D-177 plan conversion, CIV-085, live first load — owner sets the time, live session only.
4. Measure scheduled run cost; reduce or stop if costly.
5. D-205 transition leftovers: archive old Drive state/log/rule documents ("ESKİ ... KULLANMAYIN"), add Drive pointer "KAYITLAR GITHUB'DA".
6. DeepSeek mirror GUNCEL-DURUM.md: not reachable in scheduled runs; the lead refreshes it in the next live session with the Mac linked.
7. Codex cloud fixes from PR comments: not set up (D-242); fix rounds move to Copilot (D-246/D-248).
8. LOW backlog for the next 012 task (D-251): "Kaydet" header breaks in the narrow first column; date input display format (BELİRSİZ). 024 (D-250): summary widens the 2027 column — watch only.
