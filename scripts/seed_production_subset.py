#!/usr/bin/env python3
"""Seed the LB-3 volumetric subset for killer-query evidence."""

from __future__ import annotations

import argparse
import os
import random
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "nrg_research.db"

INSTITUTES = [
    "IIT Bombay",
    "IIT Madras",
    "IIT Delhi",
    "IIT Gandhinagar",
    "IIT Kanpur",
    "IIT Kharagpur",
    "IIT Hyderabad",
    "IIT Roorkee",
]
YEARS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
STAGES = [f"Level {i}" for i in range(1, 10)]
AGENCIES = ["DST-SERB", "ANRF", "MeitY", "DBT", "CSIR", "ICMR"]

TARGETS = {
    "academic_courses_details": 50_000,
    "innovations_at_various_stages_of_technology_readiness_level": 10_000,
    "innovation_grant_from_govt": 30_000,
    "combined_ipo_patent_data": 20_000,
    "publications": 100_000,
    "researchers": 5_000,
}


def connect() -> sqlite3.Connection:
    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith("sqlite:///"):
        path = Path(database_url.removeprefix("sqlite:///"))
        if not path.is_absolute():
            path = REPO_ROOT / path
    else:
        path = DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def delete_owned_rows(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM academic_courses_details WHERE id LIKE 'LB3-AC-%'")
    conn.execute(
        "DELETE FROM innovations_at_various_stages_of_technology_readiness_level WHERE id LIKE 'LB3-TRL-%'"
    )
    conn.execute("DELETE FROM innovation_grant_from_govt WHERE id LIKE 'LB3-IG-%'")
    conn.execute("DELETE FROM combined_ipo_patent_data WHERE id LIKE 'LB3-PAT-%'")
    conn.execute("DELETE FROM publications WHERE publication_id LIKE 'LB3-PUB-%'")


def ensure_indexes(conn: sqlite3.Connection) -> None:
    """Create local indexes matching the LB-3 PostgreSQL migration intent."""
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lb3_academic_year_institute "
        "ON academic_courses_details(financial_year, institute)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lb3_trl_stage_institute_year "
        "ON innovations_at_various_stages_of_technology_readiness_level(stage_of_technology, institute, financial_year)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lb3_grant_institute_year "
        "ON innovation_grant_from_govt(institute, year_of_receiving)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lb3_patent_status_applicants_date "
        "ON combined_ipo_patent_data(status, applicants, date_of_grant)"
    )


