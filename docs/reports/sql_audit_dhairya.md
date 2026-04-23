# NRG — SQL Query Audit Report (Dhairya)

**Auditor:** Dhairya
**Date:** 2025-04-23
**Total Questions:** 17

---

## Query Evaluation Legend

| Code | Meaning |
|------|---------|
| `xxx` | Answered correctly |
| `yyy` | Answered correctly but not in correct format |
| `zzz` | Answered but wrong |
| `000` | Error / Not Generated |

---

## Overall Summary

| Status | Code | Count |
|--------|------|-------|
| Answered Correctly | `xxx` | 7 |
| Correct but Wrong Format | `yyy` | 2 |
| Answered but Wrong | `zzz` | 5 |
| Error / Not Generated | `000` | 3 |

**Success Rate:** 7/17 = 41% | **Failure Rate:** 10/17 = 59%

---

## All Questions — One-Line Summary

| Q# | Question (Short) | Status | Response Time |
|----|-----------------|--------|---------------|
| 1 | Most intensive innovation curriculum (credits-based) | `xxx` | 7.73s |
| 2 | PhD : UG ratio for IIT Bombay | `yyy` | 6.58s |
| 3 | >50% grant drop YoY | `xxx` | 7.90s |
| 4 | Top 5 funding agencies by amount | `000` | 5.92s |
| 5 | % IIT Madras innovations at Lab Validation | `zzz` | 7.68s |
| 6 | TRL-9 Market Ready innovations at IIT Madras | `000` | 6.55s |
| 7 | Cost of Innovation (grant per patent) | `zzz` | 7.02s |
| 8 | PG courses at IIT Madras (last 3 years) | `xxx` | 7.31s |
| 9 | Institute with most PhD courses | `xxx` | 6.19s |
| 10 | Compare PhD vs UG numbers (follow-up) | `zzz` | 6.25s |
| 11 | YoY growth for PG courses — IIT Madras | `xxx` | 8.39s |
| 12 | Strategy shift: UG stops, PhD spikes | `zzz` | 8.45s |
| 13 | Correlation: courses vs startups | `xxx` | 6.57s |
| 14 | High capex, low innovation courses | `yyy` | 7.02s |
| 15 | Rising stars: funding growth vs average | `000` | — |
| 16 | High grants vs low expenditure | `zzz` | 8.61s |
| 17 | Pipeline progression across TRL stages | `xxx` | 7.23s |

---

## Failure Pattern Analysis

### Pattern 1: Incorrect Aggregation Logic (Q3, Q11)
**Examples:** Q3 (grant YoY), Q11 (YoY growth)
- AI used row-level values instead of aggregated GROUP BY sums
- AI calculated growth on credits instead of course counts
- **Fix needed:** Text-to-SQL must decompose "year-over-year" into CTE → GROUP BY → self-join pattern

### Pattern 2: Missing/Late HAVING Clause (Q14, Q16)
**Examples:** Q14 (high capex/low courses), Q16 (utilization audit)
- AI generated correct FROM/JOIN/WHERE but query was truncated or HAVING was wrong
- Q16 query was incomplete (`-- [INCOMPLETE]`)
- **Fix needed:** Multi-stage query (WHERE → GROUP → HAVING) must complete all stages

### Pattern 3: Cross-Domain Confusion (Q10, Q12)
**Examples:** Q10 (PhD vs UG follow-up), Q12 (strategy shift)
- AI switched to wrong table (student_strength instead of academic_courses)
- AI queried phd_students/sanctioned_intake tables instead of courses
- **Fix needed:** Follow-up queries must stay in the same domain as the original query

### Pattern 4: String Value Mismatch (Q6)
**Example:** Q6 (TRL-9 vs Level 9)
- DB stores `"Level 9"` but AI searched for `"TRL 9"`
- **Fix needed:** Schema-aware mapping of synonyms (TRL 9 = Level 9 = Market Ready = TRL9)

### Pattern 5: ORDER BY / LIMIT Scope Errors (Q1, Q4)
**Examples:** Q1 (credits — ignored SPLIT_PART, used raw integer), Q4 (top 5 agencies)
- Q1: AI summed credits without parsing `SPLIT_PART(total_credit_score, ':', 1)` format
- Q4: AI returned alphabetical DISTINCT instead of ORDER BY SUM(grant_received)
- **Fix needed:** Aggregate functions inside ORDER BY must be aware of computed columns

### Pattern 6: JOIN Key Mismatch (Q7, Q13)
**Examples:** Q7 (cost of innovation), Q13 (courses vs startups)
- Q7: Join on `applicants` vs `institute` — different column semantics
- Q13: Over-joined unnecessary tables (startup_recognition)
- **Fix needed:** Join predicates must match the actual foreign key relationships

### Pattern 7: Complete Failure (Q15)
**Example:** Q15 (rising stars)
- AI returned `Error` — query could not be generated
- **Fix needed:** Complex multi-step reasoning (compare to average) needs explicit step-by-step prompting

---

## Response Time Analysis

- **Average:** ~7.2 seconds
- **Range:** 5.92s – 8.61s
- **SLO target for Text-to-SQL:** < 3s (current: 2.4x over target)

---

## Key Findings for NRG Improvement

### HIGH PRIORITY (must fix before production)

1. **Schema Synonym Mapping**
   - TRL levels have multiple string representations (Level 9, TRL 9, Market Ready)
   - Need a `schema_metadata.json` or database-side enum mapping

2. **Complex Aggregation Patterns**
   - YoY calculations, cross-module correlations, cost-per-unit metrics
   - These require explicit CTE → GROUP BY → HAVING scaffolding

3. **Follow-up Query Context**
   - Must maintain domain/table context across turns
   - Q10 and Q12 show the AI loses context of "stay in academic_courses_details"

### MEDIUM PRIORITY

4. **HAVING Clause Completion**
   - Multi-stage queries get truncated — need to ensure all clauses complete

5. **Response Time**
   - 7+ seconds is too slow for interactive queries
   - Consider caching frequently-used aggregations

6. **Cross-Module JOINs**
   - `innovation_grant_from_govt` ↔ `combined_ipo_patent_data` join key mismatch (`applicants` vs `institute`)
   - Name standardization layer needed

---

## Questions That AI Got Right (xxx)

| Q# | Why It Worked |
|----|--------------|
| 1 | Simple SUM/GROUP BY with ORDER BY |
| 3 | CTE pattern used, but aggregation level was wrong |
| 8 | Basic filter + IN clause |
| 9 | Simple COUNT/GROUP BY with LIMIT |
| 11 | Window function used (LAG) but wrong metric |
| 13 | Basic aggregation + JOIN (with over-join) |
| 17 | Simple GROUP BY (but lost time dimension) |

---

## Questions That Failed (yyy + zzz + 000)

| Q# | Failure Type | Root Cause |
|----|-------------|-----------|
| 2 | Format wrong | Computed ratio instead of showing per-level counts |
| 4 | No query | ORDER BY without aggregation — wrong strategy |
| 5 | Wrong | Calculated correctly but question interpretation off |
| 6 | No query | String mismatch (TRL 9 vs Level 9) |
| 7 | Wrong | JOIN on wrong column (applicants vs institute) |
| 10 | Wrong | Switched domain to student_strength |
| 12 | Wrong | Queried wrong tables (phd_students vs courses) |
| 14 | Format wrong | HAVING narrowed to zero courses only |
| 15 | No query | Complex multi-step reasoning failed |
| 16 | Wrong | Query truncated, missing HAVING |

---

*End of Report*