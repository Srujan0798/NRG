# Database Schema Design Review — NRG Platform

**Date:** 2026-04-25
**Database:** SQLite (dev) / PostgreSQL (prod)
**Reviewer:** Session 92 Agent (database-schema-designer skill)

---

## Schema Inventory (Verified)

### Actual SQLite Schema (from `src/data/nrg_research.db`)

| Table | PK Column | Row Count | Key Columns |
|-------|-----------|-----------|-------------|
| researchers | researcher_id | 5,615 | state, research_area, institution_id |
| institutions | institution_id | ~181 | type, state |
| publications | publication_id | ~12,000 | year, venue |
| researcher_publications | (composite) | — | researcher_id, publication_id |
| funding_records | funding_id | — | researcher_id, institution_id |
| keywords | keyword_id | — | keyword |
| publication_keywords | (composite) | — | publication_id, keyword_id |
| labs | lab_id | — | institution_id, research_area |
| researcher_labs | (composite) | — | researcher_id, lab_id |
| collaborations | collaboration_id | — | researcher_id_1, researcher_id_2 |
| patents | patent_id | — | researcher_id |
| research_documents | doc_id | — | researcher_id |
| projects | project_id | — | researcher_id |
| sqlite_sequence | (internal) | — | — |

### Missing Tables (in PostgreSQL, not in SQLite dev)
- `audit_events` — DB co-sign table (PostgreSQL only)
- `audit_db_cosign` — DBCoSign verification
- `tb_gov_ministries_mstr` — Government ministries lookup

---

## Issues Found

### Issue 1: Missing Composite Index on Junction Tables
**Severity:** ⚠️ High
**Tables:** `researcher_publications`, `researcher_labs`, `publication_keywords`

The junction tables have composite primary keys but no additional indexes for JOIN performance.

**Fix:**
```sql
-- researcher_publications: often queried by researcher_id alone
CREATE INDEX idx_rp_researcher ON researcher_publications(researcher_id);

-- publication_keywords: often filtered by keyword_id
CREATE INDEX idx_pk_keyword ON publication_keywords(keyword_id);
```

---

### Issue 2: `name` Column in `researchers` Is PII But Not Enforced
**Severity:** ⚠️ High
**Table:** `researchers`

The `name` column is plain text, not marked as PII in the schema. According to the PII strategy (ADR-004), researcher names are PII and should be subject to tier-based filtering.

**Fix:**
```sql
-- Add tier filter as a policy-level constraint, not column-level
-- (tier filtering is done at query time, not storage time)
-- However, the column should be documented:
COMMENT ON COLUMN researchers.name IS 'PII: Researcher full name. Tier 1 full access, Tier 2 aggregate, Tier 3 anonymized in queries.';
```

---

### Issue 3: No `updated_at` on `researchers` Table
**Severity:** 🟡 Medium
**Table:** `researchers`

The documented schema says `updated_at TIMESTAMP DEFAULT NOW()` but the actual SQLite schema has no `updated_at` column. No way to detect stale records.

**Fix:** Add `updated_at` column:
```sql
ALTER TABLE researchers ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
```

---

### Issue 4: `orcid` Not Indexed
**Severity:** 🟡 Medium
**Table:** `researchers`

ORCID is a unique researcher identifier but has no index. Should be UNIQUE constrained.

```sql
CREATE UNIQUE INDEX idx_researchers_orcid ON researchers(orcid);
```

---

### Issue 5: Missing Index for Common Filter Pattern
**Severity:** 🟡 Medium
**Pattern:** `researchers WHERE state = X AND research_area LIKE Y`

Currently has separate indexes on `state` and `research_area` but no composite index.

```sql
CREATE INDEX idx_researchers_state_area ON researchers(state, research_area);
```

---

### Issue 6: `funding_records.amount` Should Be DECIMAL Not REAL
**Severity:** 🟡 Medium
**Table:** `funding_records`

Financial amounts should use `DECIMAL(15,2)` for precision. FLOAT/DOUBLE can cause rounding errors.

```sql
-- Check actual type:
PRAGMA table_info(funding_records);
-- If type is REAL, migrate:
ALTER TABLE funding_records MODIFY amount DECIMAL(15,2);
```

---

## Schema vs. Documented Drift

| Document Says | Actual DB | Drift |
|-------------|-----------|-------|
| `researchers.updated_at` exists | Not present | ⚠️ Missing |
| `name` is VARCHAR(255) | Present | ✅ OK |
| `email` has UNIQUE constraint | No UNIQUE constraint | ⚠️ Missing |
| `institutions.institution_id` PK | Same | ✅ OK |
| `publications.doi` VARCHAR(50) | No length constraint | ⚠️ Missing |

---

## Recommendations

| Priority | Action | SQL |
|----------|--------|-----|
| P1 | Add ORCID unique index | `CREATE UNIQUE INDEX idx_researchers_orcid ON researchers(orcid)` |
| P1 | Add `updated_at` to researchers | `ALTER TABLE researchers ADD COLUMN updated_at TIMESTAMP` |
| P2 | Add composite state+area index | `CREATE INDEX idx_researchers_state_area ON researchers(state, research_area)` |
| P2 | Add UNIQUE on email | `CREATE UNIQUE INDEX idx_researchers_email ON researchers(email)` |
| P3 | Check funding amount type | `PRAGMA table_info(funding_records)` |
| P3 | Document PII columns with COMMENT | `COMMENT ON COLUMN researchers.name IS 'PII...'` |

---

## PostgreSQL Production Additions

For the production PostgreSQL schema, these are additionally required:

```sql
-- Row-Level Security (RLS) for tier-based access
ALTER TABLE researchers ENABLE ROW LEVEL SECURITY;

CREATE POLICY tier1_access ON researchers
    FOR ALL USING (access_tier <= 1);

CREATE POLICY tier2_access ON researchers
    FOR ALL USING (access_tier <= 2);

-- Audit events table (for DB co-sign)
CREATE TABLE audit_events (
    event_id TEXT PRIMARY KEY,
    chain_hash TEXT NOT NULL,
    per_user_binding TEXT,
    user_id TEXT,
    event_type TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Audit co-sign trigger (managed by db_cosign.py)
-- See ADR-006 for file locking requirements
```
