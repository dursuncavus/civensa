# CIVENSA — CURRENT STATE

Updated: 24 Oct 2026, ~18:50 Istanbul (live session).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.4 · `PROJECT_RULES.md` v1.3 · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive + DeepSeek workspace YEDEK-KAYIT.md): empty.

Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Open pull requests (DOĞRULANDI, GitHub REST ~02:45Z)
| PR | Task | Head | State | Next action |
| --- | --- | --- | --- | --- |
| #85 | CIV-087 AR-15 Turkish errors + #80 cleanup | 5ddd8a9 | Lead merged phase5 in (conflicts with #82 resolved); CI running with annotations | Read failing test, lead fixes, merge |
| (new) | CIV-088 AR-16 similarity warning | — | Package `tasks/CIV-088.md`, dispatched 24 Oct ~18:50 | Review when ready |
| (new) | CIV-090 AR-06 deviation explanation gate | — | Package `tasks/CIV-090.md`, dispatched 24 Oct ~19:00 | Review when ready |

## Open — owner
- (resolved 24 Oct ~22:37) D-218 billing blocker — budget raised.
- (done) Owner raised the Actions budget 24 Oct. CIV-091 running in Codex. CIV-092 public-repo readiness approved by owner (D-220); after it merges: owner approves deleting old plaintext backup artifacts and switching the repo to public (two separate confirmations).
0. (closed) Merges are done by the lead in live sessions (D-214).
1. (closed) Codex "Tam erişim" stays ON — owner decision D-210.
2. (closed) Plaintext password files (log 79): owner decision D-217 — not tracked, do not remind the owner.

## Open queue — lead / scheduled run "Civensa gece kontrol" (05:41, 08:41)
1. Scheduled-run merges are refused by the session permission check (D-213). Live session: decide how scheduled runs merge (owner merges, or permission change) — BELİRSİZ.
2. #85: read failing test from annotations on 5ddd8a9, fix (lead), "@codex review", merge.
3. CIV-088 dispatched (lead defaults: >85% word similarity after normalization, numbers ignored, ≥30 words, previous year approved version). Ask Ali/Strateji to confirm the defaults (add to ~2 Nov list).
4. D-177 plan conversion, CIV-085, live first load — owner sets the time, live session only.
5. ~2 Nov ask-Ali list incl. log 73 BELİRSİZ (a)–(c).
6. Measure scheduled run cost; reduce or stop if costly.
7. D-205 transition (#86 merged 24 Oct): archive Drive state/log/rule documents with "ESKİ ... KULLANMAYIN", add Drive pointer "KAYITLAR GITHUB'DA", civensa-lead skill (owner saves), scheduled task prompt (DONE 24 Oct 03:30).
8. Guard may never run (pull_request_target uses default branch `main`, D-213) — check and fix in live session.
9. DeepSeek mirror GUNCEL-DURUM.md is not reachable in scheduled runs; the lead refreshes it in the next live session with the Mac linked.

## Next IDs
- Next new task ID: CIV-093.
- Next decision: D-221.
