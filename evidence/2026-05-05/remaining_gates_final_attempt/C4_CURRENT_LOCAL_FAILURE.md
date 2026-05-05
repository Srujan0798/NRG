# C4 Current Local Status

Date: 2026-05-05
Status: PARTIAL local / EXTERNAL BLOCKED

## Latest Result

The latest local Quality Bar scorecard is `5/6`.

- Scorecard source: `scripts/quality_bar_scorecard.json`
- Evidence copy: `evidence/2026-05-05/remaining_gates_final_attempt/quality_bar_scorecard_current_5_6_partial.json`
- C4 mode: `local_regression`
- C4 local result: 9 passed / 9 total
- Live Locust executed: false
- Reason live Locust did not run locally: port 8000 did not return an NRG API `/health` response.

## Fix Applied

The previous scorecard only checked whether TCP port 8000 was open. On this
machine port 8000 was held by an `ssh` listener, not the NRG API, so the
scorecard ran Locust against the wrong service and produced HTTP 0 failures.

`scripts/quality_bar_scorecard.py` now requires a real NRG `/health` JSON
response before running live Locust. If no live API is available, local runs use
the strict C4 SLO regression suite and C4 is marked PARTIAL, not PASS.
Deployment CI sets `NRG_C4_REQUIRE_LIVE=1` so release gates still require live
API C4 and cannot silently fall back.

## Closure Boundary

Local C4 regression passes, but C4 remains partial. Cluster/live 1000-user proof
is still blocked until a usable `KUBECONFIG` or deployed NRG API target is
available.
