# Query Service Extraction Evidence

Date: 2026-05-03

## Scope

Moved the live query and streaming answer-engine body out of
`src/api/main.py` into `src/api/query_service.py`.

`src/api/main.py` now keeps:

- FastAPI app setup, middleware, lifecycle, dependency wiring, and router
  registration.
- Thin compatibility wrappers for `_build_stream_answer_payload`,
  `_query_stream_response`, and `_query_with_langgraph_impl`.

`src/api/query_service.py` now owns:

- `/query` execution.
- `/api/query/stream` execution.
- Query cache, audit append, tier filtering, AI post-filter synthesis,
  prompt-safety handling, consent checks, and async boundaries for blocking
  answer paths through injected dependencies.

## Regression Added

- `tests/api/test_query_service_extraction.py`
  - Verifies `QueryAnswerService` and `QueryServiceDependencies` exist.
  - Verifies the compatibility wrappers in `src/api/main.py` stay thin.

## Checks Run

```text
python3 -m py_compile src/api/main.py src/api/query_service.py src/api/routes/query.py \
  tests/api/test_query_async_boundaries.py tests/api/test_query_service_extraction.py
PASS

pytest tests/api/test_query_service_extraction.py tests/api/test_query_async_boundaries.py -q
4 passed in 0.50s

pytest tests/api/test_critical_path_stream.py tests/api/test_langgraph_api.py \
  tests/api/test_query_async_boundaries.py tests/api/test_query_service_extraction.py -q
38 passed, 7 warnings in 10.07s

pytest tests/api/test_query_helper_drift.py tests/api/test_query_security_validation.py \
  tests/api/test_tier_response_filtering.py tests/api/test_audit_event_endpoint.py -q
16 passed, 13 warnings in 4.62s

git diff --check
PASS

python3 scripts/verify_corpus_sync.py
PASS

bash scripts/forbidden_vocab_check.sh
PASS

.venv/bin/ruff check src/api/main.py src/api/query_service.py \
  tests/api/test_query_async_boundaries.py tests/api/test_query_service_extraction.py
PASS
```

## Notes

- The service dependencies use call-through lambdas for legacy monkeypatch
  compatibility in existing API tests.
- The router still exposes the same public `/query`, `/api/query/stream` GET,
  and `/api/query/stream` POST surfaces.
- This is local structural proof only. Deployed and cluster gates remain
  blocked until target URLs and production context are supplied.
