# Schema Gap Analysis — PostgreSQL vs SQLite

**PostgreSQL (Production):** 58 tables
**SQLite (Development):** 18 tables
**Gap:** 40 tables missing from dev

---

## Category 1: MAPPED — Tables in both schemas

Tables that exist in both PostgreSQL and SQLite with roughly equivalent structure.

| PostgreSQL Table | SQLite Equivalent | Column Mapping | Gap Notes |
|-----------------|-------------------|----------------|-----------|
| `research_consultancy_details_consultancy` | ❌ MISSING | — | No SQLite equivalent |
| `research_consultancy_details_sponsered` | ❌ MISSING | — | No SQLite equivalent |
| `user_registration` | ❌ MISSING | — | SQLite uses `refresh_tokens`, different auth |
| `user_registration_old` | ❌ MISSING | — | Legacy only |

**Note:** Our 18 SQLite tables do NOT map to any of the 58 PostgreSQL tables directly — the schemas are completely different. The PostgreSQL schema is a Django-based academic management system, while our SQLite schema is a custom research graph schema.

---

## Category 2: MISSING_CRITICAL — Needed for Dhairya queries

Tables required to answer Dhairya's 17 benchmark queries. **ALL are missing from SQLite.**

### Q1, Q2, Q8, Q9, Q10, Q11, Q12, Q13, Q14 — `academic_courses_details`
```
PostgreSQL: academic_courses_details
SQLite:     MISSING

Columns:
  - financial_year (text)
  - title_of_course (text)
  - course_code (text)
  - type_of_course (text)
  - level_of_course (text)  -- UG, PG, PhD
  - course_offering_department (text)
  - total_credit_score (text)  -- format "3:1" (lecture:tutorial)
  - institute (text)
  - as_on_year (text)
  - id (integer PK)

Impact: Cannot answer 9 of 17 Dhairya queries without this table.
```

### Q3, Q4 — `innovation_grant_from_govt`
```
PostgreSQL: innovation_grant_from_govt
SQLite:     MISSING

Columns:
  - gov_organisation_name (text)
  - grant_received (bigint)
  - year_of_receiving (text)
  - institute (text)
  - id (integer)
  - financial_year (text)

Impact: Q3 (YoY grant drop), Q4 (top 5 agencies) completely blocked.
```

### Q5, Q6, Q17 — `innovations_at_various_stages_of_technology_readiness_level`
```
PostgreSQL: innovations_at_various_stages_of_technology_readiness_level
SQLite:     MISSING

Columns:
  - innovation_name (text)
  - stage_of_technology (text)  -- Level 1-9
  - financial_year (text)
  - institute (text)
  - as_on_year (text)
  - id (integer)

Impact: Q5 (Lab Validation bottleneck), Q6 (TRL 9 Market Ready), Q17 (TRL pipeline)
```

### Q7 — `combined_ipo_patent_data`
```
PostgreSQL: combined_ipo_patent_data
SQLite:     patents (partially)

Columns:
  - id (integer PK)
  - oid (text)
  - application_number (text)
  - applicants (text)
  - status (text)  -- Granted, Pending, Abandoned
  - ... (30 more columns)

SQLite `patents` table has: patent_id, title, inventor_ids, applicant_institution,
status, research_area, patent_type, claims_count, filing_date, grant_date, jurisdiction

Gap: PostgreSQL `combined_ipo_patent_data` has different schema than SQLite `patents`.
     PostgreSQL uses `applicants` (text), SQLite uses `inventor_ids` (pipe-separated).
     PostgreSQL has 34 columns vs SQLite's 13.
```

### Q13 — `incubation_details`
```
PostgreSQL: incubation_details
SQLite:     MISSING

Columns:
  - financial_year (text)
  - no_of_pre_incubation_units (integer)
  - expenditure_on_pre_incubation_activities (bigint)
  - income_generated_pre_incubation (bigint)
  - no_of_incubation_units (integer)
  - income_generated_incubation (bigint)
  - expenditure_on_incubation_activities (bigint)
  - institute (text)
  - as_on_year (text)
  - id (integer)

Impact: Q13 (correlation courses vs startups) blocked.
```

### Q14 — `financial_expenses_capital`
```
PostgreSQL: financial_expenses_capital
SQLite:     MISSING

Columns:
  - id (integer PK)
  - financial_year (text)
  - library (bigint)
  - equipment (bigint)
  - workshops (bigint)
  - other_capital (bigint)
  - total_capital (bigint)
  - institute (text)

Impact: Q14 (high capex, low innovation courses) blocked.
```

### Q16 — `financial_expenses_operational`
```
PostgreSQL: financial_expenses_operational
SQLite:     MISSING

Columns:
  - id (integer PK)
  - financial_year (text)
  - salaries (bigint)
  - maintenance (bigint)
  - seminars (bigint)
  - other_operational (bigint)
  - total_operational (bigint)
  - institute (text)

Impact: Q16 (high grants vs low expenditure) blocked.
```

---

## Category 3: MISSING_NICE_TO_HAVE — Not in Dhairya queries

Tables that would expand NRG capabilities but aren't needed for current benchmark.

### Academic / Student Data
| Table | Columns | Purpose |
|-------|---------|---------|
| `actual_student_strength` | 16 | Student enrollment by program, gender, state |
| `phd_students` | 7 | PhD student counts by program type |
| `sanctioned_intake` | 6 | Sanctioned seats per program |
| `placements_and_higher_studies` | 14 | Placement rates, median salary, higher studies |
| `package_data` | 4 | Placement salary packages |
| `role_data` | 3 | Placement role categories |

