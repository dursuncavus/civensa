# CIVENSA PROJECT RULES — v1.4

Status: ACTIVE · Type: Canonical Project Rules · Project: Civensa
Scope: All Civensa research, analysis, product, UX, architecture, coding, testing, reporting, and multi-AI work
Single Source of Truth: YES (this file, `docs/lead/PROJECT_RULES.md`)
Version: 1.4 · Date: 2026-10-26
Depends on: AI WORKING CONSTITUTION v1.2 (Drive); `docs/lead/HIERARCHY.md` v1.4

Change note (v1.4, D-271): section 24 now enforces the research gate in every task package (mandatory PRIOR ART field). No other rule changed.
Change note (v1.3, D-205): file moved from Drive into the repository. Sections 17 and 19 point to `docs/lead/` instead of Drive; dependency updated to constitution v1.2 and hierarchy v1.4. No product or engineering rule changed.
Change note (v1.2): Section 19 replaced. Civensa decision authority moved from ChatGPT/Nexa to Claude at the owner's request on 13 Oct 2026.
Change note (v1.1): adds explicit Civensa validation terminology, makes the research gate non-optional for significant work, and expands Definition of Done to require end-to-end verification.

These project rules supplement the global AI Working Constitution. If a Civensa-specific instruction conflicts with the latest confirmed global constitution, the global constitution has priority unless an explicit higher-priority safety, legal, or platform rule applies.

## 1. PRODUCT PURPOSE
Civensa is an AI-assisted institutional reporting platform initially focused on Turkish municipalities.
Civensa must reduce the real operational burden of institutional reporting, especially: data entry, data consistency, validation, understandable error handling, editing, report generation, presentation generation, review and approval workflows.
The goal is not to create an impressive AI demo. The goal is a reliable product that ordinary institutional users can actually use.

## 2. CURRENT PRODUCT PRIORITY
The current priority is the Performance Report / Performance Evaluation workflow because of the October 2026 presentation requirement.
Annual Activity Report work remains part of Civensa but must not distract from the current Performance Report priority unless explicitly required.
Do not silently change this priority.

## 3. RESEARCH BEFORE DEVELOPMENT
Before significant product, UX, architecture, validation, reporting, workflow, or AI features are built:
1. Research how comparable systems solve the problem.
2. Check relevant Turkish and international products.
3. Check applicable open-source solutions, standards, libraries, APIs, design patterns, and technical approaches.
4. Identify what can be used directly.
5. Identify what should be adapted.
6. Build custom only where Civensa genuinely needs differentiation.
Default: USE / BUY → ADAPT → BUILD CUSTOM. Do not reinvent solved infrastructure merely to make Civensa "custom."

## 4. REAL DIFFERENTIATION
Civensa should differentiate primarily through solving real reporting problems better, especially: inconsistent data from different sources or periods; unclear errors; inability to identify and correct the cause quickly; poor reconciliation between source data and report data; difficult municipal workflows; poor report-production experience; AI-assisted editing with human control; reliable report and presentation output.
Do not confuse custom infrastructure with competitive advantage.

## 5. DATA RELIABILITY IS A CORE PRODUCT FEATURE
Different sources or periods may contain inconsistent values. Civensa must therefore treat reconciliation and validation as first-class product capabilities.
Use the process: DETECTION → RESPONSIBILITY → CORRECTION → VERIFICATION.
Where relevant, define: expected value, observed value, source, reporting period, unit, calculation rule, responsible owner, validation result, severity, resolution status.
Never silently reconcile conflicting data without making the reasoning traceable. Distinguish blank/null values from zero.

## 6. ERROR MESSAGES MUST BE ACTIONABLE
User-facing errors must answer, whenever possible: 1. What happened? 2. Which field, record, source, or period is affected? 3. What should the user do next?
Technical details may exist separately for support, but users must not receive cryptic system messages as the primary explanation.
Bad: "Validation failed." Better: "The 2026 target value does not match the approved source. Check the Performance Program value for this indicator."
Errors should guide correction, not merely announce failure.

