"""Text-to-SQL Schema Extractor - Extract schema metadata only, NO data, policy-filtered."""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy import create_engine, inspect

from src.auth.rbac import get_policy_engine

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

TIER_COLUMN_VISIBILITY = {
    1: {},
    2: {
        "researchers": ["id", "name", "department", "email"],
        "publications": ["id", "title", "year", "venue"],
        "projects": ["id", "name", "status", "funding"],
    },
    3: {
        "researchers": ["id", "name", "department", "email", "phone", "aadhaar_number"],
        "publications": ["id", "title", "year", "venue", "abstract"],
        "projects": ["id", "name", "status", "funding", "budget"],
    },
}


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

    def get_tier_filtered_columns(
        self,
        table_name: str,
        tier: int | None = None,
        persona: str | None = None,
    ) -> List[str]:
        """
        Get column names visible for a table under a given tier or persona.

        Uses RBACPolicyEngine for authoritative policy lookup.
        Falls back to all columns if no policy found for the tier.
        """
        engine = get_policy_engine()
        try:
            if persona:
                policy = engine.get_policy(persona=persona)
            elif tier is not None:
                policy = engine.get_policy(tier=tier)
            else:
                return []
        except KeyError:
            return []

        return engine.get_visible_columns(policy, table_name)

    def generate_llm_schema(
        self,
        table_names: Optional[List[str]] = None,
        tier: int | None = None,
        persona: str | None = None,
    ) -> Dict[str, Any]:
        """Generate tier-filtered, abstracted schema for LLM exposure.

        Columns are filtered by RBAC policy per table, and sensitive column names
        are replaced with abstract identifiers to prevent schema fingerprinting.

        Args:
            table_names: List of tables to include. Defaults to all tables.
            tier: Integer tier level (1/2/3). Optional if persona is provided.
            persona: Named persona string. Takes precedence over tier if provided.
        """
        schema = self.get_schema_metadata(table_names)

        engine = get_policy_engine()
        try:
            if persona:
                policy = engine.get_policy(persona=persona)
            elif tier is not None:
                policy = engine.get_policy(tier=tier)
            else:
                policy = engine.get_policy(tier=1)
        except KeyError:
            return schema

        abstract_mapping: Dict[str, str] = {}
        abstract_counter = 1

        for table_name, table_info in schema["tables"].items():
            visible_patterns = engine.get_visible_columns(policy, table_name)

            filtered_columns = []
            for col in table_info["columns"]:
                col_name = col["name"]

                if visible_patterns and "*" not in visible_patterns and col_name not in visible_patterns:
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
