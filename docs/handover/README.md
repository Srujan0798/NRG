# NRG Handoff Package - Master Index

**Version:** 2026-04-27 local validation refresh
**Classification:** IIT-GN internal handoff
**Owner:** NRG engineering team

This directory is the operator-facing handoff package for National Research Graph. It is written for the professor's assistant, IIT-GN operators, security reviewers, and developers who need to run, audit, and extend the system without relying on the original builders.

## Current Status

NRG is locally handoff-ready for professor-assistant technical evaluation. The local release has reproducible evidence for schema parity, tier response filtering, critical query execution, audit-chain verification, frontend build, and live red-team replay.

Three gates still require external infrastructure before a sovereign-cluster production sign-off:

| Gate | Status | Reason |
|---|---:|---|
| C4 load SLO at 1000 concurrent users | External gate | Requires the target sovereign Kubernetes cluster and representative data volume. |
| C5 vector-drift baseline | External gate | Requires the production Qdrant corpus and scheduled drift baseline. |
| 600GB real dataset ingest | External gate | Requires official dataset access and the signed intake window. |

Do not claim sovereign-cluster production sign-off until those three items are executed and recorded.

## Handoff Artifacts

| # | Document | Purpose | Primary Audience |
|---|---|---|---|
| 1 | [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) | Plain-English system overview and value model | IIT-GN leadership, ministry reviewers |
| 2 | [ARCHITECTURE.md](ARCHITECTURE.md) | 5-layer system architecture and runtime flow | Engineers, NIC reviewers |
| 3 | [API_REFERENCE.md](API_REFERENCE.md) | Endpoint contracts, request examples, response shapes | Developers and integrators |
| 4 | [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) | Boot, health checks, backup, incidents, recovery | Operators and on-call engineers |
| 5 | [SECURITY_COMPLIANCE_ATTESTATION.md](SECURITY_COMPLIANCE_ATTESTATION.md) | DPDP, RBAC, egress, audit evidence map | Security and compliance reviewers |
| 6 | [DATA_INTAKE_PROTOCOL.md](DATA_INTAKE_PROTOCOL.md) | SFTP, GPG, HMAC intake workflow | Data and infrastructure teams |
| 7 | [UAT_RESULTS.md](UAT_RESULTS.md) | User acceptance test plan and sign-off template | Professor, ministry, industry evaluators |
| 8 | [PITCH_DECK_GUIDE.md](PITCH_DECK_GUIDE.md) | Capability narrative guide for executive review | Presenter and leadership team |

Supporting documents outside this directory:

| Document | Purpose |
|---|---|
| [../../README.md](../../README.md) | Developer setup and local run instructions |
| [../SCHEMA.md](../SCHEMA.md) | 58-table schema reference generated from `db_struct.sql` |
| [../PRODUCTION_WALKTHROUGH.md](../PRODUCTION_WALKTHROUGH.md) | Presenter workflow and critical query sequence |
| [../PRODUCTION_READINESS_SUMMARY.md](../PRODUCTION_READINESS_SUMMARY.md) | Engineering summary of fixes, evidence, and remaining external gates |

## Evidence Index

Fresh evidence from 2026-04-26 is stored under `evidence/2026-04-26/`.
Additional 2026-04-27 evidence is stored under `evidence/2026-04-27/`.

| Evidence | What It Proves |
|---|---|
| `test_suite_full.log` | Full fast test suite completed: 1572 passed, 63 skipped, 219 deselected in 250.34s. |
| `37_live_red_team_replay_chunked.md` | Live API replay completed with 0 dangerous allowed responses. |
| `killer_query_health.json` | Three critical production queries returned rows with P95 under 60ms on the local reference dataset. |
| `schema_parity_58_58.txt` | Alembic/schema parity reached 58/58 tables with expected skips only. |
| `explain_index_usage.txt` | Local query-plan evidence for critical indexes and query paths. |
| `production_validation/tier_differentiation_live.json` | Tier-filtering evidence for API responses. |

Additional 2026-04-27 evidence:

| Evidence | What It Proves |
|---|---|
| `critical_query_regression.log` | Dhairya adversarial suite plus API critical-query tests completed: 78 passed in 4.84s. |
| `cost_per_patent_10cr_results.csv` | Local reference data returns valid cost-per-granted-patent rows for institutes above the ₹10Cr grant threshold. |
| `critical_query_cost_per_patent.md` | Engineering note for the cost-per-granted-patent production-query hardening. |

## Local Operator Quick Start

```bash
docker compose up -d
curl http://localhost:8000/health/all
curl http://localhost:8000/audit/verify
```

For detailed setup, seed, test, and troubleshooting instructions, start with [../../README.md](../../README.md).

## Sign-Off Checklist

| Area | Local Evidence Status | External Sign-Off Needed |
|---|---:|---:|
| API response contract | Complete | No |
| Tier response filtering | Complete | No |
| 58-table schema parity | Complete | No |
| Audit chain verification | Complete | No |
| Live red-team replay | Complete | No |
| Frontend build | Complete | No |
| 1000-user C4 SLO | Pending cluster run | Yes |
| Qdrant C5 drift baseline | Pending corpus baseline | Yes |
| Official 600GB ingest | Pending data access | Yes |

## Ownership Notes

NRG can be handed to the professor's assistant for local technical evaluation now. The production operator should not remove the external-gate language until cluster load testing, vector baseline, and official dataset ingestion have all been run and attached as evidence.

*Last updated: 2026-04-27*
