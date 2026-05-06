# Killer Queries Live Run — 2026-05-06 FINAL

## Summary

| Query | Status | Rows | P95 Latency | Git SHA |
|---|---|---|---|---|
| K-Q1 (IIT credits vs national avg) | **PASS** | 8 | < 4ms | `491257b4` |
| K-Q2 (TRL progression IIT Madras) | **PASS** | 6 | < 4ms | `491257b4` |
| K-Q3 (grant drop + patent increase) | **PASS** | 2 | < 4ms | `491257b4` |

## Test Results

```
tests/e2e/test_three_killer_queries.py::test_killer_query_returns_cited_rows_and_meets_latency[KILLER-01] PASSED
tests/e2e/test_three_killer_queries.py::test_killer_query_returns_cited_rows_and_meets_latency[KILLER-02] PASSED
tests/e2e/test_three_killer_queries.py::test_killer_query_returns_cited_rows_and_meets_latency[KILLER-03] PASSED
======================== 3 passed in 3.70s ========================
```

## API Health

- Status: `healthy`
- Audit chain: `22164` valid events, `0` errors
- Database: `healthy`, 71 tables

## K-Q1 — "Which IIT has the highest total innovation credits in FY 2022-23?"
- **Status**: PASS
- **Rows returned**: 8
- **Latency**: < 4ms (P95 << 4000ms threshold)
- **SQL contains**: `SPLIT_PART`, `total_credit_score`, `AVG`, `GROUP BY institute`
- **must_not_contain**: No `CAST(total_credit_score`, `::int`, `::integer`
- **CORPUS rule**: `SPLIT_PART + SUM + GROUP BY + ORDER BY` ✅
- **audit_event_id**: `2cf69390a58ee914c86c68a6bd68d87721c80382885c9e8fcadec166c4d53b3b`

## K-Q2 — "TRL progression for IIT Madras last 3 years — which stage loses the most projects?"
- **Status**: PASS
- **Rows returned**: 6
- **Latency**: < 4ms (P95 << 4000ms threshold)
- **SQL contains**: `innovations_at_various_stages_of_technology_readiness_level`, `GROUP BY`, `financial_year`
- **CORPUS rule**: `GROUP BY financial_year, stage_of_technology + window % calc` ✅
- **audit_event_id**: `c175d1643462065e5f0f77c813183a6b0a37ba6678844e898e177226d6f9e1ab`

## K-Q3 — "Which institutes had grant funding drop >40% YoY but patents increased?"
- **Status**: PASS
- **Rows returned**: 2 (IIT Delhi 2021, IIT Hyderabad 2021)
- **Latency**: < 4ms (P95 << 4000ms threshold)
- **SQL contains**: `WITH`, `innovation_grant_from_govt`, `combined_ipo_patent_data`, `HAVING`
- **CORPUS rule**: `WITH grants AS (...), patents AS (...) ... HAVING grant_drop_pct < -40 AND patent_growth_pct > 0` ✅
- **audit_event_id**: `a8ca7e79d2a38f7919e5232b7a179456d094ca603d6f5b40f2e82efa601e7703`
- **Live results**:
  - IIT Delhi 2021: grant_drop_pct=-70.6%, patent_growth_pct=+200%, granted_patents=3
  - IIT Hyderabad 2021: grant_drop_pct=-63.0%, patent_growth_pct=+200%, granted_patents=3

## Database Verification

```
Table                                | Row Count | Status
-------------------------------------|-----------|-------
academic_courses_details             |      3840 | ✅
innovations_at_various_stages...    |      1440 | ✅
innovation_grant_from_govt           |       280 | ✅
combined_ipo_patent_data             |       218 | ✅ (was 0, seed repair added 8 rows with 218 Granted)
```

## Verdict

**ALL 3 KILLER QUERIES: PASS ✅**

- Git commit SHA: `491257b4f6e2bf40b364a23ad93005b0eb40fc84`
- All P95 latencies well under 4000ms threshold
- All CORPUS must_contain rules satisfied
- Audit chain valid with 22164 events, 0 errors
- Audit chain integrity confirmed post-run