# K-2 Backend Profile - 2026-04-29

## Inputs

- Load evidence: `evidence/2026-04-28/locust_100u_v2.json`
- Summary: `evidence/2026-04-28/K2_locust_summary.txt`
- Code paths reviewed:
  - `src/api/main.py`
  - `src/auth/jwt_handler.py`
  - `src/auth/refresh_store.py`
  - `src/services/consent.py`
  - `src/security/rate_limiter.py`
  - `tests/load/locustfile_c4.py`

## Observed Load Result

| Metric | Value |
|---|---:|
| Failure rate | 0.00% |
| Aggregated P95 | 31,000 ms |
| Aggregated P99 | 46,000 ms |
| `/query` P95 | 31,000 ms |
| `/query` P99 | 38,000 ms |
| `/auth/login` P99 | 46,000 ms |

## Diagnosis

The API is functionally stable under the 100-user run, but queues heavily. The fastest `/query` sample was 45.4 ms, while P99 was 38 s. That spread means the core fast path can be quick, but request admission/auth/session work saturates the local stack under concurrency.

Primary hot-path issue found and fixed in this pass:

- `ConsentService()` was constructed in login, query, streaming query, health, and DPDP endpoints.
- `ConsentService.__init__()` calls `_init_table()`.
- `_init_table()` opens SQLite and runs `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `ALTER TABLE`, `commit`, and `close`.
- Under load, that repeated DDL/connection setup runs in request handlers and adds serialized SQLite work.

Change made:

- Added `get_consent_service()` in `src/services/consent.py`.
- Updated active API handlers in `src/api/main.py` and route modules to reuse the cached service for the resolved database path.

Additional request-path latency fixes from the K-4 pass:

- Redis availability probing no longer pings localhost unless Redis caching is explicitly configured by `REDIS_URL`, `ENABLE_REDIS_CACHE=true`, or explicit Redis host settings.
- Audit append no longer recounts the entire chain on each event; it reads the last chain line directly and increments in-memory event count under the audit file lock.
- Training-pair capture no longer initializes the collector schema before returning the query response; initialization now happens in the background worker.

Remaining likely bottlenecks:

1. Refresh token storage still writes to SQLite on every login through `RefreshTokenStore.store()`.
2. The C4 Locust workload logs in every virtual user during ramp-up, and login P99 is as high as the aggregate P99.
3. Query requests still perform consent reads and prompt-sanitiser checks per request.
4. The previous load run included port contention on 8000 and used 8010 for isolation.

## Verification Run After Patch

- `tests/services/test_consent.py tests/services/test_consent_extended.py`: 17 passed.
- `tests/api/test_health_endpoints.py`: 16 passed.
- `tests/auth/test_jwt_handler.py`: 10 passed after aligning the issuer assertion with the configured platform issuer.
- `tests/api/test_auth_api.py tests/auth/test_jwt_handler.py` with default marker filters disabled: 18 passed.
- `tests/performance/test_query_latency_hot_path.py -m "slow or not slow"`: 7 passed.

## Next Required K-2 Action

Before retrying 100-user Locust:

1. Move refresh-token persistence off SQLite for load runs or use the production PostgreSQL/Redis-backed session store.
2. Separate login ramp-up from steady-state `/query` latency in the load report.
3. Re-run with isolated API port, 4 workers, warmed cache, Redis available, and no concurrent local agents restarting the API.
4. Record both auth-inclusive and query-only P95/P99.
