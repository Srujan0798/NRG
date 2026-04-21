"""Text-to-SQL Skill - Natural language to SQL with zero data leakage."""

import os
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
import json

import sqlglot
from sqlglot import exp

from src.audit import log_llm_call as audit_log_llm_call


logger = logging.getLogger(__name__)

TIER_AWARE_TABLES = {
    "researchers",
    "publications",
    "funding_records",
    "projects",
    "patents",
    "collaborations",
}
MAX_LIMIT = 200
FORBIDDEN_SQL_PATTERN = re.compile(
    r"(--|/\*|\*/|;|\b("
    r"attach|detach|alter|create|delete|drop|insert|pragma|replace|truncate|union|update|vacuum"
    r")\b)",
    re.IGNORECASE,
)


class TierAwareSqlRewriter:
    """
    Rewrites SQL to enforce tier-based access control using sqlglot.

    - Parses SQL and rejects non-SELECT
    - Injects WHERE access_tier >= :user_tier for TIER_AWARE_TABLES
    - Enforces outer LIMIT 200
    """

    def rewrite(self, sql: str, user_tier: int) -> str:
        """Rewrite SQL with tier filtering."""
        self._validate_sql_text(sql)

        try:
            statements = sqlglot.parse(sql, dialect=self._get_dialect())
        except sqlglot.errors.ParseError as e:
            logger.warning("SQL parse error: %s", e)
            raise PermissionError("SQL could not be safely parsed") from e

        if len(statements) != 1:
            raise PermissionError("Only a single SELECT statement is allowed")

        parsed = statements[0]

        if not isinstance(parsed, exp.Select):
            raise PermissionError("Only SELECT queries are allowed")

        tables_in_query = self._get_tables(parsed)
        needs_tier_filter = tables_in_query & TIER_AWARE_TABLES

        if needs_tier_filter:
            parsed = self._inject_tier_filter(parsed, user_tier, needs_tier_filter)

        parsed = self._enforce_limit(parsed)

        return parsed.sql(dialect=self._get_dialect())

    def _validate_sql_text(self, sql: str) -> None:
        if not sql or not sql.strip():
            raise PermissionError("Empty SQL is not allowed")

        if FORBIDDEN_SQL_PATTERN.search(sql):
            raise PermissionError("Potentially unsafe SQL is not allowed")

    def _get_dialect(self) -> str:
        db_url = os.getenv("DATABASE_URL", "")
        if db_url.startswith("postgresql") or db_url.startswith("postgres"):
            return "postgres"
        return "sqlite"

    def _get_tables(self, parsed: exp.Select) -> set:
        tables = set()
        for table in parsed.find_all(exp.Table):
            if table.name:
                tables.add(table.name.lower())
        return tables

    def _inject_tier_filter(
        self, parsed: exp.Select, user_tier: int, tables: set
    ) -> exp.Select:
        if self._has_tier_filter(parsed):
            return parsed

        tier_condition: Optional[exp.Condition] = None
        for table in parsed.find_all(exp.Table):
            if table.name and table.name.lower() in tables:
                table_ref = table.alias_or_name
                condition = exp.GTE(
                    this=exp.column("access_tier", table=table_ref),
                    expression=exp.Literal.number(user_tier),
                )
                tier_condition = condition if tier_condition is None else exp.and_(
                    tier_condition,
                    condition,
                )

        if tier_condition is None:
            tier_condition = exp.GTE(
                this=exp.column("access_tier"),
                expression=exp.Literal.number(user_tier),
            )

        existing_where = parsed.args.get("where")
        if existing_where:
            parsed.set("where", exp.Where(this=exp.and_(existing_where.this, tier_condition)))
            return parsed

        parsed.set("where", exp.Where(this=tier_condition))
        return parsed

    def _has_tier_filter(self, parsed: exp.Select) -> bool:
        for column in parsed.find_all(exp.Column):
            if column.name == "access_tier":
                return True
        return False

    def _enforce_limit(self, parsed: exp.Select) -> exp.Select:
        existing_limit = parsed.args.get("limit")
        if existing_limit is None:
            parsed.set("limit", exp.Limit(expression=exp.Literal.number(MAX_LIMIT)))
        else:
            existing_val = existing_limit.args.get("expression")
            if existing_val and isinstance(existing_val, exp.Literal):
                current_limit = int(existing_val.this)
                if current_limit > MAX_LIMIT:
                    existing_val.set("this", str(MAX_LIMIT))
        return parsed

    def _safe_fallback(self, sql: str, user_tier: int) -> str:
        raise PermissionError("Unsafe SQL fallback refused")

