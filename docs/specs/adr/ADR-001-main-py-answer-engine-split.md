# ADR-001: Main.py Answer-Engine Split

Date: 2026-05-05

## Status

Accepted. Canonical implementation ADR: `docs/adr/ADR-007-main-py-answer-engine-split.md`.

## Context

`src/api/main.py` previously carried app construction, middleware setup, router
registration, dependencies, and live query route behavior in one module. That
made route wiring and answer-engine behavior easy to change together and made
query-helper drift harder to review.

## Decision

`src/api/main.py` remains the FastAPI composition root:

- app construction;
- lifecycle and middleware wiring;
- dependency binding;
- router registration;
- compatibility wrappers where existing tests or callers require them.

Live answer behavior belongs in `src/api/query_service.py` through
`QueryAnswerService`.

## Consequences

- New answer-engine behavior should be implemented in `QueryAnswerService` or a
  dependency injected into that service.
- `main.py` should not grow a second query implementation.
- Route registration tests and query-service tests are the contract for public
  behavior.

## Verification

- `tests/api/test_query_service_extraction.py`
- `tests/api/test_query_async_boundaries.py`
- `tests/api/test_critical_path_stream.py`
- `tests/api/test_langgraph_api.py`
- `tests/api/test_query_helper_drift.py`
- `evidence/2026-05-03/query_service_extraction/README.md`
