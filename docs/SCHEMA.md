# NRG Schema Reference

Generated: 2026-04-26T18:15:35.184589+00:00
Source of truth: `db_struct.sql` in this repository.
Table count: 58 parsed `CREATE TABLE public.*` statements.

This document is intentionally mechanical: it records the production table and column surface exactly as parsed from the PostgreSQL dump. Business explanations live in `docs/schema/OFFICIAL_POSTGRESQL_SCHEMA.md`; this file is the quick handoff reference developers should keep open while debugging SQL generation.

## Critical SQL Rules

- `academic_courses_details.total_credit_score` is text in `X:Y` format. Never cast it directly to integer.
- TRL user terms must normalize to database values such as `Level 9` before filtering `stage_of_technology`.
- Patent-cost joins use `innovation_grant_from_govt.institute = combined_ipo_patent_data.applicants` and filter granted patents first.
- Funding trend queries must aggregate by institute and year before year-over-year comparison.
- Tier-filtered API responses must remove PII fields after SQL execution as well as before synthesis.

## Table Groups

- **Academic and student data** (6): `academic_courses_details`, `actual_student_strength`, `phd_students`, `sanctioned_intake`, `tb_academic_year_mstr`, `tb_course_program_types`
- **Django and auth support** (12): `auth_group`, `auth_group_permissions`, `auth_permission`, `auth_user`, `auth_user_groups`, `auth_user_user_permissions`, `django_admin_log`, `django_content_type`, `django_migrations`, `django_session`, `user_registration`, `user_registration_old`
- **Finance, consultancy, and investment** (8): `fdi_investment`, `financial_expenses_capital`, `financial_expenses_operational`, `research_consultancy_details_consultancy`, `research_consultancy_details_sponsered`, `seed_funding`, `startup_receiving_vc_investment`, `startups_turnover_50_lacs`
- **Innovation, TRL, grants, and patents** (7): `combined_ipo_patent_data`, `combined_ipo_patent_data_old`, `innovation_grant_from_govt`, `innovations_at_various_stages_of_technology_readiness_level`, `ipo_patent_details_flat`, `ipo_patent_details_flat_old`, `patents_details`
- **Institutions and ministries** (3): `tb_goi_ministries_mstr`, `tb_institute_mstr`, `tb_institute_scrap_data_url`
- **Other operational tables** (6): `adv_se`, `fdp_details`, `founders_of_fortune_500_companies`, `package_data`, `placements_and_higher_studies`, `role_data`
- **Search, publications, and rankings** (13): `advance_search_data`, `advance_search_data_15_12`, `advance_search_data_old`, `expertise`, `faculty_details`, `faculty_strength`, `master_expertise`, `nirf_extracted_table`, `nirf_pdf_record`, `nirf_table_row`, `scraped_data`, `scraped_data_save`, `scraped_raw_data`
- **Startup and incubation** (3): `incubation_details`, `startup_recognition`, `startup_recognition_old`

## Tables and Columns

### 1. `academic_courses_details`

- Columns: 10
- Primary keys parsed inline: none declared inline
- Sequences: academic_courses_details_id_seq
- Production notes:
  - `total_credit_score` is stored as text in `X:Y` format. Production SQL must parse it with `SPLIT_PART(total_credit_score, ':', 1)::double precision` for PostgreSQL.
  - Hot filters: `institute`, `financial_year`, `level_of_course`.

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `financial_year` | `text` | yes | `` |
| `title_of_course` | `text` | yes | `` |
| `course_code` | `text` | yes | `` |
| `type_of_course` | `text` | yes | `` |
| `level_of_course` | `text` | yes | `` |
| `course_offering_department` | `text` | yes | `` |
| `total_credit_score` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `` |

### 2. `actual_student_strength`

- Columns: 16
- Primary keys parsed inline: none declared inline
- Sequences: actual_student_strength_new_id_seq1

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `program` | `text` | yes | `` |
| `male_students` | `integer` | yes | `` |
| `female_students` | `integer` | yes | `` |
| `total_students` | `integer` | yes | `` |
| `within_state` | `integer` | yes | `` |
| `outside_state` | `integer` | yes | `` |
| `outside_country` | `integer` | yes | `` |
| `economically_backward` | `integer` | yes | `` |
| `socially_challenged` | `integer` | yes | `` |
| `reimbursed_by_government` | `integer` | yes | `` |
| `reimbursed_by_institution` | `integer` | yes | `` |
| `reimbursed_by_private` | `integer` | yes | `` |
| `not_reimbursed` | `integer` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |

### 3. `adv_se`

- Columns: 0
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| _No columns parsed from dump body_ |  |  |  |

### 4. `advance_search_data`

