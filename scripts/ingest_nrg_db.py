#!/usr/bin/env python3
"""
Ingest NRG CSVs into SQLite.

Source: /Users/srujansai/Desktop/NRG DB/National_Research_Database/
Target: nrg_research.db (project root)

Idempotent: drops and recreates tables on each run.
"""

import csv
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TABLES = [
    "researchers",
    "publications",
    "projects",
    "funding_records",
    "labs",
    "patents",
    "collaborations",
    "research_documents",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA_PATH = REPO_ROOT / "src" / "data" / "schema" / "nrg_full_schema.sql"
DEFAULT_SOURCE_DIR = Path("/Users/srujansai/Desktop/NRG DB/National_Research_Database")
DEFAULT_DB_PATH = REPO_ROOT / "nrg_research.db"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    with open(schema_path, "r") as f:
        conn.executescript(f.read())


# ---------------------------------------------------------------------------
# Frontmatter parser
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML or JSON frontmatter and body from a research document .txt file."""
    # Try YAML frontmatter
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n+(.*)", text, re.DOTALL)
    if match:
        try:
            meta = yaml.safe_load(match.group(1))
        except Exception:
            meta = {}
        body = match.group(2).strip()
        return meta if isinstance(meta, dict) else {}, body

    # Try JSON frontmatter inside triple backticks
    match = re.match(r"^```json\s*\n(.*?)\n```\s*\n+(.*)", text, re.DOTALL)
    if match:
        try:
            json_str = match.group(1)
            # Fix trailing commas (e.g. "researcher_ids":,)
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            # Fix bare commas after colons
            json_str = re.sub(r':(\s*[,}\]])', r':null\1', json_str)
            meta = json.loads(json_str)
        except Exception:
            meta = {}
        body = match.group(2).strip()
        return meta if isinstance(meta, dict) else {}, body

    # Try JSON frontmatter after "Metadata:" label
    match = re.match(r"^Metadata:\s*\n(\{.*?)\n\}\s*\n+(.*)", text, re.DOTALL)
    if match:
        try:
            json_str = match.group(1) + "}"
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            json_str = re.sub(r':(\s*[,}\]])', r':null\1', json_str)
            meta = json.loads(json_str)
        except Exception:
            meta = {}
        body = match.group(2).strip()
        return meta if isinstance(meta, dict) else {}, body

    return {}, text


def _tier_to_int(tier_text: Optional[str]) -> int:
    """Map tier text to integer for access_tier column."""
    if not tier_text:
        return 1
    tier_text = str(tier_text).lower()
    if "tier1" in tier_text or "tier_1" in tier_text:
        return 1
    if "tier2" in tier_text or "tier_2" in tier_text:
        return 2
    if "tier3" in tier_text or "tier_3" in tier_text:
        return 3
    return 1


# ---------------------------------------------------------------------------
# CSV loaders
# ---------------------------------------------------------------------------

def load_researchers(conn: sqlite3.Connection, source_dir: Path) -> int:
    rows = 0
    skipped = 0
    path = source_dir / "researchers.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                tier_text = row.get("tier_access")
                conn.execute(
                    """
                    INSERT INTO researchers
                    (researcher_id, name, institution_id, state, department,
                     research_area, secondary_research_areas, years_experience,
                     year_joined, h_index, total_funding_received_inr_crores,
                     email, phone, orcid, tier_access, access_tier)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["researcher_id"],
                        row["full_name"],
                        row["affiliation"],
                        row["state"],
                        row.get("department"),
                        row.get("primary_research_area"),
                        row.get("secondary_research_areas"),
                        int(row["years_experience"]) if row.get("years_experience") else None,
                        None,  # year_joined not in CSV
                        int(row["h_index"]) if row.get("h_index") else None,
                        float(row["total_funding_received_inr_crores"]) if row.get("total_funding_received_inr_crores") else None,
                        row.get("email"),
                        row.get("phone"),
                        None,  # orcid not in CSV
                        tier_text,
                        _tier_to_int(tier_text),
                    ),
                )
                rows += 1
            except Exception as e:
                skipped += 1
                if skipped <= 3:
                    print(f"   ⚠️  Skipping malformed row {row.get('researcher_id')}: {e}")
    if skipped > 3:
        print(f"   ⚠️  ... and {skipped - 3} more malformed rows skipped")
    return rows


