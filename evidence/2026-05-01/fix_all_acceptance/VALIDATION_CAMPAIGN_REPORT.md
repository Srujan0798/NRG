# NRG Fix-All Acceptance Report

Date: 2026-05-01

Scope: local pinned-venv validation for the current answer-engine path, health gate, frontend build, browser proof, and security block contract. This report does not claim deployed/cluster production readiness.

## Result

Local acceptance status: **PASS**

Production readiness status: **BLOCKED BY REMAINING EXTERNAL GATES**

The local stack now passes the pinned deployment gate and the live browser answer-engine proof. The remaining blockers are not code-level local failures: they require deployed environment evidence, cluster/load evidence, production Qdrant baseline, and final owner/founder sign-off.

## Root Cause Fixed

The root `/health` response was reporting `status: unhealthy` because the live HMAC audit chain now has 47,863 events and a no-repair chain health read took about 2037 ms. The previous default health audit timeout was 1.0 s, so health could fail even though the audit chain itself was valid.

Fix:

- Raised the default audit health timeout from 1.0 s to 3.0 s in `src/api/main.py`.
- Applied the same env-backed default in `src/api/routes/health.py`.
- Kept `NRG_HEALTH_AUDIT_TIMEOUT_SECONDS` as the override for stricter or looser environments.

## Browser Contract Fixed

The live browser proof expected security blocks from `/query` to always be HTTP 400. The backend answer-engine contract already allows a safe blocked envelope with HTTP 200 or 400, as long as the payload proves:

- `route: blocked`
- `blocked: true`
- `status: blocked`
- `tier`
- `audit_event_id`
- no source rows, SQL, citations, or leaked PII

Fix:

- Updated `frontend/tests/e2e/live_quantum_query_recheck.spec.ts` to accept the real blocked-envelope contract.
- Updated `frontend/tests/e2e/live_full_stack_proof.spec.ts` the same way.
- Made both specs accept `NRG_EVIDENCE_DIR` so new validation evidence does not get written into stale dated folders.

## Evidence Index

Core checks:

- `00_truth_inventory.log` - repo inventory at start of pass.
- `01_corpus_sync.log` - corpus sync check passed.
- `02_pinned_env.log` - pinned venv versions captured.
- `03_health_before_fix.json` - health returned unhealthy before timeout fix.
- `05_audit_health_timing.log` - audit chain itself was healthy, valid, and 47,863 events long.
- `06_health_after_timeout_fix.json` - health returned healthy after timeout fix.
- `07_deployment_gate_venv.log` - pre-fix deployment gate failed on the test-suite phase.
- `08_pytest_venv_direct_retry.log` - direct pinned test run passed: 1749 passed, 56 skipped, 257 deselected.
- `09_deployment_gate_venv_after_health_fix.log` - deployment gate passed all stages.
- `10_health_timeout_regression.log` - focused health timeout regression tests passed.
- `11_frontend_build.log` - frontend production build passed.
- `12_frontend_jest.log` - frontend Jest suite passed: 26 suites, 97 tests.
- `13_live_quantum_browser_recheck.log` - live quantum messy-query browser proof passed.
- `14_live_full_stack_browser_proof.log` - broader live full-stack browser proof passed.
- `15_query_security_contract.log` - backend blocked-envelope security contract passed.
- `16_python_compile.log` - patched Python files compile.
- `17_git_diff_check.log` - whitespace diff check passed.
- `18_secret_scan_evidence.log` - current evidence folder contains no JWT/access-token patterns.
- `19_port_18000_after_stop.log` - local API and browser proof ports were closed after validation.

Browser evidence:

- `live_quantum_query_recheck/01_researcher_quantum_query_api.json`
- `live_quantum_query_recheck/02_login_desktop.png`
- `live_quantum_query_recheck/05_quantum_answer_verified_desktop.png`
- `live_quantum_query_recheck/06_citation_drawer_desktop.png`
- `live_quantum_query_recheck/07_source_data_drawer_desktop.png`
- `live_quantum_query_recheck/08_audit_proof_drawer_desktop.png`
- `live_quantum_query_recheck/09_quantum_answer_verified_mobile.png`
- `live_quantum_query_recheck/10_tier3_blocked_quantum_pii_query.json`
- `live_quantum_query_recheck/live_quantum_recheck_messy_query_returns_specific_evidence_citations_source_rows_audit_proof_and_tier_3_block.webm`
- `live_full_stack_proof/01_login_desktop.png`
- `live_full_stack_proof/04_answer_verified_desktop.png`
- `live_full_stack_proof/05_citation_drawer_desktop.png`
- `live_full_stack_proof/06_source_data_drawer_desktop.png`
- `live_full_stack_proof/07_audit_proof_drawer_desktop.png`
- `live_full_stack_proof/08_answer_verified_mobile.png`
- `live_full_stack_proof/09_tier3_blocked_browser_query.json`
- `live_full_stack_proof/live_full_stack_proof_login_messy_query_citations_source_data_audit_proof_and_tier_block.webm`

## Commands Proven

- `.venv/bin/python scripts/verify_corpus_sync.py`
- `.venv/bin/python -m pytest tests/ -v --tb=short -x -q`
- `.venv/bin/python scripts/deployment_gate.py`
- `.venv/bin/python -m pytest tests/api/test_health_endpoints.py::test_root_health_times_out_slow_audit_check tests/api/test_health_endpoints.py::test_root_health_reports_table_count_and_fast_audit_status -q`
- `npm --prefix frontend run build`
- `npm --prefix frontend test -- --runInBand`
- `npx playwright test -c tests/playwright.config.ts tests/e2e/live_quantum_query_recheck.spec.ts --reporter=list`
- `npx playwright test -c tests/playwright.config.ts tests/e2e/live_full_stack_proof.spec.ts --reporter=list`
- `.venv/bin/python -m pytest tests/api/test_query_security_validation.py -q`
- `.venv/bin/python -m py_compile src/api/main.py src/api/routes/health.py`
- `git diff --check`

## Remaining Blockers

These are still not closed by this local pass:

- Deployed browser replay against the production URL.
- Production Qdrant/vector baseline and scheduler status.
- 1000-user sovereign-cluster load evidence, or an explicit accepted lower target.
- Final owner/founder signing package.

## Notes

The live browser proof was run after restarting the local API with `NRG_QUOTA_DISABLED=1` to prevent prior aggressive local validation from rate-limiting the same test identity. This does not disable the DLP block itself; the evidence still shows the Tier 3 PII request returned a blocked answer-engine envelope with an audit event ID.
