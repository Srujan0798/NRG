# Killer Queries Fix — Assignment A — Evidence Summary
**Date:** 2026-05-05
**Commit:** $(git rev-parse HEAD)

## Status: ALL 3 PASSED

### Test Results
```
tests/e2e/test_three_killer_queries.py::test_killer_query_returns_cited_rows_and_meets_latency[KILLER-01] PASSED
tests/e2e/test_three_killer_queries.py::test_killer_query_returns_cited_rows_and_meets_latency[KILLER-02] PASSED
tests/e2e/test_three_killer_queries.py::test_killer_query_returns_cited_rows_and_meets_latency[KILLER-03] PASSED
3 passed in 11.38s
```

### Latency (NRG_KILLER_QUERY_RUNS=20)
All 3 queries pass with P95 < 4000ms requirement.

## What Was Fixed

The assignment described Dhairya-audit failures (Q5, Q17 for K-02; Q3, Q16 for K-03).
The system has since been repaired via prior work:

1. **K-02 fix:** Schema-aware prompt (`schema_aware_prompt.py:51-57`) now includes
   `_mentions_stage_transition()` guidance requiring `GROUP BY financial_year, stage_of_technology`
   and correct TRL mapping (Lab Validation → Level 4, Market Ready → Level 9).

2. **K-03 fix:** Multi-part guidance in `schema_aware_prompt.py:59-75` covers:
   - `_mentions_grant_patent_efficiency()` → CTE over innovation_grant_from_govt + combined_ipo_patent_data
   - `_mentions_grant_trend()` → year-over-year CTE with self-join
   - Combined_ipo_patent_data.applicants text join pattern included

3. **Earlier fixes (from git history):**
   - Commit `8131bdb9`: trl_stages VIEW migration for safe 62-char table aliasing
   - Commit `5cedd2a2`: Dhairya query benchmark routing fixes
   - Commit `c510ae35`: Canonical trl_stages alias across 17 files

## K-02 SQL (contains required elements ✓)
- `innovations_at_various_stages_of_technology_readiness_level` ✓
- `GROUP BY financial_year` ✓
- Stage transition analysis with bottleneck detection ✓

## K-03 SQL (contains required elements ✓)
- `WITH` (grants CTE, grant_yoy CTE, patents CTE, patent_yoy CTE) ✓
- `innovation_grant_from_govt` ✓
- `combined_ipo_patent_data` ✓
- `HAVING grant_drop_pct < -40 AND patent_growth_pct > 0` ✓

## K-01 SQL (unchanged, still passes ✓)
- `SPLIT_PART` for credit parsing ✓
- `total_credit_score` TEXT field handling ✓
- `AVG` for national average comparison ✓
- `GROUP BY institute` ✓

## Acceptance Criteria Met
- [x] K-02 SQL contains: innovations_at_various_stages_of_technology_readiness_level, GROUP BY, financial_year
- [x] K-03 SQL contains: WITH, innovation_grant_from_govt, combined_ipo_patent_data, HAVING
- [x] Both queries return >= 1 row from local seed data
- [x] P95 latency < 4000ms on local stack
- [x] All 3 killer queries (K-01, K-02, K-03) pass together
- [x] Evidence files created

## No Blockers