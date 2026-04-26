---
name: Principal Engineer audit merge - 2026-04-25
description: Maps same-day Grok, Claude, Product Auditor, Kimi/Moonshot, and MiniMax readiness audits into existing launch blockers, risk register entries, Text-to-SQL hardening tests, and query corpus.
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

## Product Auditor Funding-Readiness Addendum

The later Product Auditor review emphasized funding-readiness, data-sovereignty proof, browser-path stability, and scale evidence. It maps to existing execution homes and does not create a new task track.

| Added emphasis | Durable home | Status |
|---|---|---|
| The Dhairya 41 percent baseline remains the external starting point; a team-written regression suite is insufficient without live generalization evidence | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`; LB-2, LB-7, LB-8; `tests/benchmarks/killer_queries.yaml` | Covered; current-head live evidence still required |
| TRL term handling, exact schema naming, aggregation logic, join validity, and no-result behavior are user-trust risks | LB-2, LB-3, LB-7, LB-8; `tests/benchmarks/killer_queries.yaml`; `tests/orchestration/test_join_graph_blindness.py` | Covered by corpus and semantic-retrieval work; must be rerun against current stack |
| PII masking, RBAC response shaping, egress control, WORM logs, and tamper-proof audit trails must be demonstrated, not asserted | LB-1, LB-5; protocols #39, #46, #50; `.claude/memory/patterns/db-layer-defence.md`; `.claude/memory/patterns/network-policy-worm-logs.md` | Covered; live API and cluster evidence still required |
| Browser-path risks include slow dashboard render, blank zero-result state, raw error exposure, and unsupported answers | Frontend M5a work; `.claude/rules/ux/protocol.md`; LB-3 evidence; `frontend/tests/` | Covered; needs fresh browser evidence after frontend changes |
| Scale roadmap requires composite indexes, partitioning, materialized views, load evidence, Helm, and disaster-recovery proof | LB-6; C4/C5 cluster gates; `.claude/memory/patterns/partitioning-pitr.md`; `infrastructure/helm/nrg/`; `infrastructure/sovereign/disaster_recovery.sh` | Covered; cluster-bound proof still required |
| Three strategic Product Auditor queries on TRL conversion by state, academic-origin patent growth, and three-party collaboration | `tests/benchmarks/killer_queries.yaml` `KILLER-10..12` | Already in canonical corpus |

## Kimi/Moonshot Addendum

The Kimi/Moonshot review and its self-audit cross-check repeated the same production blockers with sharper severity language. The durable signal is already captured in existing gates; the operator suggestions to bypass weak surfaces are treated only as feature-flag discipline, never as completion evidence.

| Added emphasis | Durable home | Status |
|---|---|---|
| Tier payloads must differ structurally, not just visually; identical Tier 1/2/3 JSON is a compliance failure | LB-1; `.claude/memory/patterns/tier-shape-boundary.md`; `scripts/regen_evidence.sh`; `tests/api/test_tier_isolation_live.py` | Open until 09/10/11 evidence is regenerated against current HEAD |
| Live red-team evidence must supersede contradictory old reports; unit-level security passes cannot close the live-gateway question | LB-5; `scripts/red_team_live_replay.py`; closure protocol #56 | Open until replay output is timestamped and audit-bound |
| Zero-request load output is a failed C4 run, not partial evidence | C4 cluster gate; `tests/load/locustfile.py`; `scripts/load_test_run.py`; `docs/ops/LOAD_TEST_REPORT_TEMPLATE.md` | Cluster-bound until request count, p95, p99, and failure rate are recorded |
| Vector drift quality below SLO means the RAG path cannot be part of a user-facing flow until the Qdrant baseline is established | C5 cluster gate; `scripts/vector_drift_check.py`; `.claude/memory/patterns/acceptance-path-discipline.md` | Cluster-bound; feature flag required while C5 is below PASS |
| Audit-chain mismatch must be treated as a C2 blocker until runtime append and rebuild paths verify with the same key discipline | `.claude/memory/bugs/audit-singleton.md`; `.claude/memory/patterns/audit-reliability-check.md`; closure protocol #61 | Covered; final seal requires fresh verify output |
| Credit parsing, TRL synonyms, patent-cost join key, query-plan indexes, and follow-up context remain the hard Text-to-SQL correctness spine | LB-2, LB-6, LB-7, LB-8; `tests/benchmarks/killer_queries.yaml`; `tests/benchmarks/test_text_to_sql_prompt_hardening.py` | Covered by existing tests and schema work; live execution still required |
| Kimi's three strategic analytics questions | `tests/benchmarks/killer_queries.yaml` `KILLER-13..15` | Already in canonical corpus |

## MiniMax Addendum

The MiniMax review converged on the same hard blockers and added two new strategic analytics queries. Its user-session workarounds are classified as feature-flag discipline only; they do not replace the required LB evidence.

| Added emphasis | Durable home | Status |
|---|---|---|
| Follow-up context loss is the most natural user-session failure mode; Q10/Q12 must be treated as live-flow blockers, not only regression fixtures | LB-2, LB-7; `.claude/memory/bugs/silent-wrong-answer.md`; `tests/benchmarks/killer_queries.yaml` ADV follow-up cases | Covered; current-head live proof still required |
| Audit-chain singleton repair must survive process restart and runtime append, not only one rebuild script | `.claude/memory/bugs/audit-singleton.md`; `.claude/memory/patterns/audit-reliability-check.md`; closure protocol #61 | Covered; final seal requires fresh verify output |
| The 47-to-58 table bridge must either create the support tables or explicitly document separate ownership; ambiguity blocks schema parity | LB-6; `tests/data/test_schema_parity.py`; closure protocol #58 | Covered; open until schema parity is live |
| Full-suite stalls and slow PII tests are CI confidence blockers even when focused suites pass | LB-4; `.claude/memory/bugs/venv-pytest-blocker.md`; closure protocol #57 | Open until canonical suite evidence is current |
| 6-node pipeline checks must include routing metadata, provider fallback, verifier citation checks, and graceful degradation on node failure | LB-7; orchestration tests; `src/orchestration/` | Covered by existing gates; live and full-suite evidence still required |
| MiniMax strategic analytics questions on TRL progression, cost-per-patent versus TRL diversity, and PhD-course-to-incubation gap | `tests/benchmarks/killer_queries.yaml` `KILLER-16..18` | KILLER-16 already existed; KILLER-17..18 added during this merge |

## Verification Performed During Merge

- `tests/benchmarks/test_text_to_sql_prompt_hardening.py` passed on 2026-04-26.
- `schema_aware_prompt.py` was restored to read `db_struct.sql` from the repository root.
- Kimi/Moonshot strategic questions are already present as `KILLER-13..15`.
- MiniMax strategic questions are present as `KILLER-16..18`.
- No new blocker rows were created because the reviews map cleanly to LB-1 through LB-8 plus existing cluster gates.

## Execution Rule

If any same-day Principal Engineer, Product Auditor, Kimi/Moonshot, or MiniMax review is pasted again, do not reprocess it. Point to this file, then continue the closure sequence:

1. #56 for LB-1, LB-2, LB-3, and LB-5 live evidence.
2. #57 for LB-4 full-suite seal.
3. #58, #59, and #60 for schema parity, confidence defense, and semantic retrieval.
4. #61 and #62 for local seal and sovereign activation.
