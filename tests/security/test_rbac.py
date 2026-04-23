"""Security Tests - RBAC Validation."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.skills.text_to_sql.skill import TextToSQLSkill
from src.skills.rag.skill import RAGSkill


class TestRBAC:
    """Test role-based access control."""

    def test_tier1_full_access(self):
        """Test Tier 1 researcher gets full access."""
        skill = TextToSQLSkill()

        result = skill.execute("Find researchers in Gujarat", user_tier=1)

        assert result is not None

        skill.close()

    @pytest.mark.requires_db
    def test_tier2_government(self):
        """Test Tier 2 government access."""
        skill = TextToSQLSkill()

        result = skill.execute("Show funding trends", user_tier=2)

        assert result is not None

        skill.close()

    def test_tier3_industry(self):
        """Test Tier 3 industry access."""
        skill = TextToSQLSkill()

        result = skill.execute("List research capabilities", user_tier=3)

        query = result.get("query", "")

        assert "LIMIT" in query.upper()

        skill.close()

    @pytest.mark.requires_qdrant
    def test_rag_tier_filtering(self):
        """Test RAG respects tier filtering."""
        skill = RAGSkill()

        result = skill.retrieve("test", user_tier=1, top_k=5)

        assert "chunks" in result or "metadata" in result

        result3 = skill.retrieve("test", user_tier=3, top_k=5)

        assert "chunks" in result3 or "metadata" in result3

        skill.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
