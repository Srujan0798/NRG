"""SQLite Schema Extractor - Extract schema metadata only, NO data."""

import sqlite3
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.data.database import get_sqlite_connection, resolve_database_path


POSTGRESQL_ONLY_TABLES = {
    "academic_courses_details",
    "innovation_grant_from_govt",
    "innovations_at_various_stages_of_technology_readiness_level",
    "combined_ipo_patent_data",
    "incubation_details",
    "financial_expenses_capital",
    "financial_expenses_operational",
    "phd_students",
    "sanctioned_intake",
    "actual_student_strength",
    "placements_and_higher_studies",
    "package_data",
    "role_data",
    "faculty_details",
    "faculty_strength",
    "fdp_details",
    "expertise",
    "master_expertise",
    "seed_funding",
    "startup_receiving_vc_investment",
    "startup_recognition",
    "startups_turnover_50_lacs",
    "fdi_investment",
    "research_consultancy_details_consultancy",
    "research_consultancy_details_sponsered",
    "nirf_extracted_table",
    "nirf_pdf_record",
    "nirf_table_row",
    "patents_details",
    "ipo_patent_details_flat",
    "ipo_patent_details_flat_old",
    "combined_ipo_patent_data_old",
    "founders_of_fortune_500_companies",
    "scraped_data",
    "scraped_data_save",
    "scraped_raw_data",
    "advance_search_data",
    "advance_search_data_15_12",
    "advance_search_data_old",
    "tb_institute_mstr",
    "tb_institute_scrap_data_url",
    "tb_goi_ministries_mstr",
    "tb_academic_year_mstr",
    "tb_course_program_types",
    "user_registration",
}

POSTGRESQL_ONLY_KEYWORDS = {
    "academic_courses_details": {
        "course", "curriculum", "credit", "credits", "ug ", "pg ", "phd",
        "undergraduate", "postgraduate", "doctoral", "level_of_course",
        "academic course", "innovation course", "elective", "core course",
    },
    "innovation_grant_from_govt": {
        "grant", "funding", "govt grant", "government grant", "fund agency",
        "sanctioned grant", "grant received", "fund agency", "dST", "SERB",
        "innovation grant", "funding agency", "gov_organisation",
    },
    "innovations_at_various_stages_of_technology_readiness_level": {
        "trl", "technology readiness", "lab validation", "market ready",
        "pilot scale", "prototype", "technology readiness level",
        "level 1", "level 2", "level 3", "level 4", "level 5",
        "level 6", "level 7", "level 8", "level 9",
        "pipeline progression", "innovation pipeline", "commercialize",
        "trl stage",
    },
    "combined_ipo_patent_data": {
        "ipo patent", "combined patent", "patent granted", "patent filed",
        "patent status", "cost of innovation", "patent cost", "applicants",
    },
    "financial_expenses_capital": {
        "capex", "capital expense", "capital asset", "library", "equipment",
        "workshop", "capital spending", "high capex", "low capex",
    },
    "financial_expenses_operational": {
        "operational expense", "salaries", "maintenance", "seminars",
        "operating cost", "utilization audit", "low expenditure",
    },
    "incubation_details": {
        "incubated", "incubation", "startup", "startup incubated",
        "incubated startup", "cohort", "pre-incubation",
    },
    "phd_students": {
        "phd student", "phd enrollment", "doctoral student",
    },
    "sanctioned_intake": {
        "sanctioned intake", "student intake", "seats",
    },
    "actual_student_strength": {
        "student strength", "student count", "male female",
        "economically backward", "socially challenged",
    },
    "placements_and_higher_studies": {
        "placement", "higher studies", "median package", "students placed",
    },
    "package_data": {
        "package", "salary package", "lpa",
    },
    "faculty_details": {
        "faculty count", "number of faculty",
    },
    "faculty_strength": {
        "faculty strength", "faculty gender",
    },
    "expertise": {
        "expertise", "research area faculty",
    },
    "seed_funding": {
        "seed funding", "dpiit", "startup funding",
    },
    "startup_recognition": {
        "recognized startup", "startup recognition", "dst-tbi",
    },
    "nirf": {
        "nirf", "ranking", "nirf ranking",
    },
}

SQLITE_ONLY_TABLES = {
    "researchers", "institutions", "publications", "funding_records",
    "projects", "patents", "collaborations", "labs", "keywords",
    "research_documents", "researcher_publications", "researcher_labs",
    "publication_keywords", "audit_events", "consent_ledger",
    "refresh_tokens", "schema_migrations",
}


