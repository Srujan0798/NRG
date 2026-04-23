# NRG — Text-to-SQL Audit Report

**Auditor:** SesDhairya (External Engineer)
**Date:** 2025-04-23
**Total Questions:** 17
**Product:** National Research Graph (NRG) — AI SQL Generation Pipeline

---

## Evaluation Legend

| Code | Meaning | Description |
|------|---------|-------------|
| `xxx` | Correct | Query returned correct results in correct format |
| `yyy` | Format Mismatch | Query correct but output format didn't match expectation |
| `zzz` | Wrong | Query generated but logic/joins were incorrect |
| `000` | Error | Query generation failed or returned error |

---

## Overall Results

| Status | Code | Count | Rate |
|--------|------|-------|------|
| Correct | `xxx` | 7 | 41% |
| Format Mismatch | `yyy` | 2 | 12% |
| Wrong | `zzz` | 5 | 29% |
| Error | `000` | 3 | 18% |
| **Success Rate** | | **7/17** | **41%** |
| **Failure Rate** | | **10/17** | **59%** |

**Average Response Time:** ~7.2 seconds (range: 5.92s – 8.61s)
**SLO Target:** < 3s (current: 2.4x over target)

---

## Summary Table

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

## Detailed Query Analysis

---

### Q1 — `xxx` — ⏱ 7.73s

**Question:** Which institute offers the most intensive innovation curriculum in FY 2022-23 based on total credits, not just course count?

**Status Reason:** AI summed credits incorrectly — ignored `SPLIT_PART` format; also added `LIMIT 1` without user asking.

**Expected (Actual) Query:**
```sql
SELECT
    institute,
    COUNT(*) AS total_courses,
    SUM(
        SPLIT_PART(total_credit_score, ':', 1)::double precision
    ) AS total_innovation_intensity
FROM academic_courses_details
WHERE financial_year = '2022-23'
GROUP BY institute
ORDER BY total_innovation_intensity DESC;
```

**AI Generated:**
```sql
SELECT "institute",
       SUM(CAST("total_credit_score" AS INTEGER)) AS total_credits
FROM public.academic_courses_details
WHERE "financial_year" = '2022-23'
GROUP BY "institute"
ORDER BY total_credits DESC
LIMIT 1;
```

**Root Cause:** `total_credit_score` uses format `"3:1"` (lecture:tutorial). AI cast directly to integer instead of parsing with `SPLIT_PART`. Also added unwanted `LIMIT 1`.

---

### Q2 — `yyy` — ⏱ 6.58s

**Question:** Show me the ratio of PhD level innovation courses to Undergraduate ones for IIT Bombay.

**Status Reason:** Ratio computed correctly, but user expected per-level counts, not a single ratio value.

**Expected (Actual) Query:**
```sql
SELECT
    level_of_course,
    COUNT(*) as course_count
FROM academic_courses_details
WHERE institute = 'IIT Bombay'
  AND level_of_course IN ('UG', 'PhD')
GROUP BY level_of_course;
```

**AI Generated:**
```sql
SELECT (COUNT(CASE WHEN "level_of_course" = 'PhD' THEN 1 END)::DECIMAL
        / NULLIF(COUNT(CASE WHEN "level_of_course" = 'UG' THEN 1 END), 0))
    AS phd_to_ug_ratio
FROM public.academic_courses_details
WHERE "institute" = 'IIT Bombay';
```

**Root Cause:** Ambiguous question — "ratio" could mean computed ratio OR per-level breakdown. AI chose ratio. Format mismatch only.

---

### Q3 — `xxx` — ⏱ 7.90s

**Question:** Flag any institute where grant funding has dropped by more than 50% year-over-year between 2020-21 to 2021-22.

**Status Reason:** Marked `xxx` but AI used row-level grant comparison instead of yearly aggregated sums — only worked by coincidence.

