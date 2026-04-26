# Compose Production Profile Check

Date: 2026-04-26

## Scope

This closes the local compose regression where `docker compose --profile prod`
could start the API and PgBouncer path without the PostgreSQL service being in
the same profile set.

## Verification

```bash
PYTEST_ADDOPTS=--no-cov pytest tests/unit/test_compose_config.py -q
docker compose config --quiet
scripts/forbidden_vocab_check.sh docker-compose.yml tests/unit/test_compose_config.py
```

Results:

```text
tests/unit/test_compose_config.py: 4 passed in 0.54s
docker compose config --quiet: exit 0
production vocabulary gate: exit 0
```

## Files

- `docker-compose.yml`
- `tests/unit/test_compose_config.py`

