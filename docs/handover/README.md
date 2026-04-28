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
| [../operations/PHASE7_SOVEREIGN_ACTIVATION_RUNBOOK.md](../operations/PHASE7_SOVEREIGN_ACTIVATION_RUNBOOK.md) | Sovereign cluster activation commands and evidence gates |
| [HANDOVER_PACKET_MANIFEST.md](HANDOVER_PACKET_MANIFEST.md) | Final zip contents and packaging gate |
| [../SCHEMA.md](../SCHEMA.md) | 58-table schema reference generated from `db_struct.sql` |
| [../PRODUCTION_WALKTHROUGH.md](../PRODUCTION_WALKTHROUGH.md) | Presenter workflow and critical query sequence |
| [../PRODUCTION_READINESS_SUMMARY.md](../PRODUCTION_READINESS_SUMMARY.md) | Engineering summary of fixes, evidence, and remaining external gates |
| [../../FRONTEND_PRODUCTION_READINESS_REPORT.md](../../FRONTEND_PRODUCTION_READINESS_REPORT.md) | Frontend hardening report, screen coverage, evidence, and remaining physical-device gates |

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
| `PRODUCTION_WEB_APP_STATUS.md` | Full authenticated web application support screens, role-aware navigation, screenshot/video evidence, and remaining external blockers. |
| `researchers_schema_drift_regression.log` | Regression coverage for `/researchers` schema drift when deployed tables lack newer ORM columns. |
| `researchers_endpoint_schema_drift_live.txt` | Live Tier 1 `/researchers` request returns HTTP 200 after the schema-drift fix. |
| `tier3_researchers_pii_guard_live.txt` | Live Tier 3 `/researchers` request returns anonymized aggregates rather than individual records. |
| `tier3_researchers_pii_guard_assertion.log` | Automated assertion that the Tier 3 `/researchers` response contains no email, phone, name, or `@` token. |
| `docs/audits/frontend_production_app_2026-04-27/frontend-tests.log` | Frontend Jest suite completed: 19 suites passed, 71 tests passed. |
| `docs/audits/frontend_production_app_2026-04-27/frontend-build.log` | Vite production build completed successfully. |
| `docs/audits/frontend_production_app_2026-04-27/frontend-lint.log` | ESLint completed with no warnings. |
| `docs/audits/frontend_production_app_2026-04-27/screenshots/` | Desktop and mobile captures for login, publications, researchers, reports, industry, and settings. |
| `docs/audits/frontend_production_app_2026-04-27/videos/` | Production walkthrough recordings captured from the local running stack. |
| `FRONTEND_PRODUCTION_READINESS_REPORT.md` | Final frontend hardening report covering issues found, fixes shipped, evidence, and physical-device items not locally proven. |
| `docs/audits/frontend_hardening_2026-04-27/frontend-tests.log` | Hardened frontend Jest suite completed: 19 suites passed, 76 tests passed. |
| `docs/audits/frontend_hardening_2026-04-27/frontend-build.log` | Hardened Vite production build completed successfully. |
| `docs/audits/frontend_hardening_2026-04-27/frontend-lint.log` | Hardened ESLint run completed with no warnings. |
| `docs/audits/frontend_hardening_2026-04-27/console-summary.txt` | Automated browser pass recorded zero console errors, page errors, request failures, and HTTP 4xx/5xx responses. |
| `docs/audits/frontend_hardening_2026-04-27/before/` | Before screenshots for login and all authenticated support screens on desktop and mobile. |
| `docs/audits/frontend_hardening_2026-04-27/after/` | After screenshots for login and all authenticated support screens on desktop and mobile. |
| `docs/audits/frontend_hardening_2026-04-27/videos/` | Production walkthrough recording captured from the local hardened running stack. |
| `evidence/2026-04-27/final_validation/FINAL_PRODUCTION_REVALIDATION.md` | Final local revalidation summary, one-command compose fix, test evidence, and honest Docker-daemon limitation. |

Additional 2026-04-28 / 2026-04-29 evidence:

| Evidence | What It Proves |
|---|---|
| `evidence/2026-04-28/UAT_T1_queries.md` | Tier 1 researcher UAT query set and expected filtering behavior. |
| `evidence/2026-04-28/UAT_T2_queries.md` | Tier 2 ministry UAT query set and aggregate-only filtering behavior. |
| `evidence/2026-04-28/UAT_T3_queries.md` | Tier 3 industry UAT query set and public-data-only filtering behavior. |
| `evidence/2026-04-28/K1_health_qdrant_critical.log` | Qdrant zero-vector health behavior returns CRITICAL. |
| `evidence/2026-04-28/K3_trl_view_test.log` | TRL view and 63-byte identifier guard tests pass. |
| `evidence/2026-04-28/K5A_vocab_check_pass.log` | Full-repo production vocabulary gate exits cleanly. |
| `evidence/2026-04-28/locust_100u_v2.json` | K-2 100-user load evidence; C4 remains failed by latency. |
| `evidence/2026-04-28/docs_sync_report.txt` | Docs-sync findings and open documentation drift. |
| `evidence/2026-04-28/handover_packet_complete.log` | Handover packet structural completeness check. |
| `evidence/2026-04-28/sprint_review.md` | Sprint review, quality-bar status, and next-sprint questions. |

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

*Last updated: 2026-04-29*
