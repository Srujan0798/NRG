"""SQLite Schema Extractor - Extract schema metadata only, NO data."""

import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path


class SQLiteSchemaExtractor:
    """Extract schema metadata from SQLite without exposing data."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "nrg_research.db"
        self.conn = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def get_table_names(self) -> List[str]:
        """Get all table names from database."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cursor.fetchall()]

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a table."""
        conn = self._get_connection()
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            # row: (cid, name, type, notnull, dflt_value, pk)
            columns.append({
                "name": row[1],
                "type": row[2],
                "nullable": not row[3],  # notnull = 1 means nullable = False
                "default": row[4],
                "pk": row[5] == 1,
            })
        return columns

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key information for a table."""
        conn = self._get_connection()
        cursor = conn.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = []
        for row in cursor.fetchall():
            # row: (id, seq, table, from, to, on_update, on_delete, match)
            fks.append({
                "constrained_columns": [row[3]],
                "referred_table": row[2],
                "referred_columns": [row[4]] if row[4] else [],
            })
        return fks

    def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get index information for a table."""
        conn = self._get_connection()
        cursor = conn.execute(f"PRAGMA index_list({table_name})")
        indexes = []
        for row in cursor.fetchall():
            # row: (seq, name, unique, origin, partial)
            index_name = row[1]
            # Get columns for this index
            col_cursor = conn.execute(f"PRAGMA index_info({index_name})")
            columns = [col_row[2] for col_row in col_cursor.fetchall()]
            indexes.append({
                "name": index_name,
                "columns": columns,
                "unique": row[2] == 1,
            })
        return indexes

    def get_schema_metadata(
        self, table_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract schema metadata: table names and column headers ONLY.

        Returns structure for LLM prompt - NO data rows.
        """
        schema = {"tables": {}}

        if table_names is None:
            table_names = self.get_table_names()

        for table_name in table_names:
            columns = self.get_columns(table_name)
            foreign_keys = self.get_foreign_keys(table_name)
            indexes = self.get_indexes(table_name)

            # Get primary keys
            primary_keys = [col["name"] for col in columns if col.get("pk")]

            schema["tables"][table_name] = {
                "columns": [
                    {
                        "name": col["name"],
                        "type": col["type"],
                        "nullable": col["nullable"],
                        "default": col["default"],
                    }
                    for col in columns
                ],
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys,
                "indexes": [
                    {"name": idx["name"], "columns": idx["columns"]}
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
                        f"    - {', '.join(fk['constrained_columns'])} -> "
                        f"{fk['referred_table']}.{', '.join(fk['referred_columns'])}"
                    )

            prompt_parts.append("")

        return "\n".join(prompt_parts)

    def get_relevant_tables(self, query: str) -> List[str]:
        """
        Prune schema to only relevant tables for query intent.

        Simple keyword matching - checks if query mentions entity keywords.
        """
        query_lower = query.lower()
        all_tables = self.get_table_names()

        # Map table names to query keywords that indicate relevance
        keywords = {
            "researchers": ["researcher", "faculty", "professor", "scientist", "people", "person"],
            "labs": ["lab", "laboratory", "center"],
            "publications": [
                "publication",
                "paper",
                "article",
                "journal",
                "conference",
            ],
            "funding_records": ["funding", "grant", "fund", "budget"],
            "institutions": ["institution", "university", "iit", "nit", "college"],
            "keywords": ["topic", "keyword", "specialization"],
            "researcher_publications": ["author", "wrote", "published"],
            "researcher_labs": ["member", "works in", "affiliated"],
        }

        relevant = set()
        for table in all_tables:
            table_lower = table.lower()
            # Check if query keywords match this table
            if table_lower in keywords:
                for kw in keywords[table_lower]:
                    if kw in query_lower:
                        relevant.add(table)
                        break

        # If no specific tables matched, try a broad match: return the
        # most commonly useful tables rather than all of them
        if not relevant:
            default_tables = {"researchers", "institutions", "labs"}
            relevant = {t for t in all_tables if t in default_tables}

        return list(relevant) if relevant else all_tables

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
