"""Schema Sync Check — Compare live DB schema against db_struct.sql for drift detection.

This module provides functionality to detect schema drift between the authoritative
db_struct.sql (PostgreSQL) and the actual live database schema.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

_NRG_ROOT = Path(__file__).resolve().parents[3]
DB_STRUCT_PATH = _NRG_ROOT / "db_struct.sql"


@dataclass
class ColumnDef:
    name: str
    data_type: str
    nullable: bool = True
    default: Optional[str] = None
    is_primary_key: bool = False


@dataclass
class TableDef:
    name: str
    columns: List[ColumnDef] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    sequences: List[str] = field(default_factory=list)


@dataclass
class SchemaDiff:
    table_name: str
    missing_tables: List[str] = field(default_factory=list)
    extra_tables: List[str] = field(default_factory=list)
    missing_columns: Dict[str, List[str]] = field(default_factory=dict)
    extra_columns: Dict[str, List[str]] = field(default_factory=dict)
    type_mismatches: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    nullable_mismatches: Dict[str, bool] = field(default_factory=dict)


def parse_db_struct_sql(sql_path: Path = DB_STRUCT_PATH) -> Dict[str, TableDef]:
    """Parse db_struct.sql to extract table definitions.

    Returns dict mapping table_name -> TableDef.
    """
    content = sql_path.read_text(encoding="utf-8")
    tables: Dict[str, TableDef] = {}

    create_table_pattern = re.compile(
        r"CREATE TABLE\s+public\.(\w+)\s*\((.*?)\);",
        re.DOTALL | re.IGNORECASE,
    )

    for match in create_table_pattern.finditer(content):
        table_name = match.group(1)
        table_body = match.group(2)

        columns: List[ColumnDef] = []
        primary_keys: List[str] = []
        foreign_keys: List[Dict[str, str]] = []
        sequences: List[str] = []

        for line in table_body.split("\n"):
            line = line.strip().rstrip(",")
            if not line:
                continue

            if line.upper().startswith("PRIMARY KEY"):
                pk_match = re.match(r"PRIMARY KEY\s*\((.+?)\)", line, re.IGNORECASE)
                if pk_match:
                    pk_cols = [c.strip().strip('"') for c in pk_match.group(1).split(",")]
                    primary_keys.extend(pk_cols)
                continue

            if line.upper().startswith("FOREIGN KEY"):
                fk_match = re.match(
                    r"FOREIGN KEY\s*\((.+?)\)\s*REFERENCES\s+(\w+)\s*\((.+?)\)",
                    line,
                    re.IGNORECASE,
                )
                if fk_match:
                    from_col = fk_match.group(1).strip().strip('"')
                    to_table = fk_match.group(2).strip()
                    to_col = fk_match.group(3).strip().strip('"')
                    foreign_keys.append(
                        {
                            "column": from_col,
                            "references_table": to_table,
                            "references_column": to_col,
                        }
                    )
                continue

            if line.upper().startswith("CONSTRAINT"):
                continue

            col_match = re.match(r'"?(\w+)"?\s+(.+)', line, re.IGNORECASE)
            if col_match:
                col_name = col_match.group(1)
                col_type, col_rest = _split_column_type(col_match.group(2))

                nullable = "NOT NULL" not in col_rest.upper()
                default = None
                if "DEFAULT" in col_rest.upper():
                    def_match = re.search(
                        r"DEFAULT\s+([^\s,]+)", col_rest, re.IGNORECASE
                    )
                    if def_match:
                        default = def_match.group(1)

                columns.append(
                    ColumnDef(
                        name=col_name,
                        data_type=col_type,
                        nullable=nullable,
                        default=default,
                    )
                )

        for seq_match in re.finditer(
            r"CREATE SEQUENCE\s+public\.(\w+)", content, re.IGNORECASE
        ):
            seq_name = seq_match.group(1)
            if seq_name.startswith(f"{table_name}_"):
                sequences.append(seq_name)

        tables[table_name] = TableDef(
            name=table_name,
            columns=columns,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
            sequences=sequences,
        )

    return tables


def _split_column_type(column_tail: str) -> tuple[str, str]:
    """Split a PostgreSQL column definition into type and trailing constraints."""
    match = re.split(
        r"\s+(DEFAULT|NOT\s+NULL|NULL|COLLATE|CONSTRAINT|PRIMARY|REFERENCES|CHECK|UNIQUE)\b",
        column_tail,
        maxsplit=1,
        flags=re.IGNORECASE,
    )
    column_type = match[0].strip()
    column_rest = ""
    if len(match) > 1:
        column_rest = " ".join(part for part in match[1:] if part).strip()
    return column_type, column_rest


def get_live_table_names(engine) -> List[str]:
    """Get all table names from live database."""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    return inspector.get_table_names()


def get_live_table_columns(engine, table_name: str) -> List[ColumnDef]:
    """Get column definitions from live database."""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)

    return [
        ColumnDef(
            name=col["name"],
            data_type=str(col["type"]),
            nullable=col["nullable"],
            default=str(col.get("default")) if col.get("default") else None,
        )
        for col in columns
    ]


def get_live_primary_keys(engine, table_name: str) -> List[str]:
    """Get primary key columns from live database."""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    pk_constraint = inspector.get_pk_constraint(table_name)
    return pk_constraint.get("constrained_columns", [])


def get_live_foreign_keys(engine, table_name: str) -> List[Dict[str, str]]:
    """Get foreign key definitions from live database."""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    fks = inspector.get_foreign_keys(table_name)

    return [
        {
            "column": fk["constrained_columns"][0],
            "references_table": fk["referred_table"],
            "references_column": fk["referred_columns"][0],
        }
        for fk in fks
    ]


def check_schema_sync(
    engine, authoritative_schema: Optional[Dict[str, TableDef]] = None
) -> SchemaDiff:
    """Compare live DB schema against authoritative db_struct.sql.

    Args:
        engine: SQLAlchemy engine connected to live database
        authoritative_schema: Pre-parsed schema (optional, will parse if not provided)

    Returns:
        SchemaDiff with all discrepancies found
    """
    if authoritative_schema is None:
        authoritative_schema = parse_db_struct_sql()

    live_table_names = get_live_table_names(engine)
    authorative_table_names = set(authoritative_schema.keys())

    diff = SchemaDiff(table_name="")

    live_table_set = set(live_table_names)
    auth_table_set = authorative_table_names

    # Live DBs may contain app-owned operational tables in addition to the
    # canonical db_struct.sql source tables. Report them, but do not treat them
    # as blocking drift; missing canonical tables still fail.
    diff.extra_tables = sorted(live_table_set - auth_table_set)
    diff.missing_tables = sorted(auth_table_set - live_table_set)

    common_tables = live_table_set & auth_table_set

    for table_name in common_tables:
        auth_table = authoritative_schema[table_name]
        live_columns = get_live_table_columns(engine, table_name)

        auth_col_map = {col.name: col for col in auth_table.columns}
        live_col_map = {col.name: col for col in live_columns}

        auth_col_names = set(auth_col_map.keys())
        live_col_names = set(live_col_map.keys())

        extra_cols = live_col_names - auth_col_names
        missing_cols = auth_col_names - live_col_names

        if extra_cols:
            diff.extra_columns[table_name] = sorted(extra_cols)
        if missing_cols:
            diff.missing_columns[table_name] = sorted(missing_cols)

        for col_name in auth_col_names & live_col_names:
            auth_col = auth_col_map[col_name]
            live_col = live_col_map[col_name]

            auth_type = normalize_type(auth_col.data_type)
            live_type = normalize_type(live_col.data_type)

            if auth_type != live_type:
                diff.type_mismatches[f"{table_name}.{col_name}"] = (
                    auth_type,
                    live_type,
                )

            if auth_col.nullable != live_col.nullable:
                diff.nullable_mismatches[f"{table_name}.{col_name}"] = live_col.nullable

    return diff


def normalize_type(data_type: str) -> str:
    """Normalize PostgreSQL data type for comparison."""
    dt = data_type.upper().strip()

    dt = re.sub(r"CHARACTER VARYING", "VARCHAR", dt)
    dt = re.sub(r"WITHOUT TIME ZONE", "", dt)
    dt = re.sub(r"WITH TIME ZONE", "", dt)
    dt = re.sub(r"\s+", "", dt)
    dt = re.sub(r"\(\)", "", dt)

    return dt


def format_diff_report(diff: SchemaDiff) -> str:
    """Format schema diff into human-readable report."""
    lines = ["SCHEMA SYNC REPORT", "=" * 60, ""]

    has_blocking_issues = (
        diff.missing_tables
        or diff.missing_columns
        or diff.extra_columns
        or diff.type_mismatches
    )

    if not has_blocking_issues:
        lines.append("✅ No blocking schema drift detected — live DB covers db_struct.sql")
        if diff.extra_tables:
            lines.append("")
            lines.append(f"ℹ️ EXTRA TABLES in live DB (application-owned, OK) ({len(diff.extra_tables)}):")
            for table in diff.extra_tables:
                lines.append(f"   + {table}")
        return "\n".join(lines)

    if diff.missing_tables:
        lines.append(f"❌ MISSING TABLES ({len(diff.missing_tables)}):")
        for table in diff.missing_tables:
            lines.append(f"   - {table}")
        lines.append("")

    if diff.extra_tables:
        lines.append(f"ℹ️ EXTRA TABLES in live DB (application-owned, OK) ({len(diff.extra_tables)}):")
        for table in diff.extra_tables:
            lines.append(f"   + {table}")
        lines.append("")

    if diff.missing_columns:
        lines.append(f"❌ MISSING COLUMNS ({len(diff.missing_columns)} tables):")
        for table, cols in sorted(diff.missing_columns.items()):
            lines.append(f"   {table}: {', '.join(cols)}")
        lines.append("")

    if diff.extra_columns:
        lines.append(f"⚠️ EXTRA COLUMNS in live DB ({len(diff.extra_columns)} tables):")
        for table, cols in sorted(diff.extra_columns.items()):
            lines.append(f"   {table}: {', '.join(cols)}")
        lines.append("")

    if diff.type_mismatches:
        lines.append(
            f"⚠️ TYPE MISMATCHES ({len(diff.type_mismatches)} columns):"
        )
        for col_path, (auth_type, live_type) in sorted(diff.type_mismatches.items()):
            lines.append(f"   {col_path}: expected {auth_type}, got {live_type}")
        lines.append("")

    if diff.nullable_mismatches:
        lines.append(
            f"⚠️ NULLABLE MISMATCHES ({len(diff.nullable_mismatches)} columns):"
        )
        for col_path, is_nullable in sorted(diff.nullable_mismatches.items()):
            lines.append(f"   {col_path}: nullable={is_nullable}")
        lines.append("")

    return "\n".join(lines)


def check_schema_sync_from_env() -> Tuple[bool, str]:
    """Check schema sync using DATABASE_URL environment variable.

    Returns:
        Tuple of (success: bool, report: str)
    """
    from sqlalchemy import create_engine

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return False, "DATABASE_URL environment variable not set"

    try:
        engine = create_engine(database_url, echo=False)
        diff = check_schema_sync(engine)
        report = format_diff_report(diff)

        success = not (
            diff.missing_tables
            or diff.missing_columns
            or diff.extra_columns
            or diff.type_mismatches
        )

        return success, report
    except Exception as e:
        return False, f"Error connecting to database: {e}"


def get_table_count_from_db_struct() -> int:
    """Get total table count from db_struct.sql."""
    schema = parse_db_struct_sql()
    return len(schema)


def get_dhairya_required_tables() -> Set[str]:
    """Return tables required for Dhairya benchmark queries."""
    return {
        "academic_courses_details",
        "innovation_grant_from_govt",
        "trl_stages",
        "combined_ipo_patent_data",
        "incubation_details",
        "financial_expenses_capital",
        "financial_expenses_operational",
    }


if __name__ == "__main__":
    import sys

    success, report = check_schema_sync_from_env()
    print(report)
    sys.exit(0 if success else 1)
