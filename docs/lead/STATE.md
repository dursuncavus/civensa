# CIVENSA — CURRENT STATE

Updated: 27 Oct 2026, ~09:45 Istanbul (live session CV Lider 33, D-287).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.5 · `PROJECT_RULES.md` v1.4 (D-271: PRIOR ART field mandatory in every package) · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries, last modified 23 Oct (DOĞRULANDI 27 Oct 05:45).
Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Next session — start here (D-253)
Owner opens a new chat with one line: `CV Lider 34 · Claude Opus 5.5 · civensa-lead`. The lead reads this section first and works from it.
1. #168 CIV-114 (reviewed OK, head 4163ad0): merge when every check is success and behind 0.
2. #167 CIV-115 (head 1119915, job cap 40 by the lead, D-287): read the "@codex review" result; merge when no major finding, CI green, behind 0.
3. CIV-116 (Rapor hazırlığı prototype, dispatched D-287): review the PR (prototype, small → lead); owner approves the look before the implementation task.
4. Owner look approval (screenshots + text-change lists, one message): CIV-109 (#154), CIV-111 (#161), CIV-113 (#163), CIV-112 (#165, docs/design/rollout/civ-112), CIV-114 (#168, docs/design/rollout/civ-114); CIV-104 (#145) once.
5. Ali Abi answers: none yet; data/logic packages before UI (D-243).
6. CIV-117 (bounded test waits, D-288) dispatched to the second Codex slot: lead reviews the PR (test-only, small).
7. CIV-118 (Rapor hazırlığı implementation, D-289) dispatched: review when the PR opens; large → DeepSeek first pass allowed (D-274, no web search).
8. CIV-119 (046 Gönderim yetkileri, D-290) dispatched: review when the PR opens.
9. eMudhra hotfix (D-291): #178 merge when green; owner merges #177 to main + Render deploy, then confirm the deploy succeeded.
10. Merge rule v1.5 (D-292). Open: #173, #167, #178, #184, #181, #183 (draft), #185, #175 — merge as each is reviewed + green.
11. Next IDs: task CIV-124, decision D-293.

## Claude quota (BEYAN, owner screen 26 Oct 12:48)
- Weekly 47% at 18:14 Monday (session 24%); lasts until the Saturday reset at this pace. Offload large reviews to DeepSeek (D-274).
- Rule until reset (D-226): short live sessions — reviews, Ali answers and packages first; fix rounds through Copilot (D-265). Night check once a day (05:41).
- Claude Pro ends 3 Nov 2026 (BEYAN). Owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov DeepSeek runs as backup lead (BACKUP_LEAD.md).

Dispatch format (D-232, D-249): platform + environment ("Bulut → civensa") + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block. Session end: one-line handover (D-253) after this file is rewritten.
Evidence rule (D-252): one-screen changes → targeted tests + changed-state screenshots + contrast; all-screen capture only when shared files change, committed as a short count summary.

## Open pull requests (DOĞRULANDI 27 Oct ~09:45)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| #168 | CIV-114 | reviewed OK; owner updated branch 4163ad0, CI running | merge when green, behind 0 |
| #167 | CIV-115 | job cap 40 pushed by the lead (D-287), head 1119915; "@codex review" running | read review, CI, merge |
| #172 | CIV-116 | merged a6c6173, owner approved (D-289) | — |
| #173 | CIV-117 | reviewed OK (D-289), CI running | merge when green, behind 0 |
| (new) | CIV-118 | dispatched D-289 | review when the PR opens |
| (new) | CIV-119 | dispatched D-290 | review when the PR opens |
Merged 27 Oct: #165 CIV-112 → 2ce4f59 (owner).
Merged 26 Oct: #163 CIV-113 → 88c9dfb; #154 CIV-109 → 34329a7; #161 CIV-111 → 31b00e4 (D-283); #160 CIV-110 → 0b4b333 (D-282); #156 CIV-108 prototype → 633ac07 (D-277); #150 CIV-105 → 7cb58d9 (D-278; all jobs green, D-280); #148 CIV-106 → 1ed8620 (D-273); #145 CIV-104 → e0df9ce (D-268); #140 CIV-103 → 6efbe25 (D-265); #138 copilot-setup-steps → cbed4d8 (D-264); #136 production environment → d02b7cc; #132 CIV-102 → 873d361.

## Open — owner
- Look approval CIV-109 (#154), CIV-111 (#161), CIV-113 (#163), CIV-112 (#165), CIV-114 (#168) (D-283, D-287).
- Look approval CIV-104 (#145): 11 text changes + screenshots (D-268).
- UI redesign (D-224/D-225): continues per D-243 order.
- (closed) Look approvals CIV-101/102/103 (D-267); public repo (D-261); merges by the lead in live sessions (D-214); Codex "Tam erişim" ON (D-210); plaintext password files not tracked (D-217).

## Open queue — lead / scheduled run "Civensa gece kontrol" (05:41 only, D-265)
1. Scheduled-run merges are refused by the session permission check (D-213, again D-255 on #132) — scheduled runs review and record; live sessions or the owner merge.
2. Ask-Ali list (13 items) artifact "Ali Abi Soruları" https://claude.ai/artifact/KVuaFCeKzTv9kQGpwRWiz8 ; e-mailed 26 Oct; answers in "CIVENSA-CEVAPLAR v1" format.
3. D-177 plan conversion, CIV-085, live first load — owner sets the time, live session only.
4. Measure scheduled run cost; reduce or stop if costly.
5. (closed, D-286) D-205 Drive archive and pointer "KAYITLAR GITHUB'DA" done.
6. DeepSeek mirror GUNCEL-DURUM.md: not reachable in scheduled runs; the lead refreshes it in the next live session with the Mac linked.
7. Codex cloud fixes from PR comments: not set up (D-242); fix rounds move to Copilot (D-246/D-248).
8. LOW backlog: shell top-right period label repeats the title on Genel Bakış (D-273);  012 date input display format (BELİRSİZ, D-251); 024 summary widens the 2027 column (D-250); 021 progress table at 390 has no scroll hint (D-268) — watch only; 022 home runs the all-department progress overview per load (D-285) — watch on pilot data.