def batched(items: Iterable[tuple], size: int = 1_000) -> Iterable[list[tuple]]:
    batch: list[tuple] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def seed_courses(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "academic_courses_details")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            institute = INSTITUTES[i % len(INSTITUTES)]
            year = YEARS[i % len(YEARS)]
            lecture = 6 if institute == "IIT Bombay" and year == "2022-23" else 2 + (i % 5)
            practical = 2 if institute == "IIT Bombay" and year == "2022-23" else i % 3
            yield (
                year,
                f"Innovation Systems {i % 400}",
                f"LB3C{i:06d}",
                "Core" if i % 3 else "Elective",
                ["UG", "PG", "PhD"][i % 3],
                ["Computer Science", "Design", "Mechanical Engineering", "Materials Science"][i % 4],
                f"{lecture}:{practical}",
                institute,
                "2026",
                f"LB3-AC-{i:06d}",
            )

    sql = (
        "INSERT INTO academic_courses_details "
        "(financial_year, title_of_course, course_code, type_of_course, level_of_course, "
        "course_offering_department, total_credit_score, institute, as_on_year, id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    for batch in batched(rows()):
        conn.executemany(sql, batch)
    return count_rows(conn, "academic_courses_details")


def seed_trl(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "innovations_at_various_stages_of_technology_readiness_level")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            institute = "IIT Madras" if i % 4 == 0 else INSTITUTES[i % len(INSTITUTES)]
            year = YEARS[1 + (i % 4)]
            stage = "Level 4" if i % 5 in (0, 1) else ("Level 9" if i % 5 == 2 else STAGES[i % len(STAGES)])
            yield (
                f"LB3 innovation {i:06d}",
                stage,
                year,
                institute,
                "2026",
                f"LB3-TRL-{i:06d}",
            )

    sql = (
        "INSERT INTO innovations_at_various_stages_of_technology_readiness_level "
        "(innovation_name, stage_of_technology, financial_year, institute, as_on_year, id) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )
    for batch in batched(rows()):
        conn.executemany(sql, batch)
    return count_rows(conn, "innovations_at_various_stages_of_technology_readiness_level")


def seed_grants(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "innovation_grant_from_govt")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    efficiency_leaders = {"IIT Madras", "IIT Bombay", "IIT Delhi"}

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            institute = INSTITUTES[i % len(INSTITUTES)]
            year = YEARS[i % len(YEARS)]
            base = 5_000_000 + (i % 17) * 425_000
            if institute in efficiency_leaders and year == "2022-23":
                amount = 18_000_000 + (i % 3) * 500_000
            elif institute in efficiency_leaders and year == "2023-24":
                amount = 8_000_000 + (i % 3) * 250_000
            else:
                amount = base
            yield (
                AGENCIES[i % len(AGENCIES)],
                int(amount),
                year,
                institute,
                "2026",
                f"LB3-IG-{i:06d}",
            )

    sql = (
        "INSERT INTO innovation_grant_from_govt "
        "(gov_organisation_name, grant_received, year_of_receiving, institute, as_on_year, id) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )
    for batch in batched(rows()):
        conn.executemany(sql, batch)
    return count_rows(conn, "innovation_grant_from_govt")


def seed_patents(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "combined_ipo_patent_data")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    efficiency_leaders = {"IIT Madras", "IIT Bombay", "IIT Delhi"}

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            institute = INSTITUTES[i % len(INSTITUTES)]
            if institute in efficiency_leaders:
                year = 2023 if i % 3 else 2022
            else:
                year = 2022 + (i % 3)
            status = "Granted" if institute in efficiency_leaders or i % 4 else "Published"
            yield (
                f"LB3-PAT-{i:06d}",
                f"LB3-APP-{i:06d}",
                f"LB3 patentable system {i:06d}",
                f"{year}-06-{(i % 27) + 1:02d}",
                f"LB3 Inventor {i % 200}",
                f"{institute} Research Foundation",
                status,
                f"IN{year}{i:06d}",
                f"{year}-09-{(i % 27) + 1:02d}",
                institute,
            )

    sql = (
        "INSERT INTO combined_ipo_patent_data "
        "(id, application_number, invention_title, application_filing_date, inventors, applicants, "
        "status, patent_number, date_of_grant, university_name) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    for batch in batched(rows()):
        conn.executemany(sql, batch)
    return count_rows(conn, "combined_ipo_patent_data")


def seed_publications(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "publications")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    random.seed(42)

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            area = ["AI/ML", "Nanotechnology", "Sustainable Energy", "Robotics"][i % 4]
            year = 2020 + (i % 6)
            yield (
                f"LB3-PUB-{i:06d}",
                f"LB3 {area} research article {i:06d}",
                f"Volumetric evidence abstract for {area}",
                f"LB3 Author {i % 500}",
                f"RES-{random.randint(0, 5614):06d}",
                ["Nature", "IEEE Access", "Science India", "ACM Computing Surveys"][i % 4],
                year,
                str(1 + (i % 40)),
                str(1 + (i % 12)),
                f"{1 + i % 50}-{50 + i % 900}",
                f"10.9000/lb3.{i:06d}",
                None,
                i % 250,
                round(1.5 + (i % 120) / 10, 2),
                "Journal Article",
                area,
                1,
            )

    sql = (
        "INSERT INTO publications "
        "(publication_id, title, abstract, authors, researcher_ids, venue, year, volume, issue, pages, "
        "doi, pmid, citations, impact_factor, publication_type, research_area, access_tier) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    for batch in batched(rows()):
        conn.executemany(sql, batch)
    return count_rows(conn, "publications")


def append_audit(summary: dict[str, int]) -> str | None:
    try:
        from src.audit import AuditEvent, get_audit_log

        return get_audit_log().append(
            AuditEvent(
                event_type="lb3_seed_subset",
                user_id="system",
                result=summary,
            )
        )
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed LB-3 volumetric subset.")
    parser.add_argument("--no-audit", action="store_true")
    args = parser.parse_args()

    started = datetime.now(UTC).isoformat()
    with connect() as conn:
        delete_owned_rows(conn)
        conn.commit()
        summary = {
            "academic_courses_details": seed_courses(conn, TARGETS["academic_courses_details"]),
            "innovations_at_various_stages_of_technology_readiness_level": seed_trl(
                conn,
                TARGETS["innovations_at_various_stages_of_technology_readiness_level"],
            ),
            "innovation_grant_from_govt": seed_grants(conn, TARGETS["innovation_grant_from_govt"]),
            "combined_ipo_patent_data": seed_patents(conn, TARGETS["combined_ipo_patent_data"]),
            "publications": seed_publications(conn, TARGETS["publications"]),
            "researchers": count_rows(conn, "researchers"),
        }
        ensure_indexes(conn)
        conn.commit()

    audit_hash = None if args.no_audit else append_audit(summary)
    finished = datetime.now(UTC).isoformat()
    print(
        {
            "started": started,
            "finished": finished,
            "counts": summary,
            "audit_hash": audit_hash,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
