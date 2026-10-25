# CIVENSA — CURRENT STATE

Updated: 25 Oct 2026, ~21:35 Istanbul (live session, CV Lider 22).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.4 · `PROJECT_RULES.md` v1.3 · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive): no entries, last modified 23 Oct (DOĞRULANDI 25 Oct 19:15).

## Claude quota (BEYAN, owner screen 25 Oct ~10:15)
- Weekly usage 21%; at the current rate it runs out Friday evening (30 Oct).
- October extra-usage charge: $40.30 of $45 limit.
- Rule until reset (D-226): no long live sessions — finish the task, write a short record, close. Reviews, Ali answers (Mon 26 Oct) and packages come first; no design iterations on Claude.

Dispatch format (D-232): platform + exact model (Codex: GPT-6.1 Sol) + effort; title is the first line inside the paste block; every session ends with a handover block.

Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Open pull requests (DOĞRULANDI 25 Oct 19:35; #118 CIV-098 merged 9f0bdc5, #119 CIV-097 merged 7ddecbb, D-235)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| #122 | CIV-099 design → 012 section editor | reviewed de89a0e; list-order fix via owner into the CIV-099 Codex task (D-238, D-239) | Check fix commit, CI, behind 0, merge; owner approves look + 77 case changes |
| — | CIV-100 024 polish (mismatch box, checkbox tick) | package given to owner 21:35 (D-240) | Review screenshots + CI, merge |

## Open — owner
- Public repo (D-220/D-222/D-223), in order, each with owner confirmation:
  1. DONE 25 Oct — age secrets set (BEYAN + screenshot), private key in owner's Passwords app.
  2. DONE 25 Oct (D-228) — default branch is now `feature/authorization-workflow-phase5` (DOĞRULANDI REST). `main` and civensa-pilot untouched (Auto-Deploy off, D-227).
  3. One encrypted backup run verified — 25 Oct 05:07 UTC run came from `main` (plaintext, D-230); first phase5 encrypted run expected 26 Oct, check it (night check 08:41 or next live session); no manual dispatch (live database = escalation).
  4. Delete old plaintext backup artifacts (includes civensa-db-backup-20261025-0507Z, D-230) — only after step 3 is verified (D-233).
  5. Full-history gitleaks (workflow_dispatch) — must be clean.
  6. Switch repo to public.
- Claude Pro ends 3 Nov 2026 (BEYAN 25 Oct 10:22; Billing page shows only "Subscribed via iOS app", no date). iOS subscription is cancelled. Owner renews Pro from claude.ai on the web on 3 Nov; otherwise from 3 Nov the lead is unavailable and DeepSeek runs as backup lead (BACKUP_LEAD.md).
- UI redesign (D-224/D-225): CIV-095 prototype (D-231), CIV-096 shell + 034 (D-233), CIV-098 Modüller grid and CIV-097 024 data entry (D-235) merged. Owner approved the look and the 024 letter-case changes (D-237). CIV-099 (012) next (D-236).
0. (closed) Merges are done by the lead in live sessions (D-214).
1. (closed) Codex "Tam erişim" stays ON — owner decision D-210.
2. (closed) Plaintext password files (log 79): owner decision D-217 — not tracked, do not remind the owner.

## Open queue — lead / scheduled run "Civensa gece kontrol" (05:41, 08:41)
1. Scheduled-run merges are refused by the session permission check (D-213). Live session: decide how scheduled runs merge (owner merges, or permission change) — BELİRSİZ.
2. Ask-Ali list (13 items: log 73 (a)–(c), AR-16 defaults, AR-01/02/03/04/13/17/18) published as artifact "Ali Abi Soruları" https://claude.ai/artifact/KVuaFCeKzTv9kQGpwRWiz8 ; ChatGPT e-mails it from the owner's Gmail on Mon 26 Oct. Answers come back as an e-mail reply in "CIVENSA-CEVAPLAR v1" format; the lead reads them via Gmail, records decisions and dispatches Codex packages the same day.
3. D-177 plan conversion, CIV-085, live first load — owner sets the time, live session only.
4. Measure scheduled run cost; reduce or stop if costly.
5. D-205 transition leftovers: archive Drive state/log/rule documents with "ESKİ ... KULLANMAYIN", add Drive pointer "KAYITLAR GITHUB'DA".
6. (closed, D-237) Guard runs on lead PRs after the default-branch switch (#120).
7. DeepSeek mirror GUNCEL-DURUM.md: refresh in the next live session with the Mac linked.

## Next IDs
- Next new task ID: CIV-101.
- Next decision: D-241.
