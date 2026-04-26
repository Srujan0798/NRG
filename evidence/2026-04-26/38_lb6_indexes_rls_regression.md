# LB-6 Schema Index and Row Policy Regression

Date: 2026-04-26

## Scope

This evidence records local regression coverage for the LB-6 migration:

- `alembic/versions/lb6_schema_parity_indexes_rls_001.py`
- `tests/data/test_schema_indexes.py`
- `tests/data/test_rls_policies.py`
- `tests/data/test_schema_parity.py`

## Verification

Command:

```bash
PYTEST_ADDOPTS=--no-cov pytest \
  tests/data/test_schema_indexes.py \
  tests/data/test_rls_policies.py \
  tests/data/test_schema_parity.py \
  -q
```

Result:

```text
14 passed, 7 skipped in 0.85s
```

## Acceptance Notes

- Composite index definitions cover the LB-6 hot join/filter paths.
- Expression indexes cover normalized institute, applicant, and startup keys.
- Index DDL is idempotent and uses concurrent creation when requested.
- Row policy coverage includes `expertise`, `combined_ipo_patent_data`,
  `user_registration`, and `user_registration_old`.
- Row policy tests execute the migration helper and verify per-table RLS
  enablement.
- Downgrade tests verify RLS disablement, policy cleanup, view cleanup, and
  function cleanup.
- Schema parity remains at 58/58 locally; live database checks are skipped
  when PostgreSQL is not available in the local environment.
