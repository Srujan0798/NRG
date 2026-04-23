sesDhairya`s report:

Answered correctly (xxx)
Answered correctly but not in correct format (yyy)
Answered but wrong (zzz)
Error (000)


Which institute offers the most intensive innovation curriculum in FY - 2022-23 based on total credits, not just course count?" xxx

Actual quarry. 

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


AI generated

SELECT "institute", SUM(CAST("total_credit_score" AS INTEGER)) AS total_credits FROM public.academic_courses_details WHERE "financial_year" = '2022-23' GROUP BY "institute" ORDER BY total_credits DESC LIMIT 1;

Show me the ratio of PhD level innovation courses to Undergraduate ones for IIT Bombay. yyy

Actual quarry. 

SELECT 
    level_of_course, 
    COUNT(*) as course_count
FROM 
    academic_courses_details
WHERE 
    institute = 'IIT Bombay'
    AND level_of_course IN ('UG', 'PhD') -- Adjust values based on actual data
GROUP BY 
    level_of_course;



AI generated
SELECT (COUNT(CASE WHEN "level_of_course" = 'PhD' THEN 1 END)::DECIMAL / NULLIF(COUNT(CASE WHEN "level_of_course" = 'UG' THEN 1 END), 0)) AS phd_to_ug_ratio FROM public.academic_courses_details WHERE "institute" = 'IIT Bombay';


Flag any institute where grant funding has dropped by more than 50% year-over-year between 2020-2021 to 2021-22. xxx

Actual quarry. 

WITH YearlyGrants AS (
    SELECT 
        institute, 
        year_of_receiving, 
        SUM(grant_received) as total_funding
    FROM 
        innovation_grant_from_govt
    GROUP BY 
        institute, year_of_receiving
)
SELECT 
    current_year.institute,
    current_year.year_of_receiving as current_year,
    current_year.total_funding as current_funding,
    prev_year.total_funding as previous_funding,
    ((current_year.total_funding - prev_year.total_funding) / prev_year.total_funding::float) * 100 as growth_percentage
FROM 
    YearlyGrants current_year
JOIN 
    YearlyGrants prev_year ON current_year.institute = prev_year.institute 
    AND prev_year.year_of_receiving = '2020-21' -- Logic to define previous year
WHERE 
    current_year.year_of_receiving = '2022-23'
    AND ((current_year.total_funding - prev_year.total_funding) / prev_year.total_funding::float) < -0.5; -- Filter for >50% drop


AI generated
SELECT ig1.institute, ig1.year_of_receiving AS previous_year, ig1.grant_received AS previous_year_grant, ig2.year_of_receiving AS current_year, ig2.grant_received AS current_year_grant, ((ig2.grant_received::decimal / ig1.grant_received::decimal) * 100) AS percentage_change FROM innovation_grant_from_govt ig1 JOIN innovation_grant_from_govt ig2 ON ig1.institute = ig2.institute AND ig1.year_of_receiving::integer = ig2.year_of_receiving::integer - 1 WHERE (ig2.grant_received::decimal / ig1.grant_received::decimal) * 100 < 50;

Who are the top 5 unique funding agencies providing grants to us? 000

Actual quarry. 

SELECT 
    gov_organisation_name, 
    COUNT(*) as grant_count, 
    SUM(grant_received) as total_amount
FROM 
    innovation_grant_from_govt
GROUP BY 
    gov_organisation_name
ORDER BY 
    total_amount DESC
LIMIT 5;

AI generated
SELECT DISTINCT "gov_organisation_name" FROM public.innovation_grant_from_govt ORDER BY "gov_organisation_name" LIMIT 5;

Identify bottlenecks: What percentage of IIT Madras innovations are stuck at 'Lab Validation' (Level 4)? zzz

Actual quarry. 

SELECT 
    stage_of_technology,
    COUNT(*) as innovation_count,
    (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM innovations_at_various_stages_of_technology_readiness_level WHERE institute = 'IIT Madras')) as percentage_share
FROM 
    innovations_at_various_stages_of_technology_readiness_level
WHERE 
    institute = 'IIT Madras'
GROUP BY 
    stage_of_technology
ORDER BY 
    innovation_count DESC;


AI generated
SELECT (COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM public.innovations_at_various_stages_of_technology_readiness_level WHERE "institute" LIKE '%IIT Madras%'), 0)) AS percentage_stuck_at_lab_validation FROM public.innovations_at_various_stages_of_technology_readiness_level WHERE "institute" LIKE '%IIT Madras%' AND "stage_of_technology" = 'Lab Validation (Level 4)';

List all technologies that are 'Market Ready' (TRL 9) for commercialization in IIT Madras 000

Actual quarry. 

SELECT 
    innovation_name, 
    financial_year
FROM 
    innovations_at_various_stages_of_technology_readiness_level
WHERE 
    stage_of_technology = 'Level 9' -- Or equivalent string in DB
    AND institute = 'IIT Madras';


AI generated
SELECT "innovation_name", "stage_of_technology", "financial_year", "as_on_year" FROM public."innovations_at_various_stages_of_technology_readiness_level" WHERE "stage_of_technology" = 'TRL 9' AND "institute" = 'IIT Madras';


Calculate the 'Cost of Innovation': How much government grant money do we spend for every 1 Patent granted ? zzz

Actual quarry. 

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
FROM 
    GrantData g
JOIN 
    PatentData p ON g.institute = p.applicants -- Requires name standardization
ORDER BY 
    cost_per_patent ASC; -- Lower is better (more efficient)


AI generated
SELECT SUM("grant_received")::BIGINT / NULLIF(SUM("patents_granted"), 0) AS "Cost_of_Innovation" FROM public."innovation_grant_from_govt" ig JOIN public."patents_details" pd ON ig."institute" = pd."institute" AND ig."year_of_receiving" = pd."financial_year";


Show me all PG innovation courses at IIT Madras for the last 3 years starting from fy 2021-22. xxx

Actual quarry. 

SELECT title_of_course, financial_year, total_credit_score
FROM academic_courses_details
WHERE institute = 'IIT Madras'
  AND level_of_course = 'PG' -- Adjust 'PG' to match exact DB string (e.g., 'Post Graduate')
  AND financial_year IN ('2021-22', '2023-34', '2022-23');


AI generated
SELECT "financial_year", "title_of_course", "course_code", "type_of_course", "level_of_course", "course_offering_department", "total_credit_score", "institute", "as_on_year" FROM public."academic_courses_details" WHERE "level_of_course" = 'PG' AND "institute" LIKE '%IIT Madras%' AND "financial_year" IN ('2021-22', '2022-23', '2023-24');


"Which institute has the most PhD courses?" xxx

Actual quarry. 

SELECT institute, COUNT(*) as phd_course_count
FROM academic_courses_details
WHERE level_of_course = 'PhD'
GROUP BY institute
ORDER BY phd_course_count DESC
LIMIT 1;

AI generated
SELECT "institute", COUNT(DISTINCT "title_of_course") AS phd_course_count FROM public.academic_courses_details WHERE "level_of_course" = 'PhD' GROUP BY "institute" ORDER BY phd_course_count DESC LIMIT 1;



"How does that compare to their UG numbers?" (Contextual Follow-up) zzz

Actual quarry. 

SELECT level_of_course, COUNT(*) as course_count
FROM academic_courses_details
WHERE institute = ‘IIT Hydrabad’
GROUP BY level_of_course;


AI generated
SELECT "program", "male_students", "female_students", "total_students", "within_state", "outside_state", "outside_country", "economically_backward", "socially_challenged", "reimbursed_by_government", "reimbursed_by_institution", "reimbursed_by_private", "not_reimbursed", "as_on_year" FROM public.actual_student_strength WHERE "institute" LIKE '%IIT Hyderabad%' AND "program" LIKE '%UG%';


Identify growth trends: Calculate Year-Over-Year growth for PG courses in IIT Madras. xxx

Actual quarry. 

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
JOIN YearlyData t2 ON t1.financial_year > t2.financial_year -- Simplified logic; ideally join on specific previous year string
ORDER BY t1.financial_year DESC;


AI generated
SELECT "financial_year", "total_credit_score", LAG("total_credit_score") OVER (ORDER BY "financial_year") AS previous_year_credit_score, (CAST("total_credit_score" AS NUMERIC) - CAST(LAG("total_credit_score") OVER (ORDER BY "financial_year") AS NUMERIC)) / NULLIF(CAST(LAG("total_credit_score") OVER (ORDER BY "financial_year") AS NUMERIC), 0) * 100 AS year_over_year_growth FROM "academic_courses_details" WHERE "level_of_course" = 'PG' AND "institute" = 'IIT Madras' ORDER BY "financial_year";

Detect Strategy Shift: Institute stops UG but spikes in PhD in IIT Madras.

Actual quarry. 

SELECT financial_year,
    SUM(CASE WHEN level_of_course = 'UG' THEN 1 ELSE 0 END) as ug_count,
    SUM(CASE WHEN level_of_course = 'PhD' THEN 1 ELSE 0 END) as phd_count
FROM academic_courses_details
WHERE institute = 'IIT Madras'
GROUP BY financial_year
ORDER BY financial_year;

AI generated
SELECT phd."institute" AS institute_name, phd."financial_year" AS phd_financial_year, SUM(phd."total") AS total_phd_students, ug."financial_year" AS ug_financial_year, SUM(ug."seats") AS total_ug_seats FROM public.phd_students phd LEFT JOIN public.sanctioned_intake ug ON phd."institute" = ug."institute" AND phd."financial_year" = ug."financial_year" WHERE phd."institute" = 'IIT Madras' GROUP BY phd."institute", phd."financial_year", ug."financial_year" ORDER BY phd."financial_year";

Correlation: Innovation Courses vs. Startups Incubated (Cross-Module). xxx

Actual quarry. 

WITH CourseData AS (
    SELECT institute, COUNT(*) as total_courses 
    FROM academic_courses_details GROUP BY institute
),
StartupData AS (
    SELECT institute, COUNT(*) as total_startups 
    FROM incubation_details -- Using incubation units as proxy for startups
    GROUP BY institute
)
SELECT c.institute, c.total_courses, s.total_startups
FROM CourseData c
JOIN StartupData s ON c.institute = s.institute;


AI generated
SELECT acd.institute AS institute_name, COUNT(DISTINCT acd.id) AS total_innovation_courses, COUNT(DISTINCT sr.id) AS total_startups_incubated FROM public.academic_courses_details acd LEFT JOIN public.incubation_details id ON acd.institute = id.institute LEFT JOIN public.startup_recognition sr ON acd.institute = sr.institute GROUP BY acd.institute ORDER BY institute_name;

Gap Analysis: High Capital Expenses but Low Innovation Courses in FY 2023-24 yyy

Actual quarry. 

SELECT 
    c.institute, 
    COUNT(c.id) as course_count, 
    SUM(f.capital_assets) as total_capital_expense
FROM academic_courses_details c
JOIN financial_expenses_capital f ON c.institute = f.institute AND c.financial_year = f.financial_year
WHERE c.financial_year = '2023-24'
GROUP BY c.institute
ORDER BY total_capital_expense DESC, course_count ASC;

AI generated
SELECT fc."institute", fc."financial_year", SUM(fc."library" + fc."equipment" + fc."workshops" + fc."capital_assets") AS total_capital_expenses, COUNT(acd."id") AS total_innovation_courses FROM public.financial_expenses_capital fc LEFT JOIN public.academic_courses_details acd ON fc."institute" = acd."institute" AND fc."financial_year" = acd."financial_year" WHERE fc."financial_year" = '2023-24' GROUP BY fc."institute", fc."financial_year" HAVING SUM(fc."library" + fc."equipment" + fc."workshops" + fc."capital_assets") > 0 AND COUNT(acd."id") = 0;

Rising Stars: Institutes growing funding while the average declines.. 000

Actual quarry. 

-- This requires calculating the global average growth rate first, then comparing individual institutes against it.
-- Abstracted logic:
SELECT institute, SUM(grant_received) as total_funding
FROM innovation_grant_from_govt
WHERE as_on_year = '2024'
GROUP BY institute
ORDER BY total_funding DESC; -- Look for outliers in the "green" bars


AI generated
Error

Utilization Audit: High Grants vs Low Expenditure. zzz

Actual quarry. 

SELECT 
    g.institute, 
    SUM(g.grant_received) as grants_received,
    SUM(e.salaries + e.maintenance + e.seminars) as operational_expenses
FROM innovation_grant_from_govt g
JOIN financial_expenses_operational e ON g.institute = e.institute
WHERE g.as_on_year = '2024' AND e.as_on_year = '2023'
GROUP BY g.institute
HAVING SUM(g.grant_received) > (SUM(e.salaries + e.maintenance + e.seminars) * 2); -- Example threshold: Grants 2x higher than expenses


AI generated
SELECT ig."institute", SUM(ig."grant_received") AS total_grants_received, SUM(fe."salaries" + fe."maintenance" + fe."seminars") AS total_operational_expenditure, SUM(fc."library" + fc."equipment" + fc."workshops" + fc."capital_assets") AS total_capital_expenditure, (SUM(fe."salaries" + fe."maintenance" + fe."seminars") + SUM(fc."library" + fc."equipment" + fc."workshops" + fc."capital_assets")) AS total_expenditure FROM public."innovation_grant_from_govt" ig LEFT JOIN public."financial_expenses_operational" fe ON ig."institute" = fe."institute" AND ig."as_on_year" = fe."as_on_year" LEFT JOIN public."financial_expenses_capital" fc ON 

Pipeline Progression: Are we moving from Low TRL to High TRL?. xxx

Actual quarry. 

SELECT financial_year, stage_of_technology, COUNT(*) as project_count
FROM innovations_at_various_stages_of_technology_readiness_level
GROUP BY financial_year, stage_of_technology
ORDER BY financial_year, stage_of_technology;

AI generated
SELECT "stage_of_technology", COUNT(*) AS "count_of_innovations" FROM public.innovations_at_various_stages_of_technology_readiness_level GROUP BY "stage_of_technology" ORDER BY "stage_of_technology" ASC;

Summery:

Q#
Question (Short Description)


Reason
Response Time (seconds)
1
Most intensive innovation curriculum (credits-based)


AI summed credits incorrectly and ignored split logic; also limited result to 1 without matching intent
⏱ SQL generated in 7.73 sec
2
PhD : UG ratio for IIT Bombay


Ratio computed correctly, but original query expected counts per level, not direct ratio
⏱ SQL generated in 6.58 sec
3
>50% grant drop YoY


AI used row-level grants instead of aggregated yearly sums; logic mismatch
⏱ SQL generated in 7.90 sec
4
Top 5 funding agencies by amount


AI returned alphabetical DISTINCT names, not top by funding
⏱ SQL generated in 5.92 sec
5
% of IIT Madras innovations at Lab Validation


AI directly calculated required percentage correctly
⏱ SQL generated in 7.68 sec
6
TRL-9 (Market Ready) innovations at IIT Madras


Correct filter intent, but TRL value string mismatch (TRL 9 vs Level 9)
⏱ SQL generated in 6.55 sec
7
Cost of Innovation (grant per patent)


Oversimplified aggregation; ignored patent-grant status logic
⏱ SQL generated in 7.02 sec
8
PG innovation courses at IIT Madras (last 3 years)


Output broader than required but logically correct
⏱ SQL generated in 7.31 sec
9
Institute with most PhD courses


Correct aggregation and ordering
⏱ SQL generated in 6.19 sec
10
Compare PhD vs UG numbers (follow-up)


AI switched domain to student strength instead of courses
⏱ SQL generated in 6.25 sec
11
YoY growth for PG courses


AI calculated growth on credits, not course counts
⏱ SQL generated in 8.39 sec
12
Strategy shift: UG stops, PhD spikes


AI queried unrelated student intake tables
⏱ SQL generated in 8.45 sec
13
Correlation: courses vs startups


Over-joined extra tables but core correlation logic present
⏱ SQL generated in 6.57 sec
14
High capex, low innovation courses


Logic acceptable but HAVING clause narrowed scope incorrectly
⏱ SQL generated in 7.02 sec
15
Rising stars (funding growth vs average)


AI failed to generate a query


16
High grants vs low expenditure


Correct joins but missing final HAVING / audit condition
⏱ SQL generated in 8.61 sec
17
Pipeline progression across TRL


Lost time dimension; only stage-level aggregation
⏱ SQL generated in 7.23 sec

# NRG — SQL Query Audit Report

**Auditor:** Dhairya  
**Date:** 2025-04-23  
**Total Questions:** 17  

| Status | Code | Count |
|--------|------|-------|
| Answered Correctly | `xxx` | 7 |
| Correct but Wrong Format | `yyy` | 2 |
| Answered but Wrong | `zzz` | 5 |
| Error / Not Generated | `000` | 3 |

---

## Summary Table

| Q# | Question | Status | Observation | Response Time |
|----|----------|--------|-------------|---------------|
| 1 | Most intensive innovation curriculum (credits-based) | `xxx` | AI summed credits incorrectly; ignored SPLIT_PART logic; limited to 1 row without matching intent | 7.73s |
| 2 | PhD : UG ratio for IIT Bombay | `yyy` | Ratio computed correctly, but expected counts per level — not a direct ratio | 6.58s |
| 3 | >50% grant drop YoY (2020-21 to 2021-22) | `xxx` | AI used row-level grants instead of aggregated yearly sums; logic mismatch | 7.90s |
| 4 | Top 5 funding agencies by total amount | `000` | AI returned alphabetical DISTINCT names — not ranked by funding | 5.92s |
| 5 | % of IIT Madras innovations at Lab Validation (Level 4) | `zzz` | AI directly calculated required percentage correctly | 7.68s |
| 6 | TRL-9 (Market Ready) innovations at IIT Madras | `000` | Correct filter intent, but TRL value string mismatch ('TRL 9' vs 'Level 9') | 6.55s |
| 7 | Cost of Innovation (grant per patent) | `zzz` | Oversimplified aggregation; ignored patent-grant status logic | 7.02s |
| 8 | PG innovation courses at IIT Madras (last 3 years from 2021-22) | `xxx` | Output broader than required but logically correct | 7.31s |
| 9 | Institute with most PhD courses | `xxx` | Correct aggregation and ordering | 6.19s |
| 10 | Compare PhD vs UG numbers (contextual follow-up) | `zzz` | AI switched domain to student strength instead of course table | 6.25s |
| 11 | YoY growth for PG courses — IIT Madras | `xxx` | AI calculated growth on credits, not course counts | 8.39s |
| 12 | Detect strategy shift: UG stops, PhD spikes — IIT Madras | `zzz` | AI queried unrelated student intake tables | 8.45s |
| 13 | Correlation: Innovation courses vs. startups incubated | `xxx` | Over-joined extra tables but core correlation logic present | 6.57s |
| 14 | High capex, low innovation courses — FY 2023-24 | `yyy` | Logic acceptable but HAVING clause incorrectly narrowed scope | 7.02s |
| 15 | Rising stars: funding growth vs. declining average | `000` | AI failed to generate a query | — |
| 16 | High grants vs low expenditure (utilization audit) | `zzz` | Correct joins but missing final HAVING / audit condition; query incomplete | 8.61s |
| 17 | Pipeline progression across TRL stages | `xxx` | Lost time dimension; only stage-level aggregation, no financial_year | 7.23s |

---

## Detailed Query Analysis

---

### Q1 — `xxx` — ⏱ 7.73s

**Question:** Which institute offers the most intensive innovation curriculum in FY 2022-23 based on total credits, not just course count?

**Observation:** AI summed credits incorrectly and ignored split logic; also limited result to 1 without matching intent.

**Actual Query (Expected):**
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
SELECT "institute", SUM(CAST("total_credit_score" AS INTEGER)) AS total_credits
FROM public.academic_courses_details
WHERE "financial_year" = '2022-23'
GROUP BY "institute"
ORDER BY total_credits DESC
LIMIT 1;
```

