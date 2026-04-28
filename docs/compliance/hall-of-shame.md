# Hall of Shame - NRG Dhairya Failure Patterns

This document mirrors the seven failure patterns in
`docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`. It is a CI-checked prevention
ledger: every pattern below must have a wrong SQL example, failure explanation,
correct SQL shape, adversarial fixture, and validator rule.

## Coverage Map

| Pattern | Dhairya queries | Validator rule | Adversarial fixture |
|---|---:|---|---|
| P1 Incorrect Aggregation Logic | Q3, Q11 | `dhairya_p1_incorrect_aggregation_logic` | `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P1]` |
| P2 Missing/Late HAVING Clause | Q14, Q16 | `dhairya_p2_missing_or_late_having` | `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P2]` |
| P3 Cross-Domain Confusion | Q10, Q12 | `dhairya_p3_cross_domain_confusion` | `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P3]` |
| P4 String Value Mismatch | Q6 | `dhairya_p4_stage_string_value_mismatch` | `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P4]` |
| P5 ORDER BY / LIMIT Scope Errors | Q1, Q4 | `dhairya_p5_order_by_limit_scope_errors` | `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P5]` |
| P6 JOIN Key Mismatch | Q7, Q13 | `dhairya_p6_join_key_mismatch` | `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P6]` |
| P7 Complete Failure | Q15 | `dhairya_p7_complete_generation_failure` | `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P7]` |

### P1: Incorrect Aggregation Logic — Q3, Q11

**Dhairya Queries:** Q3, Q11

**Wrong SQL:**
```sql
SELECT financial_year, total_credit_score,
       LAG(total_credit_score) OVER (ORDER BY financial_year) AS previous_year_credit_score
FROM academic_courses_details
WHERE institute = 'IIT Madras' AND level_of_course = 'PG'
ORDER BY financial_year;
```

**Why It Fails:** Q3 and Q11 require yearly aggregates before comparison.
Row-level values and `LAG(total_credit_score)` compare individual records, not
institute/year totals or course-count growth.

**Correct SQL:**
```sql
WITH yearly AS (
    SELECT financial_year, COUNT(*) AS course_count
    FROM academic_courses_details
    WHERE institute = 'IIT Madras' AND level_of_course = 'PG'
    GROUP BY financial_year
)
SELECT cur.financial_year,
       cur.course_count,
       prev.course_count AS previous_count,
       ((cur.course_count - prev.course_count)::float / NULLIF(prev.course_count, 0)) * 100 AS growth_rate
FROM yearly cur
JOIN yearly prev ON cur.financial_year > prev.financial_year
ORDER BY cur.financial_year;
```

**Adversarial Test Fixture:** `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P1]`

**Validator Rule:** `dhairya_p1_incorrect_aggregation_logic`

### P2: Missing/Late HAVING Clause — Q14, Q16

**Dhairya Queries:** Q14, Q16

**Wrong SQL:**
```sql
SELECT ig.institute, SUM(ig.grant_received) AS total_grants_received
FROM innovation_grant_from_govt ig
LEFT JOIN financial_expenses_operational fe ON ig.institute = fe.institute
-- [INCOMPLETE - missing HAVING / audit condition]
```

**Why It Fails:** Q14 and Q16 are multi-stage audit queries. They need the full
`WHERE -> GROUP BY -> HAVING` shape or an explicit ranking/filter condition.
Truncated SQL silently drops the actual audit predicate.

**Correct SQL:**
```sql
SELECT g.institute,
       SUM(g.grant_received) AS grants_received,
       SUM(e.salaries + e.maintenance + e.seminars) AS operational_expenses
FROM innovation_grant_from_govt g
JOIN financial_expenses_operational e ON g.institute = e.institute
WHERE g.as_on_year = '2024' AND e.as_on_year = '2023'
GROUP BY g.institute
HAVING SUM(g.grant_received) > (SUM(e.salaries + e.maintenance + e.seminars) * 2);
```

**Adversarial Test Fixture:** `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P2]`

**Validator Rule:** `dhairya_p2_missing_or_late_having`

### P3: Cross-Domain Confusion — Q10, Q12

**Dhairya Queries:** Q10, Q12

**Wrong SQL:**
```sql
SELECT phd.institute, SUM(phd.total) AS total_phd_students, SUM(ug.seats) AS total_ug_seats
FROM phd_students phd
LEFT JOIN sanctioned_intake ug ON phd.institute = ug.institute
WHERE phd.institute = 'IIT Madras'
GROUP BY phd.institute;
```

**Why It Fails:** The Dhairya follow-up was still about innovation courses.
Switching to student-strength, PhD-student, or sanctioned-intake tables answers
an enrollment question the user did not ask.

**Correct SQL:**
```sql
SELECT financial_year,
       SUM(CASE WHEN level_of_course = 'UG' THEN 1 ELSE 0 END) AS ug_count,
       SUM(CASE WHEN level_of_course = 'PhD' THEN 1 ELSE 0 END) AS phd_count
FROM academic_courses_details
WHERE institute = 'IIT Madras'
GROUP BY financial_year
ORDER BY financial_year;
```

