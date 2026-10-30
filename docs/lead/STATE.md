# CIVENSA — CURRENT STATE

Updated: 30 Oct 2026, ~13:00 Istanbul (live session CV Lider 42, D-326).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.5 · `PROJECT_RULES.md` v1.4 (D-271: PRIOR ART field mandatory in every package) · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries, last modified 23 Oct (DOĞRULANDI 30 Oct 05:45).
Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Next session — start here (D-253)
Claude live (CV Lider 42, 30 Oct). Go-live done (D-323): civensa-pilot on main 7ef5a20, Alembic c086a1b2c3d4. CIV-157 and CIV-158 merged; Actions first-load rehearsal PASS (D-326).
Claude's next session: `CV Lider 43 · Claude Opus 5.5 · civensa-lead`. Read this section and the last decision in DECISIONS.md first.
1. LIVE FIRST LOAD (D-315 step 6, escalation): owner runs docs/first-load/live-runbook.md on phase5 fa7848f or newer (his Mac repo must be updated: git pull + venv). Lead guides block by block: 1 source check → 2 rehearsal (done: run 41035318472 with backup 41029891358; repeat only if >48 h or data changed) → 3 stop data entry + fresh backup → 4 cleanup plan (expect 93 personnel/SGK) → 5 cleanup apply → 6 plan (34/64/263/291/1340, 0 skipped) → 7 apply (confirmation cbbf9018302d) → 8 zero-write plan → record counts. Rollback = restore the step-3 backup (section 10).
2. Approved book is final (D-324): book checks diagnostic; İşletme loaded; 5 İşletme activity-code mismatches stay reported.
3. Owner looks pending: CIV-150 (001), CIV-151 (039/040), CIV-152 (006/015), CIV-153 (038), CIV-154 (095). One gallery artifact (screenshots in docs/design/rollout/**).
4. After the first load: D-177 İç Kontrol plan conversion (owner attaches 2024–2026 plan PDF), CIV-085. Next screens: 002/003 (003 waits for Ali); INDEX check of 069, 077–097 (D-314).
5. Small tasks to package: /health readiness + Alembic head field (D-318); lead-docs guard should pass release PRs phase5 → main (D-322).
6. Quota (BEYAN 29 Oct 20:49): week 76% then, reset Sat 00:00; owner: keep working until then.
Next IDs: task CIV-159, decision D-327.

## Claude quota (BEYAN, owner 27 Oct 16:21)
- Session 11%, week 67%, weekly reset Saturday 00:00 (D-300). Copilot 96 / 1,500 credits, reset 1 Nov.
- Claude Pro ends 3 Nov 2026 (BEYAN). Owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov DeepSeek runs as backup lead (BACKUP_LEAD.md).

Dispatch format (D-232, D-249): platform + environment ("Bulut → civensa") + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block. Session end: one-line handover (D-253) after this file is rewritten.
Evidence rule (D-252): one-screen changes → targeted tests + changed-state screenshots + contrast; all-screen capture only when shared files change, committed as a short count summary.

## Open pull requests (DOĞRULANDI 30 Oct ~13:00, D-326)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| — | none open | — | — |
Merged 30 Oct (D-326): #266 CIV-158 → fa7848f · #267 D-325 records → 329b381.
Merged 30 Oct (D-325): #262 CIV-157 → 7f6029e · #265 D-324 records → 3a3f208.
Merged 30 Oct (D-324): #264 D-323 records → bb05bcb.
Merged 30 Oct (D-322): #261 release phase5 → main (owner) → 7ef5a20 · #251 CIV-153 → 516e90c · #252 CIV-154 → f17dc64 · #260 lead records + approved IDML → 6b1fb71.
Merged 30 Oct (D-319): #257 CIV-156 → 2f2276c · #256 CIV-155 → 3544177 · #250 CIV-152 → 5936096 · #259 lead rehearsal diagnostics → a4bf3ef.
Merged 29 Oct (D-312): #246 CIV-151 → 0b8c72a · #241 CIV-149 (owner) → 49abd45.
Merged 29 Oct (D-311): #244 CIV-150 → 7e4335b.
Merged 28–29 Oct by the owner (D-309): #232 CIV-144 · #234 CIV-145 → 22e35b7 · #236 CIV-146 → eff4a06 · #238 CIV-147 → f1b7adb · #239 CIV-148 → c622bf2.
Merged 28 Oct (D-308): #228 CIV-143 → 14c692c · #230 night record → f0f1222.
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
3. D-177 plan conversion, CIV-085, live first load — after the go-live deploy (D-315), live session only.
4. Measure scheduled run cost; reduce or stop if costly.
5. (closed, D-286) D-205 Drive archive and pointer "KAYITLAR GITHUB'DA" done.
6. DeepSeek mirror GUNCEL-DURUM.md: not reachable in scheduled runs; the lead refreshes it in the next live session with the Mac linked (still pending 28 Oct).
7. Codex cloud fixes from PR comments: not set up (D-242); fix rounds move to Copilot (D-246/D-248).
8. LOW backlog: shell top-right period label repeats the title on Genel Bakış (D-273);  012 date input display format (BELİRSİZ, D-251); 024 summary widens the 2027 column (D-250); 021 progress table at 390 has no scroll hint (D-268) — watch only; 022 home runs the all-department progress overview per load (D-285) — watch on pilot data.
