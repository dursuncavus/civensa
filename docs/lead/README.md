# docs/lead — Civensa lead records (canonical)

Status: canonical from the merge of this folder into `feature/authorization-workflow-phase5` (decision D-205, owner approved 24 Oct 2026).
Before D-205 these records lived in Google Drive `AI-Work-System/projects/civensa`. Drive now keeps only the archive and the global constitution.

## Türkçe özet (Dursun için)
- Civensa'nın kuralları, güncel durumu, kararları ve görev paketleri artık bu klasörde.
- Tek dosya, tek yer: `STATE.md` güncel durum, `DECISIONS.md` kararlar. Her değişiklik git geçmişinde görünür, geri alınabilir.
- Bu klasörü sadece lider (Claude) değiştirir; Codex değiştiremez (CI bekçisi engeller).
- Genel anayasa (AI_WORKING_CONSTITUTION) Drive'da kalır; çünkü tüm projeler için ortak.

## Files
| File | What | Replaces (Drive) |
| --- | --- | --- |
| `STATE.md` | Current state, open queue, next IDs. Overwritten in place. | "Civensa Güncel Durum vX.YY" |
| `DECISIONS.md` | Append-only decisions log from D-205 on, plus index of decisions still in force. | CIVENSA_DECISIONS_LOG 1–84 |
| `HIERARCHY.md` | Roles, authority, flow, escalation. | CIVENSA_AI_HIERARCHY v1.3 |
| `PROJECT_RULES.md` | Product and engineering rules. | CIVENSA_PROJECT_RULES v1.2 |
| `BACKUP_LEAD.md` | DeepSeek backup-lead brief. | CIVENSA_BACKUP_LEAD v1 |
| `tasks/` | One file per task package `CIV-###.md`, from CIV-088 on. | Drive `gorevler` |

## Rules for this folder
1. Only the lead changes files here, on a branch named `lead/...`, through a pull request into `feature/authorization-workflow-phase5`.
2. The workflow `.github/workflows/lead-docs-guard.yml` fails any pull request that changes `docs/lead/**` or `AGENTS.md` from a branch not starting with `lead/`.
3. Lead-record PRs that change only Markdown skip the test suite (paths-ignore); a PR that changes code or workflows needs a review by a different model family (constitution rule 18).
4. Small state/decision updates may be merged by the lead right after the guard is green (no code, documents only, logged in DECISIONS.md).
5. Old Drive documents stay as read-only history (TARİHSEL). If Drive and this folder disagree, this folder wins.
6. Never write secrets, passwords, connection strings or personal data here.