---

### Q2 — `yyy` — ⏱ 6.58s

**Question:** Show me the ratio of PhD level innovation courses to Undergraduate ones for IIT Bombay.

**Observation:** Ratio computed correctly, but original query expected counts per level, not direct ratio.

**Actual Query (Expected):**
```sql
SELECT 
    level_of_course, 
    COUNT(*) as course_count
FROM 
    academic_courses_details
WHERE 
    institute = 'IIT Bombay'
    AND level_of_course IN ('UG', 'PhD')
GROUP BY 
    level_of_course;
```

**AI Generated:**
```sql
SELECT (COUNT(CASE WHEN "level_of_course" = 'PhD' THEN 1 END)::DECIMAL
        / NULLIF(COUNT(CASE WHEN "level_of_course" = 'UG' THEN 1 END), 0))
    AS phd_to_ug_ratio
FROM public.academic_courses_details
WHERE "institute" = 'IIT Bombay';
```

---

### Q3 — `xxx` — ⏱ 7.90s

**Question:** Flag any institute where grant funding has dropped by more than 50% year-over-year between 2020-2021 to 2021-22.

**Observation:** AI used row-level grants instead of aggregated yearly sums; logic mismatch.

**Actual Query (Expected):**
```sql
WITH YearlyGrants AS (
    SELECT 
        institute, 
        year_of_receiving, 
        SUM(grant_received) as total_funding
    FROM 
        innovation_grant_from_govt
    GROUP BY 
        institute, year_of_receiving
)
SELECT 
    current_year.institute,
    current_year.year_of_receiving as current_year,
    current_year.total_funding as current_funding,
    prev_year.total_funding as previous_funding,
    ((current_year.total_funding - prev_year.total_funding)
        / prev_year.total_funding::float) * 100 as growth_percentage
FROM 
    YearlyGrants current_year
JOIN 
    YearlyGrants prev_year
    ON current_year.institute = prev_year.institute
    AND prev_year.year_of_receiving = '2020-21'
WHERE 
    current_year.year_of_receiving = '2022-23'
    AND ((current_year.total_funding - prev_year.total_funding)
        / prev_year.total_funding::float) < -0.5;
```

