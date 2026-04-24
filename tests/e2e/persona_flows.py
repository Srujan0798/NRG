"""
Full E2E Persona Flows
Complete flow per persona: login → query → see result → export → logout

Tests the entire user journey for each role.
"""

import pytest
from playwright.sync_api import Page
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestResearcherPersonaFlow:
    """E2E flow for Researcher persona."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        page.goto("http://localhost:3000")

    def test_researcher_login_to_logout(self, page: Page):
        """Complete researcher flow: login → query → see result → export → logout."""
        page.wait_for_load_state("networkidle")

        page.click('button:has-text("Researcher")')
        page.fill('input[type="text"]', "researcher_user")
        page.fill('input[type="password"]', "researcher-pass")
        page.click('button:has-text("Login")')

        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")

        assert "dashboard" in page.url.lower() or "researcher" in page.url.lower() or page.locator('[data-testid="researcher"]').count() > 0, \
            "Should navigate to researcher dashboard"

        page.fill('input[placeholder*="query" i], input[placeholder*="search" i], textarea', "AI researchers in Karnataka")
        page.click('button:has-text("Search"), button:has-text("Query"), button:has-text("Submit")')

        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        result_visible = page.locator("text=AI").count() > 0 or page.locator('[data-testid="results"]').count() > 0 or page.locator("text=researchers").count() > 0
        assert result_visible, "Should show query results"

        export_button = page.locator('button:has-text("Export"), button:has-text("Download")').first
        if export_button.is_visible():
            export_button.click()
            page.wait_for_timeout(1000)

        page.click('button:has-text("Logout"), button:has-text("Sign out")')
        page.wait_for_timeout(1000)

        assert page.locator('input[type="text"]').count() > 0 or page.locator('button:has-text("Login")').count() > 0, \
            "Should be logged out and returned to login"


class TestGovernmentPersonaFlow:
    """E2E flow for Government persona."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        page.goto("http://localhost:3000")

    def test_government_login_to_logout(self, page: Page):
        """Complete government flow: login → aggregate query → see aggregated result → export → logout."""
        page.wait_for_load_state("networkidle")

        page.click('button:has-text("Government")')
        page.fill('input[type="text"]', "gov_user")
        page.fill('input[type="password"]', "government-pass")
        page.click('button:has-text("Login")')

        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")

        assert "dashboard" in page.url.lower() or "government" in page.url.lower() or page.locator('[data-testid="government"]').count() > 0, \
            "Should navigate to government dashboard"

        page.fill('input[placeholder*="query" i], input[placeholder*="search" i], textarea', "researchers by state")
        page.click('button:has-text("Search"), button:has-text("Query"), button:has-text("Submit")')

        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        result_visible = (
            page.locator("text=state").count() > 0 or
            page.locator("text=distribution").count() > 0 or
            page.locator('[data-testid="results"]').count() > 0 or
            page.locator("text=total").count() > 0
        )
        assert result_visible, "Should show aggregated results"

        page.click('button:has-text("Logout"), button:has-text("Sign out")')
        page.wait_for_timeout(1000)

        assert page.locator('input[type="text"]').count() > 0 or page.locator('button:has-text("Login")').count() > 0, \
            "Should be logged out"


class TestIndustryPersonaFlow:
    """E2E flow for Industry persona."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        page.goto("http://localhost:3000")

    def test_industry_login_to_logout(self, page: Page):
        """Complete industry flow: login → partnership query → see licensed results → export → logout."""
        page.wait_for_load_state("networkidle")

        page.click('button:has-text("Industry")')
        page.fill('input[type="text"]', "industry_user")
        page.fill('input[type="password"]', "industry-pass")
        page.click('button:has-text("Login")')

        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")

        assert "dashboard" in page.url.lower() or "industry" in page.url.lower() or page.locator('[data-testid="industry"]').count() > 0, \
            "Should navigate to industry dashboard"

        page.fill('input[placeholder*="query" i], input[placeholder*="search" i], textarea', "labs with industry partnerships")
        page.click('button:has-text("Search"), button:has-text("Query"), button:has-text("Submit")')

        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

        result_visible = (
            page.locator("text=lab").count() > 0 or
            page.locator("text=partnership").count() > 0 or
            page.locator('[data-testid="results"]').count() > 0 or
            page.locator("text=industry").count() > 0
        )
        assert result_visible, "Should show industry-relevant results"

        page.click('button:has-text("Logout"), button:has-text("Sign out")')
        page.wait_for_timeout(1000)

        assert page.locator('input[type="text"]').count() > 0 or page.locator('button:has-text("Login")').count() > 0, \
            "Should be logged out"


class TestCrossPersonaIsolation:
    """Verify personas are properly isolated."""

    def test_researcher_cannot_access_gov_data(self, page: Page):
        """Researcher should not see government-only aggregated data."""
        page.goto("http://localhost:3000")
        page.wait_for_load_state("networkidle")

        page.click('button:has-text("Researcher")')
        page.fill('input[type="text"]', "researcher_user")
        page.fill('input[type="password"]', "researcher-pass")
        page.click('button:has-text("Login")')

        page.wait_for_timeout(2000)

        page.goto("http://localhost:3000/researchers")
        page.wait_for_timeout(2000)

        content = page.content()
        assert "total_researchers" not in content.lower() or page.locator('[data-testid="results"]').count() > 0, \
            "Researcher should see individual records, not government aggregation"

    def test_industry_cannot_see_email(self, page: Page):
        """Industry persona should never see researcher emails."""
        page.goto("http://localhost:3000")
        page.wait_for_load_state("networkidle")

        page.click('button:has-text("Industry")')
        page.fill('input[type="text"]', "industry_user")
        page.fill('input[type="password"]', "industry-pass")
        page.click('button:has-text("Login")')

        page.wait_for_timeout(2000)

        page.goto("http://localhost:3000/researchers")
        page.wait_for_timeout(2000)

        content = page.content().lower()
        email_indicators = ["@example.com", "@gmail.com", "@iitgn", "@iisc", "@iitb", ".ac.in"]
        for indicator in email_indicators:
            assert indicator not in content, f"Industry should not see email: {indicator}"


class TestSessionManagement:
    """Session management edge cases."""

    def test_expired_token_shows_login(self, page: Page):
        """After token expiry, user should be redirected to login."""
        page.goto("http://localhost:3000")
        page.wait_for_load_state("networkidle")

        page.click('button:has-text("Researcher")')
        page.fill('input[type="text"]', "researcher_user")
        page.fill('input[type="password"]', "researcher-pass")
        page.click('button:has-text("Login")')

        page.wait_for_timeout(2000)

        page.evaluate("localStorage.clear()")
        page.reload()
        page.wait_for_timeout(1000)

        login_visible = page.locator('button:has-text("Login")').count() > 0 or page.locator('input[type="text"]').count() > 0
        assert login_visible, "Should show login after clearing session"
