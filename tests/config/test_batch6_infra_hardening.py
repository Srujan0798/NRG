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


def test_cd_quality_bar_starts_seeded_api_before_c4_scorecard():
    workflow = yaml.safe_load(_read(".github/workflows/cd.yml"))
    quality_bar_steps = workflow["jobs"]["quality-bar"]["steps"]
    step_names = [step.get("name") for step in quality_bar_steps]

    assert step_names.index("Start seeded API for C4 scorecard") < step_names.index("Run Quality Bar Scorecard")

    start_step = next(step for step in quality_bar_steps if step.get("name") == "Start seeded API for C4 scorecard")
    start_script = start_step["run"]
    assert workflow["env"]["NRG_LOCAL_RESEARCH_DB"] == "data/nrg_research.db"
    assert "python scripts/seed_production_subset.py --profile ci --no-audit" in start_script
    assert "python -m src.api.main" in start_script
    assert "curl -sf http://localhost:8000/health" in start_script


def test_deploy_workflow_uses_ci_safe_test_env_and_skips_browser_collection():
    workflow = yaml.safe_load(_read(".github/workflows/deploy.yml"))

    assert workflow["env"]["DATABASE_URL"] == "sqlite:///data/nrg_research.db"
    assert workflow["env"]["NRG_TEST_DATABASE_URL"] == "sqlite:///data/nrg_research.db"
    assert workflow["env"]["NRG_LOCAL_RESEARCH_DB"] == "data/nrg_research.db"
    assert workflow["env"]["JWT_ALGORITHM"] == "HS256"
    assert len(workflow["env"]["JWT_SECRET"]) >= 32

    test_job = workflow["jobs"]["test"]
    step_names = [step.get("name") for step in test_job["steps"]]
    assert step_names.index("Seed CI SQLite data") < step_names.index("Run pytest")

    seed_step = next(step for step in test_job["steps"] if step.get("name") == "Seed CI SQLite data")
    assert "python scripts/seed_production_subset.py --profile ci --no-audit" in seed_step["run"]

    test_env = test_job["steps"][-1]["env"]
    assert test_env["NRG_TEST_ISOLATE_AUDIT"] == "1"
    assert test_env["COVERAGE_FILE"] == ".coverage.deploy"

    test_script = test_job["steps"][-1]["run"]
    assert "--ignore=tests/e2e" in test_script
    assert "--dist=loadgroup" in test_script
    assert "-n 2" in test_script
    assert "--no-cov-on-fail" in test_script