**AI Generated:**
```sql
SELECT ig1.institute, ig1.year_of_receiving AS previous_year,
       ig1.grant_received AS previous_year_grant,
       ig2.year_of_receiving AS current_year,
       ig2.grant_received AS current_year_grant,
       ((ig2.grant_received::decimal / ig1.grant_received::decimal) * 100) AS percentage_change
FROM innovation_grant_from_govt ig1
JOIN innovation_grant_from_govt ig2
    ON ig1.institute = ig2.institute
    AND ig1.year_of_receiving::integer = ig2.year_of_receiving::integer - 1
WHERE (ig2.grant_received::decimal / ig1.grant_received::decimal) * 100 < 50;
```

---

### Q4 — `000` — ⏱ 5.92s

**Question:** Who are the top 5 unique funding agencies providing grants to us?

**Observation:** AI returned alphabetical DISTINCT names, not top by funding.

**Actual Query (Expected):**
```sql
SELECT 
    gov_organisation_name, 
    COUNT(*) as grant_count, 
    SUM(grant_received) as total_amount
FROM 
    innovation_grant_from_govt
GROUP BY 
    gov_organisation_name
ORDER BY 
    total_amount DESC
LIMIT 5;
```

**AI Generated:**
```sql
SELECT DISTINCT "gov_organisation_name"
FROM public.innovation_grant_from_govt
ORDER BY "gov_organisation_name"
LIMIT 5;
```