**Expected (Actual) Query:**
```sql
WITH YearlyGrants AS (
    SELECT
        institute,
        year_of_receiving,
        SUM(grant_received) as total_funding
    FROM innovation_grant_from_govt
    GROUP BY institute, year_of_receiving
)
SELECT
    current_year.institute,
    current_year.year_of_receiving as current_year,
    current_year.total_funding as current_funding,
    prev_year.total_funding as previous_funding,
    ((current_year.total_funding - prev_year.total_funding)
        / prev_year.total_funding::float) * 100 as growth_percentage
FROM YearlyGrants current_year
JOIN YearlyGrants prev_year
    ON current_year.institute = prev_year.institute
    AND prev_year.year_of_receiving = '2020-21'
WHERE current_year.year_of_receiving = '2022-23'
  AND ((current_year.total_funding - prev_year.total_funding)
        / prev_year.total_funding::float) < -0.5;
```

**AI Generated:**
```sql
SELECT ig1.institute, ig1.year_of_receiving AS previous_year,
       ig1.grant_received AS previous_year_grant,
       ig2.year_of_receiving AS current_year,
       ig2.grant_received AS current_year_grant,
       ((ig2.grant_received::decimal / ig1.grant_received::decimal) * 100)
           AS percentage_change
FROM innovation_grant_from_govt ig1
JOIN innovation_grant_from_govt ig2
    ON ig1.institute = ig2.institute
    AND ig1.year_of_receiving::integer = ig2.year_of_receiving::integer - 1
WHERE (ig2.grant_received::decimal / ig1.grant_received::decimal) * 100 < 50;
```

**Root Cause:** Row-level comparison instead of CTE + GROUP BY per year.

---

### Q4 — `000` — ⏱ 5.92s

**Question:** Who are the top 5 unique funding agencies providing grants to us?

**Status Reason:** Complete failure — AI returned alphabetical DISTINCT names instead of top by total funding.

**Expected (Actual) Query:**
```sql
SELECT
    gov_organisation_name,
    COUNT(*) as grant_count,
    SUM(grant_received) as total_amount
FROM innovation_grant_from_govt
GROUP BY gov_organisation_name
ORDER BY total_amount DESC
LIMIT 5;
```

**AI Generated:**
```sql
SELECT DISTINCT "gov_organisation_name"
FROM public.innovation_grant_from_govt
ORDER BY "gov_organisation_name"
LIMIT 5;
```

**Root Cause:** Used `DISTINCT` + `ORDER BY` on raw column instead of `GROUP BY` + `ORDER BY SUM(...)`.

---

### Q5 — `zzz` — ⏱ 7.68s

**Question:** Identify bottlenecks: What percentage of IIT Madras innovations are stuck at 'Lab Validation' (Level 4)?

**Status Reason:** Question interpretation off — user wanted breakdown of ALL stages with percentages, not just Level 4 count.

**Expected (Actual) Query:**
```sql
SELECT
    stage_of_technology,
    COUNT(*) as innovation_count,
    (COUNT(*) * 100.0 / (
        SELECT COUNT(*)
        FROM innovations_at_various_stages_of_technology_readiness_level
        WHERE institute = 'IIT Madras'
    )) as percentage_share
FROM innovations_at_various_stages_of_technology_readiness_level
WHERE institute = 'IIT Madras'
GROUP BY stage_of_technology
ORDER BY innovation_count DESC;
```

**AI Generated:**
```sql
SELECT (COUNT(*) * 100.0 / NULLIF((
    SELECT COUNT(*)
    FROM public.innovations_at_various_stages_of_technology_readiness_level
    WHERE "institute" LIKE '%IIT Madras%'), 0)) AS percentage_stuck_at_lab_validation
FROM public.innovations_at_various_stages_of_technology_readiness_level
WHERE "institute" LIKE '%IIT Madras%'
  AND "stage_of_technology" = 'Lab Validation (Level 4)';
```

**Root Cause:** Question ambiguity — "bottlenecks" implies full distribution analysis, not single stage.

---

### Q6 — `000` — ⏱ 6.55s

**Question:** List all technologies that are 'Market Ready' (TRL 9) for commercialization in IIT Madras.

**Status Reason:** Query generated but TRL value mismatch — DB stores `'Level 9'` but AI searched for `'TRL 9'`.

**Expected (Actual) Query:**
```sql
SELECT
    innovation_name,
    financial_year
FROM innovations_at_various_stages_of_technology_readiness_level
WHERE stage_of_technology = 'Level 9'
  AND institute = 'IIT Madras';
```

