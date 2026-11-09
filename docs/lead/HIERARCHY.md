# CIVENSA AI HIERARCHY — v1.10

Status: ACTIVE — canonical for all Civensa work
Date: 2026-11-09 (v1.10)
Decided by: Dursun Çavuş (owner), designed by Claude
Global rules: AI_WORKING_CONSTITUTION v1.2 (Google Drive, global rules folder; rules 36–38 apply).
Overrides for Civensa: AI_ROUTING_MATRIX v1.0 sections 1, 2 and 6 (already marked invalid for Civensa).

Change note (v1.10, D-450, owner 9 Nov 2026 11:21 "DeepSeek denetleme yapmadığı zamanlarda senin vereceğin görevleri de yapsın… Yerelde de bir yapı kuralım."): (1) DeepSeek, while not acting as backup lead, also takes lead-packaged small tasks (c). Gap: pilot calendar; Codex/Gemini lanes full. Known limit: DeepSeek scored 85 vs Gemini 95 in D-379/D-381 → findings/profiling and offline scripts first, no app/ logic until one task merges clean. Acceptance check: its first task (CIV-196) is accepted with at most one fix round. (2) Local lane on the owner's Mac (§1 LOCAL LANE). Gap: CI is the only test run for patches and lead code (pypi blocked in the lead sandbox; one CI round ≈ 25 min). Acceptance check: the lead runs the targeted tests of the next Gemini/DeepSeek patch on the Mac before opening its PR. Partly supersedes D-198: still no Codex CLI on the Mac and no second source of truth; the repo stays the only record.
Change note (v1.9, D-449, owner 9 Nov 2026 11:12 "Copilot da aktif olsun."): GitHub Copilot joins LEVEL 2 as g). Gap: four FR tasks are queued before the 14 Dec pilot and every PR waits on one lead review; Copilot adds a second automated reviewer on every task PR and a lane for small issue-sized code tasks. Acceptance check: on its first 3 reviewed PRs Copilot produces at least one finding the lead accepts and no finding that blocks a merge wrongly; its first coding task merges with CI green and at most one fix round. Limitation: Copilot-bot commits need a lead update-branch to run CI (action_required); credits are limited (monthly reset) → coding tasks only when packaged by the lead.
Change note (v1.8, D-408, owner 4 Nov 2026 18:19 "Artık sen de aktif olabilirsin. Denetimden fazlası olabilirsin."): the lead (Claude) may also implement tasks itself (§1 LEVEL 2 f). Gap: Codex is one serial lane and the Max plan leaves lead capacity unused (D-400); tasks that need deep lead context (book IDML analysis, data verification) lose detail when handed over. Review stays with a different model family: Codex ("@codex review" on the PR) + CI. Acceptance check: the first lead-coded task merges with CI green and a Codex review with at most one fix round. Limitation: the lead sandbox cannot install Python packages (pypi blocked) → CI is the only test run until the owner allows pypi.org and files.pythonhosted.org.
Change note (v1.7, D-384, result of the owner-approved head-to-head D-379/D-381): third coding lane = Gemini in Google Antigravity (Gemini 4 Argon, High) — 95/100 vs DeepSeek V4 Pro 85 and V4.1 Flash 85. DeepSeek returns to backup lead + optional first-pass reviewer only. Antigravity delivery: task in ~/development/civ###-gemini/TASK.md, output CIV-###.patch + RESULT.md, lead applies/pushes/reviews; no GitHub credential in Antigravity.
Change note (v1.6, D-378, owner 3 Nov 2026 15:52 "Deepseek tarafını da kodlama için kullanabilirsin"): DeepSeek may also implement small, self-contained tasks (§2 e). Gap: a third coding lane when both Codex lanes are busy. Acceptance check: trial CIV-170 — patch applies, CI green, Claude review passes with at most one fix round. Delivery via workspace patch (no GitHub account); Claude pushes, CI tests, Claude reviews. DeepSeek code is never reviewed or merged by DeepSeek acting as backup lead.
Change note (v1.5, D-292, owner "kural onay" 27 Oct 2026): MERGE no longer needs behind 0 when the PR's files do not overlap the newer phase5 commits; full suite runs on every phase5 push; red phase5 → revert the last merge.
Change note (v1.4, D-205, owner approved 24 Oct 03:24): canonical Civensa records move from Drive into the repository folder `docs/lead/` (this file, PROJECT_RULES, BACKUP_LEAD, STATE, DECISIONS, tasks). Drive keeps the global constitution and the read-only archive. §1 lead duties, §3 step 2/8, §6 and §7 updated; CI guard on `docs/lead/**`.
Change note (v1.3, D-202): lead may merge reviewed PRs into the Phase 5 branch; "@codex" PR-comment follow-ups; scheduled lead runs (twice a night, early exit). DeepSeek access via local workspace mirror (D-201). Staging/main merges, deploys and live actions stay with the owner.
Change note (v1.2): DeepSeek first-pass reviewer (D-191) and backup lead (D-194); Codex on ChatGPT Pro; different-model-family review; tool acceptance criteria (§8); CI gates (§9).
Change note (v1.1): task dispatch convention, Copilot position, CI-log limitation.
Change note (v1.0): Civensa decision authority moved from ChatGPT/Nexa to Claude (13 Oct 2026).

