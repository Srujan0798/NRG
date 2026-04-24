# Hall of Shame - NRG Text-to-SQL Adversarial Failures

Source: `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`.

These are production regression fixtures, not documentation examples. Every
pattern below caused a wrong or empty answer in the Dhairya audit and must stay
covered by `tests/benchmarks/test_dhairya_regression.py`.

## P1: SPLIT_PART Format Blind (Q1)

- Original query: "Which institute offers the most intensive innovation curriculum in FY 2022-23 based on total credits, not just course count?"
- Wrong SQL generated:

```sql
SELECT institute, SUM(CAST(total_credit_score AS INTEGER)) AS total_credits
FROM academic_courses_details
WHERE financial_year = '2022-23'
GROUP BY institute
ORDER BY total_credits DESC
LIMIT 1;
```

- Why it failed: `academic_courses_details.total_credit_score` is text in `"3:1"` lecture:tutorial format. Direct integer casts are invalid/wrong, and `LIMIT 1` was added without the user asking.
- Fix applied: parse the format before aggregation.

```sql
SELECT institute,
       SUM(SPLIT_PART(total_credit_score, ':', 1)::double precision) AS lecture_credits
FROM academic_courses_details
WHERE financial_year = '2022-23'
GROUP BY institute
ORDER BY lecture_credits DESC;
```

- Test covering this: `tests/benchmarks/test_dhairya_regression.py::TestDhairyaQueries::test_q01_credits_intensive_curriculum`.

## P2: DISTINCT vs GROUP BY Confusion (Q4)

- Original query: "Who are the top 5 unique funding agencies providing grants to us?"
- Wrong SQL generated:

```sql
SELECT DISTINCT gov_organisation_name
FROM innovation_grant_from_govt
ORDER BY gov_organisation_name
LIMIT 5;
```

- Why it failed: Alphabetical `DISTINCT` does not rank agencies by money.
- Fix applied: ranked metric questions use `GROUP BY` plus `ORDER BY SUM(...) DESC`.

```sql
SELECT gov_organisation_name, SUM(grant_received) AS total_grant
FROM innovation_grant_from_govt
GROUP BY gov_organisation_name
ORDER BY total_grant DESC
LIMIT 5;
```

- Test covering this: `tests/benchmarks/test_dhairya_regression.py::TestDhairyaQueries::test_q04_top_5_funding_agencies`.

## P3: Row-Level vs Aggregated YoY (Q3, Q11)

- Original query: "Flag any institute where grant funding has dropped by more than 50% year-over-year between 2020-21 to 2021-22."
- Wrong SQL generated:

```sql
SELECT curr.institute, curr.grant_received, prev.grant_received
FROM innovation_grant_from_govt curr
JOIN innovation_grant_from_govt prev ON curr.institute = prev.institute
WHERE curr.year_of_receiving = '2021-22'
  AND prev.year_of_receiving = '2020-21'
  AND curr.grant_received < prev.grant_received * 0.5;
```

- Why it failed: Institutes can have multiple grant rows per year. YoY must aggregate first, then compare annual totals.
- Fix applied: CTE with `GROUP BY institute, year`, then self-join.

```sql
WITH YearlyGrants AS (
    SELECT institute, year_of_receiving, SUM(grant_received) AS total_grant
    FROM innovation_grant_from_govt
    GROUP BY institute, year_of_receiving
)
SELECT curr.institute, curr.total_grant, prev.total_grant
FROM YearlyGrants curr
JOIN YearlyGrants prev
  ON curr.institute = prev.institute
 AND prev.year_of_receiving = '2020-21'
WHERE curr.year_of_receiving = '2021-22'
  AND curr.total_grant < prev.total_grant * 0.5;
```

- Tests covering this:
  - `tests/benchmarks/test_dhairya_regression.py::TestDhairyaQueries::test_q03_grant_drop_yoy`
  - `tests/benchmarks/test_dhairya_regression.py::TestDhairyaQueries::test_q03_grant_drop_yoy_coincidence_case`

## P4: Missing or Truncated HAVING (Q14, Q16)

- Original query: "Utilization Audit: High Grants vs Low Expenditure."
- Wrong SQL generated:

