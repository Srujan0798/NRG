"""Text-to-SQL Schema Extractor - Extract schema metadata only, NO data, tier-filtered."""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy import create_engine, inspect

TIER_COLUMN_VISIBILITY = {
    1: {},
    2: {
        "researchers": ["researcher_id", "name", "institution_id", "department", "state",
            "research_area", "secondary_research_areas", "years_experience",
            "year_joined", "h_index", "orcid", "email", "phone"],
        "institutions": ["institution_id", "name", "type", "state", "region",
            "established_year", "website"],
        "labs": ["lab_id", "name", "institution_id", "department", "lab_head",
            "established_year", "funding_source"],
        "publications": ["publication_id", "title", "year", "abstract", "journal",
            "doi", "citation_count", "authors"],
        "projects": ["project_id", "title", "pi_researcher_id", "funding_id",
            "amount", "source", "start_date", "end_date", "status"],
        "funding_records": ["funding_id", "source", "amount", "grant_type",
            "duration_months", "research_area"],
        "patents": ["patent_id", "title", "inventor_ids", "filing_date",
            "status", "jurisdiction"],
        "collaborations": ["collab_id", "name", "institution_ids", "type",
            "start_date", "end_date"],
        "keywords": ["keyword_id", "keyword", "category", "subcategory"],
        "researcher_publications": ["researcher_id", "publication_id", "author_order"],
        "researcher_labs": ["researcher_id", "lab_id", "role", "start_date"],
        "research_documents": ["doc_id", "title", "category", "upload_date"],
    },
    3: {
        "researchers": ["researcher_id", "name", "institution_id", "state",
            "research_area", "years_experience", "h_index"],
        "institutions": ["institution_id", "name", "type", "state"],
        "labs": ["lab_id", "name", "institution_id", "department"],
        "publications": ["publication_id", "title", "year", "citation_count"],
        "projects": ["project_id", "title", "source", "amount", "status"],
        "funding_records": ["funding_id", "source", "amount", "grant_type"],
        "patents": ["patent_id", "title", "status"],
        "collaborations": ["collab_id", "name", "type"],
        "keywords": ["keyword", "category"],
        "researcher_publications": ["researcher_id", "publication_id"],
        "researcher_labs": ["researcher_id", "lab_id"],
        "research_documents": ["doc_id", "title", "category"],
    },
}

SENSITIVE_COLUMNS = {
    "email", "phone", "aadhaar_number", "pan_number", "date_of_birth",
    "address", "personal_phone", "alternate_email"
}

SCHEMA_PROBING_PATTERNS = [
    r"\b(show|describe|list)\s+(tables?|columns?|fields?|schema|structure)\b",
    r"\bwhat\s+columns?\s+(does\s+)?(exist|are\s+there|in)\b",
    r"\bwhat\s+fields?\s+(does\s+)?(exist|are\s+there|in)\b",
    r"\bhow\s+many\s+columns?\b",
    r"\bselect\s+\*\s+from\b",
    r"\b(explain|describe)\s+(table|database|schema)\b",
    r"\b\d+\s+columns?\b",
]


def is_schema_probing_query(query: str) -> bool:
    """Module-level schema probing detection for convenience."""
    query_lower = query.lower()
    for pattern in SCHEMA_PROBING_PATTERNS:
        if re.search(pattern, query_lower):
            return True
    return False