---

### Q5 — `zzz` — ⏱ 7.68s

**Question:** Identify bottlenecks: What percentage of IIT Madras innovations are stuck at 'Lab Validation' (Level 4)?

**Observation:** AI directly calculated required percentage correctly.

**Actual Query (Expected):**
```sql
SELECT 
    stage_of_technology,
    COUNT(*) as innovation_count,
    (COUNT(*) * 100.0 / (
        SELECT COUNT(*)
        FROM innovations_at_various_stages_of_technology_readiness_level
        WHERE institute = 'IIT Madras'
    )) as percentage_share
FROM 
    innovations_at_various_stages_of_technology_readiness_level
WHERE 
    institute = 'IIT Madras'
GROUP BY 
    stage_of_technology
ORDER BY 
    innovation_count DESC;
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

---

### Q6 — `000` — ⏱ 6.55s

**Question:** List all technologies that are 'Market Ready' (TRL 9) for commercialization in IIT Madras.

**Observation:** Correct filter intent, but TRL value string mismatch ('TRL 9' vs 'Level 9').

**Actual Query (Expected):**
```sql
SELECT 
    innovation_name, 
    financial_year
FROM 
    innovations_at_various_stages_of_technology_readiness_level
WHERE 
    stage_of_technology = 'Level 9'
    AND institute = 'IIT Madras';
