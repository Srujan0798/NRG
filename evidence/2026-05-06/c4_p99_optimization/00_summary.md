# C4 P99 Optimization - Summary

**Date:** 2026-05-06
**Assignment:** `shishya_c4_p99_optimization.md`
**HEAD at evidence refresh:** `0f6f3d7d`

## Final Status

**BLOCKED.** The local live C4 gate was run end-to-end after API-side cache changes, but P99 is still above the `<500ms` target and the assignment stop rule was reached after 3 optimization attempts.

No completion claim is made for C4.

## Code Changes Kept

1. Increased `QUERY_RESULT_CACHE_TTL_SECONDS` default from `300` to `3600`.
2. Added user-scoped, singleflight-backed caching for repeated blocked prompt envelopes so adversarial C4 traffic does not append duplicate anomaly audit events for identical blocked prompts from the same authenticated user.
3. Preserved the existing `deps.workflow` test seam while lazily constructing the orchestration workflow.
4. Lazily constructs the main API workflow so health/startup paths do not pay orchestration import cost before a workflow-backed query is actually needed.
5. Added bounded `/health` checks for vector drift and data quality, and raised local C4 health probe timeouts where the prior defaults were too aggressive for this stack.
6. Added regression coverage for repeated blocked prompt cache behavior, authenticated-user cache isolation, and vector drift health timeout behavior.

Temporary dev-only fast-lane code was tested during attempt 3 and then removed because it did not pass C4 and was not an acceptable production fix.

## C4 Runs

| Run | Evidence | Result | Mean | P95 | P99 | Failure Rate | Samples | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Assignment baseline | `runtime_recovery/live_c4_local_8001_failure_summary.md` | FAIL | not recorded here | not recorded here | 1200ms | 0% | 338,548 | Prior failure cited by assignment |
| Reopened current scorecard | `06_reopen_current_scorecard.log` | FAIL | JSON overwritten by later run | JSON overwritten by later run | FAIL | FAIL | FAIL | Fresh gate confirmation before patch |
| Attempt 1: TTL + blocked cache | `03_after_fix.log` | FAIL | 3593ms | 8400ms | 22000ms | 2.04% | 67,086 | C5 passed, C4 failed |
| Attempt 2: Locust process tuning | `03_after_fix_attempt2_reopen_processes4.log` | FAIL | 4840ms | 17000ms | 55000ms | 5.27% | 43,995 | Multiprocess load worsened local stack |
| Attempt 3: temporary fast-lane experiment | `03_after_fix_attempt3_reopen_fast_lane.log` | FAIL | 1481ms | 3700ms | 21000ms | 1.51% | 118,788 | Code reverted after failed attempt |

Latest `scripts/quality_bar_scorecard.json` records `4/6` overall with `C4=FAIL`, `C5=FAIL`, `C4 p99_ms=21000.0`, `failure_rate=0.015110953968414317`, and `total_samples=118788`.

## Bottleneck Identified

The retained code change reduced repeated blocked-prompt audit work, but the C4 tail still comes from local runtime overload under 1000 concurrent users. The profile evidence shows API handler stage timings are far lower than Locust tail latency for many requests, while Locust reports HTTP 0 failures and very high end-to-end tails. This points to queueing and local process pressure around the live FastAPI/Locust/Docker setup, not a single slow SQL statement.

Concrete supporting evidence:

- `02_slow_endpoints.log` / `02_stage_profile.jsonl`: API stage timing evidence.
- Docker API logs during load showed audit lock timeouts during adversarial traffic.
- Full scorecard attempts still produced HTTP 0 failures despite fast single-query probes outside load.

## Verification

Targeted regression command after reverting the temporary fast-lane experiment and preserving lazy workflow compatibility:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -o addopts="" tests/api/test_query_security_validation.py::test_repeated_blocked_query_uses_cached_envelope_without_reauditing tests/api/test_query_security_validation.py::test_blocked_query_cache_is_scoped_to_authenticated_user tests/api/test_health_endpoints.py::test_query_result_cache_ttl_is_long_enough_for_load_review -q --tb=short
```

Result: `3 passed`.

Health timeout regression command:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -o addopts="" tests/api/test_health_endpoints.py::test_root_health_times_out_slow_vector_drift_check tests/api/test_health_endpoints.py::test_root_health_times_out_slow_qdrant_check tests/api/test_health_endpoints.py::test_query_result_cache_ttl_is_long_enough_for_load_review -q --tb=short
```

Result: `3 passed`.

## Evidence

- `01_baseline.log`
- `02_slow_endpoints.log`
- `02_stage_profile.jsonl`
- `03_after_fix.log`
- `03_after_fix_attempt2_reopen_processes4.log`
- `03_after_fix_attempt3_reopen_fast_lane.log`
- `04_config_changes.diff`
- `05_blockers.md`
- `09_lazy_workflow_blocked_cache_tests.log`
- `10_health_timeout_tests.log`
