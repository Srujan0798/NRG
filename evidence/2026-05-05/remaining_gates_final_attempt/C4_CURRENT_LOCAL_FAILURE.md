# C4 Current Local Status

Date: 2026-05-05
Status: LOCAL REGRESSION PASS / LIVE C4 FAIL / EXTERNAL BLOCKED

## Latest Result

The latest local Quality Bar scorecard is `5/6`.

- Scorecard source: `scripts/quality_bar_scorecard.json`
- Evidence copy: `evidence/2026-05-05/remaining_gates_final_attempt/quality_bar_scorecard_current_5_6_partial.json`
- Latest scorecard run log: `evidence/2026-05-05/remaining_gates_final_attempt/quality_bar_scorecard_after_unhealthy_health_fix.log`
- Latest live Locust report summary: `evidence/2026-05-06/runtime_recovery/live_c4_locust_failure_summary.md`
- C4 mode: `local_regression`
- C4 local result: 9 passed / 9 total
- Live Locust executed: true on the available forwarded target
- Live Locust result: FAIL, P99 4900 ms, 0.1717% failures
- Local scorecard mode remains `local_regression` unless a healthy API target is
  supplied through `NRG_C4_API_BASE_URL` with `NRG_C4_REQUIRE_LIVE=1`.

## Fix Applied

The previous scorecard accepted non-ready port-8000 targets. During this
session port 8000 was held by an `ssh` listener forwarding an unhealthy NRG API,
so the scorecard ran Locust against a non-ready service and produced HTTP 0
failures.

`scripts/quality_bar_scorecard.py` now requires a healthy NRG `/health` JSON
response before running live Locust. If no healthy live API is available, local
runs use the strict C4 SLO regression suite and C4 is marked PARTIAL, not PASS.
Deployment CI sets `NRG_C4_REQUIRE_LIVE=1` so release gates still require live
API C4 and cannot silently fall back.

## Closure Boundary

Local C4 regression passes, but available live C4 fails. Cluster/live closure is
still blocked until a performant NRG API target or usable `KUBECONFIG` is
available.
