#!/usr/bin/env python3
"""Ingest the full National Research Database CSV dump into SQLite.

The ingest is intentionally deterministic:
- create a fresh SQLite database from src/data/schema/nrg_full_schema.sql
- load source CSV rows as-is, preserving ID namespaces
- parse research document metadata from .txt YAML-like frontmatter
- atomically replace the target DB only after a successful load
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = Path("/Users/srujansai/Desktop/NRG DB/National_Research_Database")
DEFAULT_DB_PATH = REPO_ROOT / "nrg_research.db"
DEFAULT_SCHEMA_PATH = REPO_ROOT / "src/data/schema/nrg_full_schema.sql"

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

EXPECTED_COUNTS = {
    "researchers": 5615,
    "publications": 12000,
    "projects": 8049,
    "funding_records": 15435,
    "labs": 889,
    "patents": 3000,
    "collaborations": 5000,
    "research_documents": 3310,
}


def ingest_nrg_database(
    source_dir: str | Path = DEFAULT_SOURCE_DIR,
    db_path: str | Path = DEFAULT_DB_PATH,
    schema_path: str | Path = DEFAULT_SCHEMA_PATH,
) -> dict[str, Any]:
    """Create a fresh DB and load all NRG source files."""
    source = Path(source_dir)
    target = Path(db_path)
    schema = Path(schema_path)

    _validate_source(source)
    if not schema.exists():
        raise FileNotFoundError(f"Schema file not found: {schema}")

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.with_suffix(f"{target.suffix}.tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    conn = sqlite3.connect(tmp_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(schema.read_text(encoding="utf-8"))
        _load_all(source, conn)
        counts = count_tables(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        if tmp_path.exists():
            tmp_path.unlink()
        raise
    else:
        conn.close()
        tmp_path.replace(target)

    return {"db_path": str(target), "counts": counts}


def count_tables(conn: sqlite3.Connection, tables: Iterable[str] = TABLES) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in tables:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return counts


def _validate_source(source: Path) -> None:
    required = [
        "researchers.csv",
        "publications.csv",
        "projects.csv",
        "funding_transactions.csv",
        "labs_institutions.csv",
        "patents.csv",
        "collaborations.csv",
    ]
    missing = [name for name in required if not (source / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing source files in {source}: {', '.join(missing)}")
    if not (source / "Research_Documents").is_dir():
        raise FileNotFoundError(f"Missing Research_Documents directory in {source}")


def _load_all(source: Path, conn: sqlite3.Connection) -> None:
    now = _now()
    institution_rows = _build_institutions(source, now)
    _insert_many(conn, "institutions", institution_rows)
    _insert_many(conn, "researchers", _map_researchers(source / "researchers.csv", now))
    publications, researcher_publications = _map_publications(source / "publications.csv", now)
    _insert_many(conn, "publications", publications)
    _insert_many(conn, "researcher_publications", researcher_publications)
    _insert_many(conn, "projects", _map_projects(source / "projects.csv", now))
    _insert_many(conn, "funding_records", _map_funding(source / "funding_transactions.csv", now))
    _insert_many(conn, "labs", _map_labs(source / "labs_institutions.csv", now))
    _insert_many(conn, "patents", _map_patents(source / "patents.csv", now))
    _insert_many(conn, "collaborations", _map_collaborations(source / "collaborations.csv", now))
    _insert_many(conn, "research_documents", _map_research_documents(source / "Research_Documents", now))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = []
        for row in csv.DictReader(handle):
            row.pop(None, None)
            rows.append(row)
        return rows


def _insert_many(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    columns = list(rows[0])
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(columns)
    values = [tuple(row.get(column) for column in columns) for row in rows]
    conn.executemany(
        f"INSERT OR REPLACE INTO {table} ({column_sql}) VALUES ({placeholders})",
        values,
    )


def _build_institutions(source: Path, now: str) -> list[dict[str, Any]]:
    institutions: dict[str, dict[str, Any]] = {}

    for row in _read_csv(source / "researchers.csv"):
        affiliation = _clean(row.get("affiliation"))
        if affiliation:
            institutions.setdefault(
                affiliation,
                {
                    "institution_id": affiliation,
                    "name": affiliation,
                    "type": None,
                    "state": _clean(row.get("state")) or "Unknown",
                    "country": "IN",
                    "founded_year": None,
                    "website": None,
                    "created_at": now,
                    "updated_at": now,
                },
            )

    for row in _read_csv(source / "labs_institutions.csv"):
        affiliation = _clean(row.get("affiliation"))
        if affiliation:
            institutions.setdefault(
                affiliation,
                {
                    "institution_id": affiliation,
                    "name": affiliation,
                    "type": None,
                    "state": _clean(row.get("location_state")) or "Unknown",
                    "country": "IN",
                    "founded_year": None,
                    "website": None,
                    "created_at": now,
                    "updated_at": now,
                },
            )

    return list(institutions.values())


def _map_researchers(path: Path, now: str) -> list[dict[str, Any]]:
    rows = []
    for row in _read_csv(path):
        tier_access = _clean(row.get("tier_access"))
        rows.append(
            {
                "researcher_id": _required(row, "researcher_id"),
                "name": _required(row, "full_name"),
                "institution_id": _clean(row.get("affiliation")),
                "department": _clean(row.get("department")),
                "state": _required(row, "state"),
                "research_area": _clean(row.get("primary_research_area")),
                "secondary_research_areas": _clean(row.get("secondary_research_areas")),
                "years_experience": _int(row.get("years_experience")),
                "year_joined": None,
                "h_index": _int(row.get("h_index")),
                "total_funding_received_inr_crores": _float(row.get("total_funding_received_inr_crores")),
                "email": _clean(row.get("email")),
                "phone": _clean(row.get("phone")),
                "orcid": None,
                "tier_access": tier_access,
                "access_tier": tier_to_int(tier_access),
                "created_at": now,
                "updated_at": now,
            }
        )
    return rows


def _map_publications(path: Path, now: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    publications = []
    researcher_publications = []
    for row in _read_csv(path):
        publication_id = _required(row, "publication_id")
        publications.append(
            {
                "publication_id": publication_id,
                "title": _required(row, "title"),
                "abstract": None,
                "authors": _clean(row.get("authors")),
                "researcher_ids": _clean(row.get("researcher_ids")),
                "venue": _clean(row.get("journal_name")),
                "year": _int(row.get("publication_year")),
                "volume": _clean(row.get("volume")),
                "issue": _clean(row.get("issue")),
                "pages": _clean(row.get("pages")),
                "doi": _clean(row.get("doi")),
                "pmid": None,
                "citations": _int(row.get("citations")),
                "impact_factor": _float(row.get("impact_factor")),
                "publication_type": _clean(row.get("publication_type")),
                "research_area": _clean(row.get("research_area")),
                "access_tier": 1,
                "created_at": now,
                "updated_at": now,
            }
        )
        for index, researcher_id in enumerate(_split_ids(row.get("researcher_ids")), start=1):
            researcher_publications.append(
                {
                    "researcher_id": researcher_id,
                    "publication_id": publication_id,
                    "author_order": index,
                }
            )
    return publications, researcher_publications


def _map_projects(path: Path, now: str) -> list[dict[str, Any]]:
    return [
        {
            "project_id": _required(row, "project_id"),
            "title": _required(row, "title"),
            "principal_investigator_id": _required(row, "principal_investigator_id"),
            "co_pis": _clean(row.get("co_pis")),
            "start_date": _clean(row.get("start_date")),
            "end_date": _clean(row.get("end_date")),
            "funding_agency": _clean(row.get("funding_agency")),
            "sanctioned_amount_inr_crores": _float(row.get("sanctioned_amount_inr_crores")),
            "status": _clean(row.get("status")),
            "research_area": _clean(row.get("research_area")),
            "access_tier": 1,
            "created_at": now,
            "updated_at": now,
        }
        for row in _read_project_csv(path)
    ]


def _map_funding(path: Path, now: str) -> list[dict[str, Any]]:
    return [
        {
            "funding_id": _required(row, "transaction_id"),
            "researcher_id": None,
            "institution_id": None,
            "project_id": _clean(row.get("project_id")),
            "agency": _clean(row.get("agency")),
            "amount": _float(row.get("amount_released_inr_crores")),
            "amount_released_inr_crores": _float(row.get("amount_released_inr_crores")),
            "fiscal_year": _clean(row.get("fiscal_year")),
            "start_date": None,
            "end_date": None,
            "title": None,
            "access_tier": 1,
            "created_at": now,
            "updated_at": now,
        }
        for row in _read_csv(path)
    ]


def _map_labs(path: Path, now: str) -> list[dict[str, Any]]:
    rows = []
    for row in _read_csv(path):
        focus = _clean(row.get("research_focus_areas"))
        rows.append(
            {
                "lab_id": _required(row, "lab_id"),
                "name": _required(row, "lab_name"),
                "institution_id": _clean(row.get("affiliation")),
                "research_area": _first_pipe_value(focus),
                "research_focus_areas": focus,
                "established_year": None,
                "location_state": _clean(row.get("location_state")),
                "director_researcher_id": _clean_researcher_id(row.get("director_researcher_id")),
                "website": None,
                "created_at": now,
                "updated_at": now,
            }
        )
    return rows


def _read_project_csv(path: Path) -> list[dict[str, str]]:
    """Read projects.csv, repairing rare unquoted commas in project titles."""
    columns = [
        "project_id",
        "title",
        "principal_investigator_id",
        "co_pis",
        "start_date",
        "end_date",
        "funding_agency",
        "sanctioned_amount_inr_crores",
        "status",
        "research_area",
    ]
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header != columns:
            raise ValueError(f"Unexpected projects.csv header: {header}")
        for raw in reader:
            if len(raw) == len(columns):
                rows.append(dict(zip(columns, raw)))
                continue

            pi_index = next(
                (
                    index
                    for index, value in enumerate(raw[2:], start=2)
                    if value.strip().startswith(("RES_", "RES-"))
                ),
                None,
            )
            if pi_index is None or len(raw) - pi_index < 8:
                raise ValueError(f"Cannot repair malformed projects.csv row: {raw}")

            repaired = [
                raw[0],
                ",".join(raw[1:pi_index]).strip(),
                *raw[pi_index : pi_index + 7],
                ",".join(raw[pi_index + 7 :]).strip(),
            ]
            rows.append(dict(zip(columns, repaired)))
    return rows


def _map_patents(path: Path, now: str) -> list[dict[str, Any]]:
    return [
        {
            "patent_id": _required(row, "patent_id"),
            "title": _required(row, "title"),
            "inventor_ids": _clean(row.get("inventor_ids")),
            "applicant_institution": _clean(row.get("applicant_institution")),
            "patent_office": _clean(row.get("patent_office")),
            "application_number": _clean(row.get("application_number")),
            "filing_date": _clean(row.get("filing_date")),
            "grant_date": _clean(row.get("grant_date")),
            "status": _clean(row.get("status")),
            "research_area": _clean(row.get("research_area")),
            "patent_type": _clean(row.get("patent_type")),
            "claims_count": _int(row.get("claims_count")),
            "access_tier": 1,
            "created_at": now,
            "updated_at": now,
        }
        for row in _read_csv(path)
    ]


def _map_collaborations(path: Path, now: str) -> list[dict[str, Any]]:
    return [
        {
            "collaboration_id": _required(row, "collaboration_id"),
            "researcher_ids": _clean(row.get("researcher_ids")),
            "partner_institution": _clean(row.get("partner_institution")),
            "partner_country": _clean(row.get("partner_country")),
            "collaboration_type": _clean(row.get("collaboration_type")),
            "start_date": _clean(row.get("start_date")),
            "end_date": _clean(row.get("end_date")),
            "nature_of_work": _clean(row.get("nature_of_work")),
            "funding_amount_inr_crores": _float(row.get("funding_amount_inr_crores")),
            "status": _clean(row.get("status")),
            "research_area": _clean(row.get("research_area")),
            "access_tier": 1,
            "created_at": now,
            "updated_at": now,
        }
        for row in _read_csv(path)
    ]


def _map_research_documents(docs_dir: Path, now: str) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(docs_dir.glob("*.txt")):
        parsed = parse_research_document(path)
        if not parsed.get("document_id"):
            continue
        rows.append(
            {
                "document_id": parsed["document_id"],
                "title": parsed.get("title") or parsed["document_id"],
                "researcher_ids": _pipe(parsed.get("researcher_ids")),
                "affiliation": parsed.get("affiliation"),
                "publication_year": _int(parsed.get("publication_year")),
                "abstract": parsed.get("abstract"),
                "keywords": _pipe(parsed.get("keywords")),
                "research_area_tags": _pipe(parsed.get("research_area_tags")),
                "access_tier": parsed.get("access_tier"),
                "category": parsed.get("category"),
                "file_path": str(path),
                "created_at": now,
                "updated_at": now,
            }
        )
    return rows


def parse_research_document(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter = _parse_frontmatter(text)
    body = text.split("---", 2)[2] if text.startswith("---") and text.count("---") >= 2 else text
    frontmatter.setdefault("document_id", path.stem)
    frontmatter.setdefault("abstract", _extract_abstract(body))
    return frontmatter


def _parse_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    parsed: dict[str, Any] = {}
    for raw_line in parts[1].splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = _parse_frontmatter_value(value.strip())
    return parsed


def _parse_frontmatter_value(value: str) -> Any:
    if value == "":
        return None
    if value.startswith("[") and value.endswith("]"):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return [item.strip().strip('"').strip("'") for item in value.strip("[]").split(",") if item.strip()]
    return value.strip('"').strip("'")


def _extract_abstract(body: str) -> str | None:
    match = re.search(
        r"(?is)##\s+Abstract\s*\n+(.*?)(?:\n---|\n##\s+|\Z)",
        body,
    )
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()


def tier_to_int(value: str | None) -> int:
    tier = (value or "").lower()
    if "tier2" in tier or "policy" in tier or "government" in tier:
        return 2
    if "tier3" in tier or "analyst" in tier or "industry" in tier:
        return 3
    return 1


def _split_ids(value: str | None) -> list[str]:
    cleaned = _clean(value)
    if not cleaned:
        return []
    delimiter = "|" if "|" in cleaned else ";"
    return [item.strip() for item in cleaned.split(delimiter) if item.strip()]


def _pipe(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    if isinstance(value, tuple):
        return "|".join(str(item) for item in value)
    return str(value).replace(";", "|")


def _first_pipe_value(value: str | None) -> str | None:
    if not value:
        return None
    return value.split("|", 1)[0].strip() or None


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _clean_researcher_id(value: Any) -> str | None:
    cleaned = _clean(value)
    if not cleaned:
        return None
    match = re.match(r"^(RES[-_]\d+)", cleaned)
    return match.group(1) if match else cleaned


def _required(row: dict[str, Any], column: str) -> str:
    value = _clean(row.get(column))
    if not value:
        raise ValueError(f"Missing required column {column} in row {row}")
    return value


def _int(value: Any) -> int | None:
    cleaned = _clean(value)
    if cleaned is None:
        return None
    return int(float(cleaned))


def _float(value: Any) -> float | None:
    cleaned = _clean(value)
    if cleaned is None:
        return None
    return float(cleaned)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest full NRG CSV database into SQLite")
    parser.add_argument("--source-dir", "--csv-dir", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--schema-path", default=str(DEFAULT_SCHEMA_PATH))
    parser.add_argument("--json", action="store_true", help="Print machine-readable result")
    args = parser.parse_args()

    result = ingest_nrg_database(
        source_dir=Path(args.source_dir),
        db_path=Path(args.db_path),
        schema_path=Path(args.schema_path),
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for table in TABLES:
            expected = EXPECTED_COUNTS.get(table)
            actual = result["counts"][table]
            suffix = f" / expected {expected}" if expected is not None else ""
            print(f"{table}: {actual}{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
