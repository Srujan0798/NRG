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
| W5 Load/performance | `evidence/2026-04-30/wave5_performance_load_acceptance.md` | LOCAL PASS, C4 external blocker remains |

## Raw API Evidence

- `evidence/2026-04-30/09_tier1_query_response.json`
- `evidence/2026-04-30/10_tier2_query_response.json`
- `evidence/2026-04-30/11_tier3_query_response.json`
- `evidence/2026-04-30/wave3_blocked_query_responses.json`

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

Final local 100-query result:

- 100/100 successful responses
- P50: 1613.59ms
- P95: 2031.49ms
- P99: 2094.72ms
- Throughput: 42.62 qps
- Every successful response included an audit event ID

## Audit Evidence

Final command:

```bash
.venv/bin/python scripts/audit_investigate.py
```

Final result:

```json
{
  "ok": true,
  "events_checked": 38383,
  "broken_indices": []
}
```

Audit repair note:

- Pre-fix concurrent local profile corrupted the local chain.
- `scripts/audit_rebuild.py --rebuild --preserve-lineage` preserved 38,301 events, corrected 4,525 hashes, and logged a rebuild event.
- Final verification passed after another 100-query profile.

## Not Yet Final

These are still external or live-stack gates:

- Strict C4 500ms/1000-user Locust proof.
- Live deployed browser replay after Wave 5.
- Production Qdrant corpus/drift baseline.
- Founder GPG signing ceremony and signed release tag.
