from __future__ import annotations

from sqlalchemy import create_engine, text

from scripts.seed_local_quality_fixtures import seed_quality_fixtures


def _count(engine, table: str) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one())


def test_seed_quality_fixtures_populates_empty_core_tables(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'quality-fixtures.sqlite'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE actual_student_strength (id INTEGER PRIMARY KEY, institute TEXT, program TEXT, male_students INTEGER, female_students INTEGER, total_students INTEGER, as_on_year TEXT)"))
        conn.execute(text("CREATE TABLE tb_institute_mstr (id INTEGER PRIMARY KEY, institute_name TEXT, short_name TEXT, institute_type TEXT, city TEXT, state TEXT, established_year INTEGER, website_url TEXT)"))

    report = seed_quality_fixtures(
        engine,
        min_rows=3,
        tables={"actual_student_strength", "tb_institute_mstr"},
        refresh_freshness=False,
    )

    assert _count(engine, "actual_student_strength") == 3
    assert _count(engine, "tb_institute_mstr") == 3
    assert report["actual_student_strength"]["inserted"] == 3
    assert report["tb_institute_mstr"]["inserted"] == 3


def test_seed_quality_fixtures_only_tops_up_existing_rows(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'quality-fixtures-existing.sqlite'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE sanctioned_intake (id INTEGER PRIMARY KEY, institute TEXT, program TEXT, financial_year TEXT, seats INTEGER, as_on_year TEXT)"))
        conn.execute(text("INSERT INTO sanctioned_intake (id, institute, program, financial_year, seats, as_on_year) VALUES (1, 'IIT Bombay', 'UG', '2024-25', 500, '2026')"))

    report = seed_quality_fixtures(
        engine,
        min_rows=3,
        tables={"sanctioned_intake"},
        refresh_freshness=False,
    )

    assert _count(engine, "sanctioned_intake") == 3
    assert report["sanctioned_intake"]["before"] == 1
    assert report["sanctioned_intake"]["inserted"] == 2
