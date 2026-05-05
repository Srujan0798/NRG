# Live C4 Local API Failure Summary

Generated: 2026-05-06 01:34 IST

Source: `scripts/quality_bar_scorecard.json`

## Result

Status: FAIL

The local API was started on `http://127.0.0.1:8001` with quota/rate limiting
disabled for load testing, quiet access logs, and a healthy `/health` response.
The scorecard was run with `NRG_C4_REQUIRE_LIVE=1`, `NRG_C4_API_BASE_URL` set
to the local target, 1000 users, 4 Locust processes, and the maintained
5-minute C4 workload.

| Metric | Value |
|---|---:|
| Requests | 338548 |
| Failures | 0 |
| Failure rate | 0.0000% |
| P50 | 45 ms |
| P90 | 610 ms |
| P95 | 800 ms |
| P99 | 1200 ms |
| Max | 2200 ms |

## Endpoint Metrics

| Endpoint | Requests | Failures | Failure rate | P99 |
|---|---:|---:|---:|---:|
| `/query::researcher` | 243300 | 0 | 0.0000% | 1100 ms |
| `/query::government` | 72948 | 0 | 0.0000% | 1200 ms |
| `/query::adversarial` | 17754 | 0 | 0.0000% | 1500 ms |

## Interpretation

C4 remains failed for live-load evidence. The rate-limit failure was resolved
and access-log terminal I/O was removed from the local run, but the local laptop
runtime still misses the P99 <500 ms gate at the maintained 1000-user workload.

An 8-worker, 1-minute diagnostic still reported P99 1100 ms with 0 failures, so
worker count alone did not close the gap. A temporary ORJSON response-path
experiment made the diagnostic worse and was reverted.

The temporary local Qdrant `nrg_research` collection created only for C4 health
probing was deleted after the run because it contained dummy vectors.
