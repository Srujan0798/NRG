import sqlite3

from scripts.seed_relations import seed_relations


def test_seed_relations_supports_current_sqlite_schema(tmp_path):
    db_path = tmp_path / "nrg_research.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE researchers (
            researcher_id TEXT PRIMARY KEY
        );
        CREATE TABLE publications (
            publication_id TEXT PRIMARY KEY
        );
        CREATE TABLE labs (
            lab_id TEXT PRIMARY KEY
        );
        CREATE TABLE keywords (
            keyword_id INTEGER PRIMARY KEY,
            keyword TEXT NOT NULL
        );
        CREATE TABLE researcher_publications (
            researcher_id TEXT NOT NULL,
            publication_id TEXT NOT NULL,
            author_order INTEGER,
            PRIMARY KEY (researcher_id, publication_id)
        );
        CREATE TABLE publication_keywords (
            publication_id TEXT NOT NULL,
            keyword_id INTEGER NOT NULL,
            PRIMARY KEY (publication_id, keyword_id)
        );
        CREATE TABLE researcher_labs (
            researcher_id TEXT NOT NULL,
            lab_id TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            role TEXT,
            PRIMARY KEY (researcher_id, lab_id)
        );
        """
    )
    conn.executemany(
        "INSERT INTO researchers (researcher_id) VALUES (?)",
        [(f"r{i}",) for i in range(1, 4)],
    )
    conn.executemany(
        "INSERT INTO publications (publication_id) VALUES (?)",
        [(f"p{i}",) for i in range(1, 5)],
    )
    conn.executemany(
        "INSERT INTO labs (lab_id) VALUES (?)",
        [(f"l{i}",) for i in range(1, 3)],
    )
    conn.commit()
    conn.close()

    seed_relations(str(db_path))

    conn = sqlite3.connect(db_path)
    try:
        for table in (
            "keywords",
            "researcher_publications",
            "publication_keywords",
            "researcher_labs",
        ):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert count > 0, table

        migration = conn.execute(
            "SELECT applied_at FROM schema_migrations WHERE version = ?",
            ("seed_relations_001",),
        ).fetchone()
        assert migration is not None
    finally:
        conn.close()
