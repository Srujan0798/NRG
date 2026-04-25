# SQL Queries Audit — Patterns, Gaps, and Validator Coverage

**Skill**: `sql-queries`
**Date**: 2026-04-25
**Analyst**: Eternal Shishya
**Evidence File**: `evidence/18_SQL_QUERIES.md`

---

## 1. Schema Gap: 18 Dev Tables vs 58 Production Tables

### Critical Mismatch

| Environment | Tables | Status |
|------------|--------|--------|
| Dev SQLite (`nrg_research.db`) | **18** | Working, simplified subset |
| Prod PostgreSQL (`db_struct.sql`) | **58** | Authoritative, 40 tables missing |

The `schema_hints.md` documents 58 tables with specific query patterns for each. However, the dev environment only has 18 tables. The most-referenced table in Dhairya's benchmark — `academic_courses_details` (referenced in **9 of 17 queries**) — **does not exist in dev SQLite**.

### Tables Missing from Dev (Subset — Most Critical)

| Table | Dhairya Queries | Purpose |
|-------|----------------|---------|
| `academic_courses_details` | Q1,Q2,Q8,Q9,Q10,Q11,Q12,Q13,Q14 | Innovation curriculum, credit scoring |
| `innovation_grant_from_govt` | Q3,Q4,Q7,Q16 | Government grants by agency/institute |
| `innovations_at_various_stages..._readiness_level` | Q5,Q6,Q17 | TRL stages (Level 1–9) |
| `combined_ipo_patent_data` | Q7,Q13 | Patent records with status |
| `financial_expenses_capital` | Q14 | Capital expenditure |
| `financial_expenses_operational` | Q16 | Operational expenditure |
| `incubation_details` | Q13 | Pre-incubation + incubation |
| `patents_details` | Q13 | Patent summary by year |
| `phd_students` | Q11 | PhD student counts |
| `placements_and_higher_studies` | Q12 | Placement rates, salary |

### The `credit_score` Parsing Trap

The `schema_hints.md:26-37` documents a critical parsing rule that many LLMs get wrong:

```sql
-- WRONG (will return NULL or 0 for "3:1" format):
SELECT SUM(CAST(total_credit_score AS INTEGER))
FROM academic_courses_details

-- RIGHT:
SELECT SUM(SPLIT_PART(total_credit_score, ':', 1)::double precision)
FROM academic_courses_details
```

The TextToSQL skill generates queries against the PostgreSQL schema. If the `validator.py` doesn't check for this pattern, a wrong query would pass validation and return incorrect results.

**Finding**: The `QueryCompletenessValidator` (`validator.py:113-217`) catches HAVING without GROUP BY, ORDER BY issues, and incomplete markers — but does **NOT** check for `CAST(...AS INTEGER)` on columns that contain composite formats like `"3:1"`.

---

## 2. SQL Injection Vulnerability at `main.py:479`

**This was identified in evidence/05 and confirmed in evidence/10. It is documented here because the `sql-queries` skill is the right framework for the fix.**

The query at `src/api/main.py:479`:
```python
f"SELECT * FROM researchers WHERE research_area LIKE '%{request.query.split()[0]}%' LIMIT 10"
```

This is **raw string interpolation** inside an `f-string`. Even though there's a `SQLValidator` class in `validator.py`, the query at line 479 uses `db.execute_query` directly — bypassing the validator entirely.

