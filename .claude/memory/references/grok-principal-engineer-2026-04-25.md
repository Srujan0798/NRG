---
name: Principal Engineer audit merge - 2026-04-25
description: Maps same-day Grok and Claude Principal Engineer readiness audits into existing launch blockers, risk register entries, Text-to-SQL hardening tests, and query corpus.
type: reference
---

This record maps the 2026-04-25 Principal Engineer reviews into the active NRG workflow. The pasted reviews are now disposable input; agents execute against the files listed here.

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

## Same-Day Claude Principal Engineer Addendum

The later Claude Principal Engineer review on 2026-04-25 maps to the same execution homes and does not create a new task track.

| Added emphasis | Durable home | Status |
|---|---|---|
| Six-node pipeline checks for receiver state, planner decomposition, router classification, executor correctness, synthesizer fallback, and verifier claim checks | `tests/orchestration/`; LB-2, LB-7, and LB-8 protocols | Covered by existing protocol gates; live proof still required |
| Ten cross-table break questions covering patent/grant joins, TRL stage ordering, median patent timelines, intake disparity, PII-aware email-domain analysis, state-level expenditure, startup joins, per-year ranking, citation casting, and entity resolution | `tests/benchmarks/killer_queries.yaml` `ADV-11..20` | Already in canonical corpus |
| Three strategic query scenarios for biotech grant-to-patent efficiency, NIRF rank versus sponsored research, and international collaboration citation impact | `tests/benchmarks/killer_queries.yaml` `KILLER-04..06` | Already in v1.1 corpus |
| Dashboard scale and visible trust signals must not rely on tiny seed counts | `.claude/memory/patterns/dashboard-decoupled-metadata.md`; LB-3 seed-scale evidence | Covered; must be rechecked after frontend changes |
| Runtime tier filtering and live red-team replay remain mandatory before local seal | LB-1 and LB-5; closure protocol #56 | Still open until regenerated against current HEAD |

## Verification Performed During Merge

- `tests/benchmarks/test_text_to_sql_prompt_hardening.py` passed on 2026-04-26.
- `schema_aware_prompt.py` was restored to read `db_struct.sql` from the repository root.
- No new blocker rows were created because the reviews map cleanly to LB-1 through LB-8 plus existing cluster gates.

## Execution Rule

If either same-day Principal Engineer review is pasted again, do not reprocess it. Point to this file, then continue the closure sequence:

1. #56 for LB-1, LB-2, LB-3, and LB-5 live evidence.
2. #57 for LB-4 full-suite seal.
3. #58, #59, and #60 for schema parity, confidence defense, and semantic retrieval.
4. #61 and #62 for local seal and sovereign activation.
