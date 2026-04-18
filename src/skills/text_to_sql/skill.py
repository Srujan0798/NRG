"""Text-to-SQL Skill - Natural language to SQL with zero data leakage."""

import os
import logging
from typing import Dict, Any, Optional
import json

from .sqlite_schema_extractor import SQLiteSchemaExtractor
from .sqlite_sandbox import SQLiteSandbox


logger = logging.getLogger(__name__)


class TextToSQLSkill:
    """Sovereign Text-to-SQL module."""

    def __init__(self, llm_provider: Optional[Any] = None):
        self.llm_provider = llm_provider
        self.extractor = SQLiteSchemaExtractor()
        self.sandbox = SQLiteSandbox()

    def generate_sql(self, user_query: str, schema_prompt: str) -> str:
        """
        Generate SQL from natural language using schema-only context.

        Returns SQL query string - data values never leave sandbox.
        """
        if not self.llm_provider:
            return self._fallback_sql(user_query)

        messages = [
            {
                "role": "system",
                "content": """You are a SQL expert. Generate accurate PostgreSQL queries.
                
RULES:
- Return ONLY the SQL query, no explanations
- Use proper UUID handling (uuid_generate_v4())
- Filter by access_tier based on user_tier parameter
- Always include LIMIT for safety (default 100)
- Use parameterized queries where possible
- Return valid, executable PostgreSQL syntax""",
            },
            {
                "role": "user",
                "content": f"{schema_prompt}\n\nUser Query: {user_query}\n\nGenerate SQL:",
            },
        ]

        try:
            response = self.llm_provider.chat(messages)
            sql = response.content.strip()
            sql = sql.strip("`").strip("sql").strip()
            return sql
        except Exception as e:
            logger.warning(f"LLM SQL generation failed: {e}")
            return self._fallback_sql(user_query)

    def _fallback_sql(self, query: str) -> str:
        """Simple keyword-based SQL generation fallback."""
        query_lower = query.lower()

        if "researcher" in query_lower or "faculty" in query_lower:
            return "SELECT * FROM researchers LIMIT 100"
        elif "lab" in query_lower or "laboratory" in query_lower:
            return "SELECT * FROM labs LIMIT 100"
        elif "publication" in query_lower or "paper" in query_lower:
            return "SELECT * FROM publications LIMIT 100"
        elif "funding" in query_lower or "grant" in query_lower:
            return "SELECT * FROM funding LIMIT 100"
        elif "collaboration" in query_lower:
            return "SELECT * FROM collaborations LIMIT 100"
        else:
            return "SELECT * FROM researchers LIMIT 100"

    def execute(self, user_query: str, user_tier: int = 1) -> Dict[str, Any]:
        """
        Execute text-to-sql skill.

        Returns result dict with audit log entry.
        """
        relevant_tables = self.extractor.get_relevant_tables(user_query)
        schema = self.extractor.get_schema_metadata(relevant_tables)
        schema_prompt = self.extractor.generate_llm_prompt(schema)

        sql = self.generate_sql(user_query, schema_prompt)

        sql = self._apply_tier_filter(sql, user_tier)

        result = self.sandbox.execute_readonly(sql, user_tier)

        result["schema_used"] = list(schema["tables"].keys())
        result["audit_logged"] = True

        return result

    def _apply_tier_filter(self, sql: str, user_tier: int) -> str:
        """Apply access tier filter to SQL.

        Tier 1 (Researcher): Own data and public data
        Tier 2 (Government): Aggregated and anonymized
        Tier 3 (Industry): Limited and licensed

        For SQLite, we don't have access_tier column, so we rely on RBAC filtering
        at the API middleware level. This function just ensures safe query limits.
        """
        # Add LIMIT if not present for safety
        if "LIMIT" not in sql.upper():
            sql = sql.rstrip(";") + " LIMIT 100"

        return sql

    def close(self):
        """Clean up resources."""
        self.extractor.close()
        self.sandbox.close()


def main():
    """Demo entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="NRG Text-to-SQL Skill")
    parser.add_argument("--demo", type=str, help="Demo query")

    args = parser.parse_args()

    if args.demo:
        skill = TextToSQLSkill()
        result = skill.execute(args.demo)
        print(json.dumps(result, indent=2, default=str))
        skill.close()
    else:
        print("Text-to-SQL Skill Ready")


if __name__ == "__main__":
    main()
