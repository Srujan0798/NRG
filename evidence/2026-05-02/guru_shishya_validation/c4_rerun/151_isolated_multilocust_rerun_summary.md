# Isolated Multi-Process C4 Rerun Summary

Date: 2026-05-02

## Purpose

Record the isolated `uvloop`/`httptools` rerun after the multi-process Locust runner fix. This evidence is useful because it proves the runner can now complete with four Locust worker processes and zero HTTP failures, but it does not close C4.

## Inputs

- Prewarm evidence: `147_c4_prewarm_4workers_uvloop_httptools_isolated_rerun.json`
- Scorecard evidence: `149_quality_bar_scorecard_60s_4workers_uvloop_httptools_isolated_rerun.json`
- Locust HTML report: `150_locust_report_60s_4workers_uvloop_httptools_isolated_rerun.html`

## Result

The prewarm completed 312/312 requests successfully in 1.563 seconds. All prewarm responses returned HTTP 200, all expected audit event IDs were present, and 60 adversarial requests were blocked as expected.

The 60-second C4 scorecard still reports `5/6`, with C4 failed:

- requested users: 1000
- Locust worker processes: 4
- Locust exit code: 0
- total samples: 72,084
- failure rate: 0.0%
- aggregate P99: 1100 ms
- C4 P99 target: 500 ms

Per-workload P99:

- `/query::researcher`: 740 ms across 53,253 requests
- `/query::government`: 770 ms across 15,360 requests
- `/query::adversarial`: 2600 ms across 2,751 requests

## Interpretation

This rerun is better as evidence quality than the previous failed local multi-process attempt because it completed cleanly with zero failures and far more samples. It is not better than the best stable local P99 result: `133_quality_bar_scorecard_60s_asgi_middleware_4workers.json` remains the best aggregate C4 diagnostic so far at 970 ms with zero failures.

The remaining blocker is the latency tail under 1000-user client pressure, especially the adversarial workload. The next engineering step should profile and reduce the blocked/adversarial answer path, including audit-envelope cost and any security classification work that still occurs before returning the bounded response.

## Status

Do not claim C4 pass from this run. It is a clean failed load run that narrows the next bottleneck.
