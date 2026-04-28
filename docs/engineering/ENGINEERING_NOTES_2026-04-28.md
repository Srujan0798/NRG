# Engineering Notes — 2026-04-28

## Python 3.14 + Pydantic V1 Incompatibility

**Issue:** Python 3.14 (running here as `python3`) emits a deprecation warning from `pydantic.v1`:
```
UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
```

**Impact:** This is a **warning-only** issue on this machine. The codebase uses
`pydantic.v1` (the shim) rather than `pydantic` directly, which is the correct
pattern. The warning fires during import but does not break functionality.

**Production concern:** If deploying to a Python 3.14 host, upgrade to Pydantic v2 which
is fully compatible. The codebase is already using the `pydantic.v1` shim pattern,
so migration to Pydantic v2 should be straightforward.

**Note:** The `.venv` uses Python 3.11.7 which has no such warning. Only the system
Python 3.14 (used for some scripts) triggers this.

## JWT_SECRET Production Status

**File:** `.env.prod`
**Value:** `CHANGE_ME_generate_with_openssl_rand_hex_32`
**Length:** 43 bytes (≥ 32 bytes minimum for HS256)

**Status:** This is a **placeholder**. It must be replaced with a real secret
before production deployment:
```bash
openssl rand -hex 32
```

**Test fixtures** use short secrets (e.g., `test-secret-key-for-security-tests` at 36 bytes)
which is acceptable for test environments.

## Schema Alias Status

**Canonical alias:** `trl_stages`
**Maps to:** `innovations_at_various_stages_of_technology_readiness_level`

All 17 files across schema_retriever, table_relationships, sqlite_schema_extractor,
validator, and test files have been updated to use the canonical `trl_stages` alias
consistently. All 99 schema-related tests pass.

**Key files:**
- `src/skills/text_to_sql/schema_retriever.py`: `_table_to_alias()` maps long name → `trl_stages`
- `src/skills/text_to_sql/sqlite_schema_extractor.py`: `POSTGRESQL_ONLY_TABLES` includes `trl_stages`
- `src/skills/text_to_sql/validator.py`: `_check_stage_synonym_sql()` checks `TRL_STAGES` in SQL
- `tests/benchmarks/test_dhairya_regression.py`: Q05 and Q17 assert `TRL_STAGES` in SQL