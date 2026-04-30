# Browser Flow Calibration Results

## Command

```bash
cd frontend
PLAYWRIGHT_BASE_URL=http://127.0.0.1:3010 PLAYWRIGHT_PORT=3010 API_TARGET=127.0.0.1:8020 npx playwright test -c tests/playwright.config.ts tests/e2e/live_quantum_query_recheck.spec.ts --reporter=list
```

## First Run

Result: FAIL

Failure:

- The API proof for `best quantum researchers....` completed.
- Browser login page stayed on `Signing you in...`.
- Playwright timed out waiting for `data-testid="tier-dashboard"`.
- Failure screenshot: `frontend/tests/test-results/e2e-live_quantum_query_rec-ce54e-udit-proof-and-Tier-3-block-chromium/test-failed-1.png`
- Error context: `frontend/tests/test-results/e2e-live_quantum_query_rec-ce54e-udit-proof-and-Tier-3-block-chromium/error-context.md`

Root cause:

- The login surface ran a backend availability poll against root `/health`.
- Root `/health` can spend tens of seconds in deep dependency checks.
- That degraded the login flow during live browser testing.

Fix:

- Changed `frontend/src/hooks/useAuth.tsx` to poll lightweight `/health/db` with a 5s timeout instead of root `/health` with a 10s timeout.

## Retest

Result: PASS

Output:

```text
✓ 1 [chromium] › tests/e2e/live_quantum_query_recheck.spec.ts:45:5 › live quantum recheck: messy query returns specific evidence, citations, source rows, audit proof, and Tier 3 block (36.3s)
1 passed (50.1s)
```

Evidence:

- `evidence/2026-04-30/live_quantum_query_recheck/01_researcher_quantum_query_api.json`
- `evidence/2026-04-30/live_quantum_query_recheck/02_login_desktop.png`
- `evidence/2026-04-30/live_quantum_query_recheck/03_researcher_dashboard_desktop.png`
- `evidence/2026-04-30/live_quantum_query_recheck/04_streaming_planning_desktop.png`
- `evidence/2026-04-30/live_quantum_query_recheck/05_quantum_answer_verified_desktop.png`
- `evidence/2026-04-30/live_quantum_query_recheck/06_citation_drawer_desktop.png`
- `evidence/2026-04-30/live_quantum_query_recheck/07_source_data_drawer_desktop.png`
- `evidence/2026-04-30/live_quantum_query_recheck/08_audit_proof_drawer_desktop.png`
- `evidence/2026-04-30/live_quantum_query_recheck/09_quantum_answer_verified_mobile.png`
- `evidence/2026-04-30/live_quantum_query_recheck/10_tier3_blocked_quantum_pii_query.json`
- `evidence/2026-04-30/live_quantum_query_recheck/console_errors.json`
- `evidence/2026-04-30/live_quantum_query_recheck/live_quantum_recheck_messy_query_returns_specific_evidence_citations_source_rows_audit_proof_and_tier_3_block.webm`

Campaign interpretation:

- Live local browser proof now passes.
- The visible path covers login, dashboard, messy query, streaming phases, verified answer, citation drawer, source drawer, audit drawer, mobile screenshot, and Tier 3 PII block raw JSON.
