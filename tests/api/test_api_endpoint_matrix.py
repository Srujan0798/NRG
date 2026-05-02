from __future__ import annotations

import re
from pathlib import Path

from fastapi.routing import APIRoute

from src.api.main import app


MATRIX_PATH = Path("docs/specs/API_ENDPOINT_MATRIX.md")
EXCLUDED_FRAMEWORK_PATHS = {
    "/docs",
    "/docs/oauth2-redirect",
    "/openapi.json",
    "/redoc",
}


def _registered_route_operations() -> set[tuple[str, str]]:
    operations: set[tuple[str, str]] = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if route.path in EXCLUDED_FRAMEWORK_PATHS:
            continue
        for method in route.methods or set():
            if method in {"HEAD", "OPTIONS"}:
                continue
            operations.add((method, route.path))
    return operations


def _documented_route_operations() -> set[tuple[str, str]]:
    content = MATRIX_PATH.read_text()
    operations: set[tuple[str, str]] = set()
    row_pattern = re.compile(r"^\|\s*`(?P<method>[A-Z]+)`\s*\|\s*`(?P<path>[^`]+)`\s*\|")
    for line in content.splitlines():
        match = row_pattern.match(line)
        if match:
            operations.add((match.group("method"), match.group("path")))
    return operations


def test_api_endpoint_matrix_matches_registered_routes() -> None:
    assert _documented_route_operations() == _registered_route_operations()
