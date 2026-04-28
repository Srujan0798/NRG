# Cold Query Optimization Pattern

Date captured: 2026-04-28

## Problem

Cold analytical queries can cross the user-facing latency budget when they force
embedding model load, schema retrieval, Text-to-SQL generation, result
synthesis, and cache population in one request.

## Pattern

1. Emit phase events within 500 ms of request acceptance.
2. Cache repeated query plans and query responses by question hash.
3. Keep `QUERY_RESULT_CACHE_TTL_SECONDS` at 300 seconds or higher during
   acceptance windows.
4. Put LLM synthesis behind a strict timeout. Fall back to local or rule-based
   synthesis when the timeout fires.
5. Preload embedding models before accepting load-test or production traffic.
6. Treat worker death during model load as a capacity bug, not a transient test
   artifact.

## Verification

- Unit/API tests must prove cache TTL and synthesis timeout behavior.
- Frontend build must prove phase-progress components compile.
- Load evidence must separate stable warmed-cache results from corrected
  >50-QPS pacing results.
