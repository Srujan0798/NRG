# L-1 Final Code Review

**Date:** 2026-04-29 IST
**Scope:** `src/`, `tests/`, `frontend/`
**Method:** Three parallel review passes: Simplicity/DRY, Security/PII, Performance.
**Policy:** Critical issues only; per protocol, findings were recorded in `BACKLOG.md` and not fixed in this pass.

## Summary

Result: release-blocking findings found. Do not cut `v1.0.0-eternal` until these are triaged or explicitly accepted by the founder/security owner.

## Critical Findings

| ID | Severity | Area | Finding | Evidence |
|---|---|---|---|---|
| L1-CR-001 | P0 | Security/PII | PII encryption fails open when `NRG_PII_ENCRYPTION_KEY` is missing or invalid; fallback can use an all-zero key and store plaintext. | `src/security/pii_encryption.py:25`, `src/security/pii_encryption.py:56` |
| L1-CR-002 | P0 | Security/PII | Blocked SQL is stored/logged without redaction; previews can leak passwords, tokens, Aadhaar/PAN, emails, or other PII. | `src/security/query_allowlist.py:56`, `src/security/query_allowlist.py:67`, `src/security/query_allowlist.py:72` |
| L1-CR-003 | P0 | Security/DPDP | DPDP deletion audit logging is broken because `hashlib` is used without import; data deletion can commit before audit logging fails. | `src/security/dpdp_compliance.py:22`, `src/security/dpdp_compliance.py:38`, `src/security/dpdp_compliance.py:93` |
| L1-CR-004 | P0 | Security/Egress | Egress guard fails open if the allowlist file is missing and can return unfiltered schema. | `src/security/egress_guard/__init__.py:53`, `src/security/egress_guard/__init__.py:168` |
| L1-CR-005 | P0 | API/Simplicity | Modular query route can 500 because `src/api/query_helpers.py` references `os.getenv` without importing `os`. | `src/api/query_helpers.py:87`, `src/api/query_helpers.py:292`, `src/api/routes/query.py:136` |
| L1-CR-006 | P0 | API/DRY | Duplicated fast-path logic between `main.py` and `query_helpers.py` has drifted; router path lacks bounded local query branch and loses citation/provenance fields. | `src/api/main.py:734`, `src/api/main.py:784`, `src/api/main.py:947`, `src/api/query_helpers.py:344`, `src/api/query_helpers.py:389` |
| L1-CR-007 | P1 | Performance | Async request handlers call synchronous workflow execution directly; cache misses can block the FastAPI event loop. | `src/api/main.py:2354`, `src/api/main.py:2596`, `src/api/routes/query.py:64`, `src/api/routes/query.py:253` |
| L1-CR-008 | P1 | Performance | `TextToSQLSkill` is cached as a singleton but closed after every request, disposing extractor/sandbox and PostgreSQL engine. | `src/orchestration/nodes/executor.py:55`, `src/orchestration/nodes/executor.py:120`, `src/skills/text_to_sql/skill.py:1542`, `src/skills/text_to_sql/sandbox.py:165` |

## Residual Test Gaps

- Missing tests for missing/invalid PII encryption key fail-closed behavior.
- Missing tests proving blocked-query logs redact PII and secrets.
- Missing tests proving DPDP purge writes a durable audit record.
- Missing tests proving egress allowlist load failure blocks rather than passing through.
- Missing route parity tests between `main.py` and `src/api/routes/query.py`.
- Missing citation/provenance schema assertions for all fast-path responses.
- Missing concurrent `/query` load test for event-loop responsiveness on cache misses.
- Missing pool-lifecycle regression test proving repeated text-to-SQL requests do not dispose/recreate PostgreSQL pools per request.

## Verification Notes

- L-3 schema parity passed: `16 passed in 66.04s`; see `evidence/2026-04-28/schema_parity_check.log`.
- L-5 forbidden vocabulary sweep passed after replacing one active Markdown use of forbidden wording; final log is empty with exit 0.
- L-2 exact full coverage command did not complete; see `evidence/2026-04-28/test_coverage_report.txt`.
- L-4 local performance baseline is blocked by broken Docker/Colima and unavailable PostgreSQL/Qdrant; see `evidence/2026-04-28/perf_baseline_local.txt`.
