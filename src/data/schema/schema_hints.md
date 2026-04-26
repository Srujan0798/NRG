# NRG Database Schema — PostgreSQL Production (58 Tables)

**Source:** `db_struct.sql` (pg_dump from PostgreSQL 14.20, 2026-01-09)
**Total Tables:** 58
**Dhairya Benchmark:** 17 queries (all reference PostgreSQL tables)

> **IMPORTANT:** This is the PRODUCTION PostgreSQL schema. The development SQLite has only 18 tables and does NOT contain most of these tables. When running against SQLite dev, queries to missing tables should return "not available in development database."

---

## Table Purpose Descriptions

### academic_courses_details (10 cols) — **MOST REFERENCED TABLE — 9 of 17 queries**
**Purpose:** Innovation curriculum courses with credit scoring per institution.
**Dhairya Q#:** 1, 2, 8, 9, 10, 11, 12, 13, 14

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `financial_year` | text | Format `2022-23` |
| `title_of_course` | text | Course name |
| `course_code` | text | Course code |
| `type_of_course` | text | e.g., Innovation, Core, Elective |
| `level_of_course` | text | `UG`, `PG`, `PhD` — **MUST filter exactly** |
| `course_offering_department` | text | Department |
| `total_credit_score` | text | **Format `"3:1"` (lecture:tutorial) — MUST parse with SPLIT_PART** |
| `institute` | text | Institution name — use `LIKE '%IIT%'` for fuzzy |
| `as_on_year` | text | Snapshot year |

**CRITICAL PARSING RULE:**
```sql
-- WRONG (will fail on "3:1" format):
SELECT SUM(CAST(total_credit_score AS INTEGER))

-- RIGHT (parse lecture:tutorial format):
SELECT SUM(SPLIT_PART(total_credit_score, ':', 1)::double precision)
```

**Enum Values:** `level_of_course` = `UG`, `PG`, `PhD`

---

### innovation_grant_from_govt (6 cols) — **CRITICAL for Q3, Q4**
**Purpose:** Government grants by organization, year, institute.
**Dhairya Q#:** 3, 4, 7, 16

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer | Primary key |
| `gov_organisation_name` | text | Funding agency (DST, SERB, etc.) |
| `grant_received` | bigint | **Amount in rupees** |
| `year_of_receiving` | text | Format `2020-21`, `2021-22` |
| `institute` | text | Institution name |
| `financial_year` | text | Alternative year format |

**CRITICAL RULE — "Top N funding agencies":**
```sql
-- WRONG:
SELECT DISTINCT gov_organisation_name FROM innovation_grant_from_govt ORDER BY grant_received LIMIT 5

-- RIGHT:
SELECT gov_organisation_name, SUM(grant_received) as total
FROM innovation_grant_from_govt
GROUP BY gov_organisation_name
ORDER BY total DESC LIMIT 5
```

**CRITICAL RULE — YoY grant drop >50%:**
```sql
WITH YearlyGrants AS (
    SELECT institute, year_of_receiving, SUM(grant_received) as total_funding
    FROM innovation_grant_from_govt
    GROUP BY institute, year_of_receiving
)
SELECT curr.institute, curr.year_of_receiving, curr.total_funding,
       prev.total_funding as prev_funding,
       ((curr.total_funding - prev.total_funding) / prev.total_funding::float) * 100 as growth_pct
FROM YearlyGrants curr
JOIN YearlyGrants prev ON curr.institute = prev.institute
    AND prev.year_of_receiving = '2020-21'
WHERE curr.year_of_receiving = '2022-23'
  AND ((curr.total_funding - prev.total_funding) / prev.total_funding::float) < -0.5;
```

---

### innovations_at_various_stages_of_technology_readiness_level (6 cols) — **TRL tracking**
**Purpose:** TRL stages per innovation (Level 1–9).
**Dhairya Q#:** 5, 6, 17

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer | Primary key |
| `innovation_name` | text | Innovation title |
| `stage_of_technology` | text | **"Level 1" through "Level 9"** |
| `financial_year` | text | Year |
| `institute` | text | Institution |
| `as_on_year` | text | Snapshot |

