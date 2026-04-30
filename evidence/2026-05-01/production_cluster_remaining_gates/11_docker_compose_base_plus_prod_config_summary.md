# Docker Compose Production Config Check
timestamp_utc=2026-04-30T21:44:51Z

Command: docker compose -f docker-compose.yml -f docker-compose.prod.yml config
Result: PASS
Exit code: 0

Note: Full config output was intentionally not retained because it expands environment values from compose files.
The incorrect override-only command remains captured in 06_docker_compose_prod_config.log and is expected to fail because docker-compose.prod.yml is an override file.
