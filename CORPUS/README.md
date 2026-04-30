# NRG — Canonical Project Corpus

**What is this:** Reference package for understanding the National Research Graph project.

---

## The 3 Official Source Files (from the person who gave the project)

| File | Description |
|------|-------------|
| `Core_Idea_Clean.md` | Vision & product specification — what NRG is and why |
| `db_struct.sql` | **Production PostgreSQL schema** — 3681 lines, pg_dump from actual 58-table database |
| `SQL_AUDIT_RAW_dhairya.sql` | Raw audit log from SesDhairya — query results and AI-generated SQL |

---

## SQL Audit Summary (cleaner version)

See `SQL_AUDIT_REPORT_CLEAN.md` for a clean summary of the 17 Dhairya queries.

**Key finding:** AI SQL generator scored 7/17 (41%) on production queries.
The 3 killer queries every release must pass are in `tests/benchmarks/killer_queries.yaml`.

---

## Database Schemas (which to use when)

| File | Type | Use |
|-------|------|-----|
| `schema/db_struct.sql` | PostgreSQL dump | **THE SOURCE OF TRUTH** — actual production schema with 58 tables |
| `schema/production_schema.sql` | PostgreSQL DDL | Ideal normalized production schema |
| `schema/nrg_full_schema.sql` | SQLite DDL | Local dev schema (18 tables, subset) |
| `schema/sqlite_schema.sql` | SQLite DDL | Older local schema |

---

## AI SQL Quality Hints (from Dhairya failures)

### Critical Rules
1. **`SPLIT_PART`** — Credit score format `"3:1"` must parse with `SPLIT_PART(col, ':', 1)`
2. **`Level 9`** — TRL Market Ready is stored as `"Level 9"`, NOT `"TRL 9"` or `"Market Ready"`
3. **62-char table** — `innovations_at_various_stages_of_technology_readiness_level` — never abbreviate
4. **CTE + GROUP BY** — YoY comparisons need CTE → GROUP BY → self-JOIN, never row-level

### Tables that matter
```
academic_courses_details          — 9 of 17 Dhairya queries
innovation_grant_from_govt       — funding analysis
combined_ipo_patent_data         — patent status = 'Granted'
innovations_at_various_stages_of_technology_readiness_level  — TRL pipeline
```

---

## Access Tiers (Row-Level Security)

| Tier | Role | Data |
|------|------|------|
| 1 | Researcher | Full details, all researchers |
| 2 | Government | Aggregated, anonymized |
| 3 | Industry | Overview only |

Every table has `access_tier INTEGER` column. Queries must filter by tier.

---

*For tests, benchmarks, and scripts — see the main project README.md*
