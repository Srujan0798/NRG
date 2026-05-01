# C4 Hot-Path Follow-Up: ASGI Middleware and Auth Cache

Date: 2026-05-02

This is not a C4 pass certificate. It records the next performance isolation pass after the duplicate `/query` prompt-sanitiser work was removed.

## Code Changes Validated

- `/query` is skipped by `PromptSanitiserMiddleware`; the route-level validator owns the full blocked answer envelope and audit ID.
- `RequestLoggingMiddleware`, `SecurityHeadersMiddleware`, `PromptSanitiserMiddleware`, and `AuthContextMiddleware` now avoid `BaseHTTPMiddleware` on the hot path and use direct ASGI call wrappers.
- `AuthContextMiddleware` has a short verified-token cache keyed by token and client IP. The default TTL is 5 seconds and can be disabled with `NRG_AUTH_CONTEXT_CACHE_TTL_SECONDS=0`.
- App-level gzip can be disabled for edge-compression deployments with `NRG_APP_GZIP_MIN_SIZE=0`.
- FastAPI uses `ORJSONResponse` as the default response class for JSON-heavy paths.

## Measured Results

| Evidence | Topology | Result |
| --- | --- | --- |
| `113_c4_prewarm_after_query_middleware_skip.json` | 4 workers, duplicate `/query` middleware removed | 312/312 prewarm passed; median 3.135 ms; max 126.16 ms. |
| `115_quality_bar_scorecard_60s_after_query_middleware_skip.json` | 4 workers | C4 failed: 35,428 samples, 0 failures, aggregate P99 2700 ms. |
| `119_c4_prewarm_asgi_middleware.json` | pure ASGI middleware, 4 workers | 312/312 prewarm passed; median 2.865 ms; max 142.44 ms. |
| `133_quality_bar_scorecard_60s_asgi_middleware_4workers.json` | pure ASGI middleware, 4 workers | C4 failed but improved: 47,233 samples, 0 failures, aggregate P99 970 ms; researcher P99 940 ms; government P99 950 ms; adversarial P99 1300 ms. |
| `127_quality_bar_scorecard_60s_asgi_middleware_8workers.json` | pure ASGI middleware, 8 workers, backlog 4096 | Rejected as improvement: 44,440 samples, 22.09% failures, aggregate P99 7800 ms. |
| `139_quality_bar_scorecard_60s_asgi_authcache_4workers.json` | pure ASGI middleware, 4 workers, auth cache TTL 30s | C4 failed: 45,249 samples, 0 failures, aggregate P99 1200 ms. Useful as auth-cache safety evidence, not a C4 improvement. |

## Current C4 Status

C4 remains **FAIL**. The best stable local result in this pass is:

- 1000 users
- 47,233 samples
- 0 failures
- aggregate P99 970 ms
- required P99 < 500 ms

The hot path is materially cleaner, but the release gate is still not closed. Do not claim `6/6` quality-bar compliance from this evidence.

## Next Work

The remaining gap is local request scheduling/queueing under the 1000-user workload. Next options should be tested one at a time:

1. Run the same strict C4 workload on the intended sovereign deployment topology, not local same-machine client and server.
2. Add a production-grade external cache/shared read model so all workers share warmed answers instead of per-process cache islands.
3. Evaluate an async audit/event writer design that preserves event IDs and HMAC ordering without request-path file-lock serialization.
4. Keep the pure-ASGI middleware change because it reduced the best stable P99 from the previous 2100-2700 ms range to 970 ms with zero failures.
