# CIVENSA — CURRENT STATE

Updated: 26 Oct 2026, ~18:55 Istanbul (live session CV Lider 31, D-282).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.4 · `PROJECT_RULES.md` v1.4 (D-271: PRIOR ART field mandatory in every package) · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries, last modified 23 Oct (DOĞRULANDI 26 Oct 05:45).
Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Next session — start here (D-253)
Owner opens a new chat with one line: `CV Lider 32 · Claude Opus 5.5 · civensa-lead`. The lead reads this section first and works from it.
1. CIV-109 #154 and CIV-111 #161: CI was running at 20:50 (shard "test (18, 1)" slow again). Merge each only when every check on the exact head is success and behind 0; #154 also needs the "@codex review" answer. Then show the owner the screenshots for look approval (CIV-109, CIV-111 incl. text changes).
2. CIV-113 (041 PP tamamlanma listesi): dispatched to Codex (D-282) → review, CI, merge.
3. CIV-112 (022 task list): package ready; dispatch to Codex right after #154 merges.
4. Next in D-243 order: 023 Müdürlük veri girişi (strategy view of /department/{id}) — check overlap with 024 (CIV-0xx, same template) before writing.
5. Owner look approval for CIV-104 (#145) still open (probably superseded by D-270..D-277 — ask once).
6. Ali Abi answers: none at 20:50; data/logic packages before UI (D-243).
7. Shard "test (18, 1)" hung once (D-278) and is slow again: if it stalls > 30 min, cancel and re-run; if it repeats, write a CI task (split shards / find the slow test via --durations).
8. Next IDs: task CIV-114, decision D-283.

## Claude quota (BEYAN, owner screen 26 Oct 12:48)
- Weekly 47% at 18:14 Monday (session 24%); lasts until the Saturday reset at this pace. Offload large reviews to DeepSeek (D-274).
- Rule until reset (D-226): short live sessions — reviews, Ali answers and packages first; fix rounds through Copilot (D-265). Night check once a day (05:41).
- Claude Pro ends 3 Nov 2026 (BEYAN). Owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov DeepSeek runs as backup lead (BACKUP_LEAD.md).

Dispatch format (D-232, D-249): platform + environment ("Bulut → civensa") + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block. Session end: one-line handover (D-253) after this file is rewritten.
Evidence rule (D-252): one-screen changes → targeted tests + changed-state screenshots + contrast; all-screen capture only when shared files change, committed as a short count summary.

## Open pull requests (DOĞRULANDI 26 Oct ~18:35)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| #154 | CIV-109 | ready, CI + @codex review (D-282) | merge when all success |
| #161 | CIV-111 | CI after lead update-branch | merge when all success |
| — | CIV-113 | dispatched to Codex ~20:50 | PR expected |
| — | CIV-112 | package ready | dispatch after #154 |
Merged 26 Oct: #160 CIV-110 → 0b4b333 (D-282); #156 CIV-108 prototype → 633ac07 (D-277); #150 CIV-105 → 7cb58d9 (D-278; all jobs green, D-280); #148 CIV-106 → 1ed8620 (D-273); #145 CIV-104 → e0df9ce (D-268); #140 CIV-103 → 6efbe25 (D-265); #138 copilot-setup-steps → cbed4d8 (D-264); #136 production environment → d02b7cc; #132 CIV-102 → 873d361.

## Open — owner
- Look approval CIV-104 (#145): 11 text changes + screenshots (D-268).
- UI redesign (D-224/D-225): continues per D-243 order.
- (closed) Look approvals CIV-101/102/103 (D-267); public repo (D-261); merges by the lead in live sessions (D-214); Codex "Tam erişim" ON (D-210); plaintext password files not tracked (D-217).

## Open queue — lead / scheduled run "Civensa gece kontrol" (05:41 only, D-265)
1. Scheduled-run merges are refused by the session permission check (D-213, again D-255 on #132) — scheduled runs review and record; live sessions or the owner merge.
2. Ask-Ali list (13 items) artifact "Ali Abi Soruları" https://claude.ai/artifact/KVuaFCeKzTv9kQGpwRWiz8 ; e-mailed 26 Oct; answers in "CIVENSA-CEVAPLAR v1" format.
3. D-177 plan conversion, CIV-085, live first load — owner sets the time, live session only.
4. Measure scheduled run cost; reduce or stop if costly.
5. D-205 transition leftovers: archive old Drive state/log/rule documents ("ESKİ ... KULLANMAYIN"), add Drive pointer "KAYITLAR GITHUB'DA".
6. DeepSeek mirror GUNCEL-DURUM.md: not reachable in scheduled runs; the lead refreshes it in the next live session with the Mac linked.
7. Codex cloud fixes from PR comments: not set up (D-242); fix rounds move to Copilot (D-246/D-248).
8. LOW backlog: shell top-right period label repeats the title on Genel Bakış (D-273);  012 date input display format (BELİRSİZ, D-251); 024 summary widens the 2027 column (D-250); 021 progress table at 390 has no scroll hint (D-268) — watch only.
