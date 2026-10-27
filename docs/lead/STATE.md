# CIVENSA — CURRENT STATE

Updated: 27 Oct 2026, ~16:25 Istanbul (live session CV Lider 34, D-297..D-300).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.5 · `PROJECT_RULES.md` v1.4 (D-271: PRIOR ART field mandatory in every package) · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries, last modified 23 Oct (DOĞRULANDI 27 Oct 05:45).
Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Next session — start here (D-253)
Owner opens a new chat with one line: `CV Lider 35 · Claude Opus 5.5 · civensa-lead`. The lead reads this section first and works from it.
1. Quota (D-300): Claude week 67% at 16:21 Tue, reset Saturday 00:00. No new screen packages until reset; review/merge only, short sessions. DeepSeek first pass for large PRs (CIV-135).
2. Merge rule HIERARCHY v1.5 (D-292). Copilot pushes wait for approval → lead empty commit or update-branch runs CI. Copilot sometimes rewrites tests/artifacts/** → restore from phase5. CI setup is now fast (D-298); a "runner setup" error → rerun failed jobs.
3. Design rules for every review and package: D-292 (label next to value, no far-edge status) + D-299 (no split of what fits one column, no duplicate text, one-line summaries, group by status, status = text + colour).
4. Open, in order: #195 CIV-129 (CI on 9c0dbfc → merge → owner look 017/018); Copilot drafts #199 CIV-128, #201 CIV-133, #205 CIV-134, #207 CIV-136, #209 CIV-137, #192 CIV-127 → review each when ready, CI, merge, owner look (screenshots in docs/design/rollout/civ-1xx/); Codex CIV-135 (007/008) → owner presses "PR oluştur" → DeepSeek first pass → lead review.
5. Remaining screens after reset: 003 (needs Ali), 025–028, 031 (İç Kontrol).
6. Ali Abi answers: none yet.
7. Next IDs: task CIV-138, decision D-301.

## Claude quota (BEYAN, owner 27 Oct 16:21)
- Session 11%, week 67%, weekly reset Saturday 00:00 (D-300). Copilot 96 / 1,500 credits, reset 1 Nov.
- Claude Pro ends 3 Nov 2026 (BEYAN). Owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov DeepSeek runs as backup lead (BACKUP_LEAD.md).

Dispatch format (D-232, D-249): platform + environment ("Bulut → civensa") + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block. Session end: one-line handover (D-253) after this file is rewritten.
Evidence rule (D-252): one-screen changes → targeted tests + changed-state screenshots + contrast; all-screen capture only when shared files change, committed as a short count summary.

## Open pull requests (DOĞRULANDI 27 Oct ~16:25)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| #195 | CIV-129 017/018 | CI running on 9c0dbfc | merge, owner look |
| #199 | CIV-128 reconciliation short status | Copilot draft | review |
| #201 | CIV-133 activity reports rows | Copilot draft | review, owner look |
| #205 | CIV-134 users table + one-line summary | Copilot draft | review, owner look |
| #207 | CIV-136 structure status switch | Copilot draft | review, owner look |
| #209 | CIV-137 operations checks grouped | Copilot draft | review, owner look |
| #192 | CIV-127 016 audit | Copilot draft | review, owner look |
| (Codex) | CIV-135 007/008 | Codex running | PR → DeepSeek → review |
Merged 27 Oct: #203 CIV-131 → 2d1de5f · #202 CIV-132 → f441bdf · #196 CIV-130 → db5aa88 · #194 CIV-126 → c810bd3 · #188 CIV-124 → bb03104 · CI fix D-298 (cc34fce) · #185 CIV-123 → 758a02b · #165 CIV-112 (owner) · #168 CIV-114 · #179 CIV-119 · #173 CIV-117 · #178 certifi phase5 · #184 CIV-122 · #167 CIV-115 · #181 CIV-120 · #175 CIV-118 · #186 rule v1.5 + push CI · #183 CIV-121 · #189 CIV-125 · #172 CIV-116 prototype · main: #177 certifi → ce0cb4d, live on civensa-pilot (D-293).
Merged 26 Oct: #163 CIV-113 → 88c9dfb; #154 CIV-109 → 34329a7; #161 CIV-111 → 31b00e4 (D-283); #160 CIV-110 → 0b4b333 (D-282); #156 CIV-108 prototype → 633ac07 (D-277); #150 CIV-105 → 7cb58d9 (D-278; all jobs green, D-280); #148 CIV-106 → 1ed8620 (D-273); #145 CIV-104 → e0df9ce (D-268); #140 CIV-103 → 6efbe25 (D-265); #138 copilot-setup-steps → cbed4d8 (D-264); #136 production environment → d02b7cc; #132 CIV-102 → 873d361.

## Open — owner
- Look approvals done for CIV-109/111/112/113/114/118/119/120/121 (D-295), CIV-122/123 (D-297). CIV-124 (D-300). Pending: CIV-127, CIV-129, and the fix rounds CIV-133/134/136/137.
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
