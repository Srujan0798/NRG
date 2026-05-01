#!/usr/bin/env python3
"""Seed deterministic local data-quality fixtures for empty NRG benchmark tables.

This is a local development and validation helper. It does not claim to replace
official production intake; it only prevents empty canonical tables from hiding
query-path regressions in a founder laptop or CI-like local stack.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.observability.data_quality import DEFAULT_CORE_TABLES  # noqa: E402

DEFAULT_DATABASE_URL = "postgresql://nrg:nrg_default_password@localhost:5432/nrg"
DEFAULT_MIN_ROWS = 1000

INSTITUTES = (
    ("Indian Institute of Technology Bombay", "IIT Bombay", "Mumbai", "Maharashtra"),
    ("Indian Institute of Technology Madras", "IIT Madras", "Chennai", "Tamil Nadu"),
    ("Indian Institute of Technology Delhi", "IIT Delhi", "New Delhi", "Delhi"),
    ("Indian Institute of Technology Hyderabad", "IIT Hyderabad", "Hyderabad", "Telangana"),
    ("Indian Institute of Science Bengaluru", "IISc Bengaluru", "Bengaluru", "Karnataka"),
    ("National Institute of Technology Karnataka", "NIT Karnataka", "Surathkal", "Karnataka"),
    ("Indian Institute of Technology Gandhinagar", "IIT Gandhinagar", "Gandhinagar", "Gujarat"),
    ("Indian Institute of Technology Kanpur", "IIT Kanpur", "Kanpur", "Uttar Pradesh"),
    ("Indian Institute of Technology Kharagpur", "IIT Kharagpur", "Kharagpur", "West Bengal"),
    ("Indian Institute of Technology Roorkee", "IIT Roorkee", "Roorkee", "Uttarakhand"),
)
PROGRAMS = ("UG", "PG", "PhD")
YEARS = ("2021-22", "2022-23", "2023-24", "2024-25", "2025-26")
DOMAINS = ("AI", "Quantum", "Energy", "Biotech", "Materials", "Robotics")
REFRESH_TIMESTAMP_COLUMNS = ("updated_at", "created_at", "inserted_at", "fetched_at", "loaded_at", "ingested_at")
FRESHNESS_REFRESH_TABLES = {
    "institutions",
    "researchers",
    "publications",
    "combined_ipo_patent_data",
    "academic_courses_details",
    "innovation_grant_from_govt",
    "innovations_at_various_stages_of_technology_readiness_level",
}


def seed_quality_fixtures(
    engine_or_url: Engine | str,
    *,
    min_rows: int = DEFAULT_MIN_ROWS,
    tables: set[str] | None = None,
    refresh_freshness: bool = True,
) -> dict[str, dict[str, Any]]:
    engine = create_engine(engine_or_url, pool_pre_ping=True) if isinstance(engine_or_url, str) else engine_or_url
    inspector = inspect(engine)
    live_tables = set(inspector.get_table_names())
    target_tables = sorted((tables or set(DEFAULT_CORE_TABLES)) & live_tables)
    report: dict[str, dict[str, Any]] = {}

    with engine.begin() as conn:
        for table in target_tables:
            columns = {column["name"] for column in inspector.get_columns(table)}
            before = _count_rows(conn, table, engine)
            needed = max(0, min_rows - before)
            inserted = 0
            if needed:
                start_id = _max_id(conn, table, engine) + 1 if "id" in columns else before + 1
                rows = [_row_for_table(table, columns, start_id + offset, offset) for offset in range(needed)]
                rows = [row for row in rows if row]
                if rows:
                    _insert_rows(conn, table, rows, engine)
                    inserted = len(rows)
                    _sync_postgres_sequence(conn, table, engine)

            after = before + inserted
            report[table] = {"before": before, "inserted": inserted, "after": after}

        if refresh_freshness:
            refreshed = _refresh_local_freshness(conn, live_tables, inspector, engine)
            if refreshed:
                report["_freshness_refresh"] = refreshed

    return report


def _row_for_table(table: str, columns: set[str], row_id: int, offset: int) -> dict[str, Any]:
    institute_full, institute_short, city, state = INSTITUTES[offset % len(INSTITUTES)]
    institute = institute_short
    program = PROGRAMS[offset % len(PROGRAMS)]
    year = YEARS[offset % len(YEARS)]
    as_on_year = "2026"
    domain = DOMAINS[offset % len(DOMAINS)]
    base = {
        "id": row_id,
        "institute": institute,
        "as_on_year": as_on_year,
        "financial_year": year,
    }

    table_rows: dict[str, dict[str, Any]] = {
        "actual_student_strength": {
            **base,
            "program": program,
            "male_students": 180 + (offset % 220),
            "female_students": 120 + (offset % 180),
            "total_students": 300 + (offset % 400),
            "within_state": 110 + (offset % 140),
            "outside_state": 160 + (offset % 180),
            "outside_country": 5 + (offset % 20),
            "economically_backward": 45 + (offset % 60),
            "socially_challenged": 35 + (offset % 55),
            "reimbursed_by_government": 50 + (offset % 70),
            "reimbursed_by_institution": 20 + (offset % 30),
            "reimbursed_by_private": 10 + (offset % 20),
            "not_reimbursed": 120 + (offset % 180),
        },
        "faculty_details": {
            **base,
            "num_faculties": 60 + (offset % 140),
        },
        "financial_expenses_capital": {
            **base,
            "library": 1_000_000 + offset * 1000,
            "equipment": 5_000_000 + offset * 2500,
            "workshops": 300_000 + offset * 250,
            "capital_assets": 8_000_000 + offset * 3000,
        },
        "financial_expenses_operational": {
            **base,
            "salaries": 60_000_000 + offset * 10_000,
            "maintenance": 4_000_000 + offset * 1000,
            "seminars": 500_000 + offset * 100,
        },
        "patents_details": {
            **base,
            "patents_published": 5 + (offset % 25),
            "patents_granted": 2 + (offset % 12),
            "patents_commercialized": offset % 5,
        },
        "phd_students": {
            **base,
            "program_type": "Full-time" if offset % 3 else "Part-time",
            "department": domain,
            "total": 30 + (offset % 180),
            "graduate": 5 + (offset % 50),
            "male": 20 + (offset % 110),
            "female": 10 + (offset % 70),
        },
        "placements_and_higher_studies": {
            **base,
            "program": program,
            "year_of_intake": year,
            "students_intaken": 200 + (offset % 250),
            "students_admitted": 180 + (offset % 220),
            "year_of_lateral_entry": year,
            "students_admitted_lateral_entry": offset % 40,
            "year_of_graduation": year,
            "graduated_students": 150 + (offset % 180),
            "placed_students": 120 + (offset % 150),
            "median_salary_per_annum": 900_000 + (offset % 80) * 10_000,
            "higher_studies_students": 10 + (offset % 45),
        },
        "research_consultancy_details_consultancy": {
            **base,
            "consultancy_projects": 2 + (offset % 20),
            "client_organisations": 1 + (offset % 12),
            "amount_recieved_consultancy_projects": 500_000 + offset * 5000,
        },
        "research_consultancy_details_sponsered": {
            **base,
            "sponsered_projects": 2 + (offset % 22),
            "funding_agencies": 1 + (offset % 10),
            "amount_recieved_sponsered_research": 800_000 + offset * 8000,
        },
        "sanctioned_intake": {
            **base,
            "program": program,
            "seats": 120 + (offset % 400),
        },
        "startup_recognition": {
            **base,
            "startup_name": f"{domain} Venture {row_id:04d}",
            "year_of_recognition": "2026",
            "recognition_year": "2026",
            "recognition_body": "NRG Local Fixture",
            "registration_no": f"NRG-LOCAL-{row_id:06d}",
            "sector": domain,
        },
        "tb_institute_mstr": {
            "id": row_id,
            "institute_name": f"{institute_full} Local Centre {offset // len(INSTITUTES) + 1}",
            "short_name": institute_short,
            "institute_type": "Institute of National Importance",
            "city": city,
            "state": state,
            "address": f"{city}, {state}",
            "established_year": 1950 + (offset % 70),
            "website_url": f"https://{institute_short.lower().replace(' ', '')}.example.edu",
        },
    }

    row = table_rows.get(table, {**base})
    return {column: value for column, value in row.items() if column in columns}


def _insert_rows(conn: Any, table: str, rows: list[dict[str, Any]], engine: Engine) -> None:
    columns = list(rows[0])
    quoted_columns = ", ".join(_quote(engine, column) for column in columns)
    placeholders = ", ".join(f":{column}" for column in columns)
    conn.execute(text(f"INSERT INTO {_quote(engine, table)} ({quoted_columns}) VALUES ({placeholders})"), rows)


def _refresh_local_freshness(conn: Any, live_tables: set[str], inspector: Any, engine: Engine) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0)
    refreshed: dict[str, Any] = {}
    for table in sorted(FRESHNESS_REFRESH_TABLES & live_tables):
        columns = {column["name"] for column in inspector.get_columns(table)}
        timestamp_columns = [column for column in REFRESH_TIMESTAMP_COLUMNS if column in columns]
        if not timestamp_columns or _count_rows(conn, table, engine) == 0:
            continue
        assignments = ", ".join(f"{_quote(engine, column)} = :now" for column in timestamp_columns)
        conn.execute(text(f"UPDATE {_quote(engine, table)} SET {assignments}"), {"now": now})
        refreshed[table] = {"columns": timestamp_columns, "value": now.isoformat()}
    return refreshed


def _count_rows(conn: Any, table: str, engine: Engine) -> int:
    return int(conn.execute(text(f"SELECT COUNT(*) FROM {_quote(engine, table)}")).scalar_one() or 0)


def _max_id(conn: Any, table: str, engine: Engine) -> int:
    value = conn.execute(text(f"SELECT MAX({_quote(engine, 'id')}) FROM {_quote(engine, table)}")).scalar_one()
    return int(value or 0)


def _sync_postgres_sequence(conn: Any, table: str, engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        return
    conn.execute(
        text(
            "SELECT setval(pg_get_serial_sequence(:table_name, 'id'), "
            f"COALESCE((SELECT MAX({_quote(engine, 'id')}) FROM {_quote(engine, table)}), 1), true) "
            "WHERE pg_get_serial_sequence(:table_name, 'id') IS NOT NULL"
        ),
        {"table_name": table},
    )


def _quote(engine: Engine, identifier: str) -> str:
    return engine.dialect.identifier_preparer.quote(identifier)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
    parser.add_argument("--min-rows", type=int, default=DEFAULT_MIN_ROWS)
    parser.add_argument("--table", action="append", default=[], help="Specific table to seed; repeatable.")
    parser.add_argument("--no-refresh-freshness", action="store_true")
    parser.add_argument(
        "--allow-synthetic",
        action="store_true",
        help="Required unless NRG_ALLOW_LOCAL_QUALITY_FIXTURES=1 is set.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.allow_synthetic and os.getenv("NRG_ALLOW_LOCAL_QUALITY_FIXTURES") != "1":
        print(
            "Refusing to seed local synthetic quality fixtures without --allow-synthetic "
            "or NRG_ALLOW_LOCAL_QUALITY_FIXTURES=1.",
            file=sys.stderr,
        )
        return 2

    report = seed_quality_fixtures(
        args.database_url,
        min_rows=args.min_rows,
        tables=set(args.table) if args.table else None,
        refresh_freshness=not args.no_refresh_freshness,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