### Faculty / HR
| Table | Columns | Purpose |
|-------|---------|---------|
| `faculty_details` | 4 | Faculty counts per institute |
| `faculty_strength` | 11 | Faculty demographics by gender, category |
| `fdp_details` | 9 | Faculty Development Programs |
| `expertise` | 10 | Faculty expertise and research areas |
| `master_expertise` | 3 | Institute-department expertise mapping |

### NIRF / Rankings
| Table | Columns | Purpose |
|-------|---------|---------|
| `nirf_extracted_table` | 5 | NIRF ranking data extraction |
| `nirf_pdf_record` | 6 | NIRF PDF upload records |
| `nirf_table_row` | 3 | NIRF table row data |

### Startups / Investment
| Table | Columns | Purpose |
|-------|---------|---------|
| `seed_funding` | 10 | Startup seed funding and DPIIT registration |
| `startup_receiving_vc_investment` | 7 | VC investment in startups |
| `startup_recognition` | 6 | Recognized startups by institute |
| `startups_turnover_50_lacs` | 6 | Startups with >50 lakh turnover |
| `fdi_investment` | 6 | Foreign direct investment in startups |
| `founders_of_fortune_500_companies` | 8 | Alumni founders at Fortune 500 |

### Scraped / Bibliometric
| Table | Columns | Purpose |
|-------|---------|---------|
| `scraped_data` | 36 | Scopus/OpenAlex bibliometric data |
| `scraped_data_save` | 36 | Backup scraped data |
| `scraped_raw_data` | 36 | Raw scraped data |
| `advance_search_data` | 37 | Indexed research data |
| `advance_search_data_15_12` | 35 | Historical search data |
| `advance_search_data_old` | 35 | Legacy search data |

### Institute Reference
| Table | Columns | Purpose |
|-------|---------|---------|
| `tb_institute_mstr` | 9 | Institute master data |
| `tb_institute_scrap_data_url` | 10 | Scrape URLs for institutes |
| `tb_goi_ministries_mstr` | 7 | Government ministries reference |
| `tb_academic_year_mstr` | 3 | Academic year master |
| `tb_course_program_types` | 2 | Course program type master |

### Patent Details
| Table | Columns | Purpose |
|-------|---------|---------|
| `patents_details` | 7 | Patent summary by year |
| `ipo_patent_details_flat` | 28 | IPO/Patent flattened data |
| `ipo_patent_details_flat_old` | 28 | Legacy IPO/Patent data |
| `combined_ipo_patent_data_old` | 34 | Legacy patent data |

---

## Category 4: DJANGO_INTERNAL — Skip (Django framework tables)

These are Django framework tables, not NRG business data.

| Table | Reason to Skip |
|-------|---------------|
| `auth_group` | Django auth |
| `auth_group_permissions` | Django auth M2M |
| `auth_permission` | Django auth |
| `auth_user` | Django auth |
| `auth_user_groups` | Django auth M2M |
| `auth_user_user_permissions` | Django auth M2M |
| `django_admin_log` | Django admin |
| `django_content_type` | Django content types |
| `django_migrations` | Django migrations |
| `django_session` | Django sessions |
| `user_registration_old` | Legacy NRG users |
| `adv_se` | Empty/placeholder |

---

## Summary: 40 Missing Tables

```
MISSING_CRITICAL (7 tables for Dhairya queries):
  1. academic_courses_details
  2. innovation_grant_from_govt
  3. innovations_at_various_stages_of_technology_readiness_level
  4. combined_ipo_patent_data
  5. incubation_details
  6. financial_expenses_capital
  7. financial_expenses_operational

MISSING_NICE_TO_HAVE (29 tables):
  Student: actual_student_strength, phd_students, sanctioned_intake,
           placements_and_higher_studies, package_data, role_data
  Faculty: faculty_details, faculty_strength, fdp_details,
           expertise, master_expertise
  NIRF:    nirf_extracted_table, nirf_pdf_record, nirf_table_row
  Startup: seed_funding, startup_receiving_vc_investment, startup_recognition,
           startups_turnover_50_lacs, fdi_investment, founders_of_fortune_500_companies
  Data:    scraped_data, scraped_data_save, scraped_raw_data,
           advance_search_data, advance_search_data_15_12, advance_search_data_old
  Ref:     tb_institute_mstr, tb_institute_scrap_data_url, tb_goi_ministries_mstr,
           tb_academic_year_mstr, tb_course_program_types
  Patents: patents_details, ipo_patent_details_flat, ipo_patent_details_flat_old,
          combined_ipo_patent_data_old

SKIP (4 tables):
  auth_group, auth_user, django_migrations, django_session

TOTAL: 7 + 29 + 4 = 40 missing tables
```

---

## Our SQLite Schema (18 tables) — No direct mapping to PostgreSQL

```
audit_events
collaborations
consent_ledger
funding_records
institutions
keywords
labs
patents                -- partially maps to combined_ipo_patent_data (different schema)
projects
publications
refresh_tokens
research_documents
researcher_labs
researcher_publications
researchers
schema_migrations
sqlite_sequence
```

**Key insight:** The PostgreSQL schema and SQLite schema are completely different data models. The PostgreSQL schema is an academic institution management system (Django-based). The SQLite schema is a research knowledge graph. They share almost no tables.

**This means:** The SQL Oracle improvements (schema hints, few-shot examples) built for our SQLite schema cannot help with Dhairya's queries — they reference completely different tables with completely different columns.

---

## Implication for Protocol #21 (THE SCHEMA BRIDGE)

1. **Cannot answer Dhairya's queries on SQLite dev** — tables don't exist
2. **Need PostgreSQL for true benchmark** — production has all 58 tables
3. **Dual-schema support needed** — SQLite dev mode vs PostgreSQL production mode
4. **Table translation layer** — for dev mode, detect queries to missing tables and return "not available in dev"
5. **Migration needed** — 40 missing tables need to be created in PostgreSQL via Alembic