---
name: Grok Principal Engineer audit merge - 2026-04-25
description: Maps the Grok Principal Engineer readiness audit into existing launch blockers, risk register entries, Text-to-SQL hardening tests, and query corpus.
type: reference
---

This record maps the 2026-04-25 Grok Principal Engineer review into the active NRG workflow. The pasted review is now disposable input; agents execute against the files listed here.

## Classification

| Audit claim | Durable home | Status in current tree |
|---|---|---|
| Tier-specific response shapes must be proven against a running API | LB-1 in `BACKLOG.md`; protocol #46; `tests/api/test_tier_isolation_live.py`; local sanity evidence under `evidence/2026-04-26/local_sanity_t*_*.json` | Covered; evidence must be regenerated after response-shape changes |
| Credit-score parsing must exist in the production Text-to-SQL prompt, not only in regression assertions | `src/skills/text_to_sql/skill.py`; `src/skills/text_to_sql/schema_aware_prompt.py`; `tests/benchmarks/test_text_to_sql_prompt_hardening.py`; `tests/benchmarks/test_dhairya_regression.py` | Covered and focused test verified on 2026-04-26 |
| Live red-team replay must run against a running API before final local seal | LB-5 in `BACKLOG.md`; closure protocol #56; `scripts/red_team_live_replay.py` | Still open until regenerated against current HEAD |
| Full pytest must complete under 15 minutes without router-eval stalls | LB-4 in `BACKLOG.md`; closure protocol #57; `.claude/memory/bugs/venv-pytest-blocker.md` | Still open until canonical suite evidence is current |
| Seed-scale evidence must use at least 50k rows and cited responses for the canonical query set | LB-3 in `BACKLOG.md`; closure protocol #56; local sanity evidence | Partially covered locally; must be repeated after every LB code seal |
| Vector drift baseline cannot be claimed without populated Qdrant | C5 cluster-bound item in `BACKLOG.md`; `scripts/vector_drift_check.py`; master execution plan M6 | Cluster-bound until Qdrant baseline exists |
| 600 GB ingest and 1000-user load are not local code claims | Closure protocol #62; `docs/handover/DATA_INTAKE_PROTOCOL.md`; C4/C5 cluster gates | Cluster-bound |
| Strategic break questions around credits, TRL progression, grant/patent efficiency, follow-up context, PII blocking, graph depth, and SQL transparency | `tests/benchmarks/killer_queries.yaml`; `tests/orchestration/test_join_graph_blindness.py`; Dhairya regression suite | Covered in corpus; live execution still required for final seal |

## Verification Performed During Merge

- `tests/benchmarks/test_text_to_sql_prompt_hardening.py` passed on 2026-04-26.
- `schema_aware_prompt.py` was restored to read `db_struct.sql` from the repository root.
- No new blocker rows were created because the review maps cleanly to LB-1 through LB-5 plus existing cluster gates.

## Execution Rule

If this review is pasted again, do not reprocess it. Point to this file, then continue the closure sequence:

1. #56 for LB-1, LB-2, LB-3, and LB-5 live evidence.
2. #57 for LB-4 full-suite seal.
3. #58, #59, and #60 for schema parity, confidence defense, and semantic retrieval.
4. #61 and #62 for local seal and sovereign activation.
