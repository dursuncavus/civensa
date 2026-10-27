# CIVENSA — CURRENT STATE

Updated: 27 Oct 2026, ~05:45 Istanbul (scheduled run "Civensa gece kontrol", D-285, D-286).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.4 · `PROJECT_RULES.md` v1.4 (D-271: PRIOR ART field mandatory in every package) · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries, last modified 23 Oct (DOĞRULANDI 27 Oct 05:45).
Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Next session — start here (D-253)
Owner opens a new chat with one line: `CV Lider 33 · Claude Opus 5.5 · civensa-lead`. The lead reads this section first and works from it.
1. Merge #165 CIV-112 (reviewed OK, D-285; scheduled run could not merge). Then update-branch #168 CIV-114 (reviewed OK) and merge when every check is success. #167 CIV-115: check Codex applied the 40-min job cap (D-285); review the new head, merge when green and behind 0. Codex does not act on PR comments (D-285 addendum): send the one-line change as a Copilot fix round.
2. Owner look approval (screenshots + text-change lists, one message): CIV-109 (#154, docs/design/rollout/civ-109), CIV-111 (#161; LOW in D-282), CIV-113 (#163), then CIV-112 (#165, docs/design/rollout/civ-112) and CIV-114 (#168, docs/design/rollout/civ-114). Ask once about CIV-104 (#145).
3. After CIV-115 merges: if a test times out, the annotation names it → fix task.
4. Next D-243 screens: strategy review screens are done (042, 041, 023); write the next queue proposal; LOW backlog as one Copilot polish task.
5. Ali Abi answers: none at 23:45; data/logic packages before UI (D-243).
6. Next IDs: task CIV-116, decision D-287.

## Claude quota (BEYAN, owner screen 26 Oct 12:48)
- Weekly 47% at 18:14 Monday (session 24%); lasts until the Saturday reset at this pace. Offload large reviews to DeepSeek (D-274).
- Rule until reset (D-226): short live sessions — reviews, Ali answers and packages first; fix rounds through Copilot (D-265). Night check once a day (05:41).
- Claude Pro ends 3 Nov 2026 (BEYAN). Owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov DeepSeek runs as backup lead (BACKUP_LEAD.md).

Dispatch format (D-232, D-249): platform + environment ("Bulut → civensa") + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block. Session end: one-line handover (D-253) after this file is rewritten.
Evidence rule (D-252): one-screen changes → targeted tests + changed-state screenshots + contrast; all-screen capture only when shared files change, committed as a short count summary.

## Open pull requests (DOĞRULANDI 27 Oct ~05:45)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| #165 | CIV-112 | reviewed OK, CI green 99edef3, behind 0 (D-285) | merge (live session or owner) |
| #168 | CIV-114 | reviewed OK, CI green a80c78d (D-285) | after #165: update-branch, CI, merge |
| #167 | CIV-115 | MEDIUM: job cap 30 → 40 min; Codex will not act on the comment (D-285) | Copilot fix round, review, CI, merge |
Merged 26 Oct: #163 CIV-113 → 88c9dfb; #154 CIV-109 → 34329a7; #161 CIV-111 → 31b00e4 (D-283); #160 CIV-110 → 0b4b333 (D-282); #156 CIV-108 prototype → 633ac07 (D-277); #150 CIV-105 → 7cb58d9 (D-278; all jobs green, D-280); #148 CIV-106 → 1ed8620 (D-273); #145 CIV-104 → e0df9ce (D-268); #140 CIV-103 → 6efbe25 (D-265); #138 copilot-setup-steps → cbed4d8 (D-264); #136 production environment → d02b7cc; #132 CIV-102 → 873d361.

## Open — owner
- Look approval CIV-109 (#154), CIV-111 (#161), CIV-113 (#163) (D-283).
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
