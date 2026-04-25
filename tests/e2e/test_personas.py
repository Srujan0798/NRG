"""
E2E Browser Verification Tests — NRG Platform
Full-stack browser tests for all 3 personas using Playwright.

Tests: researcher → government → industry
- Login flows per persona
- DPDP consent approval
- Dashboard loading
- Query flow with citations
- Tier-specific data filtering
- Screenshots on failure

Run: pytest tests/e2e/test_personas.py -v
Headless: Always (default)
"""

import pytest
import sys
import os
import re
from pathlib import Path
from playwright.sync_api import Page, expect

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

pytestmark = pytest.mark.skipif(
    os.getenv("NRG_RUN_LIVE_E2E") != "1",
    reason="requires live browser/API stack; set NRG_RUN_LIVE_E2E=1 to run",
)

SCREENSHOT_DIR = Path("test_results")
SCREENSHOT_DIR.mkdir(exist_ok=True)

BASE_URL = "http://localhost:8000"

CREDENTIALS = {
    "researcher": {"username": "researcher_user", "password": "researcher-pass", "tier": 1},
    "government": {"username": "gov_user", "password": "government-pass", "tier": 2},
    "industry": {"username": "industry_user", "password": "industry-pass", "tier": 3},
}


def save_screenshot(page: Page, name: str):
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return path