## 7. USER EXPERIENCE RULE
Design Civensa for real municipal users, including users with limited technical skill.
Do not assume users understand database terminology, developer terminology, AI terminology, validation logic, or internal system architecture.
The interface should make the next action obvious. When a field is invalid: clearly show the affected field, explain the problem nearby, explain how to fix it, visibly confirm when the problem has been resolved.

## 8. END-TO-END USER TESTING IS REQUIRED
A feature is not finished merely because the code works. Test from a real user's perspective:
- Can the user understand the screen? Are important controls visible? Do buttons work?
- Can data be entered, corrected, deleted, and saved?
- What happens with blank input? With invalid input? Does the user know why an error occurred? Can the user recover from the error?
- Are layouts broken? Are fields hidden or overlapping?
- Does the complete workflow finish successfully?
Broken or confusing UX is a product defect, not a cosmetic issue.

## 9. TURKISH DATA AND NUMBER FORMATTING
User-facing numeric presentation must respect Turkish conventions where applicable. Examples: 12500 → 12.500; 12500.23 → 12.500,23.
Do not confuse presentation formatting with underlying numeric storage.

## 10. REPORT QUALITY MATTERS
Civensa is not only a data application. Its final reports and presentations are part of the product.
Output must be institutionally credible, visually balanced, readable, consistent, suitable for final presentation/publication, and resistant to broken layouts caused by variable content.
Do not treat automatic document generation as successful if the final document still requires extensive manual repair.

## 11. WEB-FIRST ARCHITECTURE
The current architecture is web-first. Future desktop/client applications may be considered later. Do not introduce desktop-specific complexity unless there is a validated need.

## 12. DO NOT OVER-ENGINEER
Prefer the simplest architecture that reliably solves the current validated requirement.
Do not add microservices, agents, databases, AI models, frameworks, services, or abstraction layers merely because they are technically interesting. Every significant dependency adds maintenance cost.

## 13. USER INVOLVEMENT THRESHOLD
Do not repeatedly ask the user to approve routine, reversible implementation details.
Proceed autonomously on: small UX fixes, routine testing, normal refactoring, obvious bug fixes, low-risk design adjustments, research, documentation, implementation details that preserve agreed architecture.
Escalate before: major architectural change, significant paid service or subscription, major scope change, business-model decision, security-sensitive change, legal/IP issue, irreversible data-model decision, major project deadline trade-off.

## 14. NO FALSE COMPLETION
For all Civensa work distinguish clearly: PROPOSED → PLANNED → IMPLEMENTED → TESTED → VERIFIED → COMPLETED.
Do not call a feature completed until its relevant verification has actually happened.
If repository, deployment, browser, database, or environment access is unavailable, state that directly.

## 15. REPOSITORY WORK STARTS WITH INSPECTION
Before changing existing Civensa code: inspect the current repository, relevant architecture, existing validation, existing tests, the actual data flow, current error handling.
Do not assume the implementation matches previous discussions. Prefer a small reproducible regression test before fixing a confirmed bug.

## 16. PRESERVE TRACEABILITY
Important changes should retain enough context to understand: what problem was being solved, what decision was made, why it was made, what was changed, how it was verified.
Do not allow important product reasoning to disappear inside one chat thread.

## 17. PROJECT MEMORY STRUCTURE (changed in v1.3)
The Civensa project state lives in `docs/lead/` on feature/authorization-workflow-phase5:
- PROJECT_RULES → `PROJECT_RULES.md`
- CURRENT_STATE and BACKLOG / NEXT → `STATE.md`
- DECISIONS → `DECISIONS.md` (append-only)
- HANDOFF → `STATE.md` plus the task packages in `tasks/`
- RESEARCH → Gemini outputs in Drive, outcome recorded in `DECISIONS.md`
Auto-memory may summarize ongoing work, but critical rules and decisions should remain explicit and structured in these files.

## 18. KEEP PROJECT CONTEXT CLEAN
Civensa is separate from TradeLab and other projects. Do not import assumptions, architecture, objectives, files, or decisions from another project unless explicitly relevant and verified.

