"""Tests for sovereign egress guard."""

import pytest
from unittest.mock import patch, MagicMock
from src.security.egress.guard import (
    SovereignHTTPXClient,
    SovereigntyViolation,
    create_sovereign_client,
    SENSITIVE_FIELDS,
)


class TestSovereignHTTPXClient:
    def test_inspect_payload_blocks_sensitive_field_abstract(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation):
            client.inspect_payload({"abstract": "This is a research abstract about AI"})

    def test_inspect_payload_blocks_sensitive_field_full_text(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation):
            client.inspect_payload({"full_text": "Full publication content here"})

    def test_inspect_payload_blocks_sensitive_field_raw_content(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation):
            client.inspect_payload({"raw_content": "sensitive raw data"})

    def test_inspect_payload_blocks_nested_sensitive_field(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation):
            client.inspect_payload({"data": {"fulltext": "publication full text"}})

    def test_inspect_payload_allows_clean_payload(self):
        client = SovereignHTTPXClient()
        client.inspect_payload({"user_query": "Show me researchers in AI"})
        client.inspect_payload({"schema_prompt": "TABLE researchers(id, name)"})
        client.inspect_payload({"plan_json": "{}", "intent_label": "structured"})

    def test_inspect_payload_allows_allowlisted_fields(self):
        client = SovereignHTTPXClient()
        client.inspect_payload({
            "user_query": "test",
            "schema_prompt": "schema",
            "plan_json": "{}",
            "intent_label": "rag",
            "citation_ids": [1, 2, 3],
            "session_id": "abc",
            "user_tier": 1,
        })

    def test_inspect_payload_blocked_pattern(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation):
            client.inspect_payload({"publications.full_text": "leaked content"})

    def test_inspect_payload_disabled(self):
        client = SovereignHTTPXClient()
        client._enabled = False
        client.inspect_payload({"full_text": "should not raise when disabled"})

    def test_sovereignty_violation_attributes(self):
        exc = SovereigntyViolation("test reason", blocked_field="abstract")
        assert exc.reason == "test reason"
        assert exc.blocked_field == "abstract"
        assert "test reason" in str(exc)

    def test_create_sovereign_client(self):
        client = create_sovereign_client()
        assert isinstance(client, SovereignHTTPXClient)

    def test_post_blocks_sensitive_payload(self):
        mock_inner = MagicMock()
        client = SovereignHTTPXClient(inner=mock_inner)
        with pytest.raises(SovereigntyViolation):
            client.post("https://api.example.com", json={"abstract": "sensitive"})
        mock_inner.post.assert_not_called()

    def test_post_allows_clean_payload(self):
        mock_inner = MagicMock()
        mock_inner.post.return_value = MagicMock(status_code=200)
        client = SovereignHTTPXClient(inner=mock_inner)
        client.post("https://api.example.com", json={"user_query": "hello"})
        mock_inner.post.assert_called_once()
