# Maximum Enforcement Local Acceptance Report

Date: 2026-05-05
Scope: local Docker API stack plus local Playwright E2E server, Chromium only.
Verdict: local main-flow gate PASS; whole-project / production readiness is BLOCKED.

## Commands Run

| Command | Result |
| --- | --- |
| `npm run build` in `frontend/` | PASS. TypeScript and Vite production build completed; Vite reported `built in 3m 19s`, largest JS chunk `vendor-recharts-xdmfsjT3.js` at `319.01 kB`. |
| `NRG_EVIDENCE_DIR=../evidence/2026-05-05/maximum_enforcement_local_browser_final npx playwright test -c tests/playwright.config.ts e2e/live_quantum_query_recheck.spec.ts --project=chromium` | PASS. `1 passed (28.8s)`. |
| `POSTGRES_USER=nrg POSTGRES_PASSWORD=nrg_default_password POSTGRES_DB=nrg docker compose up -d pgbouncer api` | PASS. Recreated PgBouncer/API after `/health` exposed empty-password PgBouncer config. |
| `POSTGRES_USER=nrg POSTGRES_PASSWORD=nrg_default_password POSTGRES_DB=nrg UVICORN_WORKERS=1 docker compose up -d api` | PASS. Recreated API with the local one-worker acceptance profile. |
| `curl -sS http://127.0.0.1:8000/health/all` | PASS. Returned `healthy: true`. |
| `curl -sS http://127.0.0.1:8000/health` | PASS after PgBouncer/API env repair. Returned `healthy: true`, PostgreSQL healthy with 50,000 researchers and 50,000 publications, and audit healthy. |
| `.venv/bin/python scripts/audit_chain_health_check.py` | PASS. `ok: true`, `valid: true`, `valid_event_count: 312819`, `errors: []`. |
| `curl -sS -i -X POST http://127.0.0.1:8000/api/telemetry ...` | PASS. HTTP `202 Accepted`, `x-request-id: e92fd6b9-5d7f-4217-9381-590e9a047ea9`, audit event `9c7cf2b5d3c1460812ee315b457b01e0274b2f7807089dd7a10b69699fa359ad`. |
| `.venv/bin/python -m pytest tests/config/test_docker_compose_pgbouncer.py tests/config/test_batch6_infra_hardening.py::test_compose_uses_restart_healthchecks_and_no_password_defaults tests/api/test_telemetry_contract.py -q --tb=short` | PASS. `4 passed in 7.23s`. |

## Evidence

| Gate | Status | Evidence |
| --- | --- | --- |
| API startup and aggregate health | PASS | `/health/all` returned `healthy: true`; Docker reported `nrg-api`, `nrg-pgbouncer`, `nrg-postgres`, `nrg-redis`, `nrg-qdrant`, and `nrg-frontend` healthy/running after the repair. |
| Strict API health | PASS | `/health` returned `healthy: true`; database `status: healthy`, dialect `postgresql`, `researchers: 50000`, `publications: 50000`, `table_count: 80`; audit `chain_valid: true`. |
| Browser main flow | PASS | `02_login_desktop.png`, `03_researcher_dashboard_desktop.png`, `04_streaming_planning_desktop.png`, `05_quantum_answer_verified_desktop.png`, `06_citation_drawer_desktop.png`, `07_source_data_drawer_desktop.png`, `08_audit_proof_drawer_desktop.png`, `09_quantum_answer_verified_mobile.png`, and the `.webm` recording in this folder. |
| Console/network hygiene | PASS | `console_errors.json`, `browser_network_errors.json`, and `browser_network_ignored.json` are all `[]`. |
| Tier 1 raw API response | PASS | `01_researcher_quantum_query_api.json`: query `best quantum researchers....`, tier `1`, route `sql`, 5 source rows, 2 citations, audit event `f1bd4143972dfc9261058daf5216bdb447616f31cc00ff0c7ef9aaa8ed58327e`. |
| Tier 3 PII block | PASS | `10_tier3_blocked_quantum_pii_query.json`: tier `3`, route `blocked`, `blocked: true`, audit event `47386e9475fa83d386bc1e674ef4f61096fb5b103ecd4b6adecc69e15470f066`. Regex PII scan found 0 email/phone/Aadhaar-like string hits. |
| Audit chain after flow | PASS | `.venv/bin/python scripts/audit_chain_health_check.py` returned `valid: true`, `valid_event_count: 312819`, `errors: []`. |
| Telemetry ingestion | PASS | Direct `/api/telemetry` returned HTTP `202` with request ID and audit event ID. |
| Local PgBouncer repair | PASS local environment | PgBouncer config changed from invalid `auth_user=nrg:` to `auth_user=nrg`; `docker exec nrg-pgbouncer psql ...` returned `current_user nrg`, `current_database nrg`. |

## Blockers

| Surface | Status | Blocker |
| --- | --- | --- |
| Deployed browser replay | BLOCKED | No deployed frontend/API URL is available in this workspace. |
| Production API/Qdrant/Redis proof | BLOCKED | No production service target is available in this workspace. |
| Sovereign-cluster C4 | BLOCKED | No reachable cluster context or explicit cluster-load target is available. Current C4 evidence remains local quota-neutral only. |
| Founder signatures | BLOCKED | Founder detached GPG signatures require founder private key access. |
| S3-09 remote closure | BLOCKED | Local rewritten-history scan has evidence, but remote force-push coordination and credential rotation require operator approval. |
| Deployed image scans | BLOCKED | Local image evidence exists; deployed image scan target is unavailable. |

## Commit State

This folder was generated after `6b647d4f evidence: refresh clean local browser proof`
as final local browser evidence for the May 5 cleanup pass.
