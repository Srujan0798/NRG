from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _compose() -> dict:
    return yaml.safe_load((ROOT / "docker-compose.yml").read_text())


def test_compose_routes_api_database_traffic_through_pgbouncer():
    compose = _compose()
    services = compose["services"]

    assert "pgbouncer" in services
    api_env = services["api"]["environment"]

    assert any("DATABASE_URL=" in item and "@pgbouncer:6432/" in item for item in api_env)
    assert not any("${POSTGRES_PASSWORD:-}" in item for item in api_env)
    assert services["api"]["depends_on"]["pgbouncer"]["condition"] == "service_healthy"


def test_pgbouncer_pool_defaults_are_bounded():
    pgbouncer = _compose()["services"]["pgbouncer"]
    env = dict(item.split("=", 1) for item in pgbouncer["environment"])

    assert pgbouncer["image"].startswith("edoburu/pgbouncer")
    assert env["POOL_MODE"] == "transaction"
    assert int(env["MAX_CLIENT_CONN"]) >= 200
    assert 10 <= int(env["DEFAULT_POOL_SIZE"]) <= 50


def test_pgbouncer_and_postgres_defaults_use_same_nonempty_password():
    compose = _compose()
    postgres_env = compose["services"]["postgres"]["environment"]
    pgbouncer_env = dict(item.split("=", 1) for item in compose["services"]["pgbouncer"]["environment"])

    assert postgres_env["POSTGRES_PASSWORD"] == "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}"
    assert "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}" in pgbouncer_env["DATABASE_URL"]
    assert "${POSTGRES_PASSWORD:-}" not in pgbouncer_env["DATABASE_URL"]
