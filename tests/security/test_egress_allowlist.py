"""Tests for egress allowlist - Protocol #39: Schema Allowlist.

Tests the YAML-based allowlist integration with SovereignHTTPXClient
and the EgressSchemaAllowlist loader.
"""

import os
from pathlib import Path

import pytest
from src.security.egress.guard import SovereignHTTPXClient, SovereigntyViolation
from src.security.egress.schema_allowlist_loader import EgressSchemaAllowlist, get_allowlist


class TestEgressSchemaAllowlistLoader:
    """Unit tests for EgressSchemaAllowlist loader."""

    def test_is_table_allowed_valid(self):
        allowlist = get_allowlist()
        assert allowlist.is_table_allowed("researchers")
        assert allowlist.is_table_allowed("publications")
        assert allowlist.is_table_allowed("institutions")

    def test_is_table_allowed_invalid(self):
        allowlist = get_allowlist()
        assert not allowlist.is_table_allowed("secret_table")
        assert not allowlist.is_table_allowed("users")
        assert not allowlist.is_table_allowed("passwords")

    def test_is_column_allowed_valid(self):
        allowlist = get_allowlist()
        assert allowlist.is_column_allowed("researchers", "name")
        assert allowlist.is_column_allowed("researchers", "researcher_id")
        assert allowlist.is_column_allowed("publications", "title")

    def test_is_column_allowed_blocked(self):
        allowlist = get_allowlist()
        assert not allowlist.is_column_allowed("researchers", "email")
        assert not allowlist.is_column_allowed("researchers", "phone")
        assert not allowlist.is_column_allowed("publications", "full_text")

    def test_get_blocked_content_returns_frozenset(self):
        allowlist = get_allowlist()
        blocked = allowlist.get_blocked_content()
        assert isinstance(blocked, frozenset)
        assert "full_text" in blocked
        assert "abstract" in blocked
        assert "raw_content" in blocked

    def test_is_llm_prompt_allowed(self):
        allowlist = get_allowlist()
        assert allowlist.is_llm_prompt_allowed("user_query")
        assert allowlist.is_llm_prompt_allowed("schema_prompt")
        assert allowlist.is_llm_prompt_allowed("plan_json")
        assert not allowlist.is_llm_prompt_allowed("password")

    def test_get_allowed_tables(self):
        allowlist = get_allowlist()
        tables = allowlist.get_allowed_tables()
        assert "researchers" in tables
        assert "publications" in tables
        assert "institutions" in tables

    def test_get_table_columns(self):
        allowlist = get_allowlist()
        allowed, blocked = allowlist.get_table_columns("researchers")
        assert "name" in allowed
        assert "email" in blocked


class TestSovereignHTTPXClientAllowed:
    """Allowed content tests - should NOT raise."""

    def test_allowed_user_query(self):
        client = SovereignHTTPXClient()
        client.inspect_payload({"user_query": "Show me researchers in AI"})

    def test_allowed_schema_prompt_valid_table(self):
        client = SovereignHTTPXClient()
        client.inspect_payload({
            "schema_prompt": "SELECT researcher_id, name, institution_id FROM researchers",
            "user_query": "List researchers"
        })

    def test_allowed_plan_json(self):
        client = SovereignHTTPXClient()
        client.inspect_payload({"plan_json": '{"subqueries": ["q1"]}'})

    def test_allowed_citation_ids(self):
        client = SovereignHTTPXClient()
        client.inspect_payload({"citation_ids": [1, 2, 3]})

    def test_allowed_session_id(self):
        client = SovereignHTTPXClient()
        client.inspect_payload({"session_id": "abc123"})


class TestSovereignHTTPXClientBlockedTables:
    """Blocked table tests - should raise SovereigntyViolation."""

    def test_blocked_unlisted_table_in_schema_prompt(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="Unlisted table"):
            client.inspect_payload({
                "schema_prompt": "SELECT * FROM secret_researchers",
                "user_query": "test"
            })

    def test_blocked_unlisted_table_join(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="Unlisted table"):
            client.inspect_payload({
                "schema_prompt": "SELECT * FROM researchers JOIN secret_data ON researchers.id = secret_data.id",
                "user_query": "test"
            })

    def test_blocked_user_credentials_table(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="Unlisted table"):
            client.inspect_payload({
                "schema_prompt": "SELECT * FROM user_credentials",
                "user_query": "test"
            })

    def test_blocked_passwords_table(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="Unlisted table"):
            client.inspect_payload({
                "schema_prompt": "SELECT username, password FROM passwords",
                "user_query": "test"
            })

    def test_blocked_private_notes_table(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="Unlisted table"):
            client.inspect_payload({
                "schema_prompt": "SELECT * FROM private_notes WHERE researcher_id = 1",
                "user_query": "test"
            })


