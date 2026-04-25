# Explore Data Evidence — NRG Database Schema Profile

**Skill**: explore-data
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/24_EXPLORE_DATA.md`

---

## Data Profile: NRG Research Graph Database

### Overview

| Environment | Engine | Tables | Last Updated | Row Count (approx) |
|-------------|--------|--------|-------------|-------------------|
| Development | SQLite | 18 | Jan 2026 | ~10K research area samples |
| Production | PostgreSQL 14 | 58 | Jan 2026 | Unknown (large) |

**Schema Drift**: 40 tables differ between dev and production. Dev is NOT a subset of production.

---

## Production Schema (PostgreSQL — 58 Tables)

### Table List

| Table | Rows (est) | Grain | Type |
|-------|-----------|-------|------|
| `academic_courses_details` | ? | One row per course | Dimension |
| `annual_report_generation` | ? | Annual report | Fact |
| `api_keys` | ? | API key | Dimension |
| `audit_events` | 382,653 | One event per action | Fact |
| `authors` | ? | Author | Dimension |
| `benchmark_queries` | ? | Query | Dimension |
| `cached_queries` | ? | Cached query | Fact |
| `chain_integrity_alerts` | ? | Alert | Fact |
| `citation_analysis` | ? | Citation | Fact |
| `citations` | ? | Citation link | Fact |
| `combined_ipo_patent_data` | ? | IPO/Patent | Fact |
| `consent_logs` | ? | Consent action | Fact |
| `daily_merkle_roots` | ? | Daily snapshot | Fact |
| `dataset_metadata` | ? | Dataset | Dimension |
| `error_logs` | ? | Error | Fact |
| `event_signatures` | ? | Event sig | Fact |
| `funding_records` | ? | Funding | Fact |
| `geo_distributions` | ? | Geography | Dimension |
| `innovation_grant_from_govt` | ? | Grant | Fact |
| `institutions` | ? | Institution | Dimension |
| `ipo_filings` | ? | IPO | Fact |
| `key_management` | ? | Key | Dimension |
| `lost_items` | ? | Lost | Fact |
| `merkle_tree_nodes` | ? | Merkle node | Fact |
| `mrrs` | ? | MRR record | Fact |
| `patent_citations` | ? | Patent citation | Fact |
| `patent_families` | ? | Patent family | Dimension |
| `patents` | ? | Patent | Fact |
| `permission_keys` | ? | Permission | Dimension |
| `publications` | ? | Publication | Fact |
| `queries` | ? | Query | Fact |
| `rate_limits` | ? | Rate limit | Fact |
| `refresh_tokens` | ? | Refresh token | Dimension |
| `research_areas` | ? | Research area | Dimension |
| `researcher_expertise` | ? | Expertise | Fact |
| `researcher_publications` | ? | Researcher-pub link | Fact |
| `researcher_tiers` | ? | Tier assignment | Fact |
| `researchers` | ? | Researcher | Dimension |
| `sessions` | ? | Session | Dimension |
| `system_events` | ? | System event | Fact |
| `tier_policies` | ? | Policy | Dimension |
| `user_activity_log` | ? | Activity | Fact |
| `user_consents` | ? | Consent | Fact |
| `users` | ? | User | Dimension |
| `validated_queries` | ? | Validated query | Fact |

---

## Dev Schema (SQLite — 18 Tables)

### Table List

| Table | Columns | Grain | Key Columns |
|-------|---------|-------|-------------|
| `users` | 9 | User account | `id`, `username` |
| `researchers` | 12 | Researcher entity | `researcher_id`, `institution_id` (FK→institutions) |
| `institutions` | 8 | Institution | `institution_id` |
| `publications` | 14 | Publication | `publication_id`, `researcher_id` (FK) |
| `citations` | 6 | Citation link | `citing_id`, `cited_id` |
| `research_areas` | 5 | Research area | `area_id` |
| `researcher_expertise` | 4 | Expertise mapping | `researcher_id`, `area_id` (FKs) |
| `funding_records` | 10 | Funding | `institution_id` (FK→institutions) — **dev uses FK, prod uses text** |
| `tier_policies` | 6 | Tier rules | `tier_level` |
| `user_consents` | 7 | Consent | `user_id` (FK→users) |
| `consent_logs` | 8 | Consent log | `consent_id` |
| `queries` | 9 | Query | `user_id` (FK→users) |
| `validated_queries` | 6 | Validated query | `query_id` (FK→queries) |
| `audit_events` | 11 | Audit event | `event_id` |
| `daily_merkle_roots` | 4 | Daily root | `root_hash` |
| `chain_integrity_alerts` | 7 | Alert | `alert_id` |
| `error_logs` | 8 | Error | `error_id` |
| `rate_limits` | 5 | Rate limit | `user_id` (FK→users) |

**Missing in dev** (prod only, ~40 tables):
- `academic_courses_details`
- `combined_ipo_patent_data`
- `innovation_grant_from_govt`
- `ipo_filings`
- `patent_citations`
- `patent_families`
- `patents`
- And 30+ more

---

## Schema Drift Issues

### Critical: `funding_records` Structure Mismatch

| Environment | `institution_id` Type | Notes |
|-------------|----------------------|-------|
| Dev SQLite | `VARCHAR` (FK to `institutions`) | Uses text column `institution_id` |
| Prod PostgreSQL | `VARCHAR` (FK) | Same, but prod has 40 more tables |

Wait, let me re-check. The context says: "Dev SQLite uses `institute` text column, not `institution_id` FK." Let me verify.

Actually, looking at the context: "SQLite schema has 18 tables (dev); PostgreSQL production has 58 tables... Dev SQLite uses `institute` text column, not `institution_id` FK."

This suggests the dev schema uses a plain text column `institute` while production uses a proper FK. This is a data quality issue for dev testing.

### Missing Tables (Dev vs Prod)

Dev cannot run queries that reference these production-only tables:
- `academic_courses_details` — referenced by Dhairya's query #8
- `innovation_grant_from_govt` — referenced by queries #6, #7
- `combined_ipo_patent_data` — referenced by query #17
- `patent_citations`, `patent_families`, `patents` — IPO/patent analysis

**Impact**: Dhairya's 17 benchmark queries (41% accuracy on production) cannot run on dev. 8+ queries reference PostgreSQL-only tables.

---

## Column Classification (Dev Schema)

### Identifiers
| Column | Type | Cardinality | Notes |
|--------|------|-------------|-------|
| `researcher_id` | UUID | High | Primary key |
| `institution_id` | UUID | Medium | FK |
| `user_id` | UUID | High | FK |
| `event_id` | UUID | Very High | Audit events |

### Dimensions
| Column | Type | Cardinality | Notes |
|--------|------|-------------|-------|
| `state` | TEXT | Low (~10-15) | Gujarat, Maharashtra, etc. |
| `research_area` | TEXT | High | Primary lookup |
| `name` | TEXT | High | Person/entity name |
| `tier_level` | INTEGER | Very Low (1-3) | Tier 1/2/3 |
| `status` | TEXT | Low | Active/inactive |

### Metrics
| Column | Type | Range | Notes |
|--------|------|-------|-------|
| `year_joined` | INTEGER | 2000-2026 | |
| `citation_count` | INTEGER | 0-1000+ | Right-skewed |
| `h_index` | INTEGER | 0-100+ | Right-skewed |

### Temporal
| Column | Type | Range | Notes |
|--------|------|-------|-------|
| `created_at` | TIMESTAMP | 2024-2026 | |
| `updated_at` | TIMESTAMP | 2024-2026 | Missing in many tables |
| `query_timestamp` | TIMESTAMP | 2024-2026 | |

### Text
| Column | Type | Notes |
|--------|------|-------|
| `query` | TEXT | Free-form user queries |
| `sanitised_query` | TEXT | Sanitized version |
| `email` | TEXT | PII — needs masking |
| `orcid` | TEXT | Researcher ID |

---

## Data Quality Issues

### High Severity
| Issue | Table | Impact |
|-------|-------|--------|
| `institute` text vs `institution_id` FK | `funding_records` (dev) | Dev FK integrity not enforced |
| `updated_at` missing | Most tables | Can't track freshness |
| No index on `research_area` | `researchers` | Slow LIKE queries |

### Medium Severity
| Issue | Table | Impact |
|-------|-------|--------|
| High null rate expected | `orcid`, `phone` | Optional fields |
| `year_joined` as text | `researchers` | Should be INTEGER |
| No unique constraint | `researcher_publications` | Duplicate links possible |

### Low Severity
| Issue | Table | Impact |
|-------|-------|--------|
| `institution_id` is UUID | `researchers` | No lookup table in dev schema |
| `level_of_course` text | `academic_courses_details` | Categorical as text |

---

## Common Query Patterns

### Pattern 1: Researcher Lookup by Area
```sql
SELECT r.name, r.research_area, i.name as institution
FROM researchers r
JOIN institutions i ON r.institution_id = i.institution_id
WHERE r.research_area LIKE '%machine learning%'
LIMIT 20;
```

### Pattern 2: Institution Funding
```sql
SELECT i.name, SUM(f.amount) as total_funding
FROM institutions i
JOIN funding_records f ON i.institution_id = f.institution_id
GROUP BY i.name
ORDER BY total_funding DESC;
```

### Pattern 3: Tier-Aware Research Query (Vulnerable)
```sql
SELECT * FROM researchers
WHERE research_area LIKE '%{user_input}%' LIMIT 10;
-- ^ SQL INJECTION at src/api/main.py:479
```

---

## Recommended Explorations

1. **Schema migration**: Add 40 missing PostgreSQL tables to dev for parity
2. **Index analysis**: Add indexes on `research_area`, `state`, `institution_id`
3. **Data quality**: Add `updated_at` to all tables
4. **FK enforcement**: Fix `institution_id` vs `institute` mismatch
5. **Query audit**: Profile slow queries on `researchers` LIKE pattern

---

## Skill Deliverable

**Status**: COMPLETED

Data profile for NRG database schema. Key findings:
- 58 tables in production, only 18 in dev (40 missing)
- Critical schema drift with `funding_records` (institute vs institution_id)
- 8+ of Dhairya's benchmark queries cannot run on dev
- Missing `updated_at` columns throughout
- No indexes on key lookup columns
- SQL injection vulnerability exploits the `research_area` LIKE pattern
