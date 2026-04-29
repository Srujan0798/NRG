# NRG Hybrid Prompt Stones

This folder contains the consolidated prompt set created from `prompts /`.
The original prompt files are preserved unchanged.

Use these as command protocols for focused work. Do not paste all of them at
once. Pick the stone that matches the task, attach the required project files,
and require evidence before accepting any completion claim.

## Recommended Use

1. Use `01_master_execution_stone.md` when starting or restarting the full
   production push.
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
