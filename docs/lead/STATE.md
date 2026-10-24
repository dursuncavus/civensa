# CIVENSA — CURRENT STATE

Updated: 24 Oct 2026, ~03:40 Istanbul. Replaces Drive "Civensa Güncel Durum v0.77".
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.4 · `PROJECT_RULES.md` v1.3 · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive + DeepSeek workspace YEDEK-KAYIT.md): empty.

Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Open pull requests (DOĞRULANDI, GitHub REST ~00:30Z)
| PR | Task | Head | State | Next action |
| --- | --- | --- | --- | --- |
| #84 | CIV-089 CI gitleaks + failure annotations | f6bfc39 | DRAFT; test(18,0) green, test(18,1) rerun running | Owner marks "Ready for review" (D-204); lead merges when test(18,1) green |
| #85 | CIV-087 AR-15 Turkish errors + #80 cleanup | 4894d48 | Not mergeable (D-203): MEDIUM login `?message=` reflection, 2 LOW, test(18,0) failed | "@codex" follow-ups posted; re-review after new head. Codex pickup: BELİRSİZ |
| #82 | CIV-086 AR-14 typeset data contract | fb7a88c | Draft, CI running | Review when Codex marks ready (migration c086, single alembic head) |
| this PR | Lead records into repo (D-205) | — | Open | Codex review of guard workflow, then lead merges |

## Open — owner
1. Mark #84 "Ready for review": https://github.com/dursuncavus/civensa/pull/84
2. Codex "Tam erişim": v0.76 says still ON at 02:49 screenshot, log 77 BEYAN says off — owner to confirm it is off.
3. Plaintext password files on Desktop/Downloads/Documents (log 79) → owner moves them into the Passwords app; then lead removes the files.

## Open queue — lead / scheduled run "Civensa gece kontrol" (05:41, 08:41)
1. #84 merge per D-197/D-204.
2. #85 re-review after Codex fix.
3. #82 review when ready.
4. Codex slots: 3 busy (CIV-086, -087, -089). First free slot: CIV-088 = AR-16 (lead writes `tasks/CIV-088.md`).
5. D-177 plan conversion, CIV-085, live first load — owner sets the time, live session only.
6. ~2 Nov ask-Ali list incl. log 73 BELİRSİZ (a)–(c).
7. Measure first-night scheduled run cost; reduce or stop if costly.
8. D-205 transition after this PR merges: archive Drive state/log/rule documents with "ESKİ ... KULLANMAYIN", add Drive pointer "KAYITLAR GITHUB'DA", update civensa-lead skill (owner saves the proposal), update scheduled task prompt, refresh DeepSeek mirror GUNCEL-DURUM.md when the Mac is linked.

## Next IDs
- Next new task ID: CIV-090 (CIV-088 reserved).
- Next decision: D-206.
