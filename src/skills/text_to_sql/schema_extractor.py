"""Text-to-SQL Schema Extractor - Extract schema metadata only, NO data."""

import os
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.engine import Engine


class SchemaExtractor:
    """Extract schema metadata without exposing data."""

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://nrg:nrg_secret@localhost:5432/nrg",
        )
        self.engine = create_engine(
            self.connection_string, echo=False, pool_pre_ping=True
        )
        self.inspector = inspect(self.engine)

    def get_schema_metadata(
        self, table_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract schema metadata: table names and column headers ONLY.

        Returns structure for LLM prompt - NO data rows.
        """
        schema = {"tables": {}}

        if table_names is None:
            table_names = self.inspector.get_table_names()

        for table_name in table_names:
            columns = self.inspector.get_columns(table_name)
            primary_keys = self.inspector.get_pk_constraint(table_name)
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            indexes = self.inspector.get_indexes(table_name)

            schema["tables"][table_name] = {
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "default": str(col.get("default"))
                        if col.get("default")
                        else None,
                    }
                    for col in columns
                ],
                "primary_keys": primary_keys.get("constrained_columns", [])
                if primary_keys
                else [],
                "foreign_keys": [
                    {
                        "constrained_columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"],
                    }
                    for fk in foreign_keys
                ],
                "indexes": [
                    {"name": idx["name"], "columns": idx["column_names"]}
                    for idx in indexes
                ],
            }

        return schema

    def generate_llm_prompt(self, schema: Dict[str, Any]) -> str:
        """
        Generate schema-only prompt for LLM.

        IMPORTANT: This includes ZERO data values - only structure.
        """
        prompt_parts = ["DATABASE SCHEMA (metadata only - no data values):", ""]

        for table_name, table_info in schema["tables"].items():
            prompt_parts.append(f"## Table: {table_name}")
            prompt_parts.append("Columns:")

            for col in table_info["columns"]:
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                prompt_parts.append(f"  - {col['name']}: {col['type']} {nullable}")

            if table_info["primary_keys"]:
                prompt_parts.append(
                    f"  PRIMARY KEY: {', '.join(table_info['primary_keys'])}"
                )

            if table_info["foreign_keys"]:
                prompt_parts.append("Foreign Keys:")
                for fk in table_info["foreign_keys"]:
                    prompt_parts.append(
                        f"  - {fk['constrained_columns']} -> "
                        f"{fk['referred_table']}.{fk['referred_columns']}"
                    )

            prompt_parts.append("")

        return "\n".join(prompt_parts)

    def get_relevant_tables(self, query: str) -> List[str]:
        """
        Prune schema to only relevant tables for query intent.

        Simple keyword matching - can be enhanced with LLM.
        """
        query_lower = query.lower()
        all_tables = self.inspector.get_table_names()

        keywords = {
            "researchers": ["researcher", "faculty", "professor", "scientist"],
            "labs": ["lab", "laboratory", "center", "institute"],
            "publications": [
                "publication",
                "paper",
                "article",
                "journal",
                "conference",
            ],
            "funding": ["funding", "grant", "fund", "budget", "project"],
            "collaborations": ["collaboration", "partner", "joint"],
            "institutions": ["institution", "university", "iit", "nit"],
            "topics": ["topic", "research_area", "specialization"],
        }

        relevant = []
        for table in all_tables:
            table_lower = table.lower()
            for entity, entity_keywords in keywords.items():
                if entity in table_lower:
                    relevant.append(table)
                    break

        return relevant if relevant else all_tables

    def close(self):
        self.engine.dispose()
