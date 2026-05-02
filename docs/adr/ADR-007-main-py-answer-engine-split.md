# ADR-007: Query Answer Service Extraction

Date: 2026-05-03

## Status

Accepted and locally implemented.

## Context

`src/api/main.py` had grown to include application setup, middleware, route
registration, runtime dependencies, and the live answer-engine route bodies for
`/query` and `/api/query/stream`.

That structure made the query path harder to review because route wiring and
answer-engine behavior changed in the same file. It also made the existing
`src/api/query_helpers.py` drift issue more dangerous: helper-looking functions
could be mistaken for the live route contract.

## Decision

Move the live answer-engine route bodies behind `QueryAnswerService` in
`src/api/query_service.py`.

`src/api/main.py` remains responsible for:

- FastAPI app construction;
- middleware and lifecycle wiring;
- dependency binding;
- router registration;
- thin compatibility wrappers for existing call sites.

`QueryAnswerService` now owns:

- `/query` execution;
- `/api/query/stream` execution;
- answer payload normalization handoff;
- query-path audit event handling;
- cache, tier-filter, C4 read-model, fast-path, adversarial, killer-query, and
  LangGraph workflow sequencing through injected dependencies.

`src/api/query_helpers.py` remains a compatibility/helper module. Behavioral
authority is the service plus the route tests, not a second independent query
implementation.

## Consequences

- Query behavior is isolated from app setup without changing public endpoints.
- Future query refactors should target `QueryAnswerService` and its tests.
- New code must not introduce another parallel query implementation in
  `main.py`, `query_helpers.py`, or route modules.
- Any helper exported from `query_helpers.py` must either delegate to the live
  path or be covered by a drift test proving it matches the live contract.

## Verification

- `tests/api/test_query_service_extraction.py`
- `tests/api/test_query_async_boundaries.py`
- `tests/api/test_critical_path_stream.py`
- `tests/api/test_langgraph_api.py`
- `tests/api/test_query_helper_drift.py`

Evidence:

- `evidence/2026-05-03/query_service_extraction/README.md`
- `evidence/2026-05-03/post_state_replay/README.md`
