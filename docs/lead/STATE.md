# CIVENSA — CURRENT STATE

Updated: 27 Oct 2026, ~21:00 Istanbul (live session CV Lider 36, D-303).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.5 · `PROJECT_RULES.md` v1.4 (D-271: PRIOR ART field mandatory in every package) · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries, last modified 23 Oct (DOĞRULANDI 27 Oct 05:45).
Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Next session — start here (D-253)
Owner opens a new chat with one line: `CV Lider 37 · Claude Opus 5.5 · civensa-lead`. The lead reads this section AND the last decision in DECISIONS.md first.
1. Quota (D-300): Claude week 67% at 16:21 Tue + two review sessions since; reset Saturday 00:00. No new Codex screen packages until reset; owner-look fixes go to Copilot.
2. Merge rule HIERARCHY v1.5 (D-292). Copilot issues: POST /issues, then POST /issues/{n}/assignees with "copilot-swe-agent[bot]". Copilot pushes wait for approval → lead empty commit via git push (git-data REST is blocked) or PUT update-branch runs CI. Draft PR → POST /pulls/{n}/ccr/ready_for_review first. Restore tests/artifacts/** from phase5 if touched.
3. Design rules for every review and package: D-292 + D-299.
4. Open, in order: #216 CIV-140 (Copilot test fix requested; watcher may have merged it — check) → then show the owner the CIV-140 look (add to gallery artifact https://claude.ai/artifact/DLJU4E5RC2zX6cdh3sYDJZ by republishing with url); CIV-141 issue #220 (017 widths/dates); CIV-142 issue #221 (users table). For each: review, CI, merge, owner look via gallery.
5. Remaining screens after reset: 003 (needs Ali), 025–028, 031 (İç Kontrol).
6. Ali Abi answers: none yet.
7. Next IDs: task CIV-143, decision D-304. Codex idle by design (D-300). Long chat → new chat each session.

## Claude quota (BEYAN, owner 27 Oct 16:21)
- Session 11%, week 67%, weekly reset Saturday 00:00 (D-300). Copilot 96 / 1,500 credits, reset 1 Nov.
- Claude Pro ends 3 Nov 2026 (BEYAN). Owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov DeepSeek runs as backup lead (BACKUP_LEAD.md).

Dispatch format (D-232, D-249): platform + environment ("Bulut → civensa") + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block. Session end: one-line handover (D-253) after this file is rewritten.
Evidence rule (D-252): one-screen changes → targeted tests + changed-state screenshots + contrast; all-screen capture only when shared files change, committed as a short count summary.

## Open pull requests (DOĞRULANDI 27 Oct ~21:00)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| #216 | CIV-140 graphical indicator summary | ready, test fix asked from Copilot | CI → merge → owner look |
| (issue #220) | CIV-141 017 widths + dates | Copilot assigned | review → CI → merge → owner look |
| (issue #221) | CIV-142 users table rhythm | Copilot assigned | review → CI → merge → owner look |
Merged 27 Oct evening (D-303): #199 CIV-128 → 0200f60 · #205 CIV-134 → 5106ad5 · #209 CIV-137 → c6a8fab · #218 CIV-138 → 2b1e7df · #207 CIV-136 → 1f74a2d · #214 CIV-139 → 6ba0e55.
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
6. DeepSeek mirror GUNCEL-DURUM.md: not reachable in scheduled runs; the lead refreshes it in the next live session with the Mac linked.
7. Codex cloud fixes from PR comments: not set up (D-242); fix rounds move to Copilot (D-246/D-248).
8. LOW backlog: shell top-right period label repeats the title on Genel Bakış (D-273);  012 date input display format (BELİRSİZ, D-251); 024 summary widens the 2027 column (D-250); 021 progress table at 390 has no scroll hint (D-268) — watch only; 022 home runs the all-department progress overview per load (D-285) — watch on pilot data.
