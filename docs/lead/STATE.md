# CIVENSA — CURRENT STATE

Updated: 24 Oct 2026, ~18:50 Istanbul (live session).
Rules: AI_WORKING_CONSTITUTION v1.2 (Drive, global) · `HIERARCHY.md` v1.4 · `PROJECT_RULES.md` v1.3 · `BACKUP_LEAD.md` v2.
Backup log ("Civensa Yedek Kaydı", Drive + DeepSeek workspace YEDEK-KAYIT.md): empty.

Tags: DOĞRULANDI (lead checked) · TARİHSEL (past fact) · BEYAN (owner said) · BELİRSİZ (unknown).

## Open pull requests (DOĞRULANDI ~25 Oct 02:30)
| PR | Task | State | Next action |
| --- | --- | --- | --- |
| (Codex) | CIV-093 UI screen map | running | Review when PR opens |
| (Codex) | CIV-094 review follow-ups | dispatched | Review when PR opens |

## Open — owner
- (resolved 24 Oct ~22:37) D-218 billing blocker — budget raised.
- Public repo (D-220/D-222): CIV-092 merged into phase5. Next, in order, each with owner confirmation: (1) owner creates age key pair and sets BACKUP_AGE_RECIPIENT / BACKUP_AGE_IDENTITY secrets (lead gives hidden-prompt commands); (2) phase5 → main merge (owner) so scheduled backups encrypt; (3) one encrypted backup run verified; (4) delete old plaintext backup artifacts; (5) run full-history gitleaks (workflow_dispatch) — must be clean; (6) switch repo to public.
0. (closed) Merges are done by the lead in live sessions (D-214).
1. (closed) Codex "Tam erişim" stays ON — owner decision D-210.
2. (closed) Plaintext password files (log 79): owner decision D-217 — not tracked, do not remind the owner.

## Open queue — lead / scheduled run "Civensa gece kontrol" (05:41, 08:41)
1. Scheduled-run merges are refused by the session permission check (D-213). Live session: decide how scheduled runs merge (owner merges, or permission change) — BELİRSİZ.
2. #85: read failing test from annotations on 5ddd8a9, fix (lead), "@codex review", merge.
3. CIV-088 merged (#89); its defaults are in the ask-Ali list.
4. D-177 plan conversion, CIV-085, live first load — owner sets the time, live session only.
5. Ask-Ali list (13 items: log 73 (a)–(c), AR-16 defaults, AR-01/02/03/04/13/17/18) published as artifact "Ali Abi Soruları" https://claude.ai/artifact/KVuaFCeKzTv9kQGpwRWiz8 ; ChatGPT e-mails it from the owner's Gmail on Mon 26 Oct. Answers come back as an e-mail reply in "CIVENSA-CEVAPLAR v1" format; the lead reads them via Gmail and records decisions.
6. Measure scheduled run cost; reduce or stop if costly.
7. D-205 transition (#86 merged 24 Oct): archive Drive state/log/rule documents with "ESKİ ... KULLANMAYIN", add Drive pointer "KAYITLAR GITHUB'DA", civensa-lead skill (owner saves), scheduled task prompt (DONE 24 Oct 03:30).
8. Guard may never run (pull_request_target uses default branch `main`, D-213) — check and fix in live session.
9. DeepSeek mirror GUNCEL-DURUM.md is not reachable in scheduled runs; the lead refreshes it in the next live session with the Mac linked.

## Next IDs
- Next new task ID: CIV-095.
- Next decision: D-223.
