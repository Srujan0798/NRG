# Hall of Shame — NRG Benchmark & Failure Patterns

> This document records failure patterns so they are never repeated.
> It is a learning tool, not a blame tool.

## Pattern 1: Credit Score Parsing Without SPLIT_PART

- **Date:** 2026-04-23
- **Test / Component:** `tests/benchmarks/test_dhairya_regression.py` (Q1)
- **Severity:** Critical
- **Root Cause:** Text-to-SQL used `CAST(total_credit_score AS INTEGER)` instead of parsing the `X:Y` format stored in the column.
- **Impact:** Q1 ("most intensive innovation curriculum") returned wrong institute rankings — credits were being compared as raw strings rather than numeric components.
- **Fix:** `src/skills/text_to_sql/skill.py` updated to emit `SPLIT_PART(total_credit_score, ':', 1)` before numeric aggregation. Commits `sql_audit_fix_branch` and `cc8b5d3`.
- **Prevention:** Schema-aware prompt now explicitly documents the `X:Y` credit format. New test `test_credit_score_parsing` added to `tests/skills/test_text_to_sql.py`.

---

## Pattern 2: TRL Stage String Mismatch

- **Date:** 2026-04-23
- **Test / Component:** `tests/benchmarks/test_dhairya_regression.py` (Q6)
- **Severity:** High
- **Root Cause:** Database stores `"Level 9"` but the LLM searched for `"TRL 9"`. No synonym mapping existed.
- **Impact:** Q6 ("TRL-9 Market Ready innovations at IIT Madras") returned zero results — query generated but returned no rows.
- **Fix:** `src/skills/text_to_sql/sql_examples.py` and `src/skills/text_to_sql/schema_retriever.py` updated to include stage-of-technology synonym set (Level 9 = TRL 9 = Market Ready = TRL9). Schema metadata now expanded.
- **Prevention:** `tests/skills/test_schema_retriever.py` now includes stage synonym recall test.

---

## Pattern 3: YoY Calculation Using Row-Level Instead of Aggregated Values

- **Date:** 2026-04-23
- **Test / Component:** `tests/benchmarks/test_dhairya_regression.py` (Q3, Q11)
- **Severity:** Critical
- **Root Cause:** LLM generated `LAG(amount) OVER (ORDER BY year)` on raw rows instead of CTE-grouped sums. Growth was computed on per-row values, not institutional aggregates.
- **Impact:** Q3 (">50% grant drop YoY") and Q11 ("YoY growth for PG courses") returned incorrect or truncated results.
- **Fix:** Prompt updated to emit explicit CTE scaffolding: `WITH yearly AS (SELECT institute, year, SUM(col) AS total FROM table GROUP BY institute, year) SELECT ... LAG(total) FROM yearly`.
- **Prevention:** Dhairya regression suite now covers YoY queries. Two dedicated tests added for CTE aggregation patterns.

---

## Pattern 4: JOIN Key Mismatch (applicants vs institute)

- **Date:** 2026-04-23
- **Test / Component:** `tests/benchmarks/test_dhairya_regression.py` (Q7)
- **Severity:** High
- **Root Cause:** `innovation_grant_from_govt` and `combined_ipo_patent_data` were joined on `applicants` vs `institute` columns — different semantics. No text normalization applied.
- **Impact:** Q7 ("cost of innovation = grant per patent") returned either zero results or incorrect cross-joins.
- **Fix:** Prompt updated to include join key normalization: `WHERE lower(trim(gov.institute)) = lower(trim(patent.applicants))`. Sandbox validation rejects cross-domain joins without explicit normalization.
- **Prevention:** `tests/skills/test_sandbox.py` includes cross-table join semantic validation.

---

## Pattern 5: ORDER BY Without Aggregation (DISTINCT abuse)

- **Date:** 2026-04-23
- **Test / Component:** `tests/benchmarks/test_dhairya_regression.py` (Q4)
- **Severity:** Medium
- **Root Cause:** LLM generated `SELECT DISTINCT ... ORDER BY SUM(grant_received)` — DISTINCT cannot order by aggregate functions. Correct pattern is `GROUP BY col ORDER BY SUM(val) DESC`.
- **Impact:** Q4 ("top 5 funding agencies by amount") returned alphabetical ordering instead of ranked sums.
- **Fix:** SQL examples in prompt updated to show GROUP BY + ORDER BY + LIMIT pattern. Validator now flags DISTINCT + ORDER BY + aggregate.
- **Prevention:** `tests/benchmarks/test_dhairya_regression.py` Q4 is a permanent regression anchor.

---

## Pattern 6: Multi-Stage Query Truncation (Incomplete HAVING)

- **Date:** 2026-04-23
- **Test / Component:** `tests/benchmarks/test_dhairya_regression.py` (Q14, Q16)
- **Severity:** High
- **Root Cause:** LLM generated `WHERE ... GROUP BY ...` but truncated before the HAVING clause. Q16 had `-- [INCOMPLETE]` marker in output.
- **Impact:** Q14 ("high capex, low innovation courses") and Q16 ("high grants vs low expenditure") returned wrong or empty results.
- **Fix:** Prompt enforces multi-stage completion: all three stages (WHERE → GROUP BY → HAVING) must appear together or the query is rejected by validator.
- **Prevention:** Dhairya suite includes two multi-stage HAVING tests. Validator now rejects truncated SQL.

---

## Pattern 7: Complete Query Generation Failure (Complex Reasoning)

- **Date:** 2026-04-23
- **Test / Component:** `tests/benchmarks/test_dhairya_regression.py` (Q15)
- **Severity:** Medium
- **Root Cause:** Q15 ("rising stars: funding growth vs average") requires multi-step reasoning: compute per-institute growth, compare to mean, rank. LLM could not decompose the steps.
- **Impact:** Q15 returned `Error` — no query generated. The only complete failure in the 17-query Dhairya set.
- **Fix:** Prompt enhanced with explicit step-by-step reasoning framing: "Step 1: compute X. Step 2: compute Y. Step 3: compare." Chain-of-thought examples added for comparative-rank queries.
- **Prevention:** Q15 retained as permanent regression test for complex multi-step query decomposition.

---

## Meta: How to Add a New Pattern

1. Open a PR with the pattern following the template above.
2. Link to the failing test or incident report.
3. Assign to the Backend Agent for review.
4. Ensure the pattern has a corresponding regression test in `tests/benchmarks/test_dhairya_regression.py` before closing the issue.