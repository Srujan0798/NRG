import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text()


def test_compose_uses_restart_healthchecks_and_no_password_defaults():
    compose = yaml.safe_load(_read("docker-compose.yml"))
    services = compose["services"]

    for service_name in ["postgres", "pgbouncer", "qdrant", "redis", "api", "frontend", "kong"]:
        service = services[service_name]
        assert service["restart"] == "unless-stopped"
        assert "healthcheck" in service

    for path in ROOT.glob("docker-compose*.yml"):
        source = path.read_text()
        assert "nrg_default_password" not in source
        assert "POSTGRES_PASSWORD:-nrg" not in source
        assert "POSTGRES_PASSWORD:-password" not in source.lower()
        for line in source.splitlines():
            if re.search(r"POSTGRES_PASSWORD\s*[:=]", line, re.IGNORECASE):
                assert "${POSTGRES_PASSWORD" in line


def test_kong_rate_limits_are_per_consumer_with_distinct_tier_quotas():
    expected = {
        "infrastructure/kong/kong.yaml": {
            "tier1-researcher": 120,
            "tier2-government": 300,
            "tier3-industry": 40,
        },
        "infrastructure/kong/kong.yml": {
            "researcher": 120,
            "government": 300,
            "industry": 40,
        },
    }

    for path, expected_minutes in expected.items():
        config = yaml.safe_load(_read(path))
        per_consumer = {
            plugin.get("consumer"): plugin["config"]["minute"]
            for plugin in config.get("plugins", [])
            if plugin.get("name") == "rate-limiting"
        }
        assert per_consumer == expected_minutes
        assert len(set(per_consumer.values())) == len(expected_minutes)

        for service in config.get("services", []):
            for route in service.get("routes", []):
                assert all(plugin.get("name") != "rate-limiting" for plugin in route.get("plugins", []))


def test_nginx_rejects_api_path_traversal_vectors():
    for path in ["infrastructure/nginx/conf.d/default.conf", "infrastructure/nginx/frontend.conf"]:
        source = _read(path)
        assert "$request_uri" in source
        assert r"\.\." in source
        assert "%2e%2e" in source
        assert "%252e%252e" in source
        assert "return 400" in source


def test_prometheus_intervals_match_slo_contract():
    prometheus_config = _read("infrastructure/helm/nrg/templates/monitors/prometheus-config.yaml")
    service_monitor = _read("infrastructure/helm/nrg/templates/monitors/prometheus-servicemonitor.yaml")

    assert "job_name: 'nrg-api-health'" in prometheus_config
    assert "scrape_interval: {{ .Values.prometheus.healthScrapeInterval | default \"15s\" }}" in prometheus_config
    assert "metrics_path: /health" in prometheus_config
    assert "job_name: 'nrg-api-metrics'" in prometheus_config
    assert "scrape_interval: {{ .Values.prometheus.metricsScrapeInterval | default \"60s\" }}" in prometheus_config
    assert "metricsScrapeInterval: \"60s\"" in _read("infrastructure/helm/nrg/values.yaml")
    assert "healthScrapeInterval: \"15s\"" in _read("infrastructure/helm/nrg/values.yaml")
    assert "path: /metrics" in service_monitor
    assert "path: /health" in service_monitor


def test_grafana_dashboard_urls_do_not_carry_auth_tokens():
    forbidden_params = {"token", "auth_token", "access_token", "api_key", "apikey", "jwt"}

    def walk(value):
        if isinstance(value, dict):
            for item in value.values():
                yield from walk(item)
        elif isinstance(value, list):
            for item in value:
                yield from walk(item)
        elif isinstance(value, str):
            yield value

    dashboard_dir = ROOT / "infrastructure/grafana/dashboards"
    for dashboard_path in dashboard_dir.glob("*.json"):
        dashboard = json.loads(dashboard_path.read_text())
        for value in walk(dashboard):
            if "://" not in value and not value.startswith("/"):
                continue
            params = set(parse_qs(urlsplit(value).query))
            assert params.isdisjoint(forbidden_params), f"{dashboard_path} exposes auth in URL: {value}"


def test_helm_vault_templates_escape_vault_agent_delimiters():
    for path in [
        "infrastructure/helm/nrg/templates/_helpers.tpl",
        "infrastructure/helm/nrg/templates/vault/vault-config.yaml",
        "infrastructure/helm/nrg/templates/deployments/postgres-deployment.yaml",
    ]:
        source = _read(path)
        assert not re.search(r"\{\{\-?\s*with\s+secret", source)
        assert not re.search(r"\{\{\s*secret\s+\"", source)
        assert not re.search(r"\{\{\s*\.Data\.", source)


def test_ci_docker_build_steps_use_buildx_cache():
    for path in [".github/workflows/cd.yml", ".github/workflows/deploy.yml"]:
        source = _read(path)
        assert "docker/setup-buildx-action@v3" in source
        assert source.count("docker/build-push-action@v5") == source.count("cache-from: type=gha")
        assert source.count("docker/build-push-action@v5") == source.count("cache-to: type=gha,mode=max")
        assert "dockerfile:" not in source

    assert "file: Dockerfile.api" in _read(".github/workflows/cd.yml")
