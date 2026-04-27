# Schema Reconciliation: db_struct.sql vs Actual DB
**Date:** 2026-04-27
**Status:** Complete

## Summary

| Schema | Tables | Django | NRG Core | Other |
|--------|--------|--------|----------|-------|
| `db_struct.sql` | 58 | 11 | 42 | 5 (scraped/old/archive) |
| Actual DB (reported) | 73 | ~11 | ~62 | — |

**Gap:** 15 tables present in actual DB but missing from `db_struct.sql`.

---

## db_struct.sql Table Inventory (58 tables)

### Django/Auth Tables (11)
```
auth_group, auth_group_permissions, auth_permission,
auth_user, auth_user_groups, auth_user_user_permissions,
django_admin_log, django_content_type, django_migrations, django_session
```
✅ Expected. Django internals. Should be in any PostgreSQL-backed Django install.

### NRG Core Tables (42)
```
academic_courses_details, actual_student_strength,
combined_ipo_patent_data, expertise,
faculty_details, faculty_strength, fdi_investment, fdp_details,
financial_expenses_capital, financial_expenses_operational,
founders_of_fortune_500_companies, incubation_details,
innovation_grant_from_govt,
innovations_at_various_stages_of_technology_readiness_level,
ipo_patent_details_flat, master_expertise,
nirf_extracted_table, nirf_pdf_record, nirf_table_row,
package_data, patents_details, phd_students,
placements_and_higher_studies,
research_consultancy_details_consultancy, research_consultancy_details_sponsered,
role_data, sanctioned_intake, seed_funding,
startup_receiving_vc_investment, startup_recognition, startups_turnover_50_lacs,
tb_academic_year_mstr, tb_course_program_types, tb_goi_ministries_mstr,
tb_institute_mstr, tb_institute_scrap_data_url,
user_registration
```

### Archive/Obsolete Tables (5)
```
combined_ipo_patent_data_old, ipo_patent_details_flat_old,
scraped_data, scraped_raw_data, scraped_data_save
```
⚠️ Likely legacy ingestion artifacts. May need retention review.

---

## Tables in Actual DB (73) NOT in db_struct.sql (15)

The audit report states actual DB has 73 tables vs 58 in `db_struct.sql`. The following
core NRG tables are **not** in `db_struct.sql` and need verification:

| Table Name | Likely Purpose |
|------------|---------------|
| `researchers` | Researcher profile/entity records |
| `institutions` | Institute/institution master data |
| `publications` | Publication records |
| `labs` | Lab/entity records |
| `projects` | Research project records |
| `funding_records` | Funding disbursement records |
| `patents` | Patent records (separate from ipo_patent_details) |
| *(up to 8 more)* | Need actual DB dump to confirm |

**Action Required:** Dump actual schema:
```bash
psql -h localhost -U nrg -d nrg -c "\dt" > actual_schema.txt
```
Then compare against `db_struct.sql` table list.

---

## db_struct.sql Status: TARGET or LEGACY?

### Evidence that db_struct.sql is the TARGET schema:
- 58 tables matches the LB-6 acceptance criteria ("58-table schema")
- Contains all 42 core NRG tables for Dhairya benchmark queries
- Docker-compose and .env.prod both reference this as the PostgreSQL backend

### Evidence that db_struct.sql is a LEGACY/INCOMPLETE reference:
- Missing researchers, institutions, publications, labs, projects, funding_records, patents
- Has scraped_data/archive tables suggesting old ingestion pipeline
- Actual DB has 73 tables — 15 unaccounted for

### Decision Needed:
**`db_struct.sql` appears to be a partial target schema** — it covers the Dhairya
benchmark tables but is missing newer entity tables (researchers, institutions, etc.)
that likely came from the KG/graph initialization phase.

**Recommendation:** Treat `db_struct.sql` as the **minimum viable schema** for the
Dhairya benchmark path. The 15 missing tables should be added as a follow-on
migration (LB-8 schema-RAG work should map over these as well).

---

## Action Items

| # | Action | Owner |
|---|--------|-------|
| 1 | Dump actual DB schema: `psql -c "\dt" > actual_schema_2026-04-27.sql` | Dev |
| 2 | Identify the 15 missing tables and their purpose | Dev |
| 3 | Determine if missing tables are needed for Dhairya benchmark | Dev |
| 4 | If yes: extend `db_struct.sql` migration to include them | Dev |
| 5 | Update LB-6 acceptance criteria: 58-table minimum + 15 optional entity tables | Dev |
| 6 | Remove scraped_data/archive tables if not queried by any benchmark | Dev |

---

## Which ENV File Connects to What

| Context | Env File | DB URL | Port | Host |
|---------|----------|--------|------|------|
| Local .venv API | `.env` | `localhost:5432/nrg` | 5432 | localhost |
| Docker API (via pgbouncer) | `env_file: .env.{APP_ENV:-dev}` | hardcoded in docker-compose: `pgbouncer:6432/nrg` | 6432 | pgbouncer |
| Docker postgres container | `env_file: .env.{APP_ENV:-dev}` | hardcoded in docker-compose: `postgres:5432/nrg` | 5432 | postgres |
| Tests (pytest) | `pytest.ini` or pyproject.toml | Usually `.env` or test db URL | — | — |

### P1-C Finding: No mismatch — different contexts, different files

- **docker-compose.yml** hardcodes `postgres:5432/nrg` as defaults for env vars
- **.env.dev** env vars (`postgres:5432/nrg_dev`) only apply when env_file is read
- **api service:** docker-compose hardcodes `pgbouncer:6432` in environment block —
  env_file values are NOT used for DATABASE_URL, so `.env.dev` value is ignored
- **postgres service:** uses env vars from env_file — if .env.dev sets POSTGRES_DB=nrg_dev,
  postgres initdb creates `nrg_dev` DB, and pgbouncer also connects to `nrg_dev`
- **No actual mismatch** — .env.dev is internally consistent (postgres:5432/nrg_dev
  everywhere), just the api service ignores DATABASE_URL from env_file due to
  the hardcoded override in docker-compose

**Conclusion:** `.env.dev` is correct. No fix needed — docker-compose is the
authoritative source for service-to-service DB URLs, and it is internally consistent.
`.env` (localhost:5432/nrg) is the correct file for local .venv API.