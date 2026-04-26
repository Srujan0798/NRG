#!/usr/bin/env python3
"""Seed the local PostgreSQL stack for the founder laptop sanity check."""

from __future__ import annotations

import argparse
import json
import os
import random
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

import psycopg2
from psycopg2.extras import execute_values


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "postgresql://nrg:nrg_default_password@localhost:5432/nrg"
EVIDENCE_DIR = REPO_ROOT / "evidence" / "2026-04-26"
SEED_ID_BASE = 91_000_000
SEED_NAMESPACE = uuid.UUID("9a1b52c8-737c-49a4-9c78-f0177d112f20")

INSTITUTES = [
    "IIT Bombay",
    "IIT Madras",
    "IIT Delhi",
    "IIT Gandhinagar",
    "IIT Kanpur",
    "IIT Kharagpur",
    "IIT Hyderabad",
    "IIT Roorkee",
    "IIT Guwahati",
    "IIT Ropar",
]
YEARS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
STAGES = [f"Level {i}" for i in range(1, 10)]
AGENCIES = ["ANRF", "DST-SERB", "MeitY", "DBT", "CSIR", "ICMR", "DRDO"]
AREAS = [
    "Artificial Intelligence",
    "Renewable Energy",
    "Hydrogen Fuel Cells",
    "Biotechnology",
    "Materials Science",
    "Computer Science",
]
STATES = ["Maharashtra", "Tamil Nadu", "Delhi", "Gujarat", "Karnataka", "Telangana"]


def chunks(rows: Iterable[tuple], size: int = 2_000) -> Iterable[list[tuple]]:
    batch: list[tuple] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def scalar(cur, sql: str) -> int:
    cur.execute(sql)
    return int(cur.fetchone()[0])


def cleanup(cur) -> None:
    cur.execute("DELETE FROM academic_courses_details WHERE id >= %s", (SEED_ID_BASE,))
    cur.execute(
        "DELETE FROM innovations_at_various_stages_of_technology_readiness_level WHERE id >= %s",
        (SEED_ID_BASE,),
    )
    cur.execute("DELETE FROM innovation_grant_from_govt WHERE id >= %s", (SEED_ID_BASE,))
    cur.execute("DELETE FROM combined_ipo_patent_data WHERE id >= %s", (SEED_ID_BASE,))
    cur.execute("DELETE FROM publications WHERE title LIKE 'NRG Local Sanity Publication %'")
    cur.execute("DELETE FROM researchers WHERE email LIKE 'nrg.local.sanity.%@example.in'")


def ensure_lb6_objects(cur) -> None:
    statements = [
        "CREATE INDEX IF NOT EXISTS idx_lb6_courses_institute_year_level "
        "ON academic_courses_details (institute, financial_year, level_of_course)",
        "CREATE INDEX IF NOT EXISTS idx_lb6_grants_institute_year "
        "ON innovation_grant_from_govt (institute, year_of_receiving)",
        "CREATE INDEX IF NOT EXISTS idx_lb6_grants_agency_year "
        "ON innovation_grant_from_govt (gov_organisation_name, year_of_receiving)",
        "CREATE INDEX IF NOT EXISTS idx_lb6_trl_institute_year_stage "
        "ON innovations_at_various_stages_of_technology_readiness_level "
        "(institute, financial_year, stage_of_technology)",
        "CREATE INDEX IF NOT EXISTS idx_lb6_patents_status_applicants_grant_date "
        "ON combined_ipo_patent_data (status, applicants, date_of_grant)",
        "CREATE INDEX IF NOT EXISTS idx_lb6_patents_field_status "
        "ON combined_ipo_patent_data (field_of_invention, status)",
        "CREATE INDEX IF NOT EXISTS idx_lb6_patents_applicants_norm "
        "ON combined_ipo_patent_data ((upper(trim(applicants))))",
        """
        CREATE OR REPLACE VIEW vw_innovations_trl AS
        SELECT
            id,
            innovation_name,
            stage_of_technology AS tech_readiness_stage,
            financial_year,
            institute,
            as_on_year,
            NULL::integer AS project_count,
            NULL::numeric AS grant_amount
        FROM innovations_at_various_stages_of_technology_readiness_level
        """,
    ]
    for statement in statements:
        cur.execute(statement)


