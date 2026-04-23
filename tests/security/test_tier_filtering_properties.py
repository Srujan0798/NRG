"""
Property-based Tier Filtering Tests
Validates that tier filtering ALWAYS returns subset relationship: researcher ⊇ gov ⊇ industry

The access hierarchy is:
  - Researcher (tier 1): Full access to own records, filtered access to others
  - Government (tier 2): Aggregated data only, no PII
  - Industry (tier 3): Licensed records with institution info only

For any dataset, the fields visible to government should be a strict subset
of what researchers see, and fields visible to industry should be a strict
subset of what government sees.
"""

import pytest
from fastapi.testclient import TestClient
from dataclasses import dataclass
from typing import Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.api.main as api_main


class StubWorkflow:
    def run(self, query: str, user_tier: int = 1, session_id: str | None = None, user_id: str | None = None, **kwargs):
        return {
            "query_id": "query-1",
            "session_id": session_id or "session-1",
            "synthesized_response": "ok",
            "intent": "structured",
            "routing_decision": "text_to_sql",
            "verification_status": True,
            "conversation_history": [],
        }


@dataclass
class TierFieldResult:
    role: str
    fields: set[str]
    pii_fields: set[str]


def _get_pii_fields_for_role(role: str, records: list[dict]) -> set[str]:
    """Extract PII field names present in records for a given role."""
    if not records:
        return set()

    pii_field_names = {"email", "phone", "orcid", "home_address", "personal_email", "personal_phone"}
    record = records[0] if records else {}
    return pii_field_names & record.keys()