class TestSovereignHTTPXClientBlockedColumns:
    """Blocked column tests - should raise SovereigntyViolation."""

    def test_blocked_email_column(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="email"):
            client.inspect_payload({
                "user_query": "test",
                "email": "researcher@example.com"
            })

    def test_blocked_phone_column(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="phone"):
            client.inspect_payload({
                "user_query": "test",
                "phone": "+1234567890"
            })

    def test_blocked_full_text_field(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="full_text"):
            client.inspect_payload({
                "user_query": "test",
                "full_text": "secret research content..."
            })

    def test_blocked_fulltext_nested(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="fulltext"):
            client.inspect_payload({
                "data": {"fulltext": "publication content here"}
            })

    def test_blocked_researcher_table_column_in_schema(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="email"):
            client.inspect_payload({
                "schema_prompt": "SELECT researcher_id, email FROM researchers",
                "user_query": "test"
            })


class TestSovereignHTTPXClientBlockedPatterns:
    """Blocked content pattern tests - should raise SovereigntyViolation."""

    def test_blocked_raw_content_field(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="raw_content"):
            client.inspect_payload({
                "user_query": "test",
                "raw_content": "sensitive raw data"
            })

    def test_blocked_raw_db_dump(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="raw_db_dump"):
            client.inspect_payload({
                "user_query": "test",
                "raw_db_dump": "full database dump here"
            })

    def test_blocked_publication_text(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="publication_text"):
            client.inspect_payload({
                "user_query": "test",
                "publication_text": "full publication text"
            })

    def test_blocked_research_content(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="research_content"):
            client.inspect_payload({
                "user_query": "test",
                "research_content": "unpublished research data"
            })

    def test_blocked_full_publication_record(self):
        client = SovereignHTTPXClient()
        with pytest.raises(SovereigntyViolation, match="full_publication_record"):
            client.inspect_payload({
                "user_query": "test",
                "full_publication_record": "complete record with all fields"
            })


class TestYAMLHotReload:
    """YAML hot-reload tests."""

    def test_reload_on_mtime_change(self):
        loader = EgressSchemaAllowlist()
        loader._cache = {}
        loader._mtime = 0

        original_data = loader._load()
        assert original_data is not None

        temp_path = Path(__file__).resolve().parents[2] / "src" / "security" / "egress_allowlist.yaml"
        original_mtime = os.path.getmtime(temp_path)

        loader._cache = {}
        loader._mtime = original_mtime - 100
        reloaded = loader._load()
        assert reloaded is not None
        assert "tables" in reloaded

    def test_singleton_same_instance(self):
        instance1 = EgressSchemaAllowlist()
        instance2 = EgressSchemaAllowlist()
        assert instance1 is instance2


class TestFalsePositives:
    """False positive tests - legitimate queries should NOT be blocked."""

    def test_researcher_name_not_blocked(self):
        client = SovereignHTTPXClient()
        client.inspect_payload({
            "user_query": "Find researchers named John",
            "schema_prompt": "SELECT researcher_id, name FROM researchers WHERE name LIKE '%John%'"
        })

    def test_publication_title_not_blocked(self):
        client = SovereignHTTPXClient()
        client.inspect_payload({
            "user_query": "Find publications about AI",
            "schema_prompt": "SELECT publication_id, title, year FROM publications WHERE title LIKE '%AI%'"
        })

    def test_institution_name_not_blocked(self):
        client = SovereignHTTPXClient()
        client.inspect_payload({
            "user_query": "List institutions in California",
            "schema_prompt": "SELECT institution_id, name, state FROM institutions WHERE state = 'CA'"
        })

    def test_complex_query_with_multiple_tables(self):
        client = SovereignHTTPXClient()
        client.inspect_payload({
            "user_query": "Show me researchers with high h-index who have published in top journals",
            "schema_prompt": """
                SELECT r.name, r.h_index, p.title, p.year
                FROM researchers r
                JOIN researcher_publications rp ON r.researcher_id = rp.researcher_id
                JOIN publications p ON rp.publication_id = p.publication_id
                WHERE r.h_index > 50
                ORDER BY r.h_index DESC
            """
        })

    def test_aggregate_query(self):
        client = SovereignHTTPXClient()
        client.inspect_payload({
            "user_query": "Count researchers by institution",
            "schema_prompt": """
                SELECT institution_id, COUNT(*) as researcher_count
                FROM researchers
                GROUP BY institution_id
            """
        })