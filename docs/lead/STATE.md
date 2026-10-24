# CIVENSA — CURRENT STATE

Updated: 24 Oct 2026, ~03:45 Istanbul. Replaces Drive "Civensa Güncel Durum v0.77".
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.4 · `PROJECT_RULES.md` v1.3 · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive + DeepSeek workspace YEDEK-KAYIT.md): empty.

Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Open pull requests (DOĞRULANDI, GitHub REST ~00:30Z)
| PR | Task | Head | State | Next action |
| --- | --- | --- | --- | --- |
| #84 | CIV-089 CI gitleaks + failure annotations | 04975b3 | Ready; f6bfc39 fully green; was behind 4 → branch updated 00:30Z (D-206), CI rerunning | Lead/scheduled run merges when green on 04975b3 and behind 0 |
| #85 | CIV-087 AR-15 Turkish errors + #80 cleanup | 124c5aa | 124c5aa only changed CSRF text; D-203 MEDIUM still open (D-208); CI running | Owner pastes fix follow-up into Codex task CIV-087; re-review new head |
| #82 | CIV-086 AR-14 typeset data contract | fb7a88c | Draft, CI running | Review when Codex marks ready (migration c086, single alembic head) |
| #86 | Lead records into repo (D-205) | lead/civ-lead-records | Codex P1 fixed (D-207, pull_request_target); re-review requested | Lead merges when Codex re-review has no P0/P1 and tests green |

## Open — owner
1. Codex "Tam erişim": v0.76 says still ON at 02:49 screenshot, log 77 BEYAN says off — owner to confirm it is off.
2. Plaintext password files on Desktop/Downloads/Documents (log 79) → owner moves them into the Passwords app; then lead removes the files.

## Open queue — lead / scheduled run "Civensa gece kontrol" (05:41, 08:41)
1. #84 merge per D-197/D-206.
2. #85 re-review after Codex fix (follow-up via owner, D-208).
3. #82 review when ready.
4. Codex slots: 3 busy (CIV-086, -087, -089). First free slot: CIV-088 = AR-16 (lead writes `tasks/CIV-088.md`).
5. D-177 plan conversion, CIV-085, live first load — owner sets the time, live session only.
6. ~2 Nov ask-Ali list incl. log 73 BELİRSİZ (a)–(c).
7. Measure first-night scheduled run cost; reduce or stop if costly.
8. D-205 transition after this PR merges: archive Drive state/log/rule documents with "ESKİ ... KULLANMAYIN", add Drive pointer "KAYITLAR GITHUB'DA", update civensa-lead skill (proposal shown to owner 24 Oct; owner saves it), scheduled task prompt (DONE 24 Oct 03:30), refresh DeepSeek mirror GUNCEL-DURUM.md when the Mac is linked.

## Next IDs
- Next new task ID: CIV-090 (CIV-088 reserved).
- Next decision: D-209.
