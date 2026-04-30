# Final Evidence Index

Date: 2026-04-30

## Primary Handover Report

- `docs/handover/SHOW_READINESS_2026-04-30.md`

## Wave Evidence

| Wave | Evidence | Status |
|------|----------|--------|
| W0 State lock | `evidence/2026-04-30/00_current_state.md` | PASS |
| W1 Backend answer engine | `evidence/2026-04-30/wave1_messy_query_acceptance.md` | PASS |
| W2 Frontend main flow | `evidence/2026-04-30/wave2_frontend_main_flow_build.md` | PASS |
| W3 Security/tier/audit | `evidence/2026-04-30/wave3_security_tier_audit_acceptance.md` | PASS |
| W4 SQL/RAG retrieval | `evidence/2026-04-30/wave4_retrieval_sql_rag_acceptance.md` | PASS |
| W5 Load/performance | `evidence/2026-04-30/c4_read_model_singleflight_closure.md` | LOCAL 100-USER C4 PASS, 1000-user cluster proof remains |

## Raw API Evidence

- `evidence/2026-04-30/09_tier1_query_response.json`
- `evidence/2026-04-30/10_tier2_query_response.json`
- `evidence/2026-04-30/11_tier3_query_response.json`
- `evidence/2026-04-30/wave3_blocked_query_responses.json`

## Live Full-Stack Browser Proof

Command:

```bash
cd frontend && PLAYWRIGHT_BASE_URL=http://127.0.0.1:3010 PLAYWRIGHT_PORT=3010 API_TARGET=127.0.0.1:8020 npx playwright test -c tests/playwright.config.ts tests/e2e/live_full_stack_proof.spec.ts
```

Result: `1 passed`.

Evidence:

- `evidence/2026-04-30/live_full_stack_proof/README.md`
- `evidence/2026-04-30/live_full_stack_proof/01_login_desktop.png`
- `evidence/2026-04-30/live_full_stack_proof/02_researcher_dashboard_desktop.png`
- `evidence/2026-04-30/live_full_stack_proof/03_streaming_planning_desktop.png`
- `evidence/2026-04-30/live_full_stack_proof/04_answer_verified_desktop.png`
- `evidence/2026-04-30/live_full_stack_proof/05_citation_drawer_desktop.png`
- `evidence/2026-04-30/live_full_stack_proof/06_source_data_drawer_desktop.png`
- `evidence/2026-04-30/live_full_stack_proof/07_audit_proof_drawer_desktop.png`
- `evidence/2026-04-30/live_full_stack_proof/08_answer_verified_mobile.png`
- `evidence/2026-04-30/live_full_stack_proof/09_tier3_blocked_browser_query.json`
- `evidence/2026-04-30/live_full_stack_proof/live_full_stack_proof_login_messy_query_citations_source_data_audit_proof_and_tier_block.webm`

Live proof summary:

- `best quantum researchers` returned `status=success`, `route=sql`, `tier=1`, 5 SQL rows, 1 citation, and an audit event ID.
- Tier 3 sensitive request returned `status=blocked`, `route=blocked`, `tier=3`, no source rows, and an audit event ID.
- Browser console stack-trace error list: `[]`.

## Live Quantum Query Recheck

Command:

```bash
cd frontend && PLAYWRIGHT_BASE_URL=http://127.0.0.1:3010 PLAYWRIGHT_PORT=3010 API_TARGET=127.0.0.1:8020 npx playwright test -c tests/playwright.config.ts tests/e2e/live_quantum_query_recheck.spec.ts --reporter=list
```

Result: `1 passed`.

Evidence:

- `evidence/2026-04-30/live_quantum_query_recheck/README.md`
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

Live recheck summary:

- `best quantum researchers....` returned `route=sql`, `tier=1`, 5 SQL rows, 1 citation, and an audit event ID.
- The answer text contains quantum-specific researcher evidence and does not contain the generic fallback string.
- Tier 3 sensitive quantum PII request returned `status=blocked`, `route=blocked`, `tier=3`, and an audit event ID.
- Browser console stack-trace error list: `[]`.

## Screenshot Evidence

Desktop:

