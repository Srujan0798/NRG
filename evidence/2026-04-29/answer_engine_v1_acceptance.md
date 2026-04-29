# Answer Engine v1 Acceptance Evidence

Date: 2026-04-29

## Backend

Command:
`pytest tests/contract/test_answer_engine_v1_contract.py tests/api/test_langgraph_api.py tests/api/test_answer_records_api.py tests/api/test_query_security_validation.py tests/api/test_critical_path_stream.py tests/orchestration/test_verifier_node.py tests/orchestration/test_verifier_numeric_faithfulness.py -q`

Result:
41 passed, 1 warning.

## Frontend

Command:
`cd frontend && npm test -- tests/lib/answerEngineContract.test.ts tests/lib/queryServiceSanitization.test.ts tests/components/ProofInspector.test.tsx tests/components/QueryWorkbench.test.tsx tests/components/AnswerEngineSurface.test.tsx --runInBand`

Result:
5 test suites passed, 11 tests passed.

## E2E

Command:
`cd frontend && npx playwright test -c tests/playwright.config.ts e2e/streaming_answer.spec.ts e2e/answer_engine_v1_walk.spec.ts --project=chromium`

Result:
2 passed.

## Build

Command:
`cd frontend && npm run build`

Result:
TypeScript and Vite production build passed.

## Acceptance

- Ask workspace visible.
- Query progresses through human-readable phases.
- Final answer uses canonical envelope.
- Source, SQL, and audit proof visible.
- Blocked sensitive query returns safe envelope.
- Tier filtering remains enforced before frontend render.