class SchemaExtractor:
    """Extract schema metadata without exposing data."""

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string: str = connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://nrg:nrg_secret@localhost:5432/nrg",
        ) or "postgresql://nrg:nrg_secret@localhost:5432/nrg"
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
        schema: Dict[str, Any] = {"tables": {}}

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
        """
        query_lower = query.lower()
        all_tables = self.inspector.get_table_names()

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
                "course", "curriculum", "credit", "credits", "ug ", "pg ", "phd",
                "undergraduate", "postgraduate", "doctoral", "level_of_course",
                "academic course", "innovation course", "elective", "core course",
            ],
            "innovation_grant_from_govt": [
                "grant", "funding", "govt grant", "government grant", "fund agency",
                "sanctioned grant", "grant received", "fund agency", "dST", "SERB",
                "innovation grant", "funding agency",
            ],
            "innovations_at_various_stages_of_technology_readiness_level": [
                "trl", "technology readiness", "lab validation", "market ready",
                "pilot scale", "prototype", "technology readiness level",
                "level 1", "level 2", "level 3", "level 4", "level 5",
                "level 6", "level 7", "level 8", "level 9",
                "pipeline progression", "innovation pipeline", "commercialize",
            ],
            "combined_ipo_patent_data": [
                "ipo patent", "combined patent", "patent granted", "patent filed",
                "patent status", "cost of innovation", "patent cost",
            ],
            "financial_expenses_capital": [
                "capex", "capital expense", "capital asset", "library", "equipment",
                "workshop", "capital spending", "high capex", "low capex",
            ],
            "financial_expenses_operational": [
                "operational expense", "salaries", "maintenance", "seminars",
                "operating cost", "utilization audit", "low expenditure",
            ],
            "incubation_details": [
                "incubated", "incubation", "startup", "startup incubated",
                "incubated startup", "cohort",
            ],
            "startup_recognition": [
                "recognized startup", "startup recognition", "dst-tbi",
            ],
            "phd_students": [
                "phd student", "phd enrollment", "doctoral student",
            ],
            "sanctioned_intake": [
                "sanctioned intake", "student intake", "seats",
            ],
            "actual_student_strength": [
                "student strength", "student count", "male female",
                "economically backward", "socially challenged", "reimbursed",
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

        # If no specific tables matched, return commonly useful tables
        if not relevant:
            default_tables = {
                "researchers",
                "institutions",
                "labs",
                "projects",
                "publications",
                "funding_records",
                "academic_courses_details",
                "innovation_grant_from_govt",
                "innovations_at_various_stages_of_technology_readiness_level",
            }
            relevant = {t for t in all_tables if t in default_tables}

        return list(relevant) if relevant else all_tables

    def close(self):
        self.engine.dispose()

    def is_schema_probing_query(self, query: str) -> bool:
        """Check if query is attempting schema fingerprinting."""
        query_lower = query.lower()
        for pattern in SCHEMA_PROBING_PATTERNS:
            if re.search(pattern, query_lower):
                return True
        return False

    def get_tier_filtered_columns(self, table_name: str, tier: int) -> List[str]:
        """Get column names visible to a given tier for a specific table."""
        if tier == 1:
            return []

        tier_tables = TIER_COLUMN_VISIBILITY.get(tier, {})
        return tier_tables.get(table_name, [])

    def generate_llm_schema(
        self,
        table_names: Optional[List[str]] = None,
        tier: int = 1,
    ) -> Dict[str, Any]:
        """Generate tier-filtered, abstracted schema for LLM exposure.

        Columns are filtered by tier visibility per table, and sensitive column names
        are replaced with abstract identifiers to prevent schema fingerprinting.
        """
        schema = self.get_schema_metadata(table_names)

        abstract_mapping: Dict[str, str] = {}
        abstract_counter = 1

        for table_name, table_info in schema["tables"].items():
            visible_columns = self.get_tier_filtered_columns(table_name, tier) if tier > 1 else None

            filtered_columns = []
            for col in table_info["columns"]:
                col_name = col["name"]

                if visible_columns is not None and col_name not in visible_columns:
                    continue

                if col_name in SENSITIVE_COLUMNS:
                    if col_name not in abstract_mapping:
                        abstract_mapping[col_name] = f"pii_field_{abstract_counter}"
                        abstract_counter += 1
                    col = {**col, "name": abstract_mapping[col_name], "type": "REDACTED"}

                filtered_columns.append(col)

            schema["tables"][table_name]["columns"] = filtered_columns

        return schema


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