- Columns: 37
- Primary keys parsed inline: none declared inline
- Sequences: advance_search_data_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `title` | `text` | yes | `` |
| `authors` | `text` | yes | `` |
| `guide` | `text` | yes | `` |
| `domain` | `text` | yes | `` |
| `subdomain` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `year` | `text` | yes | `` |
| `url` | `text` | yes | `` |
| `abstract` | `text` | yes | `` |
| `type` | `text` | yes | `` |
| `collaboration` | `text` | yes | `` |
| `metadata` | `text` | yes | `` |
| `citation_id` | `text` | yes | `` |
| `total_citations` | `text` | yes | `` |
| `recent_citations` | `text` | yes | `` |
| `fcr` | `text` | yes | `` |
| `rcr` | `text` | yes | `` |
| `altmetrics_details` | `text` | yes | `` |
| `altmetrics_counts` | `text` | yes | `` |
| `document_type` | `text` | yes | `` |
| `source` | `text` | yes | `` |
| `open_access_status` | `text` | yes | `` |
| `sustainable_development_goal` | `text` | yes | `` |
| `fwci` | `text` | yes | `` |
| `citation_percentile` | `text` | yes | `` |
| `cited_by` | `text` | yes | `` |
| `related_to` | `text` | yes | `` |
| `doi` | `text` | yes | `` |
| `orcid` | `text` | yes | `` |
| `issn` | `text` | yes | `` |
| `topic` | `text` | yes | `` |
| `field` | `text` | yes | `` |
| `subfield` | `text` | yes | `` |
| `fetched_from` | `text` | yes | `` |
| `title_backup` | `text` | yes | `` |
| `abstract_backup` | `text` | yes | `` |

### 5. `advance_search_data_15_12`

- Columns: 35
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `nextval('public.advance_search_data_id_seq'::regclass)` |
| `title` | `text` | yes | `` |
| `authors` | `text` | yes | `` |
| `guide` | `text` | yes | `` |
| `domain` | `text` | yes | `` |
| `subdomain` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `year` | `text` | yes | `` |
| `url` | `text` | yes | `` |
| `abstract` | `text` | yes | `` |
| `type` | `text` | yes | `` |
| `collaboration` | `text` | yes | `` |
| `metadata` | `text` | yes | `` |
| `citation_id` | `text` | yes | `` |
| `total_citations` | `text` | yes | `` |
| `recent_citations` | `text` | yes | `` |
| `fcr` | `text` | yes | `` |
| `rcr` | `text` | yes | `` |
| `altmetrics_details` | `text` | yes | `` |
| `altmetrics_counts` | `text` | yes | `` |
| `document_type` | `text` | yes | `` |
| `source` | `text` | yes | `` |
| `open_access_status` | `text` | yes | `` |
| `sustainable_development_goal` | `text` | yes | `` |
| `fwci` | `text` | yes | `` |
| `citation_percentile` | `text` | yes | `` |
| `cited_by` | `text` | yes | `` |
| `related_to` | `text` | yes | `` |
| `doi` | `text` | yes | `` |
| `orcid` | `text` | yes | `` |
| `issn` | `text` | yes | `` |
| `topic` | `text` | yes | `` |
| `field` | `text` | yes | `` |
| `subfield` | `text` | yes | `` |
| `fetched_from` | `text` | yes | `` |

### 6. `advance_search_data_old`

- Columns: 35
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `nextval('public.advance_search_data_id_seq'::regclass)` |
| `title` | `text` | yes | `` |
| `authors` | `text` | yes | `` |
| `guide` | `text` | yes | `` |
| `domain` | `text` | yes | `` |
| `subdomain` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `year` | `text` | yes | `` |
| `url` | `text` | yes | `` |
| `abstract` | `text` | yes | `` |
| `type` | `text` | yes | `` |
| `collaboration` | `text` | yes | `` |
| `metadata` | `text` | yes | `` |
| `citation_id` | `text` | yes | `` |
| `total_citations` | `text` | yes | `` |
| `recent_citations` | `text` | yes | `` |
| `fcr` | `text` | yes | `` |
| `rcr` | `text` | yes | `` |
| `altmetrics_details` | `text` | yes | `` |
| `altmetrics_counts` | `text` | yes | `` |
| `document_type` | `text` | yes | `` |
| `source` | `text` | yes | `` |
| `open_access_status` | `text` | yes | `` |
| `sustainable_development_goal` | `text` | yes | `` |
| `fwci` | `text` | yes | `` |
| `citation_percentile` | `text` | yes | `` |
| `cited_by` | `text` | yes | `` |
| `related_to` | `text` | yes | `` |
| `doi` | `text` | yes | `` |
| `orcid` | `text` | yes | `` |
| `issn` | `text` | yes | `` |
| `topic` | `text` | yes | `` |
| `field` | `text` | yes | `` |
| `subfield` | `text` | yes | `` |
| `fetched_from` | `text` | yes | `` |

