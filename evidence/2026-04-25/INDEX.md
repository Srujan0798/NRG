# Evidence Files - TP-005 - 2026-04-25

## Evidence Files

| File | Description | Status |
|------|-------------|--------|
| A1_dhairya_benchmark_17_17.log | Dhairya benchmark - 17/17 queries passed | ✓ |
| A2_vector_drift_11_11.log | Vector drift check - 11/11 tests passed | ✓ |
| A3_pii_detection_pipeline.log | PII detection pipeline - 76 tests passed | ✓ |
| A4_verhoeff_checksum.log | Verhoeff checksum validation module | ✓ |
| A5_rbac_3tier_queries.log | RBAC 3-tier query tests | ✓ |
| A6_drift_full_logs.log | Drift scheduler full logs | ✓ |
| A7_egress_guard_35_35.log | Egress guard - 35/35 tests passed | ✓ |
| A8_audit_chain_verify.log | Audit chain verification results | ✓ |
| A9_audit_health_100ms.log | Backend health check - <100ms response | ✓ |
| A10_red_team_30x.log | Red team tests (30x attack vectors) | ✓ |
| A11_load_test_500rps.log | Load test at 500 RPS | ✓ |
| A12_load_test_p99_2s.log | P99 latency from load test | ✓ |
| A13_frontend_build_60s.log | Frontend build - completed in ~31s | ✓ |
| A14_frontend_eslint_0.log | Frontend ESLint - 0 errors | ✓ |
| A15_frontend_csp.log | Content-Security-Policy configuration | ✓ |
| A16_3_persona_login.log | 3-persona login flow tests | ✓ |
| A17_backend_health.log | Backend health endpoint | ✓ |
| A18_rag_warm_2s.log | RAG warm-up timing | ✓ |
| A19_db_cosign_fix.log | Database co-sign fix verification | ✓ |
| A20_drift_scheduler_fix.log | Vector drift scheduler fix | ✓ |

## Summary

- **Total Files**: 20 evidence files + INDEX.md
- **Generated**: 2026-04-25
- **Protocol**: TP-005 v4.1 FINAL ETERNAL

## Verification

Run `python scripts/verify_evidence.py` to verify all files.
