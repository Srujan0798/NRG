# Live C4 Forwarded-Target Failure Summary

Generated: 2026-05-05T19:29:34Z source report start time

Source report: `evidence/2026-05-06/runtime_recovery/live_c4_locust_report.html`

## Result

Status: FAIL

The available forwarded target at `http://127.0.0.1:8000` completed a
1000-user Locust run, but it does not meet C4.

| Metric | Value |
|---|---:|
| Requests | 150226 |
| Failures | 258 |
| Failure rate | 0.1717% |
| P95 | 2900 ms |
| P99 | 4900 ms |
| Average response time | 1244.32 ms |

## Interpretation

C4 remains failed for live-load evidence. The local TestClient SLO regression
passes, but the available live target does not satisfy P99 <500 ms or zero
failure requirements.

Superseding local API evidence was collected later in this session at
`live_c4_local_8001_failure_summary.md`. That later run removed rate-limit
failures, but still failed P99 at 1200 ms.