**The Fix** (using the sql-queries skill's dialect knowledge):
```python
# Parameterized query (works in both SQLite and PostgreSQL):
db.execute_query(
    "SELECT * FROM researchers WHERE research_area LIKE ? LIMIT 10",
    (f"%{request.query.split()[0]}%",),
    user_tier=user_tier,
)
```

---

## 3. The `QueryCompletenessValidator` — What It Catches

The `validator.py:113-217` is **excellent** and comprehensive:

| Pattern | Catches | Example |
|---------|---------|---------|
| Truncation markers | ✅ | `-- [INCOMPLETE]`, `-- TODO`, `-- FIXME` |
| Unclosed parentheses | ✅ | `SELECT * FROM (SELECT * FROM researchers` |
| Trailing operators | ✅ | `WHERE name = 'John' AND` |
| HAVING without GROUP BY | ✅ | `HAVING COUNT(*) > 5` |
| ORDER BY without aggregate | ✅ | `ORDER BY name` when `DISTINCT` present |
| Multi-statement injection | ✅ | `SELECT * FROM researchers; DROP TABLE` |
| LIMIT bypass | ✅ | `LIMIT 999999` |

**30 adversarial SQL test cases** are defined in `ADVERSARIAL_SQL_TESTS` (validator.py:221-308) — one of the most comprehensive adversarial SQL test suites seen.

---

## 4. What the Validator Does NOT Catch

### Gap 1: Composite Format Casts (e.g., `credit_score "3:1"`)
```sql
-- Passes validation, wrong results:
SELECT SUM(CAST(total_credit_score AS INTEGER))
FROM academic_courses_details

-- Correct query:
SELECT SUM(SPLIT_PART(total_credit_score, ':', 1)::double precision)
FROM academic_courses_details
```

### Gap 2: Missing `NULLIF` for Division by Zero
```sql
-- Passes validation, crashes on zero division:
SELECT total_funding / total_students FROM stats

-- Correct:
SELECT total_funding / NULLIF(total_students, 0) FROM stats
```

### Gap 3: Fuzzy Text Matching on `institute` Column
The schema requires `LIKE '%IIT%'` for fuzzy matching on institution names. The validator doesn't know this — it would accept `WHERE institute = 'IIT Madras'` which would return 0 rows.

### Gap 4: `institution_id` vs `institute` — Column Name Ambiguity
The PostgreSQL schema uses `institution_id` (FK) in junction tables, but the `institutions` table has `name` not `institute`. The dev SQLite uses `institute` text column. Queries generated for PostgreSQL using `institution_id` will fail on SQLite and vice versa.

### Gap 5: `SPLIT_PART` Usage for `credit_score` — Not Enforced
The `schema_hints.md` documents `SPLIT_PART(total_credit_score, ':', 1)` as the correct way to extract credits from `"3:1"` format. The validator doesn't enforce this — it would accept the wrong cast.

---

## 5. Dhairya Query Patterns — Where They Excel

The `schema_hints.md` (689 lines) is a **goldmine** of hard-won SQL knowledge:

### Pattern 1: CTE for Multi-Step Aggregation
```sql
-- Q3/Q4: Top N funding agencies
WITH GrantData AS (
    SELECT gov_organisation_name, SUM(grant_received) as total
    FROM innovation_grant_from_govt
    GROUP BY gov_organisation_name
)
SELECT * FROM GrantData ORDER BY total DESC LIMIT 5;
```
**Best Practice**: Use CTEs to separate aggregation stages — readable, debuggable.

### Pattern 2: YoY Comparison with Self-Join
```sql
-- Q4: YoY grant drop >50%
WITH YearlyGrants AS (
    SELECT institute, year_of_receiving, SUM(grant_received) as total_funding
    FROM innovation_grant_from_govt
    GROUP BY institute, year_of_receiving
)
SELECT curr.institute, curr.total_funding, prev.total_funding as prev_funding,
       ((curr.total_funding - prev.total_funding) / prev.total_funding::float) * 100 as growth_pct
FROM YearlyGrants curr
JOIN YearlyGrants prev ON curr.institute = prev.institute
    AND prev.year_of_receiving = '2020-21'
WHERE curr.year_of_receiving = '2022-23'
  AND ((curr.total_funding - prev.total_funding) / prev.total_funding::float) < -0.5;
```
**Best Practice**: Self-join for time-series comparison — clean, no subqueries.

### Pattern 3: Window Functions for Running Totals
```sql
-- Not explicitly in Dhairya, but schema_hints.md mentions aggregate patterns
SUM(revenue) OVER (PARTITION BY institute ORDER BY financial_year
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_total
```
**Best Practice**: Window functions for cumulative metrics.

---

## 6. Production PostgreSQL Dialect Notes

### `SPLIT_PART` — Critical for PostgreSQL
```sql
-- Extract first part of "3:1" credit score
SPLIT_PART(total_credit_score, ':', 1)::double precision

-- Extract second part (tutorial hours)
SPLIT_PART(total_credit_score, ':', 2)::double precision
```

### `DATE_TRUNC` for Fiscal Year
```sql
-- Truncate to financial year (April-March)
DATE_TRUNC('quarter', date_column) -- approximate
-- For true fiscal year:
CASE WHEN EXTRACT(MONTH FROM date_column) >= 4
     THEN DATE_TRUNC('year', date_column)
     ELSE DATE_TRUNC('year', date_column) - INTERVAL '1 year'
END as fiscal_year
```

### `ILIKE` for Case-Insensitive Text Matching
```sql
-- Correct for PostgreSQL:
SELECT * FROM innovation_grant_from_govt
WHERE gov_organisation_name ILIKE '%dst%'

-- Note: SQLite uses GLOB or LIKE (case-sensitive by default)
-- The TextToSQL skill must detect dialect and use appropriate operator
```

---

## 7. Missing Indexes (Performance Risk)

The `database-schema-designer` skill (evidence/13) identified missing indexes. The `schema_hints.md` hints at which columns are filtered:

| Table | Filter Columns Needing Index | Join Columns Needing Index |
|-------|------------------------------|---------------------------|
| `academic_courses_details` | `level_of_course`, `institute`, `financial_year` | `institute` |
| `innovation_grant_from_govt` | `gov_organisation_name`, `year_of_receiving` | `institute` |
| `institutions` | `state`, `type` | — |
| `researchers` | `state`, `research_area` | `institution_id` |
| `publications` | `year`, `access_tier` | — |
| `funding_records` | `agency`, `fiscal_year` | `institution_id` |
| Junction tables | — | `researcher_id`, `publication_id` |

**Performance Risk**: Without composite indexes on junction tables (`researcher_publications`, `project_researchers`), JOINs across large tables will be O(n²).

---

## 8. Key Recommendations

| Priority | Finding | Action |
|----------|---------|--------|
| **CRITICAL** | SQL injection at `main.py:479` | Parameterize immediately |
| **HIGH** | `credit_score "3:1"` format not validated | Add composite format detection to `QueryCompletenessValidator` |
| **HIGH** | Dev has 18 tables, prod has 58 — queries silently fail | Add table-existence check to validator; return "table not available in dev" message |
| **HIGH** | `NULLIF` not enforced for division | Add division-by-zero check to validator |
| **MEDIUM** | `ILIKE` vs `LIKE` dialect mismatch | Ensure schema extractor detects SQLite vs PostgreSQL |
| **MEDIUM** | Missing indexes on junction tables | Add `CREATE INDEX` recommendations to schema_hints |
| **LOW** | `institution_id` (PG) vs `institute` (SQLite) column name | Document dual-column mapping in schema_hints |

---

## 9. Validation Chain Summary

The SQL validation pipeline is well-architected:

```
TextToSQL Skill (skill.py)
  → Schema Extractor (schema_extractor.py) — builds schema context
  → SQL Generator (llm generate) — produces SQL
  → QueryCompletenessValidator (validator.py:113) — checks completeness
  → SQLValidator (validator.py:13) — security check (tables, columns, LIMIT)
  → Egress Guard (egress_guard/) — schema allowlist check
  → Database Executor — runs against SQLite or PostgreSQL
```

**Strength**: The layered validation approach (syntax → completeness → security → allowlist → execution) is sound.

**Weakness**: The `QueryCompletenessValidator` doesn't know about dialect-specific data format traps (like `credit_score "3:1"`).

---

## References

- Skill: `.agents/skills/sql-queries/SKILL.md`
- Schema Hints: `src/data/schema/schema_hints.md` (689 lines — authoritative reference)
- SQL Validator: `src/skills/text_to_sql/validator.py`
- Dhairya Audit: `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
- Database Schema Audit: `evidence/13_DATABASE_SCHEMA.md`
- Security Audit: `evidence/05_SECURITY_AUDIT.md`
