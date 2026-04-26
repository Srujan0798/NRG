---
name: Three Data Sources
description: NRG has 3 external data inputs — Core Idea (professor), Dhairya SQL Audit (external engineer), Official PostgreSQL Schema (professor's production DB)
type: reference
---

NRG project has 3 data sources from outside the codebase:

**Data Source 1: Core Idea** (from professor/client)
- File: `Core_Idea_Clean.md`
- What: Product vision, fine-tuning endgame, 3-persona model, sovereignty requirements
- Status: Fully integrated into CLAUDE.md, workflow, all protocols

**Data Source 2: Dhairya SQL Audit** (from external engineer)
- Files: `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`, `sesDhairya's report:.sql`
- What: 17-query real-world eval with ground-truth SQL, 41% accuracy baseline
- Status: Formatted, analyzed, agent applied fixes (schema synonyms, CTE templates, validator)

**Data Source 3: Official PostgreSQL Schema** (from professor/client — 2026-04-23)
- File: `db_struct.sql` (pg_dump from PostgreSQL 14.20, dumped 2026-01-09)
- What: 58 tables — the REAL production database schema that Dhairya tested against
- Status: NEW — needs integration

**Critical finding**: Our SQLite dev DB has 18 tables (researchers, publications, etc). The professor's PostgreSQL has 58 tables including:
- `academic_courses_details` — Dhairya's Q1,Q2,Q8,Q9,Q10,Q11,Q12 reference this
- `innovation_grant_from_govt` — Dhairya's Q3,Q4 reference this
- `innovations_at_various_stages_of_technology_readiness_level` — Dhairya's Q5,Q6,Q17
- `combined_ipo_patent_data` — Dhairya's Q7 (Cost of Innovation)
- `incubation_details` — Dhairya's Q13 (courses vs startups)
- `financial_expenses_capital` / `financial_expenses_operational` — Dhairya's Q14,Q16
- `actual_student_strength`, `phd_students`, `sanctioned_intake` — student data
- `placements_and_higher_studies` — placement data
- `seed_funding`, `fdi_investment`, `startup_recognition` — startup ecosystem
- `scraped_data` — Scopus/OpenAlex research paper data (30+ columns)
- `expertise`, `faculty_details`, `faculty_strength` — faculty data
- `nirf_*` tables — NIRF ranking PDF extraction
- Django auth tables (auth_user, auth_group, etc.)

**40 of the 58 PostgreSQL tables do NOT exist in our SQLite DB.** This means Dhairya was testing against the REAL schema, and our dev DB is a simplified subset. The SQL pipeline needs to know about ALL 58 tables for production.
