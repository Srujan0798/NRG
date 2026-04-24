# Mandatory Reads - Ultimate Protocol v4.1

Execution date: 2026-04-25 IST. Evidence folder follows protocol date `2026-04-24`.

Read files:

- `Core_Idea_Clean.md`
- `db_struct.sql`
- `BACKLOG.md`
- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
- `NRG_SELF_AUDIT_REPORT_2026-04-24.md`

## 58 Tables From `db_struct.sql`

1. `academic_courses_details`
2. `actual_student_strength`
3. `adv_se`
4. `advance_search_data`
5. `advance_search_data_15_12`
6. `advance_search_data_old`
7. `auth_group`
8. `auth_group_permissions`
9. `auth_permission`
10. `auth_user`
11. `auth_user_groups`
12. `auth_user_user_permissions`
13. `combined_ipo_patent_data`
14. `combined_ipo_patent_data_old`
15. `django_admin_log`
16. `django_content_type`
17. `django_migrations`
18. `django_session`
19. `expertise`
20. `faculty_details`
21. `faculty_strength`
22. `fdi_investment`
23. `fdp_details`
24. `financial_expenses_capital`
25. `financial_expenses_operational`
26. `founders_of_fortune_500_companies`
27. `incubation_details`
28. `innovation_grant_from_govt`
29. `innovations_at_various_stages_of_technology_readiness_level`
30. `ipo_patent_details_flat`
31. `ipo_patent_details_flat_old`
32. `master_expertise`
33. `nirf_extracted_table`
34. `nirf_pdf_record`
35. `nirf_table_row`
36. `package_data`
37. `patents_details`
38. `phd_students`
39. `placements_and_higher_studies`
40. `research_consultancy_details_consultancy`
41. `research_consultancy_details_sponsered`
42. `role_data`
43. `sanctioned_intake`
44. `scraped_data`
45. `scraped_data_save`
46. `scraped_raw_data`
47. `seed_funding`
48. `startup_receiving_vc_investment`
49. `startup_recognition_old`
50. `startup_recognition`
51. `startups_turnover_50_lacs`
52. `tb_academic_year_mstr`
53. `tb_course_program_types`
54. `tb_goi_ministries_mstr`
55. `tb_institute_mstr`
56. `tb_institute_scrap_data_url`
57. `user_registration`
58. `user_registration_old`

## `total_credit_score`

- DB type: `text`, defined in `db_struct.sql` under `academic_courses_details`.
- Format: `"X:Y"` where `X` is lecture credit and `Y` is tutorial/practical credit.
- Required SQL parsing: `SPLIT_PART(total_credit_score, ':', 1)::double precision` and, when total credit is required, add part 2 after parsing.

## Seven Dhairya Failure Patterns And Fixes

1. P1 SPLIT_PART format blind (Q1): direct integer cast replaced by explicit `"X:Y"` parsing with `SPLIT_PART`/SQLite `SUBSTR` fallback.
2. P2 DISTINCT vs GROUP BY (Q4): ranked metric queries now require `GROUP BY + ORDER BY SUM(metric) DESC LIMIT N`.
3. P3 row-level vs aggregated YoY (Q3/Q11): YoY queries use CTE aggregation grouped by institute/year before self-join.
4. P4 missing/truncated HAVING (Q14/Q16): completeness validator detects trailing clauses and HAVING without GROUP BY.
5. P5 cross-domain follow-up confusion (Q10/Q12): `NRGState.active_domain` preserves the active table/domain across turns.
6. P6 TRL synonym blindness (Q6): TRL/user phrases map to DB values such as `Level 9`.
7. P7 multi-step reasoning failure (Q15): rising-star/average-comparison queries use CTE + average/scalar comparison patterns.

## Local-Fixable Gaps

- GAP-A DB co-sign: patch `src/audit/db_cosign.py` and the audit co-sign Alembic migration to create `audit_events.db_cosign_hmac` with `audit_cosign_trigger`; add tests in `tests/security/test_per_user_audit_binding.py`.
- GAP-B 60-second drift scheduler: add `scripts/vector_drift_scheduler.py` with a 60-second asyncio loop and tests in `tests/observability/test_vector_drift_scheduler.py`.
- GAP-C Hall of Shame: rewrite `src/data/schema/failed_queries/HALL_OF_SHAME.md` with all seven Dhairya failure patterns and exact regression-test references.
