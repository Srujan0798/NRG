# Live API Test Orchestration

## Context

The broad Python suite mixed hermetic tests with live API tests. Running
`pytest tests/` without a reachable API caused false failures in tier-isolation
and red-team files. Running live tests immediately after uvicorn readiness also
exposed cold-path embedding model load that could exceed the old 15-second
request timeout.

## Constraint

Live API tests must be explicit, serial, and evidence-bound. Default local test
runs may skip them when no API is reachable, but required-live mode must hard
fail if the API cannot be started or queried. Readiness should use `/health/db`,
not root health, because optional audit/vector dependencies can be degraded
without proving the API database path is unavailable.

## Enforcement

- Keep live files registered in `tests/conftest.py` under
  `LIVE_API_TEST_PREFIXES`.
- Use `scripts/run_test_suite.sh --live-api` for full local evidence.
- Use `/health/db` for managed uvicorn readiness.
- Isolate non-live xdist audit writes under the evidence directory, with one
  audit chain per worker, and keep the live uvicorn audit chain separate from
  the active `.audit` chain.
- Run live API files with `NRG_REQUIRE_LIVE_API=1` so missing API becomes a
  failure, not a skip.
- Allow a longer configurable live red-team timeout through
  `NRG_RED_TEAM_TIMEOUT`; cold allowed queries can load embedding models.
- After broad runs, verify the active audit chain and repair with
  `scripts/audit_rebuild.py --rebuild --preserve-lineage` only when verification
  proves per-user binding drift.
