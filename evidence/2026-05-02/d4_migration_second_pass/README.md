# D4 Migration Safety Second Pass

Date: 2026-05-02

## Scope

This pass tightened the D4 Alembic migration after review:

- preserve NRG's canonical string identifier types instead of converting live
  drift columns to UUID;
- skip FK creation when referencing column types do not match;
- keep FK repairs `NOT VALID` so old drift can be repaired separately;
- keep hot-path indexes concurrent with `IF NOT EXISTS`;
- consolidate D4 migration contract tests under `tests/db/`.

## Verification

| Evidence | Result |
| --- | --- |
| `01_py_compile.log` | PASS |
| `02_targeted_tests.log` | PASS: 31 tests passed |
| `03_ruff.log` | PASS |
| `04_alembic_heads_verbose.log` | PASS: D4 is the sole `src/migrations` head |
| `05_git_diff_check.log` | PASS |

## Boundary

This proves the local migration contract and Alembic chain. Applying the
migration to a deployed PostgreSQL database is still an external database gate.
