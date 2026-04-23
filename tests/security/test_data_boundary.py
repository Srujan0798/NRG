"""Security Tests - Data Boundary Enforcement."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.skills.text_to_sql.skill import TextToSQLSkill
from src.skills.rag.skill import RAGSkill


class TestDataBoundary:
    """Test data boundary enforcement."""

    def test_no_raw_db_schema_to_llm(self):
        """Test schema-only sent to LLM, not full schema."""
        skill = TextToSQLSkill()

        schema = skill.extractor.get_schema_metadata()

        for table_name, table_info in schema.get("tables", {}).items():
            for col in table_info.get("columns", []):
                assert "name" in col
                assert "type" in col

        skill.close()

    @pytest.mark.requires_qdrant
    def test_vector_metadata_filtered(self):
        """Test vector results have metadata filtering."""
        skill = RAGSkill()

        result = skill.retrieve("test query", user_tier=1, top_k=5)

        for meta in result.get("metadata", []):
            assert "access_tier" in meta
            assert "source_id" in meta

        skill.close()

    def test_audit_log_created(self):
        """Test audit log entries created."""
        skill = TextToSQLSkill()

        result = skill.execute("test", user_tier=1)

        assert result.get("audit_logged") is True

        skill.close()


class TestAccessControl:
    """Test access control mechanisms."""

    def test_tier1_can_access_all(self):
        """Test Tier 1 access."""
        skill = TextToSQLSkill()

        result = skill.execute("test", user_tier=1)

        assert result is not None

        skill.close()

    def test_tier2_restricted(self):
        """Test Tier 2 restrictions applied."""
        skill = TextToSQLSkill()

        result = skill.execute("test", user_tier=2)

        query = result.get("query", "")

        assert "LIMIT" in query.upper()

        skill.close()

    def test_tier3_most_restricted(self):
        """Test Tier 3 most restricted."""
        skill = TextToSQLSkill()

        result = skill.execute("test", user_tier=3)

        query = result.get("query", "")

        assert "LIMIT" in query.upper()

        skill.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
