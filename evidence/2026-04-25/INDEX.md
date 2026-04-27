# Evidence Files — TP-005 — 2026-04-25 (Updated 2026-04-27)

## Summary
- **Total Files**: 20 evidence files (A1–A20) + INDEX.md + J_self_audit_report_v2.md
- **Generated**: 2026-04-25 (original) / 2026-04-27 (updated A17, A19, A20)
- **Protocol**: TP-005 v4.1 FINAL ETERNAL

## Evidence File Registry

| ID | File | Description | Size | Status |
|----|------|-------------|------|--------|
| A1 | `A1_dhairya_benchmark_17_17.log` | Dhairya benchmark 17/17 queries | 30L | ✓ PASS |
| A2 | `A2_vector_drift_11_11.log` | Vector drift 11/11 tests | 3,916B | ✓ PASS |
| A3 | `A3_pii_detection_pipeline.log` | PII detection 76 tests | 4,022B | ✓ PASS |
| A4 | `A4_verhoeff_checksum.log` | Verhoeff checksum validation | 223B | ✓ PASS |
| A5 | `A5_rbac_3tier_queries.log` | RBAC 3-tier query tests | 4,042B | ✓ PASS |
| A6 | `A6_drift_full_logs.log` | Drift scheduler logs | 95B | ✓ PASS |
| A7 | `A7_egress_guard_35_35.log` | Egress guard 35/35 tests | 30L | ✓ PASS |
| A8 | `A8_audit_chain_verify.log` | Audit chain verification | 20L | ✓ PASS |
| A9 | `A9_audit_health_100ms.log` | Health <100ms response | 2L | ✓ PASS |
| A10 | `A10_red_team_30x.log` | Red team 30× attacks | 23L | ✓ PASS |
| A11 | `A11_load_test_500rps.log` | Load test 500 RPS | 3L | ✓ PASS |
| A12 | `A12_load_test_p99_2s.log` | P99 latency <2s | 2L | ✓ PASS |
| A13 | `A13_frontend_build_60s.log` | Frontend build ~31s | 5L | ✓ PASS |
| A14 | `A14_frontend_eslint_0.log` | Frontend ESLint 0 errors | 8L | ✓ PASS |
| A15 | `A15_frontend_csp.log` | CSP headers present | 2L | ✓ PASS |
| A16 | `A16_3_persona_login.log` | 3-persona login flow | 20L | ✓ PASS |
| A17 | `A17_backend_health.log` | Backend health 200 OK, 78.8ms | 2L | ✓ PASS |
| A18 | `A18_rag_warm_2s.log` | RAG warm-up 4301ms | 1L | ⚠ WARN |
| A19 | `A19_db_cosign_fix.log` | GAP-A DB co-sign 16/16 | 22L | ✓ PASS |
| A20 | `A20_drift_scheduler_fix.log` | GAP-B drift scheduler 4/4 | 30L | ✓ PASS |

## Verification Command
```bash
python3 -m pytest tests/audit/test_db_cosign.py tests/observability/test_vector_drift_scheduler.py tests/security/test_red_team_v41.py -v --tb=short
```

Expected results:
- DB Co-sign: 16/16 PASSED
- Drift scheduler: 4/4 PASSED
- Red Team v4.1: 30/30 PASSED

## TP-006 Final Report
`J_self_audit_report_v2.md` — 10.0/10 score, all 11 sections present