## Türkçe özet (kullanıcı için)
- Civensa'da kararı Claude verir. Claude yokken DeepSeek sınırlı yetkiyle yedek liderdir; Claude dönünce onun kararlarını kontrol eder.
- Kod yazan: Codex; küçük, kendi içinde kapalı işlerde Antigravity'deki Gemini de (v1.7). YENİ (v1.8): Claude da kendi görevlerini kodlar; onun kodunu Codex inceler, CI test eder. Kodu, yazan model ailesinden farklı biri inceler. YENİ (v1.10): DeepSeek boştayken liderin küçük görevlerini de yapar; Mac'te yerel test hattı kurulur. YENİ (v1.9): GitHub Copilot her görev PR'ını ayrıca otomatik inceler ve liderin issue olarak yazdığı küçük işleri kodlar.
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
- MERGE (v1.3): may merge a PR into feature/authorization-workflow-phase5 (merge commit, via GitHub REST) only when ALL hold: lead review done with no open HIGH/MEDIUM finding; CI green on the exact head commit; PR not draft; behind phase5 by 0, OR (v1.5, D-292) behind only by commits that change none of the PR's files and CI green on the PR head; after every code merge the full suite runs on phase5 (push trigger) and a red phase5 run is answered by reverting the last merge first; for migration PRs, alembic has exactly one head after merge. Each merge is logged (PR, head SHA, CI run) in DECISIONS.md.
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
c) DeepSeek — optional first-pass reviewer for large PRs (D-191) while Claude is lead; YENİ v1.10 (D-450): also a coder for lead-packaged small tasks when not acting as backup lead. Delivery like e): ~/development/civ###-deepseek/TASK.md → CIV-###.patch + RESULT.md; the lead applies, tests locally, pushes, reviews (different model family). Same AGENTS.md hard rules; migrations, auth and live-write logic stay with Codex.
e) Gemini in Google Antigravity (Gemini 4 Argon, High) — coder for small, self-contained tasks (v1.7, D-384; replaces the v1.6 DeepSeek coding trial). Package in English, saved as docs/lead/tasks/CIV-###.md and copied to ~/development/civ###-gemini/TASK.md on the owner's Mac. Output: CIV-###.patch (git format-patch, one commit) + RESULT.md. Claude (Mac linked) applies it on branch task/civ-###-gemini, pushes, opens the PR, CI judges, Claude reviews (different model family). Same hard rules as Codex (AGENTS.md); no push, merge, deploy or live database; the owner answers its permission prompts (allow clone/install/test, refuse git push). Migrations, auth and live-write logic stay with Codex.
f) Claude, the lead, as coder (v1.8, D-408) — takes a task itself when it is not waiting on the owner's dispatch and needs lead context. Same package (docs/lead/tasks/CIV-###.md, header "Coder: Claude"), same AGENTS.md hard rules. Branch task/civ-###-claude from phase5, PR titled with the task ID, description lists files, CI results and what was not verified. Review: comment "@codex review" on the PR; MERGE (§1) applies with the Codex review in place of the lead review (no open HIGH/MEDIUM finding from Codex; the lead answers or fixes each Codex finding and records it). The lead never reviews its own code as the only reviewer. Escalation list (§4) unchanged.
g) GitHub Copilot (v1.9, D-449) — (1) automated reviewer: the lead requests a Copilot review on each task PR; findings are evidence, the lead decides; it never replaces the different-family review. (2) coder for small issue-sized tasks: the lead writes the package as a GitHub issue (English, same structure as docs/lead/tasks/CIV-###.md, which stays the record) and assigns Copilot; base phase5; same AGENTS.md hard rules; migrations, auth and live-write logic stay with Codex.
d) GitHub Actions CI — test judge. TESTED = CI green on that exact commit.

LOCAL LANE (v1.10, D-450) — owner's Mac
- Folders: ~/development/civ###-<gemini|deepseek>/ (TASK.md in; CIV-###.patch + RESULT.md out). One clean clone ~/development/civensa-test (phase5) with a Python venv, used only to apply a patch and run its targeted tests.
- Runner: a Claude Code Remote Control session on the Mac started by the lead and approved by the owner; it applies patches, runs tests and reports. It never pushes to main/staging, deploys, touches the live database or reads secrets; pushes go only to task/ and lead/ branches.
- CI stays the judge: TESTED = CI green on that exact commit. Local runs only shorten the loop.

OUTSIDE THE CIVENSA CHAIN
- ChatGPT chat, Nexa Hub, Qwen. (GitHub Copilot moved into LEVEL 2 g in v1.9; Gemini in Antigravity is LEVEL 2 e since v1.7.)
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