### 7. `auth_group`

- Columns: 2
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `name` | `character` | no | `` |

### 8. `auth_group_permissions`

- Columns: 3
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `bigint` | no | `` |
| `group_id` | `integer` | no | `` |
| `permission_id` | `integer` | no | `` |

### 9. `auth_permission`

- Columns: 4
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `name` | `character` | no | `` |
| `content_type_id` | `integer` | no | `` |
| `codename` | `character` | no | `` |

### 10. `auth_user`

- Columns: 11
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `password` | `character` | no | `` |
| `last_login` | `timestamp` | yes | `` |
| `is_superuser` | `boolean` | no | `` |
| `username` | `character` | no | `` |
| `first_name` | `character` | no | `` |
| `last_name` | `character` | no | `` |
| `email` | `character` | no | `` |
| `is_staff` | `boolean` | no | `` |
| `is_active` | `boolean` | no | `` |
| `date_joined` | `timestamp` | no | `` |

### 11. `auth_user_groups`

- Columns: 3
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `bigint` | no | `` |
| `user_id` | `integer` | no | `` |
| `group_id` | `integer` | no | `` |

### 12. `auth_user_user_permissions`

- Columns: 3
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `bigint` | no | `` |
| `user_id` | `integer` | no | `` |
| `permission_id` | `integer` | no | `` |

### 13. `combined_ipo_patent_data`

- Columns: 34
- Primary keys parsed inline: none declared inline
- Sequences: combined_ipo_patent_data_id_seq
- Production notes:
  - Patent applicant institution joins through `applicants`, not a generic `institute` column.
  - Cost-per-patent queries must filter `status = 'Granted'` before aggregation.

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `oid` | `text` | yes | `` |
| `application_number` | `text` | yes | `` |
| `inserted_at` | `timestamp` | yes | `` |
| `source_collection` | `text` | yes | `` |
| `invention_title` | `text` | yes | `` |
| `publication_number` | `text` | yes | `` |
| `publication_date` | `text` | yes | `` |
| `publication_type` | `text` | yes | `` |
| `application_filing_date` | `text` | yes | `` |
| `field_of_invention` | `text` | yes | `` |
| `inventors` | `text` | yes | `` |
| `applicants` | `text` | yes | `` |
| `abstract` | `text` | yes | `` |
| `email_record` | `text` | yes | `` |
| `additional_email` | `text` | yes | `` |
| `application_type` | `text` | yes | `` |
| `examination_request_date` | `text` | yes | `` |
| `first_examination_report_date` | `text` | yes | `` |
| `certificate_issue_date` | `text` | yes | `` |
| `post_grant_journal_date` | `text` | yes | `` |
| `reply_to_fer_date` | `text` | yes | `` |
| `status` | `text` | yes | `` |
| `patent_number` | `text` | yes | `` |
| `date_of_grant` | `text` | yes | `` |
| `legal_status` | `text` | yes | `` |
| `due_date_next_renewal` | `text` | yes | `` |
| `renewal_history` | `jsonb` | yes | `` |
| `aishe_code` | `text` | yes | `` |
| `fetched_at` | `timestamp` | yes | `` |
| `granted_patent_title` | `text` | yes | `` |
| `patent_grant_number` | `text` | yes | `` |
| `university_name` | `text` | yes | `` |
| `fetched_from` | `text` | yes | `` |

### 14. `combined_ipo_patent_data_old`

- Columns: 34
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `nextval('public.combined_ipo_patent_data_id_seq'::regclass)` |
| `oid` | `text` | yes | `` |
| `application_number` | `text` | yes | `` |
| `inserted_at` | `timestamp` | yes | `` |
| `source_collection` | `text` | yes | `` |
| `invention_title` | `text` | yes | `` |
| `publication_number` | `text` | yes | `` |
| `publication_date` | `text` | yes | `` |
| `publication_type` | `text` | yes | `` |
| `application_filing_date` | `text` | yes | `` |
| `field_of_invention` | `text` | yes | `` |
| `inventors` | `text` | yes | `` |
| `applicants` | `text` | yes | `` |
| `abstract` | `text` | yes | `` |
| `email_record` | `text` | yes | `` |
| `additional_email` | `text` | yes | `` |
| `application_type` | `text` | yes | `` |
| `examination_request_date` | `text` | yes | `` |
| `first_examination_report_date` | `text` | yes | `` |
| `certificate_issue_date` | `text` | yes | `` |
| `post_grant_journal_date` | `text` | yes | `` |
| `reply_to_fer_date` | `text` | yes | `` |
| `status` | `text` | yes | `` |
| `patent_number` | `text` | yes | `` |
| `date_of_grant` | `text` | yes | `` |
| `legal_status` | `text` | yes | `` |
| `due_date_next_renewal` | `text` | yes | `` |
| `renewal_history` | `jsonb` | yes | `` |
| `aishe_code` | `text` | yes | `` |
| `fetched_at` | `timestamp` | yes | `` |
| `granted_patent_title` | `text` | yes | `` |
| `patent_grant_number` | `text` | yes | `` |
| `university_name` | `text` | yes | `` |
| `fetched_from` | `text` | yes | `` |

