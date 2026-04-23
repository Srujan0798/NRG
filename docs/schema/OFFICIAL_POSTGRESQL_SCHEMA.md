# Official PostgreSQL Schema — NRG Production Database

**Source:** `db_struct.sql` (pg_dump from PostgreSQL 14.20, dumped 2026-01-09)
**Total Tables:** 58
**Dhairya Benchmark Queries:** 17 (all reference PostgreSQL tables)

---

## Summary

| Category | Count | Tables |
|----------|-------|--------|
| Academic / Courses | 6 | `academic_courses_details`, `actual_student_strength`, `phd_students`, `sanctioned_intake`, `tb_academic_year_mstr`, `tb_course_program_types` |
| Innovation / TRL | 2 | `innovations_at_various_stages_of_technology_readiness_level`, `innovation_grant_from_govt` |
| Financial | 2 | `financial_expenses_capital`, `financial_expenses_operational` |
| Patents / IPO | 4 | `combined_ipo_patent_data`, `combined_ipo_patent_data_old`, `ipo_patent_details_flat`, `ipo_patent_details_flat_old`, `patents_details` |
| Incubation / Startups | 6 | `incubation_details`, `seed_funding`, `startup_recognition`, `startup_recognition_old`, `startups_turnover_50_lacs`, `startup_receiving_vc_investment` |
| Placement | 3 | `placements_and_higher_studies`, `package_data`, `role_data` |
| Faculty | 4 | `faculty_details`, `faculty_strength`, `fdp_details`, `expertise`, `master_expertise` |
| NIRF / Rankings | 3 | `nirf_extracted_table`, `nirf_pdf_record`, `nirf_table_row` |
| Consultancy | 2 | `research_consultancy_details_consultancy`, `research_consultancy_details_sponsered` |
| scraped_data | 4 | `scraped_data`, `scraped_data_save`, `scraped_raw_data`, `advance_search_data`, `advance_search_data_15_12`, `advance_search_data_old` |
| FDI / Investment | 1 | `fdi_investment` |
| Institute Masters | 3 | `tb_institute_mstr`, `tb_institute_scrap_data_url`, `tb_goi_ministries_mstr` |
| User / Auth (Django) | 9 | `user_registration`, `user_registration_old`, `auth_user`, `auth_group`, `auth_permission`, `auth_user_groups`, `auth_user_user_permissions`, `django_admin_log`, `django_content_type`, `django_migrations`, `django_session` |
| Misc | 2 | `founders_of_fortune_500_companies` |

---

## Detailed Table Documentation

---

### `academic_courses_details` (10 columns)
**Purpose:** Innovation curriculum courses across institutions with credit scoring.
**Dhairya Q#:** 1, 2, 8, 9, 10, 11, 12, 13, 14
**Criticality:** HIGH — Most referenced table in benchmark

| Column | Type | Description |
|--------|------|-------------|
| `financial_year` | text | Year in format `2022-23` |
| `title_of_course` | text | Course name |
| `course_code` | text | Course code |
| `type_of_course` | text | e.g., Innovation, Core |
| `level_of_course` | text | `UG`, `PG`, `PhD` |
| `course_offering_department` | text | Department offering the course |
| `total_credit_score` | text | Format `"3:1"` (lecture:tutorial) — MUST parse with SPLIT_PART |
| `institute` | text | Institution name |
| `as_on_year` | text | Snapshot year |
| `id` | integer NOT NULL | Primary key |

**Key Pattern:** `total_credit_score` uses format `"3:1"` — parsing requires `SPLIT_PART(total_credit_score, ':', 1)::double precision`

---

### `actual_student_strength` (16 columns)
**Purpose:** Student enrollment by program, gender, state.
**Dhairya Q#:** None directly

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `program` | text | Program name |
| `male_students` | integer | Male count |
| `female_students` | integer | Female count |
| ... | ... | (12 more columns) |

---

### `adv_se` (0 columns — likely empty/placeholder)
**Dhairya Q#:** None

---

### `advance_search_data` (37 columns)
**Purpose:** Indexed research publication data.
**Dhairya Q#:** None directly
**Similar to:** `scraped_data`

---

### `advance_search_data_15_12` (35 columns)
**Purpose:** Historical search data (pre-2020).
**Dhairya Q#:** None

---