```

**AI Generated:**
```sql
SELECT "innovation_name", "stage_of_technology", "financial_year", "as_on_year"
FROM public."innovations_at_various_stages_of_technology_readiness_level"
WHERE "stage_of_technology" = 'TRL 9'
AND "institute" = 'IIT Madras';
```

---

### Q7 — `zzz` — ⏱ 7.02s

**Question:** Calculate the 'Cost of Innovation': How much government grant money do we spend for every 1 Patent granted?

**Observation:** Oversimplified aggregation; ignored patent-grant status logic.

**Actual Query (Expected):**
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
FROM 
    GrantData g
JOIN 
    PatentData p ON g.institute = p.applicants
ORDER BY 
    cost_per_patent ASC;
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

---

### Q8 — `xxx` — ⏱ 7.31s

**Question:** Show me all PG innovation courses at IIT Madras for the last 3 years starting from FY 2021-22.

**Observation:** Output broader than required but logically correct.

**Actual Query (Expected):**
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

---

### Q9 — `xxx` — ⏱ 6.19s

**Question:** Which institute has the most PhD courses?

**Observation:** Correct aggregation and ordering.

**Actual Query (Expected):**
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
SELECT "institute", COUNT(DISTINCT "title_of_course") AS phd_course_count
FROM public.academic_courses_details
WHERE "level_of_course" = 'PhD'
GROUP BY "institute"
ORDER BY phd_course_count DESC
LIMIT 1;
```

---

### Q10 — `zzz` — ⏱ 6.25s

**Question:** How does that compare to their UG numbers? *(Contextual Follow-up)*

**Observation:** AI switched domain to student strength instead of course table.

**Actual Query (Expected):**
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

---

### Q11 — `xxx` — ⏱ 8.39s

**Question:** Identify growth trends: Calculate Year-Over-Year growth for PG courses in IIT Madras.

**Observation:** AI calculated growth on credits, not course counts.

**Actual Query (Expected):**
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
JOIN YearlyData t2
    ON t1.financial_year > t2.financial_year
ORDER BY t1.financial_year DESC;
```

**AI Generated:**
```sql
SELECT "financial_year", "total_credit_score",
       LAG("total_credit_score") OVER (ORDER BY "financial_year") AS previous_year_credit_score,
       (CAST("total_credit_score" AS NUMERIC)
        - CAST(LAG("total_credit_score") OVER (ORDER BY "financial_year") AS NUMERIC))
       / NULLIF(CAST(LAG("total_credit_score") OVER (ORDER BY "financial_year") AS NUMERIC), 0) * 100
       AS year_over_year_growth
FROM "academic_courses_details"
WHERE "level_of_course" = 'PG'
AND "institute" = 'IIT Madras'
ORDER BY "financial_year";
```

---

### Q12 — `zzz` — ⏱ 8.45s

**Question:** Detect Strategy Shift: Institute stops UG but spikes in PhD in IIT Madras.

**Observation:** AI queried unrelated student intake tables instead of academic_courses_details.

**Actual Query (Expected):**
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

---

### Q13 — `xxx` — ⏱ 6.57s

**Question:** Correlation: Innovation Courses vs. Startups Incubated (Cross-Module).

**Observation:** Over-joined extra tables but core correlation logic present.

**Actual Query (Expected):**
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

---

### Q14 — `yyy` — ⏱ 7.02s

**Question:** Gap Analysis: High Capital Expenses but Low Innovation Courses in FY 2023-24.

**Observation:** Logic acceptable but HAVING clause narrowed scope incorrectly to only zero-course institutes.

**Actual Query (Expected):**
```sql
SELECT 
    c.institute, 
    COUNT(c.id) as course_count, 
    SUM(f.capital_assets) as total_capital_expense
FROM academic_courses_details c
JOIN financial_expenses_capital f
    ON c.institute = f.institute
    AND c.financial_year = f.financial_year
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

---

### Q15 — `000` — ⏱ —

**Question:** Rising Stars: Institutes growing funding while the average declines.

**Observation:** AI failed to generate a query.

**Actual Query (Expected):**
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

---

### Q16 — `zzz` — ⏱ 8.61s

**Question:** Utilization Audit: High Grants vs Low Expenditure.

**Observation:** Correct joins but missing final HAVING / audit condition; query incomplete.

**Actual Query (Expected):**
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

---

### Q17 — `xxx` — ⏱ 7.23s

**Question:** Pipeline Progression: Are we moving from Low TRL to High TRL?

**Observation:** Lost time dimension; only stage-level aggregation without financial_year breakdown.

**Actual Query (Expected):**
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

---

*End of Report — NRG SQL Audit — Dhairya — 2025-04-23*

