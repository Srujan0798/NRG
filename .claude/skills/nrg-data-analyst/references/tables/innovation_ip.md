# Innovation & IP Tables

This document contains tables for tracking innovation, patents, government grants, incubation, and startups.

---

## Quick Reference

### Business Context
These tables track the innovation pipeline from government-funded research through patent filings, technology readiness levels, incubation, and startup formation. Data comes from annual government dumps and quarterly IPO data.

### Standard Filters
```sql
-- Filter to known Indian institutions
WHERE institute IN (SELECT name FROM institutions WHERE country = 'India')

-- Exclude incomplete records
AND financial_year IS NOT NULL
```

---

## Key Tables

### innovation_grant_from_govt
**Location**: `public.innovation_grant_from_govt`
**Description**: Government scheme grants received by institutions.
**Primary Key**: `id` (TEXT, NOT UUID)
**Update Frequency**: Annual (3-6 month lag from government dumps)

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | TEXT | Unique identifier | Non-UUID |
| **institute** | TEXT | Institution name | NOT NULL; TEXT not UUID FK |
| **gov_organisation_name** | TEXT | Funding ministry/agency | e.g., 'DST', 'DBT', 'MeitY' |
| **grant_received** | REAL | Amount received | NOT NULL |
| **year_of_receiving** | TEXT | FY: '2020-21', '2021-22' | TEXT, not DATE |
| **as_on_year** | TEXT | Reporting year | |
| **scheme_name** | TEXT | Specific scheme | e.g., 'SPARC', 'IMPRINT' |
| **access_tier** | INTEGER | Visibility | DEFAULT 1 |
| **created_at** | TEXT | Timestamp | TEXT, not TIMESTAMP |

**Indexes**: `idx_grant_institute`, `idx_grant_org`, `idx_grant_year`

**Sample Queries**:
```sql
-- Total grants by government organization
SELECT gov_organisation_name,
       SUM(grant_received) AS total_grants,
       COUNT(*) AS num_schemes
FROM innovation_grant_from_govt
WHERE year_of_receiving = '2022-23'
GROUP BY gov_organisation_name
ORDER BY total_grants DESC;

-- Top funded institutes
SELECT institute, SUM(grant_received) AS total
FROM innovation_grant_from_govt
GROUP BY institute
ORDER BY total DESC
LIMIT 10;
```

---

### combined_ipo_patent_data
**Location**: `public.combined_ipo_patent_data`
**Description**: Indian Patent Office patent filings and grants.
**Primary Key**: `id` (TEXT)
**Update Frequency**: Quarterly (1-3 month lag)

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | TEXT | Unique identifier | |
| **institute** | TEXT | Filing institution | NOT NULL; TEXT not UUID |
| **applicants** | TEXT | Applicant names | May include multiple |
| **title** | TEXT | Patent title | |
| **application_number** | TEXT | IPO application number | |
| **status** | TEXT | Current status | 'Granted', 'Filed', 'Examined', 'Rejected' |
| **filing_date** | TEXT | Filing date | TEXT format |
| **grant_date** | TEXT | Grant date | NULL if not granted |
| **financial_year** | TEXT | FY of filing | e.g., '2021-22' |
| **access_tier** | INTEGER | Visibility | DEFAULT 1 |
| **created_at** | TEXT | Timestamp | |

**Indexes**: `idx_patent_institute`, `idx_patent_status`, `idx_patent_year`

**Sample Queries**:
```sql
-- Patent grant rate by institute
SELECT institute,
       COUNT(*) FILTER (WHERE status = 'Granted') AS granted,
       COUNT(*) AS total,
       ROUND(COUNT(*) FILTER (WHERE status = 'Granted') * 100.0 / COUNT(*), 2) AS grant_rate
FROM combined_ipo_patent_data
WHERE financial_year >= '2020-21'
GROUP BY institute
HAVING COUNT(*) >= 5
ORDER BY grant_rate DESC;

-- Patent trends over time
SELECT financial_year, status, COUNT(*) AS count
FROM combined_ipo_patent_data
GROUP BY financial_year, status
ORDER BY financial_year, status;
```

---

### innovations_at_various_stages_of_technology_readiness_level
**Location**: `public.innovations_at_various_stages_of_technology_readiness_level`
**Description**: Innovations tracked through Technology Readiness Levels.
**Primary Key**: `id` (TEXT)
**Update Frequency**: Annual

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | TEXT | Unique identifier | |
| **institute** | TEXT | Institution name | |
| **financial_year** | TEXT | FY | |
| **stage_of_technology** | TEXT | TRL level | '1', '2', ..., '9' or descriptive |
| **title** | TEXT | Innovation title | |
| **sector** | TEXT | Industry sector | |
| **access_tier** | INTEGER | Visibility | DEFAULT 1 |
| **created_at** | TEXT | Timestamp | |

**Indexes**: `idx_trl_institute`, `idx_trl_stage`, `idx_trl_year`

**Sample Queries**:
```sql
-- TRL distribution
SELECT stage_of_technology, COUNT(*) AS innovation_count
FROM innovations_at_various_stages_of_technology_readiness_level
GROUP BY stage_of_technology
ORDER BY stage_of_technology;
```

---

### incubation_details
**Location**: `public.incubation_details`
**Description**: Startup incubation programs and their outcomes.
**Primary Key**: `id` (TEXT)
**Update Frequency**: Annual

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | TEXT | Unique identifier | |
| **institute** | TEXT | Host institution | |
| **startup_name** | TEXT | Incubated startup | |
| **status** | TEXT | Current status | e.g., 'Active', 'Graduated', 'Closed' |
| **sector** | TEXT | Business sector | |
| **financial_year** | TEXT | FY of incubation | |
| **access_tier** | INTEGER | Visibility | DEFAULT 1 |
| **created_at** | TEXT | Timestamp | |

**Indexes**: `idx_incubate_institute`, `idx_incubate_status`

---

### startup_recognition
**Location**: `public.startup_recognition`
**Description**: Recognized startups from institutions.
**Primary Key**: `id` (TEXT)
**Update Frequency**: Annual

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | TEXT | Unique identifier | |
| **institute** | TEXT | Parent institution | |
| **startup_name** | TEXT | Startup name | |
| **recognition_type** | TEXT | Type of recognition | |
| **financial_year** | TEXT | FY | |
| **access_tier** | INTEGER | Visibility | DEFAULT 1 |
| **created_at** | TEXT | Timestamp | |

**Indexes**: `idx_startup_institute`

---

## Common Gotchas

1. **All academic schema tables use TEXT institute names**: No UUID foreign keys. Join to `institutions` by name matching.

2. **Financial year is TEXT**: Format '2020-21'. Use string comparison or `SUBSTRING(financial_year, 1, 4)::INTEGER` for year arithmetic.

3. **Grant amounts in academic schema are REAL**: Not DECIMAL. May have floating-point precision issues for exact financial reporting.

4. **Patent status values**: Case-sensitive. Use exact strings: 'Granted', 'Filed', 'Examined', 'Rejected'.

5. **TRL stage may be numeric or descriptive**: Check actual values before querying.
