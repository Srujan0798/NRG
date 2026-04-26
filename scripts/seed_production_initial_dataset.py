from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEED_DATA_PATH = ROOT / "scripts" / "seed_data.json"


def load_seed_data(path: Path = SEED_DATA_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_killer_query_results(data: dict[str, Any]) -> dict[str, Any]:
    patents = list(data["solar_seed_patents"])
    return {
        "top_funding_agencies": list(data["funding_agencies"]),
        "trl_progression": list(data["trl_progression"]),
        "solar_seed_to_patents": {
            "researchers": patents,
            "median_patents_per_researcher": statistics.median(
                row["patent_count"] for row in patents
            ),
            "median_months_to_first_patent": statistics.median(
                row["first_patent_months"] for row in patents
            ),
        },
        "iit_b_vs_iit_m_ai_ml": list(data["iit_ai_ml_comparison"]),
        "demo_graph": data["demo_graph"],
    }


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _rows(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [dict(row) for row in cursor.fetchall()]


def seed_sqlite(db_path: Path, data: dict[str, Any] | None = None) -> dict[str, int]:
    data = data or load_seed_data()
    with _connect(db_path) as conn:
        conn.executescript(
            """
            DROP TABLE IF EXISTS demo_funding_agencies;
            DROP TABLE IF EXISTS demo_trl_progression;
            DROP TABLE IF EXISTS demo_solar_seed_patents;
            DROP TABLE IF EXISTS demo_iit_ai_ml_comparison;

            CREATE TABLE demo_funding_agencies (
                agency TEXT PRIMARY KEY,
                amount_inr_crore REAL NOT NULL,
                distinct_institutes INTEGER NOT NULL,
                projects INTEGER NOT NULL,
                lead_institute TEXT NOT NULL,
                focus TEXT NOT NULL
            );

            CREATE TABLE demo_trl_progression (
                institution TEXT NOT NULL,
                state TEXT NOT NULL,
                project TEXT NOT NULL,
                domain TEXT NOT NULL,
                year INTEGER NOT NULL,
                trl INTEGER NOT NULL,
                milestone TEXT NOT NULL,
                starting_trl INTEGER NOT NULL,
                latest_trl INTEGER NOT NULL
            );

            CREATE TABLE demo_solar_seed_patents (
                researcher TEXT PRIMARY KEY,
                institution TEXT NOT NULL,
                state TEXT NOT NULL,
                seed_year INTEGER NOT NULL,
                seed_funding_inr_lakh REAL NOT NULL,
                patent_count INTEGER NOT NULL,
                first_patent_months INTEGER NOT NULL,
                core_patent TEXT NOT NULL
            );

            CREATE TABLE demo_iit_ai_ml_comparison (
                year INTEGER NOT NULL,
                institution TEXT NOT NULL,
                grant_amount_inr_crore REAL NOT NULL,
                publications INTEGER NOT NULL,
                patents INTEGER NOT NULL,
                active_researchers INTEGER NOT NULL,
                PRIMARY KEY (year, institution)
            );
            """
        )
        conn.executemany(
            """
            INSERT INTO demo_funding_agencies
            (agency, amount_inr_crore, distinct_institutes, projects, lead_institute, focus)
            VALUES (:agency, :amount_inr_crore, :distinct_institutes, :projects, :lead_institute, :focus)
            """,
            data["funding_agencies"],
        )
        trl_rows = [
            {
                "institution": item["institution"],
                "state": item["state"],
                "project": item["project"],
                "domain": item["domain"],
                "starting_trl": item["starting_trl"],
                "latest_trl": item["latest_trl"],
                "year": transition["year"],
                "trl": transition["trl"],
                "milestone": transition["milestone"],
            }
            for item in data["trl_progression"]
            for transition in item["transitions"]
        ]
        conn.executemany(
            """
            INSERT INTO demo_trl_progression
            (institution, state, project, domain, year, trl, milestone, starting_trl, latest_trl)
            VALUES (:institution, :state, :project, :domain, :year, :trl, :milestone, :starting_trl, :latest_trl)
            """,
            trl_rows,
        )
        conn.executemany(
            """
            INSERT INTO demo_solar_seed_patents
            (researcher, institution, state, seed_year, seed_funding_inr_lakh, patent_count, first_patent_months, core_patent)
            VALUES (:researcher, :institution, :state, :seed_year, :seed_funding_inr_lakh, :patent_count, :first_patent_months, :core_patent)
            """,
            data["solar_seed_patents"],
        )
        conn.executemany(
            """
            INSERT INTO demo_iit_ai_ml_comparison
            (year, institution, grant_amount_inr_crore, publications, patents, active_researchers)
            VALUES (:year, :institution, :grant_amount_inr_crore, :publications, :patents, :active_researchers)
            """,
            data["iit_ai_ml_comparison"],
        )
        return {
            "demo_funding_agencies": conn.execute(
                "SELECT COUNT(*) FROM demo_funding_agencies"
            ).fetchone()[0],
            "demo_trl_progression": conn.execute(
                "SELECT COUNT(*) FROM demo_trl_progression"
            ).fetchone()[0],
            "demo_solar_seed_patents": conn.execute(
                "SELECT COUNT(*) FROM demo_solar_seed_patents"
            ).fetchone()[0],
            "demo_iit_ai_ml_comparison": conn.execute(
                "SELECT COUNT(*) FROM demo_iit_ai_ml_comparison"
            ).fetchone()[0],
        }


def query_top_funding_agencies(db_path: Path) -> list[dict[str, Any]]:
    with _connect(db_path) as conn:
        return _rows(
            conn.execute(
                """
                SELECT agency, amount_inr_crore, distinct_institutes, projects, lead_institute, focus
                FROM demo_funding_agencies
                ORDER BY amount_inr_crore DESC
                LIMIT 5
                """
            )
        )


def query_trl_progression(db_path: Path) -> list[dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = _rows(
            conn.execute(
                """
                SELECT institution, state, project, domain, year, trl, milestone, starting_trl, latest_trl
                FROM demo_trl_progression
                ORDER BY institution, year
                """
            )
        )
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        item = grouped.setdefault(
            row["institution"],
            {
                "institution": row["institution"],
                "state": row["state"],
                "project": row["project"],
                "domain": row["domain"],
                "starting_trl": row["starting_trl"],
                "latest_trl": row["latest_trl"],
                "transitions": [],
            },
        )
        item["transitions"].append(
            {"year": row["year"], "trl": row["trl"], "milestone": row["milestone"]}
        )
    return list(grouped.values())


def query_solar_seed_to_patents(db_path: Path) -> dict[str, Any]:
    with _connect(db_path) as conn:
        researchers = _rows(
            conn.execute(
                """
                SELECT researcher, institution, state, seed_year, seed_funding_inr_lakh,
                       patent_count, first_patent_months, core_patent
                FROM demo_solar_seed_patents
                ORDER BY patent_count DESC, researcher
                """
            )
        )
    return {
        "researchers": researchers,
        "median_patents_per_researcher": statistics.median(
            row["patent_count"] for row in researchers
        ),
        "median_months_to_first_patent": statistics.median(
            row["first_patent_months"] for row in researchers
        ),
    }


def query_iit_b_vs_iit_m_ai_ml(db_path: Path) -> list[dict[str, Any]]:
    with _connect(db_path) as conn:
        return _rows(
            conn.execute(
                """
                SELECT year, institution, grant_amount_inr_crore, publications, patents, active_researchers
                FROM demo_iit_ai_ml_comparison
                ORDER BY year, institution
                """
            )
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed deterministic NRG initial production dataset")
    parser.add_argument("--database", type=Path, default=ROOT / "data" / "demo_seed.db")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args(argv)

    data = load_seed_data()
    seed_sqlite(args.database, data)
    if args.print_json:
        print(json.dumps(build_killer_query_results(data), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
