"""SQLite Schema Extractor - Extract schema metadata only, NO data."""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.config.database import get_database_manager, DatabaseManager

REPO_ROOT = Path(__file__).resolve().parents[3]
POPULATED_LOCAL_DB = REPO_ROOT / "data" / "nrg_research.db"
ROOT_LOCAL_DB = REPO_ROOT / "nrg_research.db"


POSTGRESQL_ONLY_TABLES = {
    "academic_courses_details",
    "innovation_grant_from_govt",
    "trl_stages",
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
    "trl_stages": {
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


def _resolve_default_schema_database_url() -> Optional[str]:
    configured_test = os.getenv("NRG_TEST_DATABASE_URL")
    if configured_test:
        return configured_test

    raw_url = os.getenv("DATABASE_URL")
    if raw_url and raw_url.startswith("postgresql://"):
        return None

    default_local_urls = {
        None,
        "",
        "sqlite:///nrg_research.db",
        f"sqlite:///{ROOT_LOCAL_DB}",
    }
    if POPULATED_LOCAL_DB.exists() and raw_url in default_local_urls:
        return f"sqlite:///{POPULATED_LOCAL_DB}"

    if raw_url and raw_url.startswith("sqlite:///"):
        return raw_url
    return f"sqlite:///{ROOT_LOCAL_DB}"


class SQLiteSchemaExtractor:
    """Extract schema metadata from SQLite without exposing data."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_manager = DatabaseManager(f"sqlite:///{db_path}")
        else:
            database_url = _resolve_default_schema_database_url()
            self.db_manager = (
                DatabaseManager(database_url)
                if database_url
                else get_database_manager()
            )

    def get_table_names(self) -> List[str]:
        """Get all table names from database (excludes PostgreSQL-only tables)."""
        rows = self.db_manager.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row["name"] for row in rows]

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
        rows = self.db_manager.fetch_all(f"PRAGMA table_info({table_name})")
        columns = []
        for row in rows:
            columns.append({
                "name": row["name"],
                "type": row["type"],
                "nullable": not row["notnull"],
                "default": row["dflt_value"],
                "pk": row["pk"] == 1,
            })
        return columns

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key information for a table."""
        rows = self.db_manager.fetch_all(f"PRAGMA foreign_key_list({table_name})")
        fks = []
        for row in rows:
            fks.append({
                "constrained_columns": [row["from"]],
                "referred_table": row["table"],
                "referred_columns": [row["to"]] if row["to"] else [],
            })
        return fks

    def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get index information for a table."""
        rows = self.db_manager.fetch_all(f"PRAGMA index_list({table_name})")
        indexes = []
        for row in rows:
            index_name = row["name"]
            col_rows = self.db_manager.fetch_all(f"PRAGMA index_info({index_name})")
            columns = [col_row["name"] for col_row in col_rows]
            indexes.append({
                "name": index_name,
                "columns": columns,
                "unique": row["unique"] == 1,
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
        from src.skills.text_to_sql._schema_prompt_utils import relevant_tables_for_query
        all_tables = self.get_table_names()
        return relevant_tables_for_query(query, all_tables)

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
        """Close database connections (no-op with DatabaseManager)."""
        pass


def _load_schema_hints() -> str:
    from src.skills.text_to_sql._schema_prompt_utils import _load_schema_hints as _shared_load_hints
    return _shared_load_hints()


def _load_value_synonyms() -> str:
    from src.skills.text_to_sql._schema_prompt_utils import _load_value_synonyms as _shared_load_synonyms
    return _shared_load_synonyms()


def extract_schema(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function used by validation scripts and agents."""
    extractor = SQLiteSchemaExtractor(db_path=db_path)
    try:
        return extractor.get_schema_metadata()
    finally:
        extractor.close()