```sql
SELECT ig.institute, SUM(ig.grant_received) AS total_grants_received,
       SUM(fe.salaries + fe.maintenance + fe.seminars) AS total_operational_expenditure
FROM innovation_grant_from_govt ig
LEFT JOIN financial_expenses_operational fe ON ig.institute = fe.institute
-- INCOMPLETE: missing GROUP BY / HAVING audit condition
```

- Why it failed: The SQL was truncated before the aggregate audit condition.
- Fix applied: completeness validation rejects trailing clauses and HAVING-without-GROUP-BY; generation uses full aggregate predicate.

```sql
SELECT g.institute, SUM(g.grant_received) AS grants_received,
       SUM(e.salaries + e.maintenance + e.seminars) AS operational_expenses
FROM innovation_grant_from_govt g
JOIN financial_expenses_operational e ON g.institute = e.institute
GROUP BY g.institute
HAVING SUM(g.grant_received) > SUM(e.salaries + e.maintenance + e.seminars) * 2;
```

- Tests covering this:
  - `tests/benchmarks/test_dhairya_regression.py::TestDhairyaQueries::test_q16_utilization_audit`
  - `tests/benchmarks/test_dhairya_regression.py::TestQueryCompletenessValidator::test_having_without_group_by_fails`

## P5: Cross-Domain Follow-Up Confusion (Q10, Q12)

- Original follow-up: "Now compare that for undergraduate courses."
- Wrong behavior: switched away from `academic_courses_details` into unrelated student-strength/intake tables.
- Why it failed: Conversation state did not preserve active table/domain.
- Fix applied: `active_domain` persists in `NRGState` and planner/router logic uses it for follow-up queries.

```sql
SELECT institute, level_of_course, COUNT(*) AS course_count
FROM academic_courses_details
WHERE level_of_course = 'UG'
GROUP BY institute, level_of_course
ORDER BY course_count DESC;
```

- Tests covering this:
  - `tests/benchmarks/test_dhairya_regression.py::TestDhairyaQueries::test_q10_followup_stays_courses_domain`
  - `tests/benchmarks/test_dhairya_regression.py::TestDhairyaQueries::test_q12_followup_stays_courses_domain`

## P6: TRL Synonym Blindness (Q6)

- Original query: "List all technologies that are 'Market Ready' (TRL 9) for commercialization in IIT Madras."
- Wrong SQL generated:

```sql
SELECT innovation_name, stage_of_technology
FROM innovations_at_various_stages_of_technology_readiness_level
WHERE stage_of_technology = 'TRL 9'
  AND institute = 'IIT Madras';
```

- Why it failed: The DB stores `'Level 9'`, not `'TRL 9'`.
- Fix applied: synonym map translates `TRL-9`, `TRL9`, `TRL 9`, `Market Ready`, and `Stage 9` to `'Level 9'`.

```sql
SELECT innovation_name, stage_of_technology, financial_year
FROM innovations_at_various_stages_of_technology_readiness_level
WHERE institute LIKE '%IIT Madras%'
  AND stage_of_technology = 'Level 9';
```

- Test covering this: `tests/benchmarks/test_dhairya_regression.py::TestDhairyaQueries::test_q06_trl9_market_ready`.

## P7: Multi-Step Reasoning Failure (Q15)

- Original query: "Rising Stars: Institutes growing funding while the average declines."
- Wrong SQL generated: no SQL; the system returned `Error`.
- Why it failed: Comparing individual growth to global average requires multi-stage CTE reasoning.
- Fix applied: CTE for institute funding, CTE for global average, then compare.

```sql
WITH InstFunding AS (
    SELECT institute, year_of_receiving, SUM(grant_received) AS total
    FROM innovation_grant_from_govt
    GROUP BY institute, year_of_receiving
),
AvgFunding AS (
    SELECT year_of_receiving, AVG(total) AS avg_total
    FROM InstFunding
    GROUP BY year_of_receiving
)
SELECT i.institute, i.year_of_receiving, i.total, a.avg_total
FROM InstFunding i
JOIN AvgFunding a ON i.year_of_receiving = a.year_of_receiving
WHERE i.total > a.avg_total
ORDER BY i.total DESC;
```

- Test covering this: `tests/benchmarks/test_dhairya_regression.py::TestDhairyaQueries::test_q15_rising_stars`.
