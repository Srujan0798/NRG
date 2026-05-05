# Principal Auditor External Audit Merge - 2026-04-26

This record maps the 2026-04-26 Principal Auditor review into existing NRG execution assets. The pasted review is now disposable input; agents execute against the files listed below.

## Classification

| Audit claim | Durable home | Execution owner |
|---|---|---|
| Text-to-SQL 41 percent baseline, schema context overload, and join graph blindness | `protocols/53_LB8_SEMANTIC_LAYER_SCHEMA_RAG.md`; `tests/benchmarks/killer_queries.yaml`; `.claude/memory/references/dhairya-benchmark.md` | backend + ml + data architecture |
| 58-table parity, hot join indexes, RLS, and Tier 1/2/3 data-shape proof | `protocols/51_LB6_SCHEMA_PARITY_58_TABLES.md`; `docs/specs/CLOSURE_PLAN_2026-04-26.md` protocol #58 | backend + database |
| Silent wrong-answer defense, anomaly detection, confidence UI, and clarification fallback | `protocols/52_LB7_SEMANTIC_SQL_SELF_CORRECTION.md`; `.claude/memory/bugs/silent-wrong-answer.md`; closure protocol #59 | backend + ml + frontend |
| PostgreSQL 63-byte identifier risk for the long TRL field | `.claude/memory/bugs/postgres-identifier-limit.md`; `docs/runbooks/PRODUCTION_LAUNCH_RISK_REGISTER.md` risk #22 | database |
| `total_credit_score` text parsing and materialized scored view requirement | `tests/benchmarks/killer_queries.yaml` advanced corpus; LB-8 semantic glossary requirement | backend + database |
| DPDP dynamic masking, k-anonymity, and HMAC trigger enforcement below the API layer | `.claude/memory/patterns/db-layer-defence.md`; `.claude/memory/patterns/k-anonymity-threshold.md`; LB-6 RLS acceptance | security + database |
| Prompt-injection, SSRF, and system-prompt extraction risks | LB-5 live red-team replay; `docs/runbooks/PRODUCTION_LAUNCH_RISK_REGISTER.md` risks #2, #6, #7, #8 | security |
| AIRAWAT / SLURM asynchronous execution and 60-second load-balancer cutoff | `.claude/memory/patterns/async-compute-queue.md`; risk register #28 | devops + backend |
| PgBouncer / connection-pool exhaustion risk | risk register #29; M5b performance track in master execution plan | devops |
| UX cold-start, clarification, null-result, Bhashini, transparent computation, and mobile table degradation | `.claude/rules/ux/protocol.md` and frontend M5a acceptance work | frontend + product |
| Three strategic query scenarios from the review | `tests/benchmarks/killer_queries.yaml` v11 corpus: `KILLER-07`, `KILLER-08`, `KILLER-09` | testing + data |

## Execution Rule

No new parallel task pack is created from this audit. Existing authority remains:

1. `docs/specs/MASTER_EXECUTION_PLAN_2026-04-25.md`
2. `docs/specs/CLOSURE_PLAN_2026-04-26.md`
3. `protocols/51_LB6_SCHEMA_PARITY_58_TABLES.md`
4. `protocols/52_LB7_SEMANTIC_SQL_SELF_CORRECTION.md`
5. `protocols/53_LB8_SEMANTIC_LAYER_SCHEMA_RAG.md`
6. `tests/benchmarks/killer_queries.yaml`

## Non-Negotiable Evidence

- LB-6 is not closed until schema parity reports 58/58, RLS tier counts differ on the same live PostgreSQL instance, and hot-join EXPLAIN output shows no sequential scans on foreign-key paths.
- LB-7 is not closed until low-confidence or anomalous results route to retry or clarification instead of shipping as confident answers.
- LB-8 is not closed until the join graph covers all 58 tables, schema retrieval reaches recall@5 >= 90 percent, and prompt payload drops by at least 60 percent versus full-DDL packaging.
- The strategic query corpus is not considered stable until `KILLER-07..09` return cited rows through the production planner path.
