# Live Quantum Query Recheck

Fresh full-stack proof that `best quantum researchers` does not return the generic fallback answer.

- Backend: `/query` through the E2E proxy.
- Frontend: login -> dashboard -> query -> streaming answer -> citation drawer -> source drawer -> audit drawer -> mobile screenshot.
- Security: Tier 3 direct PII request stays blocked and includes an audit event ID.

## Audit Proof Drawer Closure

The first browser run exposed a real integration bug: the frontend audit proof drawer called
`GET /audit/event/{audit_event_id}`, but the backend only exposed `/audit/events` and
`/audit/verify`. The missing single-event route fell through to the API container's SPA
fallback and produced `500 Internal Server Error` console entries.

Fix:

- Added authenticated `GET /audit/event/{event_id}`.
- Real recent chain events return normalized `id`, `hmac`, `current_hmac`, `prev_hmac`,
  `next_hmac`, `action`, `actor`, `timestamp`, `integrity_status`, and evidence count.
- Older or pruned response hashes return a `pending` reference instead of a backend 500.
- Unauthorized existing events remain hidden with `404`.

Verification after the fix:

- `tests/api/test_audit_event_endpoint.py tests/api/test_langgraph_api.py tests/api/test_query_security_validation.py`: `41 passed`.
- `npx playwright ... tests/e2e/live_quantum_query_recheck.spec.ts`: `1 passed`.
- `console_errors.json`: `[]`.
- `api_logs_after_audit_event_fix.log`: audit event drawer calls returned `200 OK`; no `500`,
  traceback, or missing `dist/frontend/index.html` error matched the final scan.
- `health_all_after_audit_event_fix.json`: local API, Qdrant, Redis, and consent service healthy;
  local LLM remains optional unavailable.
- `corpus_sync_after_audit_event_fix.json`: source-truth corpus mirrors match the canonical files.
- `ruff_audit_event_fix.log`: changed backend files pass Ruff.
