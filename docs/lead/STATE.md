# CIVENSA — CURRENT STATE

Updated: 3 Nov 2026 ~16:05 Istanbul (live session CV Lider 52, D-376).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.5 · `PROJECT_RULES.md` v1.4 (D-271: PRIOR ART field mandatory in every package) · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries after 31 Oct (DOĞRULANDI 3 Nov 05:45, file unchanged since 23 Oct).
Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Next session — start here (D-253)
Claude live (CV Lider 52, 3 Nov ~15:20–16:05). Release #298 live; /health ready=true, migration c162 (D-350). On phase5, not on main/live: CIV-163 (b2a500f), CIV-166 (758522c), CIV-167 (21812ec), CIV-165 (a6cdc83).
Claude's next session: `CV Lider 53 · Claude Opus 5.5 · civensa-lead`. First job: review the CIV-168 PR (2026 backup rehearsal workflow). Read this section and the last decision in DECISIONS.md first. Session start also checks Gmail for Ali Abi's mails (D-361).
1. Releases live (D-346/D-350). Only Ali Abi uses the system; departments are not opened until the infrastructure is complete — data comes from the old system (BEYAN, D-351/D-352). Render stays Free; Starter ($7/month) on department rollout day.
2. Codex: CIV-165 #328 merged → a6cdc83 (D-375). CIV-168 (2026 PP backup rehearsal, D-376) dispatched 3 Nov ~16:05 → lead reviews its PR.
3. 2026 PP load path (D-372/D-376): CIV-168 PR review → merge → lead dispatches db-backup + "2026 PP verified backup rehearsal" → PASS → owner live load from a phase5 checkout (`scripts/first_load_live.py --year 2026`, plan → fresh backup → apply with 1aaa0bb81c3c → resume plan), same as D-327. Ready before 1 Jan 2027; data-entry deadline ~15–20 Jan.
4. Ask Ali (new, D-375): printed 2026 book inconsistencies — Bilgi İşlem / Çevre Koruma / İmar cost vs economic totals differ (496 / 775 / 989 TL); Ruhsat ve Denetim economic table wrong totals; Zabıta and Veteriner economic tables show the total as "Diğer Bütçe Dışı Kaynak". Loaded as printed; FR 2026 needs the correct figures.
5. İç Kontrol (D-358 first to departments): row check CLOSED (D-366). Waits only for Ali: 7 questions + 8 mappings in "CV İç Kontrol Dönüşümü – Ortak Liste" (https://docs.google.com/spreadsheets/d/1O4DmrNnBfcz9HJuxAXxGwMCvukTo2467HobZptmz-XI/edit), 3 monitoring assumptions, which half-year + deadline. Then lead edits workbook, owner uploads on civensa-pilot → maps 8 names → commits draft. Ali also: list of directorate merges/closures since 2024 (D-359 gap b); 70-question list compare (D-336).
6. Faaliyet Raporu (D-354): 7 AR items PARTIAL, wait for Ali/Mali Hizmetler inputs; checklist "FR Girdileri" https://claude.ai/artifact/5bGm5xrVbPSjM7wfv1qrMA. Needed samples: one current directorate indicator Excel (D-361 FR5), Mali Hizmetler budget template (ML1). Open to Ali: approval steps in Civensa or on paper (PR2).
7. Watch reactions to the 554 book-check items (D-324, D-352). LOW backlog (D-328). UI: only 002/003 left, waits for Ali (D-345).
8. One live lead session at a time (D-363). Owner: check Claude Design standalone site before 14 Dec 2026 (D-363).
9. Quota: weekly reset Sat 00:00. Claude Pro renewal BELİRSİZ (sessions still run 3 Nov).
Next IDs: task CIV-169, decision D-377.

## Claude quota (BEYAN, owner 27 Oct 16:21)
- Session 11%, week 67%, weekly reset Saturday 00:00 (D-300). Copilot 96 / 1,500 credits, reset 1 Nov.
- Claude Pro ends 3 Nov 2026 (BEYAN). Owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov DeepSeek runs as backup lead (BACKUP_LEAD.md).

Dispatch format (D-232, D-249): platform + environment ("Bulut → civensa") + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block. Session end: one-line handover (D-253) after this file is rewritten.
Evidence rule (D-252): one-screen changes → targeted tests + changed-state screenshots + contrast; all-screen capture only when shared files change, committed as a short count summary.

## Open pull requests (DOĞRULANDI 3 Nov ~16:05, D-376)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| — | — | none open at 16:05 (CIV-165 merged, D-375); CIV-168 PR expected | lead reviews CIV-168 PR |
Merged 3 Nov (D-375): #328 CIV-165 → a6cdc83. (D-373): #321 CIV-167 → 21812ec.
Merged 31 Oct (D-350): #298 release phase5 → main (owner) → 503e970, deployed · #299 D-349 → 6999a2f.
Merged 31 Oct (D-349): #296 CIV-162 → 8ff85f9 · #297 D-348 → ac9b7c8.
Merged 31 Oct (D-346): #292 release phase5 → main (owner) → 80b6ca1, deployed · #293 D-345 → 6d9be83.
Merged 31 Oct (D-343): #289 CIV-160 → e061e93 · #288 D-342 → 85d3e9b · #287 D-341 → a5c40f6.
Merged 30 Oct (D-339): #284 CIV-161 → fa2f693 · #283 D-338 → c4fa7c1 · #282 D-337 → fee1955.
Merged 30 Oct (D-337): #280 CIV-085 → b299845 · #281 D-336 → cd3a514 · #279 D-335 → 3b724ac.
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
3. (D-331) D-177 conversion done, import waits for Ali; live first load done (D-327); CIV-085 next — live session only.
4. Measure scheduled run cost; reduce or stop if costly.
5. (closed, D-286) D-205 Drive archive and pointer "KAYITLAR GITHUB'DA" done.
6. (done 3 Nov ~15:50, CV Lider 52) DeepSeek mirror GUNCEL-DURUM.md refreshed from STATE.md (D-376) with the Mac linked; YEDEK-KAYIT.md has no entry after 29 Oct (already covered by D-309). Refresh again in the next live session with the Mac linked.
7. Codex cloud fixes from PR comments: not set up (D-242); fix rounds move to Copilot (D-246/D-248).
8. LOW backlog: shell top-right period label repeats the title on Genel Bakış (D-273);  012 date input display format (BELİRSİZ, D-251); 024 summary widens the 2027 column (D-250); 021 progress table at 390 has no scroll hint (D-268) — watch only; 022 home runs the all-department progress overview per load (D-285) — watch on pilot data.
