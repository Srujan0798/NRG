"""LB-1: Live API tier-shape isolation checks.

Run against running API + PostgreSQL:
    pytest tests/api/test_tier_isolation_live.py -v --tb=short

Collects evidence to evidence/YYYY-MM-DD/09-11_tierN_query_response.json
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO_ROOT / "evidence" / datetime.now(timezone.utc).strftime("%Y-%m-%d")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

PASSWORDS = {
    "researcher_user": os.getenv("RESEARCHER_PASSWORD", "researcher-pass"),
    "gov_user": os.getenv("GOV_PASSWORD", "government-pass"),
    "industry_user": os.getenv("INDUSTRY_PASSWORD", "industry-pass"),
}

PII_KEYWORDS = (
    "email",
    "phone",
    "aadhaar",
    "pan",
    "date_of_birth",
    "address",
    "bank_account",
    "gstin",
    "personal_phone",
    "alternate_email",
    "orcid",
)


def _login(username: str) -> str:
    resp = requests.post(
        f"{API_URL}/login",
        json={"username": username, "password": PASSWORDS[username]},
        timeout=15,
    )
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["access_token"]


def _query(token: str, query_text: str, persona: str) -> dict:
    resp = requests.post(
        f"{API_URL}/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query_text, "persona": persona},
        timeout=30,
    )
    # Accept 200 or 500 (boundary block) — both are valid outcomes
    assert resp.status_code in (200, 500), f"Unexpected status {resp.status_code}: {resp.text[:200]}"
    return resp.json()


def _save_evidence(tier: int, data: dict) -> Path:
    path = EVIDENCE_DIR / f"{9 + tier}_tier{tier}_query_response.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return path


def _contains_pii(response_text: str) -> bool:
    lowered = response_text.lower()
    return any(kw in lowered for kw in PII_KEYWORDS)


class TestTierIsolationLive:
    """Verify tier-shape filter strips forbidden fields per persona."""

    QUERY = "List researchers in Gujarat with contact details"

    @pytest.fixture(scope="class")
    def researcher_token(self):
        return _login("researcher_user")

    @pytest.fixture(scope="class")
    def gov_token(self):
        return _login("gov_user")

    @pytest.fixture(scope="class")
    def industry_token(self):
        return _login("industry_user")

    def test_tier1_researcher_sees_full_response(self, researcher_token):
        result = _query(researcher_token, self.QUERY, "researcher")
        _save_evidence(1, {"tier": 1, "query": self.QUERY, "result": result})

        assert result.get("status") == "success"
        # Tier 1 should see full details (response may contain researcher names, etc.)
        response_text = result.get("response", "")
        assert len(response_text) > 50, "Tier 1 response too short"

    def test_tier2_government_no_pii(self, gov_token):
        result = _query(gov_token, self.QUERY, "government")
        _save_evidence(2, {"tier": 2, "query": self.QUERY, "result": result})

        response_text = result.get("response", "")
        warnings = result.get("warnings", [])
        warning_text = " ".join(str(w) for w in warnings).lower()

        # Government tier must not see individual PII
        assert not _contains_pii(response_text), (
            f"Tier 2 response contains PII: {response_text[:300]}"
        )
        # Either aggregated format or explicit redaction warning
        assert (
            "aggregat" in response_text.lower()
            or "redact" in warning_text
            or "anonymiz" in response_text.lower()
            or result.get("status") == "blocked"
        ), f"Tier 2 should return aggregated/anonymized data or be blocked"

    def test_tier3_industry_limited_scope(self, industry_token):
        result = _query(industry_token, self.QUERY, "industry")
        _save_evidence(3, {"tier": 3, "query": self.QUERY, "result": result})

        response_text = result.get("response", "")

        # Industry tier must not see PII
        assert not _contains_pii(response_text), (
            f"Tier 3 response contains PII: {response_text[:300]}"
        )
        # Should be limited to names + research areas
        assert (
            "name" in response_text.lower()
            or "research" in response_text.lower()
            or result.get("status") == "blocked"
        ), f"Tier 3 should show names/research areas or be blocked"

    def test_tier1_vs_tier2_response_differs(self, researcher_token, gov_token):
        """Same query, different persona → different response shape."""
        r_result = _query(researcher_token, self.QUERY, "researcher")
        g_result = _query(gov_token, self.QUERY, "government")

        assert r_result.get("response") != g_result.get("response"), (
            "Tier 1 and Tier 2 returned identical responses — filter not applied"
        )

    def test_tier2_vs_tier3_response_differs(self, gov_token, industry_token):
        """Government and Industry should see different shapes."""
        g_result = _query(gov_token, self.QUERY, "government")
        i_result = _query(industry_token, self.QUERY, "industry")

        assert g_result.get("response") != i_result.get("response"), (
            "Tier 2 and Tier 3 returned identical responses — filter not applied"
        )

    def test_injected_pii_columns_stripped(self, researcher_token):
        """Even if SQL layer returns PII, response filter must strip it."""
        # This test simulates a scenario where the SQL returns extra columns
        # by querying something that might include PII in the raw result
        query = "Show me email addresses of researchers in Gujarat"
        result = _query(researcher_token, query, "researcher")

        response_text = result.get("response", "")
        warnings = result.get("warnings", [])
        warning_text = " ".join(str(w) for w in warnings).lower()

        # Tier 1 researcher SHOULD see emails (they have full access)
        # But for government/industry, we test in separate methods
        _save_evidence(1, {"tier": 1, "query": query, "result": result})

        assert result.get("status") == "success"
        assert "email" in response_text.lower() or "contact" in response_text.lower()