### `advance_search_data_old` (35 columns)
**Purpose:** Legacy search data.
**Dhairya Q#:** None

---

### `auth_group` (2 columns)
**Purpose:** Django auth groups.
**Dhairya Q#:** None
**Skip for NRG**

---

### `auth_group_permissions` (3 columns)
**Purpose:** Django auth many-to-many.
**Dhairya Q#:** None

---

### `auth_permission` (4 columns)
**Purpose:** Django auth permissions.
**Dhairya Q#:** None

---

### `auth_user` (11 columns)
**Purpose:** Django user accounts.
**Dhairya Q#:** None

---

### `auth_user_groups` (3 columns)
**Purpose:** Django auth many-to-many.
**Dhairya Q#:** None

---

### `auth_user_user_permissions` (3 columns)
**Purpose:** Django auth many-to-many.
**Dhairya Q#:** None

---

### `combined_ipo_patent_data` (34 columns)
**Purpose:** Detailed IPO patent records — applicants, status, application numbers.
**Dhairya Q#:** 7, 13

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `oid` | text | Object ID |
| `application_number` | text | Patent application number |
| `applicants` | text | Who applied (institute/person) |
| `status` | text | `Granted`, `Pending`, etc. |
| ... | ... | (29 more columns) |

**Key Pattern:** Q7 (Cost of Innovation) uses `applicants` for join, `status = 'Granted'` filter.

---

### `combined_ipo_patent_data_old` (34 columns)
**Purpose:** Legacy patent data.
**Dhairya Q#:** None

---

### `django_admin_log` (9 columns)
**Dhayra Q#:** None — Django internal, skip

---

### `django_content_type` (3 columns)
**Dhairya Q#:** None — Django internal, skip

---

### `django_migrations` (4 columns)
**Dhairya Q#:** None — Django internal, skip

---

### `django_session` (3 columns)
**Dhairya Q#:** None — Django internal, skip

---

### `expertise` (10 columns)
**Purpose:** Faculty expertise and research areas.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `name` | character varying | Faculty name |
| `designation` | character varying | Title |
| `email` | character varying | Email |
| ... | ... | (6 more columns) |

---

### `faculty_details` (4 columns)
**Purpose:** Faculty counts per institute.

| Column | Type | Description |
|--------|------|-------------|
| `num_faculties` | integer | Count |
| `institute` | text | Institution name |
| `as_on_year` | text | Snapshot year |
| `id` | integer NOT NULL | Primary key |

---

### `faculty_strength` (11 columns)
**Purpose:** Detailed faculty demographics by gender, category.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `institute` | character varying(100) | Institution |
| `academic_year` | character varying(10) | Year |
| ... | ... | (8 more columns) |

---

### `fdi_investment` (6 columns)
**Purpose:** Foreign direct investment in startups.

| Column | Type | Description |
|--------|------|-------------|
| `startup_name` | text | Startup |
| `investment_received` | bigint | Amount |
| `year_of_receiving` | text | Year |
| `institute` | text | Institution |
| ... | ... | (2 more) |

---

### `fdp_details` (9 columns)
**Purpose:** Faculty Development Programs.

| Column | Type | Description |
|--------|------|-------------|
| `financial_year` | text | Year |
| `title_of_course` | text | FDP title |
| `fdp_sponsered` | text | Sponsor |
| `certificate_offering_department` | text | Department |
| ... | ... | (5 more) |

---

### `financial_expenses_capital` (8 columns)
**Purpose:** Capital expenditure — library, equipment, workshops.
**Dhairya Q#:** 14

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `financial_year` | text | Year |
| `library` | bigint | Library spending |
| `equipment` | bigint | Equipment spending |
| `workshops` | bigint | Workshop spending |
| ... | ... | (4 more) |

---

### `financial_expenses_operational` (7 columns)
**Purpose:** Operational expenditure — salaries, maintenance, seminars.
**Dhairya Q#:** 16

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `financial_year` | text | Year |
| `salaries` | bigint | Salary spending |
| `maintenance` | bigint | Maintenance |
| `seminars` | bigint | Seminar costs |
| ... | ... | (3 more) |

---

### `founders_of_fortune_500_companies` (8 columns)
**Purpose:** Alumni founders at Fortune 500 companies.

