# L1 Async Query Boundary Verification

Date: 2026-05-02

## Scope

This pass closes L1-CR-007 locally. The check verifies that the async query
handlers do not call blocking answer-engine paths directly on the event loop.

## Verification

| Command | Result | Evidence |
|---|---:|---|
| `.venv/bin/python -m pytest tests/api/test_query_async_boundaries.py -q --tb=short --no-cov` | PASS, 2 passed | `01_query_async_boundary_tests.log` |
| `.venv/bin/python -m py_compile tests/api/test_query_async_boundaries.py` | PASS | `02_query_async_boundary_py_compile.log` |

## Coverage

- `_query_with_langgraph_impl` has no direct calls to `_c4_read_model_response`,
  `_fast_query_response`, `_academic_follow_up_response`, `_killer_query_response`,
  `_advanced_adversarial_response`, or `_run_workflow`.
- Those blocking paths are registered through `asyncio.to_thread`.
- `_query_stream_response` builds the answer payload through
  `asyncio.to_thread(_build_stream_answer_payload, ...)`.

## Remaining

- L1-CR-006 remains OPEN: the active `/query` behavior still lives in
  `src/api/main.py`; `src/api/query_helpers.py` remains partial helper logic and
  needs a separate route/helper extraction pass.
