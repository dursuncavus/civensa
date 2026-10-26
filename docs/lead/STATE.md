# CIVENSA — CURRENT STATE

Updated: 26 Oct 2026, ~12:50 Istanbul (live session CV Lider 27, D-264).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.4 · `PROJECT_RULES.md` v1.3 · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries, last modified 23 Oct (DOĞRULANDI 26 Oct 05:45).
Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Next session — start here (D-253)
Owner opens a new chat with one line: `CV Lider 28 · Claude Opus 5.5 · civensa-lead`. The lead reads this section first and works from it.
1. #140 (CIV-103): Copilot fix round 1 started 12:47 (D-264). Read Copilot's commits: only section-index.css, activity_sections_index.html, the related tests and the four PNGs may change. If workflows wait for approval, give the owner the direct link. CI green + diff OK → merge; owner approves the look and the text list.
2. Record how the Copilot round went (time, credits used on the owner's Copilot usage page, model) — this decides whether Copilot replaces D-208 for fix rounds.
3. Ali Abi answers: e-mail sent 26 Oct 07:37Z; read the reply (Gmail "Civensa – cevabınızı beklediğimiz sorular"); record decisions; data/logic packages before UI (D-243).
4. Next UI task per D-243 after CIV-103: 022/021 Genel Bakış.
5. Owner: lower the virtual card limit raised on 26 Oct (D-260); approve CIV-101/CIV-102 look + text changes (#129, #132).
6. Next IDs: task CIV-104, decision D-265.

## Claude quota (BEYAN, owner screen 25 Oct ~10:15)
- Weekly usage 21% on 25 Oct morning; at that rate it runs out Friday evening (30 Oct). October extra-usage charge: $40.30 of $45 limit.
- Rule until reset (D-226): short live sessions — reviews, Ali answers and packages first; no design iterations on Claude.
- Claude Pro ends 3 Nov 2026 (BEYAN). iOS subscription cancelled; owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov DeepSeek runs as backup lead (BACKUP_LEAD.md).

Dispatch format (D-232, D-249): platform + environment ("Bulut → civensa") + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block. Session end: one-line handover (D-253) after this file is rewritten.
Evidence rule (D-252): one-screen changes → targeted tests + changed-state screenshots + contrast; all-screen capture only when shared files change, committed as a short count summary.

## Open pull requests (DOĞRULANDI 26 Oct ~12:50)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| #140 | CIV-103 EK-1 index | CI green on 54140dc; MEDIUM uppercase finding; Copilot fixing | lead reviews Copilot diff, then merge |
Merged 26 Oct: #138 copilot-setup-steps → cbed4d8 (D-264); #139 lead records; #137; #136 production environment → d02b7cc; #132 CIV-102 → 873d361.

## Open — owner
- Public repo: DONE 26 Oct (D-261) — steps 1–7 complete; daily backups encrypted, secrets only in environment "production" (phase5).
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
