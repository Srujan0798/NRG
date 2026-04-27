# NRG Live Completion Evidence Summary

Date: 2026-04-27
Host: local API on `127.0.0.1:8010` with forwarded PostgreSQL, Redis, and Qdrant

## Code Changes

1. API response boundary:
   - File: `src/auth/rbac_policies.yaml`
   - Added `government_grant_value` as a tier response field class.
   - Tier 3 is no longer allowed to receive grant amount fields such as `grant_received`, `total_grant`, or `sum_grant_received`.

2. Regression coverage:
   - File: `tests/api/test_tier_response_filtering.py`
   - Added `test_industry_response_strips_government_grant_amount_fields`.
   - The test fails if Tier 3 receives government grant values in `sql_results`.

3. Load harness:
   - File: `tests/load/locustfile.py`
   - Added optional `LOAD_TEST_*_TOKEN` support to bypass per-user login bottlenecks.
   - Added the canonical `question` field beside `query` in `/query` request bodies.
   - Replaced invalid `resp.duration` timing with local elapsed timing.

4. Load harness contract:
   - File: `tests/config/test_locustfile_contract.py`
   - Added assertions for preissued token support, canonical query payload, and valid timing code.

## Evidence Files

Health:
   - `local_api_health.json`
   - PostgreSQL-backed health returned healthy with `researchers=50000` and `publications=50000`.

Tier response isolation:
   - `fixed_uncached_tier1_query_response.json`
   - `fixed_uncached_tier2_query_response.json`
   - `fixed_uncached_tier3_query_response.json`
   - Tier 1 and Tier 2 retained `total_grant`.
   - Tier 3 retained `gov_organisation_name` and stripped `total_grant`.
   - Tier 3 response warnings include `pii_strip:tier3:government_grant_value`.

Direct security checks:
   - `local_pii_block_response.json`
   - `local_injection_block_response.json`
   - PII probe returned HTTP 400 with `Security violation: DLP_VIOLATION`.
   - Prompt-injection probe returned HTTP 400 with `Security violation: PROMPT_INJECTION`.

Red-team replay:
   - `red_team_live_results.md`
   - 210 HTTP calls were replayed against the live local API.
   - No `ALLOWED-DANGEROUS` responses were detected.
   - Baseline RT-01 through RT-30 resolved to `BLOCKED` or `DOWNGRADED`.

Database plan:
   - `explain_analyze_top_funding.log`
   - The top-funding aggregate ran in 39.368 ms on 50,000 rows.
   - PostgreSQL used a sequential scan on `innovation_grant_from_govt`.

Load:
   - `load_test_1_token_query_smoke_fixed_stats.csv`
   - 1-user smoke: 10 completed `/query` requests, 0 failures, P99 37000 ms.
   - `load_test_200_token_fixed_stats.csv`
   - 200-user local run: 113 completed `/query` attempts, 113 failures, P99 7900 ms.

## Current Verdict

Closed locally:
   - Tier 3 no longer receives government grant amount fields through `/query`.
   - The load harness no longer depends on 200 concurrent logins to reach query traffic.
   - The load harness now records query timings instead of crashing on a missing Locust attribute.

Still blocking:
   - C4 SLO is not met.
   - 200-user local load produced query traffic but failed under pressure.
   - Single-user query traffic has a long tail up to 37.5 seconds due the live LLM synthesis path.
   - The verifier log still warns that SQLite is used for citation validation while PostgreSQL is active.

The system is materially safer after the Tier 3 response-boundary fix, but it is not ready for a high-stakes live showing until the query path has deterministic fast responses or a scaled async worker model.
