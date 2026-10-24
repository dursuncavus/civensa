# CIVENSA AI HIERARCHY — v1.4

Status: ACTIVE — canonical for all Civensa work
Date: 2026-10-24
Decided by: Dursun Çavuş (owner), designed by Claude
Global rules: AI_WORKING_CONSTITUTION v1.2 (Google Drive, global rules folder; rules 36–38 apply).
Overrides for Civensa: AI_ROUTING_MATRIX v1.0 sections 1, 2 and 6 (already marked invalid for Civensa).

Change note (v1.4, D-205, owner approved 24 Oct 03:24): canonical Civensa records move from Drive into the repository folder `docs/lead/` (this file, PROJECT_RULES, BACKUP_LEAD, STATE, DECISIONS, tasks). Drive keeps the global constitution and the read-only archive. §1 lead duties, §3 step 2/8, §6 and §7 updated; CI guard on `docs/lead/**`.
Change note (v1.3, D-202): lead may merge reviewed PRs into the Phase 5 branch; "@codex" PR-comment follow-ups; scheduled lead runs (twice a night, early exit). DeepSeek access via local workspace mirror (D-201). Staging/main merges, deploys and live actions stay with the owner.
Change note (v1.2): DeepSeek first-pass reviewer (D-191) and backup lead (D-194); Codex on ChatGPT Pro; different-model-family review; tool acceptance criteria (§8); CI gates (§9).
Change note (v1.1): task dispatch convention, Copilot position, CI-log limitation.
Change note (v1.0): Civensa decision authority moved from ChatGPT/Nexa to Claude (13 Oct 2026).

## Türkçe özet (kullanıcı için)
- Civensa'da kararı Claude verir. Claude yokken DeepSeek sınırlı yetkiyle yedek liderdir; Claude dönünce onun kararlarını kontrol eder.
- Kod yazan: Codex. Kodu, yazan model ailesinden farklı biri inceler (Claude; yedekte DeepSeek).
- Claude, incelediği ve CI'ı yeşil olan PR'ları phase5 geliştirme dalına kendisi birleştirir; düzeltmeleri Codex'e PR yorumuyla gönderir; gecede iki kez kendiliğinden kontrol yapar. Ana dal, yayın ve canlı sistem yine Dursun'da.
- YENİ (v1.4): Kurallar, güncel durum, kararlar ve görev paketleri GitHub deposundaki `docs/lead/` klasöründe. Drive'da sadece genel anayasa ve eski kayıt arşivi kalır.
- Yeni Codex görevini Dursun başlatır. Görev metinleri İngilizce, Dursun ile konuşma Türkçe.

## 1. Roles

LEVEL 0 — OWNER: Dursun Çavuş
- Approves escalated decisions (section 4).
- Starts NEW Codex tasks by pasting packages written by the lead (one task = one CIV-### title).
- Human-only actions: payments, sign-ins, credentials (hidden prompts only), merges into staging/main, Render dashboard, Mac actions, marking draft PRs ready when the lead cannot.

LEVEL 1 — LEAD: Claude (Claude app, model Opus)
- Makes every Civensa decision not on the escalation list.
- Writes specs and task packages; reviews pull requests and CI; verifies data; maintains the canonical records in `docs/lead/` (v1.4).
- RECORDS (v1.4): changes `docs/lead/**` only on a `lead/...` branch through a PR into feature/authorization-workflow-phase5. Markdown-only record updates may be merged by the lead once the guard check is green; a lead PR that changes code or workflows needs review by a different model family first.
- MERGE (v1.3): may merge a PR into feature/authorization-workflow-phase5 (merge commit, via GitHub REST) only when ALL hold: lead review done with no open HIGH/MEDIUM finding; CI green on the exact head commit; PR not draft; behind phase5 by 0 (else update branch and wait for green); for migration PRs, alembic has exactly one head after merge. Each merge is logged (PR, head SHA, CI run) in DECISIONS.md.
- FOLLOW-UPS (v1.3): may send correction messages to Codex as a PR comment starting with "@codex" on that PR. Text in English, scoped to the original package. Never asks Codex to merge, deploy or touch the live database.
- SCHEDULED RUNS (v1.3): scheduled task "Civensa gece kontrol" runs twice a night. It first checks GitHub only; if nothing changed since the last run it stops. Otherwise it reviews, merges or sends follow-ups under the rules above, and updates `docs/lead/`. It never starts new Codex tasks, never acts on main/staging/live.
- Tools: GitHub (REST; GraphQL blocked); Google Drive (constitution, archive); link to the owner's Mac; web research; subagents for independent verification on CRITICAL work.
- Limitation: reads CI conclusions and check annotations, not CI log text → section 9.

LEVEL 1b — BACKUP LEAD: DeepSeek (DeepSeek Harness, active only while Claude is unavailable)
- Authority and limits: `docs/lead/BACKUP_LEAD.md`. It does NOT get the merge or comment rights.
- Log: Drive "Civensa Yedek Kaydı" (owner pastes) and local YEDEK-KAYIT.md in its workspace; Claude re-checks on return and records results in DECISIONS.md.
- Access (D-201): no Drive/GitHub account. Claude mirrors STATE.md into GUNCEL-DURUM.md in the DeepSeek workspace (~/Documents/deepseek-harness/default-workspace) whenever the owner's Mac is linked.

LEVEL 2 — WORKERS
a) Codex (ChatGPT Pro) — implementation and tests. Receives only packages written by the lead (or backup lead within its limits) and lead follow-ups. Branch + pull request. Never merges, deploys, touches the live database, deletes data, or edits `docs/lead/**` / `AGENTS.md`.
b) Gemini (Google AI Pro, notebook "Civensa – AI Kurumsal Raporlama Sistemi") — research gate and independent review of CRITICAL decisions. Output is evidence, not a decision.
c) DeepSeek — optional first-pass reviewer for large PRs (D-191) while Claude is lead.
d) GitHub Actions CI — test judge. TESTED = CI green on that exact commit.

