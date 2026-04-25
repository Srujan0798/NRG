# TP-005 — Evidence Verification A1–A20

**Owner:** CODER  
**Estimated Duration:** 2–3 hours  
**Blockers:** TP-001, TP-002, TP-003 (must complete first)  
**v4.1 Reference:** Part A — Evidence Files, Part D — Checklist D1–D10, Part H — Benchmarks  

---

## Objective

Verify or create all 20 evidence files (A1–A20) in `evidence/2026-04-25/`. Run all benchmarks and tests to confirm current state. Produce a verification script.

---

## Current State

- Some evidence may exist in `evidence/2026-04-24/`.
- A19 and A20 will be produced by TP-001 and TP-002.
- Many benchmarks already pass (Dhairya 17/17, drift 11/11, egress 35/35).

---

## Fortify Phase (Read & Audit)

1. List current evidence:
   ```bash
   ls -la evidence/2026-04-24/ 2>/dev/null
   ls -la evidence/2026-04-25/ 2>/dev/null
   ```
2. Read v4.1 Part A to confirm the full list of 20 required evidence files.
3. Check which tests/benchmarks exist:
   ```bash
   ls tests/benchmarks/
   ls tests/security/
   ls tests/observability/
   ls tests/api/
   ```

---

## Elevate Phase (Generate & Verify)

### Required Evidence Files

| ID | Name | How to Generate | Target |
|----|------|-----------------|--------|
| A1 | Dhairya benchmark 17/17 | `pytest tests/benchmarks/test_dhairya_regression.py -v` | All pass |
| A2 | Vector drift 11/11 | `pytest tests/observability/test_vector_drift.py -v` | All pass |
| A3 | PII detection pipeline | Run PII tests + sample detection | Shows masking |
| A4 | Verhoeff checksum | Run Verhoeff tests + live demo | Shows validation |
| A5 | RBAC 3-tier screenshots | Document API responses per tier | 3 distinct outputs |
| A6 | Drift detection full logs | From drift test or scheduler | Non-empty logs |
| A7 | Egress guard 35/35 | `pytest tests/security/test_egress_guard.py -v` | All pass |
| A8 | Audit chain verify_chain | `pytest tests/audit/test_audit_chain.py -v` | Pass + valid |
| A9 | Audit health <100ms | `curl -w "%{time_total}" http://localhost:8000/health` | <0.1s |
| A10 | Red Team 30× | From TP-004 | 30/30 executed |
| A11 | Load test 500 req/s | `locust` or `wrk` or Python script | 500+ RPS |
| A12 | Load test p99 <2s | Same load test | p99 < 2.0s |
| A13 | Frontend build <60s | `time npm run build` (frontend/) | <60s |
| A14 | Frontend 0 ESLint errors | `npm run lint` (frontend/) | 0 errors |
| A15 | Frontend CSP headers | `curl -I http://localhost:8000` | CSP present |
| A16 | 3 persona login flow | Document login + query for each tier | 3 success logs |
| A17 | Backend health endpoint | `curl http://localhost:8000/health` | 200 OK |
| A18 | RAG retrieval <2s warm | Time a warm query via API | <2s |
| A19 | GAP-A db cosign fix | From TP-001 | Tests pass |
| A20 | GAP-B drift scheduler | From TP-002 | Scheduler runs |

### For each evidence file:

1. If it already exists in `evidence/2026-04-25/` and is non-empty → verify it.
2. If missing or empty → regenerate it by running the relevant test/command.
3. Write output to `evidence/2026-04-25/AXX_name.log`.

### Verification Script

Create `scripts/verify_evidence.py` that:
- Checks all 20 files exist in `evidence/2026-04-25/`
- Checks each file is non-empty (>100 bytes)
- Prints a pass/fail table
- Exits 0 if all pass, 1 if any fail

---

## Immortalize Phase (Evidence & Commit)

1. Run the verification script:
   ```bash
   python scripts/verify_evidence.py
   ```

2. Create master index:
   ```
   evidence/2026-04-25/INDEX.md
   ```
   Contents: table of all 20 files with size, description, and pass/fail status.

3. Commit with message:
   ```
   chore(audit): v4.1 evidence files A1–A20 + verification script
   ```

---

## Acceptance Criteria

- [ ] All 20 evidence files exist in `evidence/2026-04-25/`
- [ ] Each file is >100 bytes (non-empty)
- [ ] `scripts/verify_evidence.py` passes (exits 0)
- [ ] `evidence/2026-04-25/INDEX.md` exists and lists all 20
- [ ] No files from `evidence/2026-04-24/` were modified
- [ ] Dhairya 17/17 still passes
- [ ] Drift 11/11 still passes
- [ ] Egress 35/35 still passes

---

## Rollback Plan

Evidence files are logs — safe to delete and regenerate. The verification script can be rerun.