```markdown
# SesDhairya's Report

## Query Evaluation Legend
**Answered correctly (xxx)**  
**Answered correctly but not in correct format (yyy)**  
**Answered but wrong (zzz)**  
**Error (000)**

---

## 1. Which institute offers the most intensive innovation curriculum in FY - 2022-23 based on total credits, not just course count? **xxx**

**Actual Query**

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

**AI Generated**

```sql
SELECT "institute", SUM(CAST("total_credit_score" AS INTEGER)) AS total_credits FROM public.academic_courses_details WHERE "financial_year" = '2022-23' GROUP BY "institute" ORDER BY total_credits DESC LIMIT 1;
```

---

## 2. Show me the ratio of PhD level innovation courses to Undergraduate ones for IIT Bombay. **yyy**

**Actual Query**

```sql
SELECT 
    level_of_course, 
    COUNT(*) as course_count
FROM 
    academic_courses_details
WHERE 
    institute = 'IIT Bombay'
    AND level_of_course IN ('UG', 'PhD') -- Adjust values based on actual data
GROUP BY 
    level_of_course;
```

**AI Generated**

```sql
SELECT (COUNT(CASE WHEN "level_of_course" = 'PhD' THEN 1 END)::DECIMAL / NULLIF(COUNT(CASE WHEN "level_of_course" = 'UG' THEN 1 END), 0)) AS phd_to_ug_ratio FROM public.academic_courses_details WHERE "institute" = 'IIT Bombay';
```

---

## 3. Flag any institute where grant funding has dropped by more than 50% year-over-year between 2020-2021 to 2021-22. **xxx**

**Actual Query**

```sql
WITH YearlyGrants AS (
    SELECT 
        institute, 
        year_of_receiving, 
        SUM(grant_received) as total_funding
    FROM 
        innovation_grant_from_govt
    GROUP BY 
        institute, year_of_receiving
)
SELECT 
    current_year.institute,
    current_year.year_of_receiving as current_year,
    current_year.total_funding as current_funding,
    prev_year.total_funding as previous_funding,
    ((current_year.total_funding - prev_year.total_funding) / prev_year.total_funding::float) * 100 as growth_percentage
FROM 
    YearlyGrants current_year
JOIN 
    YearlyGrants prev_year ON current_year.institute = prev_year.institute 
    AND prev_year.year_of_receiving = '2020-21' -- Logic to define previous year
WHERE 
    current_year.year_of_receiving = '2022-23'
    AND ((current_year.total_funding - prev_year.total_funding) / prev_year.total_funding::float) < -0.5; -- Filter for >50% drop
```

**AI Generated**

```sql
SELECT ig1.institute, ig1.year_of_receiving AS previous_year, ig1.grant_received AS previous_year_grant, ig2.year_of_receiving AS current_year, ig2.grant_received AS current_year_grant, ((ig2.grant_received::decimal / ig1.grant_received::decimal) * 100) AS percentage_change FROM innovation_grant_from_govt ig1 JOIN innovation_grant_from_govt ig2 ON ig1.institute = ig2.institute AND ig1.year_of_receiving::integer = ig2.year_of_receiving::integer - 1 WHERE (ig2.grant_received::decimal / ig1.grant_received::decimal) * 100 < 50;
```

---

## 4. Who are the top 5 unique funding agencies providing grants to us? **000**

**Actual Query**

```sql
SELECT 
    gov_organisation_name, 
    COUNT(*) as grant_count, 
    SUM(grant_received) as total_amount
FROM 
    innovation_grant_from_govt
GROUP BY 
    gov_organisation_name
ORDER BY 
    total_amount DESC
LIMIT 5;
```

**AI Generated**

```sql
SELECT DISTINCT "gov_organisation_name" FROM public.innovation_grant_from_govt ORDER BY "gov_organisation_name" LIMIT 5;
```

---

## 5. Identify bottlenecks: What percentage of IIT Madras innovations are stuck at 'Lab Validation' (Level 4)? **zzz**

**Actual Query**

```sql
SELECT 
    stage_of_technology,
    COUNT(*) as innovation_count,
    (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM innovations_at_various_stages_of_technology_readiness_level WHERE institute = 'IIT Madras')) as percentage_share
FROM 
    innovations_at_various_stages_of_technology_readiness_level
WHERE 
    institute = 'IIT Madras'
GROUP BY 
    stage_of_technology
ORDER BY 
    innovation_count DESC;
```

**AI Generated**

```sql
SELECT (COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM public.innovations_at_various_stages_of_technology_readiness_level WHERE "institute" LIKE '%IIT Madras%'), 0)) AS percentage_stuck_at_lab_validation FROM public.innovations_at_various_stages_of_technology_readiness_level WHERE "institute" LIKE '%IIT Madras%' AND "stage_of_technology" = 'Lab Validation (Level 4)';
```

---

## 6. List all technologies that are 'Market Ready' (TRL 9) for commercialization in IIT Madras **000**

**Actual Query**

```sql
SELECT 
    innovation_name, 
    financial_year
FROM 
    innovations_at_various_stages_of_technology_readiness_level
WHERE 
    stage_of_technology = 'Level 9' -- Or equivalent string in DB
    AND institute = 'IIT Madras';
```

**AI Generated**

```sql
SELECT "innovation_name", "stage_of_technology", "financial_year", "as_on_year" FROM public."innovations_at_various_stages_of_technology_readiness_level" WHERE "stage_of_technology" = 'TRL 9' AND "institute" = 'IIT Madras';
```

---

## 7. Calculate the 'Cost of Innovation': How much government grant money do we spend for every 1 Patent granted ? **zzz**

**Actual Query**

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
FROM 
    GrantData g
JOIN 
    PatentData p ON g.institute = p.applicants -- Requires name standardization
ORDER BY 
    cost_per_patent ASC; -- Lower is better (more efficient)
```

**AI Generated**

```sql
SELECT SUM("grant_received")::BIGINT / NULLIF(SUM("patents_granted"), 0) AS "Cost_of_Innovation" FROM public."innovation_grant_from_govt" ig JOIN public."patents_details" pd ON ig."institute" = pd."institute" AND ig."year_of_receiving" = pd."financial_year";
```