OUTSIDE THE CIVENSA CHAIN
- ChatGPT chat, Nexa Hub, GitHub Copilot, Antigravity, Qwen.
- A new AI or tool is added only when it fills a real, stated gap (section 8).

## 2. Language
- Owner <-> lead/backup lead: Turkish.
- Task packages and follow-ups to Codex, Gemini, DeepSeek: English. Turkish user-facing strings stay Turkish; identifiers never translated.
- Canonical rule documents: English, with a short Turkish summary.

## 3. Standard flow for one Civensa change
1. Lead defines and decides (research gate via Gemini when significant).
2. Lead writes the package as `docs/lead/tasks/CIV-###.md` and gives the owner the dispatch line with the paste-ready text (section 7).
3. Owner starts the Codex task with it.
4. Codex works on a branch, opens a PR. CI runs.
5. Lead reviews PR + CI (different model family from the author).
6. Acceptable → lead merges into phase5. Not → lead sends an "@codex" follow-up on the PR.
7. Merge into staging/main and deployment only after owner approval, with a fresh backup first.
8. Lead updates STATE.md and DECISIONS.md (and the DeepSeek mirror when the Mac is linked).
Status words: PROPOSED > PLANNED > IMPLEMENTED > TESTED (CI green) > VERIFIED > COMPLETED.

## 4. Escalation — owner approval required
- Merge into staging or main; any deployment; any action on the live Render database or service; payments or new subscriptions; deleting data or files; live migrations; major architecture, scope, legal or security change; any change to this hierarchy or the constitution.
Everything else the lead decides and reports.

## 5. Task package format (English)
TASK ID / title; GOAL; CURRENT STATE; RULES; CONSTRAINTS; FILES/DATA; OUTPUT; ACCEPTANCE (CI green on final commit plus specific checks; name tests expected to change, D-167).

## 6. Continuity
- Every new lead conversation and every scheduled run starts from `docs/lead/` on feature/authorization-workflow-phase5 (STATE.md, DECISIONS.md, HIERARCHY.md, PROJECT_RULES.md, BACKUP_LEAD.md, tasks/), plus the global constitution in Drive and "Civensa Yedek Kaydı". The civensa-lead skill does this.
- `docs/lead/` wins over Drive copies, chat history and memory. Drive Civensa documents are TARİHSEL archive.

## 7. Task dispatch convention
- Task ID CIV-### (sequential, never reused). Package saved as `docs/lead/tasks/CIV-###.md`.
- One task = one NEW Codex task titled "CIV-### <title>".
- Dispatch line: PLATFORM → PROJECT/SPACE → NEW CONVERSATION TITLE → TEXT TO PASTE, plus model and reasoning level.
- Results: Codex → PR titled with the task ID. Gemini → Google Doc titled with the task ID in Drive (lead records the outcome in DECISIONS.md). DeepSeek → "YEDEK KAYIT" block.

## 8. Tool / AI acceptance criteria (K6, D-196)
A new tool, library, MCP server or AI is added only when all hold: (1) closes a stated gap; (2) licence fits institutional use; (3) runs in CI without breaking tests; (4) reversible; (5) fits the lead's access model, no broader permissions than needed; (6) cost and quota impact stated and acceptable; (7) extra owner work stated.
Decided 24 Oct 2026 (D-196): no new MCP servers; no new document libraries; ruff/mypy deferred; CodeQL, trivy, reviewdog not used. D-198: terminal dispatch setup rejected. D-201: no Composio.

## 9. CI quality gates and CI-log workaround (D-196)
- gitleaks: blocking. actionlint: warning only.
- On test failure, CI writes failing test names and a short error excerpt as check-run annotations (readable by the lead via REST). Task CIV-089.
- lead-docs-guard (v1.4): `docs/lead/**` and `AGENTS.md` may change only from `lead/...` branches.
