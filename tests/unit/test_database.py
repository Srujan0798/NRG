"""Unit tests for NRGDatabase using Test-Driven Development."""

import os
import sqlite3

import pytest

from src.data.database import NRGDatabase


class TestNRGDatabase:
    """Test suite for NRGDatabase class."""

    @pytest.fixture
    def test_db(self, tmp_path, monkeypatch):
        """Create a test database instance."""
        monkeypatch.setattr("src.data.database.invalidate_query_cache", lambda: 0)
        db_path = tmp_path / "test_nrg.db"

        db = NRGDatabase(str(db_path))
        db.initialize_schema()
        yield db

    def test_database_connection(self, test_db):
        """Test database connection is established."""
        conn = test_db.connect()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)

    def test_schema_initialization(self, test_db):
        """Test that schema is properly initialized."""
        with test_db.connect() as conn:
            # Check researchers table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='researchers'"
            )
            assert cursor.fetchone() is not None

            # Check institutions table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='institutions'"
            )
            assert cursor.fetchone() is not None

    def test_insert_researcher(self, test_db):
        """Test inserting a researcher."""
        researcher_id = test_db.insert_researcher(
            name="Dr. Test Researcher",
            institution_id="test-institution-001",
            state="MH",
            research_area="Test Research",
            year_joined=2023,
            email="test@example.com",
        )

        assert researcher_id is not None
        assert isinstance(researcher_id, str)
        assert len(researcher_id) == 36  # UUID length

        # Verify researcher was inserted
        researcher = test_db.get_researcher_by_id(researcher_id)
        assert researcher is not None
        assert researcher["name"] == "Dr. Test Researcher"
        assert researcher["state"] == "MH"
        assert researcher["research_area"] == "Test Research"

    def test_insert_researcher_invalidates_query_cache(self, tmp_path, monkeypatch):
        """Writes must evict cached query results after commit."""
        calls = []
        monkeypatch.setattr("src.data.database.invalidate_query_cache", lambda: calls.append("invalidate") or 1)
        db = NRGDatabase(str(tmp_path / "invalidate_insert.db"))
        db.initialize_schema()
        calls.clear()

        db.insert_researcher(
            name="Dr. Cache Writer",
            institution_id="inst-cache-001",
            state="KA",
            research_area="Cache Invalidation",
        )

        assert calls == ["invalidate"]

    def test_execute_mutating_query_invalidates_query_cache(self, tmp_path, monkeypatch):
        """Parameterized mutating SQL must evict cached query results."""
        calls = []
        monkeypatch.setattr("src.data.database.invalidate_query_cache", lambda: calls.append("invalidate") or 1)
        db = NRGDatabase(str(tmp_path / "invalidate_update.db"))
        db.initialize_schema()
        researcher_id = db.insert_researcher(
            name="Dr. Cache Update",
            institution_id="inst-cache-002",
            state="MH",
            research_area="Cache Invalidation",
        )
        calls.clear()

        db.execute_query(
            "UPDATE researchers SET state = ? WHERE researcher_id = ?",
            ("GJ", researcher_id),
        )

        assert calls == ["invalidate"]

    def test_execute_select_query_does_not_invalidate_query_cache(self, test_db, monkeypatch):
        """Read-only SQL must not evict cached query results."""
        calls = []
        monkeypatch.setattr("src.data.database.invalidate_query_cache", lambda: calls.append("invalidate") or 1)

        test_db.execute_query("SELECT * FROM researchers")

        assert calls == []

    def test_query_researchers_by_state(self, test_db):
        """Test querying researchers by state."""
        # Insert test data
        test_db.insert_researcher(
            name="Dr. Maharashtra Researcher",
            institution_id="inst-mh-001",
            state="MH",
            research_area="AI",
        )

        test_db.insert_researcher(
            name="Dr. Gujarat Researcher",
            institution_id="inst-gj-001",
            state="GJ",
            research_area="Robotics",
        )

        # Query by state
        mh_researchers = test_db.query_researchers(state="MH")
        assert len(mh_researchers) == 1
        assert mh_researchers[0]["name"] == "Dr. Maharashtra Researcher"
        assert mh_researchers[0]["state"] == "MH"

        gj_researchers = test_db.query_researchers(state="GJ")
        assert len(gj_researchers) == 1
        assert gj_researchers[0]["name"] == "Dr. Gujarat Researcher"
        assert gj_researchers[0]["state"] == "GJ"

    def test_query_researchers_by_research_area(self, test_db):
        """Test querying researchers by research area."""
        # Insert test data
        test_db.insert_researcher(
            name="Dr. AI Researcher",
            institution_id="inst-ai-001",
            state="KA",
            research_area="Artificial Intelligence",
        )

        test_db.insert_researcher(
            name="Dr. Robotics Researcher",
            institution_id="inst-rob-001",
            state="TN",
            research_area="Robotics Engineering",
        )

        # Query by research area
        ai_researchers = test_db.query_researchers(
            research_area="Artificial Intelligence"
        )
        assert len(ai_researchers) == 1
        assert ai_researchers[0]["research_area"] == "Artificial Intelligence"

        robotics_researchers = test_db.query_researchers(research_area="Robotics")
        assert len(robotics_researchers) == 1
        assert "Robotics" in robotics_researchers[0]["research_area"]

    def test_get_researcher_by_id_not_found(self, test_db):
        """Test getting a non-existent researcher returns None."""
        researcher = test_db.get_researcher_by_id("non-existent-id")
        assert researcher is None

    def test_transaction_rolls_back_on_exception(self, test_db):
        """Database helper transactions must not commit partial writes on error."""
        with pytest.raises(RuntimeError):
            with test_db.transaction() as conn:
                conn.execute(
                    """
                    INSERT INTO researchers
                    (researcher_id, name, institution_id, state)
                    VALUES (?, ?, ?, ?)
                    """,
                    ("rollback-id", "Dr Rollback", "inst-rollback", "GJ"),
                )
                raise RuntimeError("force rollback")

        assert test_db.get_researcher_by_id("rollback-id") is None

    def test_database_close(self, test_db):
        """Test database connection can be closed."""
        test_db.close()
        # Should not raise an error


if __name__ == "__main__":
    # Run tests directly for quick validation
    import tempfile

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db = NRGDatabase(db_path)
        db.initialize_schema()

        # Run basic tests
        test_instance = TestNRGDatabase()

        print("🧪 Running database tests...")

        # Test connection
        conn = db.connect()
        assert conn is not None
        print("✅ Database connection test passed")

        # Test schema
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='researchers'"
        )
        assert cursor.fetchone() is not None
        print("✅ Schema initialization test passed")

        # Test insert
        researcher_id = db.insert_researcher(
            name="Dr. Test Runner",
            institution_id="test-runner-inst",
            state="TS",
            research_area="Testing",
        )
        assert researcher_id is not None
        print("✅ Researcher insertion test passed")

        # Test query
        researchers = db.query_researchers(state="TS")
        assert len(researchers) == 1
        assert researchers[0]["name"] == "Dr. Test Runner"
        print("✅ Researcher query test passed")

        print("🎉 All database tests passed!")

    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
