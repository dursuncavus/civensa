# CIVENSA — CURRENT STATE

Updated: 26 Oct 2026, ~10:50 Istanbul (live session CV Lider 25, D-257).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.4 · `PROJECT_RULES.md` v1.3 · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries, last modified 23 Oct (DOĞRULANDI 26 Oct 05:45).
Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Next session — start here (D-253)
Owner opens a new chat with one line: `CV Lider 26 · Claude Opus 5.5 · civensa-lead`. The lead reads this section first and works from it.
0. URGENT (D-258): no CI and no daily backup since 25 Oct 21:43Z (last good backup 25 Oct 05:07Z). Cause BELİRSİZ — NOT the budget ($50.69 of $80 used). Check Billing Overview / Payment history with the owner first.
1. Ali Abi answers: read Gmail "CIVENSA-CEVAPLAR v1" (not arrived 26 Oct 10:45); record decisions; write Codex packages the same day (data/logic before UI, D-243).
2. Public repo step 3 → 6 as soon as Actions runs again (lasting fix for Actions cost, D-257).
3. Copilot postponed until the repo is public (D-257).
4. Next UI task per D-243: 010/009 EK-1 section index; bundle related screens and the D-251 LOW items (D-252).
5. Owner: approve CIV-102 look + listed text changes (#132, merged 873d361).
6. Next IDs: task CIV-103, decision D-259.

## Claude quota (BEYAN, owner screen 25 Oct ~10:15)
- Weekly usage 21% on 25 Oct morning; at that rate it runs out Friday evening (30 Oct). October extra-usage charge: $40.30 of $45 limit.
- Rule until reset (D-226): short live sessions — reviews, Ali answers and packages first; no design iterations on Claude.
- Claude Pro ends 3 Nov 2026 (BEYAN). iOS subscription cancelled; owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov DeepSeek runs as backup lead (BACKUP_LEAD.md).

Dispatch format (D-232, D-249): platform + environment ("Bulut → civensa") + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block. Session end: one-line handover (D-253) after this file is rewritten.
Evidence rule (D-252): one-screen changes → targeted tests + changed-state screenshots + contrast; all-screen capture only when shared files change, committed as a short count summary.

## Open pull requests (DOĞRULANDI 26 Oct ~10:50)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| #134 | lead records D-255–D-257 | guard cannot run (Actions budget) | merge when guard green |
Merged 25–26 Oct: #126 CIV-100 → b8e063f; #129 CIV-101 → b1fcaad; #132 CIV-102 → 873d361 (D-257).

## Open — owner
- Public repo (D-220/D-222/D-223), in order, each with owner confirmation:
  1. DONE 25 Oct — age secrets set, private key in owner's Passwords app.
  2. DONE 25 Oct (D-228) — default branch is `feature/authorization-workflow-phase5`. `main` and civensa-pilot untouched (Auto-Deploy off, D-227).
  3. One encrypted backup run verified — the 26 Oct 05:10Z scheduled run failed to start (D-256); waits for the Actions budget (D-257); no manual dispatch (live database = escalation).
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
