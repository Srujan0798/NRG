#!/usr/bin/env python3
"""Verify all 20 evidence files exist and are valid."""

import os
from pathlib import Path

EVIDENCE_DIR = Path("evidence/2026-04-25")

FILES = [
    "A1_dhairya_benchmark_17_17.log",
    "A2_vector_drift_11_11.log",
    "A3_pii_detection_pipeline.log",
    "A4_verhoeff_checksum.log",
    "A5_rbac_3tier_queries.log",
    "A6_drift_full_logs.log",
    "A7_egress_guard_35_35.log",
    "A8_audit_chain_verify.log",
    "A9_audit_health_100ms.log",
    "A10_red_team_30x.log",
    "A11_load_test_500rps.log",
    "A12_load_test_p99_2s.log",
    "A13_frontend_build_60s.log",
    "A14_frontend_eslint_0.log",
    "A15_frontend_csp.log",
    "A16_3_persona_login.log",
    "A17_backend_health.log",
    "A18_rag_warm_2s.log",
    "A19_db_cosign_fix.log",
    "A20_drift_scheduler_fix.log",
    "INDEX.md",
]

def verify():
    missing = []
    empty = []
    valid = []

    for f in FILES:
        path = EVIDENCE_DIR / f
        if not path.exists():
            missing.append(f)
        elif path.stat().st_size == 0:
            empty.append(f)
        else:
            valid.append(f)

    print("=" * 60)
    print("EVIDENCE VERIFICATION REPORT")
    print("=" * 60)
    print(f"Total files checked: {len(FILES)}")
    print(f"Valid: {len(valid)}")
    print(f"Missing: {len(missing)}")
    print(f"Empty: {len(empty)}")
    print()

    if valid:
        print("VALID FILES:")
        for f in valid:
            size = (EVIDENCE_DIR / f).stat().st_size
            print(f"  [OK] {f} ({size} bytes)")

    if missing:
        print("\nMISSING FILES:")
        for f in missing:
            print(f"  [!!] {f}")

    if empty:
        print("\nEMPTY FILES:")
        for f in empty:
            print(f"  [--] {f}")

    print()
    if not missing and not empty:
        print("STATUS: PASS - All evidence files present and valid")
        return True
    else:
        print("STATUS: FAIL - Some evidence files missing or empty")
        return False

if __name__ == "__main__":
    success = verify()
    exit(0 if success else 1)
