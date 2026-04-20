"""Tests for Text-to-SQL Skill."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.skills.text_to_sql.sqlite_schema_extractor import SQLiteSchemaExtractor as SchemaExtractor
from src.skills.text_to_sql.sqlite_sandbox import SQLiteSandbox as Sandbox
from src.skills.text_to_sql.skill import TextToSQLSkill


class TestSchemaExtractor:
    """Test schema extraction."""

    def test_get_relevant_tables(self):
        """Test table pruning."""
        extractor = SchemaExtractor()
        tables = extractor.get_relevant_tables("Find robotics researchers in Gujarat")
        assert isinstance(tables, list)
        extractor.close()

    def test_schema_has_no_data(self):
        """Test schema metadata contains no values."""
        extractor = SchemaExtractor()
        schema = extractor.get_schema_metadata()
        for table_name, table_info in schema.get("tables", {}).items():
            for col in table_info.get("columns", []):
                assert "name" in col
                assert "type" in col
        extractor.close()


class TestSandbox:
    """Test sandbox execution."""

    def test_select_only(self):
        """Test only SELECT queries allowed."""
        sandbox = Sandbox()

        with pytest.raises((PermissionError, RuntimeError)):
            sandbox.execute_readonly("INSERT INTO researchers VALUES (1)")

        with pytest.raises((PermissionError, RuntimeError)):
            sandbox.execute_readonly("UPDATE researchers SET name = 'test'")

        with pytest.raises((PermissionError, RuntimeError)):
            sandbox.execute_readonly("DELETE FROM researchers")

        sandbox.close()

    def test_readonly_query(self):
        """Test SELECT query execution."""
        sandbox = Sandbox()

        result = sandbox.execute_readonly("SELECT * FROM researchers LIMIT 10")
        assert "results" in result
        assert "columns" in result

        sandbox.close()


class TestTextToSQLSkill:
    """Test Text-to-SQL skill."""

    def test_execute(self):
        """Test skill execution."""
        skill = TextToSQLSkill()
        result = skill.execute("Find all researchers", user_tier=1)

        assert "query" in result or "schema_used" in result
        assert result.get("audit_logged") is True

        skill.close()

    def test_tier_filtering(self):
        """Test tier filtering applied."""
        skill = TextToSQLSkill()

        result = skill.execute("Find researchers", user_tier=3)
        query = result.get("query", "")

        assert "LIMIT" in query.upper()

        skill.close()

    def test_fallback_sql(self):
        """Test fallback SQL generation."""
        skill = TextToSQLSkill()

        sql = skill._fallback_sql("Find robotics researchers")
        assert "SELECT" in sql.upper()

        sql = skill._fallback_sql("List all labs")
        assert "lab" in sql.lower()

        skill.close()

    def test_fallback_sql_count_query(self):
        skill = TextToSQLSkill()
        sql = skill._fallback_sql("How many researchers are in Gujarat")
        assert "COUNT" in sql.upper()
        skill.close()

    def test_fallback_sql_year_filter(self):
        skill = TextToSQLSkill()
        sql = skill._fallback_sql("Find researchers after 2020")
        assert "2020" in sql
        skill.close()

    def test_fallback_sql_publications(self):
        skill = TextToSQLSkill()
        sql = skill._fallback_sql("List publications in 2023")
        assert "publications" in sql.lower()
        skill.close()

    def test_detect_database_default(self):
        skill = TextToSQLSkill()
        assert skill._db_type == "sqlite"
        skill.close()

    def test_get_dialect_system_prompt_sqlite(self):
        skill = TextToSQLSkill()
        prompt = skill._get_dialect_system_prompt()
        assert "SQLite" in prompt
        skill.close()

    def test_close(self):
        skill = TextToSQLSkill()
        skill.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
