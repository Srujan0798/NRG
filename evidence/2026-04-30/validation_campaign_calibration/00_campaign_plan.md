# NRG Validation Campaign Calibration Plan

Date: 2026-04-30
Mode: `calibration`

## Purpose

Run the first real campaign using the new validation-campaign workflow. This is a focused confidence pass, not a production-readiness claim.

## In Scope

- Raw API login for Tier 1, Tier 2, and Tier 3 personas.
- Query breadth across answer-engine routes: quantum researcher ranking, funding, publications, TRL, patents, ambiguous requests, noisy wording, and out-of-corpus questions.
- Tier safety checks for representative queries.
- Security probes for direct PII, prompt injection, SQL injection, and tier escalation.
- Audit-event presence on allowed and blocked query paths.
- Audit-chain health.
- Targeted backend regression tests.
- Frontend production build.
- One live browser proof using the existing quantum query recheck if backend and frontend start cleanly.

## Out Of Scope

- 1000-user sovereign-cluster C4 proof.
- Deployed browser replay.
- Production Qdrant corpus baseline.
- Founder GPG signing.
- Claims that every UI path and every query class are exhaustively proven.

## Commands Planned

```bash
python3 -m compileall -q src/api/main.py
python3 -m pytest tests/api/test_c4_read_model.py tests/api/test_k4_publication_count_fast_path.py tests/api/test_query_security_validation.py tests/api/test_request_logging_middleware.py tests/api/test_health_endpoints.py -q
python3 <campaign_api_probe>
python3 <audit_chain_probe>
cd frontend && npm run build
python3 -m uvicorn src.api.main:app --host 127.0.0.1 --port 8020 --no-access-log --log-level error
cd frontend && PLAYWRIGHT_BASE_URL=http://127.0.0.1:3010 PLAYWRIGHT_PORT=3010 API_TARGET=127.0.0.1:8020 npx playwright test -c tests/playwright.config.ts tests/e2e/live_quantum_query_recheck.spec.ts --reporter=list
```

## Expected Evidence

- `01_truth_report.md`
- `02_query_corpus.csv`
- `03_api_results.jsonl`
- `04_backend_test_results.txt`
- `05_security_red_team_results.md`
- `06_tier_matrix.md`
- `07_frontend_build.txt`
- `08_browser_flow_results.md`
- `09_audit_chain.md`
- `10_findings_and_fixes.md`
- `VALIDATION_CAMPAIGN_REPORT.md`
- `raw_json/*.json`
- browser screenshots/videos under `evidence/2026-04-30/live_quantum_query_recheck/`

## Pass Criteria

- Targeted backend tests pass.
- API calibration has no CRITICAL failures.
- Tier 3 raw JSON does not expose obvious PII for representative allowed queries.
- Direct PII, prompt injection, SQL injection, and tier escalation probes are blocked or safely bounded with audit IDs.
- Audit chain verifies after campaign probes.
- Frontend build passes.
- Browser proof passes or records a clear blocker with logs.