**CRITICAL SYNONYM MAPPINGS — MUST translate user terms to DB values:**
```
"TRL 9" / "Market Ready" / "Commercialized"  → "Level 9"
"TRL 8" / "Commissioned"                     → "Level 8"
"TRL 7" / "System Test"                      → "Level 7"
"TRL 6" / "Technology Demonstration"         → "Level 6"
"TRL 5" / "Lab Validation"                   → "Level 5"
"TRL 4" / "Lab Validation"                   → "Level 4"  (Q5 uses this!)
"TRL 3" / "Analytical Proof of Concept"      → "Level 3"
"TRL 2" / "Basic Principles"                 → "Level 2"
"TRL 1" / "Basic Research"                   → "Level 1"
```

**CRITICAL QUERY PATTERNS:**
```sql
-- Q6: Market Ready (TRL 9) at IIT Madras
SELECT innovation_name, financial_year
FROM innovations_at_various_stages_of_technology_readiness_level
WHERE stage_of_technology = 'Level 9'
  AND institute LIKE '%IIT Madras%';

-- Q5: Lab Validation (Level 4) bottleneck
SELECT stage_of_technology, COUNT(*) as innovation_count,
       (COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM innovations_at_various_stages_of_technology_readiness_level WHERE institute LIKE '%IIT Madras%'), 0)) as pct
FROM innovations_at_various_stages_of_technology_readiness_level
WHERE institute LIKE '%IIT Madras%'
GROUP BY stage_of_technology
ORDER BY innovation_count DESC;

-- Q17: Full TRL pipeline distribution
SELECT stage_of_technology, COUNT(*) as count
FROM innovations_at_various_stages_of_technology_readiness_level
GROUP BY stage_of_technology
ORDER BY stage_of_technology;
```

---

### combined_ipo_patent_data (34 cols) — **Detailed patent records**
**Purpose:** IPO/Patent records with applicants, status, application numbers.
**Dhairya Q#:** 7, 13

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `oid` | text | Object ID |
| `application_number` | text | Patent application number |
| `applicants` | text | **Institute/person that applied** — used for Q7 join |
| `status` | text | **'Granted', 'Pending', 'Abandoned'** — filter for Q7 |
| ... | (30 more) | |

**CRITICAL PATTERN — Q7 (Cost of Innovation):**
```sql
-- WRONG: Join on institute, ignore status filter
-- RIGHT:
WITH GrantData AS (
    SELECT institute, SUM(grant_received) as total_money
    FROM innovation_grant_from_govt
    GROUP BY institute
),
PatentData AS (
    SELECT applicants, COUNT(*) as total_patents
    FROM combined_ipo_patent_data
    WHERE status = 'Granted'
    GROUP BY applicants
)
SELECT g.institute, g.total_money, p.total_patents,
       (g.total_money / NULLIF(p.total_patents, 0)) as cost_per_patent
FROM GrantData g
LEFT JOIN PatentData p ON LOWER(TRIM(g.institute)) = LOWER(TRIM(p.applicants));
```

---

### financial_expenses_capital (8 cols)
**Purpose:** Capital expenditure — library, equipment, workshops.
**Dhairya Q#:** 14

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `financial_year` | text | Year |
| `library` | bigint | Library spending |
| `equipment` | bigint | Equipment spending |
| `workshops` | bigint | Workshop costs |
| `other_capital` | bigint | Other capital |
| `total_capital` | bigint | **Total capital expenditure** |
| `institute` | text | Institution |

---

