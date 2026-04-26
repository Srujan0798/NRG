# Final Production Revalidation — 2026-04-27

## Scope

This revalidation covers the handover-critical paths requested for NRG v1.0.0:

- default container startup contract
- backend tier, SQL, security, audit, and observability regression paths
- frontend production workspace regression, lint, and build
- forbidden-vocabulary gate
- Docker daemon availability on the current machine

The mandatory project source files are present in this repository:

- `Core_Idea_Clean.md`
- `db_struct.sql`
- `BACKLOG.md`
- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
- `NRG_SELF_AUDIT_REPORT_2026-04-24.md`

## Code Fix Applied In This Pass

Plain `docker compose up` previously omitted `postgres` from the default service graph because the Postgres service was profile-gated. That violated the one-command handover contract: the API defaults to `pgbouncer`, and PgBouncer requires Postgres.

Fix:

- `docker-compose.yml`: removed `profiles` from `postgres`.
- `README.md`: changed the primary container start command to `docker compose up -d`.
- `docs/PRODUCTION_WALKTHROUGH.md`: changed the production walk-through start command to `docker compose up -d`.
- `docs/PRODUCTION_READINESS_SUMMARY.md`: updated the startup-contract language.
- `tests/unit/test_compose_config.py`: added a regression requiring Postgres to be part of the default graph.

## Evidence Produced

| Evidence | Result |
|---|---|
| `compose_contract.log` | Compose contract tests passed: 7 passed. |
| `docker_compose_default_services.txt` | Default graph includes `postgres`, `pgbouncer`, `qdrant`, `redis`, `api`, and `frontend`. |
| `docker_compose_config_quiet.txt` | Compose config validates: PASS. |
| `backend_focused_production.log` | Focused backend production suite passed: 127 passed. |
| `full_python_suite.log` | Full Python suite passed: 1579 passed, 63 skipped, 219 deselected. |
| `frontend_focused_production.log` | Focused frontend hardening suite passed: 14 passed. |
| `frontend_full_suite.log` | Full frontend Jest suite passed: 19 suites passed, 76 tests passed. |
| `frontend_lint.log` | Frontend ESLint passed. |
| `frontend_build.log` | Vite production build passed. |
| `forbidden_vocab_check.txt` | Repository vocabulary gate passed. |
| `docker_daemon_status.txt` | Docker client exists, but Docker daemon was unavailable on this machine. |
| `docker_compose_ps_status.txt` | Live Compose status could not run because the Docker daemon was unavailable. |
| `local_port_occupancy.txt` | Existing SSH tunnel occupied default service ports `8000`, `5432`, `6379`, and `6333`; it was not terminated. |

## Live Container Startup Status

`docker compose config` is now correct for the one-command path. A live `docker compose up` run was not executed in this workspace because Docker Desktop / Docker daemon was not running:

```text
failed to connect to the docker API at unix:///var/run/docker.sock
```

Default local service ports were also occupied by an existing SSH tunnel owned by the user. That tunnel was left untouched.

## External Gates Not Claimed

These are still honest external gates, not code claims:

- sovereign-cluster C4 load SLO
- production Qdrant vector-drift baseline after corpus population
- official 600GB data ingest and validation
- physical iOS/Android and real carrier-network frontend validation
