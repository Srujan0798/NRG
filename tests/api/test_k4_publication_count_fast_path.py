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
    monkeypatch.delenv("NRG_LOCAL_RESEARCH_DB", raising=False)
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


def test_common_c4_query_shapes_use_bounded_fast_path():
    queries = [
        "find robotics researchers in Gujarat",
        "labs working on renewable energy",
        "funding agencies for electronics research",
        "publication counts by institution",
        "List institutions in Gujarat",
        "technology transfer candidates",
        "researchers with h_index > 50 in computer science",
        "total researchers by state",
        "researchers open to collaboration",
    ]

    for query in queries:
        response = api_main._fast_query_response(
            query,
            user_tier=1,
            user_id="k4-test-user",
            session_id="k4-load-shapes",
        )

        assert response is not None, query
        assert response["routing_decision"] == "fast_path"
        assert response["synthesis_method"] in {"rule_based", "rule_based_read_model"}
        assert response["citations"]
        assert response["node_timings"]["executor"] == 0.0