### financial_expenses_operational (7 cols)
**Purpose:** Operational expenditure — salaries, maintenance, seminars.
**Dhairya Q#:** 16

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `financial_year` | text | Year |
| `salaries` | bigint | Salary spending |
| `maintenance` | bigint | Maintenance |
| `seminars` | bigint | Seminar costs |
| `other_operational` | bigint | Other operational |
| `total_operational` | bigint | Total operational |
| `institute` | text | Institution |

---

### incubation_details (10 cols)
**Purpose:** Pre-incubation + incubation units, expenditure, income.
**Dhairya Q#:** 13

| Column | Type | Critical Notes |
|--------|------|----------------|
| `financial_year` | text | Year |
| `no_of_pre_incubation_units` | integer | Pre-incubated startups |
| `expenditure_on_pre_incubation_activities` | bigint | Spending |
| `income_generated_pre_incubation` | bigint | Revenue |
| `no_of_incubation_units` | integer | Active incubatees |
| `income_generated_incubation` | bigint | Incubation revenue |
| `expenditure_on_incubation_activities` | bigint | Incubation spending |
| `institute` | text | Institution |
| `as_on_year` | text | Snapshot |
| `id` | integer | Primary key |

---

### patents_details (7 cols)
**Purpose:** Patent summary by year — published/granted/commercialized.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `financial_year` | text | Year |
| `patents_published` | integer | Filed count |
| `patents_granted` | integer | Granted count |
| `patents_commercialized` | integer | Commercialized count |
| `institute` | text | Institution |
| `as_on_year` | text | Snapshot |
| `id` | integer | Primary key |

---

### phd_students (7 cols)
**Purpose:** PhD student counts by program type and institute.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `financial_year` | text | Year |
| `program_type` | text | PhD program type |
| `total` | integer | Student count |
| `institute` | text | Institution |
| `as_on_year` | text | Snapshot |

---

### placements_and_higher_studies (14 cols)
**Purpose:** Placement rates, median salary, higher studies outcomes.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `program` | text | Program name |
| `year_of_intake` | text | Intake year |
| `students_intaken` | integer | Intake count |
| `students_placed` | integer | Placed count |
| `median_package` | integer | Median salary (LPA) |
| ... | (8 more) | |

---

### actual_student_strength (16 cols)
**Purpose:** Student enrollment by program, gender, state.
*(Not referenced in Dhairya benchmark)*

---

### sanctioned_intake (6 cols)
**Purpose:** Sanctioned seats per program.
*(Not referenced in Dhairya benchmark)*

---

### faculty_details (4 cols)
**Purpose:** Faculty counts per institute.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `num_faculties` | integer | Count |
| `institute` | text | Institution |
| `as_on_year` | text | Snapshot year |
| `id` | integer PK | Primary key |

---

### faculty_strength (11 cols)
**Purpose:** Detailed faculty demographics by gender, category.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `institute` | varchar(100) | Institution |
| `academic_year` | varchar(10) | Year |
| `as_on` | varchar(20) | Snapshot |
| ... | (7 more) | |

---

### fdp_details (9 cols)
**Purpose:** Faculty Development Programs.
*(Not referenced in Dhairya benchmark)*

---

### expertise (10 cols)
**Purpose:** Faculty expertise and research areas.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `name` | varchar | Faculty name |
| `designation` | varchar | Title |
| `email` | varchar | Email (PII — Tier 2/3 restricted) |
| ... | (6 more) | |

---

### master_expertise (3 cols)
**Purpose:** Institute-department expertise mapping.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `institute` | varchar | Institution |
| `department` | varchar | Department |

---

### seed_funding (10 cols)
**Purpose:** Startup seed funding and DPIIT registration.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `startup_name` | varchar(255) | Startup |
| `dpiit_no` | varchar(100) | DPIIT number |
| `seed_funding_received` | bigint | Amount |
| `year_of_receiving` | text | Year |
| `institute` | text | Institution |
| ... | (5 more) | |

---