---

## 8. Show me all PG innovation courses at IIT Madras for the last 3 years starting from fy 2021-22. **xxx**

**Actual Query**

```sql
SELECT title_of_course, financial_year, total_credit_score
FROM academic_courses_details
WHERE institute = 'IIT Madras'
  AND level_of_course = 'PG' -- Adjust 'PG' to match exact DB string (e.g., 'Post Graduate')
  AND financial_year IN ('2021-22', '2023-34', '2022-23');
```

**AI Generated**

```sql
SELECT "financial_year", "title_of_course", "course_code", "type_of_course", "level_of_course", "course_offering_department", "total_credit_score", "institute", "as_on_year" FROM public."academic_courses_details" WHERE "level_of_course" = 'PG' AND "institute" LIKE '%IIT Madras%' AND "financial_year" IN ('2021-22', '2022-23', '2023-24');
```

---

## 9. "Which institute has the most PhD courses?" **xxx**

**Actual Query**

```sql
SELECT institute, COUNT(*) as phd_course_count
FROM academic_courses_details
WHERE level_of_course = 'PhD'
GROUP BY institute
ORDER BY phd_course_count DESC
LIMIT 1;
```

**AI Generated**

```sql
SELECT "institute", COUNT(DISTINCT "title_of_course") AS phd_course_count FROM public.academic_courses_details WHERE "level_of_course" = 'PhD' GROUP BY "institute" ORDER BY phd_course_count DESC LIMIT 1;
```

---

## 10. "How does that compare to their UG numbers?" (Contextual Follow-up) **zzz**

**Actual Query**

```sql
SELECT level_of_course, COUNT(*) as course_count
FROM academic_courses_details
WHERE institute = ‘IIT Hydrabad’
GROUP BY level_of_course;
```

**AI Generated**

```sql
SELECT "program", "male_students", "female_students", "total_students", "within_state", "outside_state", "outside_country", "economically_backward", "socially_challenged", "reimbursed_by_government", "reimbursed_by_institution", "reimbursed_by_private", "not_reimbursed", "as_on_year" FROM public.actual_student_strength WHERE "institute" LIKE '%IIT Hyderabad%' AND "program" LIKE '%UG%';
```

---

## 11. Identify growth trends: Calculate Year-Over-Year growth for PG courses in IIT Madras. **xxx**

**Actual Query**

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
JOIN YearlyData t2 ON t1.financial_year > t2.financial_year -- Simplified logic; ideally join on specific previous year string
ORDER BY t1.financial_year DESC;
```

**AI Generated**

```sql
SELECT "financial_year", "total_credit_score", LAG("total_credit_score") OVER (ORDER BY "financial_year") AS previous_year_credit_score, (CAST("total_credit_score" AS NUMERIC) - CAST(LAG("total_credit_score") OVER (ORDER BY "financial_year") AS NUMERIC)) / NULLIF(CAST(LAG("total_credit_score") OVER (ORDER BY "financial_year") AS NUMERIC), 0) * 100 AS year_over_year_growth FROM "academic_courses_details" WHERE "level_of_course" = 'PG' AND "institute" = 'IIT Madras' ORDER BY "financial_year";
```

---

## 12. Detect Strategy Shift: Institute stops UG but spikes in PhD in IIT Madras.

**Actual Query**

```sql
SELECT financial_year,
    SUM(CASE WHEN level_of_course = 'UG' THEN 1 ELSE 0 END) as ug_count,
    SUM(CASE WHEN level_of_course = 'PhD' THEN 1 ELSE 0 END) as phd_count
FROM academic_courses_details
WHERE institute = 'IIT Madras'
GROUP BY financial_year
ORDER BY financial_year;
```

**AI Generated**

```sql
SELECT phd."institute" AS institute_name, phd."financial_year" AS phd_financial_year, SUM(phd."total") AS total_phd_students, ug."financial_year" AS ug_financial_year, SUM(ug."seats") AS total_ug_seats FROM public.phd_students phd LEFT JOIN public.sanctioned_intake ug ON phd."institute" = ug."institute" AND phd."financial_year" = ug."financial_year" WHERE phd."institute" = 'IIT Madras' GROUP BY phd."institute", phd."financial_year", ug."financial_year" ORDER BY phd."financial_year";
```

---

## 13. Correlation: Innovation Courses vs. Startups Incubated (Cross-Module). **xxx**

**Actual Query**

```sql
WITH CourseData AS (
    SELECT institute, COUNT(*) as total_courses 
    FROM academic_courses_details GROUP BY institute
),
StartupData AS (
    SELECT institute, COUNT(*) as total_startups 
    FROM incubation_details -- Using incubation units as proxy for startups
    GROUP BY institute
)
SELECT c.institute, c.total_courses, s.total_startups
FROM CourseData c
JOIN StartupData s ON c.institute = s.institute;
```

**AI Generated**

```sql
SELECT acd.institute AS institute_name, COUNT(DISTINCT acd.id) AS total_innovation_courses, COUNT(DISTINCT sr.id) AS total_startups_incubated FROM public.academic_courses_details acd LEFT JOIN public.incubation_details id ON acd.institute = id.institute LEFT JOIN public.startup_recognition sr ON acd.institute = sr.institute GROUP BY acd.institute ORDER BY institute_name;
```

---

## 14. Gap Analysis: High Capital Expenses but Low Innovation Courses in FY 2023-24 **yyy**

**Actual Query**

```sql
SELECT 
    c.institute, 
    COUNT(c.id) as course_count, 
    SUM(f.capital_assets) as total_capital_expense
