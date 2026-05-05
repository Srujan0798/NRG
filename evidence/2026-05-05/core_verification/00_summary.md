# Core Verification Report

Date: 2026-05-05
Verifier: Guru (.claude)
Status: PARTIAL — schema and focused Dhairya regression verified; live browser/deployment proof still blocked

---

## 1. db_struct.sql Parity — VERIFIED PASS

Command: `scripts/check_schema_sync.py`
Result: SCHEMA IN SYNC

- db_struct.sql defines 58 tables
- Live PostgreSQL has all 58 tables + 22 application-owned tables
- 7 Dhairya benchmark tables confirmed present
- No blocking drift detected

Evidence: `01_schema_sync.log`

---

## 2. Dhairya Failure Patterns — VERIFIED PASS

Command: `pytest tests/benchmarks/test_dhairya_adversarial.py -v`
Result: 10 passed, 31 deselected

- P1-P7 failure pattern validators all reject documented wrong SQL
- Hall of shame documents all required fields
- Pattern contracts are mirrored in validators

Evidence: `02_dhairya_replay.log`

---

## 3. Dhairya Regression Queries (17 queries) — VERIFIED PASS

Command: `pytest tests/benchmarks/test_dhairya_regression.py -v`
Result: 43 passed in 180.91s

Evidence: `evidence/2026-05-05/dhairya_regression_full/01_full_run.log`

Note: The older broad SQL accuracy run in `03_dhairya_all.log` still contains
database-down failures from a separate command. It is not a replacement for the
focused 43-test Dhairya regression pass above.

---

## 4. Killer Queries K-Q2 / K-Q3 — ASSIGNED TO SHISHYA

Status: Not verified by Guru — assigned to Shishya agent.
Evidence path: `evidence/2026-05-05/killer_queries_fix/`

---

## 5. Core Idea Feature Check — MANUAL VERIFICATION NEEDED

Checked file existence:

| Core Idea Requirement | File/Location | Status |
|----------------------|---------------|--------|
| 5-layer architecture | `src/api/main.py`, `src/query/`, `src/security/` | EXISTS |
| 6-node LangGraph | `src/query/planner.py` or similar | NEEDS CHECK |
| 3 user tiers | `tests/e2e/test_three_killer_queries.py` ROLES dict | EXISTS (researcher/government/industry) |
| Zero-data-leakage | `src/security/`, `tests/security/test_pii_indian.py` | EXISTS |
| Audit chain | `.audit/chain.jsonl`, `scripts/audit_investigate.py` | EXISTS, 282,779 events |
| JWT auth (RS256) | `infrastructure/kong/ssl/jwt_rsa.key` | EXISTS |

FULL VERIFICATION: Requires live browser/API walkthrough against Core_Idea_Clean.md sections 1-2.

---

## GAPS

1. K-Q2/K-Q3 need fresh staging/API proof, including screenshots and SQL traces
2. Core Idea browser walkthrough not done
3. Staging deployment not done (blocked on deployed URLs/credentials)

---

## NEXT ACTIONS

1. Run K-Q2/K-Q3 on a running staging/API stack and save SQL + screenshots
2. Founder provides staging URL for live walkthrough
3. Founder provides deployment/cluster access for external gates