### 15. `django_admin_log`

- Columns: 8
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `action_time` | `timestamp` | no | `` |
| `object_id` | `text` | yes | `` |
| `object_repr` | `character` | no | `` |
| `action_flag` | `smallint` | no | `` |
| `change_message` | `text` | no | `` |
| `content_type_id` | `integer` | yes | `` |
| `user_id` | `integer` | no | `` |

### 16. `django_content_type`

- Columns: 3
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `app_label` | `character` | no | `` |
| `model` | `character` | no | `` |

### 17. `django_migrations`

- Columns: 4
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `bigint` | no | `` |
| `app` | `character` | no | `` |
| `name` | `character` | no | `` |
| `applied` | `timestamp` | no | `` |

### 18. `django_session`

- Columns: 3
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `session_key` | `character` | no | `` |
| `session_data` | `text` | no | `` |
| `expire_date` | `timestamp` | no | `` |

### 19. `expertise`

- Columns: 10
- Primary keys parsed inline: none declared inline
- Sequences: expertise_16_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `name` | `character` | yes | `` |
| `designation` | `character` | yes | `` |
| `email` | `character` | yes | `` |
| `phone` | `character` | yes | `` |
| `phd` | `character` | yes | `` |
| `research` | `character` | yes | `` |
| `image` | `character` | yes | `` |
| `department` | `character` | yes | `` |
| `institute` | `character` | yes | `` |

### 20. `faculty_details`

- Columns: 4
- Primary keys parsed inline: none declared inline
- Sequences: faculty_details_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `num_faculties` | `integer` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `` |

### 21. `faculty_strength`

- Columns: 11
- Primary keys parsed inline: none declared inline
- Sequences: faculty_strength_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `institute` | `character` | yes | `` |
| `academic_year` | `character` | yes | `` |
| `as_on` | `character` | yes | `` |
| `male_strength` | `character` | yes | `` |
| `female_strength` | `character` | yes | `` |
| `total_strength` | `character` | yes | `` |
| `total_sanctioned_strength` | `character` | yes | `` |
| `uploaded_on` | `character` | yes | `` |
| `url` | `character` | yes | `` |
| `types` | `character` | yes | `` |

### 22. `fdi_investment`

- Columns: 6
- Primary keys parsed inline: none declared inline
- Sequences: fdi_investment_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `startup_name` | `text` | yes | `` |
| `investment_received` | `bigint` | yes | `` |
| `year_of_receiving` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `` |

### 23. `fdp_details`

- Columns: 9
- Primary keys parsed inline: none declared inline
- Sequences: fdp_details_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `financial_year` | `text` | yes | `` |
| `title_of_course` | `text` | yes | `` |
| `fdp_sponsered` | `text` | yes | `` |
| `certificate_offering_department` | `text` | yes | `` |
| `program_start_date` | `text` | yes | `` |
| `program_end_date` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `` |

### 24. `financial_expenses_capital`

- Columns: 8
- Primary keys parsed inline: none declared inline
- Sequences: financial_expenses_capital_new_id_seq1

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `financial_year` | `text` | yes | `` |
| `library` | `bigint` | yes | `` |
| `equipment` | `bigint` | yes | `` |
| `workshops` | `bigint` | yes | `` |
| `capital_assets` | `bigint` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |

### 25. `financial_expenses_operational`

- Columns: 7
- Primary keys parsed inline: none declared inline
- Sequences: financial_expenses_operational_new_id_seq1

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `financial_year` | `text` | yes | `` |
| `salaries` | `bigint` | yes | `` |
| `maintenance` | `bigint` | yes | `` |
| `seminars` | `bigint` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |

### 26. `founders_of_fortune_500_companies`

- Columns: 8
- Primary keys parsed inline: none declared inline
- Sequences: founders_of_fortune_500_companies_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `name_of_alumni` | `text` | yes | `` |
| `program_passed_from` | `text` | yes | `` |
| `year_of_passing` | `text` | yes | `` |
| `comapny_name` | `text` | yes | `` |
| `year_of_appearence` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `` |

### 27. `incubation_details`