| Column | Type | Description |
|--------|------|-------------|
| `name_of_alumni` | text | Founder name |
| `program_passed_from` | text | Program |
| `year_of_passing` | text | Graduation year |
| `comapny_name` | text | Company |
| ... | ... | (4 more) |

---

### `incubation_details` (10 columns)
**Purpose:** Pre-incubation + incubation units, expenditure, income.
**Dhairya Q#:** 13

| Column | Type | Description |
|--------|------|-------------|
| `financial_year` | text | Year |
| `no_of_pre_incubation_units` | integer | Pre-incubated startups |
| `expenditure_on_pre_incubation_activities` | bigint | Spending |
| `income_generated_pre_incubation` | bigint | Revenue |
| `no_of_incubation_units` | integer | Active incubatees |
| ... | ... | (5 more) |

---

### `innovation_grant_from_govt` (6 columns)
**Purpose:** Government grants by organization and institute.
**Dhairya Q#:** 3, 4

| Column | Type | Description |
|--------|------|-------------|
| `gov_organisation_name` | text | Funding agency |
| `grant_received` | bigint | Amount |
| `year_of_receiving` | text | Year |
| `institute` | text | Institution |
| `id` | integer | Primary key |
| `financial_year` | text | Year |

**Key Pattern:** Q3 (YoY grant drop >50%) uses CTE + GROUP BY on `year_of_receiving`. Q4 (top 5 agencies) uses `GROUP BY gov_organisation_name ORDER BY SUM(grant_received) DESC`.

---

### `innovations_at_various_stages_of_technology_readiness_level` (6 columns)
**Purpose:** TRL stages per innovation.
**Dhairya Q#:** 5, 6, 17

| Column | Type | Description |
|--------|------|-------------|
| `innovation_name` | text | Innovation title |
| `stage_of_technology` | text | `Level 1` through `Level 9` |
| `financial_year` | text | Year |
| `institute` | text | Institution |
| `as_on_year` | text | Snapshot |
| `id` | integer | Primary key |

**Critical Synonym Mappings:**
- `TRL 9` = `Level 9` = `Market Ready`
- `TRL 8` = `Level 8` = `Commissioned`
- `TRL 7` = `Level 7` = `System Test`
- `TRL 6` = `Level 6` = `Technology Demonstration`
- `TRL 5` = `Level 5` = `Lab Validation` (Q5 asks about this)
- `TRL 4` = `Level 4` = `Lab Validation` (wait — Q5 says Lab Validation = Level 4?)

**Discrepancy Note:** Q5 mentions "Lab Validation (Level 4)" but the synonym mapping suggests Level 5 is also Lab Validation. Verify actual DB values.

---

### `ipo_patent_details_flat` (28 columns)
**Purpose:** IPO/Patent data flattened.
**Dhairya Q#:** None

---

### `ipo_patent_details_flat_old` (28 columns)
**Purpose:** Legacy patent data.
**Dhairya Q#:** None

---

### `master_expertise` (3 columns)
**Purpose:** Institute-department expertise mapping.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `institute` | character varying | Institution |
| `department` | character varying | Department |

---

### `nirf_extracted_table` (5 columns)
**Purpose:** NIRF ranking data extraction.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `pdf_record_id` | integer NOT NULL | FK to nirf_pdf_record |
| `title` | character varying(255) NOT NULL | Ranking metric |
| `header` | jsonb | Header data |
| `row_data` | jsonb | Row values |

---

### `nirf_pdf_record` (6 columns)
**Purpose:** NIRF PDF upload records.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `institute` | character varying(255) NOT NULL | Institution |
| `year` | character varying(10) NOT NULL | Year |
| `uploaded_by` | character varying(255) | Uploader |
| `uploaded_at` | timestamp without time zone | Upload time |
| `file_path` | character varying(512) | File location |

---

### `nirf_table_row` (3 columns)
**Purpose:** NIRF table row data.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `table_id` | integer NOT NULL | FK to nirf_extracted_table |
| `data` | jsonb NOT NULL | Row data |

---

### `package_data` (4 columns)
**Purpose:** Placement salary packages.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `name` | character varying | Student name |
| `package` | character varying | Salary amount |
| `status` | character varying | Placement status |

---

### `patents_details` (7 columns)
**Purpose:** Patent summary by year — published/granted/commercialized.

