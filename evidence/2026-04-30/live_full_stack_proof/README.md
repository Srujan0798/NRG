# Live Full-Stack Proof

Date: 2026-04-30

This directory contains the live local full-stack browser proof captured against:

- Backend: `uvicorn src.api.main:app` on `127.0.0.1:8020`
- Frontend: production build served by `frontend/e2e-server.js` on `127.0.0.1:3010`
- API proxy target: `127.0.0.1:8020`
- Browser command: `PLAYWRIGHT_BASE_URL=http://127.0.0.1:3010 PLAYWRIGHT_PORT=3010 API_TARGET=127.0.0.1:8020 npx playwright test -c tests/playwright.config.ts tests/e2e/live_full_stack_proof.spec.ts`

## Passed Path

- Login screen renders.
- Tier 1 researcher login succeeds.
- Researcher dashboard renders with the query box.
- Messy query `best quantum researchers` streams through planning, execution, synthesis, and verification.
- Final answer contains Quantum Computing researcher evidence.
- Citation drawer opens.
- Source-data drawer opens and shows SQL/row evidence.
- Audit proof drawer opens and shows HMAC proof.
- Mobile answer screenshot has no separate mock path.
- Tier 3 blocked sensitive query returns `route=blocked`, `tier=3`, and an `audit_event_id`.

## Files

- `01_login_desktop.png`
- `02_researcher_dashboard_desktop.png`
- `03_streaming_planning_desktop.png`
- `04_answer_verified_desktop.png`
- `05_citation_drawer_desktop.png`
- `06_source_data_drawer_desktop.png`
- `07_audit_proof_drawer_desktop.png`
- `08_answer_verified_mobile.png`
- `09_tier3_blocked_browser_query.json`
- `researcher_best_quantum_query.json`
- `industry_blocked_sensitive_query.json`
- `console_errors.json`
- `live_full_stack_proof_login_messy_query_citations_source_data_audit_proof_and_tier_block.webm`

