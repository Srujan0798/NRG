# Batch 2 + Batch 5 Requested Verification

Date: 2026-05-02

## Commands Requested

```bash
cd frontend && npm run build && npm test -- --runInBand
.venv/bin/python -m pytest tests/orchestration/ tests/skills/ -q --tb=short --no-cov -x
git status --short
```

## Batch 2 Frontend

Command: `npm run build`

Result: PASS.

Observed summary:

- TypeScript compile completed.
- Vite production build completed.
- Largest chunk shown: `vendor-recharts-xdmfsjT3.js` at `319.01 kB`, below the 500 KB chunk budget.
- Build finished in `6.27s`.

Command: `npm test -- --runInBand`

Result: PASS.

Observed summary:

- Test suites: `32 passed, 32 total`
- Tests: `107 passed, 107 total`
- The earlier Jest open-handle warning was reproduced with `--detectOpenHandles`, traced to `tests/lib/dpdpStore.test.ts`, and fixed by mocking `dpdpService.grantConsent` / `dpdpService.revokeConsent` at the store unit-test boundary.
- Final `npm test -- --runInBand --detectOpenHandles`: `32 passed, 107 passed`, no open-handle report.
- Final `npm run build && npm test -- --runInBand`: PASS, `32 passed, 107 passed`, no post-run open-handle warning.

## Batch 5 AI/RAG

Command: `.venv/bin/python -m pytest tests/orchestration/ tests/skills/ -q --tb=short --no-cov -x`

First run: FAIL.

Failure:

- `tests/orchestration/test_router.py::TestRouterConfidenceThresholds::test_low_confidence_upgraded_to_hybrid`
- Cause: `_stage2_llm_confirmation` assumed `_classify_intent_via_llm` always returned a tuple. The test intentionally mocked the legacy string return `"hybrid"`, causing string indexing / confidence parsing to fail.

Fix:

- Updated `src/orchestration/nodes/router.py` to normalize LLM route results from string, tuple/list, or dict forms.
- Legacy string route results now receive at least `CONFIDENCE_THRESHOLD_LOW`.

Focused rerun:

- `tests/orchestration/test_router.py::TestRouterConfidenceThresholds::test_low_confidence_upgraded_to_hybrid`
- Result: PASS, `1 passed`.

Final full rerun:

- Result: PASS.
- Observed summary: `391 passed, 6 skipped, 35 deselected`.
- Final rerun after the frontend open-handle cleanup also passed: `391 passed, 6 skipped, 35 deselected in 30.86s`.

## Git Status Boundary

`git status --short` remains dirty with many modified/untracked files from prior and current batches. Relevant current additions include:

- `evidence/2026-05-02/batch2_frontend_polish/`
- `evidence/2026-05-02/batch5_orchestration_ai_rag/`
- `src/skills/rag/ingestion.py`

This verification does not claim a clean git tree.