| Column | Type | Description |
|--------|------|-------------|
| `financial_year` | text | Year |
| `patents_published` | integer | Filed |
| `patents_granted` | integer | Granted |
| `patents_commercialized` | integer | Commercialized |
| `institute` | text | Institution |
| `as_on_year` | text | Snapshot |
| `id` | integer | Primary key |

---

### `phd_students` (7 columns)
**Purpose:** PhD student counts by program type.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `financial_year` | text | Year |
| `program_type` | text | PhD program type |
| `total` | integer | Student count |
| `institute` | text | Institution |
| `as_on_year` | text | Snapshot |
| `id` | integer | Primary key |

---

### `placements_and_higher_studies` (14 columns)
**Purpose:** Placement rates, median salary, higher studies.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `program` | text | Program name |
| `year_of_intake` | text | Intake year |
| `students_intaken` | integer | Intake count |
| `students_placed` | integer | Placed count |
| `median_package` | integer | Median salary |
| ... | ... | (8 more columns) |

---

### `research_consultancy_details_consultancy` (7 columns)
**Purpose:** Consultancy projects and revenue.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `financial_year` | text | Year |
| `consultancy_projects` | integer | Project count |
| `client_organisations` | integer | Client count |
| `revenue_generated` | bigint | Revenue |
| `institute` | text | Institution |
| ... | ... | (2 more) |

---

### `research_consultancy_details_sponsered` (7 columns)
**Purpose:** Sponsored research projects.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `financial_year` | text | Year |
| `sponsered_projects` | integer | Project count |
| `funding_agencies` | integer | Agency count |
| `funding_amount` | bigint | Funding |
| `institute` | text | Institution |
| ... | ... | (2 more) |

---

### `role_data` (3 columns)
**Purpose:** Placement role categories.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `name` | character varying | Role name |
| `status` | character varying | Status |

---

### `sanctioned_intake` (6 columns)
**Purpose:** Sanctioned seats per program.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `program` | text | Program name |
| `financial_year` | text | Year |
| `seats` | integer | Sanctioned seats |
| `institute` | text | Institution |
| `as_on_year` | text | Snapshot |

---

### `scraped_data` (36 columns)
**Purpose:** Scopus/OpenAlex bibliometric data.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `title` | text | Paper title |
| `authors` | text | Author names |
| `guide` | text | Guide/supervisor |
| `year` | text | Publication year |
| `journal` | text | Journal name |
| `doi` | text | DOI |
| ... | ... | (29 more columns) |

---

### `scraped_data_save` (36 columns)
**Purpose:** Backup of scraped bibliometric data.
**Dhairya Q#:** None

---

### `scraped_raw_data` (36 columns)
**Purpose:** Raw scraped data before processing.
**Dhairya Q#:** None

---

### `seed_funding` (10 columns)
**Purpose:** Startup seed funding and DPIIT registration.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `startup_name` | character varying(255) | Startup |
| `dpiit_no` | character varying(100) | DPIIT number |
| `seed_funding_received` | bigint | Amount |
| `year_of_receiving` | text | Year |
| `institute` | text | Institution |
| ... | ... | (5 more) |

---

### `startup_receiving_vc_investment` (7 columns)
**Purpose:** VC investment in startups.

| Column | Type | Description |
|--------|------|-------------|
| `startup_name` | text | Startup |
| `amount_received` | bigint | Investment amount |
| `organisation_name` | text | VC firm |
| `year_of_receiving` | text | Year |
| `institute` | text | Institution |
| ... | ... | (3 more) |

---

### `startup_recognition` (6 columns)
**Purpose:** Recognized startups by institute.

| Column | Type | Description |
|--------|------|-------------|
| `startup_name` | text | Startup |
| `year_of_recognition` | text | Year recognized |
| `registration_no` | text | Registration number |
| `institute` | text | Institution |
| `dpiit_no` | text | DPIIT number |
| `as_on_year` | text | Snapshot |

---

### `startup_recognition_old` (6 columns)
**Purpose:** Legacy startup recognition data.

---

### `startups_turnover_50_lacs` (6 columns)
**Purpose:** Startups with >50 lakh turnover.

| Column | Type | Description |
|--------|------|-------------|
| `startup_name` | text | Startup |
| `company_turnover` | bigint | Turnover amount |
| `financial_year` | text | Year |
| `institute` | text | Institution |
| `as_on_year` | text | Snapshot |
| `id` | integer | Primary key |

