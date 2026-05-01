# C4 Declared Prewarm No-Profile Diagnostic

Generated: 2026-05-01T23:22:13.076890+00:00

## Setup

- API: host uvicorn, 4 workers, quota disabled, Redis disabled, no query-stage profiler, no request-envelope profiler.
- Prewarm: 12 rounds of the declared C4 workload query set across researcher, government, and adversarial personas.
- Prewarm requests: 312 total, 0 failures, statuses {'200': 312}.
- Locust: scorecard C4 runner, 1000 users, 100 spawn rate, 60 seconds.

## Result

- C4 status: FAIL
- Aggregate P99: 2100.0 ms (threshold 500.0 ms)
- Failure rate: 0.0
- Total samples: 45559
- 1000 concurrent detected: True

## Endpoint Metrics

- `/query::adversarial`: requests=2795, failures=0, p99=2400.0 ms
- `/query::government`: requests=10854, failures=0, p99=2100.0 ms
- `/query::researcher`: requests=31211, failures=0, p99=2100.0 ms

## Interpretation

Declared prewarm removed cold-key setup from the test, but client-observed P99 still missed the 500ms C4 gate. This means the remaining issue is not only cold cache creation. The prior combined envelope profile showed route-handler cache-hit work at low millisecond scale while the full ASGI request envelope was much larger; the likely remaining boundary is request lifecycle, queueing, transport scheduling, and worker concurrency under 1000 users.

No C4 release pass is claimed from this diagnostic.
