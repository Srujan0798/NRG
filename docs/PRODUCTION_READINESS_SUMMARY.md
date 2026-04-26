# NRG Production Readiness Summary

Date: 2026-04-26, updated 2026-04-27
Scope: local release validation on the founder laptop plus evidence captured in `evidence/2026-04-26/`

## Executive Status

NRG is locally handoff-ready for professor-assistant evaluation. The core application, SQL generation path, tier response boundary, schema bridge, red-team replay, frontend build, and handoff documentation now have reproducible evidence.

NRG is not yet fully signed off for sovereign-cluster operation because three external gates require infrastructure and data that are not present on this laptop:

- C4: 1000-user P99 SLO on the sovereign Kubernetes target.
- C5: Qdrant vector-drift baseline after the target collection is populated.
- Data intake: real 600GB PostgreSQL load and validation.

Those are deployment-environment gates, not code paths that can be honestly proven from this workspace.

## Code and Configuration Changes

- Fixed the container startup contract: `postgres` now participates in the `prod` compose profile, matching the documented `docker compose --profile prod up -d` path.
- Hardened `scripts/red_team_live_replay.py` local startup by forcing the API-owned process to skip embedding warm-up and Indic fallback loading. This prevents local security replay startup from waiting on model initialization.
- Added regression tests for both release contracts:
  - `tests/unit/test_compose_config.py::test_prod_profile_starts_postgres_dependency`
  - `tests/scripts/test_red_team_live_replay.py::test_local_api_startup_skips_embedder_warmup`
- Generated `docs/SCHEMA.md` from `db_struct.sql`; it now lists all 58 parsed tables and every parsed column.

## Verified Gates

| Gate | Evidence | Result |
|---|---|---|
| Dhairya SQL and adversarial suite | `tests/benchmarks/test_dhairya_regression.py`, `tests/benchmarks/test_dhairya_adversarial.py` | PASS |
| Tier response boundary | `tests/api/test_tier_isolation_live.py`, `tests/api/test_tier_response_filtering.py`, `tests/api/test_k_anonymity_response_boundary.py` | PASS |
| Schema parity, indexes, RLS | `tests/data/test_schema_parity.py`, `tests/data/test_schema_indexes.py`, `tests/data/test_rls_policies.py` | PASS |
| Silent wrong-answer controls | `tests/skills/test_result_anomaly_detector.py`, `tests/orchestration/test_silent_wrong_answer.py` | PASS |
| Schema-RAG and join graph | `tests/orchestration/test_join_graph_blindness.py`, `tests/skills/test_schema_retriever.py` | PASS |
| Full fast suite | `evidence/2026-04-26/test_suite_full.log` | 1572 passed, 63 skipped, 219 deselected in 250.34s |
| Critical query health | `evidence/2026-04-26/killer_query_health.json` | healthy, all P95 values under 4s |
| Live red-team replay | `evidence/2026-04-26/37_live_red_team_replay_chunked.md` | 192 BLOCKED, 12 DOWNGRADED, 6 ALLOWED-SAFE, 0 ALLOWED-DANGEROUS |
| Frontend build | `npm run build` from `frontend/` | PASS |
| Compose config | `docker compose config --quiet` | PASS |

## Critical Query Evidence

The local volumetric reference database contains enough data for meaningful query validation:

- `academic_courses_details`: 50,000 rows
- `innovations_at_various_stages_of_technology_readiness_level`: 10,000 rows
- `innovation_grant_from_govt`: 30,000 rows
- `combined_ipo_patent_data`: 20,000 rows
- `publications`: 100,000 rows
- `researchers`: 5,615 rows

Critical query P95 timings from `killer_query_health.json`:

- KILLER-01: 25.04ms, 8 rows, citation present.
- KILLER-02: 52.95ms, 4 rows, citation present.
- KILLER-03: 22.8ms, 3 rows, citation present.

### 2026-04-27 Critical Query Addendum

The requested critical query set now includes **Cost per granted patent for institutes with >₹10Cr grants**. That path is covered by fresh code, regression tests, and local data evidence:

- API bounded query path: `src/api/main.py`
- Text-to-SQL fallback path: `src/skills/text_to_sql/skill.py`
- Regression evidence: `evidence/2026-04-27/critical_query_regression.log` (`78 passed in 4.84s`)
- Result evidence: `evidence/2026-04-27/cost_per_patent_10cr_results.csv`
- Detailed note: `evidence/2026-04-27/critical_query_cost_per_patent.md`

The SQL semantics are:

- grants grouped by `innovation_grant_from_govt.institute`
- threshold preserved as `HAVING SUM(grant_received) > 100000000`
- patents counted from `combined_ipo_patent_data`
- patents filtered with `status = 'Granted'`
- applicant-to-institute join uses `combined_ipo_patent_data.applicants`
- null cost-per-patent values sorted after valid numeric ratios

### 2026-04-27 Production Web Application Addendum

The authenticated web app now includes production support screens beyond the front page:

- `/app/publications`: live publications explorer.
- `/app/researchers`: Tier 1 researcher profile workspace.
- `/app/reports`: Tier 2 aggregate government reports.
- `/app/industry`: Tier 3 anonymized capability view.
- `/app/settings`: session profile and audit trail view.

Fresh evidence:

- `docs/audits/frontend_production_app_2026-04-27/frontend-tests.log`: 19 suites passed, 71 tests passed.
- `docs/audits/frontend_production_app_2026-04-27/frontend-build.log`: Vite production build passed.
- `docs/audits/frontend_production_app_2026-04-27/frontend-lint.log`: ESLint passed with no warnings.
- `docs/audits/frontend_production_app_2026-04-27/screenshots/`: desktop and mobile captures for login, publications, researchers, reports, industry, and settings.
- `docs/audits/frontend_production_app_2026-04-27/videos/`: production walkthrough recordings from the local running stack.

The `/researchers` API crash found during screen validation is fixed and covered:

- `tests/data/test_database_v2_schema_drift.py`
- `evidence/2026-04-27/researchers_schema_drift_regression.log`
- `evidence/2026-04-27/researchers_endpoint_schema_drift_live.txt`

Tier 3 researcher PII protection was replayed live:

- `evidence/2026-04-27/tier3_researchers_pii_guard_live.txt`
- `evidence/2026-04-27/tier3_researchers_pii_guard_assertion.log`

## Handoff Position

The project can be handed to the professor’s assistant for local evaluation with this constraint statement:

> The local release path is green and evidence-backed. Final sovereign operation requires running the same gates on the target Kubernetes/PostgreSQL/Qdrant environment after the real data load.

Do not represent cluster SLO, Qdrant baseline, or 600GB ingest as complete until the corresponding evidence exists.
