# NRG Validation Campaign Report

Date: 2026-04-30
Mode: `calibration`

## Scope

This campaign used the new validation-campaign workflow as the driver. It covered the highest-risk local path: login, role/tier behavior, messy query answer quality, security blocks, audit proof, frontend build, and one live browser workflow.

This is not a production-readiness claim. Production readiness still requires deployed 1000-user C4 proof, deployed browser replay, production Qdrant baseline, and founder signing.

## Results

| Gate | Result | Evidence |
| --- | --- | --- |
| Campaign plan and truth lock | PASS | `00_campaign_plan.md`, `01_truth_report.md` |
| Query corpus | PASS | `02_query_corpus.csv` |
| Backend targeted tests | PASS | `04_backend_test_results.txt` |
| API corpus and tier/security checks | PASS | `03_api_results.jsonl`, `raw_json/*.json` |
| Security probes | PASS | `05_security_red_team_results.md` |
| Tier matrix | PASS | `06_tier_matrix.md` |
| Frontend build | PASS | `07_frontend_build.txt` |
| Browser workflow | PASS after fix | `08_browser_flow_results.md`, `../live_quantum_query_recheck/` |
| Audit chain after campaign | PASS | `09_audit_chain.md` |
| Findings and fixes | RECORDED | `10_findings_and_fixes.md` |

## Commands Run

```bash
python3 -m compileall -q src/api/main.py
python3 -m pytest tests/api/test_c4_read_model.py tests/api/test_k4_publication_count_fast_path.py tests/api/test_query_security_validation.py tests/api/test_request_logging_middleware.py tests/api/test_health_endpoints.py -q
python3 <api calibration probe>
python3 <audit chain probe>
cd frontend && npm run build
python3 -m uvicorn src.api.main:app --host 127.0.0.1 --port 8020 --no-access-log --log-level error
cd frontend && PLAYWRIGHT_BASE_URL=http://127.0.0.1:3010 PLAYWRIGHT_PORT=3010 API_TARGET=127.0.0.1:8020 npx playwright test -c tests/playwright.config.ts tests/e2e/live_quantum_query_recheck.spec.ts --reporter=list
```

## Recorded Coverage

- 20 recorded validation steps in `03_api_results.jsonl`.
- 3 login proofs: Researcher, Government, Industry.
- 14 query/security probes.
- 1 health probe.
- 1 audit-chain proof.
- 1 live browser workflow proof.

Representative query: `best quantum researchers....`

Representative security probes:

- Tier 3 direct PII request.
- Prompt injection request.
- SQL injection request.
- Tier escalation request.

## Fix Made

Changed `frontend/src/hooks/useAuth.tsx`:

- Before: login screen polled deep root `/health` with a 10s timeout.
- After: login screen polls lightweight `/health/db` with a 5s timeout.

Reason:

- The first browser run failed because root `/health` could block on deeper dependency checks during login.
- After the fix and rebuild, the live browser proof passed.

## Findings

No CRITICAL failures were found in the calibration slice.

HIGH performance finding:

- Some non-fast-path or deep dependency checks were slow:
  - First cold quantum query: about 12.5s.
  - TRL query: about 10.2s.
  - Out-of-corpus sports query: about 376s due RAG/Qdrant timeout behavior.
  - Root `/health`: about 37.1s.

Recommended next fix:

- Keep login and ordinary UX paths away from deep root `/health`.
- Add bounded timeout/fallback handling for out-of-corpus RAG routes.
- Split root health into fast readiness plus optional deep diagnostics before acceptance/release-candidate campaigns.

## Current Blockers

- Production Qdrant baseline is still unproven.
- 1000-user deployed C4 is still unproven.
- Deployed browser replay is still unproven.
- Founder signing is still pending.

Commit SHA: not committed.