def load_publications(conn: sqlite3.Connection, source_dir: Path) -> int:
    rows = 0
    skipped = 0
    path = source_dir / "publications.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute(
                    """
                    INSERT INTO publications
                    (publication_id, title, abstract, authors, researcher_ids,
                     venue, year, volume, issue, pages, doi, pmid,
                     citations, impact_factor, publication_type, research_area)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["publication_id"],
                        row["title"],
                        None,  # abstract not in CSV
                        row.get("authors"),
                        row.get("researcher_ids"),
                        row.get("journal_name"),
                        int(row["publication_year"]) if row.get("publication_year") else None,
                        row.get("volume"),
                        row.get("issue"),
                        row.get("pages"),
                        row.get("doi"),
                        None,  # pmid not in CSV
                        int(row["citations"]) if row.get("citations") else None,
                        float(row["impact_factor"]) if row.get("impact_factor") else None,
                        row.get("publication_type"),
                        row.get("research_area"),
                    ),
                )
                rows += 1
            except Exception as e:
                skipped += 1
                if skipped <= 3:
                    print(f"   ⚠️  Skipping malformed row {row.get('publication_id')}: {e}")
    if skipped > 3:
        print(f"   ⚠️  ... and {skipped - 3} more malformed rows skipped")
    return rows


def load_projects(conn: sqlite3.Connection, source_dir: Path) -> int:
    rows = 0
    skipped = 0
    path = source_dir / "projects.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute(
                    """
                    INSERT INTO projects
                    (project_id, title, principal_investigator_id, co_pis,
                     start_date, end_date, funding_agency,
                     sanctioned_amount_inr_crores, status, research_area)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["project_id"],
                        row["title"],
                        row.get("principal_investigator_id"),
                        row.get("co_pis"),
                        row.get("start_date"),
                        row.get("end_date"),
                        row.get("funding_agency"),
                        float(row["sanctioned_amount_inr_crores"]) if row.get("sanctioned_amount_inr_crores") else None,
                        row.get("status"),
                        row.get("research_area"),
                    ),
                )
                rows += 1
            except Exception as e:
                skipped += 1
                if skipped <= 3:
                    print(f"   ⚠️  Skipping malformed row {row.get('project_id')}: {e}")
    if skipped > 3:
        print(f"   ⚠️  ... and {skipped - 3} more malformed rows skipped")
    return rows


def load_funding_records(conn: sqlite3.Connection, source_dir: Path) -> int:
    rows = 0
    skipped = 0
    path = source_dir / "funding_transactions.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute(
                    """
                    INSERT INTO funding_records
                    (funding_id, researcher_id, institution_id, project_id,
                     fiscal_year, agency, amount, start_date, end_date, title)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["transaction_id"],
                        None,  # researcher_id not in CSV
                        None,  # institution_id not in CSV
                        row.get("project_id"),
                        row.get("fiscal_year"),
                        row.get("agency"),
                        float(row["amount_released_inr_crores"]) if row.get("amount_released_inr_crores") else None,
                        None,  # start_date not in CSV
                        None,  # end_date not in CSV
                        None,  # title not in CSV
                    ),
                )
                rows += 1
            except Exception as e:
                skipped += 1
                if skipped <= 3:
                    print(f"   ⚠️  Skipping malformed row {row.get('transaction_id')}: {e}")
    if skipped > 3:
        print(f"   ⚠️  ... and {skipped - 3} more malformed rows skipped")
    return rows


def load_labs(conn: sqlite3.Connection, source_dir: Path) -> int:
    rows = 0
    skipped = 0
    path = source_dir / "labs_institutions.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute(
                    """
                    INSERT INTO labs
                    (lab_id, name, institution_id, research_area,
                     research_focus_areas, established_year, location_state,
                     director_researcher_id, website)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["lab_id"],
                        row["lab_name"],
                        row.get("affiliation"),
                        row.get("research_focus_areas"),
                        row.get("research_focus_areas"),
                        None,  # established_year not in CSV
                        row.get("location_state"),
                        row.get("director_researcher_id"),
                        None,  # website not in CSV
                    ),
                )
                rows += 1
            except Exception as e:
                skipped += 1
                if skipped <= 3:
                    print(f"   ⚠️  Skipping malformed row {row.get('lab_id')}: {e}")
    if skipped > 3:
        print(f"   ⚠️  ... and {skipped - 3} more malformed rows skipped")
    return rows


