# Isolated 8-Worker Prewarm Rejection

Date: 2026-05-02

## Evidence

`152_c4_prewarm_8workers_uvloop_httptools_isolated_rerun.json`

## Result

The 8-worker isolated prewarm is rejected as a candidate topology:

- total prewarm requests: 624
- HTTP 200 responses: 159
- connection/reset failures: 465
- missing audit event IDs: 465
- duration: 21.603 seconds
- slowest successful requests exceeded 5 seconds

Representative failure:

`ConnectionResetError(54, 'Connection reset by peer')`

## Interpretation

This confirms the earlier 8-worker finding: increasing local API worker count does not close C4 on this machine. It destabilizes the workload before the scorecard can provide useful pass/fail evidence.

Keep the 4-worker evidence as the primary local diagnostic baseline. Do not spend more time on the 8-worker local topology unless the runtime environment changes.
