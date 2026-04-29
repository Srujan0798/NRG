# Live Hybrid Query Acceptance

Date: 2026-04-29

## Query

`Top funding agencies and explain the policy pattern`

## Backend Live Stream

Command:
`pytest tests/api/test_live_hybrid_stream.py tests/api/test_critical_path_stream.py tests/contract/test_answer_engine_v1_contract.py tests/orchestration/test_synthesizer_citations.py -q`

Result:
11 passed, 1 warning.

Observed live stream contract:
- `event: answer` returns `route = hybrid`.
- `source_data.sql_query` starts with `SELECT gov_organisation_name`.
- `source_data.rows` contains at least 5 live funding aggregate rows.
- `source_data.documents` contains local strategy document chunks.
- `provenance.synth = rule_based_hybrid`.
- `provenance.hybrid_evidence.sql_rows` equals returned SQL row count.
- `provenance.hybrid_evidence.document_chunks` equals returned document count.
- `audit_event_id` is present.

## Real Browser Path

Backend server command:
`uvicorn src.api.main:app --host 127.0.0.1 --port 8000`

Browser command:
`cd frontend && PLAYWRIGHT_PORT=3010 API_TARGET=127.0.0.1:8000 NRG_LIVE_BACKEND_E2E=1 CI=1 npx playwright test -c tests/playwright.config.ts tests/e2e/live_hybrid_backend.spec.ts --project=chromium`

Result:
1 passed.

What this proves:
- The browser logs in through the real backend.
- The app sends the query through the real `/api/query/stream` endpoint.
- The source drawer shows Evidence mix, Structured SQL rows, Document excerpts, and the SQL used.
- The browser test does not install the mocked SSE server.

## Supporting Frontend Regression

Command:
`cd frontend && PLAYWRIGHT_PORT=3011 CI=1 npx playwright test -c tests/playwright.config.ts tests/e2e/hybrid_proof_acceptance.spec.ts tests/e2e/answer_engine_v1_walk.spec.ts tests/e2e/streaming_answer.spec.ts --project=chromium`

Result:
3 passed.

Command:
`cd frontend && npm test -- --runInBand tests/components/StreamingAnswerPanel.test.tsx tests/components/AnswerPanelSqlResults.test.tsx tests/components/AnswerTrustActions.test.tsx tests/lib/answerEngineContract.test.ts`

Result:
4 test suites passed, 5 tests passed.

## Build And Static Checks

Command:
`cd frontend && npm run build`

Result:
TypeScript and Vite production build passed.

Command:
`cd frontend && npm run lint -- --quiet`

Result:
Passed.

Command:
`node --check frontend/e2e-server.js`

Result:
Passed.

Command:
`git diff --check`

Result:
Passed.

## Implementation Notes

- Funding-ranking plus explanation/policy-pattern questions now use a bounded hybrid path.
- Structured evidence comes from `innovation_grant_from_govt` aggregate SQL.
- Document evidence comes from local strategy documents:
  - `docs/strategy/national_pitch_deck.md`
  - `docs/strategy/iit_nit_expansion_proposal.md`
- The E2E proxy now detects API paths by URL pathname so query strings on `/api/query/stream` are proxied correctly.