**AI Generated:**
```sql
SELECT "innovation_name", "stage_of_technology", "financial_year", "as_on_year"
FROM public."innovations_at_various_stages_of_technology_readiness_level"
WHERE "stage_of_technology" = 'TRL 9'
  AND "institute" = 'IIT Madras';
```

**Root Cause:** No domain synonym mapping — `'TRL 9'`, `'Level 9'`, and `'Market Ready'` all mean the same thing but DB uses `'Level 9'`.

---

### Q7 — `zzz` — ⏱ 7.02s

**Question:** Calculate the 'Cost of Innovation': How much government grant money do we spend for every 1 Patent granted?

**Status Reason:** Oversimplified aggregation; joined on wrong columns (`institute` vs `applicants`); ignored patent `status = 'Granted'` filter.

**Expected (Actual) Query:**
```sql
WITH GrantData AS (
    SELECT institute, SUM(grant_received) as total_money
    FROM innovation_grant_from_govt
    GROUP BY institute
),
PatentData AS (
    SELECT applicants, COUNT(id) as total_patents
    FROM combined_ipo_patent_data
    WHERE status = 'Granted'
    GROUP BY applicants
)
SELECT
    g.institute,
    g.total_money,
    p.total_patents,
    (g.total_money / NULLIF(p.total_patents, 0)) as cost_per_patent
FROM GrantData g
JOIN PatentData p ON g.institute = p.applicants
ORDER BY cost_per_patent ASC;
```

**AI Generated:**
```sql
SELECT SUM("grant_received")::BIGINT / NULLIF(SUM("patents_granted"), 0)
    AS "Cost_of_Innovation"
FROM public."innovation_grant_from_govt" ig
JOIN public."patents_details" pd
    ON ig."institute" = pd."institute"
    AND ig."year_of_receiving" = pd."financial_year";
```

**Root Cause:** Wrong table (`patents_details` vs `combined_ipo_patent_data`), wrong join column (`applicants` vs `institute`), no `status = 'Granted'` filter.

---

### Q8 — `xxx` — ⏱ 7.31s

**Question:** Show me all PG innovation courses at IIT Madras for the last 3 years starting from FY 2021-22.

**Status Reason:** Output broader than required but logically correct.

**Expected (Actual) Query:**
```sql
SELECT title_of_course, financial_year, total_credit_score
FROM academic_courses_details
WHERE institute = 'IIT Madras'
  AND level_of_course = 'PG'
  AND financial_year IN ('2021-22', '2022-23', '2023-24');
```

**AI Generated:**
```sql
SELECT "financial_year", "title_of_course", "course_code", "type_of_course",
       "level_of_course", "course_offering_department", "total_credit_score",
       "institute", "as_on_year"
FROM public."academic_courses_details"
WHERE "level_of_course" = 'PG'
  AND "institute" LIKE '%IIT Madras%'
  AND "financial_year" IN ('2021-22', '2022-23', '2023-24');
```

**Root Cause:** Returned extra columns but correct. Used `LIKE '%IIT Madras%'` which is actually more robust.

---

### Q9 — `xxx` — ⏱ 6.19s

**Question:** Which institute has the most PhD courses?

**Status Reason:** Correct aggregation and ordering.

**Expected (Actual) Query:**
```sql
SELECT institute, COUNT(*) as phd_course_count
FROM academic_courses_details
WHERE level_of_course = 'PhD'
GROUP BY institute
ORDER BY phd_course_count DESC
LIMIT 1;
```

**AI Generated:**
```sql
SELECT "institute",
       COUNT(DISTINCT "title_of_course") AS phd_course_count
FROM public.academic_courses_details
WHERE "level_of_course" = 'PhD'
GROUP BY "institute"
ORDER BY phd_course_count DESC
LIMIT 1;
```

**Root Cause:** None — query correct. Used `COUNT(DISTINCT title_of_course)` which is arguably better than `COUNT(*)`.

---

### Q10 — `zzz` — ⏱ 6.25s

**Question:** How does that compare to their UG numbers? *(Contextual Follow-up)*

