# NRG Hybrid Prompt Stones

This folder contains the consolidated prompt set created from `prompts /`.
The original prompt files are preserved unchanged.

Use these as command protocols for focused work. Do not paste all of them at
once. Pick the stone that matches the task, attach the required project files,
and require evidence before accepting any completion claim.

## Current Operating Truth

Before assigning any stone, attach or tell the agent to read:

- `.claude/CURRENT_STATE.md`
- `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
- `docs/specs/NRG_ETERNAL_MASTER_AGENT_PROMPT.md`
- `Core_Idea_Clean.md`
- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
- `db_struct.sql`
- the latest relevant folder under `evidence/2026-04-30/`

Current project stance:

- NRG is locally show-ready for the verified answer-engine path.
- Local 100-user C4 smoke passed after the read-model/single-flight work:
  `evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/`.
- Production readiness is still blocked on 1000-user sovereign-cluster proof,
  deployed browser replay, production Qdrant baseline, and founder signing.
- Do not restart broad cleanup unless a dead file blocks the product path.
- `CORPUS/` is a portable mirror for AI handoff, not the canonical source tree.
  Run `python3 scripts/verify_corpus_sync.py` before using it.
- External apps, screenshots, and agent-built bundles are value sources, not
  replacement source trees. Use the hybrid release fusion skill under `.claude/skills/` to
  mine every useful UI, interaction, query, validation, and evidence idea, then
  adapt only NRG-compatible pieces into the existing product path.

## Recommended Use

1. Use `01_master_execution_stone.md` when starting or restarting the full
   production-path push or when a single agent must coordinate all remaining
   gates.
2. Use `02_main_flow_stone.md` when the only thing that matters is login,
   role selection, query, answer, proof, and polish.
3. Use `03_frontend_zero_flaw_stone.md` when the web app exists but feels
   broken, inconsistent, slow, or unprofessional.
4. Use `04_backend_security_data_stone.md` when fixing the API, Text-to-SQL,
   RBAC, audit chain, data contracts, and query correctness.
5. Use `05_audit_red_team_stone.md` when asking an agent to judge the system
   honestly before showing it to anyone.
6. Use `06_evidence_acceptance_stone.md` as the proof gate before accepting
   "done".
7. Use `07_show_readiness_handover_stone.md` for professor-assistant readiness,
   walkthrough, screenshots, critical queries, and handover package.
8. Use `08_full_coverage_validation_campaign_stone.md` when the task is broad
   validation across many queries, workflows, tiers, UI states, security probes,
   audit proof, and performance evidence.
9. Use the hybrid release fusion skill under `.claude/skills/` before merging any external
   app or agent-built bundle. The required first output is a value matrix:
   source, useful idea, decision, NRG target, and verification gate.

## Current Wave Map

Use this order unless `.claude/CURRENT_STATE.md` says otherwise:

1. Backend answer correctness and stable `/query` contract.
2. SQL/RAG retrieval truth and health honesty.
3. Frontend main-flow proof.
4. Security, tier, and audit proof.
5. Deployment-grade performance proof, especially the 1000-user cluster C4 run.
6. Full-coverage validation campaign when broad confidence is needed.
7. Handover evidence and walkthrough refresh.

When external app material is present, run the fusion skill before choosing a
wave. Useful UI/UX and interaction patterns usually feed Wave 3; query examples
and response behavior feed Waves 1, 2, and 6; unsafe replacement code is rejected
as a direct merge but can still become tests, docs, or backlog.

The local C4 read-model pass is complete. The next performance assignment is
not to rebuild the read model again; it is to prove it in the target deployment.

## Hybrid Map

| Hybrid stone | Source prompt family |
| --- | --- |
| `01_master_execution_stone.md` | `1`, `2`, `4`, `7`, `11`, `16`, `19`, `22`, selected `fullstack-dev` architecture gates |
| `02_main_flow_stone.md` | `15`, `16`, `22`, `3`, critical parts of `7`, selected streaming/error/export UX gates |
| `03_frontend_zero_flaw_stone.md` | `13`, `14`, `16`, `3`, frontend parts of `4` and `19` |
| `04_backend_security_data_stone.md` | backend/security/data parts of `1`, `2`, `6`, `7`, `19`, `m`, selected `fullstack-dev` backend boundaries, selected spreadsheet/export safety rules |
| `05_audit_red_team_stone.md` | `6`, `d`, `g`, `k`, `m`, `q`, `z` |
| `06_evidence_acceptance_stone.md` | evidence gates from `1`, `2`, `7`, `19`, `6`, `k`, `m`, selected `ui-ux-pro-max`, `fullstack-dev`, and spreadsheet/export gates |
| `07_show_readiness_handover_stone.md` | show script and readiness parts from `3`, `4`, `7`, `q`, `m` |
| `08_full_coverage_validation_campaign_stone.md` | broad coverage strategy distilled from external validation prompts, merged with NRG-specific evidence, tier, UI, query, audit, and performance gates |

## What Changed

- Repeated versions were merged into one stronger prompt per task.
- Raw anger, profanity, and unsafe secret material were removed from reusable prompts.
- Completion claims were replaced with evidence gates.
- "Just make it look good" instructions were converted into explicit screens,
  contracts, tests, and proof artifacts.
- The empty source file `prompts /10` was treated as unused.

## Non-Negotiable Operating Rule

Prompts do not make a production system by themselves. A stone is valid only
when it forces this loop:

1. Read the real repo and source docs.
2. Identify the actual gap.
3. Patch the code or docs.
4. Run fresh verification.
5. Save evidence.
6. Report only what is proven.

Every agent final response must include files changed, tests or commands run,
evidence paths, blockers, and commit SHA if committed or `not committed`.
