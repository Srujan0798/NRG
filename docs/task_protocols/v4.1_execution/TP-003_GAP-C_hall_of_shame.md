# TP-003 — GAP-C: HALL_OF_SHAME.md

**Owner:** SECURITY  
**Estimated Duration:** 1–2 hours  
**Blockers:** None  
**v4.1 Reference:** Part B — Mandatory Local Fix C  

---

## Objective

Document exactly 7 Dhairya benchmark failure patterns in `HALL_OF_SHAME.md` at the project root. Each pattern must include date, root cause, fix, and prevention. This is a **learning document**, not a blame document.

---

## Current State

- `HALL_OF_SHAME.md` **does not exist**.
- Dhairya benchmark tests exist in `tests/benchmarks/test_dhairya_regression.py`.
- Historical failures may be in git history, logs, or previous evidence.

---

## Fortify Phase (Read & Audit)

1. Read `tests/benchmarks/test_dhairya_regression.py` — understand the 17 queries.
2. Search git history for benchmark failures:
   ```bash
   git log --grep="Dhairya\|benchmark\|regression" --oneline -20
   ```
3. Search logs for past failures:
   ```bash
   grep -r "FAILED\|Error\|fail" logs/ 2>/dev/null | head -50
   ```
4. Check if any previous `HALL_OF_SHAME.md` or similar doc exists:
   ```bash
   find . -name "*shame*" -o -name "*failure*" -o -name "*regression*" 2>/dev/null | grep -v node_modules | grep -v .venv
   ```
5. Identify 7 distinct failure patterns. If fewer than 7 real failures exist, supplement with **known vulnerability patterns** that were caught before reaching production (e.g., the ScoredPoint bug, the health check hang, etc.).

---

## Elevate Phase (Implement)

1. Create `HALL_OF_SHAME.md` at the **project root** (`/Users/srujansai/Desktop/NRG/HALL_OF_SHAME.md`).
2. Use this exact structure:

```markdown
# Hall of Shame — NRG Benchmark & Failure Patterns

> This document records failure patterns so they are never repeated.
> It is a learning tool, not a blame tool.

## Pattern 1: [Short Name]
- **Date:** YYYY-MM-DD
- **Test / Component:** `test_name` or `component.py`
- **Severity:** Critical / High / Medium
- **Root Cause:** What exactly went wrong (1–2 sentences)
- **Impact:** What broke or what data was at risk
- **Fix:** How it was fixed (commit hash if known)
- **Prevention:** What test, guard, or process now prevents this

---

## Pattern 2: ...

(repeat for exactly 7 patterns)

---

## Meta: How to Add a New Pattern

1. Open a PR with the pattern following the template above.
2. Link to the failing test or incident report.
3. Assign to the Security agent for review.
```

3. The 7 patterns **must** include (if applicable):
   - The `ScoredPoint.score` vs `vector_score` RAG bug (fixed 2026-04-25)
   - The health check `verify_chain()` hang (fixed 2026-04-25)
   - The embedder model reload per query (fixed 2026-04-25)
   - At least 1 SQL injection near-miss or test failure
   - At least 1 PII detection false negative or bypass
   - At least 1 RBAC escalation attempt (from red team or test)
   - At least 1 vector drift false negative or latency spike

4. If real historical data is sparse, document the **patterns that the Red Team tests are designed to catch** — but mark them as "Prevented — caught by test".

---

## Immortalize Phase (Evidence)

1. Evidence is the file itself:
   ```
   HALL_OF_SHAME.md
   ```

2. Verify:
   ```bash
   grep -c "^## Pattern" HALL_OF_SHAME.md
   ```
   Must return **7**.

3. Commit with message:
   ```
   docs(security): GAP-C HALL_OF_SHAME.md — 7 failure patterns
   ```

---

## Acceptance Criteria

- [ ] `HALL_OF_SHAME.md` exists at project root
- [ ] Contains exactly 7 patterns (`grep -c "^## Pattern"` returns 7)
- [ ] Each pattern has: Date, Test/Component, Severity, Root Cause, Impact, Fix, Prevention
- [ ] At least 3 patterns reference real fixes from 2026-04-25
- [ ] File is valid markdown (no broken links, renders correctly)
- [ ] No sensitive data (passwords, tokens, real PII) in the document

---

## Rollback Plan

Delete the file. It is a standalone documentation file with no runtime impact.
