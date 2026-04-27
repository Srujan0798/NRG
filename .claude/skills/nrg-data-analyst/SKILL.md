---
name: nrg-data-analyst
description: "NRG (National Research Graph) data analysis skill. Provides PostgreSQL 16 context for India's sovereign research database including 18+ core tables, entity definitions, metric calculations, and common query patterns. Use when analyzing NRG data for: (1) researcher discovery and profiling, (2) funding and publication analytics, (3) institutional benchmarking, (4) patent and innovation tracking, or any data questions requiring NRG-specific context."
---

# NRG Data Analyst

## SQL Dialect: PostgreSQL 16

- **Table references**: `schema.table` (public schema, lowercase)
- **Safe division**: `NULLIF(denominator, 0)` pattern: `numerator / NULLIF(denominator, 0)`
- **Date functions**:
  - `DATE_TRUNC('month', date_col)`
  - `date_col - INTERVAL '1 day'`
  - `DATE_PART('year', date_col)`
  - `AGE(end_date, start_date)` for intervals
- **Column selection**: No EXCEPT; list columns explicitly
- **Arrays**: `UNNEST(array_column)` to flatten
- **JSON**: `json_col->>'field_name'` for text, `json_col->'field_name'` for JSON
- **Timestamps**: `AT TIME ZONE 'Asia/Kolkata'` for IST conversion; all stored in UTC
- **String matching**: `LIKE`, `col ~ 'pattern'` for regex, `ILIKE` for case-insensitive
- **Boolean**: Native BOOLEAN; use `TRUE`/`FALSE`
- **UUID**: Native UUID type; use `gen_random_uuid()` for generation
- **Full-text search**: `to_tsvector('english', text_col)` for search indexing

**Postgres 16 specific:**
- `JSONB` path queries: `jsonb_col @? '$.path[*] ? (@ == "value")'`
- `MERGE` statement available for upserts (alternative to INSERT ... ON CONFLICT)
- `pg_stat_statements` enabled for query performance analysis

---

## Entity Disambiguation

When users mention these terms, clarify which entity they mean:

**"Institute" can mean:**
- **Institution** (formal): A university or research center in `institutions` table (`institution_id`)
- **Institute** (academic schema): The `institute` TEXT field in academic tables (e.g., `innovation_grant_from_govt.institute`) — this is a VARCHAR name, NOT a foreign key to `institutions`
- **Key distinction**: Core schema uses UUID foreign keys; academic schema uses raw TEXT institute names

**"Grant" can mean:**
- **Funding** (core): Individual researcher grants in `funding` table, linked to `researchers` and `institutions`
- **Innovation Grant** (academic): Government scheme grants in `innovation_grant_from_govt`, linked by TEXT institute name
- **Key distinction**: `funding` has UUID FKs; `innovation_grant_from_govt` has TEXT institute names

**"Student" can mean:**
- **PhD Students**: `phd_students` table (research scholars)
- **Sanctioned Intake**: `sanctioned_intake` table (approved seats by program)
- **Actual Strength**: `actual_student_strength` table (enrolled students)
- **Key distinction**: Use `sanctioned_intake` + `actual_student_strength` together for admission gap analysis

**"Researcher" vs "Author":**
- **Researcher**: Profile in `researchers` table (may not have publications yet)
- **Author**: Implicit via publications; there is NO `researcher_publications` junction table in current schema
- **Key gap**: Publications are standalone; researcher-publication linkage is via text search or external ORCID matching

---

## Business Terminology

| Term | Definition | Notes |
|------|------------|-------|
| **Access Tier** | Visibility level: 1=public, 2=industry, 3=academic, 4=government | RLS-enforced; government sees all, public sees only tier=1 |
| **h-index** | Research impact metric: h papers with ≥h citations each | Stored on `researchers.h_index`; NULL if unknown |
| **TRL** | Technology Readiness Level (1-9): innovation maturity stage | `innovations_at_various_stages_of_technology_readiness_level.stage_of_technology` |
| **Capex** | Capital expenditure (infrastructure, equipment) | `financial_expenses_capital` |
| **Opex** | Operational expenditure (salaries, maintenance) | `financial_expenses_operational` |
| **IPO Patent** | Indian Patent Office patent filing | `combined_ipo_patent_data`; status ∈ {Granted, Filed, Examined, Rejected} |
| **Financial Year** | Indian FY format: '2020-21', '2021-22', '2022-23' | Stored as TEXT in academic tables; use string comparison |
| **ORCID** | Open Researcher and Contributor ID (0000-0000-0000-0000) | `researchers.orcid`; unique identifier for deduplication |
| **DOI** | Digital Object Identifier for publications | `publications.doi`; NULL for unpublished work |

