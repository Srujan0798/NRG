#!/usr/bin/env python3
"""Seed the LB-3 volumetric subset for killer-query evidence."""

from __future__ import annotations

import argparse
import os
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
INSTITUTION_PROFILES = [
    ("LB3-INST-IIT-BOMBAY", "IIT Bombay", "IIT", "Maharashtra"),
    ("LB3-INST-IIT-MADRAS", "IIT Madras", "IIT", "Tamil Nadu"),
    ("LB3-INST-IIT-DELHI", "IIT Delhi", "IIT", "Delhi"),
    ("LB3-INST-IIT-GANDHINAGAR", "IIT Gandhinagar", "IIT", "Gujarat"),
    ("LB3-INST-IIT-KANPUR", "IIT Kanpur", "IIT", "Uttar Pradesh"),
    ("LB3-INST-IIT-KHARAGPUR", "IIT Kharagpur", "IIT", "West Bengal"),
    ("LB3-INST-IIT-HYDERABAD", "IIT Hyderabad", "IIT", "Telangana"),
    ("LB3-INST-IIT-ROORKEE", "IIT Roorkee", "IIT", "Uttarakhand"),
    ("LB3-INST-IISC-BENGALURU", "IISc Bengaluru", "IISc", "Karnataka"),
    ("LB3-INST-CSIR-NCL", "CSIR National Chemical Laboratory", "CSIR", "Maharashtra"),
    ("LB3-INST-CSIR-CECRI", "CSIR Central Electrochemical Research Institute", "CSIR", "Tamil Nadu"),
    ("LB3-INST-GUJARAT-ROBOTICS", "Gujarat Robotics Research Centre", "State Research Centre", "Gujarat"),
]
INSTITUTION_BY_NAME = {
    name: {"id": institution_id, "type": institution_type, "state": state}
    for institution_id, name, institution_type, state in INSTITUTION_PROFILES
}
RESEARCHER_PROFILES = [
    ("IISc Bengaluru", "Computer Science", "AI/ML", "Machine Learning; Deep Learning; Computer Vision", 78, 9.4),
    ("IIT Gandhinagar", "Mechanical Engineering", "Robotics", "Autonomous Systems; Control Systems", 74, 7.6),
    ("IIT Bombay", "Physics", "Quantum Computing", "Qubits; Quantum Algorithms; QKD", 86, 8.8),
    ("IIT Delhi", "Computer Science", "Computer Science", "Software Systems; Cybersecurity; AI/ML", 82, 8.1),
    ("IIT Madras", "Computer Science", "Machine Learning", "AI/ML; NLP; Deep Learning", 76, 8.5),
    ("CSIR National Chemical Laboratory", "Chemical Sciences", "Hydrogen Catalysis", "Hydrogen Energy; Catalysis; Catalyst Design", 73, 7.9),
    ("IIT Madras", "Energy", "Renewable Energy", "Solar; Wind; Battery; Hydrogen", 69, 10.2),
    ("IIT Delhi", "Biotechnology", "Biotechnology", "Genomics; Proteomics; Drug Discovery", 64, 6.8),
    ("IIT Hyderabad", "Electrical Engineering", "Electronics", "VLSI; Semiconductors; Power Electronics", 61, 6.2),
    ("IIT Gandhinagar", "Computer Science", "Data Science", "Analytics; Machine Learning; AI/ML", 67, 7.0),
]
PUBLICATION_AREAS = [
    "AI/ML",
    "Machine Learning",
    "Quantum Computing",
    "Renewable Energy",
    "Robotics",
    "Hydrogen Catalysis",
    "Biotechnology",
    "Electronics",
]

TARGETS = {
    "institutions": len(INSTITUTION_PROFILES),
    "academic_courses_details": 50_000,
    "innovations_at_various_stages_of_technology_readiness_level": 10_000,
    "innovation_grant_from_govt": 30_000,
    "combined_ipo_patent_data": 20_000,
    "publications": 100_000,
    "researchers": 5_000,
    "researcher_publications": 120_000,
    "projects": 5_000,
    "funding_records": 8_000,
    "patents": 4_000,
    "collaborations": 2_500,
    "labs": 600,
    "research_documents": 6_000,
    "incubation_details": 500,
}