# Indian states for WHERE clause extraction
_INDIAN_STATES = [
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "delhi", "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand",
    "karnataka", "kerala", "madhya pradesh", "maharashtra", "manipur",
    "meghalaya", "mizoram", "nagaland", "odisha", "punjab", "rajasthan",
    "sikkim", "tamil nadu", "telangana", "tripura", "uttar pradesh",
    "uttarakhand", "west bengal",
]

_STATE_ABBREVIATIONS = {
    "andhra pradesh": "AP",
    "arunachal pradesh": "AR",
    "assam": "AS",
    "bihar": "BR",
    "chhattisgarh": "CG",
    "delhi": "DL",
    "goa": "GA",
    "gujarat": "GJ",
    "haryana": "HR",
    "himachal pradesh": "HP",
    "jharkhand": "JH",
    "karnataka": "KA",
    "kerala": "KL",
    "madhya pradesh": "MP",
    "maharashtra": "MH",
    "manipur": "MN",
    "meghalaya": "ML",
    "mizoram": "MZ",
    "nagaland": "NL",
    "odisha": "OR",
    "punjab": "PB",
    "rajasthan": "RJ",
    "sikkim": "SK",
    "tamil nadu": "TN",
    "telangana": "TS",
    "tripura": "TR",
    "uttar pradesh": "UP",
    "uttarakhand": "UK",
    "west bengal": "WB",
}

# Research areas for WHERE clause extraction
_RESEARCH_AREAS = [
    "ai", "machine learning", "deep learning", "nlp",
    "natural language processing", "computer vision", "robotics",
    "quantum computing", "cybersecurity", "data science",
    "bioinformatics", "biotechnology", "nanotechnology", "sustainable energy",
    "climate", "climate science", "semiconductor", "vlsi", "drug discovery",
    "healthcare ai", "smart manufacturing", "agriculture technology",
    "catalysis", "iot", "blockchain",
]