### startup_receiving_vc_investment (7 cols)
**Purpose:** VC investment in startups.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `startup_name` | text | Startup |
| `amount_received` | bigint | Investment |
| `organisation_name` | text | VC firm |
| `year_of_receiving` | text | Year |
| `institute` | text | Institution |
| ... | (3 more) | |

---

### startup_recognition (6 cols)
**Purpose:** Recognized startups by institute.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `startup_name` | text | Startup |
| `year_of_recognition` | text | Year |
| `registration_no` | text | Registration |
| `institute` | text | Institution |
| `dpiit_no` | text | DPIIT number |
| `as_on_year` | text | Snapshot |

---

### startups_turnover_50_lacs (6 cols)
**Purpose:** Startups with >50 lakh turnover.
*(Not referenced in Dhairya benchmark)*

---

### fdi_investment (6 cols)
**Purpose:** Foreign direct investment in startups.
*(Not referenced in Dhairya benchmark)*

---

### research_consultancy_details_consultancy (7 cols)
**Purpose:** Consultancy projects and revenue.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `financial_year` | text | Year |
| `consultancy_projects` | integer | Project count |
| `client_organisations` | integer | Client count |
| `revenue_generated` | bigint | Revenue |
| `institute` | text | Institution |
| ... | (2 more) | |

---

### research_consultancy_details_sponsered (7 cols)
**Purpose:** Sponsored research projects.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `financial_year` | text | Year |
| `sponsered_projects` | integer | Project count |
| `funding_agencies` | integer | Agency count |
| `funding_amount` | bigint | Funding |
| `institute` | text | Institution |
| ... | (2 more) | |

---

### nirf_extracted_table (5 cols)
**Purpose:** NIRF ranking data extraction.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `pdf_record_id` | integer FK | FK to nirf_pdf_record |
| `title` | varchar(255) | Ranking metric |
| `header` | jsonb | Header data |
| `row_data` | jsonb | Row values |

---

### nirf_pdf_record (6 cols)
**Purpose:** NIRF PDF upload records.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `institute` | varchar(255) | Institution |
| `year` | varchar(10) | Year |
| `uploaded_by` | varchar(255) | Uploader |
| `uploaded_at` | timestamp | Upload time |
| `file_path` | varchar(512) | File path |

---

### nirf_table_row (3 cols)
**Purpose:** NIRF table row data.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `table_id` | integer FK | FK to nirf_extracted_table |
| `data` | jsonb | Row data |

---

### package_data (4 cols)
**Purpose:** Placement salary packages.
*(Not referenced in Dhairya benchmark)*

---

### role_data (3 cols)
**Purpose:** Placement role categories.
*(Not referenced in Dhairya benchmark)*

---

### scraped_data (36 cols)
**Purpose:** Scopus/OpenAlex bibliometric data.
*(Not referenced in Dhairya benchmark but referenced in schema)*

---

### scraped_data_save / scraped_raw_data (36 cols each)
**Purpose:** Backup and raw scraped data.
*(Not referenced in Dhairya benchmark)*

---

### advance_search_data / advance_search_data_15_12 / advance_search_data_old
**Purpose:** Indexed research publication data.
*(Not referenced in Dhairya benchmark)*

---

### ipo_patent_details_flat / ipo_patent_details_flat_old (28 cols)
**Purpose:** IPO/Patent flattened data.
*(Not referenced in Dhairya benchmark)*

---

### combined_ipo_patent_data_old (34 cols)
**Purpose:** Legacy patent data.
*(Not referenced in Dhairya benchmark)*

---

### founders_of_fortune_500_companies (8 cols)
**Purpose:** Alumni founders at Fortune 500.
*(Not referenced in Dhairya benchmark)*

---

### user_registration (17 cols)
**Purpose:** NRG user accounts.
*(NRG auth system — not in Dhairya benchmark)*

---

### user_registration_old (10 cols)
**Purpose:** Legacy users.
*(Skip)*

---

### tb_institute_mstr (9 cols)
**Purpose:** Institute master data.

