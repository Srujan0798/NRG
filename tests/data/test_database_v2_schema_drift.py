"""Regression coverage for schema-drift tolerant API data access."""

from pathlib import Path

from sqlalchemy import text

from src.data.database_v2 import NRGDatabase


def test_query_researchers_falls_back_when_orm_columns_are_missing(tmp_path: Path):
    """The live handover DB may miss legacy ORM columns; /researchers must not 500."""
    db = NRGDatabase(f"sqlite:///{tmp_path / 'schema_drift.db'}")
    with db.engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE researchers (
                    researcher_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    state TEXT,
                    research_area TEXT,
                    email TEXT,
                    phone TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO researchers
                    (researcher_id, name, state, research_area, email, phone)
                VALUES
                    ('r-1', 'Dr. Schema Drift', 'Gujarat', 'Robotics',
                     'schema@example.edu', '+91-9999999999')
                """
            )
        )

    rows = db.query_researchers(state="Gujarat", research_area="Robotics")

    assert rows == [
        {
            "researcher_id": "r-1",
            "name": "Dr. Schema Drift",
            "institution_id": None,
            "department": None,
            "state": "Gujarat",
            "research_area": "Robotics",
            "secondary_research_areas": None,
            "years_experience": None,
            "year_joined": None,
            "h_index": None,
            "total_funding_received_inr_crores": None,
            "email": "schema@example.edu",
            "phone": "+91-9999999999",
            "orcid": None,
        }
    ]
