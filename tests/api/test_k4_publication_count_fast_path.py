import sqlite3

import src.api.main as api_main


def test_publication_count_fast_path_counts_iit_papers_from_local_sqlite(tmp_path, monkeypatch):
    db_dir = tmp_path / "data"
    db_dir.mkdir()
    db_path = db_dir / "nrg_research.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE publications (
                publication_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER
            );
            CREATE TABLE researcher_publications (
                researcher_id TEXT,
                publication_id TEXT
            );
            CREATE TABLE researchers (
                researcher_id TEXT PRIMARY KEY,
                institution_id TEXT
            );
            CREATE TABLE institutions (
                institution_id TEXT PRIMARY KEY,
                name TEXT
            );
            INSERT INTO publications VALUES
                ('p1', 'IIT paper', 'A', 2023),
                ('p2', 'IISc paper', 'B', 2023),
                ('p3', 'IIT old paper', 'C', 2022);
            INSERT INTO institutions VALUES
                ('i1', 'IIT Gandhinagar'),
                ('i2', 'IISc Bengaluru');
            INSERT INTO researchers VALUES
                ('r1', 'i1'),
                ('r2', 'i2');
            INSERT INTO researcher_publications VALUES
                ('r1', 'p1'),
                ('r2', 'p2'),
                ('r1', 'p3');
            """
        )

    monkeypatch.setattr(api_main, "REPO_ROOT", tmp_path)
    api_main._publication_count_cache.clear()

    response = api_main._publication_count_fast_response(
        "How many IIT papers published in 2023?",
        user_tier=1,
        session_id="k4-test",
    )

    assert response is not None
    assert response["routing_decision"] == "fast_path"
    assert response["intent"] == "publication_count"
    assert response["sql_results"] == [
        {"year": 2023, "scope": "IIT-linked", "publication_count": 1}
    ]
    assert "1 IIT-linked papers" in response["response"]
