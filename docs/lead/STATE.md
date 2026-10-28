# CIVENSA — CURRENT STATE

Updated: 28 Oct 2026, ~10:15 Istanbul (live session CV Lider 37, D-308).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.5 · `PROJECT_RULES.md` v1.4 (D-271: PRIOR ART field mandatory in every package) · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries, last modified 23 Oct (DOĞRULANDI 27 Oct 05:45).
Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Next session — start here (D-253)
DEEPSEEK BACKUP LEAD UNTIL SAT 31 OCT 00:00 (D-308, owner decision to save Claude quota). Claude handles only what BACKUP_LEAD.md reserves for the lead; returns after the weekly reset.
Claude's next session: `CV Lider 38 · Claude Opus 5.5 · civensa-lead`. Read this section, the last decision in DECISIONS.md, and "Civensa Yedek Kaydı" (Drive) first; re-check every DeepSeek MERGE OK and dispatched task.
Allowed work for DeepSeek (BACKUP_LEAD.md "YOU MAY"):
1. #228 CIV-143 users table — lead-reviewed head 1bd4180 (D-308). If CI is green and behind 0: MERGE OK, owner merges. If Copilot pushes again: review that head first.
2. #232 CIV-144 (Copilot) — 007/008 value row on ONE baseline line (owner 10:00: all six items bottom-aligned, no "·") + evidence list: file line indented under its source, smaller gap inside a source than between sources; also the "İncelenmeli" state (owner 10:02). Review against issue #231 and lead comments 6462795106, 6462821999, 6462865204. Check the 1440 screenshots for the two defects before MERGE OK.
3. One Codex task at a time, next ID CIV-145: bring the İç Kontrol screens (031; templates app/templates/internal_control/*.html) onto the design system per D-243 (existing components only; same pattern and evidence rule D-252 as CIV-127..140). Codex reads the repo itself; DeepSeek writes the package in the standard format incl. PRIOR ART (D-271). 003 waits for Ali; 025–028 wait for the lead (screen definitions not in the repo).
4. Owner looks: gallery "Civensa Onay 2" https://claude.ai/artifact/3N57MjqiTX6ud7q4Krij9c (017, users, 007/008) — record the owner's answers in the backup log.
Not allowed: anything under "YOU MUST NOT"; merges into staging/main; docs/lead edits.
Next IDs: task CIV-145, decision D-309.

## Claude quota (BEYAN, owner 27 Oct 16:21)
- Session 11%, week 67%, weekly reset Saturday 00:00 (D-300). Copilot 96 / 1,500 credits, reset 1 Nov.
- Claude Pro ends 3 Nov 2026 (BEYAN). Owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov DeepSeek runs as backup lead (BACKUP_LEAD.md).

Dispatch format (D-232, D-249): platform + environment ("Bulut → civensa") + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block. Session end: one-line handover (D-253) after this file is rewritten.
Evidence rule (D-252): one-screen changes → targeted tests + changed-state screenshots + contrast; all-screen capture only when shared files change, committed as a short count summary.

## Open pull requests (DOĞRULANDI 28 Oct ~05:45)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| #228 (issue #227) | CIV-143 users table follow-up | ready, head 1bd4180 reviewed by lead (D-308), CI running | merge after green (DeepSeek MERGE OK → owner) → owner look |
| #232 (issue #231) | CIV-144 value row + evidence list | Copilot draft | review → CI → merge → owner look |
Merged 27 Oct late (D-304/D-306): #222 CIV-141 → 70fc4da · #223 CIV-142 → c3ccfcc.
Merged 27 Oct evening (D-303): #199 CIV-128 → 0200f60 · #205 CIV-134 → 5106ad5 · #209 CIV-137 → c6a8fab · #218 CIV-138 → 2b1e7df · #207 CIV-136 → 1f74a2d · #214 CIV-139 → 6ba0e55 · #216 CIV-140 → 0e2cf1c.
Merged 27 Oct: #211 CIV-135 → 43f4de6 · #192 CIV-127 → 97f2225 · #201 CIV-133 → 5b683c4 · #195 CIV-129 → fd930c9 · #203 CIV-131 → 2d1de5f · #202 CIV-132 → f441bdf · #196 CIV-130 → db5aa88 · #194 CIV-126 → c810bd3 · #188 CIV-124 → bb03104 · CI fix D-298 (cc34fce) · #185 CIV-123 → 758a02b · #165 CIV-112 (owner) · #168 CIV-114 · #179 CIV-119 · #173 CIV-117 · #178 certifi phase5 · #184 CIV-122 · #167 CIV-115 · #181 CIV-120 · #175 CIV-118 · #186 rule v1.5 + push CI · #183 CIV-121 · #189 CIV-125 · #172 CIV-116 prototype · main: #177 certifi → ce0cb4d, live on civensa-pilot (D-293).
Merged 26 Oct: #163 CIV-113 → 88c9dfb; #154 CIV-109 → 34329a7; #161 CIV-111 → 31b00e4 (D-283); #160 CIV-110 → 0b4b333 (D-282); #156 CIV-108 prototype → 633ac07 (D-277); #150 CIV-105 → 7cb58d9 (D-278; all jobs green, D-280); #148 CIV-106 → 1ed8620 (D-273); #145 CIV-104 → e0df9ce (D-268); #140 CIV-103 → 6efbe25 (D-265); #138 copilot-setup-steps → cbed4d8 (D-264); #136 production environment → d02b7cc; #132 CIV-102 → 873d361.

## Open — owner
- Look approvals D-303: CIV-127/128/129/131/132/133/135/136/137/138/139 approved; 017 → CIV-141, 047 users → CIV-142; CIV-140 pending.
- Look approvals done for CIV-109/111/112/113/114/118/119/120/121 (D-295), CIV-122/123 (D-297). CIV-124 (D-300). Pending: CIV-127, CIV-129, CIV-133, CIV-135 (merged), CIV-134/136/137 (open).
- Look approval CIV-104 (#145): 11 text changes + screenshots (D-268).
- UI redesign (D-224/D-225): continues per D-243 order.
- (closed) Look approvals CIV-101/102/103 (D-267); public repo (D-261); merges by the lead in live sessions (D-214); Codex "Tam erişim" ON (D-210); plaintext password files not tracked (D-217).

## Open queue — lead / scheduled run "Civensa gece kontrol" (05:41 only, D-265)
1. Scheduled-run merges are refused by the session permission check (D-213, again D-255 on #132) — scheduled runs review and record; live sessions or the owner merge.
2. Ask-Ali list (13 items) artifact "Ali Abi Soruları" https://claude.ai/artifact/KVuaFCeKzTv9kQGpwRWiz8 ; e-mailed 26 Oct; answers in "CIVENSA-CEVAPLAR v1" format.
3. D-177 plan conversion, CIV-085, live first load — owner sets the time, live session only.
4. Measure scheduled run cost; reduce or stop if costly.
5. (closed, D-286) D-205 Drive archive and pointer "KAYITLAR GITHUB'DA" done.
6. DeepSeek mirror GUNCEL-DURUM.md: not reachable in scheduled runs; the lead refreshes it in the next live session with the Mac linked (still pending 28 Oct).
7. Codex cloud fixes from PR comments: not set up (D-242); fix rounds move to Copilot (D-246/D-248).
8. LOW backlog: shell top-right period label repeats the title on Genel Bakış (D-273);  012 date input display format (BELİRSİZ, D-251); 024 summary widens the 2027 column (D-250); 021 progress table at 390 has no scroll hint (D-268) — watch only; 022 home runs the all-department progress overview per load (D-285) — watch on pilot data.