**Status Reason:** AI switched domain to `student_strength` table instead of staying in `academic_courses_details`.

**Expected (Actual) Query:**
```sql
SELECT level_of_course, COUNT(*) as course_count
FROM academic_courses_details
WHERE institute = 'IIT Hyderabad'
GROUP BY level_of_course;
```

**AI Generated:**
```sql
SELECT "program", "male_students", "female_students", "total_students",
       "within_state", "outside_state", "outside_country",
       "economically_backward", "socially_challenged",
       "reimbursed_by_government", "reimbursed_by_institution",
       "reimbursed_by_private", "not_reimbursed", "as_on_year"
FROM public.actual_student_strength
WHERE "institute" LIKE '%IIT Hyderabad%'
  AND "program" LIKE '%UG%';
```

**Root Cause:** No follow-up context tracking — AI lost track of previous query domain (courses vs students).

---

### Q11 — `xxx` — ⏱ 8.39s

**Question:** Identify growth trends: Calculate Year-Over-Year growth for PG courses in IIT Madras.

**Status Reason:** Marked `xxx` but AI calculated growth on credits, not course counts.

**Expected (Actual) Query:**
```sql
WITH YearlyData AS (
    SELECT financial_year, COUNT(*) as course_count
    FROM academic_courses_details
    WHERE institute = 'IIT Madras' AND level_of_course = 'PG'
    GROUP BY financial_year
)
SELECT
    t1.financial_year as current_year,
    t1.course_count as current_count,
    t2.course_count as prev_count,
    ((t1.course_count - t2.course_count)::float / t2.course_count) * 100 as growth_rate
FROM YearlyData t1
JOIN YearlyData t2 ON t1.financial_year > t2.financial_year
ORDER BY t1.financial_year DESC;
```

**AI Generated:**
```sql
SELECT "financial_year", "total_credit_score",
       LAG("total_credit_score") OVER (ORDER BY "financial_year")
           AS previous_year_credit_score,
       (CAST("total_credit_score" AS NUMERIC)
        - CAST(LAG("total_credit_score") OVER (ORDER BY "financial_year") AS NUMERIC))
       / NULLIF(CAST(LAG("total_credit_score") OVER (ORDER BY "financial_year") AS NUMERIC), 0) * 100
       AS year_over_year_growth
FROM "academic_courses_details"
WHERE "level_of_course" = 'PG'
  AND "institute" = 'IIT Madras'
ORDER BY "financial_year";
```

**Root Cause:** Used window function on `total_credit_score` instead of `COUNT(*)` for course count growth. Only correct by coincidence.

---

### Q12 — `zzz` — ⏱ 8.45s

**Question:** Detect Strategy Shift: Institute stops UG but spikes in PhD in IIT Madras.

**Status Reason:** AI queried `phd_students` and `sanctioned_intake` tables instead of `academic_courses_details`.

**Expected (Actual) Query:**
```sql
SELECT financial_year,
    SUM(CASE WHEN level_of_course = 'UG' THEN 1 ELSE 0 END) as ug_count,
    SUM(CASE WHEN level_of_course = 'PhD' THEN 1 ELSE 0 END) as phd_count
FROM academic_courses_details
WHERE institute = 'IIT Madras'
GROUP BY financial_year
ORDER BY financial_year;
```

**AI Generated:**
```sql
SELECT phd."institute" AS institute_name,
       phd."financial_year" AS phd_financial_year,
       SUM(phd."total") AS total_phd_students,
       ug."financial_year" AS ug_financial_year,
       SUM(ug."seats") AS total_ug_seats
FROM public.phd_students phd
LEFT JOIN public.sanctioned_intake ug
    ON phd."institute" = ug."institute"
    AND phd."financial_year" = ug."financial_year"
WHERE phd."institute" = 'IIT Madras'
GROUP BY phd."institute", phd."financial_year", ug."financial_year"
ORDER BY phd."financial_year";
```

**Root Cause:** Cross-domain confusion — followed up on courses query but switched to student enrollment tables.

---

### Q13 — `xxx` — ⏱ 6.57s

**Question:** Correlation: Innovation Courses vs. Startups Incubated (Cross-Module).

