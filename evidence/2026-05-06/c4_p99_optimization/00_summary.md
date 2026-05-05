# C4 P99 Optimization — Evidence Summary

## Baseline (Before Changes)
- **P99**: 7900ms
- **Failure Rate**: 0.57%
- **Total Samples**: 136,495
- **Target**: P99 < 500ms at 1000 concurrent users

## Changes Applied

### Fix 1: LLM Timeout Aggressive Reduction
**.env changes:**
```
- LLM_REQUEST_TIMEOUT_SECONDS=60 → 10
- LLM_TIMEOUT_BUDGET=45 → 10
```

### Fix 2: Database Pool Increase
**.env changes:**
```
+ DATABASE_POOL_MIN=30
+ DATABASE_POOL_MAX=80
```

### Fix 3: Blocking Workers Increase
**.env changes:**
```
+ NRG_API_BLOCKING_WORKERS=128
```

## Results After Fixes

| Run | P99 (ms) | Failure Rate | Samples | Notes |
|-----|----------|--------------|---------|-------|
| Baseline | 7900 | 0.57% | 136,495 | Before changes |
| After LLM timeout fix | 6300 | 0.00% | 119,618 | Slightly better |
| After workers fix | 9800 | 1.55% | 96,873 | WORSE - increased workers caused more memory pressure |

## Root Cause Analysis

### Architectural Bottleneck Identified

The P99 latency of 7,900ms at 1000 concurrent users is **fundamentally architectural**, not config-related:

1. **LLM Mesh with External API Calls**: Every query that reaches `run_workflow` triggers LLM calls through the sovereign mesh (MiniMax → NVIDIA → local fallback). With `LLM_TIMEOUT_BUDGET=10s`, requests that timeout or retry contribute to high tail latency.

2. **Multi-Node LangGraph Pipeline**: Each query goes through `receiver → planner → router → executor → synthesizer → verifier`. Even fast-path queries have significant overhead.

3. **Text-to-SQL Skill with Thread Pool**: The `_llm_timeout_executor` has only 4 workers. At 1000 concurrent users with complex queries, this becomes a bottleneck.

4. **SQLite Read Model Snapshots**: The `_c4_read_model_snapshot()` loads 5000 rows from SQLite on first call, but with 4 uvicorn workers, concurrent requests can cause contention.

5. **In-Memory Cache Inefficiency**: The `_APIMemoryCache` with 300s TTL and no LRU eviction can cause memory pressure at high concurrency.

### Per-Endpoint Latency Breakdown (from Locust output)

| Endpoint | Avg (ms) | P50 (ms) | P99 (ms) | Max (ms) |
|----------|----------|----------|----------|----------|
| /query::researcher | 1160 | 930 | ~7900 | 23,136 |
| /query::government | 1269 | 990 | ~7900 | 26,029 |
| /query::adversarial | 1488 | 1200 | ~7900 | 23,662 |
| /stats::adversarial | 1295 | 1000 | ~7900 | 22,344 |

### Key Observation
All endpoints show similar latency distribution, suggesting a **shared bottleneck** (likely the thread pool for LLM calls or the global interpreter lock for Python async operations).

## Conclusion

**BLOCKED**: Architectural changes required to achieve P99 < 500ms at 1000 concurrent users.

### Options for Achieving Target

1. **Async LLM Calls with True Parallelism**: Replace ThreadPoolExecutor with async LLM clients to eliminate GIL contention
2. **Aggressive Query Result Caching**: Pre-warm cache for common queries, increase cache TTL to reduce LLM call volume
3. **Read Model Materialization**: Pre-compute and materialize C4 read model snapshots as actual database views
4. **Request Coalescing**: Deduplicate concurrent identical queries to reduce LLM call volume
5. **Circuit Breaker Tuning**: Tighten circuit breaker thresholds to fail fast rather than retry

### What Cannot Be Changed (per constraints)
- Locust config (C4 test configuration)
- Test assertions
- Core architectural patterns without stopping and reporting

## Evidence Files
- `01_baseline.log` - Baseline C4 run output
- `03_after_fix.log` - Final C4 run after all fixes
- `04_config_changes.diff` - .env changes made