- Columns: 10
- Primary keys parsed inline: none declared inline
- Sequences: incubation_details_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `financial_year` | `text` | yes | `` |
| `no_of_pre_incubation_units` | `integer` | yes | `` |
| `expenditure_on_pre_incubation_activities` | `bigint` | yes | `` |
| `income_generated_pre_incubation` | `bigint` | yes | `` |
| `no_of_incubation_units` | `integer` | yes | `` |
| `expenditure_on_incubation_activities` | `bigint` | yes | `` |
| `income_generated_incubation` | `bigint` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `` |

### 28. `innovation_grant_from_govt`

- Columns: 6
- Primary keys parsed inline: none declared inline
- Sequences: innovation_grant_from_govt_id_seq
- Production notes:
  - Grant analytics aggregate `grant_received` by institute/year or agency/year before comparison.

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `gov_organisation_name` | `text` | yes | `` |
| `grant_received` | `bigint` | yes | `` |
| `year_of_receiving` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `` |

### 29. `innovations_at_various_stages_of_technology_readiness_level`

- Columns: 6
- Primary keys parsed inline: none declared inline
- Sequences: none
- Production notes:
  - `stage_of_technology` stores canonical strings such as `Level 9`; user-facing terms like TRL 9 and Market Ready must normalize before SQL generation.
  - Hot filters: `institute`, `financial_year`, `stage_of_technology`.

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `innovation_name` | `text` | yes | `` |
| `stage_of_technology` | `text` | yes | `` |
| `financial_year` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `` |

### 30. `ipo_patent_details_flat`

- Columns: 28
- Primary keys parsed inline: none declared inline
- Sequences: ipo_patent_details_flat_id_seq, ipo_patent_details_flat_id_seq1

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `oid` | `text` | yes | `` |
| `application_number` | `text` | yes | `` |
| `inserted_at` | `timestamp` | yes | `` |
| `source_collection` | `text` | yes | `` |
| `invention_title` | `text` | yes | `` |
| `publication_number` | `text` | yes | `` |
| `publication_date` | `text` | yes | `` |
| `publication_type` | `text` | yes | `` |
| `application_filing_date` | `text` | yes | `` |
| `field_of_invention` | `text` | yes | `` |
| `inventors` | `text` | yes | `` |
| `applicants` | `text` | yes | `` |
| `abstract` | `text` | yes | `` |
| `email_record` | `text` | yes | `` |
| `additional_email` | `text` | yes | `` |
| `application_type` | `text` | yes | `` |
| `examination_request_date` | `text` | yes | `` |
| `first_examination_report_date` | `text` | yes | `` |
| `certificate_issue_date` | `text` | yes | `` |
| `post_grant_journal_date` | `text` | yes | `` |
| `reply_to_fer_date` | `text` | yes | `` |
| `status` | `text` | yes | `` |
| `patent_number` | `text` | yes | `` |
| `date_of_grant` | `text` | yes | `` |
| `legal_status` | `text` | yes | `` |
| `due_date_next_renewal` | `text` | yes | `` |
| `renewal_history` | `jsonb` | yes | `` |

### 31. `ipo_patent_details_flat_old`

- Columns: 28
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `oid` | `text` | yes | `` |
| `application_number` | `text` | yes | `` |
| `inserted_at` | `timestamp` | yes | `` |
| `source_collection` | `text` | yes | `` |
| `invention_title` | `text` | yes | `` |
| `publication_number` | `text` | yes | `` |
| `publication_date` | `text` | yes | `` |
| `publication_type` | `text` | yes | `` |
| `application_filing_date` | `text` | yes | `` |
| `field_of_invention` | `text` | yes | `` |
| `inventors` | `text` | yes | `` |
| `applicants` | `text` | yes | `` |
| `abstract` | `text` | yes | `` |
| `email_record` | `text` | yes | `` |
| `additional_email` | `text` | yes | `` |
| `application_type` | `text` | yes | `` |
| `examination_request_date` | `text` | yes | `` |
| `first_examination_report_date` | `text` | yes | `` |
| `certificate_issue_date` | `text` | yes | `` |
| `post_grant_journal_date` | `text` | yes | `` |
| `reply_to_fer_date` | `text` | yes | `` |
| `status` | `text` | yes | `` |
| `patent_number` | `text` | yes | `` |
| `date_of_grant` | `text` | yes | `` |
| `legal_status` | `text` | yes | `` |
| `due_date_next_renewal` | `text` | yes | `` |
| `renewal_history` | `jsonb` | yes | `` |

### 32. `master_expertise`

- Columns: 3
- Primary keys parsed inline: none declared inline
- Sequences: master_expertise_id_seq2

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `institute` | `character` | yes | `` |
| `department` | `character` | yes | `` |

### 33. `nirf_extracted_table`

- Columns: 5
- Primary keys parsed inline: none declared inline
- Sequences: nirf_extracted_table_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `pdf_record_id` | `integer` | no | `` |
| `title` | `character` | no | `` |
| `header` | `jsonb` | yes | `` |
| `created_at` | `timestamp` | yes | `now()` |