def load_patents(conn: sqlite3.Connection, source_dir: Path) -> int:
    rows = 0
    skipped = 0
    path = source_dir / "patents.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute(
                    """
                    INSERT INTO patents
                    (patent_id, title, inventor_ids, applicant_institution,
                     patent_office, application_number, filing_date, grant_date,
                     status, research_area, patent_type, claims_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["patent_id"],
                        row["title"],
                        row.get("inventor_ids"),
                        row.get("applicant_institution"),
                        row.get("patent_office"),
                        row.get("application_number"),
                        row.get("filing_date"),
                        row.get("grant_date"),
                        row.get("status"),
                        row.get("research_area"),
                        row.get("patent_type"),
                        int(row["claims_count"]) if row.get("claims_count") else None,
                    ),
                )
                rows += 1
            except Exception as e:
                skipped += 1
                if skipped <= 3:
                    print(f"   ⚠️  Skipping malformed row {row.get('patent_id')}: {e}")
    if skipped > 3:
        print(f"   ⚠️  ... and {skipped - 3} more malformed rows skipped")
    return rows


def load_collaborations(conn: sqlite3.Connection, source_dir: Path) -> int:
    rows = 0
    skipped = 0
    path = source_dir / "collaborations.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute(
                    """
                    INSERT INTO collaborations
                    (collaboration_id, researcher_ids, partner_institution,
                     partner_country, collaboration_type, start_date, end_date,
                     nature_of_work, funding_amount_inr_crores, status, research_area)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["collaboration_id"],
                        row.get("researcher_ids"),
                        row.get("partner_institution"),
                        row.get("partner_country"),
                        row.get("collaboration_type"),
                        row.get("start_date"),
                        row.get("end_date"),
                        row.get("nature_of_work"),
                        float(row["funding_amount_inr_crores"]) if row.get("funding_amount_inr_crores") else None,
                        row.get("status"),
                        row.get("research_area"),
                    ),
                )
                rows += 1
            except Exception as e:
                skipped += 1
                if skipped <= 3:
                    print(f"   ⚠️  Skipping malformed row {row.get('collaboration_id')}: {e}")
    if skipped > 3:
        print(f"   ⚠️  ... and {skipped - 3} more malformed rows skipped")
    return rows


def load_research_documents(conn: sqlite3.Connection, source_dir: Path) -> int:
    rows = 0
    skipped = 0
    docs_dir = source_dir / "Research_Documents"
    txt_files = sorted(docs_dir.glob("*.txt"))
    for txt_path in txt_files:
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read()
            meta, body = parse_frontmatter(text)
            if not meta:
                skipped += 1
                if skipped <= 3:
                    print(f"   ⚠️  Skipping {txt_path.name}: no parseable frontmatter")
                continue

            doc_id = meta.get("document_id", txt_path.stem)
            researcher_ids = meta.get("researcher_ids", [])
            if isinstance(researcher_ids, list):
                researcher_ids = "|".join(str(r) for r in researcher_ids)
            else:
                researcher_ids = str(researcher_ids) if researcher_ids else None

            keywords = meta.get("keywords", [])
            if isinstance(keywords, list):
                keywords = "|".join(str(k) for k in keywords)
            else:
                keywords = str(keywords) if keywords else None

            tags = meta.get("research_area_tags", [])
            if isinstance(tags, list):
                tags = "|".join(str(t) for t in tags)
            else:
                tags = str(tags) if tags else None

            abstract = meta.get("abstract")
            if not abstract and body:
                abstract = body[:2000]

            conn.execute(
                """
                INSERT INTO research_documents
                (document_id, title, researcher_ids, affiliation,
                 publication_year, abstract, keywords, research_area_tags,
                 access_tier, category, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    meta.get("title"),
                    researcher_ids,
                    meta.get("affiliation"),
                    int(meta["publication_year"]) if meta.get("publication_year") else None,
                    abstract,
                    keywords,
                    tags,
                    _tier_to_int(meta.get("access_tier")),
                    meta.get("category"),
                    str(txt_path),
                ),
            )
            rows += 1
        except Exception as e:
            skipped += 1
            if skipped <= 3:
                print(f"   ⚠️  Skipping {txt_path.name}: {e}")
    if skipped > 3:
        print(f"   ⚠️  ... and {skipped - 3} more files skipped")
    return rows


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def ingest_nrg_database(
    source_dir: Path = DEFAULT_SOURCE_DIR,
    db_path: Path = DEFAULT_DB_PATH,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
) -> dict:
    """Ingest all NRG CSVs and documents into a fresh SQLite database.

    Returns:
        dict with keys "counts" mapping table names to row counts.
    """
    if db_path.exists():
        db_path.unlink()

    conn = get_conn(db_path)
    init_schema(conn, schema_path)

    counts = {}
    counts["researchers"] = load_researchers(conn, source_dir)
    counts["publications"] = load_publications(conn, source_dir)
    counts["projects"] = load_projects(conn, source_dir)
    counts["funding_records"] = load_funding_records(conn, source_dir)
    counts["labs"] = load_labs(conn, source_dir)
    counts["patents"] = load_patents(conn, source_dir)
    counts["collaborations"] = load_collaborations(conn, source_dir)
    counts["research_documents"] = load_research_documents(conn, source_dir)

    conn.commit()
    conn.close()
    return {"counts": counts}


def main() -> None:
    print(f"🗄  Creating / overwriting {DEFAULT_DB_PATH}")
    result = ingest_nrg_database()
    counts = result["counts"]
    for table, count in counts.items():
        print(f"📥 {table}: {count} rows")
    print("✅ All data loaded successfully")


if __name__ == "__main__":
    main()
