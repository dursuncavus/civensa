# CIVENSA — CURRENT STATE

Updated: 5 Nov 2026 ~09:35 Istanbul (CV Lider 62, D-420).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.8 (D-408: the lead also codes; Codex reviews its PRs) · `PROJECT_RULES.md` v1.4 (D-271: PRIOR ART field mandatory in every package) · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries after 31 Oct (DOĞRULANDI 3 Nov 05:45, file unchanged since 23 Oct).
Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Next session — start here (D-253)
Release #384 live (main c46cf4d, 4 Nov 21:11; D-410): CIV-175/176/177/178 are live, /health ok, migration c162a1b2c3d4. 9 Nov page for Ali: https://claude.ai/artifact/1TNVQZsZG9aWfmFNAPibZn (D-403). CIV-179 #382 (InDesign tagged text) PARKED until the owner's new Faaliyet Raporu template exists (D-410); mechanism proven in InDesign.
CV Lider 62 (5 Nov ~09:20, DOĞRULANDI): no answer from Ali Abi; CIV-181 (K5 audit CSV keys + department Word name + ACTION_LABELS) dispatched to Codex (D-418) and CIV-182 (İdare meclis sunumu recipe, D-419) in parallel → review both PRs. Meclis deck needs a content layer (photos, spotlights, öne çıkan işler; D-420): owner sends last meclis presentation → lead researches + specs. Owner tests Ornek-Sunum.html on the hall computer.
CV Lider 61 (4 Nov ~21:25, DOĞRULANDI): no mail from Ali Abi; only open PR #382 (parked); the 18:03Z db-backup failure mail is the refused main dispatch already covered by D-410. Sunum work (D-411–D-415) continues in CV Lider 62 if the owner has remarks on the Fen İşleri presentation; local prototype files are not in the repo (artifact + files sent to the owner). Claude's next session: `CV Lider 62 · Claude Opus 5.5 · civensa-lead`. First job: Gmail check (D-361) → Ali Abi's answers (thread "Civensa – 2026 Faaliyet Raporu soruları", D-404; he returns 9 Nov). After his 2026 mapping upload: re-measure the 2026 snapshot and K4 (full PP PDF, 105 s of 120 s locally, D-409), then Strategy publishes 2026 via "Onaylı kitaptan yayınla". No Codex work is unblocked before Ali's answers.
1. Releases live (D-346/D-350). Only Ali Abi uses the system; departments are not opened until the infrastructure is complete — data comes from the old system (BEYAN, D-351/D-352). Render stays Free; Starter ($7/month) on department rollout day.
2. Codex: CIV-172 #354 merged (D-393); CIV-174 #358 merged after two Copilot rounds (D-394): warnings stored compactly (10.9 KB), builder no longer parses snapshots. CIV-175 #369 reviewed (D-401): 2026 snapshot 25.8 MB, 21.2 MB of it repeated cost_reconciliation errors from the 128 unmapped activities; no codec now. CIV-176 #372 merged (D-403): metadata loads no longer read snapshot_json. CIV-177 #374 merged (D-405): dashboard progress state and "Son işlem" period-bound. Copilot-bot commits need a lead update-branch to run CI (action_required).
3. 2026 PP (D-398/D-399): loaded live 4 Nov (33/105/226, 2027 protected); release #364 live; UI check passed (D-399). Next (D-401/D-406): CIV-178 merged first (else the mapping blocks the approved-book publish) → Ali applies the 2026 mapping (9 Nov) → lead re-measures the 2026 snapshot locally (CIV-175 script; >10 MB → codec task) → Strategy publishes 2026 via "Onaylı kitaptan yayınla" (needs the "Onay dayanağı" council decision text from Ali). 2026 dashboard status/last action 21.09 on 4 directorates → fixed by CIV-177 on phase5, live after the next release (D-405).
4. Ask Ali (D-375): printed 2026 book inconsistencies — Bilgi İşlem / Çevre Koruma / İmar cost vs economic totals differ (496 / 775 / 989 TL); Ruhsat ve Denetim economic table wrong totals; Zabıta and Veteriner economic tables show the total as "Diğer Bütçe Dışı Kaynak"; Fen İşleri p.223 2027/2028 totals malformed (D-403). Pages on the 9 Nov page. Loaded as printed; FR 2026 needs the correct figures.
4b. Ali Abi returns from leave Monday 9 Nov 2026 (BEYAN). Prepare for that day, in D-387 order: (1) one current directorate indicator Excel (FR5); (2) Mali Hizmetler budget-actuals template (ML1); (3) printed 2026 PP book inconsistencies (D-375); (4) PR2 — approval in Civensa or on paper; (5) İç Kontrol: plan approval date + 3 council mappings; timing of the new 2026–2028 plan. Also: review + upload the 2026 mapping draft (D-402; Düşük rows first); the "Onay dayanağı" text for 2026 and 2027 (council decision date/number) for the approved-book publication (CIV-174).
5. İç Kontrol (D-386/D-387): FR 2026 first, old plan archive only, module prepared for the new 2026–2028 plan. Open to Ali: plan approval date, 3 council mappings.
6. Faaliyet Raporu (D-354): 7 AR items PARTIAL; checklist "FR Girdileri" https://claude.ai/artifact/5bGm5xrVbPSjM7wfv1qrMA.
7. LOW (D-390/D-394/D-405): CIV-169 K2–K6 (K6 held until 2027 is published from the approved book; K4 re-measured after the 2026 mapping) + publication JSON hash note; ACTION_LABELS registered from program_routes. Watch reactions to the 554 book-check items (D-324, D-352). LOW backlog (D-328). UI: only 002/003 left, waits for Ali (D-345).
8. One live lead session at a time (D-363). Owner: check Claude Design standalone site before 14 Dec 2026 (D-363).
9. Claude account on Max from 4 Nov 2026 (BEYAN; next charge 4 Dec). Extra capacity goes to lead analysis/preparation work (D-400). The "Claude quota" block below is TARİHSEL (Pro era).
10. Sunum module (D-411/D-412/D-413): reveal.js 6.0.1 + ECharts 6.1.0 via Civensa Jinja templates, Civensa design tokens; animated HTML + 16:9 PDF from the same file. Prototype https://claude.ai/artifact/DMpNp2f68JsogL2eMgJSRD review round 1 done (D-414); full Fen İşleri 2025 presentation with real data = CIV-180 reference (D-415); waits for the owner's hall-computer test + further remarks → CIV-180 (engine + FR müdürlük presentation). Future report modules proposed in D-411 (not accepted; after 1 Jan 2027).
11. CIV-180 merged into phase5 (#394 → ab7551a, D-417); not live until the next release.
Next IDs: task CIV-183, decision D-421.

## Claude quota (BEYAN, owner 27 Oct 16:21)
- Session 11%, week 67%, weekly reset Saturday 00:00 (D-300). Copilot 96 / 1,500 credits, reset 1 Nov.
- Claude Pro ends 3 Nov 2026 (BEYAN). Owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov DeepSeek runs as backup lead (BACKUP_LEAD.md).

Dispatch format (D-232, D-249): platform + environment ("Bulut → civensa") + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block. Session end: one-line handover (D-253) after this file is rewritten.
Evidence rule (D-252): one-screen changes → targeted tests + changed-state screenshots + contrast; all-screen capture only when shared files change, committed as a short count summary.

## Open pull requests (DOĞRULANDI 4 Nov ~19:00, D-409)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| (pending) | CIV-182 | dispatched 5 Nov (D-419) | review when Codex opens the PR |
| (pending) | CIV-181 | dispatched 5 Nov (D-418) | review when Codex opens the PR |
| #382 | CIV-179 | PARKED (D-410): mechanism proven; open Codex P2s on financial tables | resume with the owner's new template |
Merged 5 Nov (D-417): #394 CIV-180 → ab7551a.
Merged 4 Nov (D-410): #384 release phase5 → main (owner) → c46cf4d, deployed · #383 D-409 records.
Merged 4 Nov (D-409): #381 CIV-178 → 7656624.
Merged 4 Nov (D-405): #374 CIV-177 → 92c644e.
Merged 4 Nov (D-403): #372 CIV-176 → 8828250 · #369 CIV-175 → 385a6fb · #371 D-402 → 40309a8.
Merged 4 Nov (D-399): #364 release phase5 → main (owner) → 7437119, deployed · #365 D-398 → e43f9a8 · #360/#361/#362 lead fixes.
Merged 3 Nov (D-393/D-394): #354 CIV-172 → 38eb017 · #358 CIV-174 → ac17369.
Merged 3 Nov: #356 CIV-173 Gemini → 28a2bd2 (D-392) · #336 CIV-169 → e5aa923 (D-390) · #333 CIV-168 → a5cfeee (D-382) · #342 CIV-170 Gemini → 3f7dec1 (D-384); closed #337/#343 (DeepSeek, D-384).
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
- Sunum (D-413/D-414): test Ornek-Sunum.html on the presentation-hall computer; further remarks on https://claude.ai/artifact/DMpNp2f68JsogL2eMgJSRD → lead writes CIV-180.
- Ask Ali 9 Nov (D-411/D-415): the 4 inconsistencies in the printed 2025 FR Fen İşleri chapter (D-415); when müdürlükler present the FR to the mayor;  who prepares Kurumsal Mali Durum, SP monitoring, Kamu Hizmet Envanteri and how long each takes.
- New Faaliyet Raporu template (D-410): keep the 2025 style names; add paragraph style "tablo sonuç" (tablo yazı + bold); send the template when ready → CIV-179 resumes.
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
