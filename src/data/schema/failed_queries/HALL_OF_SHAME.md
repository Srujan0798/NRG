# NRG Text-to-SQL Hall of Shame

This ledger records the seven Dhairya benchmark failure patterns that must never regress.
It is the production-path companion to the root `HALL_OF_SHAME.md` and is read by the
Text-to-SQL validator when rejected SQL shapes are recorded.

### P1: SPLIT_PART Format Blind (Q1)

**Original question:** Average credit score across departments.  
**Wrong SQL generated:** `SELECT AVG(total_credit_score) FROM academic_courses_details`.  
**Why it failed:** `total_credit_score` is stored as text in `X:Y` format, for example `3:1`. Direct numeric casts either fail or aggregate the wrong value.  
**Fix applied:** Production SQL must parse the column with `SPLIT_PART(total_credit_score, ':', 1)::double precision` plus the second component when total credits are required.  
**Test covering this:** `tests/benchmarks/test_dhairya_regression.py`, `tests/benchmarks/test_text_to_sql_prompt_hardening.py`.

### P2: Aggregation Scope Error (Q4)

**Original question:** Top funding agencies by total amount.  
**Wrong SQL generated:** `SELECT DISTINCT gov_organisation_name ... ORDER BY gov_organisation_name`.  
**Why it failed:** Ranking by total funding requires grouped sums, not distinct alphabetical ordering.  
**Fix applied:** Use `GROUP BY gov_organisation_name ORDER BY SUM(grant_received) DESC`.  
**Test covering this:** Dhairya Q4 regression and adversarial ranked-funding mutations.

### P3: Year-Over-Year Row Comparison (Q3, Q11)

**Original question:** Flag institutes with large year-over-year funding drops or course growth.  
**Wrong SQL generated:** Window functions over raw rows.  
**Why it failed:** Individual rows were compared before institute/year aggregation, producing false drops and false growth.  
**Fix applied:** First aggregate in a CTE by institute and financial year, then self-join or window over those yearly totals.  
**Test covering this:** Dhairya Q3/Q11 regression and silent-wrong-answer suite.

### P4: TRL Synonym Leakage (Q6)

**Original question:** List TRL 9 or Market Ready technologies.  
**Wrong SQL generated:** `stage_of_technology = 'TRL 9'`.  
**Why it failed:** The schema stores market-ready technologies as `Level 9`, not as user-facing TRL phrases.  
**Fix applied:** Normalize `TRL 9`, `TRL-9`, `TRL9`, and `Market Ready` to `stage_of_technology = 'Level 9'`.  
**Test covering this:** Dhairya Q6 regression and TRL prompt-hardening tests.

### P5: Follow-Up Context Loss (Q10, Q12)

**Original question:** After a course query, "How does that compare to UG numbers?"  
**Wrong SQL generated:** Query switched to student-strength tables.  
**Why it failed:** Follow-up planning lost the previous domain and treated "UG numbers" as enrolment instead of course-level comparison.  
**Fix applied:** Session state carries previous domain/table context; course follow-ups stay in `academic_courses_details` unless the user explicitly asks for student counts.  
**Test covering this:** Dhairya Q10/Q12 regression and graph session memory tests.

### P6: Grant And Patent JOIN Key Mismatch (Q7, Q13)

**Original question:** Cost of innovation or grant per granted patent by institute.  
**Wrong SQL generated:** Joined grant institute to the wrong patent table/column or skipped patent status.  
**Why it failed:** `combined_ipo_patent_data.applicants` is the semantic key matching `innovation_grant_from_govt.institute`, and only `status = 'Granted'` counts.  
**Fix applied:** Join with `lower(trim(g.institute)) = lower(trim(p.applicants))` and filter `p.status = 'Granted'`.  
**Test covering this:** Dhairya Q7/Q13 regression and patent join validator checks.

### P7: Multi-Stage HAVING Or Complete Reasoning Failure (Q14, Q15, Q16)

**Original question:** Financial audit and rising-star comparisons requiring multiple stages.  
**Wrong SQL generated:** Truncated `HAVING`, incomplete SQL, or no SQL at all.  
**Why it failed:** The planner did not fully decompose multi-stage filters and comparative ranking logic.  
**Fix applied:** Prompt templates require complete CTE, `GROUP BY`, and `HAVING` stages; validators reject incomplete SQL and low-confidence answers trigger correction or clarification.  
**Test covering this:** Dhairya Q14/Q15/Q16 regression and result-anomaly detector tests.
