from pathlib import Path

import yaml


def _compose() -> dict:
    return yaml.safe_load(Path("docker-compose.yml").read_text())


def test_dev_profile_starts_all_dev_dependencies():
    services = _compose()["services"]

    # Core services should be available (with or without profiles)
    for svc in ["postgres", "qdrant", "redis", "api", "frontend"]:
        assert svc in services, f"Service {svc} missing from compose"
    # Postgres and kong remain profile-gated
    assert "profiles" in services["postgres"]
    assert "profiles" in services["kong"]


def test_api_container_uses_service_hostnames_for_dependencies():
    api = _compose()["services"]["api"]
    environment = api["environment"]

    assert api["build"]["dockerfile"] == "Dockerfile.api"
    assert api["env_file"] == [".env.${APP_ENV:-dev}"]
    assert "QDRANT_HOST=${QDRANT_HOST:-qdrant}" in environment
    assert "QDRANT_PORT=${QDRANT_PORT:-6333}" in environment
    assert "REDIS_URL=redis://redis:6379/0" in environment


def test_kong_uses_non_conflicting_public_port():
    ports = _compose()["services"]["kong"]["ports"]

    assert "${KONG_PORT:-8080}:8000" in ports
