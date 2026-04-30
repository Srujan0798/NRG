# Archive Notes

The original folder `prompts /` was not modified.

## Source Inventory

- `1` and `2`: principal engineer verification protocols with evidence gates,
  Dhairya failures, red-team checks, and live proof tests.
- `3`: user-experience audit from the professor's point of view.
- `4`: broad product delivery protocol including backend, data, frontend,
  show script, questions, and final artifacts.
- `6`: final audit prompt with specific traps and required deliverables.
- `7`: synthesis protocol with gap list, critical fixes, killer queries,
  walkthrough, and evidence folder.
- `11`: production cleanup and handover prompt.
- `13` and `14`: frontend hardening prompts.
- `15`: raw user concern prompt. It contained emotional context and an exposed
  API-looking secret. The reusable hybrid prompts intentionally do not copy that
  secret or the profane language.
- `16`: complete production web app prompt, especially the "not just landing
  page" constraint.
- `19`: full master execution protocol with 20-section production plan.
- `22`: focused final main-flow completion prompt.
- `d`, `g`, `k`, `m`, `q`, `z`: independent audit/verdict variants with useful
  technical risk maps, killer query ideas, gap protocols, and readiness scores.
- `10`: empty.
- `G `: audit-style prompt/output variant grouped with the audit family.

## Consolidation Decisions

- Execution protocols were merged into `01_master_execution_stone.md`.
- Login/query/result urgency was merged into `02_main_flow_stone.md`.
- Frontend polish and UX audit items were merged into
  `03_frontend_zero_flaw_stone.md`.
- Backend, Text-to-SQL, security, RBAC, audit-chain, and schema correctness were
  merged into `04_backend_security_data_stone.md`.
- Independent audit variants were merged into `05_audit_red_team_stone.md`.
- Evidence gates were merged into `06_evidence_acceptance_stone.md`.
- Show readiness, walkthrough, assistant-facing prep, and handover were merged
  into `07_show_readiness_handover_stone.md`.
- `ui-ux-pro-max` was partially merged into `02`, `03`, and `06`: chart
  selection rules, NRG-specific public-service/academic dashboard style
  selection, Lucide icon discipline, motion/z-index guardrails, and accessibility
  checks were kept. Generic industry palette catalogs, unrelated mobile-stack
  rules, and framework-specific scaffolding were not copied.
- `fullstack-dev` was partially merged into `01`, `02`, `04`, and `06`: service
  boundary discipline, env/CORS validation, API client contracts, safe error
  envelopes, structured observability, migration safety, SSE/WebSocket/job/cache
  guardrails, and release evidence gates were kept. Generic stack templates,
  language-specific boilerplate, broad testing catalogs, and unrelated framework
  recipes were not copied.
- `minimax-xlsx` was partially merged into `02`, `04`, `06`, and `07`:
  spreadsheet export integrity, formula-first XLSX output, formula validation,
  template-edit preservation, spreadsheet formula-injection defense, and
  date/identifier formatting evidence were kept. The low-level OOXML tutorial,
  helper script source, and financial-model-specific style catalog were not
  copied.
- External broad-validation prompts were distilled into `08`: query corpus
  breadth, workflow matrices, tier comparisons, interaction coverage, red-team
  passes, evidence indexing, and periodic checkpointing were kept. Artificial
  certainty, arbitrary hour/count demands, and impossible completion claims were
  not copied.

## Removed Or Normalized

- Duplicate "no vibe coding" language was collapsed into enforceable rules.
- Repeated "final warning" sections were replaced by acceptance gates.
- Raw profanity and personal attacks were removed.
- Unsafe secret text from `15` was not copied. If that key was real, rotate or
  revoke it.
- Claims like "zero flaws forever" were converted into testable checks.
- "Production-ready" language was made conditional on evidence.

## How To Keep This Folder Useful

- Add new prompt ideas only if they introduce a new capability or sharper
  acceptance criterion.
- Do not add another full duplicate master prompt. Update the relevant stone.
- Keep each stone task-specific.
- Keep evidence gates stricter than the implementation prompt.
- Keep stones aligned with `.claude/CURRENT_STATE.md` and
  `docs/specs/NRG_ETERNAL_MASTER_AGENT_PROMPT.md`. If current truth
  changes, update the shared current-state language instead of copying a new
  master protocol into this folder.
