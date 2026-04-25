#!/usr/bin/env python3
"""Seed deterministic demo data for the four NRG killer queries.

The committed fixture is intentionally small, readable, and deterministic. The
SQLite seeding path writes demo_* tables so rehearsal checks can validate row
counts without mutating production-shaped tables unless an operator explicitly
uses this script against a chosen database.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURE = Path(__file__).with_name("seed_data.json")
DEFAULT_DATABASE = REPO_ROOT / "nrg_research.db"


def load_seed_data(path: Path | str = DEFAULT_FIXTURE) -> dict[str, Any]:
    """Load the deterministic demo fixture."""
    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_killer_query_results(data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the four canonical killer-query result sets plus graph evidence."""
    source = data or load_seed_data()
    solar_rows = sorted(
        source["solar_seed_patents"],
        key=lambda row: (-row["patent_count"], row["first_patent_months"], row["researcher"]),
    )
    median_patents = statistics.median(row["patent_count"] for row in solar_rows)
    median_months = statistics.median(row["first_patent_months"] for row in solar_rows)

    return {
        "top_funding_agencies": sorted(
            source["funding_agencies"],
            key=lambda row: row["amount_inr_crore"],
            reverse=True,
        )[:5],
        "trl_progression": sorted(
            source["trl_progression"],
            key=lambda row: (row["latest_trl"] - row["starting_trl"], row["latest_trl"], row["institution"]),
            reverse=True,
        ),
        "solar_seed_to_patents": {
            "researchers": solar_rows,
            "median_patents_per_researcher": median_patents,
            "median_months_to_first_patent": median_months,
            "total_patents": sum(row["patent_count"] for row in solar_rows),
            "seed_cohort_size": len(solar_rows),
        },
        "iit_b_vs_iit_m_ai_ml": sorted(
            source["iit_ai_ml_comparison"],
            key=lambda row: (row["year"], row["institution"]),
        ),
        "demo_graph": source["demo_graph"],
    }


def _connect(db_path: Path | str) -> sqlite3.Connection:
    path = Path(db_path)
    if str(path.parent) not in {"", "."}:
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def seed_sqlite(db_path: Path | str = DEFAULT_DATABASE, fixture_path: Path | str = DEFAULT_FIXTURE) -> dict[str, int]:
    """Create and populate demo_* tables from the deterministic fixture."""
    data = load_seed_data(fixture_path)
    conn = _connect(db_path)
    try:
        _create_demo_tables(conn)
        _clear_demo_tables(conn)
        _insert_demo_rows(conn, data)
        conn.commit()
        return _demo_table_counts(conn)
    finally:
        conn.close()


