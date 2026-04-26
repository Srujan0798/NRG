---
name: feedback_compose_one_command
description: Plain docker compose up must start the complete local production stack, including data dependencies.
type: feedback
---

# Compose One-Command Contract

The primary handover command must remain `docker compose up -d`. Core data dependencies cannot be hidden behind profiles if the API depends on them by default.

**Why:**

A fresh evaluator should not need to know Docker Compose profile mechanics before the system starts. If Postgres is profile-gated while the API defaults to PgBouncer/Postgres, the first-run path is broken even when `docker compose config --quiet` passes.

**How to apply:**

- Keep `postgres`, `pgbouncer`, `qdrant`, `redis`, `api`, and `frontend` in the default Compose service graph.
- Gate optional gateway/proxy services behind profiles, not required data services.
- Keep `tests/unit/test_compose_config.py::test_default_compose_up_includes_postgres_dependency` green.
- If docs mention one-command startup, verify it with `docker compose config --services`.

**Source:** Founder production handover directive, 2026-04-27.