### 34. `nirf_pdf_record`

- Columns: 6
- Primary keys parsed inline: none declared inline
- Sequences: nirf_pdf_record_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `institute` | `character` | no | `` |
| `year` | `character` | no | `` |
| `uploaded_by` | `character` | yes | `` |
| `uploaded_at` | `timestamp` | yes | `now()` |
| `pdf_name` | `character` | yes | `` |

### 35. `nirf_table_row`

- Columns: 3
- Primary keys parsed inline: none declared inline
- Sequences: nirf_table_row_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `table_id` | `integer` | no | `` |
| `data` | `jsonb` | no | `` |

### 36. `package_data`

- Columns: 4
- Primary keys parsed inline: none declared inline
- Sequences: package_data_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `name` | `character` | yes | `` |
| `package` | `character` | yes | `` |
| `status` | `character` | yes | `` |

### 37. `patents_details`

- Columns: 7
- Primary keys parsed inline: none declared inline
- Sequences: patents_details_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `financial_year` | `text` | yes | `` |
| `patents_published` | `integer` | yes | `` |
| `patents_granted` | `integer` | yes | `` |
| `patents_commercialized` | `integer` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `` |

### 38. `phd_students`

- Columns: 7
- Primary keys parsed inline: none declared inline
- Sequences: phd_students_new_id_seq1

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `financial_year` | `text` | yes | `` |
| `program_type` | `text` | yes | `` |
| `total` | `integer` | yes | `` |
| `graduate` | `integer` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |

### 39. `placements_and_higher_studies`

- Columns: 14
- Primary keys parsed inline: none declared inline
- Sequences: placements_and_higher_studies_new_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `program` | `text` | yes | `` |
| `year_of_intake` | `text` | yes | `` |
| `students_intaken` | `integer` | yes | `` |
| `students_admitted` | `integer` | yes | `` |
| `year_of_lateral_entry` | `text` | yes | `` |
| `students_admitted_lateral_entry` | `integer` | yes | `` |
| `year_of_graduation` | `text` | yes | `` |
| `graduated_students` | `integer` | yes | `` |
| `placed_students` | `integer` | yes | `` |
| `median_salary_per_annum` | `bigint` | yes | `` |
| `higher_studies_students` | `integer` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |

### 40. `research_consultancy_details_consultancy`

- Columns: 7
- Primary keys parsed inline: none declared inline
- Sequences: research_consultancy_details_consultancy_new_id_seq1
- Production notes:
  - Consultancy metrics are service-income signals; compare after grouping by institute and year.

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `financial_year` | `text` | yes | `` |
| `consultancy_projects` | `integer` | yes | `` |
| `client_organisations` | `integer` | yes | `` |
| `amount_recieved_consultancy_projects` | `bigint` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |

### 41. `research_consultancy_details_sponsered`

- Columns: 7
- Primary keys parsed inline: none declared inline
- Sequences: research_consultancy_details_sponsered_new_id_seq1

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `financial_year` | `text` | yes | `` |
| `sponsered_projects` | `integer` | yes | `` |
| `funding_agencies` | `integer` | yes | `` |
| `amount_recieved_sponsered_research` | `bigint` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |

### 42. `role_data`

- Columns: 3
- Primary keys parsed inline: none declared inline
- Sequences: role_data_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `name` | `character` | yes | `` |
| `status` | `character` | yes | `` |

### 43. `sanctioned_intake`

- Columns: 6
- Primary keys parsed inline: none declared inline
- Sequences: sanctioned_intake_new_id_seq1

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `program` | `text` | yes | `` |
| `financial_year` | `text` | yes | `` |
| `seats` | `integer` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |

### 44. `scraped_data`

- Columns: 36
- Primary keys parsed inline: none declared inline
- Sequences: scraped_data_id_seq, scraped_data_save_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `title` | `text` | yes | `` |
| `authors` | `text` | yes | `` |
| `guide` | `text` | yes | `` |
| `domain` | `text` | yes | `` |
| `subdomain` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `year` | `text` | yes | `` |
| `url` | `text` | yes | `` |
| `abstract` | `text` | yes | `` |
| `type` | `text` | yes | `` |
| `collaboration` | `text` | yes | `` |
| `metadata` | `text` | yes | `` |
| `citation_id` | `text` | yes | `` |
| `total_citations` | `text` | yes | `` |
| `recent_citations` | `text` | yes | `` |
| `fcr` | `text` | yes | `` |
| `rcr` | `text` | yes | `` |
| `altmetrics_details` | `text` | yes | `` |
| `altmetrics_counts` | `text` | yes | `` |
| `document_type` | `text` | yes | `` |
| `source` | `text` | yes | `` |
| `open_access_status` | `text` | yes | `` |
| `sustainable_development_goal` | `text` | yes | `` |
| `fwci` | `text` | yes | `` |
| `citation_percentile` | `text` | yes | `` |
| `cited_by` | `text` | yes | `` |
| `related_to` | `text` | yes | `` |
| `doi` | `text` | yes | `` |
| `orcid` | `text` | yes | `` |
| `issn` | `text` | yes | `` |
| `topic` | `text` | yes | `` |
| `field` | `text` | yes | `` |
| `subfield` | `text` | yes | `` |
| `fetched_from` | `text` | yes | `` |
| `upload_date` | `date` | yes | `` |

