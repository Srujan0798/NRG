"""Initialize the PostgreSQL database with schema."""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql

sys.path.insert(0, str(Path(__file__).parent.parent))


def init_database():
    """Initialize database with production schema."""
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://nrg_user:nrg_password@localhost:5432/nrg_research"
    )

    schema_path = Path(__file__).parent.parent / "docs" / "schema" / "researcher_db.sql"

    if not schema_path.exists():
        print(f"Schema file not found: {schema_path}")
        return False

    print(f"Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        print(f"Loading schema from: {schema_path}")
        with open(schema_path, "r") as f:
            schema_sql = f.read()

        cursor.execute(schema_sql)

        print("✓ Schema applied successfully")

        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"✓ Created {len(tables)} tables")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