def _create_demo_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS demo_funding_agencies (
            agency TEXT PRIMARY KEY,
            amount_inr_crore REAL NOT NULL,
            distinct_institutes INTEGER NOT NULL,
            projects INTEGER NOT NULL,
            lead_institute TEXT NOT NULL,
            focus TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS demo_trl_progression (
            institution TEXT NOT NULL,
            state TEXT NOT NULL,
            project TEXT NOT NULL,
            domain TEXT NOT NULL,
            transition_year INTEGER NOT NULL,
            trl INTEGER NOT NULL,
            milestone TEXT NOT NULL,
            starting_trl INTEGER NOT NULL,
            latest_trl INTEGER NOT NULL,
            PRIMARY KEY (institution, project, transition_year, trl)
        );

        CREATE TABLE IF NOT EXISTS demo_solar_seed_patents (
            researcher TEXT PRIMARY KEY,
            institution TEXT NOT NULL,
            state TEXT NOT NULL,
            seed_year INTEGER NOT NULL,
            seed_funding_inr_lakh REAL NOT NULL,
            patent_count INTEGER NOT NULL,
            first_patent_months INTEGER NOT NULL,
            core_patent TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS demo_iit_ai_ml_comparison (
            year INTEGER NOT NULL,
            institution TEXT NOT NULL,
            grant_amount_inr_crore REAL NOT NULL,
            publications INTEGER NOT NULL,
            patents INTEGER NOT NULL,
            active_researchers INTEGER NOT NULL,
            PRIMARY KEY (year, institution)
        );

        CREATE TABLE IF NOT EXISTS demo_graph_nodes (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            type TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS demo_graph_edges (
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            weight REAL NOT NULL,
            relationship TEXT NOT NULL,
            PRIMARY KEY (source, target, relationship)
        );
        """
    )


def _clear_demo_tables(conn: sqlite3.Connection) -> None:
    for table in (
        "demo_funding_agencies",
        "demo_trl_progression",
        "demo_solar_seed_patents",
        "demo_iit_ai_ml_comparison",
        "demo_graph_edges",
        "demo_graph_nodes",
    ):
        conn.execute(f"DELETE FROM {table}")


def _insert_demo_rows(conn: sqlite3.Connection, data: dict[str, Any]) -> None:
    conn.executemany(
        """
        INSERT INTO demo_funding_agencies
        (agency, amount_inr_crore, distinct_institutes, projects, lead_institute, focus)
        VALUES (:agency, :amount_inr_crore, :distinct_institutes, :projects, :lead_institute, :focus)
        """,
        data["funding_agencies"],
    )

    trl_rows: list[dict[str, Any]] = []
    for item in data["trl_progression"]:
        for transition in item["transitions"]:
            trl_rows.append(
                {
                    "institution": item["institution"],
                    "state": item["state"],
                    "project": item["project"],
                    "domain": item["domain"],
                    "transition_year": transition["year"],
                    "trl": transition["trl"],
                    "milestone": transition["milestone"],
                    "starting_trl": item["starting_trl"],
                    "latest_trl": item["latest_trl"],
                }
            )
    conn.executemany(
        """
        INSERT INTO demo_trl_progression
        (institution, state, project, domain, transition_year, trl, milestone, starting_trl, latest_trl)
        VALUES
        (:institution, :state, :project, :domain, :transition_year, :trl, :milestone, :starting_trl, :latest_trl)
        """,
        trl_rows,
    )

    conn.executemany(
        """
        INSERT INTO demo_solar_seed_patents
        (researcher, institution, state, seed_year, seed_funding_inr_lakh, patent_count, first_patent_months, core_patent)
        VALUES
        (:researcher, :institution, :state, :seed_year, :seed_funding_inr_lakh, :patent_count, :first_patent_months, :core_patent)
        """,
        data["solar_seed_patents"],
    )

    conn.executemany(
        """
        INSERT INTO demo_iit_ai_ml_comparison
        (year, institution, grant_amount_inr_crore, publications, patents, active_researchers)
        VALUES
        (:year, :institution, :grant_amount_inr_crore, :publications, :patents, :active_researchers)
        """,
        data["iit_ai_ml_comparison"],
    )

    conn.executemany(
        "INSERT INTO demo_graph_nodes (id, label, type) VALUES (:id, :label, :type)",
        data["demo_graph"]["nodes"],
    )
    conn.executemany(
        "INSERT INTO demo_graph_edges (source, target, weight, relationship) VALUES (:source, :target, :weight, :relationship)",
        data["demo_graph"]["edges"],
    )


def _demo_table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in (
        "demo_funding_agencies",
        "demo_trl_progression",
        "demo_solar_seed_patents",
        "demo_iit_ai_ml_comparison",
        "demo_graph_nodes",
        "demo_graph_edges",
    ):
        counts[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    return counts


def query_top_funding_agencies(db_path: Path | str = DEFAULT_DATABASE) -> list[dict[str, Any]]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT agency, amount_inr_crore, distinct_institutes, projects, lead_institute, focus
            FROM demo_funding_agencies
            ORDER BY amount_inr_crore DESC
            LIMIT 5
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def query_trl_progression(db_path: Path | str = DEFAULT_DATABASE) -> list[dict[str, Any]]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT institution, state, project, domain, transition_year, trl, milestone, starting_trl, latest_trl
            FROM demo_trl_progression
            ORDER BY institution, project, transition_year
            """
        ).fetchall()
    finally:
        conn.close()

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["institution"], row["project"])
        if key not in grouped:
            grouped[key] = {
                "institution": row["institution"],
                "state": row["state"],
                "project": row["project"],
                "domain": row["domain"],
                "starting_trl": row["starting_trl"],
                "latest_trl": row["latest_trl"],
                "transitions": [],
            }
        grouped[key]["transitions"].append(
            {
                "year": row["transition_year"],
                "trl": row["trl"],
                "milestone": row["milestone"],
            }
        )

    return sorted(
        grouped.values(),
        key=lambda row: (row["latest_trl"] - row["starting_trl"], row["latest_trl"], row["institution"]),
        reverse=True,
    )


def query_solar_seed_to_patents(db_path: Path | str = DEFAULT_DATABASE) -> dict[str, Any]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT researcher, institution, state, seed_year, seed_funding_inr_lakh,
                   patent_count, first_patent_months, core_patent
            FROM demo_solar_seed_patents
            ORDER BY patent_count DESC, first_patent_months ASC, researcher ASC
            """
        ).fetchall()
    finally:
        conn.close()

    researchers = [dict(row) for row in rows]
    return {
        "researchers": researchers,
        "median_patents_per_researcher": statistics.median(row["patent_count"] for row in researchers),
        "median_months_to_first_patent": statistics.median(row["first_patent_months"] for row in researchers),
        "total_patents": sum(row["patent_count"] for row in researchers),
        "seed_cohort_size": len(researchers),
    }


def query_iit_b_vs_iit_m_ai_ml(db_path: Path | str = DEFAULT_DATABASE) -> list[dict[str, Any]]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT year, institution, grant_amount_inr_crore, publications, patents, active_researchers
            FROM demo_iit_ai_ml_comparison
            ORDER BY year ASC, institution ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def query_demo_graph(db_path: Path | str = DEFAULT_DATABASE) -> dict[str, list[dict[str, Any]]]:
    conn = _connect(db_path)
    try:
        nodes = conn.execute(
            "SELECT id, label, type FROM demo_graph_nodes ORDER BY type, label"
        ).fetchall()
        edges = conn.execute(
            "SELECT source, target, weight, relationship FROM demo_graph_edges ORDER BY relationship, source, target"
        ).fetchall()
        return {
            "nodes": [dict(row) for row in nodes],
            "edges": [dict(row) for row in edges],
        }
    finally:
        conn.close()


def build_sqlite_killer_query_results(db_path: Path | str = DEFAULT_DATABASE) -> dict[str, Any]:
    return {
        "top_funding_agencies": query_top_funding_agencies(db_path),
        "trl_progression": query_trl_progression(db_path),
        "solar_seed_to_patents": query_solar_seed_to_patents(db_path),
        "iit_b_vs_iit_m_ai_ml": query_iit_b_vs_iit_m_ai_ml(db_path),
        "demo_graph": query_demo_graph(db_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed deterministic NRG demo data.")
    parser.add_argument("--database", type=Path, default=None, help="SQLite database to seed with demo_* tables.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE, help="Seed fixture JSON path.")
    parser.add_argument("--print-json", action="store_true", help="Print killer-query result sets as JSON.")
    args = parser.parse_args(argv)

    summary = seed_sqlite(args.database, args.fixture) if args.database else None

    if args.print_json:
        if args.database:
            payload = build_sqlite_killer_query_results(args.database)
        else:
            payload = build_killer_query_results(load_seed_data(args.fixture))
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif args.database:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(json.dumps(build_killer_query_results(load_seed_data(args.fixture)), indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