**Adversarial Test Fixture:** `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P3]`

**Validator Rule:** `dhairya_p3_cross_domain_confusion`

### P4: String Value Mismatch — Q6

**Dhairya Queries:** Q6

**Wrong SQL:**
```sql
SELECT innovation_name
FROM innovations_at_various_stages_of_technology_readiness_level
WHERE institute = 'IIT Madras' AND stage_of_technology = 'TRL 9';
```

**Why It Fails:** The schema stores readiness values as `Level 4`, `Level 9`,
and similar stored values. User-facing strings such as `TRL 9`, `TRL9`, and
`Market Ready` must be normalized before reaching SQL.

**Correct SQL:**
```sql
SELECT innovation_name, financial_year
FROM innovations_at_various_stages_of_technology_readiness_level
WHERE institute = 'IIT Madras'
  AND stage_of_technology = 'Level 9';
```

**Adversarial Test Fixture:** `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P4]`

**Validator Rule:** `dhairya_p4_stage_string_value_mismatch`

### P5: ORDER BY / LIMIT Scope Errors — Q1, Q4

**Dhairya Queries:** Q1, Q4

**Wrong SQL:**
```sql
SELECT DISTINCT gov_organisation_name
FROM innovation_grant_from_govt
ORDER BY gov_organisation_name
LIMIT 5;
```

**Why It Fails:** Q4 asked for top agencies by grant amount. `DISTINCT` plus
alphabetical `ORDER BY` ranks names, not funding. Q1 has the same scope family:
ranking by credits must parse `total_credit_score` before ordering, and must not
add `LIMIT 1` unless the user asks for one row.

**Correct SQL:**
```sql
SELECT gov_organisation_name,
       COUNT(*) AS grant_count,
       SUM(grant_received) AS total_amount
FROM innovation_grant_from_govt
GROUP BY gov_organisation_name
ORDER BY total_amount DESC
LIMIT 5;
```

**Adversarial Test Fixture:** `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P5]`

**Validator Rule:** `dhairya_p5_order_by_limit_scope_errors`

### P6: JOIN Key Mismatch — Q7, Q13

**Dhairya Queries:** Q7, Q13

**Wrong SQL:**
```sql
SELECT SUM(ig.grant_received) / NULLIF(SUM(pd.patents_granted), 0) AS cost_of_innovation
FROM innovation_grant_from_govt ig
JOIN patents_details pd ON ig.institute = pd.institute;
```

**Why It Fails:** Dhairya Q7 needs granted-patent counts from
`combined_ipo_patent_data`, matched with grants by institute/applicants. The
wrong table and key either undercount patents or join unrelated entities.

**Correct SQL:**
```sql
WITH grant_data AS (
    SELECT institute, SUM(grant_received) AS total_money
    FROM innovation_grant_from_govt
    GROUP BY institute
),
patent_data AS (
    SELECT applicants, COUNT(*) AS total_patents
    FROM combined_ipo_patent_data
    WHERE status = 'Granted'
    GROUP BY applicants
)
SELECT g.institute,
       g.total_money,
       p.total_patents,
       g.total_money / NULLIF(p.total_patents, 0) AS cost_per_patent
FROM grant_data g
JOIN patent_data p ON lower(trim(g.institute)) = lower(trim(p.applicants));
```

**Adversarial Test Fixture:** `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P6]`

**Validator Rule:** `dhairya_p6_join_key_mismatch`

### P7: Complete Failure — Q15

**Dhairya Queries:** Q15

**Wrong SQL:**
```text
Error
```

**Why It Fails:** Q15 requires multi-step decomposition: per-institute funding
growth, national average movement, comparison, and ranking. Returning `Error`
means no auditable SQL exists.

**Correct SQL:**
```sql
WITH yearly AS (
    SELECT institute, year_of_receiving, SUM(grant_received) AS total_funding
    FROM innovation_grant_from_govt
    GROUP BY institute, year_of_receiving
),
growth AS (
    SELECT cur.institute,
           cur.total_funding AS current_funding,
           prev.total_funding AS previous_funding,
           (cur.total_funding - prev.total_funding) / NULLIF(prev.total_funding, 0) AS growth_rate
    FROM yearly cur
    JOIN yearly prev
      ON cur.institute = prev.institute
     AND cur.year_of_receiving > prev.year_of_receiving
),
national AS (
    SELECT AVG(growth_rate) AS average_growth_rate
    FROM growth
)
SELECT g.*
FROM growth g
CROSS JOIN national n
WHERE g.growth_rate > 0 AND n.average_growth_rate < 0
ORDER BY g.growth_rate DESC;
```

**Adversarial Test Fixture:** `TestDhairyaFailurePatternContracts::test_validator_rejects_each_documented_wrong_sql[P7]`

**Validator Rule:** `dhairya_p7_complete_generation_failure`

## CI Gate

`tests/benchmarks/test_dhairya_adversarial.py::TestDhairyaFailurePatternContracts`
parses `SQL_AUDIT_REPORT_DHAIRYA.md` and this Hall of Shame. If the report gains
a new `### Pattern N:` entry or this file omits any required field, CI fails
until the pattern, fixture, and validator rule are added.