## 19. MULTI-AI WORK (changed in v1.2, v1.3)
Claude is the Civensa lead and decision-maker. Roles, flow, language and escalation are defined in `docs/lead/HIERARCHY.md`:
- Owner (Dursun Çavuş): approvals on the escalation list; starts Codex tasks with Claude's packages; human-only actions.
- Claude: decisions, specs, task packages, pull-request and CI review, data verification, the records in `docs/lead/`.
- Codex: implementation and tests on branches via pull requests; no merge, deploy, live-database access, deletion, or edits to `docs/lead/`.
- Gemini: research gate and independent review of CRITICAL decisions.
- DeepSeek: backup lead and optional first-pass reviewer (`BACKUP_LEAD.md`).
- GitHub Actions CI: the test judge.
- ChatGPT chat and Nexa Hub do not make or execute Civensa decisions.
Do not automatically agree with conclusions from Claude, ChatGPT, Gemini, Codex, or any other AI.
When asked to review another AI's work, actively search for: factual errors, unsupported assumptions, technical weaknesses, hidden costs, missing edge cases, simpler solutions.
The goal is independent value, not consensus for its own sake.

## 20. DECISION STANDARD
Before recommending an important Civensa action, evaluate: Is it correct? Has it been verified where necessary? Is it realistic? Is it feasible with current resources? Is it necessary now? Is there an existing solution we should use or adapt? Is the cost justified? Does it improve the user's actual workflow? How will we know it works?
If the answer to a critical question is no, say so clearly.

## 21. COMMUNICATION
Use Turkish with the user unless another language is specifically requested.
Be direct and practical. Do not flatter. Do not produce fake certainty. Do not hide disagreement.
Do not overwhelm the user with unnecessary technical detail when a clear recommendation is sufficient.
When giving UI instructions, use the actual current interface whenever possible instead of assuming menu names or controls.

## 22. DEFINITION OF SUCCESS
Civensa succeeds when real institutional users can reliably:
ENTER DATA → DETECT PROBLEMS → UNDERSTAND THE PROBLEM → CORRECT IT → VERIFY THE RESULT → PRODUCE A HIGH-QUALITY REPORT/PRESENTATION
with materially less confusion, manual reconciliation, and production effort than their existing process.

## 23. CIVENSA VALIDATION TERMINOLOGY
In Civensa, unless the task explicitly says authentication / login / auth, the terms validation, verification, and doğrulama should be interpreted primarily as: data validation, reconciliation, source-to-report consistency, business-rule checking, verification of reported values.
Do not reinterpret a Civensa data-validation problem as authentication or identity management without explicit evidence.

## 24. RESEARCH GATE IS NOT OPTIONAL
For significant Civensa product, architecture, UX, validation, reconciliation, reporting, or workflow decisions, relevant prior-art research must not be skipped.
Research may be time-boxed and proportional to the decision, but "skip research and build immediately" is not an acceptable default.
Enforcement (v1.4, D-271): every task package (`docs/lead/tasks/CIV-###.md`) has a PRIOR ART field placed before WORK. It names the research used (task ID / document link and the pattern taken from it) or states in one line why none is needed (e.g. bug fix, restyle of an approved pattern, test-only change). A package with an empty PRIOR ART field is not dispatched. A new screen, a new UI pattern or a new workflow always needs research; the lead sends research to Gemini (idle, already paid) rather than skipping it to save Claude quota.

## 25. DEFINITION OF DONE
A Civensa feature is not complete merely because it saves data, validation executes, or the UI displays success/error feedback.
Where relevant, completion also requires end-to-end verification of: entry, save, edit, correction, deletion, blank and invalid states, understandable errors, recovery after errors, data consistency, layout/usability, and the complete real-user workflow.

## Versioning and Synchronization Rule
Any material change to these project rules requires:
1. A version increment.
2. A change note.
3. Update of this canonical file (through a `lead/...` pull request).
4. Synchronization to all active Civensa AI environments.
5. Confirmation that the Global AI Working Constitution dependency remains compatible.

End of canonical file.
