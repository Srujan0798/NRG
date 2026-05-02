# L1 Text-to-SQL Lifecycle Fix

Date: 2026-05-02

## Scope

This pass closes L1-CR-008 locally. The executor cached `TextToSQLSkill` and
`RAGSkill` instances, but closed them at the end of each request, defeating
pooling and warm state.

## Change

- `src/orchestration/nodes/executor.py` now keeps cached SQL/RAG skills alive
  across requests.
- Cached instances are closed only when their class binding changes, which keeps
  monkeypatch/test replacement safe without closing the production hot path per
  request.
- `tests/orchestration/test_nodes.py` now asserts per-request executor calls do
  not close the cached skills.

## Verification

| Command | Result | Evidence |
|---|---:|---|
| `.venv/bin/python -m pytest tests/orchestration/test_nodes.py tests/orchestration/test_workflow_pipeline.py -q --tb=short --no-cov` | PASS, 23 passed | `01_executor_lifecycle_tests.log` |
| `.venv/bin/python -m py_compile src/orchestration/nodes/executor.py` | PASS | `02_executor_py_compile.log` |

## Remaining

- L1-CR-006 remains OPEN: active `/query` behavior still lives in
  `src/api/main.py`; `src/api/query_helpers.py` is partial helper logic and
  needs a separate focused route/helper extraction pass.
- L1-CR-007 remains UNKNOWN in this pass: async handler event-loop impact needs
  backend performance/refactor proof.
