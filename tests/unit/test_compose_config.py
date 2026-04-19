from pathlib import Path

import yaml


def _compose() -> dict:
    return yaml.safe_load(Path("docker-compose.yml").read_text())


def test_dev_profile_starts_all_dev_dependencies():
    services = _compose()["services"]

    assert "dev" in services["postgres"]["profiles"]
    assert "dev" in services["qdrant"]["profiles"]
    assert "dev" in services["redis"]["profiles"]
    assert "dev" in services["api"]["profiles"]


def test_api_container_uses_service_hostnames_for_dependencies():
    api = _compose()["services"]["api"]
    environment = api["environment"]

    assert api["build"]["dockerfile"] == "Dockerfile.api"
    assert api["env_file"] == [".env"]
    assert "QDRANT_HOST=qdrant" in environment
    assert "QDRANT_PORT=6333" in environment
    assert "REDIS_URL=redis://redis:6379/0" in environment


def test_kong_uses_non_conflicting_public_port():
    ports = _compose()["services"]["kong"]["ports"]

    assert "8080:8000" in ports
