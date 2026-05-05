# C4 P99 Optimization — Blockers and Gaps

## 🚫 BLOCKED: Architectural Changes Required

The P99 target of < 500ms at 1000 concurrent users **cannot be achieved with configuration changes alone**. The root causes are architectural:

### Primary Bottleneck: LLM Mesh Latency

Every query that reaches `run_workflow` must make external LLM API calls through the sovereign mesh:
1. MiniMax API (primary, ~2-5s latency)
2. NVIDIA API (fallback, ~3-8s latency)
3. Local LLM fallback (~1-3s latency)

At 1000 concurrent users, even with 10s timeout, these calls queue and create massive P99 tail latency.

### Secondary Bottleneck: Python GIL + ThreadPoolExecutor

The LLM calls are made via `ThreadPoolExecutor` with limited workers:
- `_llm_timeout_executor` in `skill.py`: max_workers=4
- `_LLM_TIMEOUT_EXECUTOR` in `synthesizer.py`: max_workers=4  
- `blocking_executor` in `main.py`: max_workers=128

Even with 128 blocking workers, the Python GIL prevents true parallelism for I/O-bound LLM calls.

### Tertiary Bottleneck: In-Memory SQLite Read Model

The `_c4_read_model_snapshot()` loads 5000 rows from SQLite on first call. With 4 uvicorn workers, concurrent requests can cause SQLite contention, especially under memory pressure.

## Changes That Would Help (Require Code Changes)

### 1. Async LLM Clients
Replace `ThreadPoolExecutor` with true `async/await` LLM clients that don't block threads waiting for I/O.

### 2. Aggressive Response Caching  
Increase `QUERY_RESULT_CACHE_TTL_SECONDS` from 300 to 3600 and add LRU eviction to reduce LLM call volume by 80%+ for repeated queries.

### 3. Pre-Warm C4 Read Model
Eagerly load `_c4_read_model_snapshot()` at startup rather than on first request, using `_prewarm_c4_read_model()` pattern already in code.

### 4. Request Coalescing
Deduplicate concurrent identical queries to a single LLM call using singleflight pattern.

### 5. Circuit Breaker Tuning
Tighten circuit breaker thresholds to fail immediately rather than retry exhausted providers.

## What Was Tried (And Didn't Work)

| Change | Effect on P99 |
|--------|---------------|
| LLM timeout 60s → 10s | Slightly improved (7900 → 6300ms) but failure rate increased |
| DATABASE_POOL 20/40 → 30/80 | No significant impact |
| NRG_API_BLOCKING_WORKERS 64 → 128 | **WORSENED** (7900 → 9800ms) |

## Known Gaps

1. **No Redis caching for query results**: `_api_cache` is in-memory only, no shared cache across workers
2. **No query result materialization**: Complex queries recompute every time
3. **No connection pooling metrics**: PgBouncer stats not exposed for monitoring
4. **LLM mesh health not real-time**: Circuit breaker state not exposed in health endpoint

## Evidence Files

- `00_summary.md` - Complete analysis and conclusions
- `01_baseline.log` - Baseline C4 run (P99=7900ms)
- `03_after_fix.log` - After all config fixes (P99=9800ms)
- `04_config_changes.diff` - All .env changes made
- `05_blockers.md` - This file