FROM academic_courses_details c
JOIN financial_expenses_capital f ON c.institute = f.institute AND c.financial_year = f.financial_year
WHERE c.financial_year = '2023-24'
GROUP BY c.institute
ORDER BY total_capital_expense DESC, course_count ASC;
```

**AI Generated**

```sql
SELECT fc."institute", fc."financial_year", SUM(fc."library" + fc."equipment" + fc."workshops" + fc."capital_assets") AS total_capital_expenses, COUNT(acd."id") AS total_innovation_courses FROM public.financial_expenses_capital fc LEFT JOIN public.academic_courses_details acd ON fc."institute" = acd."institute" AND fc."financial_year" = acd."financial_year" WHERE fc."financial_year" = '2023-24' GROUP BY fc."institute", fc."financial_year" HAVING SUM(fc."library" + fc."equipment" + fc."workshops" + fc."capital_assets") > 0 AND COUNT(acd."id") = 0;
```

---

## 15. Rising Stars: Institutes growing funding while the average declines. **000**

**Actual Query**

```sql
-- This requires calculating the global average growth rate first, then comparing individual institutes against it.
-- Abstracted logic:
SELECT institute, SUM(grant_received) as total_funding
FROM innovation_grant_from_govt
WHERE as_on_year = '2024'
GROUP BY institute
ORDER BY total_funding DESC; -- Look for outliers in the "green" bars
```

**AI Generated**

```sql
Error
```

---

## 16. Utilization Audit: High Grants vs Low Expenditure. **zzz**

**Actual Query**

```sql
SELECT 
    g.institute, 
    SUM(g.grant_received) as grants_received,
    SUM(e.salaries + e.maintenance + e.seminars) as operational_expenses
FROM innovation_grant_from_govt g
JOIN financial_expenses_operational e ON g.institute = e.institute
WHERE g.as_on_year = '2024' AND e.as_on_year = '2023'
GROUP BY g.institute
HAVING SUM(g.grant_received) > (SUM(e.salaries + e.maintenance + e.seminars) * 2); -- Example threshold: Grants 2x higher than expenses
```

**AI Generated**

```sql
SELECT ig."institute", SUM(ig."grant_received") AS total_grants_received, SUM(fe."salaries" + fe."maintenance" + fe."seminars") AS total_operational_expenditure, SUM(fc."library" + fc."equipment" + fc."workshops" + fc."capital_assets") AS total_capital_expenditure, (SUM(fe."salaries" + fe."maintenance" + fe."seminars") + SUM(fc."library" + fc."equipment" + fc."workshops" + fc."capital_assets")) AS total_expenditure FROM public."innovation_grant_from_govt" ig LEFT JOIN public."financial_expenses_operational" fe ON ig."institute" = fe."institute" AND ig."as_on_year" = fe."as_on_year" LEFT JOIN public."financial_expenses_capital" fc ON 
```

---

## 17. Pipeline Progression: Are we moving from Low TRL to High TRL?. **xxx**

**Actual Query**

```sql
SELECT financial_year, stage_of_technology, COUNT(*) as project_count
FROM innovations_at_various_stages_of_technology_readiness_level
GROUP BY financial_year, stage_of_technology
ORDER BY financial_year, stage_of_technology;
```

**AI Generated**

```sql
SELECT "stage_of_technology", COUNT(*) AS "count_of_innovations" FROM public.innovations_at_various_stages_of_technology_readiness_level GROUP BY "stage_of_technology" ORDER BY "stage_of_technology" ASC;
```

---

## Summary

| Q# | Question (Short Description)                                      | Reason                                                                                                   | Response Time (seconds) |
|----|-------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|--------------------------|
| 1  | Most intensive innovation curriculum (credits-based)              | AI summed credits incorrectly and ignored split logic; also limited result to 1 without matching intent | ⏱ SQL generated in 7.73 sec |
| 2  | PhD : UG ratio for IIT Bombay                                     | Ratio computed correctly, but original query expected counts per level, not direct ratio                 | ⏱ SQL generated in 6.58 sec |
| 3  | >50% grant drop YoY                                               | AI used row-level grants instead of aggregated yearly sums; logic mismatch                               | ⏱ SQL generated in 7.90 sec |
| 4  | Top 5 funding agencies by amount                                  | AI returned alphabetical DISTINCT names, not top by funding                                              | ⏱ SQL generated in 5.92 sec |
| 5  | % of IIT Madras innovations at Lab Validation                     | AI directly calculated required percentage correctly                                                     | ⏱ SQL generated in 7.68 sec |
| 6  | TRL-9 (Market Ready) innovations at IIT Madras                    | Correct filter intent, but TRL value string mismatch (TRL 9 vs Level 9)                                  | ⏱ SQL generated in 6.55 sec |
| 7  | Cost of Innovation (grant per patent)                             | Oversimplified aggregation; ignored patent-grant status logic                                            | ⏱ SQL generated in 7.02 sec |
| 8  | PG innovation courses at IIT Madras (last 3 years)                | Output broader than required but logically correct                                                       | ⏱ SQL generated in 7.31 sec |
| 9  | Institute with most PhD courses                                   | Correct aggregation and ordering                                                                         | ⏱ SQL generated in 6.19 sec |
| 10 | Compare PhD vs UG numbers (follow-up)                             | AI switched domain to student strength instead of courses                                                | ⏱ SQL generated in 6.25 sec |
| 11 | YoY growth for PG courses                                         | AI calculated growth on credits, not course counts                                                       | ⏱ SQL generated in 8.39 sec |
| 12 | Strategy shift: UG stops, PhD spikes                              | AI queried unrelated student intake tables                                                               | ⏱ SQL generated in 8.45 sec |
| 13 | Correlation: courses vs startups                                  | Over-joined extra tables but core correlation logic present                                              | ⏱ SQL generated in 6.57 sec |
| 14 | High capex, low innovation courses                                | Logic acceptable but HAVING clause narrowed scope incorrectly                                            | ⏱ SQL generated in 7.02 sec |
| 15 | Rising stars (funding growth vs average)                          | AI failed to generate a query                                                                            | -                        |
| 16 | High grants vs low expenditure                                    | Correct joins but missing final HAVING / audit condition                                                 | ⏱ SQL generated in 8.61 sec |
| 17 | Pipeline progression across TRL                                   | Lost time dimension; only stage-level aggregation                                                        | ⏱ SQL generated in 7.23 sec |
```