### 45. `scraped_data_save`

- Columns: 36
- Primary keys parsed inline: none declared inline
- Sequences: scraped_data_save_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `title` | `text` | yes | `` |
| `authors` | `text` | yes | `` |
| `guide` | `text` | yes | `` |
| `domain` | `text` | yes | `` |
| `subdomain` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `year` | `text` | yes | `` |
| `url` | `text` | yes | `` |
| `abstract` | `text` | yes | `` |
| `type` | `text` | yes | `` |
| `collaboration` | `text` | yes | `` |
| `metadata` | `text` | yes | `` |
| `citation_id` | `text` | yes | `` |
| `total_citations` | `text` | yes | `` |
| `recent_citations` | `text` | yes | `` |
| `fcr` | `text` | yes | `` |
| `rcr` | `text` | yes | `` |
| `altmetrics_details` | `text` | yes | `` |
| `altmetrics_counts` | `text` | yes | `` |
| `document_type` | `text` | yes | `` |
| `source` | `text` | yes | `` |
| `open_access_status` | `text` | yes | `` |
| `sustainable_development_goal` | `text` | yes | `` |
| `fwci` | `text` | yes | `` |
| `citation_percentile` | `text` | yes | `` |
| `cited_by` | `text` | yes | `` |
| `related_to` | `text` | yes | `` |
| `doi` | `text` | yes | `` |
| `orcid` | `text` | yes | `` |
| `issn` | `text` | yes | `` |
| `topic` | `text` | yes | `` |
| `field` | `text` | yes | `` |
| `subfield` | `text` | yes | `` |
| `fetched_from` | `text` | yes | `` |
| `upload_date` | `date` | yes | `` |

### 46. `scraped_raw_data`

- Columns: 36
- Primary keys parsed inline: none declared inline
- Sequences: scraped_raw_data_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `title` | `text` | yes | `` |
| `authors` | `text` | yes | `` |
| `guide` | `text` | yes | `` |
| `domain` | `text` | yes | `` |
| `subdomain` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `year` | `text` | yes | `` |
| `url` | `text` | yes | `` |
| `abstract` | `text` | yes | `` |
| `type` | `text` | yes | `` |
| `collaboration` | `text` | yes | `` |
| `metadata` | `text` | yes | `` |
| `citation_id` | `text` | yes | `` |
| `total_citations` | `text` | yes | `` |
| `recent_citations` | `text` | yes | `` |
| `fcr` | `text` | yes | `` |
| `rcr` | `text` | yes | `` |
| `altmetrics_details` | `text` | yes | `` |
| `altmetrics_counts` | `text` | yes | `` |
| `document_type` | `text` | yes | `` |
| `source` | `text` | yes | `` |
| `open_access_status` | `text` | yes | `` |
| `sustainable_development_goal` | `text` | yes | `` |
| `fwci` | `text` | yes | `` |
| `citation_percentile` | `text` | yes | `` |
| `cited_by` | `text` | yes | `` |
| `related_to` | `text` | yes | `` |
| `doi` | `text` | yes | `` |
| `orcid` | `text` | yes | `` |
| `issn` | `text` | yes | `` |
| `topic` | `text` | yes | `` |
| `field` | `text` | yes | `` |
| `subfield` | `text` | yes | `` |
| `fetched_from` | `text` | yes | `` |
| `upload_date` | `date` | yes | `` |

### 47. `seed_funding`

- Columns: 10
- Primary keys parsed inline: none declared inline
- Sequences: seed_funding_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `startup_name` | `character` | yes | `` |
| `dpiit_no` | `character` | yes | `` |
| `seed_funding_received` | `bigint` | yes | `` |
| `govt_org` | `character` | yes | `` |
| `year_of_receiving_fund` | `character` | yes | `` |
| `achievement_level` | `character` | yes | `` |
| `type_of_investment` | `character` | yes | `` |
| `institute` | `character` | yes | `` |
| `as_on_year` | `character` | yes | `` |

### 48. `startup_receiving_vc_investment`

- Columns: 7
- Primary keys parsed inline: none declared inline
- Sequences: startup_receiving_vc_investment_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `startup_name` | `text` | yes | `` |
| `amount_received` | `bigint` | yes | `` |
| `organisation_name` | `text` | yes | `` |
| `year_of_receiving` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `` |

