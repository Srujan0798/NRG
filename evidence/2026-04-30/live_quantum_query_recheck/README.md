# Live Quantum Query Recheck

Fresh full-stack proof that `best quantum researchers` does not return the generic fallback answer.

- Backend: `/query` through the E2E proxy.
- Frontend: login -> dashboard -> query -> streaming answer -> citation drawer -> source drawer -> audit drawer -> mobile screenshot.
- Security: Tier 3 direct PII request stays blocked and includes an audit event ID.

Command:

```bash
cd frontend && PLAYWRIGHT_BASE_URL=http://127.0.0.1:3010 PLAYWRIGHT_PORT=3010 API_TARGET=127.0.0.1:8020 npx playwright test -c tests/playwright.config.ts tests/e2e/live_quantum_query_recheck.spec.ts --reporter=list
```

Result: `1 passed`.

API summary:

- Researcher query: `route=sql`, `tier=1`, 5 SQL rows, 1 citation, audit event ID present.
- Answer specificity: contains quantum-specific researcher evidence and does not contain the generic fallback text.
- Tier 3 PII query: `status=blocked`, `route=blocked`, `tier=3`, audit event ID present.
- Browser console stack-trace error list: `[]`.
