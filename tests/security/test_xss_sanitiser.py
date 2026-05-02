"""XSS payload regression tests for the query prompt sanitiser."""

import pytest

from src.security.gateway.prompt_sanitiser import PromptSanitiser


@pytest.mark.parametrize(
    ("payload", "expected_rule"),
    [
        ("<script>alert(1)</script>", "xss_script_tag"),
        ("javascript:alert(1)", "xss_javascript_uri"),
        ("<svg/onload=alert(1)>", "xss_event_handler"),
        ("<iframe src=javascript:alert(1)>", "xss_javascript_uri"),
    ],
)
def test_xss_vectors_are_blocked(payload, expected_rule):
    result = PromptSanitiser().validate_query({"query": payload})

    assert result["valid"] is False
    assert result["reason"] == "PROMPT_INJECTION"
    assert expected_rule in result["details"]
