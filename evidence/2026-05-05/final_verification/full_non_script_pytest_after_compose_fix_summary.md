# Full Non-Script Pytest After Compose Fix

Date: 2026-05-05T19:25:00Z

Command:

```bash
.venv/bin/python -m pytest tests/ -q --ignore=tests/scripts --tb=short --no-cov -x
```

Result: PASS

- 1846 passed
- 57 skipped
- 261 deselected
- 286 warnings
- Runtime: 130.71s

Notes:

- The immediately previous run failed at
  `tests/config/test_docker_compose_pgbouncer.py::test_compose_routes_api_database_traffic_through_pgbouncer`.
- `docker-compose.yml` was corrected so API `DATABASE_URL` routes through
  `pgbouncer:6432`.
- Focused PgBouncer config tests passed before this final broad rerun.