- `evidence/2026-04-30/ui_ux/after/login_1366.png`
- `evidence/2026-04-30/ui_ux/after/hero_1366.png`
- `evidence/2026-04-30/ui_ux/after/dashboard_researcher_1366.png`
- `evidence/2026-04-30/ui_ux/after/dashboard_government_1366.png`
- `evidence/2026-04-30/ui_ux/after/dashboard_industry_1366.png`
- `evidence/2026-04-30/ui_ux/after/answer_streaming_1366.png`
- `evidence/2026-04-30/ui_ux/after/answer_final_1366.png`
- `evidence/2026-04-30/ui_ux/after/audit_list_1366.png`

Mobile:

- `evidence/2026-04-30/ui_ux/after/login_375.png`
- `evidence/2026-04-30/ui_ux/after/hero_375.png`
- `evidence/2026-04-30/ui_ux/after/dashboard_researcher_375.png`
- `evidence/2026-04-30/ui_ux/after/dashboard_government_375.png`
- `evidence/2026-04-30/ui_ux/after/dashboard_industry_375.png`
- `evidence/2026-04-30/ui_ux/after/answer_streaming_375.png`
- `evidence/2026-04-30/ui_ux/after/answer_final_375.png`
- `evidence/2026-04-30/ui_ux/after/audit_list_375.png`

## Load Evidence

- `evidence/2026-04-30/wave5_local_100_query_profile_before.json`
- `evidence/2026-04-30/wave5_local_100_query_profile_after_audit_fastpath.json`
- `evidence/2026-04-30/wave5_local_100_query_profile_after.json`
- `evidence/2026-04-30/live_c4_local_smoke/README.md`
- `evidence/2026-04-30/live_c4_local_smoke/locust_stats.csv`
- `evidence/2026-04-30/live_c4_local_smoke/locust_report.html`
- `evidence/2026-04-30/c4_read_model_singleflight_closure.md`
- `evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/locust_output.txt`
- `evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/report.html`

Final local 100-query result:

- 100/100 successful responses
- P50: 1613.59ms
- P95: 2031.49ms
- P99: 2094.72ms
- Throughput: 42.62 qps
- Every successful response included an audit event ID

Historical pre-read-model local 100-user Locust smoke:

- 3602 total requests
- 0 HTTP failures
- `/query` P95: 2300ms
- `/query` P99: 2700ms
- Strict C4 latency target failed in this historical run because P99 was above 500ms.
- Superseded by the final read-model run below.

Final local 100-user C4 read-model Locust smoke:

- 8522 total requests
- 0 HTTP failures
- Aggregate P95: 44.2ms
- Aggregate P99: 313.2ms
- `/query` P99: 170ms
- Local C4 100-user smoke passed; production claim still needs 1000-user cluster proof.

## Audit Evidence

Final command:

```bash
.venv/bin/python scripts/audit_investigate.py
```

Final result:

```json
{
  "ok": true,
  "events_checked": 39036,
  "broken_indices": []
}
```

Latest post-C4 targeted health check:

```text
chain_valid=True
status=healthy
chain_length=42085
error_count=0
```

Audit repair note:

- Pre-fix concurrent local profile corrupted the local chain.
- `scripts/audit_rebuild.py --rebuild --preserve-lineage` preserved 38,301 events, corrected 4,525 hashes, and logged a rebuild event.
- Final verification passed after another 100-query profile.

## Validation Campaign Evidence

- `evidence/2026-04-30/prompts_hybrid_freshness_pass.md`
- `evidence/2026-04-30/validation_campaign_stone_integration.md`
- `evidence/2026-04-30/validation_campaign_calibration/VALIDATION_CAMPAIGN_REPORT.md`
- `evidence/2026-04-30/validation_campaign_calibration/03_api_results.jsonl`
- `evidence/2026-04-30/validation_campaign_calibration/08_browser_flow_results.md`
- `evidence/2026-04-30/validation_campaign_calibration/09_audit_chain.md`

Calibration result:

- 20 recorded validation steps.
- Targeted backend tests passed: 34/34.
- API/tier/security calibration passed with raw JSON evidence.
- Frontend build passed after the login health-poll fix.
- Live local browser proof passed after changing login health polling from root `/health` to lightweight `/health/db`.
- No CRITICAL calibration failures found.
- Slow root-health/RAG behavior remains a documented HIGH finding for the next backend performance/retrieval pass.

## Not Yet Final

These are still external or live-stack gates:

- Strict C4 500ms/1000-user cluster Locust proof.
- Deployed-environment browser replay on the target host or cluster.
- Production Qdrant corpus/drift baseline.
- Founder GPG signing ceremony and signed release tag.