class SQLiteSchemaExtractor:
    """Extract schema metadata from SQLite without exposing data."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = resolve_database_path(db_path)
        self._thread_local = threading.local()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._thread_local, 'conn') or self._thread_local.conn is None:
            self._thread_local.conn = get_sqlite_connection(str(self.db_path))
        return self._thread_local.conn

    def get_table_names(self) -> List[str]:
        """Get all table names from database (excludes PostgreSQL-only tables)."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        return tables

    def get_all_table_names_including_postgres(self) -> List[str]:
        """Get all PostgreSQL table names (for schema bridge awareness)."""
        return list(POSTGRESQL_ONLY_TABLES)

    def get_unavailable_tables_for_query(self, query: str) -> List[str]:
        """
        Detect which PostgreSQL-only tables a query references.
        Returns list of tables that exist in PostgreSQL but NOT in SQLite dev.
        """
        query_lower = query.lower()
        unavailable = []
        for table, keywords in POSTGRESQL_ONLY_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    if table not in self.get_table_names():
                        unavailable.append(table)
                    break
        return unavailable

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
        schema: Dict[str, Any] = {"tables": {}}

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

        hints = _load_schema_hints()
        if hints:
            prompt_parts.extend(["", "SCHEMA HINTS:", hints])

        synonyms = _load_value_synonyms()
        if synonyms:
            prompt_parts.extend(["", "DOMAIN VALUE SYNONYMS:", synonyms])

        return "\n".join(prompt_parts)

    def get_relevant_tables(self, query: str) -> List[str]:
        """
        Prune schema to only relevant tables for query intent.

        Simple keyword matching - checks if query mentions entity keywords.
        Includes PostgreSQL-only tables for awareness but marks unavailable ones.
        """
        query_lower = query.lower()
        all_tables = self.get_table_names()

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
            "projects": ["project", "pi", "co-pi", "co pi", "principal investigator", "ongoing", "completed"],
            "patents": ["patent", "inventor", "filing", "grant", "technology transfer", "ip"],
            "collaborations": ["collaboration", "partner", "network", "cross-institutional"],
            "research_documents": ["document", "research document", "full text", "category"],
            "funding_records": ["funding", "grant", "fund", "budget"],
            "institutions": ["institution", "university", "iit", "nit", "college"],
            "keywords": ["topic", "keyword", "specialization"],
            "researcher_publications": ["author", "wrote", "published"],
            "researcher_labs": ["member", "works in", "affiliated"],
            "academic_courses_details": [
                "course", "pg course", "ug course", "phd course", "master course",
                "innovation curriculum", "credit", "academic", "level of course",
                "total credit", "curriculum", "iit madras", "iit bombay", "iit hyderabad",
            ],
            "innovation_grant_from_govt": [
                "grant", "funding agency", "government grant", "gov_organisation",
                "year of receiving", "funding drop", "rising star", "funding trend",
                "grant received", "yoy", "year-over-year",
            ],
            "innovations_at_various_stages_of_technology_readiness_level": [
                "trl", "technology readiness", "stage of technology", "market ready",
                "lab validation", "bottleneck", "level 9", "trl 9", "pipeline progression",
                "level 4", "various stage", "technology readiness level",
            ],
            "combined_ipo_patent_data": ["patent", "ipo", "grant", "cost per patent"],
            "financial_expenses_capital": [
                "capital expense", "capex", "capital asset", "equipment", "library",
                "workshop", "high capital", "gap analysis", "financial expense",
            ],
            "financial_expenses_operational": [
                "operational expense", "opex", "salary", "maintenance", "consumable",
                "seminar", "travel", "utilization audit", "expenditure", "low expenditure",
            ],
            "incubation_details": [
                "incubated", "startup", "incubation", "cohort", "cohort year",
                "incubated startup", "startup incubated",
            ],
        }

        relevant = set()
        for table in all_tables:
            table_lower = table.lower()
            if table_lower in keywords:
                for kw in keywords[table_lower]:
                    if kw in query_lower:
                        relevant.add(table)
                        break

        if not relevant:
            default_tables = {
                "researchers",
                "institutions",
                "labs",
                "projects",
                "publications",
                "funding_records",
            }
            relevant = {t for t in all_tables if t in default_tables}

        return list(relevant) if relevant else all_tables

    def get_postgresql_table_warning(self, query: str) -> Optional[str]:
        """
        Return a warning message if query references PostgreSQL-only tables.
        Returns None if all referenced tables are available in SQLite.
        """
        unavailable = self.get_unavailable_tables_for_query(query)
        if unavailable:
            return (
                f"NOTE: The following tables are not available in the development SQLite database "
                f"(they exist in the production PostgreSQL): {', '.join(sorted(unavailable))}. "
                f"This query may not return results in dev mode. "
                f"These tables are: {', '.join(sorted(unavailable))}."
            )
        return None

    def close(self):
        """Close database connection for current thread."""
        if hasattr(self._thread_local, 'conn') and self._thread_local.conn:
            self._thread_local.conn.close()
            self._thread_local.conn = None


def _load_schema_hints() -> str:
    hints_path = Path(__file__).resolve().parents[2] / "data" / "schema" / "schema_hints.md"
    try:
        return hints_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def _load_value_synonyms() -> str:
    synonyms_path = Path(__file__).resolve().parents[2] / "data" / "schema" / "schema_value_synonyms.md"
    try:
        return synonyms_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def extract_schema(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function used by validation scripts and agents."""
    extractor = SQLiteSchemaExtractor(db_path=db_path)
    try:
        return extractor.get_schema_metadata()
    finally:
        extractor.close()
