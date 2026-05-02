# D4-01 Table Profiles

- Live tables: 80
- db_struct.sql tables: 58
- Zero-row live tables: 56
- Non-zero live tables: 24

| Priority | Table | Rows | In db_struct.sql | Reference frequency |
|---:|---|---:|---|---:|
| 1 | `researchers` | 50000 | False | 1867 |
| 2 | `publications` | 50000 | False | 810 |
| 3 | `funding` | 0 | False | 807 |
| 4 | `institutions` | 181 | False | 536 |
| 5 | `projects` | 0 | False | 518 |
| 6 | `labs` | 0 | False | 349 |
| 7 | `innovation_grant_from_govt` | 50000 | True | 306 |
| 8 | `academic_courses_details` | 50000 | True | 305 |
| 9 | `keywords` | 0 | False | 282 |
| 10 | `patents` | 0 | False | 261 |
| 11 | `combined_ipo_patent_data` | 50000 | True | 184 |
| 12 | `funding_records` | 0 | False | 172 |
| 13 | `collaborations` | 0 | False | 165 |
| 14 | `research_documents` | 0 | False | 119 |
| 15 | `innovations_at_various_stages_of_technology_readiness_level` | 50000 | True | 118 |
| 16 | `sanctioned_intake` | 1000 | True | 89 |
| 17 | `advance_search_data` | 0 | True | 88 |
| 18 | `tb_institute_mstr` | 1000 | True | 88 |
| 19 | `phd_students` | 1000 | True | 79 |
| 20 | `actual_student_strength` | 1000 | True | 78 |
| 21 | `financial_expenses_capital` | 1000 | True | 73 |
| 22 | `financial_expenses_operational` | 1000 | True | 73 |
| 23 | `researcher_publications` | 0 | False | 71 |
| 24 | `incubation_details` | 0 | True | 68 |
| 25 | `expertise` | 0 | True | 67 |
| 26 | `patents_details` | 1000 | True | 65 |
| 27 | `seed_funding` | 0 | True | 57 |
| 28 | `scraped_data` | 0 | True | 49 |
| 29 | `researcher_labs` | 0 | False | 47 |
| 30 | `scraped_data_save` | 0 | True | 46 |
| 31 | `scraped_raw_data` | 0 | True | 46 |
| 32 | `audit_events` | 807 | False | 44 |
| 33 | `advance_search_data_15_12` | 0 | True | 42 |
| 34 | `advance_search_data_old` | 0 | True | 42 |
| 35 | `combined_ipo_patent_data_old` | 0 | True | 42 |
| 36 | `fdi_investment` | 0 | True | 42 |
| 37 | `faculty_strength` | 0 | True | 41 |
| 38 | `ipo_patent_details_flat` | 0 | True | 37 |
| 39 | `nirf_extracted_table` | 0 | True | 36 |
| 40 | `placements_and_higher_studies` | 1000 | True | 36 |
| 41 | `research_consultancy_details_consultancy` | 1000 | True | 36 |
| 42 | `startups_turnover_50_lacs` | 0 | True | 35 |
| 43 | `ipo_patent_details_flat_old` | 0 | True | 34 |
| 44 | `publication_keywords` | 0 | False | 32 |
| 45 | `research_consultancy_details_sponsered` | 1000 | True | 31 |
| 46 | `startup_recognition` | 1000 | True | 31 |
| 47 | `user_registration` | 0 | True | 29 |
| 48 | `nirf_pdf_record` | 0 | True | 28 |
| 49 | `faculty_details` | 1000 | True | 26 |
| 50 | `tb_institute_scrap_data_url` | 0 | True | 25 |
| 51 | `fdp_details` | 0 | True | 24 |
| 52 | `nirf_table_row` | 0 | True | 24 |
| 53 | `package_data` | 0 | True | 24 |
| 54 | `tb_goi_ministries_mstr` | 0 | True | 24 |
| 55 | `tb_academic_year_mstr` | 0 | True | 23 |
| 56 | `tb_course_program_types` | 0 | True | 22 |
| 57 | `founders_of_fortune_500_companies` | 0 | True | 21 |
| 58 | `master_expertise` | 0 | True | 21 |
| 59 | `startup_receiving_vc_investment` | 0 | True | 21 |
| 60 | `auth_user` | 0 | True | 19 |
| 61 | `role_data` | 0 | True | 17 |
| 62 | `auth_group` | 0 | True | 16 |
| 63 | `llm_cost_log` | 0 | False | 16 |
| 64 | `auth_permission` | 0 | True | 15 |
| 65 | `django_session` | 0 | True | 15 |
| 66 | `auth_group_permissions` | 0 | True | 14 |
| 67 | `auth_user_groups` | 0 | True | 14 |
| 68 | `django_content_type` | 0 | True | 14 |
| 69 | `django_migrations` | 0 | True | 14 |
| 70 | `user_registration_old` | 0 | True | 14 |
| 71 | `auth_user_user_permissions` | 0 | True | 13 |
| 72 | `django_admin_log` | 0 | True | 13 |
| 73 | `startup_recognition_old` | 0 | True | 13 |
| 74 | `adv_se` | 0 | True | 12 |
| 75 | `audit_event_ids` | 807 | False | 2 |
| 76 | `alembic_version` | 1 | False | 1 |
| 77 | `audit_events_2026` | 807 | False | 1 |
| 78 | `audit_events_after_2026` | 0 | False | 1 |
| 79 | `audit_events_before_2026` | 0 | False | 1 |
| 80 | `audit_events_unpartitioned_d4_backup` | 807 | False | 1 |
