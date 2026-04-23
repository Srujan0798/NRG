"""
Pytest Configuration for NRG Evaluation Tests

Fixtures and markers for SQL accuracy, quality gates, and eval harness tests.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class MockLLMClient:
    """Mock LLM that returns SQL based on pattern matching for eval."""

    def __init__(self):
        self.model = "mock-eval"

    def chat(self, messages: list) -> MagicMock:
        content = messages[-1]["content"] if messages else ""
        response = self._generate_sql_response(content)
        mock = MagicMock()
        mock.content = response
        return mock

    def _generate_sql_response(self, content: str) -> str:
        content_lower = content.lower()

        if "top 5" in content_lower and "agency" in content_lower:
            return "SELECT agency, SUM(amount) as total FROM funding_records GROUP BY agency ORDER BY total DESC LIMIT 5;"
        if "yoy" in content_lower or "year-over-year" in content_lower or "growth" in content_lower:
            return """WITH YearlyData AS (
    SELECT SUBSTR(fiscal_year, -4) as year, SUM(amount) as total
    FROM funding_records GROUP BY year
)
SELECT curr.year, curr.total as current_amount, prev.year as prev_year, prev.total as prev_amount,
ROUND(((curr.total - prev.total) * 100.0 / NULLIF(prev.total, 0)), 2) as yoy_growth
FROM YearlyData curr LEFT JOIN YearlyData prev ON CAST(prev.year AS INTEGER) = CAST(curr.year AS INTEGER) - 1
ORDER BY curr.year DESC;"""
        if "iit madras" in content_lower and ("phd" in content_lower or "ug" in content_lower or "undergraduate" in content_lower):
            return "SELECT institution_id, COUNT(*) as count FROM researchers WHERE institution_id LIKE '%IIT Madras%' GROUP BY institution_id;"
        if "top" in content_lower and "researcher" in content_lower:
            return "SELECT name, h_index, institution_id FROM researchers ORDER BY h_index DESC LIMIT 20;"
        if "cost per patent" in content_lower or "grant per patent" in content_lower:
            return """WITH GrantCTE AS (SELECT institution_id, SUM(amount) as total_grant FROM funding_records GROUP BY institution_id),
PatentCTE AS (SELECT applicant_institution, COUNT(*) as cnt FROM patents WHERE status='Granted' GROUP BY applicant_institution)
SELECT g.institution_id, g.total_grant, COALESCE(p.cnt, 0) as patents, ROUND(g.total_grant / NULLIF(p.cnt, 0), 2) as cost_per_patent
FROM GrantCTE g LEFT JOIN PatentCTE p ON g.institution_id = p.applicant_institution ORDER BY cost_per_patent ASC;"""
        if "trends" in content_lower or "over time" in content_lower or "fiscal year" in content_lower:
            return "SELECT SUBSTR(fiscal_year, -4) as year, COUNT(*) as records, SUM(amount) as total FROM funding_records GROUP BY year ORDER BY year DESC;"
        if "iit madras" in content_lower and ("innovation" in content_lower or "funding" in content_lower or "grant" in content_lower):
            return "SELECT fiscal_year, SUM(amount) as total FROM funding_records WHERE institution_id LIKE '%IIT Madras%' GROUP BY fiscal_year ORDER BY fiscal_year DESC;"
        if "correlation" in content_lower or "vs" in content_lower:
            return """WITH FundingCTE AS (SELECT institution_id, SUM(amount) as total FROM funding_records GROUP BY institution_id),
PubCTE AS (SELECT affiliation, COUNT(*) as cnt FROM research_documents GROUP BY affiliation)
SELECT f.institution_id, f.total, COALESCE(p.cnt, 0) as publications FROM FundingCTE f LEFT JOIN PubCTE p ON f.institution_id = p.affiliation ORDER BY f.total DESC LIMIT 20;"""
        if "pg course" in content_lower or "postgraduate" in content_lower:
            return "SELECT COUNT(*) as count FROM publications WHERE researcher_ids LIKE '%IIT Madras%' AND year >= 2020;"
        if "phd course" in content_lower or "doctoral" in content_lower:
            return "SELECT institution_id, COUNT(*) as count FROM researchers WHERE institution_id LIKE '%IIT%' GROUP BY institution_id ORDER BY count DESC;"
        if "high" in content_lower and ("grant" in content_lower or "funding" in content_lower):
            return """WITH FundingCTE AS (SELECT institution_id, SUM(amount) as total FROM funding_records GROUP BY institution_id)
SELECT f.institution_id, f.total FROM FundingCTE f ORDER BY f.total DESC LIMIT 20;"""
        if "institution" in content_lower and ("most" in content_lower or "phd" in content_lower):
            return "SELECT institution_id, COUNT(*) as count FROM researchers GROUP BY institution_id ORDER BY count DESC LIMIT 10;"

        return "SELECT * FROM funding_records LIMIT 100;"


class MockLLMMesh:
    """Mock SovereignLLMMesh for testing."""

    def __init__(self):
        self.provider = "mock-mesh"
        self.model = "mock-model"

    def generate(self, system_prompt: str, user_prompt: str, conversation_history: list = None):
        return MockLLMClient().chat([{"content": system_prompt + "\n" + user_prompt}]).content

    def generate_streaming(self, system_prompt: str, user_prompt: str, conversation_history: list = None):
        response = self.generate(system_prompt, user_prompt, conversation_history)
        for char in response:
            yield char


@pytest.fixture(autouse=False)
def mock_llm_client(monkeypatch):
    """Fixture that mocks LLM client and mesh for all eval tests."""
    mock = MockLLMClient()
    mock_mesh = MockLLMMesh()

    import src.config.llm_config as llm_module
    import src.config.local_llm as local_llm_module
    import src.orchestration.nodes.synthesizer as synth_module

    monkeypatch.setattr(llm_module, "get_llm_client", lambda provider=None: mock)
    monkeypatch.setattr(llm_module, "get_llm_mesh", lambda: mock_mesh)
    monkeypatch.setattr(synth_module, "get_llm_mesh", lambda: mock_mesh)
    monkeypatch.setattr(local_llm_module, "get_local_llm_client", lambda provider=None: mock)

    return mock


@pytest.fixture(autouse=False)
def mock_llm_mesh(monkeypatch):
    """Fixture that mocks SovereignLLMMesh."""
    mock_mesh = MockLLMMesh()
    import src.config.llm_config as llm_module
    import src.orchestration.nodes.synthesizer as synth_module

    monkeypatch.setattr(llm_module, "get_llm_mesh", lambda: mock_mesh)
    monkeypatch.setattr(synth_module, "get_llm_mesh", lambda: mock_mesh)

    return mock_mesh