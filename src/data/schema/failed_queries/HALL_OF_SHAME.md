# Hall of Shame — NRG Text-to-SQL Adversarial Failures

This file records the seven Dhairya benchmark failure patterns that must never regress.
Each entry is tied to the original audit examples in `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
and to regression coverage in `tests/benchmarks/test_dhairya_regression.py`.

## P1: SPLIT_PART Format Blind (Q1)

- Original query: Which institute offers the most intensive innovation curriculum in FY 2022-23 based on total credits, not just course count?
- Wrong SQL generated:
```sql
SELECT "institute",
       SUM(CAST("total_credit_score" AS INTEGER)) AS total_credits
FROM public.academic_courses_details
WHERE "financial_year" = '2022-23'
GROUP BY "institute"
ORDER BY total_credits DESC
LIMIT 1;
```
- Why it failed: `total_credit_score` is `text` in `"X:Y"` format such as `"3:1"`. A direct integer cast either fails or ignores the structured credit format.
- Fix applied: Parse the credit field with `SPLIT_PART(total_credit_score, ':', 1)::double precision` before aggregating, and only apply `LIMIT` when the user asks for a single winner.
- Test covering this: `tests/benchmarks/test_dhairya_regression.py::test_q01_uses_split_part_for_credit_score`.

## P2: Top-N Metric Ranking Becomes Alphabetical DISTINCT (Q4)

- Original query: Who are the top 5 unique funding agencies providing grants to us?
- Wrong SQL generated:
```sql
SELECT DISTINCT "gov_organisation_name"
FROM public.innovation_grant_from_govt
ORDER BY "gov_organisation_name"
LIMIT 5;
```
- Why it failed: "Top 5" by funding requires grouped sums. The generated SQL returned the first five agency names alphabetically, not the largest funders.
- Fix applied: Generate `GROUP BY gov_organisation_name ORDER BY SUM(grant_received) DESC LIMIT 5` for "top N by metric" prompts.
- Test covering this: `tests/benchmarks/test_dhairya_regression.py::test_q04_top_funding_agencies_grouped_by_sum`.

## P3: Year-Over-Year Row Comparison Instead Of Yearly Aggregation (Q3, Q11)

- Original query: Flag any institute where grant funding has dropped by more than 50% year-over-year between 2020-21 to 2021-22.
- Wrong SQL generated:
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
- Why it failed: The query compared individual grant rows before summing per institute and year, so multiple grants in the same year could silently produce wrong growth or drop signals.
- Fix applied: Use a CTE that aggregates by institute and year first, then self-join or window over those yearly totals.
- Test covering this: `tests/benchmarks/test_dhairya_regression.py::test_q03_multi_row_yearly_grants_are_summed_before_yoy_comparison`.

## P4: Missing Or Wrong HAVING / Truncated SQL (Q14, Q16)

- Original query: Utilization Audit: High Grants vs Low Expenditure.
- Wrong SQL generated:
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
- Why it failed: The SQL stopped before the required audit condition, so it could return broad spend data instead of the high-grant/low-expenditure exception set.
- Fix applied: The completeness validator rejects truncated SQL, missing terminal clauses, and missing `HAVING` for comparative aggregate filters before execution.
- Test covering this: `tests/benchmarks/test_dhairya_regression.py::test_q16_high_grants_low_expenditure_requires_having_clause`.

## P5: Active Domain Lost Across Follow-Up Turns (Q10, Q12)

- Original query: How does that compare to their UG numbers? (follow-up after "Which institute has the most PhD courses?")
- Wrong SQL generated:
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
- Why it failed: The follow-up was still about innovation courses, but the model switched domains to student-strength enrollment tables.
- Fix applied: Persist `active_domain` and prior table context across turns so course follow-ups stay in `academic_courses_details` unless the user explicitly changes domain.
- Test covering this: `tests/benchmarks/test_dhairya_regression.py::test_q10_followup_keeps_academic_courses_domain`.

## P6: TRL Synonym Map Missing (Q6)

- Original query: List all technologies that are 'Market Ready' (TRL 9) for commercialization in IIT Madras.
- Wrong SQL generated:
```sql
SELECT "innovation_name", "stage_of_technology", "financial_year", "as_on_year"
FROM public."innovations_at_various_stages_of_technology_readiness_level"
WHERE "stage_of_technology" = 'TRL 9'
  AND "institute" = 'IIT Madras';
```
- Why it failed: The database stores this stage as `'Level 9'`, while users naturally ask for `TRL 9`, `TRL-9`, `TRL9`, or `Market Ready`.
- Fix applied: Normalize `TRL-9 = TRL9 = Level 9 = Market Ready = Stage 9` to `stage_of_technology = 'Level 9'`.
- Test covering this: `tests/benchmarks/test_dhairya_regression.py::test_q06_trl_9_market_ready_maps_to_level_9`.

## P7: Complex CTE, Scalar Average, And Semantic Join Failure (Q7, Q15)

- Original query: Rising Stars: Institutes growing funding while the average declines.
- Wrong SQL generated:
```text
Error
```
- Why it failed: The model did not decompose the query into institute-level growth and global-average comparison. A related Dhairya failure also joined patent/grant data through the wrong semantic key instead of `combined_ipo_patent_data.applicants`.
- Fix applied: Generate complete CTEs for individual growth and global averages, use scalar subqueries where needed, and enforce semantic join rules such as `innovation_grant_from_govt.institute` to `combined_ipo_patent_data.applicants` with `status = 'Granted'`.
- Test covering this: `tests/benchmarks/test_dhairya_regression.py::test_q15_rising_stars_uses_cte_and_scalar_global_average`.
