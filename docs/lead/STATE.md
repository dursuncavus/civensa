# CIVENSA — CURRENT STATE

Updated: 24 Oct 2026, ~17:05 Istanbul (live session). Replaces Drive "Civensa Güncel Durum v0.77".
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.4 · `PROJECT_RULES.md` v1.3 · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive + DeepSeek workspace YEDEK-KAYIT.md): empty.

Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Open pull requests (DOĞRULANDI, GitHub REST ~02:45Z)
| PR | Task | Head | State | Next action |
| --- | --- | --- | --- | --- |
| #84 | CIV-089 CI gitleaks + failure annotations | updating | Behind 1 after #82 → update-branch 17:00; lead merges when green |
| #86 | Lead records into repo (D-205) | updating | #87 merged into it; update-branch 17:00; lead merges when green |
| #85 | CIV-087 AR-15 Turkish errors + #80 cleanup | fde1dfb | test (18,0) red, cause unknown; Codex review stuck "running"; overlaps #82 files | After #84 merges: update branch → read annotations → lead fixes (D-211 code is lead-written) |

## Open — owner
0. (closed) Merges are done by the lead in live sessions (D-214).
1. (closed) Codex "Tam erişim" stays ON — owner decision D-210.
2. Plaintext password files on Desktop/Downloads/Documents (log 79) → owner moves them into the Passwords app; then lead removes the files.

## Open queue — lead / scheduled run "Civensa gece kontrol" (05:41, 08:41)
1. Scheduled-run merges are refused by the session permission check (D-213). Live session: decide how scheduled runs merge (owner merges, or permission change) — BELİRSİZ.
2. #85: after #84 merges, update branch, read failing test from annotations, fix (lead), resolve overlap with #82, "@codex review", merge.
3. CIV-088 = AR-16 (>85% similarity warning): dispatch after #82 merges, with documented defaults if Strateji/Ali has not answered (D-212).
4. D-177 plan conversion, CIV-085, live first load — owner sets the time, live session only.
5. ~2 Nov ask-Ali list incl. log 73 BELİRSİZ (a)–(c).
6. Measure scheduled run cost; reduce or stop if costly.
7. D-205 transition after #86 merges: archive Drive state/log/rule documents with "ESKİ ... KULLANMAYIN", add Drive pointer "KAYITLAR GITHUB'DA", civensa-lead skill (owner saves), scheduled task prompt (DONE 24 Oct 03:30).
8. Guard may never run (pull_request_target uses default branch `main`, D-213) — check and fix in live session.
9. DeepSeek mirror GUNCEL-DURUM.md is not reachable in scheduled runs; the lead refreshes it in the next live session with the Mac linked.

## Next IDs
- Next new task ID: CIV-090 (CIV-088 reserved).
- Next decision: D-215.