### 49. `startup_recognition`

- Columns: 6
- Primary keys parsed inline: none declared inline
- Sequences: startup_recognition_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `startup_name` | `text` | yes | `` |
| `year_of_recognition` | `text` | yes | `` |
| `registration_no` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `nextval('public.startup_recognition_id_seq'::regclass)` |

### 50. `startup_recognition_old`

- Columns: 6
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `startup_name` | `text` | yes | `` |
| `year_of_recognition` | `text` | yes | `` |
| `registration_no` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `` |

### 51. `startups_turnover_50_lacs`

- Columns: 6
- Primary keys parsed inline: none declared inline
- Sequences: startups_turnover_50_lacs_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `startup_name` | `text` | yes | `` |
| `company_turnover` | `bigint` | yes | `` |
| `financial_year` | `text` | yes | `` |
| `institute` | `text` | yes | `` |
| `as_on_year` | `text` | yes | `` |
| `id` | `integer` | no | `` |

### 52. `tb_academic_year_mstr`

- Columns: 3
- Primary keys parsed inline: none declared inline
- Sequences: tb_academic_year_mstr_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `year` | `integer` | yes | `` |
| `academic_year` | `character` | yes | `` |

### 53. `tb_course_program_types`

- Columns: 2
- Primary keys parsed inline: none declared inline
- Sequences: tb_course_program_types_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `program_name` | `character` | yes | `` |

### 54. `tb_goi_ministries_mstr`

- Columns: 7
- Primary keys parsed inline: none declared inline
- Sequences: tb_goi_ministries_mstr_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `name` | `character` | yes | `` |
| `short_name` | `character` | yes | `` |
| `address` | `character` | yes | `` |
| `phone_no` | `character` | yes | `` |
| `email` | `character` | yes | `` |
| `website` | `character` | yes | `` |

### 55. `tb_institute_mstr`

- Columns: 9
- Primary keys parsed inline: none declared inline
- Sequences: tb_institute_mstr_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `institute_name` | `character` | yes | `` |
| `short_name` | `character` | yes | `` |
| `institute_type` | `character` | yes | `` |
| `city` | `character` | yes | `` |
| `state` | `character` | yes | `` |
| `address` | `character` | yes | `` |
| `established_year` | `integer` | yes | `` |
| `website_url` | `character` | yes | `` |

### 56. `tb_institute_scrap_data_url`

- Columns: 10
- Primary keys parsed inline: none declared inline
- Sequences: tb_institute_scrap_data_url_id_seq

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `institute_name` | `character` | yes | `` |
| `short_name` | `character` | yes | `` |
| `institute_type` | `character` | yes | `` |
| `city` | `character` | yes | `` |
| `state` | `character` | yes | `` |
| `established_year` | `integer` | yes | `` |
| `address` | `text` | yes | `` |
| `website_url` | `text` | yes | `` |
| `scrap_data_url` | `text` | yes | `` |

### 57. `user_registration`

- Columns: 17
- Primary keys parsed inline: none declared inline
- Sequences: user_registration_id_seq, user_registration_id_seq1

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `username` | `character` | yes | `` |
| `email` | `character` | yes | `` |
| `password` | `character` | yes | `` |
| `confirm_password` | `character` | yes | `` |
| `phone_number` | `character` | yes | `` |
| `role` | `character` | yes | `` |
| `is_approved` | `boolean` | no | `false` |
| `user_info` | `character` | yes | `` |
| `status` | `character` | yes | `` |
| `deleted_by` | `character` | yes | `` |
| `is_email_verified` | `boolean` | yes | `` |
| `email_otp` | `character` | yes | `` |
| `is_otp_verified` | `boolean` | yes | `` |
| `first_password` | `character` | yes | `` |
| `first_login` | `boolean` | yes | `` |
| `email_status` | `character` | yes | `` |

### 58. `user_registration_old`

- Columns: 9
- Primary keys parsed inline: none declared inline
- Sequences: none

| Column | Type | Nullable | Default |
|---|---|---:|---|
| `id` | `integer` | no | `` |
| `username` | `character` | no | `` |
| `email` | `character` | no | `` |
| `password` | `character` | no | `` |
| `confirm_password` | `character` | yes | `` |
| `phone_number` | `character` | yes | `` |
| `role` | `character` | no | `` |
| `is_approved` | `boolean` | no | `false` |
| `user_info` | `character` | yes | `` |

## Verification

Local schema parity evidence for 2026-04-26 is stored in `evidence/2026-04-26/schema_parity_58_58.txt`.
Hot-index plan evidence is stored in `evidence/2026-04-26/explain_index_usage.txt`.