| Column | Type | Critical Notes |
|--------|------|----------------|
| `id` | integer PK | Primary key |
| `institute_name` | varchar(255) | Full name |
| `short_name` | varchar(100) | Abbreviation |
| `institute_type` | varchar(100) | Type |
| ... | (6 more) | |

---

### tb_institute_scrap_data_url (10 cols)
**Purpose:** Scrape URLs for institutes.

---

### tb_goi_ministries_mstr (7 cols)
**Purpose:** Government of India ministries reference.
*(Not referenced in Dhairya benchmark)*

---

### tb_academic_year_mstr (3 cols)
**Purpose:** Academic year master data.
*(Not referenced in Dhairya benchmark)*

---

### tb_course_program_types (2 cols)
**Purpose:** Course program type master.
*(Not referenced in Dhairya benchmark)*

---

## Django Internal Tables — **SKIP (not NRG business data)**

| Table | Reason |
|-------|--------|
| `auth_group` | Django auth |
| `auth_group_permissions` | Django M2M |
| `auth_permission` | Django auth |
| `auth_user` | Django auth |
| `auth_user_groups` | Django M2M |
| `auth_user_user_permissions` | Django M2M |
| `django_admin_log` | Django admin |
| `django_content_type` | Django CT |
| `django_migrations` | Django migrations |
| `django_session` | Django sessions |
| `adv_se` | Empty/placeholder |

---

## Dhairya Query → Table Mapping

| Q# | Question | Tables | Key Columns |
|----|----------|--------|-------------|
| Q1 | Most intensive curriculum (credits-based) | `academic_courses_details` | `total_credit_score` ("3:1" format), `institute`, `financial_year` |
| Q2 | PhD:UG ratio for IIT Bombay | `academic_courses_details` | `level_of_course` (`UG`, `PhD`), `institute` |
| Q3 | >50% grant drop YoY | `innovation_grant_from_govt` | `grant_received`, `year_of_receiving`, `institute` |
| Q4 | Top 5 funding agencies | `innovation_grant_from_govt` | `gov_organisation_name`, `grant_received` |
| Q5 | % IIT Madras stuck at Lab Validation | `innovations_at_various_stages_of_technology_readiness_level` | `stage_of_technology` (`Level 4`/`Level 5`), `institute` |
| Q6 | TRL-9 Market Ready at IIT Madras | `innovations_at_various_stages_of_technology_readiness_level` | `stage_of_technology` (`Level 9`), `institute` |
| Q7 | Cost of Innovation (grant per patent) | `innovation_grant_from_govt` + `combined_ipo_patent_data` | `applicants`, `status='Granted'`, `grant_received` |
| Q8 | PG courses at IIT Madras (last 3 years) | `academic_courses_details` | `level_of_course='PG'`, `institute`, `financial_year` |
| Q9 | Institute with most PhD courses | `academic_courses_details` | `level_of_course='PhD'`, `institute` |
| Q10 | Compare PhD vs UG numbers | `academic_courses_details` | `level_of_course` (`UG`, `PhD`), `institute` |
| Q11 | YoY growth for PG courses — IIT Madras | `academic_courses_details` | `level_of_course='PG'`, `institute`, `financial_year` |
| Q12 | Strategy shift: UG stops, PhD spikes | `academic_courses_details` | `level_of_course` (`UG`, `PhD`), `institute`, `financial_year` |
| Q13 | Correlation: courses vs startups | `academic_courses_details` + `incubation_details` | course count vs incubation units |
| Q14 | High capex, low innovation courses | `academic_courses_details` + `financial_expenses_capital` | course intensity vs capital spend |
| Q15 | (Error — no table reference found) | | |
| Q16 | High grants vs low expenditure | `innovation_grant_from_govt` + `financial_expenses_operational` | `salaries`, `grant_received` |
| Q17 | Pipeline progression across TRL stages | `innovations_at_various_stages_of_technology_readiness_level` | `stage_of_technology` (all levels) |

