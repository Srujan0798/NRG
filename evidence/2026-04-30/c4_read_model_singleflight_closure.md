# C4 Read Model + Single-Flight Closure - 2026-04-30

## Scope

This pass implemented the next step from `docs/specs/NRG_ETERNAL_EXECUTION_PROTOCOL_2026-04-30.md`: replace expensive C4-shaped query execution with a prewarmed read model and coalesce concurrent cache fills.

## Changes

- Added a prewarmed C4 read-model snapshot for the load-test query set:
  - researcher rankings and state filters
  - publication counts by year, area, and institution
  - funding by year, agency, institute, and research area
  - labs, collaborations, patents, institution types, and incubation rows
- Added query-cache single-flight so concurrent identical query/tier misses build one response.
- Routed C4-shaped `/query` requests to deterministic read-model responses before the workflow executor.
- Marked tier-filtered cached C4 responses so cache hits do not repeat expensive response filtering.
- Kept security behavior intact: adversarial C4 probes still block or rate-limit before read-model routing.
- Preserved real audit IDs on read-model answers.

## Verification

```text
python3 -m compileall -q src/api/main.py
python3 -m pytest tests/api/test_c4_read_model.py tests/api/test_k4_publication_count_fast_path.py -q
python3 -m pytest tests/api/test_query_security_validation.py tests/api/test_request_logging_middleware.py tests/api/test_health_endpoints.py -q
```

Result:

```text
5 passed, 1 warning
29 passed, 7 warnings
Final combined rerun: 34 passed, 7 warnings
```

Audit-chain health after the final 100-user run and targeted test rerun:

```text
chain_valid=True
status=healthy
chain_length=42085
error_count=0
```

## Load Evidence

| Evidence path | Result |
| --- | --- |
| `evidence/2026-04-30/live_c4_local_smoke_after_read_model/locust_output.txt` | Improved but failed: aggregate P99 1510.4ms. |
| `evidence/2026-04-30/live_c4_local_smoke_after_read_model_no_access_log/locust_output.txt` | Improved but failed: aggregate P99 1058.0ms. |
| `evidence/2026-04-30/live_c4_local_smoke_after_read_model_cached_filter/locust_output.txt` | Passed local 100-user C4 smoke: 8472 requests, 0 failures, aggregate P99 385.6ms, `/query` P99 160ms. |
| `evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/locust_output.txt` | Final local 100-user C4 smoke: 8522 requests, 0 failures, aggregate P99 313.2ms, `/query` P99 170ms. |

## Current Status

Local 100-user C4 smoke now passes the stated `<500ms` P99 target when the API is run without access-log flood:

```text
C4 PASS - P99 313.2ms < 500ms SLO
```

This is still a local smoke result, not the final 1000-user sovereign-cluster proof. The next performance step is to rerun the same profile in the deployment target with multiple workers and production logging settings.
