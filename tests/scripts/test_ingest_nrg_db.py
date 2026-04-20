import csv
import sqlite3
from pathlib import Path


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _build_source_tree(root: Path) -> None:
    _write_csv(
        root / "researchers.csv",
        [
            {
                "researcher_id": "RES_1001",
                "full_name": "Dr. Rajesh Patel",
                "affiliation": "IIT Gandhinagar",
                "department": "Computer Science and Engineering",
                "primary_research_area": "AI/ML",
                "secondary_research_areas": "Robotics|Data Science",
                "state": "Gujarat",
                "years_experience": "12",
                "h_index": "35",
                "total_funding_received_inr_crores": "8.5",
                "email": "rajesh@example.edu",
                "phone": "9876543210",
                "tier_access": "Tier1_Researcher",
            }
        ],
    )
    _write_csv(
        root / "publications.csv",
        [
            {
                "publication_id": "PUB-0001",
                "title": "AI for Bharat",
                "authors": "A. Patel, B. Shah",
                "researcher_ids": "RES_1001|RES_1002",
                "journal_name": "Nature India",
                "publication_year": "2024",
                "volume": "12",
                "issue": "4",
                "pages": "10-18",
                "doi": "10.1000/test",
                "citations": "21",
                "research_area": "AI/ML",
                "publication_type": "Journal",
                "impact_factor": "5.4",
            }
        ],
    )
    _write_csv(
        root / "projects.csv",
        [
            {
                "project_id": "PRJ_5001",
                "title": "Sovereign AI",
                "principal_investigator_id": "RES_1001",
                "co_pis": "RES_1002|RES_1003",
                "start_date": "2024-04-01",
                "end_date": "2027-03-31",
                "funding_agency": "SERB",
                "sanctioned_amount_inr_crores": "1.25",
                "status": "Ongoing",
                "research_area": "AI/ML",
            }
        ],
    )
    _write_csv(
        root / "funding_transactions.csv",
        [
            {
                "transaction_id": "TXN_9001",
                "project_id": "PRJ_5001",
                "fiscal_year": "2024-2025",
                "amount_released_inr_crores": "0.60",
                "agency": "SERB",
            }
        ],
    )
    _write_csv(
        root / "labs_institutions.csv",
        [
            {
                "lab_id": "LAB_001",
                "lab_name": "Human-AI Lab",
                "affiliation": "IIT Gandhinagar",
                "location_state": "Gujarat",
                "research_focus_areas": "AI/ML|Cognitive Computing",
                "director_researcher_id": "RES_1001",
            }
        ],
    )
    _write_csv(
        root / "patents.csv",
        [
            {
                "patent_id": "PAT-0001",
                "title": "Method for AI Governance",
                "inventor_ids": "RES_1001|RES_1004",
                "applicant_institution": "IIT Gandhinagar",
                "patent_office": "Indian Patent Office",
                "application_number": "IN/2025/1",
                "filing_date": "2025-01-01",
                "grant_date": "",
                "status": "Filed",
                "research_area": "AI/ML",
                "patent_type": "Utility",
                "claims_count": "14",
            }
        ],
    )
    _write_csv(
        root / "collaborations.csv",
        [
            {
                "collaboration_id": "COLLAB-0001",
                "researcher_ids": "RES_1001|RES_1005",
                "partner_institution": "IISc Bangalore",
                "partner_country": "India",
                "collaboration_type": "Academic",
                "start_date": "2024-01-01",
                "end_date": "2025-01-01",
                "nature_of_work": "Joint research",
                "funding_amount_inr_crores": "0.75",
                "status": "Active",
                "research_area": "AI/ML",
            }
        ],
    )
    docs = root / "Research_Documents"
    docs.mkdir()
    (docs / "DOC-00001.txt").write_text(
        """---
document_id: DOC-00001
title: "Deep Learning for Multilingual NLP in Indian Languages"
researcher_ids: ["RES_1001", "RES_1002"]
affiliation: IIT Gandhinagar
publication_year: 2025
keywords: ["Hindi", "deep learning"]
research_area_tags: ["Deep Learning", "Knowledge Graphs"]
access_tier: Tier1
category: AI/ML
---

# Deep Learning for Multilingual NLP in Indian Languages

## Abstract

This document tests frontmatter parsing for the ingest pipeline.
""",
        encoding="utf-8",
    )


def test_full_schema_contains_real_nrg_tables_and_columns():
    schema = Path("src/data/schema/nrg_full_schema.sql").read_text()

    for table in [
        "projects",
        "patents",
        "collaborations",
        "research_documents",
    ]:
        assert f"CREATE TABLE {table}" in schema

    for column in [
        "department TEXT",
        "secondary_research_areas TEXT",
        "h_index INTEGER",
        "tier_access TEXT",
        "researcher_ids TEXT",
        "project_id TEXT",
        "fiscal_year TEXT",
    ]:
        assert column in schema


def test_ingest_nrg_database_loads_csvs_documents_and_is_idempotent(tmp_path):
    from scripts.ingest_nrg_db import TABLES, ingest_nrg_database

    source_root = tmp_path / "source"
    db_path = tmp_path / "nrg_research.db"
    _build_source_tree(source_root)

    first = ingest_nrg_database(source_dir=source_root, db_path=db_path)
    second = ingest_nrg_database(source_dir=source_root, db_path=db_path)

    assert first["counts"] == second["counts"]
    assert first["counts"] == {table: 1 for table in TABLES}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        researcher = conn.execute("SELECT * FROM researchers").fetchone()
        assert researcher["researcher_id"] == "RES_1001"
        assert researcher["institution_id"] == "IIT Gandhinagar"
        assert researcher["tier_access"] == "Tier1_Researcher"
        assert researcher["access_tier"] == 1

        publication = conn.execute("SELECT * FROM publications").fetchone()
        assert publication["authors"] == "A. Patel, B. Shah"
        assert publication["researcher_ids"] == "RES_1001|RES_1002"
        assert publication["year"] == 2024

        document = conn.execute("SELECT * FROM research_documents").fetchone()
        assert document["document_id"] == "DOC-00001"
        assert document["researcher_ids"] == "RES_1001|RES_1002"
        assert "frontmatter parsing" in document["abstract"]
        assert document["file_path"].endswith("DOC-00001.txt")
    finally:
        conn.close()