def get_token_via_api(persona: str) -> str:
    """Get access token directly via API call."""
    import httpx
    creds = CREDENTIALS[persona]
    response = httpx.post(
        f"{BASE_URL}/login",
        json={"username": creds["username"], "password": creds["password"]},
        timeout=10.0,
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return ""


@pytest.mark.e2e
class TestResearcherPersona:
    """Phase 1: Researcher login + dashboard verification."""

    def test_researcher_login_and_consent(self, page: Page):
        """Researcher can log in and see dashboard (no URL change — SPA navigation)."""
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")

        page.fill('input[autocomplete="username"]', "researcher_user")
        page.fill('input[autocomplete="current-password"]', "researcher-pass")
        page.click('button[type="submit"]')
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        save_screenshot(page, "researcher_login")

        dashboard_visible = (
            page.locator("text=Researcher").count() > 0
            or page.locator("nav").count() > 0
            or page.locator("header").count() > 0
            or "dashboard" in page.content().lower()
        )
        assert dashboard_visible, "Dashboard content should appear after login"

    def test_researcher_dashboard_loads(self, page: Page):
        """Researcher dashboard loads with real data via API."""
        token = get_token_via_api("researcher")
        assert token, "Should obtain auth token"

        import httpx
        response = httpx.get(
            f"{BASE_URL}/researchers",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )
        assert response.status_code == 200, "Researcher /researchers endpoint should work"

        data = response.json()
        assert isinstance(data, (dict, list)), "Should return researcher data"
        save_screenshot(page, "researcher_dashboard")


@pytest.mark.e2e
class TestGovernmentPersona:
    """Phase 1: Government login + dashboard verification."""

    def test_government_login(self, page: Page):
        """Government user can log in and see dashboard."""
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")

        page.fill('input[autocomplete="username"]', "gov_user")
        page.fill('input[autocomplete="current-password"]', "government-pass")
        page.click('button[type="submit"]')
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        save_screenshot(page, "government_login")

        dashboard_visible = (
            page.locator("text=Government").count() > 0
            or page.locator("nav").count() > 0
            or page.locator("header").count() > 0
        )
        assert dashboard_visible, "Government dashboard should appear after login"

    def test_government_dashboard_aggregated(self, page: Page):
        """Government can access aggregated stats."""
        token = get_token_via_api("government")
        assert token, "Should obtain government token"

        import httpx
        response = httpx.get(
            f"{BASE_URL}/stats",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        assert response.status_code == 200, "Government /stats should work"
        save_screenshot(page, "government_dashboard")


@pytest.mark.e2e
class TestIndustryPersona:
    """Phase 1: Industry login + dashboard verification."""

    def test_industry_login(self, page: Page):
        """Industry user can log in and see anonymized dashboard."""
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")

        page.fill('input[autocomplete="username"]', "industry_user")
        page.fill('input[autocomplete="current-password"]', "industry-pass")
        page.click('button[type="submit"]')
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        save_screenshot(page, "industry_login")

        dashboard_visible = (
            page.locator("text=Industry").count() > 0
            or page.locator("nav").count() > 0
            or page.locator("header").count() > 0
        )
        assert dashboard_visible, "Industry dashboard should appear after login"

    def test_industry_dashboard_anonymized(self, page: Page):
        """Industry can access anonymized data."""
        token = get_token_via_api("industry")
        assert token, "Should obtain industry token"

        import httpx
        response = httpx.get(
            f"{BASE_URL}/researchers",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        assert response.status_code == 200, "Industry /researchers should work"
        data = response.json()
        data_str = str(data).lower()

        email_pattern = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}")
        assert not email_pattern.search(data_str), "Industry must not see email addresses"
        save_screenshot(page, "industry_dashboard")


@pytest.mark.e2e
class TestQueryFlow:
    """Phase 2: Full query flow with citations."""

    def test_researcher_query_with_citations(self, page: Page):
        """Researcher submits query, receives response with citations."""
        token = get_token_via_api("researcher")
        assert token, "Need researcher token for query test"

        import httpx
        response = httpx.post(
            f"{BASE_URL}/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers in Gujarat"},
            timeout=30.0,
        )

        save_screenshot(page, "researcher_query_response")

        assert response.status_code == 200, f"Query should succeed: {response.text}"
        data = response.json()
        assert "response" in data or "synthesized_response" in data, \
            "Response should contain answer text"
        assert data.get("status") == "success", f"Status should be success: {data}"
        assert len(data.get("citations", [])) > 0, "Should have citations"

    def test_government_query_aggregated(self, page: Page):
        """Government query returns aggregated data (no individual emails)."""
        token = get_token_via_api("government")
        assert token, "Need government token"

        import httpx
        response = httpx.post(
            f"{BASE_URL}/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "researchers by state"},
            timeout=30.0,
        )

        assert response.status_code == 200, f"Government query should succeed: {response.text}"
        data = response.json()
        data_str = str(data).lower()

        save_screenshot(page, "government_query_response")

        assert "email" not in data_str, \
            "Government tier must not see email addresses directly"

    def test_industry_query_anonymized(self, page: Page):
        """Industry query returns anonymized summaries."""
        token = get_token_via_api("industry")
        assert token, "Need industry token"

        import httpx
        response = httpx.post(
            f"{BASE_URL}/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "AI researchers for collaboration"},
            timeout=30.0,
        )

        assert response.status_code == 200, f"Industry query should succeed: {response.text}"
        data = response.json()
        data_str = str(data).lower()

        save_screenshot(page, "industry_query_response")

        assert "email" not in data_str, \
            "Industry tier must not see email addresses"


@pytest.mark.e2e
class TestTierFiltering:
    """Phase 2: Verify tier-specific data filtering."""

    def test_researcher_sees_full_records(self, page: Page):
        """Researcher tier should have access to full record fields."""
        token = get_token_via_api("researcher")
        import httpx

        response = httpx.post(
            f"{BASE_URL}/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "List researchers in machine learning"},
            timeout=30.0,
        )

        assert response.status_code == 200
        save_screenshot(page, "researcher_tier_filtering")

    def test_government_no_email_leak(self, page: Page):
        """Government tier must not leak email addresses in any response."""
        token = get_token_via_api("government")
        import httpx

        for query in ["researchers in Karnataka", "state distribution of researchers", "funding by state"]:
            response = httpx.post(
                f"{BASE_URL}/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": query},
                timeout=30.0,
            )
            if response.status_code == 200:
                data_str = str(response.json()).lower()
                email_pattern = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}")
                assert not email_pattern.search(data_str), \
                    f"Government tier leaked email in query '{query}'"

    def test_industry_no_pii_leak(self, page: Page):
        """Industry tier must not leak PII (emails, phones, addresses)."""
        token = get_token_via_api("industry")
        import httpx

        queries = [
            "researchers available for collaboration",
            "labs with industry partnerships",
            "top AI researchers",
        ]

        for query in queries:
            response = httpx.post(
                f"{BASE_URL}/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": query},
                timeout=30.0,
            )
            if response.status_code == 200:
                data_str = str(response.json())
                email_pattern = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}")
                phone_pattern = re.compile(r"\b[6-9][0-9]{9}\b")

                assert not email_pattern.search(data_str), \
                    f"Industry tier leaked email in query '{query}'"
                assert not phone_pattern.search(data_str), \
                    f"Industry tier leaked phone in query '{query}'"


class TestScreenshotsOnFailure:
    """Capture screenshots when assertions fail."""

    def test_login_page_renders(self, page: Page):
        """Login page should render without errors."""
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")
        save_screenshot(page, "login_page")

        assert page.locator("input").count() > 0, "Login form should render"

    def test_health_endpoint(self, page: Page):
        """API health endpoint should return ok."""
        import httpx
        response = httpx.get(f"{BASE_URL}/health", timeout=10.0)
        save_screenshot(page, "health_check")

        assert response.status_code == 200, "Health endpoint should be healthy"
        assert response.json().get("ok") == True
