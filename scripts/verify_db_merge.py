#!/usr/bin/env python3
"""Verify that the Desktop NRG source corpus was merged into the project DB.

The script is intentionally read-only: it compares source CSV/text artifacts,
SQLite rows, and optional Qdrant payload coverage, then prints a PASS/FAIL
report without dumping sensitive field values.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_SOURCE_DIR = Path(
    os.getenv(
        "NRG_DATA_SOURCE_DIR",
        str(PROJECT_ROOT / "data" / "National_Research_Database"),
    )
)
DEFAULT_DB_PATH = PROJECT_ROOT / "nrg_research.db"
DEFAULT_QDRANT_COLLECTION = "nrg_research"

EXPECTED_COUNTS = {
    "researchers": 5615,
    "publications": 12000,
    "labs": 890,
    "projects": 8050,
    "patents": 3000,
    "collaborations": 5000,
    "funding_records": 15436,
    "research_documents": 3310,
    "institutions": 181,
}

CSV_HEADERS = {
    "researchers": [
        "researcher_id",
        "full_name",
        "affiliation",
        "department",
        "primary_research_area",
        "secondary_research_areas",
        "state",
        "years_experience",
        "h_index",
        "total_funding_received_inr_crores",
        "email",
        "phone",
        "tier_access",
    ],
    "publications": [
        "publication_id",
        "title",
        "authors",
        "researcher_ids",
        "journal_name",
        "publication_year",
        "volume",
        "issue",
        "pages",
        "doi",
        "citations",
        "research_area",
        "publication_type",
        "impact_factor",
    ],
    "labs": [
        "lab_id",
        "lab_name",
        "affiliation",
        "location_state",
        "research_focus_areas",
        "director_researcher_id",
    ],
    "projects": [
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
    ],
    "patents": [
        "patent_id",
        "title",
        "inventor_ids",
        "applicant_institution",
        "patent_office",
        "application_number",
        "filing_date",
        "grant_date",
        "status",
        "research_area",
        "patent_type",
        "claims_count",
    ],
    "collaborations": [
        "collaboration_id",
        "researcher_ids",
        "partner_institution",
        "partner_country",
        "collaboration_type",
        "start_date",
        "end_date",
        "nature_of_work",
        "funding_amount_inr_crores",
        "status",
        "research_area",
    ],
    "funding_records": [
        "transaction_id",
        "project_id",
        "fiscal_year",
        "amount_released_inr_crores",
        "agency",
    ],
}

CSV_FILES = {
    "researchers": "researchers.csv",
    "publications": "publications.csv",
    "labs": "labs_institutions.csv",
    "projects": "projects.csv",
    "patents": "patents.csv",
    "collaborations": "collaborations.csv",
    "funding_records": "funding_transactions.csv",
}


def _empty_to_none(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value


def _to_int(value: Any) -> int | None:
    value = _empty_to_none(value)
    return int(value) if value is not None else None


def _to_float(value: Any) -> float | None:
    value = _empty_to_none(value)
    return float(value) if value is not None else None


def _split_multi(value: Any) -> tuple[str, ...]:
    value = _empty_to_none(value)
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text.replace("'", '"'))
            if isinstance(parsed, list):
                return tuple(str(item).strip() for item in parsed if str(item).strip())
        except json.JSONDecodeError:
            pass
    parts = re.split(r"[|;]", text)
    return tuple(part.strip().strip("'\"") for part in parts if part.strip().strip("'\""))


def _split_ids(value: Any) -> tuple[str, ...]:
    value = _empty_to_none(value)
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    parts = re.split(r"[|;,]", str(value))
    return tuple(part.strip().strip("'\"") for part in parts if part.strip().strip("'\""))


def _split_embedded_identifier(value: str, pattern: str) -> tuple[str, str] | None:
    match = re.search(pattern, value)
    if not match or match.start() == 0:
        return None
    return value[: match.start()], value[match.start() :]


@dataclass
class SourceRows:
    rows: list[dict[str, Any]]
    repairs: list[str] = field(default_factory=list)
    malformed: list[str] = field(default_factory=list)


def _repair_project_row(row: list[str], line_no: int, expected: int) -> tuple[list[list[str]], str | None]:
    if len(row) == expected:
        return [row], None

    if len(row) == expected + 1 and row and row[0].startswith("PRJ"):
        extra = len(row) - expected
        repaired = [row[0], ",".join(row[1 : 2 + extra]), *row[2 + extra :]]
        if len(repaired) == expected:
            return [repaired], f"projects.csv:{line_no} repaired unescaped title comma"

    if len(row) == (expected * 2) - 1 and len(row) > 9:
        split = _split_embedded_identifier(row[9], r"PRJ[-_]\d+")
        if split:
            first_area, second_id = split
            first = [*row[:9], first_area]
            second = [second_id, *row[10:]]
            if len(first) == expected and len(second) == expected:
                return [first, second], f"projects.csv:{line_no} split glued project records"

    return [], f"projects.csv:{line_no} malformed width {len(row)}"


def _repair_labs_row(row: list[str], line_no: int, expected: int) -> tuple[list[list[str]], str | None]:
    if len(row) == expected:
        return [row], None
    if len(row) == (expected * 2) - 1 and len(row) > 5:
        split = _split_embedded_identifier(row[5], r"LAB[-_]\d+")
        if split:
            first_director, second_id = split
            first = [*row[:5], first_director]
            second = [second_id, *row[6:]]
            if len(first) == expected and len(second) == expected:
                return [first, second], f"labs_institutions.csv:{line_no} split glued lab records"
    return [], f"labs_institutions.csv:{line_no} malformed width {len(row)}"


def _repair_funding_row(row: list[str], line_no: int, expected: int) -> tuple[list[list[str]], str | None]:
    if len(row) == expected:
        return [row], None
    if len(row) == (expected * 2) - 1 and len(row) > 4:
        split = _split_embedded_identifier(row[4], r"TXN[-_]\d+")
        if split:
            first_agency, second_id = split
            first = [*row[:4], first_agency]
            second = [second_id, *row[5:]]
            if len(first) == expected and len(second) == expected:
                return [first, second], f"funding_transactions.csv:{line_no} split glued funding records"
    return [], f"funding_transactions.csv:{line_no} malformed width {len(row)}"


def _repair_csv_row(table: str, row: list[str], line_no: int, expected: int) -> tuple[list[list[str]], str | None]:
    if table == "projects":
        return _repair_project_row(row, line_no, expected)
    if table == "labs":
        return _repair_labs_row(row, line_no, expected)
    if table == "funding_records":
        return _repair_funding_row(row, line_no, expected)
    if len(row) == expected:
        return [row], None
    return [], f"{CSV_FILES[table]}:{line_no} malformed width {len(row)}"


def read_logical_csv_rows(source_dir: Path, table: str) -> SourceRows:
    path = source_dir / CSV_FILES[table]
    expected_header = CSV_HEADERS[table]
    rows: list[dict[str, Any]] = []
    repairs: list[str] = []
    malformed: list[str] = []

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if header != expected_header:
            raise ValueError(f"{path} header mismatch: {header!r}")
        for line_no, raw_row in enumerate(reader, start=2):
            repaired_rows, note = _repair_csv_row(table, raw_row, line_no, len(header))
            if note:
                if "malformed" in note:
                    malformed.append(note)
                else:
                    repairs.append(note)
            for repaired in repaired_rows:
                rows.append(dict(zip(header, repaired)))

    return SourceRows(rows=rows, repairs=repairs, malformed=malformed)


@dataclass(frozen=True)
class CompareSpec:
    table: str
    source_table: str
    id_field: str
    db_id_field: str
    query: str
    mapping: dict[str, tuple[str, Callable[[Any], Any]]]


COMPARE_SPECS = [
    CompareSpec(
        table="researchers",
        source_table="researchers",
        id_field="researcher_id",
        db_id_field="researcher_id",
        query="""
            SELECT r.*, COALESCE(i.name, r.institution_id) AS institution_name
            FROM researchers r
            LEFT JOIN institutions i ON i.institution_id = r.institution_id
        """,
        mapping={
            "researcher_id": ("researcher_id", _empty_to_none),
            "full_name": ("name", _empty_to_none),
            "affiliation": ("institution_name", _empty_to_none),
            "department": ("department", _empty_to_none),
            "primary_research_area": ("research_area", _empty_to_none),
            "secondary_research_areas": ("secondary_research_areas", _split_multi),
            "state": ("state", _empty_to_none),
            "years_experience": ("years_experience", _to_int),
            "h_index": ("h_index", _to_int),
            "total_funding_received_inr_crores": ("total_funding_received_inr_crores", _to_float),
            "email": ("email", _empty_to_none),
            "phone": ("phone", _empty_to_none),
            "tier_access": ("tier_access", _empty_to_none),
        },
    ),
    CompareSpec(
        table="publications",
        source_table="publications",
        id_field="publication_id",
        db_id_field="publication_id",
        query="SELECT * FROM publications",
        mapping={
            "publication_id": ("publication_id", _empty_to_none),
            "title": ("title", _empty_to_none),
            "authors": ("authors", _empty_to_none),
            "researcher_ids": ("researcher_ids", _split_ids),
            "journal_name": ("venue", _empty_to_none),
            "publication_year": ("year", _to_int),
            "volume": ("volume", _empty_to_none),
            "issue": ("issue", _empty_to_none),
            "pages": ("pages", _empty_to_none),
            "doi": ("doi", _empty_to_none),
            "citations": ("citations", _to_int),
            "research_area": ("research_area", _empty_to_none),
            "publication_type": ("publication_type", _empty_to_none),
            "impact_factor": ("impact_factor", _to_float),
        },
    ),
    CompareSpec(
        table="labs",
        source_table="labs",
        id_field="lab_id",
        db_id_field="lab_id",
        query="""
            SELECT l.*, COALESCE(i.name, l.institution_id) AS institution_name
            FROM labs l
            LEFT JOIN institutions i ON i.institution_id = l.institution_id
        """,
        mapping={
            "lab_id": ("lab_id", _empty_to_none),
            "lab_name": ("name", _empty_to_none),
            "affiliation": ("institution_name", _empty_to_none),
            "location_state": ("location_state", _empty_to_none),
            "research_focus_areas": ("research_focus_areas", _split_multi),
            "director_researcher_id": ("director_researcher_id", _empty_to_none),
        },
    ),
    CompareSpec(
        table="projects",
        source_table="projects",
        id_field="project_id",
        db_id_field="project_id",
        query="SELECT * FROM projects",
        mapping={
            "project_id": ("project_id", _empty_to_none),
            "title": ("title", _empty_to_none),
            "principal_investigator_id": ("principal_investigator_id", _empty_to_none),
            "co_pis": ("co_pis", _split_ids),
            "start_date": ("start_date", _empty_to_none),
            "end_date": ("end_date", _empty_to_none),
            "funding_agency": ("funding_agency", _empty_to_none),
            "sanctioned_amount_inr_crores": ("sanctioned_amount_inr_crores", _to_float),
            "status": ("status", _empty_to_none),
            "research_area": ("research_area", _empty_to_none),
        },
    ),
    CompareSpec(
        table="patents",
        source_table="patents",
        id_field="patent_id",
        db_id_field="patent_id",
        query="SELECT * FROM patents",
        mapping={
            "patent_id": ("patent_id", _empty_to_none),
            "title": ("title", _empty_to_none),
            "inventor_ids": ("inventor_ids", _split_ids),
            "applicant_institution": ("applicant_institution", _empty_to_none),
            "patent_office": ("patent_office", _empty_to_none),
            "application_number": ("application_number", _empty_to_none),
            "filing_date": ("filing_date", _empty_to_none),
            "grant_date": ("grant_date", _empty_to_none),
            "status": ("status", _empty_to_none),
            "research_area": ("research_area", _empty_to_none),
            "patent_type": ("patent_type", _empty_to_none),
            "claims_count": ("claims_count", _to_int),
        },
    ),
    CompareSpec(
        table="collaborations",
        source_table="collaborations",
        id_field="collaboration_id",
        db_id_field="collaboration_id",
        query="SELECT * FROM collaborations",
        mapping={
            "collaboration_id": ("collaboration_id", _empty_to_none),
            "researcher_ids": ("researcher_ids", _split_ids),
            "partner_institution": ("partner_institution", _empty_to_none),
            "partner_country": ("partner_country", _empty_to_none),
            "collaboration_type": ("collaboration_type", _empty_to_none),
            "start_date": ("start_date", _empty_to_none),
            "end_date": ("end_date", _empty_to_none),
            "nature_of_work": ("nature_of_work", _empty_to_none),
            "funding_amount_inr_crores": ("funding_amount_inr_crores", _to_float),
            "status": ("status", _empty_to_none),
            "research_area": ("research_area", _empty_to_none),
        },
    ),
    CompareSpec(
        table="funding_records",
        source_table="funding_records",
        id_field="transaction_id",
        db_id_field="funding_id",
        query="SELECT * FROM funding_records",
        mapping={
            "transaction_id": ("funding_id", _empty_to_none),
            "project_id": ("project_id", _empty_to_none),
            "fiscal_year": ("fiscal_year", _empty_to_none),
            "amount_released_inr_crores": ("amount", _to_float),
            "agency": ("agency", _empty_to_none),
        },
    ),
]


class MergeReport:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.lines: list[str] = []

    def ok(self, message: str) -> None:
        self.lines.append(f"PASS {message}")

    def fail(self, message: str) -> None:
        self.errors.append(message)
        self.lines.append(f"FAIL {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        self.lines.append(f"WARN {message}")


def _fetch_db_map(conn: sqlite3.Connection, spec: CompareSpec) -> dict[str, sqlite3.Row]:
    return {str(row[spec.db_id_field]): row for row in conn.execute(spec.query).fetchall()}


def _compare_rows(
    report: MergeReport,
    spec: CompareSpec,
    source_rows: list[dict[str, Any]],
    db_rows: dict[str, sqlite3.Row],
) -> None:
    source_ids = {str(row[spec.id_field]) for row in source_rows}
    db_ids = set(db_rows)
    missing = sorted(source_ids - db_ids)
    extra = sorted(db_ids - source_ids)
    if missing:
        report.fail(f"{spec.table}: {len(missing)} source IDs missing in DB: {missing[:10]}")
    if extra:
        report.fail(f"{spec.table}: {len(extra)} DB IDs absent from source: {extra[:10]}")

    mismatches: list[str] = []
    for source in source_rows:
        row_id = str(source[spec.id_field])
        db_row = db_rows.get(row_id)
        if db_row is None:
            continue
        for source_field, (db_field, normalizer) in spec.mapping.items():
            source_value = normalizer(source.get(source_field))
            db_value = normalizer(db_row[db_field])
            if source_value != db_value:
                mismatches.append(f"{row_id}:{source_field}->{db_field}")
                break

    if mismatches:
        report.fail(f"{spec.table}: {len(mismatches)} row mismatches: {mismatches[:10]}")
    elif not missing and not extra:
        report.ok(f"{spec.table}: all {len(source_rows)} logical source rows match DB rows")


def _check_counts(
    report: MergeReport,
    conn: sqlite3.Connection,
    source_by_table: dict[str, SourceRows],
) -> None:
    for table, expected in EXPECTED_COUNTS.items():
        db_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        source_count = (
            len(source_by_table[table].rows)
            if table in source_by_table
            else "derived"
        )
        if db_count != expected:
            report.fail(f"{table}: DB count {db_count}, expected {expected}, source {source_count}")
        else:
            report.ok(f"{table}: DB count {db_count}, expected {expected}, source {source_count}")


def _check_primary_keys(report: MergeReport, conn: sqlite3.Connection) -> None:
    primary_keys = {
        "researchers": "researcher_id",
        "publications": "publication_id",
        "labs": "lab_id",
        "projects": "project_id",
        "patents": "patent_id",
        "collaborations": "collaboration_id",
        "funding_records": "funding_id",
        "research_documents": "document_id",
        "institutions": "institution_id",
    }
    for table, key in primary_keys.items():
        nulls = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {key} IS NULL OR TRIM({key}) = ''"
        ).fetchone()[0]
        duplicates = conn.execute(
            f"SELECT COUNT(*) FROM (SELECT {key} FROM {table} GROUP BY {key} HAVING COUNT(*) > 1)"
        ).fetchone()[0]
        if nulls or duplicates:
            report.fail(f"{table}.{key}: {nulls} null/blank keys, {duplicates} duplicate keys")
        else:
            report.ok(f"{table}.{key}: no null or duplicate primary keys")


def _values_from_query(conn: sqlite3.Connection, query: str) -> list[str]:
    return [str(row[0]) for row in conn.execute(query).fetchall() if _empty_to_none(row[0]) is not None]


def _explode_values(
    conn: sqlite3.Connection,
    query: str,
    splitter: Callable[[Any], tuple[str, ...]] = _split_multi,
) -> list[str]:
    values: list[str] = []
    for row in conn.execute(query).fetchall():
        values.extend(splitter(row[0]))
    return values


def _check_references(report: MergeReport, conn: sqlite3.Connection) -> None:
    researchers = set(_values_from_query(conn, "SELECT researcher_id FROM researchers"))
    projects = set(_values_from_query(conn, "SELECT project_id FROM projects"))
    institutions = set(_values_from_query(conn, "SELECT institution_id FROM institutions"))

    critical_checks = {
        "projects.principal_investigator_id": (
            _values_from_query(conn, "SELECT principal_investigator_id FROM projects"),
            researchers,
        ),
        "projects.co_pis": (
            _explode_values(conn, "SELECT co_pis FROM projects", _split_ids),
            researchers,
        ),
        "funding_records.project_id": (
            _values_from_query(conn, "SELECT project_id FROM funding_records"),
            projects,
        ),
        "publications.researcher_ids": (
            _explode_values(conn, "SELECT researcher_ids FROM publications", _split_ids),
            researchers,
        ),
        "patents.inventor_ids": (
            _explode_values(conn, "SELECT inventor_ids FROM patents", _split_ids),
            researchers,
        ),
        "collaborations.researcher_ids": (
            _explode_values(conn, "SELECT researcher_ids FROM collaborations", _split_ids),
            researchers,
        ),
        "research_documents.researcher_ids": (
            _explode_values(conn, "SELECT researcher_ids FROM research_documents", _split_ids),
            researchers,
        ),
        "researchers.institution_id": (
            _values_from_query(conn, "SELECT institution_id FROM researchers"),
            institutions,
        ),
    }
    warning_checks = {
        "labs.director_researcher_id": (
            _values_from_query(conn, "SELECT director_researcher_id FROM labs"),
            researchers,
        ),
        "labs.institution_id": (
            _values_from_query(conn, "SELECT institution_id FROM labs"),
            institutions,
        ),
    }

    for name, (values, target) in critical_checks.items():
        missing = sorted({value for value in values if value not in target})
        if missing:
            report.fail(f"{name}: {len(missing)} orphan references: {missing[:10]}")
        else:
            report.ok(f"{name}: no orphan references across {len(values)} references")

    for name, (values, target) in warning_checks.items():
        missing = sorted({value for value in values if value not in target})
        if missing:
            report.warn(
                f"{name}: {len(missing)} source-inherited orphan references: {missing[:10]}"
            )
        else:
            report.ok(f"{name}: no orphan references across {len(values)} references")


def _check_namespaces(report: MergeReport, conn: sqlite3.Connection) -> None:
    ids = [row[0] for row in conn.execute("SELECT researcher_id FROM researchers").fetchall()]
    checks = {
        "Gemini RES_1001": lambda value: bool(re.fullmatch(r"RES_\d+", value)),
        "Glm RES-00001": lambda value: bool(re.fullmatch(r"RES-\d{5}", value)),
        "Minimax RES-000000": lambda value: bool(re.fullmatch(r"RES-\d{6}", value)),
    }
    for label, predicate in checks.items():
        count = sum(1 for value in ids if predicate(str(value)))
        if count:
            report.ok(f"researcher namespace {label}: {count} IDs present")
        else:
            report.fail(f"researcher namespace {label}: missing")


def _document_metadata_from_txt(path: Path) -> dict[str, Any]:
    from scripts.ingest_qdrant import access_tier_to_int, parse_document_txt

    doc = parse_document_txt(path)
    if doc is None:
        raise ValueError(f"Could not parse {path}")
    return {
        "document_id": doc.document_id,
        "title": _empty_to_none(doc.title),
        "researcher_ids": _split_ids(doc.researcher_ids),
        "affiliation": _empty_to_none(doc.affiliation),
        "publication_year": doc.publication_year,
        "keywords": _split_multi(doc.keywords),
        "research_area_tags": _split_multi(doc.research_area_tags),
        "access_tier": access_tier_to_int(doc.access_tier),
        "category": _empty_to_none(doc.category),
    }


def _check_research_documents(report: MergeReport, conn: sqlite3.Connection, source_dir: Path) -> None:
    docs_dir = source_dir / "Research_Documents"
    txt_paths = sorted(docs_dir.glob("*.txt"))
    txt_ids = {path.stem for path in txt_paths}
    db_rows = {
        row["document_id"]: row
        for row in conn.execute("SELECT * FROM research_documents").fetchall()
    }
    db_ids = set(db_rows)
    if txt_ids != db_ids:
        report.fail(
            "research_documents: txt/DB ID mismatch "
            f"txt-not-db={sorted(txt_ids - db_ids)[:10]} db-not-txt={sorted(db_ids - txt_ids)[:10]}"
        )
        return

    mismatches: list[str] = []
    for path in txt_paths:
        meta = _document_metadata_from_txt(path)
        db_row = db_rows[meta["document_id"]]
        expected = {
            "title": meta["title"],
            "researcher_ids": meta["researcher_ids"],
            "affiliation": meta["affiliation"],
            "publication_year": meta["publication_year"],
            "keywords": meta["keywords"],
            "research_area_tags": meta["research_area_tags"],
            "access_tier": meta["access_tier"],
            "category": meta["category"],
        }
        actual = {
            "title": _empty_to_none(db_row["title"]),
            "researcher_ids": _split_ids(db_row["researcher_ids"]),
            "affiliation": _empty_to_none(db_row["affiliation"]),
            "publication_year": db_row["publication_year"],
            "keywords": _split_multi(db_row["keywords"]),
            "research_area_tags": _split_multi(db_row["research_area_tags"]),
            "access_tier": db_row["access_tier"],
            "category": _empty_to_none(db_row["category"]),
        }
        if expected != actual:
            mismatches.append(meta["document_id"])

    if mismatches:
        report.fail(f"research_documents: {len(mismatches)} metadata mismatches: {mismatches[:10]}")
    else:
        report.ok(f"research_documents: {len(txt_ids)} txt files map 1:1 to DB metadata")


def _json_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected list JSON in {path}")
    return [item for item in data if isinstance(item, dict)]


def _json_document_id(record: dict[str, Any]) -> str:
    meta = record.get("metadata") if isinstance(record.get("metadata"), dict) else record
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    return str(meta.get("document_id") or payload.get("document_id") or record.get("id") or "")


def _check_json_subsets(
    report: MergeReport,
    source_dir: Path,
    source_by_table: dict[str, SourceRows],
    conn: sqlite3.Connection,
) -> None:
    json_dir = source_dir / "JSON_Data"
    checks = [
        ("researchers.json", "researcher_id", {r["researcher_id"] for r in source_by_table["researchers"].rows}),
        ("projects.json", "project_id", {r["project_id"] for r in source_by_table["projects"].rows}),
        ("labs_institutions.json", "lab_id", {r["lab_id"] for r in source_by_table["labs"].rows}),
        (
            "funding_transactions.json",
            "transaction_id",
            {r["transaction_id"] for r in source_by_table["funding_records"].rows},
        ),
    ]
    for filename, key, source_ids in checks:
        path = json_dir / filename
        records = _json_records(path)
        ids = {str(record.get(key) or "") for record in records}
        missing = sorted(ids - source_ids)
        if missing:
            report.fail(f"JSON_Data/{filename}: {len(missing)} IDs not in logical CSV: {missing[:10]}")
        else:
            report.ok(f"JSON_Data/{filename}: {len(ids)} IDs are a subset of logical CSV source")

    db_doc_ids = {row[0] for row in conn.execute("SELECT document_id FROM research_documents")}
    document_jsons = [
        "research_documents.json",
        "research_documents_batch3.json",
        "qdrant_ready_payload.json",
        "qdrant_ready_payload_batch3.json",
    ]
    for filename in document_jsons:
        path = json_dir / filename
        records = _json_records(path)
        ids = {_json_document_id(record) for record in records}
        missing = sorted(ids - db_doc_ids)
        if missing:
            report.fail(f"JSON_Data/{filename}: {len(missing)} IDs not in research_documents DB: {missing[:10]}")
        else:
            report.ok(f"JSON_Data/{filename}: {len(ids)} IDs are a subset of research_documents")


def _check_researcher_spot_check(
    report: MergeReport,
    source_rows: list[dict[str, Any]],
    db_rows: dict[str, sqlite3.Row],
) -> None:
    sample = random.Random(20260422).sample(source_rows, 10)
    spec = next(item for item in COMPARE_SPECS if item.table == "researchers")
    failures: list[str] = []
    passed: list[str] = []
    for source in sample:
        row_id = str(source["researcher_id"])
        db_row = db_rows.get(row_id)
        if db_row is None:
            failures.append(f"{row_id}:missing")
            continue
        for source_field, (db_field, normalizer) in spec.mapping.items():
            if normalizer(source.get(source_field)) != normalizer(db_row[db_field]):
                failures.append(f"{row_id}:{source_field}->{db_field}")
                break
        else:
            passed.append(row_id)
    if failures:
        report.fail(f"researcher spot-check: failures {failures}")
    else:
        report.ok(f"researcher spot-check: 10/10 full records matched ({', '.join(passed)})")


def _expected_qdrant_points(source_dir: Path) -> tuple[set[str], int]:
    from scripts.ingest_qdrant import (
        _text_for_document,
        chunk_text,
        discover_txt_files,
        parse_document_txt,
    )

    doc_ids: set[str] = set()
    points = 0
    for path in discover_txt_files(source_dir / "Research_Documents"):
        doc = parse_document_txt(path)
        if doc is None:
            continue
        doc_ids.add(doc.document_id)
        points += len(chunk_text(_text_for_document(doc)))
    return doc_ids, points


def _check_qdrant(
    report: MergeReport,
    source_dir: Path,
    collection: str,
    host: str,
    port: int,
    timeout: float,
) -> None:
    try:
        from qdrant_client import QdrantClient
    except Exception as exc:
        report.fail(f"qdrant: qdrant-client unavailable: {exc}")
        return

    expected_doc_ids, expected_points = _expected_qdrant_points(source_dir)
    try:
        client = QdrantClient(host=host, port=port, timeout=timeout)
        info = client.get_collection(collection)
        offset = None
        doc_counts: Counter[str] = Counter()
        missing_text = 0
        wrong_type = 0
        while True:
            points, offset = client.scroll(
                collection_name=collection,
                limit=512,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in points:
                payload = point.payload or {}
                doc_id = str(payload.get("document_id") or payload.get("source_id") or "")
                if doc_id:
                    doc_counts[doc_id] += 1
                if not (payload.get("text") or payload.get("content")):
                    missing_text += 1
                if payload.get("source_type") != "research_document":
                    wrong_type += 1
            if offset is None:
                break
    except Exception as exc:
        report.fail(f"qdrant: collection check failed: {exc}")
        return

    actual_points = int(info.points_count or sum(doc_counts.values()))
    actual_doc_ids = set(doc_counts)
    problems = []
    if actual_points != expected_points:
        problems.append(f"points {actual_points} != expected {expected_points}")
    if actual_doc_ids != expected_doc_ids:
        problems.append(
            "document IDs mismatch "
            f"missing={sorted(expected_doc_ids - actual_doc_ids)[:10]} "
            f"extra={sorted(actual_doc_ids - expected_doc_ids)[:10]}"
        )
    if missing_text:
        problems.append(f"{missing_text} payloads without text/content")
    if wrong_type:
        problems.append(f"{wrong_type} payloads without research_document source_type")

    if problems:
        report.fail(f"qdrant: {'; '.join(problems)}")
    else:
        distribution = dict(sorted(Counter(doc_counts.values()).items()))
        report.ok(
            "qdrant: "
            f"{actual_points} payloads cover {len(actual_doc_ids)} documents; "
            f"chunk distribution {distribution}"
        )


def verify_merge(
    source_dir: Path,
    db_path: Path,
    skip_qdrant: bool = False,
    qdrant_collection: str = DEFAULT_QDRANT_COLLECTION,
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
    qdrant_timeout: float = 10.0,
) -> MergeReport:
    report = MergeReport()
    if not source_dir.exists():
        report.fail(f"source directory does not exist: {source_dir}")
        return report
    if not db_path.exists():
        report.fail(f"database does not exist: {db_path}")
        return report

    source_by_table = {
        table: read_logical_csv_rows(source_dir, table)
        for table in CSV_FILES
    }
    for source in source_by_table.values():
        for repair in source.repairs:
            report.warn(repair)
        for malformed in source.malformed:
            report.fail(malformed)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        _check_counts(report, conn, source_by_table)
        _check_primary_keys(report, conn)
        for spec in COMPARE_SPECS:
            db_rows = _fetch_db_map(conn, spec)
            _compare_rows(report, spec, source_by_table[spec.source_table].rows, db_rows)
            if spec.table == "researchers":
                _check_researcher_spot_check(
                    report,
                    source_by_table["researchers"].rows,
                    db_rows,
                )
        _check_research_documents(report, conn, source_dir)
        _check_references(report, conn)
        _check_namespaces(report, conn)
        _check_json_subsets(report, source_dir, source_by_table, conn)
    finally:
        conn.close()

    if skip_qdrant:
        report.warn("qdrant: skipped by --skip-qdrant")
    else:
        _check_qdrant(
            report,
            source_dir,
            qdrant_collection,
            qdrant_host,
            qdrant_port,
            qdrant_timeout,
        )
    return report


def _print_report(report: MergeReport, source_dir: Path, db_path: Path) -> None:
    print("NRG DB MERGE VERIFICATION")
    print(f"Source: {source_dir}")
    print(f"DB: {db_path}")
    print("")
    for line in report.lines:
        print(line)
    print("")
    print(f"Warnings: {len(report.warnings)}")
    print(f"Errors: {len(report.errors)}")
    print(f"VERDICT: {'FAIL' if report.errors else 'PASS'}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--skip-qdrant", action="store_true")
    parser.add_argument("--qdrant-collection", default=DEFAULT_QDRANT_COLLECTION)
    parser.add_argument("--qdrant-host", default="localhost")
    parser.add_argument("--qdrant-port", type=int, default=6333)
    parser.add_argument("--qdrant-timeout", type=float, default=10.0)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = verify_merge(
        source_dir=args.source_dir,
        db_path=args.db,
        skip_qdrant=args.skip_qdrant,
        qdrant_collection=args.qdrant_collection,
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        qdrant_timeout=args.qdrant_timeout,
    )
    _print_report(report, args.source_dir, args.db)
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