---

### `tb_academic_year_mstr` (3 columns)
**Purpose:** Academic year master data.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `year` | integer | Year value |
| `academic_year` | character varying | Academic year string |

---

### `tb_course_program_types` (2 columns)
**Purpose:** Course program type master.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `program_name` | character varying | Program name |

---

### `tb_goi_ministries_mstr` (7 columns)
**Purpose:** Government of India ministries reference table.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `name` | character varying | Ministry name |
| `short_name` | character varying | Abbreviation |
| `address` | character varying | Address |
| ... | ... | (4 more) |

---

### `tb_institute_mstr` (9 columns)
**Purpose:** Institute master data.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `institute_name` | character varying(255) | Full name |
| `short_name` | character varying(100) | Abbreviation |
| `institute_type` | character varying(100) | Type |
| ... | ... | (6 more) |

---

### `tb_institute_scrap_data_url` (10 columns)
**Purpose:** Scrape URLs for institutes.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `institute_name` | character varying(255) | Institute |
| `short_name` | character varying(100) | Short name |
| `institute_type` | character varying(100) | Type |
| `scrap_url` | character varying(512) | URL to scrape |
| ... | ... | (6 more) |

---

### `user_registration` (17 columns)
**Purpose:** NRG user accounts.
**Dhairya Q#:** None — NRG auth system

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer NOT NULL | Primary key |
| `username` | character varying(50) | Username |
| `email` | character varying(254) | Email |
| `password` | character varying(128) | Hashed password |
| ... | ... | (14 more columns) |

---

### `user_registration_old` (10 columns)
**Purpose:** Legacy user data.

---

## Dhairya Query → Table Mapping

| Q# | Tables Used | Critical Columns |
|----|-------------|------------------|
| Q1 | `academic_courses_details` | `total_credit_score` (format "3:1"), `institute`, `financial_year` |
| Q2 | `academic_courses_details` | `level_of_course` (`UG`, `PhD`), `institute` |
| Q3 | `innovation_grant_from_govt` | `grant_received`, `year_of_receiving`, `institute` |
| Q4 | `innovation_grant_from_govt` | `gov_organisation_name`, `grant_received` |
| Q5 | `innovations_at_various_stages_of_technology_readiness_level` | `stage_of_technology`, `institute` |
| Q6 | `innovations_at_various_stages_of_technology_readiness_level` | `stage_of_technology` (`Level 9`), `innovation_name`, `institute` |
| Q7 | `innovation_grant_from_govt` + `combined_ipo_patent_data` | `applicants`, `status='Granted'`, `grant_received` |
| Q8 | `academic_courses_details` | `level_of_course='PG'`, `institute`, `financial_year` |
| Q9 | `academic_courses_details` | `level_of_course='PhD'`, `institute` |
| Q10 | `academic_courses_details` | `level_of_course` (`UG`, `PhD`), `institute` |
| Q11 | `academic_courses_details` | `level_of_course='PG'`, `institute`, `financial_year` |
| Q12 | `academic_courses_details` | `level_of_course` (`UG`, `PhD`), `institute`, `financial_year` |
| Q13 | `academic_courses_details` + `incubation_details` | course counts vs incubation units |
| Q14 | `academic_courses_details` + `financial_expenses_capital` | course intensity vs capital expenditure |
| Q15 | (error — no query content visible) | |
| Q16 | `innovation_grant_from_govt` + `financial_expenses_operational` | high grants vs low salaries |
| Q17 | `innovations_at_various_stages_of_technology_readiness_level` | stage distribution across TRL levels |

---

## Enum Values Discovered

### `level_of_course` in `academic_courses_details`
- `UG` — Undergraduate
- `PG` — Postgraduate
- `PhD` — Doctoral

### `stage_of_technology` in `innovations_at_various_stages_of_technology_readiness_level`
- `Level 1` through `Level 9`
- Synonyms: `TRL 1`–`TRL 9`, `Market Ready` = `Level 9`, `Lab Validation` = `Level 4` or `Level 5`

### `status` in `combined_ipo_patent_data`
- `Granted`
- `Pending`
- `Abandoned`

### `type_of_course` in `academic_courses_details`
- (not fully enumerated — likely "Innovation", "Core", "Elective")