**Status Reason:** Over-joined extra tables but core correlation logic present.

**Expected (Actual) Query:**
```sql
WITH CourseData AS (
    SELECT institute, COUNT(*) as total_courses
    FROM academic_courses_details
    GROUP BY institute
),
StartupData AS (
    SELECT institute, COUNT(*) as total_startups
    FROM incubation_details
    GROUP BY institute
)
SELECT c.institute, c.total_courses, s.total_startups
FROM CourseData c
JOIN StartupData s ON c.institute = s.institute;
```

**AI Generated:**
```sql
SELECT acd.institute AS institute_name,
       COUNT(DISTINCT acd.id) AS total_innovation_courses,
       COUNT(DISTINCT sr.id) AS total_startups_incubated
FROM public.academic_courses_details acd
LEFT JOIN public.incubation_details id ON acd.institute = id.institute
LEFT JOIN public.startup_recognition sr ON acd.institute = sr.institute
GROUP BY acd.institute
ORDER BY institute_name;
```

**Root Cause:** Extra unnecessary joins but functional. Could be simplified.

---

### Q14 — `yyy` — ⏱ 7.02s

**Question:** Gap Analysis: High Capital Expenses but Low Innovation Courses in FY 2023-24.

**Status Reason:** Logic acceptable but `HAVING` clause incorrectly narrowed scope to zero-course institutes only.

**Expected (Actual) Query:**
```sql
SELECT
    c.institute,
    COUNT(c.id) as course_count,
    SUM(f.capital_assets) as total_capital_expense
FROM academic_courses_details c
JOIN financial_expenses_capital f
    ON c.institute = f.institute AND c.financial_year = f.financial_year
WHERE c.financial_year = '2023-24'
GROUP BY c.institute
ORDER BY total_capital_expense DESC, course_count ASC;
```

**AI Generated:**
```sql
SELECT fc."institute", fc."financial_year",
       SUM(fc."library" + fc."equipment" + fc."workshops" + fc."capital_assets")
           AS total_capital_expenses,
       COUNT(acd."id") AS total_innovation_courses
FROM public.financial_expenses_capital fc
LEFT JOIN public.academic_courses_details acd
    ON fc."institute" = acd."institute"
    AND fc."financial_year" = acd."financial_year"
WHERE fc."financial_year" = '2023-24'
GROUP BY fc."institute", fc."financial_year"
HAVING SUM(fc."library" + fc."equipment" + fc."workshops" + fc."capital_assets") > 0
   AND COUNT(acd."id") = 0;
```

**Root Cause:** `HAVING COUNT(acd."id") = 0` excludes institutes with any courses — should show all with high capex, low courses.

---

### Q15 — `000` — ⏱ —

**Question:** Rising Stars: Institutes growing funding while the average declines.

**Status Reason:** AI failed to generate any query — returned `Error`.

**Expected (Actual) Query:**
```sql
SELECT institute, SUM(grant_received) as total_funding
FROM innovation_grant_from_govt
WHERE as_on_year = '2024'
GROUP BY institute
ORDER BY total_funding DESC;
```

**AI Generated:**
```
Error
```

**Root Cause:** Complex multi-step reasoning required (compare individual growth to global average). No query generated.

---

### Q16 — `zzz` — ⏱ 8.61s

**Question:** Utilization Audit: High Grants vs Low Expenditure.

**Status Reason:** Query truncated — missing final `HAVING` clause. Completed correctly but incomplete.

**Expected (Actual) Query:**
```sql
SELECT
    g.institute,
    SUM(g.grant_received) as grants_received,
    SUM(e.salaries + e.maintenance + e.seminars) as operational_expenses
FROM innovation_grant_from_govt g
JOIN financial_expenses_operational e ON g.institute = e.institute
WHERE g.as_on_year = '2024' AND e.as_on_year = '2023'
GROUP BY g.institute
HAVING SUM(g.grant_received) > (SUM(e.salaries + e.maintenance + e.seminars) * 2);
```