---

## Standard Filters

Always apply these filters unless explicitly told otherwise:

```sql
-- Respect tier isolation (critical for DPDP compliance)
-- This is automatically enforced by RLS, but include for explicit clarity:
WHERE access_tier <= :user_tier

-- Exclude test or sample data (if any institution_name contains 'test')
AND institution_id NOT IN (
    SELECT institution_id FROM institutions 
    WHERE name ILIKE '%test%' OR name ILIKE '%sample%'
)
```

**When querying academic schema tables (innovation_grant_from_govt, etc.):**
```sql
-- Academic tables use TEXT institute names, not UUIDs
-- Always filter to known NRG institutions:
WHERE institute IN (
    SELECT DISTINCT name FROM institutions WHERE country = 'India'
)
```

**When querying publications:**
```sql
-- Exclude preprints without DOI unless explicitly asked:
AND (doi IS NOT NULL OR venue IS NOT NULL)
```

---

## Key Metrics

### Total Funding by Institution
- **Definition**: Sum of all funding amounts received by an institution
- **Formula**: `SUM(amount) FROM funding GROUP BY institution_id`
- **Source**: `funding.amount`, `funding.institution_id`
- **Time grain**: Usually by year (`DATE_PART('year', start_date)`)
- **Caveats**: NULL amounts excluded; overlaps possible if researcher changed institutions

### Publication Count per Researcher
- **Definition**: Number of publications associated with a researcher
- **Formula**: Direct count from `publications` is NOT possible (no junction table). Use ORCID matching or approximate via text search.
- **Workaround**: `SELECT COUNT(*) FROM publications WHERE abstract ILIKE '%' || researcher_name || '%'`
- **Caveats**: Name matching is fuzzy; prefer ORCID linkage when available

### Patent Grant Rate
- **Definition**: % of patent applications that reached 'Granted' status
- **Formula**: `COUNT(*) FILTER (WHERE status = 'Granted') / COUNT(*) * 100`
- **Source**: `combined_ipo_patent_data.status`
- **Caveats**: 'Filed' patents may still be pending; use grant_date for confirmation

### Student Intake Gap
- **Definition**: Difference between sanctioned seats and actual enrolled students
- **Formula**: `sanctioned_intake.intake - actual_student_strength.total_students`
- **Source**: `sanctioned_intake` JOIN `actual_student_strength` ON (institute, program, financial_year)
- **Caveats**: Academic schema uses TEXT institute names; join on name matching

### Researcher Density
- **Definition**: Researchers per institution, normalized by state
- **Formula**: `COUNT(researcher_id) / state_population * 1,000,000`
- **Source**: `researchers` JOIN `institutions`
- **Caveats**: `state` field on both tables; use `institutions.state` as canonical

---

## Data Freshness

| Table | Update Frequency | Typical Lag | Notes |
|-------|------------------|-------------|-------|
| researchers | Batch (weekly) | 1-7 days | Manual curation for new profiles |
| publications | Batch (weekly) | 1-7 days | Scraped from DOI resolvers |
| funding | Batch (monthly) | 7-30 days | From institutional reports |
| innovation_grant_from_govt | Annual | 3-6 months | Government data dumps |
| combined_ipo_patent_data | Quarterly | 1-3 months | IPO bulk data |
| academic_courses_details | Annual | 1-3 months | Academic calendar aligned |
| phd_students | Annual | 1-3 months | Census-based |
| training_pairs | Real-time | <1 second | Generated from live queries |