class TextToSQLSkill:
    """Sovereign Text-to-SQL module.

    Auto-detects database backend (SQLite vs PostgreSQL) from DATABASE_URL.
    """

    def __init__(self, llm_provider: Optional[Any] = None):
        self.llm_provider = llm_provider
        self._db_type, self._db_url = self._detect_database()
        self.extractor, self.sandbox = self._initialize_backend()
        self._sql_rewriter = TierAwareSqlRewriter()

    def _detect_database(self) -> tuple:
        """Detect database type from DATABASE_URL environment variable."""
        db_url = os.getenv("DATABASE_URL", "").strip()

        if not db_url:
            return "sqlite", "sqlite:///nrg_research.db"

        if db_url.startswith("sqlite"):
            return "sqlite", db_url
        elif db_url.startswith("postgresql") or db_url.startswith("postgres"):
            return "postgresql", db_url
        else:
            # Default to SQLite for safety
            logger.warning(f"Unknown DATABASE_URL format, defaulting to SQLite: {db_url[:50]}...")
            return "sqlite", "sqlite:///nrg_research.db"

    def _initialize_backend(self) -> tuple[Any, Any]:
        """Initialize the appropriate schema extractor and sandbox based on DB type."""
        extractor: Any
        sandbox: Any
        if self._db_type == "sqlite":
            from .sqlite_schema_extractor import SQLiteSchemaExtractor
            from .sqlite_sandbox import SQLiteSandbox

            db_path = self._db_url.replace("sqlite:///", "")
            extractor = SQLiteSchemaExtractor(db_path=db_path)
            sandbox = SQLiteSandbox(db_path=db_path)
        else:
            from .schema_extractor import SchemaExtractor
            from .sandbox import Sandbox

            extractor = SchemaExtractor(connection_string=self._db_url)
            sandbox = Sandbox(connection_string=self._db_url)

        logger.info(f"Initialized TextToSQLSkill with {self._db_type} backend")
        return extractor, sandbox

    def _get_dialect_system_prompt(self) -> str:
        """Return dialect-correct system prompt based on DB type."""
        if self._db_type == "postgresql":
            return """You are a SQL expert. Generate accurate PostgreSQL queries.

RULES:
- Return ONLY the SQL query, no explanations
- Always include LIMIT for safety (default 100, max 200)
- Use parameterized queries where possible
- Return valid, executable PostgreSQL syntax
- Use single quotes for string literals
- PostgreSQL supports UUID, NOW(), EXTRACT() functions
- Table names: researchers, publications, institutions, labs, funding_records, projects, patents, collaborations, research_documents
- All tier-aware tables have access_tier column (1=researcher, 2=government, 3=industry)"""
        else:
            return """You are a SQL expert. Generate accurate SQLite queries.

RULES:
- Return ONLY the SQL query, no explanations
- Always include LIMIT for safety (default 100, max 200)
- Use parameterized queries where possible
- Return valid, executable SQLite syntax
- Use single quotes for string literals
- SQLite does not support UUID functions - use text IDs
- Table names: researchers, publications, institutions, labs, funding_records, projects, patents, collaborations, research_documents
- All tier-aware tables have access_tier column (1=researcher, 2=government, 3=industry)"""

    def generate_sql(self, user_query: str, schema_prompt: str) -> str:
        """
        Generate SQL from natural language using schema-only context.

        Returns SQL query string - data values never leave sandbox.
        """
        if not self.llm_provider:
            return self._fallback_sql(user_query)

        messages = [
            {"role": "system", "content": self._get_dialect_system_prompt()},
            {
                "role": "user",
                "content": f"{schema_prompt}\n\nUser Query: {user_query}\n\nGenerate SQL:",
            },
        ]

        try:
            response = self.llm_provider.chat(messages)
            sql: str = response.content.strip()
            sql = sql.strip("`").strip("sql").strip()
            # Audit: log LLM call for SQL generation
            try:
                audit_log_llm_call(
                    "text-to-sql",
                    messages[-1]["content"][:500],
                    {"sql": sql[:500]},
                    getattr(self.llm_provider, "model", "unknown"),
                )
            except Exception:
                logger.warning("Audit log_llm_call failed for SQL generation", exc_info=True)
            return sql
        except Exception as e:
            logger.warning(f"LLM SQL generation failed: {e}")
            return self._fallback_sql(user_query)

    def _extract_filters(self, query: str) -> Tuple[List[str], List[str]]:
        """Extract state and research area filters from natural language query."""
        query_lower = query.lower()
        matched_states = []
        matched_areas = []

        for state in _INDIAN_STATES:
            if state in query_lower:
                # Title-case the state for DB matching
                matched_states.append(state.title())

        for area in _RESEARCH_AREAS:
            if area in query_lower:
                # Use uppercase for short acronyms, title-case for others
                if len(area) <= 3:
                    matched_areas.append(area.upper())
                else:
                    matched_areas.append(area.title())

        return matched_states, matched_areas

    def _fallback_sql(self, query: str) -> str:
        """Keyword-based SQL generation fallback with WHERE clause extraction."""
        query_lower = query.lower()
        states, areas = self._extract_filters(query)

        # Determine the target table
        if any(term in query_lower for term in ["funding", "grant", "fund ", "budget", "fiscal year", "released"]):
            table = "funding_records"
        elif any(term in query_lower for term in ["project", "co-pi", "co pi", "principal investigator", "ongoing", "completed"]):
            table = "projects"
        elif any(term in query_lower for term in ["patent", "inventor", "filing", "technology transfer", "patentable"]):
            table = "patents"
        elif any(term in query_lower for term in ["collaboration", "collaborator", "partner", "network", "cross-institutional"]):
            table = "collaborations"
        elif "research document" in query_lower or "document" in query_lower:
            table = "research_documents"
        elif "researcher" in query_lower or "faculty" in query_lower or "scientist" in query_lower or "expert" in query_lower:
            table = "researchers"
        elif "lab" in query_lower or "laboratory" in query_lower:
            table = "labs"
        elif "publication" in query_lower or "paper" in query_lower or "article" in query_lower:
            table = "publications"
        elif "institution" in query_lower or "university" in query_lower:
            table = "institutions"
        else:
            # Default to researchers for people-oriented queries
            table = "researchers"

        # Build WHERE clauses from extracted filters
        conditions = []

        state_condition = ""
        area_condition = ""

        if states and table in ("researchers", "institutions", "labs"):
            state_column = "location_state" if table == "labs" else "state"
            state_conditions = []
            for state in states:
                lower_state = state.lower()
                state_conditions.append(f"LOWER({state_column}) = '{lower_state}'")
                state_code = _STATE_ABBREVIATIONS.get(lower_state)
                if state_code:
                    state_conditions.append(f"UPPER({state_column}) = '{state_code}'")
            if state_conditions:
                state_condition = "(" + " OR ".join(state_conditions) + ")"

        if areas and table in ("researchers", "labs", "projects", "patents", "collaborations"):
            search_terms = set()
            for area in areas:
                lowered = area.lower()
                search_terms.add(lowered)
                search_terms.update(term for term in lowered.split() if len(term) > 2)
            area_column = "research_focus_areas" if table == "labs" else "research_area"
            area_conditions = [f"LOWER({area_column}) LIKE '%{term}%'" for term in sorted(search_terms)]
            if area_conditions:
                area_condition = "(" + " OR ".join(area_conditions) + ")"

        if areas and table in ("publications", "research_documents"):
            search_terms = set()
            for area in areas:
                lowered = area.lower()
                search_terms.add(lowered)
                search_terms.update(term for term in lowered.split() if len(term) > 2)
            if table == "research_documents":
                area_conditions = [
                    f"(LOWER(research_area_tags) LIKE '%{term}%' OR LOWER(keywords) LIKE '%{term}%')"
                    for term in sorted(search_terms)
                ]
            else:
                area_conditions = [f"LOWER(research_area) LIKE '%{term}%'" for term in sorted(search_terms)]
            if area_conditions:
                area_condition = "(" + " OR ".join(area_conditions) + ")"

        if state_condition and area_condition and table == "researchers":
            conditions.append(f"({state_condition} OR {area_condition})")
        else:
            if state_condition:
                conditions.append(state_condition)
            if area_condition:
                conditions.append(area_condition)

        # Check for year filters
        year_match = re.search(r'\b(19|20)\d{2}\b', query)
        if year_match:
            year = year_match.group()
            if table == "researchers":
                if "after" in query_lower or "since" in query_lower:
                    conditions.append(f"year_joined >= {year}")
                elif "before" in query_lower:
                    conditions.append(f"year_joined <= {year}")
                else:
                    conditions.append(f"year_joined = {year}")
            elif table == "publications":
                if "after" in query_lower or "since" in query_lower:
                    conditions.append(f"year >= {year}")
                elif "before" in query_lower:
                    conditions.append(f"year <= {year}")
                else:
                    conditions.append(f"year = {year}")
            elif table == "research_documents":
                if "after" in query_lower or "since" in query_lower:
                    conditions.append(f"publication_year >= {year}")
                elif "before" in query_lower:
                    conditions.append(f"publication_year <= {year}")
                else:
                    conditions.append(f"publication_year = {year}")

        if "ongoing" in query_lower and table in ("projects", "collaborations"):
            conditions.append("LOWER(status) = 'ongoing'")
        elif "completed" in query_lower and table in ("projects", "collaborations"):
            conditions.append("LOWER(status) = 'completed'")

        # Check for count queries
        if "count" in query_lower or "how many" in query_lower:
            select_clause = f"SELECT COUNT(*) as count FROM {table}"
        else:
            if "top" in query_lower and table == "researchers":
                select_clause = f"SELECT * FROM {table}"
                conditions.append("h_index IS NOT NULL")
            elif "h-index" in query_lower and table == "researchers":
                select_clause = f"SELECT * FROM {table}"
                conditions.append("h_index IS NOT NULL")
            elif areas:
                select_clause = f"SELECT *, '{areas[0].lower()}' AS query_topic FROM {table}"
            else:
                select_clause = f"SELECT * FROM {table}"

        # Assemble
        if conditions:
            where_clause = " AND ".join(conditions)
            sql = f"{select_clause} WHERE {where_clause} LIMIT 100"
        else:
            sql = f"{select_clause} LIMIT 100"

        if table == "researchers" and ("top" in query_lower or "h-index" in query_lower):
            sql = sql.replace(" LIMIT 100", " ORDER BY h_index DESC LIMIT 100")

        return sql

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

        result: Dict[str, Any] = self.sandbox.execute_readonly(sql, user_tier)

        result["schema_used"] = list(schema["tables"].keys())
        result["audit_logged"] = True

        return result

    def _apply_tier_filter(self, sql: str, user_tier: int) -> str:
        """Apply access tier filter to SQL using TierAwareSqlRewriter."""
        try:
            return self._sql_rewriter.rewrite(sql, user_tier)
        except PermissionError:
            raise
        except Exception as e:
            logger.warning(f"Tier rewriter failed: {e}, using fallback")
            return self._sql_rewriter._safe_fallback(sql, user_tier)

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
