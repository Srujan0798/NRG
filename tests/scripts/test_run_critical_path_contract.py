from pathlib import Path


def test_api_image_includes_alembic_config():
    dockerfile = Path("Dockerfile.api").read_text()

    assert "COPY alembic.ini" in dockerfile
    assert "COPY alembic/" in dockerfile


def test_critical_path_runner_uses_container_venv_alembic_with_config():
    runner = Path("scripts/run_critical_path.sh").read_text()

    assert "api /app/venv/bin/alembic -c alembic.ini upgrade head" in runner
    assert "python -m alembic upgrade head" not in runner


def test_final_runner_delegates_to_strict_verified_runner_and_uses_login_username():
    runner = Path("scripts/run_critical_path_final.sh").read_text()

    assert "scripts/run_critical_path.sh" in runner
    assert "--strict" in runner
    assert "--walk" in runner
    assert '\\"username\\"' in runner
    assert '"email"' not in runner
    assert "docker compose -f docker-compose.prod.yml up -d" not in runner
    assert "frontend/tests/e2e/acceptance_walk.spec.ts" not in runner
