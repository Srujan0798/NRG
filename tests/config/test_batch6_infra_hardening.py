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


def test_cd_build_pushes_authenticated_ghcr_images_before_smoke():
    workflow = yaml.safe_load(_read(".github/workflows/cd.yml"))
    assert workflow["permissions"]["contents"] == "read"
    assert workflow["permissions"]["packages"] == "write"
    assert workflow["env"]["POSTGRES_PASSWORD"] == "nrg_ci_password"

    build_steps = workflow["jobs"]["build"]["steps"]
    step_names = [step.get("name") for step in build_steps]
    assert step_names.index("Login to Container Registry") < step_names.index("Build API image")
    assert step_names.index("Build API image") < step_names.index("Run API smoke tests")

    login_step = next(step for step in build_steps if step.get("name") == "Login to Container Registry")
    assert login_step["uses"] == "docker/login-action@v3"
    assert login_step["with"]["registry"] == "${{ env.REGISTRY }}"
    assert login_step["with"]["username"] == "${{ github.actor }}"
    assert login_step["with"]["password"] == "${{ secrets.GITHUB_TOKEN }}"

    api_step = next(step for step in build_steps if step.get("name") == "Build API image")
    frontend_step = next(step for step in build_steps if step.get("name") == "Build frontend image")
    assert api_step["with"]["push"] is True
    assert frontend_step["with"]["push"] is True

    api_tag = "${{ env.REGISTRY }}/${{ steps.image.outputs.repository }}/api:${{ github.sha }}"
    frontend_tag = "${{ env.REGISTRY }}/${{ steps.image.outputs.repository }}/frontend:${{ github.sha }}"
    assert api_step["with"]["tags"] == api_tag
    assert frontend_step["with"]["tags"] == frontend_tag

    smoke_step = next(step for step in build_steps if step.get("name") == "Run API smoke tests")
    assert api_tag in smoke_step["run"]


def test_cd_staging_deploy_skips_when_aws_secrets_are_unconfigured():
    workflow = yaml.safe_load(_read(".github/workflows/cd.yml"))
    steps = workflow["jobs"]["deploy-staging"]["steps"]
    step_names = [step.get("name") for step in steps]

    assert step_names.index("Check AWS staging configuration") < step_names.index("Configure AWS credentials")

    check_step = next(step for step in steps if step.get("name") == "Check AWS staging configuration")
    assert check_step["id"] == "aws_config"
    assert "AWS_ROLE_ARN_STAGING" in check_step["env"]
    assert "AWS_REGION" in check_step["env"]
    assert "ECR_REGISTRY" in check_step["env"]
    assert "configured=false" in check_step["run"]

    guarded_steps = [
        "Configure AWS credentials",
        "Login to ECR",
        "Push images to ECR",
        "Deploy to ECS staging",
        "Run smoke tests",
    ]
    for name in guarded_steps:
        step = next(step for step in steps if step.get("name") == name)
        assert step["if"] == "steps.aws_config.outputs.configured == 'true'"

    skipped_step = next(step for step in steps if step.get("name") == "Skip staging deploy when AWS secrets are absent")
    assert skipped_step["if"] == "steps.aws_config.outputs.configured != 'true'"
    assert "AWS staging secrets are not configured" in skipped_step["run"]


def test_cd_production_deploy_requires_manual_dispatch():
    workflow = yaml.safe_load(_read(".github/workflows/cd.yml"))
    production_job = workflow["jobs"]["deploy-production"]

    assert production_job["if"] == "github.event_name == 'workflow_dispatch' && github.event.inputs.environment == 'production'"


def test_cd_quality_bar_starts_seeded_api_before_c4_scorecard():
    workflow = yaml.safe_load(_read(".github/workflows/cd.yml"))
    quality_bar_steps = workflow["jobs"]["quality-bar"]["steps"]
    step_names = [step.get("name") for step in quality_bar_steps]

    assert step_names.index("Start seeded API for C4 scorecard") < step_names.index("Run Quality Bar Scorecard")

    start_step = next(step for step in quality_bar_steps if step.get("name") == "Start seeded API for C4 scorecard")
    start_script = start_step["run"]
    assert workflow["env"]["NRG_LOCAL_RESEARCH_DB"] == "data/nrg_research.db"
    assert "python scripts/seed_production_subset.py --profile ci --no-audit" in start_script
    assert "python -m uvicorn src.api.main:app" in start_script
    assert "--workers 4" in start_script
    assert "NRG_QUOTA_DISABLED=1" in start_script
    assert "curl -sf http://localhost:8000/health" in start_script

    scorecard_step = next(step for step in quality_bar_steps if step.get("name") == "Run Quality Bar Scorecard")
    assert "NRG_C4_REQUIRE_LIVE=1 python scripts/quality_bar_scorecard.py --json-only" in scorecard_step["run"]


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


def test_deploy_workflows_normalize_ghcr_image_repository_names():
    deploy_source = _read(".github/workflows/deploy.yml")
    cd_source = _read(".github/workflows/cd.yml")

    for source in [deploy_source, cd_source]:
        assert "Normalize image repository" in source
        assert "tr '[:upper:]' '[:lower:]'" in source
        assert "${{ steps.image.outputs.repository }}" in source

    assert "${{ github.repository }}/nrg-api" not in deploy_source
    assert "${{ github.repository }}/nrg-frontend" not in deploy_source
    assert "${{ env.IMAGE_NAME }}/api" not in cd_source
    assert "${{ env.IMAGE_NAME }}/frontend" not in cd_source


def test_ci_scheduled_red_team_replay_runs_with_python():
    workflow = yaml.safe_load(_read(".github/workflows/ci.yml"))
    steps = workflow["jobs"]["red-team-live-replay"]["steps"]

    replay_step = next(step for step in steps if step.get("name") == "Run LB-5 live replay")
    replay_script = replay_step["run"]

    assert "python scripts/red_team_live_replay.py" in replay_script
    assert "bash scripts/red_team_live_replay.py" not in replay_script
    assert "--evidence evidence/ci/red-team-live-replay/17_red_team_results.md" in replay_script


def test_ci_scheduled_artifact_uploads_match_test_evidence_dirs():
    workflow = yaml.safe_load(_read(".github/workflows/ci.yml"))

    local_steps = workflow["jobs"]["local-release-gate"]["steps"]
    local_run = next(step for step in local_steps if step.get("name") == "Run sub-15-minute local gate")["run"]
    local_upload = next(step for step in local_steps if step.get("name") == "Upload local gate evidence")
    assert "EVIDENCE_DIR=evidence/ci/local-release-gate" in local_run
    assert "evidence/ci/local-release-gate/test_suite_full_final.xml" in local_upload["with"]["path"]

    slow_steps = workflow["jobs"]["slow-nightly"]["steps"]
    slow_run = next(step for step in slow_steps if step.get("name") == "Run slow suite")["run"]
    slow_upload = next(step for step in slow_steps if step.get("name") == "Upload slow suite evidence")
    assert "EVIDENCE_DIR=evidence/ci/slow-nightly" in slow_run
    assert "evidence/ci/slow-nightly/test_suite_full_final.xml" in slow_upload["with"]["path"]
