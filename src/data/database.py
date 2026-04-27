"""Database Management for National Research Graph."""

import os
import sqlite3
from pathlib import Path
from typing import Optional
import uuid

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "sqlite:///nrg_research.db"


def resolve_database_path(db_path: Optional[str] = None) -> Path:
    """Resolve SQLite DB paths deterministically from DATABASE_URL or repo root.

    When DATABASE_URL points to PostgreSQL, falls back to a local SQLite file
    for components that require SQLite (e.g., refresh token store).
    """
    if db_path:
        raw_path = db_path
    else:
        raw_path = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
        # If main DB is PostgreSQL, use a dedicated SQLite sidecar
        if raw_path and raw_path.startswith("postgresql://"):
            raw_path = os.getenv("NRG_AUTH_DB_PATH", "sqlite:///nrg_auth.db")

    if raw_path is None:
        raw_path = DEFAULT_DATABASE_URL

    if raw_path.startswith("sqlite:///"):
        raw_path = raw_path[len("sqlite:///") :]
    elif "://" in raw_path:
        raise ValueError(f"Unsupported DATABASE_URL for SQLite connection: {raw_path}")

    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def get_sqlite_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Open a SQLite connection using the canonical project DB resolver."""
    path = resolve_database_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


class NRGDatabase:
    """SQLite database manager for National Research Graph."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = resolve_database_path(db_path)
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Connect to SQLite database."""
        conn = get_sqlite_connection(str(self.db_path))
        conn.row_factory = sqlite3.Row
        self.conn = conn
        return conn

    def initialize_schema(self) -> None:
        """Initialize the database schema."""
        schema_path = Path(__file__).parent / "schema" / "optimized_schema.sql"

        with self.connect() as conn:
            with open(schema_path, "r") as f:
                schema_sql = f.read()

            conn.executescript(schema_sql)

    def insert_researcher(
        self,
        name: str,
        institution_id: str,
        state: str,
        research_area: Optional[str] = None,
        year_joined: Optional[int] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        orcid: Optional[str] = None,
    ) -> str:
        """Insert a researcher record."""
        researcher_id = str(uuid.uuid4())

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO researchers 
                (researcher_id, name, institution_id, state, research_area, 
                 year_joined, email, phone, orcid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    researcher_id,
                    name,
                    institution_id,
                    state,
                    research_area,
                    year_joined,
                    email,
                    phone,
                    orcid,
                ),
            )

        return researcher_id

    def query_researchers(
        self, state: Optional[str] = None, research_area: Optional[str] = None, institution_id: Optional[str] = None
    ) -> list:
        """Query researchers with filters."""
        query = "SELECT * FROM researchers WHERE 1=1"
        params = []

        if state:
            query += " AND state = ?"
            params.append(state)

        if research_area:
            query += " AND research_area LIKE ?"
            params.append(f"%{research_area}%")

        if institution_id:
            query += " AND institution_id = ?"
            params.append(institution_id)

        with self.connect() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        """Execute a parameterized SQL query safely.

        Args:
            query: SQL query with ? placeholders
            params: Tuple of parameter values

        Returns:
            List of dict rows
        """
        with self.connect() as conn:
            if params:
                cursor = conn.execute(query, params)
            else:
                cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def get_researcher_by_id(self, researcher_id: str) -> Optional[dict]:
        """Get researcher by ID."""
        with self.connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM researchers WHERE researcher_id = ?", (researcher_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    """Test the database functionality."""
    db = NRGDatabase()

    try:
        # Initialize schema
        db.initialize_schema()
        print("✅ Database schema initialized")

        # Insert test data
        researcher_id = db.insert_researcher(
            name="Dr. Rajesh Kumar",
            institution_id=str(uuid.uuid4()),
            state="GJ",
            research_area="Robotics",
            year_joined=2020,
            email="rajesh.kumar@iitgn.ac.in",
        )
        print(f"✅ Researcher inserted: {researcher_id}")

        # Query researchers
        researchers = db.query_researchers(state="GJ", research_area="Robotics")
        print(f"✅ Found {len(researchers)} researchers in Gujarat working on Robotics")

        # Get specific researcher
        researcher = db.get_researcher_by_id(researcher_id)
        print(
            f"✅ Researcher details: {researcher['name']} - {researcher['research_area']}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