def seed_courses(cur, rows: int) -> None:
    def data() -> Iterable[tuple]:
        for i in range(rows):
            institute = INSTITUTES[i % len(INSTITUTES)]
            year = YEARS[(i // len(INSTITUTES)) % len(YEARS)]
            base = 6 if institute == "IIT Bombay" and year == "2022-23" else 2 + (i % 4)
            lab = 2 if institute == "IIT Bombay" and year == "2022-23" else i % 3
            yield (
                year,
                f"NRG Innovation Systems {i % 700}",
                f"NRG-FL-{i:06d}",
                "Core" if i % 3 else "Elective",
                ["UG", "PG", "PhD"][i % 3],
                AREAS[i % len(AREAS)],
                f"{base}:{lab}",
                institute,
                "2026",
                SEED_ID_BASE + i,
            )

    sql = """
        INSERT INTO academic_courses_details (
            financial_year, title_of_course, course_code, type_of_course,
            level_of_course, course_offering_department, total_credit_score,
            institute, as_on_year, id
        ) VALUES %s
    """
    for batch in chunks(data()):
        execute_values(cur, sql, batch)


def seed_trl(cur, rows: int) -> None:
    def data() -> Iterable[tuple]:
        for i in range(rows):
            institute = "IIT Madras" if i % 5 == 0 else INSTITUTES[i % len(INSTITUTES)]
            year = YEARS[(i // len(INSTITUTES)) % len(YEARS)]
            if institute == "IIT Madras" and year in {"2022-23", "2023-24", "2024-25"}:
                stage = "Level 9" if i % 4 == 0 else "Level 4"
            else:
                stage = STAGES[i % len(STAGES)]
            yield (
                f"NRG Local Technology {i % 900}",
                stage,
                year,
                institute,
                "2026",
                SEED_ID_BASE + i,
            )

    sql = """
        INSERT INTO innovations_at_various_stages_of_technology_readiness_level (
            innovation_name, stage_of_technology, financial_year, institute, as_on_year, id
        ) VALUES %s
    """
    for batch in chunks(data()):
        execute_values(cur, sql, batch)


def grant_amount(institute: str, year: str, i: int) -> int:
    if institute in {"IIT Madras", "IIT Gandhinagar", "IIT Kanpur"}:
        if year == "2022-23":
            return 2_200_000 + (i % 8) * 100_000
        if year == "2023-24":
            return 850_000 + (i % 6) * 50_000
    return 600_000 + (i % 12) * 70_000


def seed_grants(cur, rows: int) -> None:
    def data() -> Iterable[tuple]:
        for i in range(rows):
            institute = INSTITUTES[i % len(INSTITUTES)]
            year = YEARS[(i // len(INSTITUTES)) % len(YEARS)]
            yield (
                AGENCIES[i % len(AGENCIES)],
                grant_amount(institute, year, i),
                year,
                institute,
                "2026",
                SEED_ID_BASE + i,
            )

    sql = """
        INSERT INTO innovation_grant_from_govt (
            gov_organisation_name, grant_received, year_of_receiving, institute, as_on_year, id
        ) VALUES %s
    """
    for batch in chunks(data()):
        execute_values(cur, sql, batch)


def patent_year(institute: str, i: int) -> str:
    if institute in {"IIT Madras", "IIT Gandhinagar", "IIT Kanpur"}:
        return "2023-07-10" if i % 3 else "2022-07-10"
    return f"{2020 + (i % 5)}-06-15"


def seed_patents(cur, rows: int) -> None:
    def data() -> Iterable[tuple]:
        for i in range(rows):
            institute = INSTITUTES[i % len(INSTITUTES)]
            grant_date = patent_year(institute, i)
            yield (
                SEED_ID_BASE + i,
                f"NRG-OID-{i:06d}",
                f"NRGAPP{i:07d}",
                datetime.now(UTC),
                "local_sanity",
                f"{AREAS[i % len(AREAS)]} Patent {i}",
                f"NRGPUB{i:07d}",
                grant_date,
                "A",
                f"{int(grant_date[:4]) - 1}-03-01",
                AREAS[i % len(AREAS)],
                f"Inventor {i % 1000}",
                institute,
                "Structured record for local sanity check",
                "Granted",
                f"NRGPAT{i:07d}",
                grant_date,
                "Active",
                datetime.now(UTC),
                f"Granted {AREAS[i % len(AREAS)]} Patent {i}",
                f"GRANT{i:07d}",
                institute,
                "local_stack",
            )

    sql = """
        INSERT INTO combined_ipo_patent_data (
            id, oid, application_number, inserted_at, source_collection,
            invention_title, publication_number, publication_date, publication_type,
            application_filing_date, field_of_invention, inventors, applicants,
            abstract, status, patent_number, date_of_grant, legal_status,
            fetched_at, granted_patent_title, patent_grant_number, university_name, fetched_from
        ) VALUES %s
    """
    for batch in chunks(data()):
        execute_values(cur, sql, batch)


def seed_publications(cur, rows: int) -> None:
    def data() -> Iterable[tuple]:
        for i in range(rows):
            yield (
                str(uuid.uuid5(SEED_NAMESPACE, f"publication-{i}")),
                f"NRG Local Sanity Publication {i}",
                f"Evidence-linked study in {AREAS[i % len(AREAS)]}",
                ["Nature India", "IEEE Access", "Current Science", "IIT Research Review"][i % 4],
                2020 + (i % 5),
                f"10.5555/nrg.local.{i}",
                (i % 3) + 1,
            )

    sql = """
        INSERT INTO publications (
            publication_id, title, abstract, venue, year, doi, access_tier
        ) VALUES %s
    """
    for batch in chunks(data()):
        execute_values(cur, sql, batch)


def seed_researchers(cur, rows: int) -> None:
    def data() -> Iterable[tuple]:
        for i in range(rows):
            yield (
                str(uuid.uuid5(SEED_NAMESPACE, f"researcher-{i}")),
                f"Researcher {i:05d}",
                f"nrg.local.sanity.{i:05d}@example.in",
                f"+9198{i % 10}{i % 10}{i % 10}{i % 10}{i % 10}{i % 10}{i % 10}{i % 10}",
                f"0000-0002-{i % 10_000:04d}",
                STATES[i % len(STATES)],
                AREAS[i % len(AREAS)],
                2000 + (i % 24),
                (i % 3) + 1,
            )

    sql = """
        INSERT INTO researchers (
            researcher_id, name, email, phone, orcid, state, research_area, year_joined, access_tier
        ) VALUES %s
    """
    for batch in chunks(data()):
        execute_values(cur, sql, batch)


def row_counts(cur) -> dict[str, int]:
    tables = [
        "academic_courses_details",
        "innovations_at_various_stages_of_technology_readiness_level",
        "innovation_grant_from_govt",
        "combined_ipo_patent_data",
        "publications",
        "researchers",
    ]
    counts: dict[str, int] = {}
    for table in tables:
        counts[table] = scalar(cur, f"SELECT COUNT(*) FROM {table}")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed local PostgreSQL acceptance-check data")
    parser.add_argument("--url", default=os.getenv("DATABASE_URL", DEFAULT_URL))
    parser.add_argument("--rows", type=int, default=50_000)
    parser.add_argument("--keep-existing", action="store_true")
    args = parser.parse_args()

    random.seed(20260426)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC)

    with psycopg2.connect(args.url) as conn:
        with conn.cursor() as cur:
            if not args.keep_existing:
                cleanup(cur)
            ensure_lb6_objects(cur)
            seed_courses(cur, args.rows)
            seed_trl(cur, args.rows)
            seed_grants(cur, args.rows)
            seed_patents(cur, args.rows)
            seed_publications(cur, args.rows)
            seed_researchers(cur, args.rows)
            counts = row_counts(cur)

    elapsed_ms = int((datetime.now(UTC) - started).total_seconds() * 1000)
    payload = {
        "captured_at": datetime.now(UTC).isoformat(),
        "elapsed_ms": elapsed_ms,
        "target_rows_per_table": args.rows,
        "row_counts": counts,
        "meets_50000_gate": all(value >= 50_000 for value in counts.values()),
        "schema_tables": None,
    }
    with psycopg2.connect(args.url) as conn:
        with conn.cursor() as cur:
            payload["schema_tables"] = scalar(
                cur,
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema='public' AND table_type='BASE TABLE'",
            )

    (EVIDENCE_DIR / "founder_laptop_seed_counts.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["meets_50000_gate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
