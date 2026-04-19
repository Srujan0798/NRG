from fastapi.testclient import TestClient

import src.api.main as api_main


class StubWorkflow:
    def run(self, query: str, user_tier: int = 1, session_id: str | None = None):
        return {
            "query_id": "query-1",
            "session_id": session_id or "session-1",
            "synthesized_response": "ok",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "conversation_history": [],
        }


def _login(client: TestClient, username: str, password: str) -> dict:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def test_login_returns_access_and_refresh_tokens(monkeypatch):
    monkeypatch.setattr(api_main, "workflow", StubWorkflow())
    client = TestClient(api_main.app)

    response = client.post(
        "/login",
        json={"username": "researcher_user", "password": "researcher-pass"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "access_token" in payload
    assert "refresh_token" in payload
    assert payload["user"]["role"] == "researcher"
    assert payload["user"]["tier"] == 1


def test_refresh_and_logout_revoke_tokens(monkeypatch):
    monkeypatch.setattr(api_main, "workflow", StubWorkflow())
    client = TestClient(api_main.app)
    login_payload = _login(client, "gov_user", "government-pass")

    refresh_response = client.post(
        "/refresh",
        json={"refresh_token": login_payload["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed["access_token"] != login_payload["access_token"]

    logout_response = client.post(
        "/logout",
        json={"refresh_token": refreshed["refresh_token"]},
        headers={"Authorization": f"Bearer {refreshed['access_token']}"},
    )
    assert logout_response.status_code == 200

    denied_refresh = client.post(
        "/refresh",
        json={"refresh_token": refreshed["refresh_token"]},
    )
    assert denied_refresh.status_code == 401


def test_researchers_endpoint_applies_role_based_filtering(monkeypatch):
    monkeypatch.setattr(api_main, "workflow", StubWorkflow())

    sample_records = [
        {
            "researcher_id": "researcher-1",
            "name": "Dr. Owner",
            "institution_id": "iitgn",
            "state": "GJ",
            "research_area": "Robotics",
            "year_joined": 2020,
            "email": "owner@example.com",
            "phone": "9876543210",
            "orcid": "0000-0001",
        },
        {
            "researcher_id": "researcher-2",
            "name": "Dr. Public",
            "institution_id": "iisc",
            "state": "KA",
            "research_area": "AI",
            "year_joined": 2019,
            "email": "public@example.com",
            "phone": "9123456780",
            "orcid": "0000-0002",
        },
    ]

    class FakeDB:
        def __init__(self, *_args, **_kwargs):
            pass

        def query_researchers(self, state=None, research_area=None):
            return sample_records

    monkeypatch.setattr(api_main, "NRGDatabase", FakeDB)
    client = TestClient(api_main.app)

    researcher_tokens = _login(client, "researcher_user", "researcher-pass")
    researcher_response = client.get(
        "/researchers",
        headers={"Authorization": f"Bearer {researcher_tokens['access_token']}"},
    )
    assert researcher_response.status_code == 200
    researcher_payload = researcher_response.json()
    assert researcher_payload["role"] == "researcher"
    assert researcher_payload["results"][0]["email"] == "owner@example.com"
    assert researcher_payload["results"][1]["email"] is None

    government_tokens = _login(client, "gov_user", "government-pass")
    government_response = client.get(
        "/researchers",
        headers={"Authorization": f"Bearer {government_tokens['access_token']}"},
    )
    assert government_response.status_code == 200
    government_payload = government_response.json()
    assert government_payload["role"] == "government"
    assert government_payload["results"]["total_researchers"] == 2
    assert "email" not in government_payload["results"]["sample_records"][0]

    industry_tokens = _login(client, "industry_user", "industry-pass")
    industry_response = client.get(
        "/researchers",
        headers={"Authorization": f"Bearer {industry_tokens['access_token']}"},
    )
    assert industry_response.status_code == 200
    industry_payload = industry_response.json()
    assert industry_payload["role"] == "industry"
    assert industry_payload["results"][0]["licensed"] is True
    assert "email" not in industry_payload["results"][0]
