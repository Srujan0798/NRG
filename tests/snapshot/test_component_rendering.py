"""
Snapshot Tests: Component Rendering
Verify: AnswerPanel renders consistently
Use playwright-screenshot
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestComponentRendering:
    """Verify UI components render consistently."""

    def test_answer_panel_renders(self):
        """AnswerPanel should render without errors."""
        pytest.skip("Playwright snapshot tests require frontend running")

    def test_answer_panel_matches_snapshot(self):
        """AnswerPanel should match stored snapshot."""
        pytest.skip("Playwright snapshot tests require frontend running")

    def test_dashboard_cards_positioned_correctly(self):
        """Dashboard cards should be in correct positions."""
        pytest.skip("Playwright snapshot tests require frontend running")

    def test_researcher_list_renders(self):
        """Researcher list should render correctly."""
        pytest.skip("Playwright snapshot tests require frontend running")

    def test_query_input_renders(self):
        """Query input component should render."""
        pytest.skip("Playwright snapshot tests require frontend running")


class TestDashboardLayout:
    """Verify dashboard layout consistency."""

    def test_dashboard_cards_present(self):
        """All expected dashboard cards should be present."""
        pytest.skip("Playwright snapshot tests require frontend running")

    def test_dashboard_layout_not_broken(self):
        """Dashboard layout should not be visually broken."""
        pytest.skip("Playwright snapshot tests require frontend running")
