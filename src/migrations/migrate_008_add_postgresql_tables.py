"""
Migration 008: Add 40 missing PostgreSQL tables to dev SQLite.

This migration adds all tables from db_struct.sql that are missing from the
dev SQLite database, enabling text-to-SQL queries against the full schema.
"""

import re
import sqlite3
from pathlib import Path

NRG_ROOT = Path(__file__).resolve().parents[2]
DB_FILE = NRG_ROOT / "nrg_research.db"
DB_STRUCT = NRG_ROOT / "db_struct.sql"
MIGRATION_FILE = Path(__file__).resolve().parent / "008_add_postgresql_tables.sql"


def parse_postgres_type(pg_type: str) -> str:
    """Map PostgreSQL types to SQLite equivalents."""
    pg_type = pg_type.strip().upper()
    if pg_type.startswith("CHARACTER VARYING") or pg_type.startswith("VARCHAR"):
        match = re.search(r'\((\d+)\)', pg_type)
        return f"VARCHAR({match.group(1)})" if match else "TEXT"
    if pg_type in ("CHARACTER", "CHAR"):
        match = re.search(r'\((\d+)\)', pg_type)
        return f"CHAR({match.group(1)})" if match else "TEXT"
    if pg_type in ("TEXT", "JSON", "JSONB", "XML"):
        return "TEXT"
    if pg_type in ("BOOLEAN"):
        return "INTEGER"
    if pg_type in ("SMALLINT", "INT2"):
        return "INTEGER"
    if pg_type in ("INTEGER", "INT", "INT4", "BIGINT", "INT8", "OID"):
        return "INTEGER"
    if pg_type in ("REAL", "FLOAT4", "DOUBLE PRECISION", "FLOAT8"):
        return "REAL"
    if pg_type in ("NUMERIC", "DECIMAL", "MONEY"):
        return "REAL"
    if pg_type.startswith("TIMESTAMP"):
        return "TEXT"
    if pg_type.startswith("DATE"):
        return "TEXT"
    if pg_type.startswith("TIME"):
        return "TEXT"
    if pg_type in ("SERIAL", "BIGSERIAL"):
        return "INTEGER"
    if pg_type in ("UUID"):
        return "TEXT"
    if pg_type in ("BYTEA"):
        return "BLOB"
    if pg_type in ("NAME"):
        return "TEXT"
    return "TEXT"


def extract_columns(body: str) -> list[tuple[str, str, str]]:
    """Extract (name, type, nullable) from column definitions."""
    columns = []
    for line in body.split('\n'):
        line = line.strip().strip(',')
        if not line or line.startswith('--') or line.startswith('CONSTRAINT'):
            continue
        if line.startswith('FOREIGN KEY') or line.startswith('PRIMARY KEY') or line.startswith('UNIQUE'):
            continue
        if line.startswith('CHECK') or line.startswith('INDEX'):
            continue
        match = re.match(r'^(\w+)\s+(.+?)(?:,\s*$|$)', line)
        if match:
            name = match.group(1)
            type_def = match.group(2).rstrip(',').strip()
            col_type = parse_postgres_type(type_def)
            nullable = "NOT NULL" not in type_def.upper() and "DEFAULT" not in type_def.upper()
            columns.append((name, col_type, nullable))
    return columns


def generate_create_sql(table_name: str, body: str) -> str:
    """Generate a SQLite CREATE TABLE statement from PostgreSQL definition."""
    columns = extract_columns(body)

    if not columns:
        return f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY);"

    parts = []
    for name, col_type, nullable in columns:
        part = f'    "{name}" {col_type}'
        parts.append(part)

    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n" + ",\n".join(parts) + "\n);"


def parse_db_struct() -> dict[str, str]:
    """Parse db_struct.sql and return table_name -> CREATE SQL mapping."""
    with open(DB_STRUCT, 'r', encoding='utf-8') as f:
        content = f.read()

    tables = {}
    pattern = re.compile(
        r'CREATE TABLE public\.(\w+)\s*\((.*?)\);',
        re.DOTALL | re.IGNORECASE
    )

    for match in pattern.finditer(content):
        table_name = match.group(1)
        body = match.group(2)
        sql = generate_create_sql(table_name, body)
        tables[table_name] = sql

    return tables


def get_existing_tables(db_path: Path) -> set[str]:
    """Get set of existing table names in SQLite."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = {r[0] for r in cursor.fetchall()}
    conn.close()
    return tables


def run_migration():
    """Run the migration."""
    print(f"Reading schema from: {DB_STRUCT}")
    tables = parse_db_struct()
    print(f"Found {len(tables)} tables in db_struct.sql")

    existing = get_existing_tables(DB_FILE)
    print(f"Current SQLite tables: {len(existing)}")

    to_create = {name: sql for name, sql in tables.items() if name not in existing}
    print(f"Tables to create: {len(to_create)}")

    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()

    for name in sorted(to_create.keys()):
        sql = to_create[name]
        print(f"  Creating: {name}")
        try:
            cursor.execute(sql)
        except Exception as e:
            print(f"    ERROR: {e}")

    cursor.execute(
        "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (8, datetime('now'))"
    )

    conn.commit()
    conn.close()

    print(f"\nMigration complete. Created {len(to_create)} tables.")
    print(f"Total tables in DB now: {len(get_existing_tables(DB_FILE))}")

    migration_sql = "\n\n".join(to_create.values())
    MIGRATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    MIGRATION_FILE.write_text(migration_sql, encoding='utf-8')
    print(f"Migration SQL written to: {MIGRATION_FILE}")


if __name__ == "__main__":
    run_migration()