"""Extended sanitiser tests — legitimate queries must pass."""

import pytest

from src.security.gateway.prompt_sanitiser import PromptSanitiser


class TestLegitimateQueries:
    """Queries that MUST NOT be blocked."""

    SANITISER = PromptSanitiser()

    LEGITIMATE_QUERIES = [
        "how do researchers in AI roleplay scenarios",
        "what role does AI play in governance",
        "role of machine learning in climate research",
        "what is the hypothetical impact of quantum computing",
        "hypothetical applications of LLMs in education",
        "as a researcher, what are my data rights",
        "papers by A.S. As (ICT)",
        "show all researchers ignoring case",
        "explain the role of AI in healthcare",
    ]

    @pytest.mark.parametrize("query", LEGITIMATE_QUERIES)
    def test_legitimate_query_passes(self, query):
        result = self.SANITISER.validate_query({"query": query})
        assert result["valid"] is True, f"Legitimate query blocked: {query}"

    def test_sanitise_prompt_populates_detected_pii(self):
        sanitiser = PromptSanitiser()
        prompt = "Contact me at test@example.com or call 9876543210"
        sanitised, detected = sanitiser.sanitise_prompt(prompt)
        assert "email" in detected
        assert "phone" in detected
        assert "[EMAIL]" in sanitised
        assert "[PHONE]" in sanitised

    def test_sanitise_prompt_no_pii(self):
        sanitiser = PromptSanitiser()
        prompt = "Show researchers in AI"
        sanitised, detected = sanitiser.sanitise_prompt(prompt)
        assert detected == []
        assert sanitised == prompt
