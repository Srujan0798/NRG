"""HTTP 500 audit event response regressions."""

from fastapi.testclient import TestClient

import src.api.main as api_main


def test_unhandled_500_response_contains_audit_event_id():
    route_path = "/__batch3__/forced-500"
    added_route = None

    if not any(getattr(route, "path", None) == route_path for route in api_main.app.routes):
        @api_main.app.get(route_path)
        async def _forced_500():
            raise RuntimeError("forced batch3 failure")
        added_route = api_main.app.router.routes.pop()
        api_main.app.router.routes.insert(0, added_route)

    try:
        client = TestClient(api_main.app, raise_server_exceptions=False)
        response = client.get(route_path)

        assert response.status_code == 500
        payload = response.json()
        assert payload["audit_event_id"]
        assert payload["audit_event_id"] != "audit_unavailable"
    finally:
        if added_route is not None:
            api_main.app.router.routes.remove(added_route)
