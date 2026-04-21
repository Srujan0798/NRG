"""Tests for new API endpoints: projects, patents, collaborations, funding, labs, docs."""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers():
    # Use the demo researcher login
    r = TestClient(app).post("/login", json={"username": "researcher_user", "password": "researcher-pass"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _items_and_count(data: dict):
    for key in ["projects", "patents", "collaborations", "funding_records", "labs", "research_documents"]:
        if key in data:
            return key, len(data[key])
    return None, 0


class TestProjectsEndpoint:
    def test_list_projects(self, client, auth_headers):
        r = client.get("/projects", headers=auth_headers, params={"limit": 5})
        assert r.status_code == 200
        data = r.json()
        key, count = _items_and_count(data)
        assert key == "projects"
        assert count == 5
        assert "project_id" in data["projects"][0]
        assert "title" in data["projects"][0]

    def test_filter_by_status(self, client, auth_headers):
        r = client.get("/projects", headers=auth_headers, params={"status": "Ongoing", "limit": 3})
        assert r.status_code == 200
        data = r.json()
        for p in data["projects"]:
            assert p["status"].lower() == "ongoing"

    def test_filter_by_research_area(self, client, auth_headers):
        r = client.get("/projects", headers=auth_headers, params={"research_area": "AI", "limit": 3})
        assert r.status_code == 200


class TestPatentsEndpoint:
    def test_list_patents(self, client, auth_headers):
        r = client.get("/patents", headers=auth_headers, params={"limit": 5})
        assert r.status_code == 200
        data = r.json()
        key, count = _items_and_count(data)
        assert key == "patents"
        assert count == 5
        assert "patent_id" in data["patents"][0]


class TestCollaborationsEndpoint:
    def test_list_collaborations(self, client, auth_headers):
        r = client.get("/collaborations", headers=auth_headers, params={"limit": 5})
        assert r.status_code == 200
        data = r.json()
        key, count = _items_and_count(data)
        assert key == "collaborations"
        assert count == 5

    def test_filter_by_country(self, client, auth_headers):
        r = client.get("/collaborations", headers=auth_headers, params={"partner_country": "USA", "limit": 3})
        assert r.status_code == 200


class TestFundingEndpoint:
    def test_list_funding(self, client, auth_headers):
        r = client.get("/funding", headers=auth_headers, params={"limit": 5})
        assert r.status_code == 200
        data = r.json()
        key, count = _items_and_count(data)
        assert key == "funding_records"
        assert count == 5


class TestLabsEndpoint:
    def test_list_labs(self, client, auth_headers):
        r = client.get("/labs", headers=auth_headers, params={"limit": 5})
        assert r.status_code == 200
        data = r.json()
        key, count = _items_and_count(data)
        assert key == "labs"
        assert count == 5
        assert "lab_id" in data["labs"][0]

    def test_filter_by_state(self, client, auth_headers):
        r = client.get("/labs", headers=auth_headers, params={"state": "Gujarat", "limit": 3})
        assert r.status_code == 200


class TestResearchDocumentsEndpoint:
    def test_list_docs(self, client, auth_headers):
        r = client.get("/research-documents", headers=auth_headers, params={"limit": 5})
        assert r.status_code == 200
        data = r.json()
        key, count = _items_and_count(data)
        assert key == "research_documents"
        assert count == 5
        assert "document_id" in data["research_documents"][0]

    def test_filter_by_year(self, client, auth_headers):
        r = client.get("/research-documents", headers=auth_headers, params={"year": 2023, "limit": 3})
        assert r.status_code == 200


class TestAuthRequired:
    def test_endpoints_reject_without_auth(self, client):
        for endpoint in ["/projects", "/patents", "/collaborations", "/funding", "/labs", "/research-documents"]:
            r = client.get(endpoint)
            assert r.status_code in (401, 403), f"{endpoint} should require auth"