**AI Generated:**
```sql
SELECT ig."institute", SUM(ig."grant_received") AS total_grants_received,
       SUM(fe."salaries" + fe."maintenance" + fe."seminars") AS total_operational_expenditure,
       SUM(fc."library" + fc."equipment" + fc."workshops" + fc."capital_assets")
           AS total_capital_expenditure,
       (SUM(fe."salaries" + fe."maintenance" + fe."seminars")
        + SUM(fc."library" + fc."equipment" + fc."workshops" + fc."capital_assets"))
           AS total_expenditure
FROM public."innovation_grant_from_govt" ig
LEFT JOIN public."financial_expenses_operational" fe
    ON ig."institute" = fe."institute" AND ig."as_on_year" = fe."as_on_year"
LEFT JOIN public."financial_expenses_capital" fc
    ON ig."institute" = fc."institute"
-- [INCOMPLETE — missing HAVING / audit condition]
```

**Root Cause:** Query generation truncated mid-clause. No HAVING condition applied.

---

### Q17 — `xxx` — ⏱ 7.23s

**Question:** Pipeline Progression: Are we moving from Low TRL to High TRL?

**Status Reason:** Marked `xxx` but lost time dimension — only aggregated by stage, not by year+stage.

**Expected (Actual) Query:**
```sql
SELECT financial_year, stage_of_technology, COUNT(*) as project_count
FROM innovations_at_various_stages_of_technology_readiness_level
GROUP BY financial_year, stage_of_technology
ORDER BY financial_year, stage_of_technology;
```

**AI Generated:**
```sql
SELECT "stage_of_technology", COUNT(*) AS "count_of_innovations"
FROM public.innovations_at_various_stages_of_technology_readiness_level
GROUP BY "stage_of_technology"
ORDER BY "stage_of_technology" ASC;
```

**Root Cause:** Omitted `financial_year` from GROUP BY — loses time dimension needed for trend analysis.

---

## Failure Pattern Analysis

### Pattern 1: Incorrect Aggregation Logic — Q3, Q11
- AI used row-level values instead of aggregated `GROUP BY` sums
- AI calculated growth on credits instead of course counts
- **Fix:** Text-to-SQL must decompose "year-over-year" into CTE → GROUP BY → self-join pattern

### Pattern 2: Missing/Late HAVING Clause — Q14, Q16
- AI generated correct FROM/JOIN/WHERE but query was truncated or HAVING was wrong
- Q16 query was completely truncated (`-- [INCOMPLETE]`)
- **Fix:** Multi-stage query (WHERE → GROUP → HAVING) must complete all stages; add query completeness validator

### Pattern 3: Cross-Domain Confusion — Q10, Q12
- AI switched to wrong table on follow-up (student_strength instead of academic_courses)
- AI queried phd_students/sanctioned_intake instead of academic_courses_details
- **Fix:** Follow-up queries must maintain same domain/table as original query

### Pattern 4: String Value Mismatch — Q6
- DB stores `"Level 9"` but AI searched for `"TRL 9"`
- **Fix:** Schema-aware synonym mapping (TRL 9 = Level 9 = Market Ready = TRL9)

### Pattern 5: ORDER BY / LIMIT Scope Errors — Q1, Q4
- Q1: AI summed credits without parsing `SPLIT_PART` format
- Q4: AI returned alphabetical DISTINCT instead of ORDER BY SUM(grant_received)
- **Fix:** Aggregate functions inside ORDER BY must use computed columns; enforce correct LIMIT use

### Pattern 6: JOIN Key Mismatch — Q7, Q13
- Q7: Join on `applicants` vs `institute` — different column semantics
- Q13: Over-joined unnecessary tables (startup_recognition)
- **Fix:** Join predicates must match actual FK relationships; avoid extra tables

### Pattern 7: Complete Failure — Q15
- AI returned `Error` — multi-step reasoning (compare to average) too complex
- **Fix:** Explicit step-by-step prompting for complex analytical queries

---

## Response Time Analysis

| Metric | Value |
|--------|-------|
| Average | ~7.2s |
| Minimum | 5.92s |
| Maximum | 8.61s |
| SLO Target | < 3s |
| Over Target By | 2.4x |

**Recommendation:** Cache frequently-used aggregations; optimize schema-only extraction; consider async query execution.

---

*End of Report — SesDhairya — 2025-04-23*
