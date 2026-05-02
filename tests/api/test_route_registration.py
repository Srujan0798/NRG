"""Route registration invariants for explicit API imports."""

from collections import defaultdict
from pathlib import Path

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

import src.api.main as api_main


def test_routes_init_stays_import_free():
    init_source = Path("src/api/routes/__init__.py").read_text()

    assert "import " not in init_source
    assert "from " not in init_source
    assert "__all__: list[str] = []" in init_source


def test_registered_routes_have_no_method_path_conflicts():
    registered: dict[tuple[str, str], list[str]] = defaultdict(list)
    for route in api_main.app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods or []:
            if method in {"HEAD", "OPTIONS"}:
                continue
            registered[(method, route.path)].append(route.name)

    conflicts = {
        f"{method} {path}": names
        for (method, path), names in registered.items()
        if len(names) > 1
    }

    assert conflicts == {}


def test_core_registered_routes_respond():
    client = TestClient(api_main.app)
    expected = {
        "/openapi.json": 200,
        "/health/db": 200,
        "/health/llm": 200,
        "/api/health/killer_queries": 200,
    }

    for path, status_code in expected.items():
        response = client.get(path)
        assert response.status_code == status_code, path
