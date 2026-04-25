# Database Migration Evidence

**Skill**: database-migration
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/34_DATABASE_MIGRATION.md`

---

## Database Migration Analysis: NRG

### Current State

| Environment | Tables | Engine | Migration Tool |
|-------------|--------|--------|---------------|
| Development | 18 | SQLite | None (manual) |
| Production | 58 | PostgreSQL 14 | Alembic |

**Schema Drift**: 40 tables missing in dev. Migration creates 47 tables, not 58.

---

## Migration Issues Found

### Issue 1: Incomplete Migration

**File**: `alembic/versions/add_production_tables_001.py`

**Problem**: Creates 47 tables but `db_struct.sql` has 58 tables.

**Missing tables** (11 Django/support tables):
- `auth_group`, `auth_group_permissions`, `auth_permission`
- `auth_user`, `auth_user_groups`, `auth_user_user_permissions`
- `django_admin_log`, `django_content_type`, `django_migrations`
- `django_session`, `user_registration_old`

**Impact**: Cannot run full schema parity tests in dev.

**Fix**: Add the 11 missing tables to migration OR acknowledge they're not needed for NRG API.

---

### Issue 2: `funding_records` Schema Mismatch

**Dev SQLite**: Uses `institute` text column (plain)
**Production PostgreSQL**: Uses `institution_id` FK to `institutions`

**Problem**: Code may expect one or the other depending on environment.

**Fix needed**: Ensure dev uses same FK structure as prod, OR add migration to change prod to text column.

---

### Issue 3: No `updated_at` Columns

**Problem**: Most tables lack `updated_at` timestamp column.

**Impact**: Cannot track data freshness. Hard to diagnose stale data issues.

**Fix**: Add `ALTER TABLE ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()` to all fact tables.

---

## Migration Strategy

### For Schema Parity (Dev → Prod Parity)

**Step 1**: Sync 40 missing tables to dev
```bash
# Option A: Use Alembic to auto-generate from prod
alembic migration --autogenerate

# Option B: Manually sync specific tables
# Create dev versions of missing tables with same schema
```

**Step 2**: Verify with test
```python
def test_all_prod_tables_exist_in_dev():
    prod_tables = get_postgres_tables()
    dev_tables = get_sqlite_tables()
    missing = prod_tables - dev_tables
    assert missing == set(), f"Missing tables: {missing}"
```

---

### For Zero-Downtime Production Migration

**Recommended approach**: Blue-green migration

**Phase 1**: Add new columns as nullable (backward compatible)
```python
# Migration 001: Add new column nullable
op.add_column('researchers', sa.Column('updated_at', sa.DateTime(), nullable=True))
```

**Phase 2**: Deploy code that writes to new column

**Phase 3**: Backfill existing rows
```sql
UPDATE researchers SET updated_at = created_at WHERE updated_at IS NULL;
```

**Phase 4**: Add NOT NULL constraint
```python
op.alter_column('researchers', 'updated_at', nullable=False)
```

---

## Critical Migration: Fix `funding_records`

### Current State
- Dev: `institute` TEXT
- Prod: `institution_id` FK → `institutions.institution_id`

### Migration Steps

**Step 1**: Add `institution_id` column to dev
```python
op.add_column('funding_records', sa.Column('institution_id', sa.String(), nullable=True))
```

**Step 2**: Backfill from `institute` text
```sql
UPDATE funding_records
SET institution_id = (
    SELECT institution_id FROM institutions
    WHERE institutions.name = funding_records.institute
)
WHERE institution_id IS NULL;
```

**Step 3**: Add FK constraint (after backfill)
```python
op.create_foreign_key(
    'fk_funding_institution',
    'funding_records', 'institutions',
    ['institution_id'], ['institution_id']
)
```

**Step 4**: Remove old `institute` column (after verification)
```python
op.drop_column('funding_records', 'institute')
```

---

## Rollback Strategy

### Checkpoint-Based Rollback

```python
# Before migration: create backup
op.execute("CREATE TABLE researchers_backup AS SELECT * FROM researchers")

try:
    # Perform migration
    op.add_column('researchers', sa.Column('updated_at', sa.DateTime()))
except Exception as e:
    # Rollback: restore from backup
    op.execute("DROP TABLE researchers")
    op.execute("CREATE TABLE researchers AS SELECT * FROM researchers_backup")
    raise
```

---

## Evidence of Migration Gaps

| Issue | Severity | Evidence |
|-------|----------|----------|
| 11 Django tables missing | 🟡 Medium | `tests/data/test_schema_parity.py` shows 7 passed, 4 skipped |
| `funding_records` mismatch | 🔴 High | Dev uses `institute` text, prod uses FK |
| No `updated_at` columns | 🟡 Medium | Schema review of db_struct.sql |
| No rollback tests | 🟡 Medium | No `test_migration_rollback.py` found |

---

## Skill Deliverable

**Status**: COMPLETED

Database migration analysis:
- 11 Django tables missing from migration (not critical for API)
- `funding_records` has schema mismatch between dev and prod
- No `updated_at` tracking columns — data freshness unknown
- Blue-green migration strategy documented for zero-downtime deploys
- Checkpoint-based rollback recommended for safety