CI_TARGETS = {
    "institutions": len(INSTITUTION_PROFILES),
    "academic_courses_details": 300,
    "innovations_at_various_stages_of_technology_readiness_level": 150,
    "innovation_grant_from_govt": 300,
    "combined_ipo_patent_data": 250,
    "publications": 500,
    "researchers": 120,
    "researcher_publications": 700,
    "projects": 60,
    "funding_records": 100,
    "patents": 80,
    "collaborations": 80,
    "labs": 24,
    "research_documents": 100,
    "incubation_details": 30,
}


def connect() -> sqlite3.Connection:
    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith("sqlite:///"):
        path = Path(database_url.removeprefix("sqlite:///"))
        if not path.is_absolute():
            path = REPO_ROOT / path
    else:
        path = DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create the minimal local SQLite schema needed by query gates."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS institutions (
            institution_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT,
            state TEXT NOT NULL,
            country TEXT DEFAULT 'IN',
            founded_year INTEGER,
            website TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS researchers (
            researcher_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            institution_id TEXT,
            state TEXT,
            department TEXT,
            research_area TEXT,
            secondary_research_areas TEXT,
            years_experience INTEGER,
            year_joined INTEGER,
            h_index INTEGER,
            total_funding_received_inr_crores REAL,
            email TEXT,
            phone TEXT,
            orcid TEXT,
            tier_access TEXT,
            access_tier INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS publications (
            publication_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            abstract TEXT,
            authors TEXT,
            researcher_ids TEXT,
            venue TEXT,
            year INTEGER,
            volume TEXT,
            issue TEXT,
            pages TEXT,
            doi TEXT,
            pmid TEXT,
            citations INTEGER,
            impact_factor REAL,
            publication_type TEXT,
            research_area TEXT,
            access_tier INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS researcher_publications (
            researcher_id TEXT NOT NULL,
            publication_id TEXT NOT NULL,
            author_order INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (researcher_id, publication_id)
        );

        CREATE TABLE IF NOT EXISTS labs (
            lab_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            institution_id TEXT,
            research_area TEXT,
            research_focus_areas TEXT,
            established_year INTEGER,
            location_state TEXT,
            director_researcher_id TEXT,
            website TEXT,
            access_tier INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            principal_investigator_id TEXT,
            co_pis TEXT,
            start_date TEXT,
            end_date TEXT,
            funding_agency TEXT,
            sanctioned_amount_inr_crores REAL,
            status TEXT,
            research_area TEXT,
            access_tier INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS funding_records (
            funding_id TEXT PRIMARY KEY,
            researcher_id TEXT,
            institution_id TEXT,
            project_id TEXT,
            fiscal_year TEXT,
            agency TEXT,
            amount REAL,
            start_date TEXT,
            end_date TEXT,
            title TEXT,
            access_tier INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS patents (
            patent_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            inventor_ids TEXT,
            applicant_institution TEXT,
            patent_office TEXT,
            application_number TEXT,
            filing_date TEXT,
            grant_date TEXT,
            status TEXT,
            research_area TEXT,
            patent_type TEXT,
            claims_count INTEGER,
            access_tier INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS collaborations (
            collaboration_id TEXT PRIMARY KEY,
            researcher_ids TEXT,
            partner_institution TEXT,
            partner_country TEXT,
            collaboration_type TEXT,
            start_date TEXT,
            end_date TEXT,
            nature_of_work TEXT,
            funding_amount_inr_crores REAL,
            status TEXT,
            research_area TEXT,
            access_tier INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS research_documents (
            document_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            researcher_ids TEXT,
            affiliation TEXT,
            publication_year INTEGER,
            abstract TEXT,
            keywords TEXT,
            research_area_tags TEXT,
            access_tier INTEGER DEFAULT 1,
            category TEXT,
            file_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS incubation_details (
            id TEXT PRIMARY KEY,
            institute TEXT,
            financial_year TEXT,
            no_of_pre_incubation_units INTEGER,
            no_of_incubation_units INTEGER,
            income_generated_incubation REAL,
            access_tier INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS academic_courses_details (
            id TEXT PRIMARY KEY,
            financial_year TEXT,
            title_of_course TEXT,
            course_code TEXT,
            type_of_course TEXT,
            level_of_course TEXT,
            course_offering_department TEXT,
            total_credit_score TEXT,
            institute TEXT,
            as_on_year TEXT,
            access_tier INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS innovations_at_various_stages_of_technology_readiness_level (
            id TEXT PRIMARY KEY,
            innovation_name TEXT,
            stage_of_technology TEXT,
            financial_year TEXT,
            institute TEXT,
            as_on_year TEXT,
            technology_domain TEXT,
            access_tier INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE VIEW IF NOT EXISTS trl_stages AS
        SELECT * FROM innovations_at_various_stages_of_technology_readiness_level;

        CREATE TABLE IF NOT EXISTS innovation_grant_from_govt (
            id TEXT PRIMARY KEY,
            gov_organisation_name TEXT,
            grant_received REAL,
            year_of_receiving TEXT,
            institute TEXT,
            as_on_year TEXT,
            scheme_name TEXT,
            access_tier INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS combined_ipo_patent_data (
            id TEXT PRIMARY KEY,
            oid TEXT,
            application_number TEXT,
            inserted_at TEXT,
            source_collection TEXT,
            invention_title TEXT,
            publication_number TEXT,
            publication_date TEXT,
            publication_type TEXT,
            application_filing_date TEXT,
            field_of_invention TEXT,
            inventors TEXT,
            applicants TEXT,
            abstract TEXT,
            email_record TEXT,
            additional_email TEXT,
            application_type TEXT,
            examination_request_date TEXT,
            first_examination_report_date TEXT,
            certificate_issue_date TEXT,
            post_grant_journal_date TEXT,
            reply_to_fer_date TEXT,
            status TEXT,
            patent_number TEXT,
            date_of_grant TEXT,
            legal_status TEXT,
            due_date_next_renewal TEXT,
            renewal_history TEXT,
            aishe_code TEXT,
            fetched_at TEXT,
            granted_patent_title TEXT,
            patent_grant_number TEXT,
            university_name TEXT,
            fetched_from TEXT,
            title TEXT,
            filing_date TEXT,
            grant_date TEXT,
            institute TEXT,
            financial_year TEXT,
            access_tier INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


def delete_owned_rows(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM researcher_publications WHERE researcher_id LIKE 'LB3-RES-%' OR publication_id LIKE 'LB3-PUB-%'")
    conn.execute("DELETE FROM funding_records WHERE funding_id LIKE 'LB3-FUND-%'")
    conn.execute("DELETE FROM projects WHERE project_id LIKE 'LB3-PROJ-%'")
    conn.execute("DELETE FROM patents WHERE patent_id LIKE 'LB3-PATENT-%'")
    conn.execute("DELETE FROM collaborations WHERE collaboration_id LIKE 'LB3-COLL-%'")
    conn.execute("DELETE FROM labs WHERE lab_id LIKE 'LB3-LAB-%'")
    conn.execute("DELETE FROM research_documents WHERE document_id LIKE 'LB3-DOC-%'")
    conn.execute("DELETE FROM incubation_details WHERE id LIKE 'LB3-INC-%'")
    conn.execute("DELETE FROM academic_courses_details WHERE id LIKE 'LB3-AC-%'")
    conn.execute(
        "DELETE FROM innovations_at_various_stages_of_technology_readiness_level WHERE id LIKE 'LB3-TRL-%'"
    )
    conn.execute("DELETE FROM innovation_grant_from_govt WHERE id LIKE 'LB3-IG-%'")
    conn.execute("DELETE FROM combined_ipo_patent_data WHERE id LIKE 'LB3-PAT-%'")
    conn.execute("DELETE FROM publications WHERE publication_id LIKE 'LB3-PUB-%'")
    conn.execute("DELETE FROM researchers WHERE researcher_id LIKE 'LB3-RES-%'")
    conn.execute("DELETE FROM institutions WHERE institution_id LIKE 'LB3-INST-%'")


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
    conn.execute("CREATE INDEX IF NOT EXISTS idx_lb3_projects_status_area ON projects(status, research_area)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_lb3_funding_agency_year ON funding_records(agency, fiscal_year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_lb3_structured_patents_status_area ON patents(status, research_area)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_lb3_collab_country_type ON collaborations(partner_country, collaboration_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_lb3_labs_state_area ON labs(location_state, research_area)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_lb3_docs_year_category ON research_documents(publication_year, category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_lb3_researcher_pubs_pub ON researcher_publications(publication_id)")


def batched(items: Iterable[tuple], size: int = 1_000) -> Iterable[list[tuple]]:
    batch: list[tuple] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def institution_id(name: str) -> str:
    return INSTITUTION_BY_NAME[name]["id"]


def seed_institutions(conn: sqlite3.Connection, target: int) -> int:
    rows = [
        (
            institution_id_value,
            name,
            institution_type,
            state,
            "IN",
            1950 + index,
            f"https://example.in/{institution_id_value.lower()}",
        )
        for index, (institution_id_value, name, institution_type, state) in enumerate(
            INSTITUTION_PROFILES[:target],
            start=1,
        )
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO institutions
        (institution_id, name, type, state, country, founded_year, website)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return count_rows(conn, "institutions")


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

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            area = PUBLICATION_AREAS[i % len(PUBLICATION_AREAS)]
            year = 2020 + (i % 6)
            researcher_id = f"LB3-RES-{i % max(1, CI_TARGETS['researchers']):06d}"
            yield (
                f"LB3-PUB-{i:06d}",
                f"LB3 {area} research article {i:06d}",
                f"Volumetric evidence abstract for {area}",
                f"LB3 Author {i % 500}",
                researcher_id,
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


def seed_researchers(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "researchers")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            institute, department, area, secondary_areas, base_h_index, base_funding = RESEARCHER_PROFILES[
                i % len(RESEARCHER_PROFILES)
            ]
            state = INSTITUTION_BY_NAME[institute]["state"]
            yield (
                f"LB3-RES-{i:06d}",
                f"LB3 Researcher {i:06d}",
                institution_id(institute),
                state,
                department,
                area,
                secondary_areas,
                3 + (i % 25),
                2000 + (i % 25),
                base_h_index + (i // len(RESEARCHER_PROFILES)) % 12,
                round(base_funding + (i % 30) / 10, 2),
                f"lb3.researcher.{i:06d}@example.in",
                "researcher",
                1,
            )

    sql = (
        "INSERT INTO researchers "
        "(researcher_id, name, institution_id, state, department, research_area, secondary_research_areas, "
        "years_experience, year_joined, h_index, total_funding_received_inr_crores, "
        "email, tier_access, access_tier) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    for batch in batched(rows()):
        conn.executemany(sql, batch)
    return count_rows(conn, "researchers")


def seed_researcher_publications(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "researcher_publications")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    researcher_rows = conn.execute(
        "SELECT researcher_id FROM researchers WHERE researcher_id LIKE 'LB3-RES-%' ORDER BY researcher_id"
    ).fetchall()
    publication_rows = conn.execute(
        "SELECT publication_id FROM publications WHERE publication_id LIKE 'LB3-PUB-%' ORDER BY publication_id"
    ).fetchall()
    if not researcher_rows or not publication_rows:
        return existing

    researchers = [row[0] for row in researcher_rows]
    publications = [row[0] for row in publication_rows]
    quantum_researcher = "LB3-RES-000002"

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            publication_id = publications[i % len(publications)]
            researcher_id = quantum_researcher if i < min(75, len(publications)) else researchers[
                (i + i // len(publications)) % len(researchers)
            ]
            yield (researcher_id, publication_id, 1 + (i % 5))

    for batch in batched(rows()):
        conn.executemany(
            """
            INSERT OR IGNORE INTO researcher_publications
            (researcher_id, publication_id, author_order)
            VALUES (?, ?, ?)
            """,
            batch,
        )
    return count_rows(conn, "researcher_publications")


def seed_projects(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "projects")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            profile = RESEARCHER_PROFILES[i % len(RESEARCHER_PROFILES)]
            area = profile[2]
            status = "Ongoing" if i % 4 != 0 else "Completed"
            yield (
                f"LB3-PROJ-{i:06d}",
                f"LB3 {area} translational project {i:06d}",
                f"LB3-RES-{i % max(1, CI_TARGETS['researchers']):06d}",
                f"LB3-RES-{(i + 1) % max(1, CI_TARGETS['researchers']):06d}",
                f"{2020 + (i % 5)}-04-01",
                None if status == "Ongoing" else f"{2022 + (i % 4)}-03-31",
                AGENCIES[i % len(AGENCIES)],
                round(0.75 + (i % 40) * 0.18, 2),
                status,
                area,
                1,
            )

    for batch in batched(rows()):
        conn.executemany(
            """
            INSERT INTO projects
            (project_id, title, principal_investigator_id, co_pis, start_date, end_date,
             funding_agency, sanctioned_amount_inr_crores, status, research_area, access_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
    return count_rows(conn, "projects")


def seed_funding_records(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "funding_records")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    institution_ids = [row[0] for row in conn.execute("SELECT institution_id FROM institutions ORDER BY institution_id").fetchall()]

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            agency = AGENCIES[i % len(AGENCIES)]
            fiscal_year = YEARS[i % len(YEARS)]
            institution = institution_ids[i % len(institution_ids)] if institution_ids else None
            yield (
                f"LB3-FUND-{i:06d}",
                f"LB3-RES-{i % max(1, CI_TARGETS['researchers']):06d}",
                institution,
                f"LB3-PROJ-{i % max(1, CI_TARGETS['projects']):06d}",
                agency,
                round(10_000_000 + (i % 60) * 450_000, 2),
                fiscal_year,
                f"{fiscal_year[:4]}-04-01",
                f"{int(fiscal_year[:4]) + 1}-03-31",
                f"LB3 {agency} grant {i:06d}",
                1,
            )

    for batch in batched(rows()):
        conn.executemany(
            """
            INSERT INTO funding_records
            (funding_id, researcher_id, institution_id, project_id, agency, amount, fiscal_year,
             start_date, end_date, title, access_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
    return count_rows(conn, "funding_records")


def seed_structured_patents(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "patents")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            area = PUBLICATION_AREAS[i % len(PUBLICATION_AREAS)]
            institution = INSTITUTION_PROFILES[i % len(INSTITUTION_PROFILES)][1]
            filed_year = 2021 + (i % 5)
            status = "Granted" if i % 3 else "Filed"
            yield (
                f"LB3-PATENT-{i:06d}",
                f"LB3 {area} patent asset {i:06d}",
                f"LB3-RES-{i % max(1, CI_TARGETS['researchers']):06d}",
                institution,
                "Indian Patent Office",
                f"LB3-IN-{filed_year}-{i:06d}",
                f"{filed_year}-05-{(i % 27) + 1:02d}",
                f"{filed_year + 1}-08-{(i % 27) + 1:02d}" if status == "Granted" else None,
                status,
                area,
                "Utility",
                8 + (i % 24),
                1,
            )

    for batch in batched(rows()):
        conn.executemany(
            """
            INSERT INTO patents
            (patent_id, title, inventor_ids, applicant_institution, patent_office, application_number,
             filing_date, grant_date, status, research_area, patent_type, claims_count, access_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
    return count_rows(conn, "patents")


def seed_collaborations(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "collaborations")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    countries = ["USA", "Germany", "Japan", "United Kingdom", "Singapore", "France"]
    types = ["Industry Partnership", "University MoU", "Joint Research", "Technology Transfer"]

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            country = "USA" if i % 4 == 0 else countries[i % len(countries)]
            collaboration_type = "Industry Partnership" if i % 3 == 0 else types[i % len(types)]
            area = PUBLICATION_AREAS[i % len(PUBLICATION_AREAS)]
            yield (
                f"LB3-COLL-{i:06d}",
                f"LB3-RES-{i % max(1, CI_TARGETS['researchers']):06d}",
                f"{country} Research Partner {i % 25}",
                country,
                collaboration_type,
                f"{2020 + (i % 5)}-07-01",
                None if i % 5 else f"{2023 + (i % 3)}-06-30",
                f"{area} collaborative research",
                round(0.4 + (i % 35) * 0.11, 2),
                "Active" if i % 4 else "Completed",
                area,
                1,
            )

    for batch in batched(rows()):
        conn.executemany(
            """
            INSERT INTO collaborations
            (collaboration_id, researcher_ids, partner_institution, partner_country, collaboration_type,
             start_date, end_date, nature_of_work, funding_amount_inr_crores, status, research_area, access_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
    return count_rows(conn, "collaborations")


def seed_labs(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "labs")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    lab_profiles = [
        ("CSIR Hydrogen Catalysis Laboratory", "CSIR National Chemical Laboratory", "Hydrogen Catalysis"),
        ("CSIR Electrochemical Energy Laboratory", "CSIR Central Electrochemical Research Institute", "Renewable Energy"),
        ("IIT Gandhinagar Robotics Laboratory", "IIT Gandhinagar", "Robotics"),
        ("IISc AI Systems Laboratory", "IISc Bengaluru", "AI/ML"),
        ("IIT Bombay Quantum Systems Laboratory", "IIT Bombay", "Quantum Computing"),
        ("IIT Madras Renewable Energy Laboratory", "IIT Madras", "Renewable Energy"),
    ]

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            lab_name, institute, area = lab_profiles[i % len(lab_profiles)]
            state = INSTITUTION_BY_NAME[institute]["state"]
            yield (
                f"LB3-LAB-{i:06d}",
                f"{lab_name} {i // len(lab_profiles) + 1}",
                institution_id(institute),
                area,
                f"{area}; Translational Research; Instrumentation",
                1995 + (i % 28),
                state,
                f"LB3-RES-{i % max(1, CI_TARGETS['researchers']):06d}",
                f"https://example.in/labs/lb3-{i:06d}",
                1,
            )

    for batch in batched(rows()):
        conn.executemany(
            """
            INSERT INTO labs
            (lab_id, name, institution_id, research_area, research_focus_areas, established_year,
             location_state, director_researcher_id, website, access_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
    return count_rows(conn, "labs")


def seed_research_documents(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "research_documents")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    categories = ["Annual Report", "Policy Brief", "Technical Report", "Dataset Note"]

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            area = PUBLICATION_AREAS[i % len(PUBLICATION_AREAS)]
            year = 2020 + (i % 6)
            institute = INSTITUTION_PROFILES[i % len(INSTITUTION_PROFILES)][1]
            yield (
                f"LB3-DOC-{i:06d}",
                f"LB3 {area} research document {i:06d}",
                f"LB3-RES-{i % max(1, CI_TARGETS['researchers']):06d}",
                institute,
                year,
                f"Bounded evidence document for {area}",
                f"{area}; NRG; Evidence",
                area,
                1,
                categories[i % len(categories)],
                f"CORPUS/lb3/documents/{i:06d}.md",
            )

    for batch in batched(rows()):
        conn.executemany(
            """
            INSERT INTO research_documents
            (document_id, title, researcher_ids, affiliation, publication_year, abstract, keywords,
             research_area_tags, access_tier, category, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
    return count_rows(conn, "research_documents")


def seed_incubation_details(conn: sqlite3.Connection, target: int) -> int:
    existing = count_rows(conn, "incubation_details")
    needed = max(0, target - existing)
    if needed == 0:
        return existing

    def rows() -> Iterable[tuple]:
        for i in range(needed):
            institute = INSTITUTES[i % len(INSTITUTES)]
            financial_year = YEARS[i % len(YEARS)]
            incubation_units = 5 + (i % 35)
            yield (
                f"LB3-INC-{i:06d}",
                institute,
                financial_year,
                2 + (i % 20),
                incubation_units,
                round(1_000_000 + incubation_units * 125_000 + (i % 17) * 50_000, 2),
                1,
            )

    for batch in batched(rows()):
        conn.executemany(
            """
            INSERT INTO incubation_details
            (id, institute, financial_year, no_of_pre_incubation_units, no_of_incubation_units,
             income_generated_incubation, access_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
    return count_rows(conn, "incubation_details")


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
    parser.add_argument(
        "--profile",
        choices=("full", "ci"),
        default=os.getenv("NRG_SEED_PROFILE", "full"),
        help="Use smaller deterministic row counts for CI collection/runtime gates.",
    )
    args = parser.parse_args()
    targets = CI_TARGETS if args.profile == "ci" else TARGETS

    started = datetime.now(UTC).isoformat()
    with connect() as conn:
        ensure_schema(conn)
        delete_owned_rows(conn)
        conn.commit()
        summary = {
            "institutions": seed_institutions(conn, targets["institutions"]),
            "researchers": seed_researchers(conn, targets["researchers"]),
            "academic_courses_details": seed_courses(conn, targets["academic_courses_details"]),
            "innovations_at_various_stages_of_technology_readiness_level": seed_trl(
                conn,
                targets["innovations_at_various_stages_of_technology_readiness_level"],
            ),
            "innovation_grant_from_govt": seed_grants(conn, targets["innovation_grant_from_govt"]),
            "combined_ipo_patent_data": seed_patents(conn, targets["combined_ipo_patent_data"]),
            "publications": seed_publications(conn, targets["publications"]),
            "researcher_publications": seed_researcher_publications(conn, targets["researcher_publications"]),
            "projects": seed_projects(conn, targets["projects"]),
            "funding_records": seed_funding_records(conn, targets["funding_records"]),
            "patents": seed_structured_patents(conn, targets["patents"]),
            "collaborations": seed_collaborations(conn, targets["collaborations"]),
            "labs": seed_labs(conn, targets["labs"]),
            "research_documents": seed_research_documents(conn, targets["research_documents"]),
            "incubation_details": seed_incubation_details(conn, targets["incubation_details"]),
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