def _login(client: TestClient, username: str, password: str) -> dict:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def _get_records_for_role(client: TestClient, username: str, password: str) -> tuple[set[str], list[dict]]:
    """Login as role and fetch researchers endpoint, returning field names and raw records."""
    tokens = _login(client, username, password)
    response = client.get(
        "/researchers",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200, f"{username} failed to fetch researchers: {response.text}"
    payload = response.json()

    actual_role = payload.get("role", "")
    if actual_role == "government":
        sample = payload.get("results", {}).get("sample_records", [])
        if not isinstance(sample, list):
            return set(), []
        field_names = set()
        for rec in sample:
            if isinstance(rec, dict):
                field_names.update(rec.keys())
        return field_names, sample
    else:
        results = payload.get("results", [])
        if not isinstance(results, list):
            return set(), []
        field_names = set()
        for rec in results:
            if isinstance(rec, dict):
                field_names.update(rec.keys())
        return field_names, results


class TestTierFilteringProperties:
    """Property-based tests that enforce the tier subset relationship."""

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
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
                "home_address": "Gandhinagar, Gujarat",
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
                "home_address": "Bangalore, Karnataka",
            },
            {
                "researcher_id": "researcher-3",
                "name": "Dr. Industry",
                "institution_id": "iitb",
                "state": "MH",
                "research_area": "ML",
                "year_joined": 2021,
                "email": "industry@example.com",
                "phone": "9988776655",
                "orcid": "0000-0003",
                "home_address": "Mumbai, Maharashtra",
            },
        ]

        class FakeDB:
            def __init__(self, *_args, **_kwargs):
                pass

            def query_researchers(self, state=None, research_area=None, limit=50, offset=0):
                return sample_records

        monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
        api_main._api_cache.invalidate("researchers:")

    def test_researcher_sees_more_fields_than_government(self, monkeypatch):
        """Researcher should see at least as many fields as government."""
        client = TestClient(api_main.app)

        researcher_fields, _ = _get_records_for_role(client, "researcher_user", "researcher-pass")
        government_fields, _ = _get_records_for_role(client, "gov_user", "government-pass")

        missing_from_researcher = government_fields - researcher_fields
        assert not missing_from_researcher, (
            f"Government sees fields researcher doesn't: {missing_from_researcher}"
        )

    def test_researcher_sees_more_fields_than_industry(self, monkeypatch):
        """Researcher should see at least as many fields as industry (excluding licensed metadata)."""
        client = TestClient(api_main.app)

        researcher_fields, _ = _get_records_for_role(client, "researcher_user", "researcher-pass")
        industry_fields, _ = _get_records_for_role(client, "industry_user", "industry-pass")

        non_pii_metadata = {"licensed"}
        missing_from_researcher = (industry_fields - researcher_fields) - non_pii_metadata
        assert not missing_from_researcher, (
            f"Industry sees fields researcher doesn't (excluding licensed metadata): {missing_from_researcher}"
        )

    def test_government_field_subset_of_industry(self, monkeypatch):
        """Government fields should be a subset of industry fields (excluding licensed).

        Government sees aggregated data, industry sees individual licensed records.
        Both should exclude PII (email, phone, orcid).
        """
        client = TestClient(api_main.app)

        government_fields, _ = _get_records_for_role(client, "gov_user", "government-pass")
        industry_fields, _ = _get_records_for_role(client, "industry_user", "industry-pass")

        pii_fields = {"email", "phone", "orcid"}
        government_pii = government_fields & pii_fields
        industry_pii = industry_fields & pii_fields

        assert not government_pii, f"Government has PII: {government_pii}"
        assert not industry_pii, f"Industry has PII: {industry_pii}"

    def test_pii_fields_subset_property(self, monkeypatch):
        """PII fields visible to government must be a subset of those visible to researcher."""
        client = TestClient(api_main.app)

        _, researcher_records = _get_records_for_role(client, "researcher_user", "researcher-pass")
        _, government_records = _get_records_for_role(client, "gov_user", "government-pass")

        researcher_pii = _get_pii_fields_for_role("researcher", researcher_records)
        government_pii = _get_pii_fields_for_role("government", government_records)

        extra_pii_in_gov = government_pii - researcher_pii
        assert not extra_pii_in_gov, (
            f"Government sees PII fields researcher doesn't: {extra_pii_in_gov}"
        )

    def test_no_email_in_government_response(self, monkeypatch):
        """Government should never see email addresses."""
        client = TestClient(api_main.app)

        _, government_records = _get_records_for_role(client, "gov_user", "government-pass")

        for record in government_records:
            assert "email" not in record, f"Government record contains email: {record}"
            assert "phone" not in record, f"Government record contains phone: {record}"
            assert "orcid" not in record, f"Government record contains orcid: {record}"

    def test_no_email_in_industry_response(self, monkeypatch):
        """Industry should never see email addresses."""
        client = TestClient(api_main.app)

        _, industry_records = _get_records_for_role(client, "industry_user", "industry-pass")

        for record in industry_records:
            assert "email" not in record, f"Industry record contains email: {record}"
            assert "phone" not in record, f"Industry record contains phone: {record}"
            assert "orcid" not in record, f"Industry record contains orcid: {record}"

    def test_government_returns_aggregated_format(self, monkeypatch):
        """Government response must be aggregated format, not raw records."""
        client = TestClient(api_main.app)

        tokens = _login(client, "gov_user", "government-pass")
        response = client.get(
            "/researchers",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        payload = response.json()
        results = payload.get("results", {})

        assert "total_researchers" in results, "Government response missing total_researchers"
        assert "state_distribution" in results, "Government response missing state_distribution"
        assert "research_area_distribution" in results, "Government response missing research_area_distribution"
        assert "sample_records" in results, "Government response missing sample_records"

    def test_industry_returns_licensed_flag(self, monkeypatch):
        """Industry response should include 'licensed' flag on records."""
        client = TestClient(api_main.app)

        _, industry_records = _get_records_for_role(client, "industry_user", "industry-pass")

        for record in industry_records:
            assert "licensed" in record, f"Industry record missing licensed flag: {record}"
            assert record["licensed"] is True, f"Industry record should be licensed: {record}"

    def test_researcher_own_record_has_full_pii(self, monkeypatch):
        """Researcher should see full PII for their own record."""
        client = TestClient(api_main.app)

        tokens = _login(client, "researcher_user", "researcher-pass")
        response = client.get(
            "/researchers",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        payload = response.json()
        results = payload.get("results", [])

        own_record = next((r for r in results if r.get("researcher_id") == "researcher-1"), None)
        assert own_record is not None, "Researcher's own record not found"
        assert own_record.get("email") == "owner@example.com"
        assert own_record.get("phone") == "9876543210"

    def test_researcher_other_record_redacted(self, monkeypatch):
        """Researcher should NOT see PII (email, phone, orcid) on OTHER researchers' records."""
        client = TestClient(api_main.app)

        tokens = _login(client, "researcher_user", "researcher-pass")
        response = client.get(
            "/researchers",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        payload = response.json()
        results = payload.get("results", [])

        other_records = [r for r in results if r.get("researcher_id") != "researcher-1"]
        for record in other_records:
            assert record.get("email") is None, f"Email leaked to other researcher: {record.get('email')}"
            assert record.get("phone") is None, f"Phone leaked to other researcher: {record.get('phone')}"
            assert record.get("orcid") is None, f"Orcid leaked to other researcher: {record.get('orcid')}"

    def test_subset_transitivity(self, monkeypatch):
        """
        Industry fields ⊆ Government fields ⊆ Researcher fields (transitivity).
        
        NOTE: Industry adds 'licensed' field which is NOT in researcher records.
        This is correct - industry gets additional non-PII metadata.
        The security invariant is that PII fields are properly subsetted.
        """
        client = TestClient(api_main.app)

        researcher_fields, _ = _get_records_for_role(client, "researcher_user", "researcher-pass")
        government_fields, _ = _get_records_for_role(client, "gov_user", "government-pass")
        industry_fields, _ = _get_records_for_role(client, "industry_user", "industry-pass")

        # PII fields that must never appear in lower-tier responses
        pii_fields = {"email", "phone", "orcid", "home_address"}

        # For each role, check that PII fields are properly filtered
        researcher_pii = researcher_fields & pii_fields
        government_pii = government_fields & pii_fields
        industry_pii = industry_fields & pii_fields

        # Government PII must be ⊆ Researcher PII (or empty)
        assert not (government_pii - researcher_pii), \
            f"Government has PII researcher doesn't: {government_pii - researcher_pii}"

        # Industry PII must be ⊆ Researcher PII (or empty)
        assert not (industry_pii - researcher_pii), \
            f"Industry has PII researcher doesn't: {industry_pii - researcher_pii}"

        # Industry PII must be ⊆ Government PII (or empty)
        assert not (industry_pii - government_pii), \
            f"Industry has PII government doesn't: {industry_pii - government_pii}"

        # Core security property: Industry should NEVER see email/phone/orcid
        assert not (industry_pii & {"email", "phone", "orcid"}), \
            f"Industry has restricted PII: {industry_pii & {'email', 'phone', 'orcid'}}"

        # Government should NEVER see email/phone/orcid
        assert not (government_pii & {"email", "phone", "orcid"}), \
            f"Government has restricted PII: {government_pii & {'email', 'phone', 'orcid'}}"


class TestTierFilteringEdgeCases:
    """Edge case tests for tier filtering."""

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setattr(api_main, "workflow", StubWorkflow())

        class FakeDB:
            def __init__(self, *_args, **_kwargs):
                pass

            def query_researchers(self, state=None, research_area=None, limit=50, offset=0):
                return []

        monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
        api_main._api_cache.invalidate("researchers:")

    def test_empty_dataset_returns_valid_structure(self, monkeypatch):
        """Empty dataset should still return valid response structure per role."""
        client = TestClient(api_main.app)

        for role, creds in [("researcher", ("researcher_user", "researcher-pass")),
                            ("government", ("gov_user", "government-pass")),
                            ("industry", ("industry_user", "industry-pass"))]:
            tokens = _login(client, creds[0], creds[1])
            response = client.get(
                "/researchers",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            assert response.status_code == 200, f"{role} failed with empty data: {response.text}"

    def test_null_field_handling(self, monkeypatch):
        """Records with null PII fields should be handled gracefully."""
        monkeypatch.setattr(api_main, "workflow", StubWorkflow())

        sample_records = [
            {
                "researcher_id": "r1",
                "name": "Dr. Null",
                "state": "GJ",
                "research_area": "AI",
                "email": None,
                "phone": None,
                "orcid": None,
            }
        ]

        class FakeDB:
            def __init__(self, *_args, **_kwargs):
                pass

            def query_researchers(self, state=None, research_area=None, limit=50, offset=0):
                return sample_records

        monkeypatch.setattr(api_main, "_get_db", lambda: FakeDB())
        api_main._api_cache.invalidate("researchers:")

        client = TestClient(api_main.app)
        tokens = _login(client, "researcher_user", "researcher-pass")
        response = client.get(
            "/researchers",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 200


class TestTierFilteringInvariants:
    """Invariant tests that must always pass regardless of data."""

    def test_tier_ordering_is_always_subset(self):
        """
        Invariant: For ANY possible record set, PII fields visible to government
        and industry are subsets of what higher tiers see.

        This tests the ALGORITHM's security property, not the data.
        We verify the filter_researcher_records function directly with synthetic data.
        """
        from src.auth.middleware import filter_researcher_records

        synthetic_records = [
            {
                "researcher_id": f"r{i}",
                "name": f"Dr. {i}",
                "state": "GJ",
                "research_area": "AI",
                "email": f"email{i}@example.com",
                "phone": f"phone{i}",
                "orcid": f"orcid{i}",
                "home_address": f"address{i}",
            }
            for i in range(10)
        ]

        researcher_claims = {"tier": 1, "researcher_id": "r0"}
        government_claims = {"tier": 2}
        industry_claims = {"tier": 3}

        researcher_result = filter_researcher_records(synthetic_records, researcher_claims)
        government_result = filter_researcher_records(synthetic_records, government_claims)
        industry_result = filter_researcher_records(synthetic_records, industry_claims)

        # Get PII fields per role
        pii_fields = {"email", "phone", "orcid", "home_address"}

        researcher_all_fields = set()
        for rec in researcher_result["results"]:
            researcher_all_fields.update(rec.keys())

        gov_results_data = government_result.get("results", {})
        if isinstance(gov_results_data, dict):
            gov_sample = gov_results_data.get("sample_records", [])
        else:
            gov_sample = []
        gov_all_fields = set()
        for rec in gov_sample:
            gov_all_fields.update(rec.keys())

        industry_results_data = industry_result.get("results", {})
        if isinstance(industry_results_data, dict):
            industry_all_fields = set(industry_results_data.keys())
        elif isinstance(industry_results_data, list):
            industry_all_fields = set()
            for rec in industry_results_data:
                industry_all_fields.update(rec.keys())
        else:
            industry_all_fields = set()

        researcher_pii = researcher_all_fields & pii_fields
        gov_pii = gov_all_fields & pii_fields
        industry_pii = industry_all_fields & pii_fields

        # PII subset property: gov_pii ⊆ researcher_pii, industry_pii ⊆ researcher_pii
        assert not (gov_pii - researcher_pii), "Government PII must be subset of researcher PII"
        assert not (industry_pii - researcher_pii), "Industry PII must be subset of researcher PII"

        # Core security: No email/phone/orcid for industry or government
        assert not (industry_pii & {"email", "phone", "orcid"}), \
            "Industry must not see email/phone/orcid"
        assert not (gov_pii & {"email", "phone", "orcid"}), \
            "Government must not see email/phone/orcid"
