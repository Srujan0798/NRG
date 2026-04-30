# NRG — Dhairya SQL Audit Report

**Auditor:** SesDhairya (External Engineer)
**Date:** 2025-04-23
**Questions Tested:** 17
**Product:** National Research Graph — AI Text-to-SQL Pipeline
**Result:** 7/17 correct (41%) — see failure patterns below

---

## Summary

| Status | Code | Count | Rate |
|--------|------|-------|------|
| Correct | xxx | 7 | 41% |
| Format Mismatch | yyy | 2 | 12% |
| Wrong | zzz | 5 | 29% |
| Error | 000 | 3 | 18% |

**Avg Response Time:** ~7.2s (target: <3s — 2.4x over SLO)

---

## 7 Correct Queries (xxx)

| Q# | Question | Key Pattern |
|----|----------|------------|
| 1 | Most intensive innovation curriculum credits in FY 2022-23 | `SPLIT_PART(total_credit_score, ':', 1)` |
| 3 | >50% grant drop YoY | CTE + GROUP BY + self-JOIN |
| 8 | PG courses at IIT Madras (last 3 years) | `GROUP BY` + `IN (...)` |
| 9 | Institute with most PhD courses | `GROUP BY` + `COUNT(*)` + `ORDER BY DESC LIMIT 1` |
| 11 | YoY growth for PG courses — IIT Madras | Window function `LAG()` OVER |
| 13 | Correlation: courses vs startups | Two CTEs + JOIN |
| 17 | Pipeline progression across TRL stages | `GROUP BY financial_year, stage_of_technology` |

---

## 10 Failure Patterns (zzz/yyy/000)

### Q2, Q14 — Format Mismatch (yyy)

| Q# | Issue | Root Cause |
|----|-------|------------|
| 2 | Computed ratio correctly but user wanted per-level counts | Ambiguous "ratio" interpretation |
| 14 | HAVING clause wrongly narrowed to zero-course institutes | Logic error in aggregate filtering |

### Q5, Q7, Q10, Q12, Q16 — Wrong (zzz)

| Q# | Issue | Root Cause |
|----|-------|------------|
| 5 | Returned single stage % instead of all-stage breakdown | "bottlenecks" implied full distribution |
| 7 | Wrong table (`patents_details` vs `combined_ipo_patent_data`), wrong join column (`institute` vs `applicants`), no `status = 'Granted'` filter | Cross-table FK confusion |
| 10 | Switched to `student_strength` table on follow-up instead of staying in `academic_courses_details` | Lost domain context |
| 12 | Queried `phd_students` + `sanctioned_intake` instead of `academic_courses_details` | Cross-domain confusion on follow-up |
| 16 | Query truncated — missing final `HAVING` clause | Truncation mid-generation |

### Q4, Q6, Q15 — Error (000)

| Q# | Issue | Root Cause |
|----|-------|------------|
| 4 | Returned alphabetical DISTINCT instead of top-5 by SUM(grant) | `DISTINCT + ORDER BY` instead of `GROUP BY + ORDER BY SUM()` |
| 6 | Searched for `'TRL 9'` but DB stores `'Level 9'` | No synonym mapping (TRL 9 = Level 9 = Market Ready) |
| 15 | Complete failure — multi-step reasoning required | Complex analytical query too advanced |

---

## Critical Table Names (62-char limit)

```
innovations_at_various_stages_of_technology_readiness_level
```

**Always use exact table name.** AI must NOT abbreviate or alias this table.

---

## Key Schema Values

| Concept | DB Value |
|---------|----------|
| Market Ready | `'Level 9'` (not `'TRL 9'` or `'Market Ready'`) |
| Credit Score Format | `"3:1"` meaning lecture:tutorial credits — parse with `SPLIT_PART(col, ':', 1)` |
| Funding Table | `innovation_grant_from_govt` |
| TRL Table | `innovations_at_various_stages_of_technology_readiness_level` |
| Patent Table | `combined_ipo_patent_data` (status = 'Granted') |
| Courses Table | `academic_courses_details` (level_of_course IN ('UG', 'PhD', 'PG')) |

---

## Pattern Fixes Required

1. **SPLIT_PART parsing** — `SPLIT_PART(col, ':', 1)::double precision` not `CAST(col AS INTEGER)`
2. **Aggregated YoY** — CTE → GROUP BY year → self-JOIN, not row-level comparison
3. **Synonym mapping** — TRL 9 = Level 9 = Market Ready all map to `'Level 9'`
4. **Domain persistence** — Follow-up queries MUST stay in same table domain
5. **HAVING completeness** — Multi-stage queries (WHERE → GROUP → HAVING) must complete all stages
6. **Correct JOIN keys** — `innovation_grant_from_govt.institute` joins to `combined_ipo_patent_data.applicants` not `institute`
7. **GROUP BY aggregation** — `GROUP BY + ORDER BY SUM(col)` not `DISTINCT + ORDER BY col`

---

*Source: docs/reports/SQL_AUDIT_RAW_dhairya.sql (raw audit log)*
