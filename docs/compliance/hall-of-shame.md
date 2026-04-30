# NRG Text-to-SQL Hall Of Shame

This document records the Dhairya benchmark failure patterns that must never
regress. It mirrors the pattern index in
`docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` and backs the validator rules in
`src/skills/text_to_sql/validator.py`.

### P1: Incorrect Aggregation Logic — Q3, Q11

**Wrong SQL:**
```sql
SELECT ig1.institute, ig1.grant_received, ig2.grant_received
FROM innovation_grant_from_govt ig1
JOIN innovation_grant_from_govt ig2 ON ig1.institute = ig2.institute;
```

**Why It Fails:** Q3 and Q11 require yearly aggregation before comparison.
Row-level comparisons silently miss multi-row same-year cases.

**Correct SQL:**
```sql
WITH yearly AS (
  SELECT institute, year_of_receiving, SUM(grant_received) AS total_grant
  FROM innovation_grant_from_govt
  GROUP BY institute, year_of_receiving
)
SELECT curr.institute, curr.year_of_receiving, curr.total_grant, prev.total_grant
FROM yearly curr
JOIN yearly prev ON curr.institute = prev.institute;
```

**Adversarial Test Fixture:** Q3, Q11 yearly growth and drop questions.

**Validator Rule:** `dhairya_p1_incorrect_aggregation_logic`

### P2: Missing/Late HAVING Clause — Q14, Q16

**Wrong SQL:**
```sql
SELECT ig.institute, SUM(ig.grant_received) AS total_grants_received
FROM innovation_grant_from_govt ig
LEFT JOIN financial_expenses_operational fe ON ig.institute = fe.institute;
```

**Why It Fails:** Q14 and Q16 are audit/exception queries. Without the final
`HAVING` or equivalent filter, the answer is an unfocused aggregate.

**Correct SQL:**
```sql
SELECT ig.institute, SUM(ig.grant_received) AS total_grants_received
FROM innovation_grant_from_govt ig
LEFT JOIN financial_expenses_operational fe ON ig.institute = fe.institute
GROUP BY ig.institute
HAVING SUM(ig.grant_received) > COALESCE(SUM(fe.salaries + fe.maintenance + fe.seminars), 0);
```

**Adversarial Test Fixture:** Q14, Q16 high grant / low expenditure questions.

**Validator Rule:** `dhairya_p2_missing_or_late_having`

### P3: Cross-Domain Confusion — Q10, Q12

**Wrong SQL:**
```sql
SELECT institute, program, total_students
FROM actual_student_strength
WHERE program = 'UG';
```

**Why It Fails:** Q10 and Q12 are course-domain follow-ups. Switching to
student-strength tables changes the metric and produces a wrong answer.

**Correct SQL:**
```sql
SELECT institute, level_of_course, COUNT(*) AS course_count
FROM academic_courses_details
WHERE level_of_course IN ('UG', 'PhD')
GROUP BY institute, level_of_course;
```

**Adversarial Test Fixture:** Q10, Q12 course follow-ups after PhD/UG context.

**Validator Rule:** `dhairya_p3_cross_domain_confusion`

### P4: String Value Mismatch — Q6

**Wrong SQL:**
```sql
SELECT innovation_name
FROM trl_stages
WHERE stage_of_technology = 'TRL 9';
```

**Why It Fails:** Q6 uses natural user wording, but the database stores market
readiness as `Level 9`.

**Correct SQL:**
```sql
SELECT innovation_name, stage_of_technology, financial_year, institute
FROM trl_stages
WHERE stage_of_technology = 'Level 9';
```

**Adversarial Test Fixture:** Q6 `TRL 9`, `Market Ready`, and `Level 9` synonyms.

**Validator Rule:** `dhairya_p4_stage_string_value_mismatch`

### P5: ORDER BY / LIMIT Scope Errors — Q1, Q4

**Wrong SQL:**
```sql
SELECT DISTINCT gov_organisation_name
FROM innovation_grant_from_govt
ORDER BY gov_organisation_name
LIMIT 5;
```

**Why It Fails:** Q1 and Q4 ask for ranked metrics. The query must compute the
metric before ordering and limiting.

**Correct SQL:**
```sql
SELECT gov_organisation_name, SUM(grant_received) AS total_grant
FROM innovation_grant_from_govt
GROUP BY gov_organisation_name
ORDER BY total_grant DESC
LIMIT 5;
```

**Adversarial Test Fixture:** Q1 credit intensity and Q4 top agency rankings.

**Validator Rule:** `dhairya_p5_order_by_limit_scope_errors`

### P6: JOIN Key Mismatch — Q7, Q13

**Wrong SQL:**
```sql
SELECT SUM(ig.grant_received) / COUNT(pd.id)
FROM innovation_grant_from_govt ig
JOIN patents_details pd ON ig.institute = pd.institute;
```

**Why It Fails:** Q7 and Q13 require semantic joins. Patent applicants and grant
institutes do not always share a direct normalized key.

**Correct SQL:**
```sql
WITH grants AS (
  SELECT institute, SUM(grant_received) AS total_grant
  FROM innovation_grant_from_govt
  GROUP BY institute
),
patents AS (
  SELECT g.institute, COUNT(*) AS patent_count
  FROM grants g
  JOIN combined_ipo_patent_data p
    ON lower(trim(p.applicants)) LIKE '%' || lower(trim(g.institute)) || '%'
  WHERE p.status = 'Granted'
  GROUP BY g.institute
)
SELECT g.institute, g.total_grant, p.patent_count
FROM grants g
LEFT JOIN patents p ON p.institute = g.institute;
```

**Adversarial Test Fixture:** Q7 patent cost and Q13 course/incubation joins.

**Validator Rule:** `dhairya_p6_join_key_mismatch`

### P7: Complete Failure — Q15

**Wrong SQL:**
```text
Error
```

**Why It Fails:** Q15 requires decomposition into institute growth and
system-wide average movement. Returning no SQL blocks the answer path.

**Correct SQL:**
```sql
WITH inst AS (
  SELECT institute, year_of_receiving, SUM(grant_received) AS total_grant
  FROM innovation_grant_from_govt
  GROUP BY institute, year_of_receiving
),
avg_by_year AS (
  SELECT year_of_receiving, AVG(total_grant) AS avg_total
  FROM inst
  GROUP BY year_of_receiving
)
SELECT i.institute, i.year_of_receiving, i.total_grant, a.avg_total
FROM inst i
JOIN avg_by_year a ON a.year_of_receiving = i.year_of_receiving;
```

**Adversarial Test Fixture:** Q15 rising-star funding questions.

**Validator Rule:** `dhairya_p7_complete_generation_failure`
