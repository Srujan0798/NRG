import subprocess
import time
from pathlib import Path

import pytest
import requests


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "infrastructure" / "kong" / "docker-compose.yml"
ADMIN_URL = "http://localhost:8002"


def run_compose(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def wait_for_kong(timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = requests.get(f"{ADMIN_URL}/status", timeout=2)
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(1)

    raise AssertionError("Kong did not become ready within the timeout")


@pytest.fixture(scope="module")
def kong_stack():
    """Use an existing Kong environment only when the Kong admin API is ready."""
    try:
        wait_for_kong(timeout_seconds=5)
    except Exception as exc:
        pytest.skip(f"Kong Gateway admin API not ready: {exc}")
    yield
