# TP-001 — GAP-A: DB Co-sign Verification

**Owner:** CODER  
**Estimated Duration:** 2–3 hours  
**Blockers:** None  
**v4.1 Reference:** Part B — Mandatory Local Fix A  

---

## Objective

Ensure the DB co-sign module (`src/audit/db_cosign.py`) is fully functional, tested, and verified. If the Postgres trigger is missing, create it. Produce evidence file A19.

---

## Current State

- `src/audit/db_cosign.py` exists (~7,569 bytes).
- `verify_db_cosign()` function exists but is **untested**.
- Postgres trigger status is **unknown** — may or may not exist in migrations.

---

## Fortify Phase (Read & Audit)

1. Read `src/audit/db_cosign.py` fully. Understand:
   - How `verify_db_cosign()` works
   - What database tables it depends on
   - What the expected trigger behavior is
2. Search migrations for any cosign-related trigger:
   ```bash
   grep -r "cosign" db/migrations/ alembic/versions/ 2>/dev/null || echo "No trigger found"
   ```
3. Run existing audit tests to establish baseline:
   ```bash
   python -m pytest tests/audit/ -v --tb=short
   ```
4. Check if `verify_db_cosign()` is called anywhere in production code (it should be).

---

## Elevate Phase (Implement & Fix)

1. **If `verify_db_cosign()` is broken or incomplete:**
   - Fix the logic to correctly verify HMAC signatures on database audit records.
   - Ensure it handles edge cases: empty table, missing signature, tampered row.

2. **If Postgres trigger is missing:**
   - Create the trigger in `db/migrations/VXXX__add_audit_cosign_trigger.sql` (or Alembic equivalent).
   - The trigger must auto-sign audit rows on INSERT using the same HMAC key as `src/audit/__init__.py`.

3. **Write tests** in `tests/audit/test_db_cosign.py` with **minimum** these cases:
   - `test_verify_db_cosign_returns_true_when_valid` — insert valid signed row, verify passes
   - `test_verify_db_cosign_returns_false_when_tampered` — modify signed row, verify fails
   - `test_verify_db_cosign_handles_empty_table` — no rows, returns empty/valid state
   - `test_verify_db_cosign_detects_missing_signature` — row with NULL signature, fails

4. Ensure `pytest tests/audit/test_db_cosign.py -v` passes cleanly.

---

## Immortalize Phase (Evidence & Commit)

1. Create evidence file:
   ```
   evidence/2026-04-25/A19_db_cosign_fix.log
   ```
   Contents must include:
   - `cat src/audit/db_cosign.py | wc -l` (line count)
   - Test output (`pytest tests/audit/test_db_cosign.py -v`)
   - Migration file name if created
   - One-line summary: "GAP-A RESOLVED — DB co-sign verified with N tests"

2. Commit with message:
   ```
   fix(audit): GAP-A db cosign verification + tests
   ```

---

## Acceptance Criteria

- [ ] `pytest tests/audit/test_db_cosign.py -v` passes 4/4 tests minimum
- [ ] Postgres trigger exists in migrations (or was verified to already exist)
- [ ] `verify_db_cosign()` is callable and returns correct boolean
- [ ] Evidence file A19 exists and is non-empty
- [ ] No regressions in `pytest tests/audit/ -v`

---

## Rollback Plan

If the trigger causes INSERT failures:
```sql
DROP TRIGGER IF EXISTS audit_cosign_trigger ON audit_events;
```