To check data freshness:
```sql
SELECT 
    'researchers' AS table_name, 
    MAX(updated_at) AS latest_data 
FROM researchers
UNION ALL
SELECT 'publications', MAX(updated_at) FROM publications
UNION ALL
SELECT 'funding', MAX(updated_at) FROM funding;
```

---

## Knowledge Base Navigation

Use these reference files for detailed table documentation:

| Domain | Reference File | Use For |
|--------|----------------|---------|
| Core Research | `references/tables/core_research.md` | researchers, institutions, publications, labs, funding |
| Innovation & IP | `references/tables/innovation_ip.md` | patents, TRL, grants, incubation, startups |
| Academic Operations | `references/tables/academic_operations.md` | courses, students, intake, expenses |
| Training & Quality | `references/tables/training_quality.md` | training_pairs, query logs, quality grades |
| Entities | `references/entities.md` | Entity definitions and relationships |
| Metrics | `references/metrics.md` | KPI calculations and formulas |

---

## Common Query Patterns

### Funding by State and Year
```sql
SELECT 
    i.state,
    DATE_PART('year', f.start_date) AS year,
    COUNT(*) AS grant_count,
    SUM(f.amount) AS total_funding,
    AVG(f.amount) AS avg_grant_size
FROM funding f
JOIN institutions i ON f.institution_id = i.institution_id
WHERE f.start_date >= '2020-01-01'
GROUP BY i.state, DATE_PART('year', f.start_date)
ORDER BY year DESC, total_funding DESC;
```

### Top Researchers by Funding (with tier filter)
```sql
SELECT 
    r.name,
    r.research_area,
    i.name AS institution,
    COUNT(f.funding_id) AS num_grants,
    SUM(f.amount) AS total_funding
FROM researchers r
JOIN funding f ON r.researcher_id = f.researcher_id
JOIN institutions i ON r.state = i.state  -- approximate linkage
WHERE f.access_tier <= 3  -- academic tier
GROUP BY r.researcher_id, r.name, r.research_area, i.name
ORDER BY total_funding DESC
LIMIT 20;
```

### Patent Status Distribution by Institute
```sql
SELECT 
    institute,
    status,
    COUNT(*) AS patent_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY institute), 2) AS pct
FROM combined_ipo_patent_data
WHERE financial_year >= '2020-21'
GROUP BY institute, status
ORDER BY institute, patent_count DESC;
```

### Student Intake vs Actual (Admission Gap)
```sql
SELECT 
    s.institute,
    s.program,
    s.financial_year,
    s.intake AS sanctioned_seats,
    COALESCE(a.total_students, 0) AS actual_students,
    s.intake - COALESCE(a.total_students, 0) AS gap,
    ROUND(COALESCE(a.total_students, 0) * 100.0 / NULLIF(s.intake, 0), 2) AS fill_rate_pct
FROM sanctioned_intake s
LEFT JOIN actual_student_strength a 
    ON s.institute = a.institute 
    AND s.program = a.program 
    AND s.financial_year = a.financial_year
WHERE s.financial_year = '2022-23'
ORDER BY gap DESC;
```

---

## Troubleshooting

### Common Mistakes
- **Joining academic schema to core schema**: Academic tables use TEXT institute names; core uses UUID `institution_id`. Use `institutions.name` as bridge.
- **Year comparison on financial_year**: Stored as TEXT ('2020-21'), not INTEGER. Use string comparison or parse with `SUBSTRING(financial_year, 1, 4)::INTEGER`.
- **NULL h_index**: Many researchers have NULL h_index. Use `COALESCE(h_index, 0)` for aggregations.
- **Access tier confusion**: Tier 1=public, 2=industry, 3=academic, 4=government. RLS handles this automatically.

### Access Issues
- If querying `researchers` and getting fewer rows than expected: Check RLS — your session tier may be limiting results.
- For PII-restricted columns (`phone`, `email`): Government tier (4) required; lower tiers see NULL.

### Performance Tips
- Filter by `state` or `research_area` early — these have indexes.
- For `publications` text search, use `to_tsvector` + GIN index (if available) rather than `ILIKE`.
- Avoid joining `researchers` directly to `publications` — no FK exists; use ORCID or name matching.
- Academic schema tables are denormalized (TEXT institute names) — prefer filtering by name lists over joins.