---

## Mandatory Rules for SQL Generation

### RULE 1: Credit Score Parsing (Q1, Q13, Q14)
```sql
-- ALWAYS parse "3:1" format with SPLIT_PART
SELECT institute,
       SUM(SPLIT_PART(total_credit_score, ':', 1)::double precision) as total_credits
FROM academic_courses_details
WHERE financial_year = '2022-23'
GROUP BY institute
ORDER BY total_credits DESC;
```

### RULE 2: YoY Comparison — CTE + GROUP BY (Q3, Q11, Q12, Q16)
```sql
-- ALWAYS use CTE to aggregate by year first, then join
WITH YearlyData AS (
    SELECT institute, year_of_receiving, SUM(column) as total
    FROM table_name
    GROUP BY institute, year_of_receiving
)
SELECT curr.*, prev.*, ((curr.total - prev.total) / prev.total::float) * 100 as growth
FROM YearlyData curr
JOIN YearlyData prev ON curr.institute = prev.institute AND prev.year = 'prev_year'
WHERE curr.year = 'curr_year';
```

### RULE 3: Top N by Amount — GROUP BY + ORDER BY SUM (Q4)
```sql
-- WRONG: DISTINCT + ORDER BY raw column
-- RIGHT: GROUP BY + ORDER BY SUM(column)
SELECT agency, SUM(amount) as total
FROM table GROUP BY agency ORDER BY total DESC LIMIT 5;
```

### RULE 4: TRL Level Translation
```sql
-- User says "TRL 9" or "Market Ready" → DB has "Level 9"
WHERE stage_of_technology = 'Level 9'
```

### RULE 5: Cost Per Unit — CTE + JOIN (Q7)
```sql
WITH GrantCTE AS (
    SELECT institute, SUM(grant_received) as total_grant
    FROM innovation_grant_from_govt GROUP BY institute
),
PatentCTE AS (
    SELECT applicants, COUNT(*) as total_patents
    FROM combined_ipo_patent_data WHERE status = 'Granted' GROUP BY applicants
)
SELECT g.institute, g.total_grant, COALESCE(p.total_patents, 0) as patents,
       g.total_grant / NULLIF(p.total_patents, 0) as cost_per_patent
FROM GrantCTE g LEFT JOIN PatentCTE p ON LOWER(TRIM(g.institute)) = LOWER(TRIM(p.applicants));
```

### RULE 6: Multi-Stage Aggregation — WHERE → GROUP BY → HAVING (Q14, Q16)
```sql
-- Always complete all stages
SELECT ... FROM ...
WHERE <conditions>
GROUP BY <dimensions>
HAVING <aggregate_conditions>
ORDER BY ...;
```

---

## SQL Anti-Patterns (NEVER produce)

1. **Direct integer cast on credit score** → `CAST(total_credit_score AS INTEGER)` fails on "3:1"
2. **DISTINCT without aggregation for ranked results** → wrong for Q4
3. **Row-level year comparison** → must use CTE + GROUP BY
4. **TRL 9 instead of Level 9** → DB stores "Level 9", not "TRL 9"
5. **Wrong join key for patent cost** → `applicants` not `institute` for patent join in Q7
6. **Missing status filter on patents** → `status = 'Granted'` required for Q7
7. **Incomplete query** — every query must be syntactically complete

---

## Common JOIN Keys

- `innovation_grant_from_govt.institute` → `academic_courses_details.institute`
- `innovation_grant_from_govt.institute` → `incubation_details.institute`
- `innovation_grant_from_govt.institute` → `financial_expenses_capital.institute`
- `innovation_grant_from_govt.institute` → `combined_ipo_patent_data.applicants` (note: different column!)
- `academic_courses_details.institute` → `tb_institute_mstr.institute_name`

---

*Auto-injected into LLM schema prompt — covers all 58 PostgreSQL tables.*