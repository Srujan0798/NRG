"""Tests for database_v2 SQLAlchemy ORM layer."""

import pytest

from src.data.database_v2 import Institution, Lab, NRGDatabase, Publication, Researcher


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test_v2.db")
    url = f"sqlite:///{db_path}"
    database = NRGDatabase(url=url)
    database.create_tables()
    with database.get_session() as session:
        inst = Institution(institution_id="inst1", name="IITGN", state="GJ", type="university")
        session.add(inst)
        inst2 = Institution(institution_id="inst2", name="IISc", state="KA", type="research_institute")
        session.add(inst2)
        researcher = Researcher(
            researcher_id="r1", name="Dr Test", institution_id="inst1",
            state="GJ", research_area="AI", year_joined=2020,
            email="test@iitgn.ac.in", access_tier=1,
        )
        session.add(researcher)
        researcher2 = Researcher(
            researcher_id="r2", name="Dr Other", institution_id="inst2",
            state="KA", research_area="ML", year_joined=2019,
            email="other@iisc.ac.in", access_tier=2,
        )
        session.add(researcher2)
        pub = Publication(
            publication_id="p1", title="Test Paper", abstract="Abstract",
            year=2024, access_tier=1,
        )
        session.add(pub)
        pub2 = Publication(
            publication_id="p2", title="Old Paper", abstract="Old",
            year=2020, access_tier=2,
        )
        session.add(pub2)
        lab = Lab(lab_id="l1", name="AI Lab", institution_id="inst1")
        session.add(lab)
        session.commit()
    yield database
    database.engine.dispose()


class TestNRGDatabaseV2:
    def test_dialect_sqlite(self, db):
        assert db.dialect == "sqlite"

    def test_get_stats(self, db):
        stats = db.get_stats()
        assert stats["researchers"] == 2
        assert stats["publications"] == 2
        assert stats["institutions"] == 2
        assert stats["labs"] == 1
        assert len(stats["research_areas"]) > 0

    def test_query_researchers_all(self, db):
        results = db.query_researchers()
        assert len(results) == 2

    def test_query_researchers_by_state(self, db):
        results = db.query_researchers(state="GJ")
        assert len(results) == 1
        assert results[0]["name"] == "Dr Test"
        results = db.query_researchers(state="MH")
        assert len(results) == 0

    def test_query_researchers_by_area(self, db):
        results = db.query_researchers(research_area="AI")
        assert len(results) == 1

    def test_query_publications_all(self, db):
        results = db.query_publications()
        assert len(results) == 2

    def test_query_publications_by_year(self, db):
        results = db.query_publications(year=2024)
        assert len(results) == 1
        assert results[0]["title"] == "Test Paper"
        results = db.query_publications(year=2019)
        assert len(results) == 0

    def test_query_publications_limit(self, db):
        results = db.query_publications(limit=1)
        assert len(results) == 1

    def test_execute_raw_query(self, db):
        results = db.execute("SELECT COUNT(*) as cnt FROM researchers")
        assert len(results) == 1

    def test_get_session(self, db):
        with db.get_session() as session:
            count = session.query(Researcher).count()
            assert count == 2

    def test_get_session_rolls_back_partial_write_on_exception(self, db):
        with pytest.raises(RuntimeError):
            with db.get_session() as session:
                session.add(
                    Researcher(
                        researcher_id="rollback-r",
                        name="Dr Rollback",
                        institution_id="inst1",
                        state="GJ",
                    )
                )
                raise RuntimeError("force rollback")

        with db.get_session() as session:
            assert session.query(Researcher).filter_by(researcher_id="rollback-r").count() == 0

    def test_create_tables_idempotent(self, db):
        db.create_tables()
        with db.get_session() as session:
            count = session.query(Researcher).count()
            assert count == 2

    def test_default_url(self):
        db = NRGDatabase(url="sqlite:///:memory:")
        db.create_tables()
        stats = db.get_stats()
        assert stats["researchers"] == 0
        db.engine.dispose()
