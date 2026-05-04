#!/usr/bin/env python3
"""Generate Batch 4 data, SQL, schema, and migration evidence."""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import decimal
import hashlib
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.skills.text_to_sql.schema_sync_check import (  # noqa: E402
    check_schema_sync,
    format_diff_report,
    get_dhairya_required_tables,
    parse_db_struct_sql,
)


TEXT_EXTENSIONS = {".md", ".py", ".sql", ".yaml", ".yml", ".json", ".toml"}
SCAN_DIRS = ("src", "tests", "scripts", "docs")
SKIP_PARTS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "node_modules"}
DHAIRYA_QUERY_TIMEOUT_MS = 5000

CONTACT_CHECKS = {
    "email": r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$",
    "phone": r"^\+?[0-9][0-9 .()\-]{7,19}$",
}

FK_RELATIONSHIPS = (
    ("researchers", "institution_id", "institutions", "institution_id"),
    ("funding_records", "researcher_id", "researchers", "researcher_id"),
    ("funding_records", "institution_id", "institutions", "institution_id"),
    ("funding_records", "project_id", "projects", "project_id"),
    ("projects", "principal_investigator_id", "researchers", "researcher_id"),
    ("researcher_publications", "researcher_id", "researchers", "researcher_id"),
    ("researcher_publications", "publication_id", "publications", "publication_id"),
    ("publication_keywords", "publication_id", "publications", "publication_id"),
    ("labs", "institution_id", "institutions", "institution_id"),
)

HOT_PATH_QUERIES = (
    ("researchers_state", "SELECT COUNT(*) FROM researchers WHERE state = 'GJ'"),
    (
        "researchers_area",
        "SELECT COUNT(*) FROM researchers WHERE LOWER(research_area) LIKE LOWER('%AI%')",
    ),
    ("publications_year", "SELECT COUNT(*) FROM publications WHERE year = 2024"),
    (
        "audit_events_recent",
        "SELECT COUNT(*) FROM audit_events WHERE created_at >= now() - interval '30 days'",
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--output-root", type=Path, default=Path("evidence/2026-05-02"))
    args = parser.parse_args()

    if not args.database_url:
        parser.error("DATABASE_URL is required")

    output_root = (REPO_ROOT / args.output_root).resolve()
    table_profile_dir = output_root / "table_profiles"
    batch_dir = output_root / "batch4_data_sql_schema"
    table_profile_dir.mkdir(parents=True, exist_ok=True)
    batch_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine(args.database_url, pool_pre_ping=True)
    try:
        profiles = write_table_profiles(engine, table_profile_dir)
        schema_sync = write_schema_sync(engine, batch_dir)
        dhairya = write_dhairya_replay(engine, batch_dir)
        contacts = write_contact_constraint_report(engine, batch_dir)
        fks = write_fk_orphan_report(engine, batch_dir)
        partition_indexes = write_partition_and_index_report(engine, batch_dir)
        migrations = write_migration_audit(batch_dir)
        summary = {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "database": redact_database_url(args.database_url),
            "table_profiles": profiles["summary"],
            "schema_sync": schema_sync["summary"],
            "dhairya_replay": dhairya["summary"],
            "contact_constraints": contacts["summary"],
            "foreign_keys": fks["summary"],
            "partition_and_indexes": partition_indexes["summary"],
            "migration_audit": migrations["summary"],
        }
        write_json(batch_dir / "batch4_summary.json", summary)
        write_text(batch_dir / "batch4_summary.md", render_summary(summary))
    finally:
        engine.dispose()

    print(json.dumps({"ok": True, "evidence": str(batch_dir)}, indent=2))
    return 0


def write_table_profiles(engine: Engine, output_dir: Path) -> dict[str, Any]:
    authoritative = parse_db_struct_sql()
    official_tables = set(authoritative)
    inspector = inspect(engine)
    live_tables = sorted(inspector.get_table_names(schema="public"))
    frequency = table_reference_frequency(set(live_tables) | official_tables)

    rows = []
    with engine.connect() as conn:
        for table_name in live_tables:
            count = safe_count(conn, table_name)
            rows.append(
                {
                    "table": table_name,
                    "rows": count,
                    "in_db_struct": table_name in official_tables,
                    "reference_frequency": frequency.get(table_name, 0),
                }
            )

    zero_rows = [row for row in rows if row["rows"] == 0]
    nonzero_rows = [row for row in rows if isinstance(row["rows"], int) and row["rows"] > 0]
    priority = sorted(rows, key=lambda row: (-row["reference_frequency"], row["table"]))

    payload = {
        "live_table_count": len(live_tables),
        "db_struct_table_count": len(official_tables),
        "zero_row_table_count": len(zero_rows),
        "nonzero_table_count": len(nonzero_rows),
        "tables": rows,
        "zero_row_tables": zero_rows,
        "priority_by_reference_frequency": priority,
    }
    write_json(output_dir / "table_counts.json", payload)
    write_text(output_dir / "table_profiles.md", render_table_profiles(payload))
    write_text(output_dir / "zero_row_tables.md", render_zero_rows(payload))
    return {"summary": {key: payload[key] for key in payload if key.endswith("_count")}}


def write_schema_sync(engine: Engine, output_dir: Path) -> dict[str, Any]:
    authoritative = parse_db_struct_sql()
    diff = check_schema_sync(engine, authoritative)
    payload = {
        "missing_tables": sorted(diff.missing_tables),
        "extra_tables": sorted(diff.extra_tables),
        "missing_columns": {key: sorted(value) for key, value in diff.missing_columns.items()},
        "extra_columns": {key: sorted(value) for key, value in diff.extra_columns.items()},
        "type_mismatches": {
            key: {"expected": value[0], "actual": value[1]}
            for key, value in diff.type_mismatches.items()
        },
        "nullable_mismatches": diff.nullable_mismatches,
        "dhairya_required_tables": sorted(get_dhairya_required_tables()),
    }
    has_drift = any(
        payload[key]
        for key in (
            "missing_tables",
            "missing_columns",
            "extra_columns",
            "type_mismatches",
        )
    )
    payload["has_drift"] = has_drift
    write_json(output_dir / "D4-02_schema_sync.json", payload)
    write_text(output_dir / "D4-02_schema_sync.md", format_diff_report(diff))
    return {
        "summary": {
            "has_drift": has_drift,
            "missing_tables": len(payload["missing_tables"]),
            "extra_tables": len(payload["extra_tables"]),
            "missing_column_tables": len(payload["missing_columns"]),
            "type_mismatches": len(payload["type_mismatches"]),
        }
    }


def write_dhairya_replay(engine: Engine, output_dir: Path) -> dict[str, Any]:
    queries = extract_dhairya_expected_queries()
    results = []

    for query in queries:
        sql = executable_sql(query["sql"])
        result: dict[str, Any] = {"id": query["id"], "question": query["question"], "sql": sql}
        started = time.perf_counter()
        with engine.connect() as conn:
            try:
                conn.execute(text(f"SET statement_timeout TO {DHAIRYA_QUERY_TIMEOUT_MS}"))
                sample_rows = conn.execute(text(f"SELECT * FROM ({sql}) AS batch4_q LIMIT 20")).mappings().all()
                elapsed_ms = (time.perf_counter() - started) * 1000
                safe_rows = [json_safe(dict(row)) for row in sample_rows]
                result.update(
                    {
                        "status": "PASS",
                        "sample_rows": safe_rows,
                        "result_hash": sha256_json({"sample": safe_rows}),
                        "elapsed_ms": round(elapsed_ms, 3),
                        "query_timeout_ms": DHAIRYA_QUERY_TIMEOUT_MS,
                    }
                )
            except SQLAlchemyError as exc:
                conn.rollback()
                result.update({"status": "FAIL", "error": str(exc)})
                results.append(result)
                continue

        with engine.connect() as conn:
            try:
                conn.execute(text(f"SET statement_timeout TO {DHAIRYA_QUERY_TIMEOUT_MS}"))
                count = conn.execute(text(f"SELECT COUNT(*) FROM ({sql}) AS batch4_q")).scalar()
                result["row_count"] = int(count or 0)
                result["result_hash"] = sha256_json(
                    {"row_count": result["row_count"], "sample": result["sample_rows"]}
                )
            except SQLAlchemyError as exc:
                conn.rollback()
                result["row_count"] = None
                result["row_count_error"] = str(exc)
        results.append(result)

    passed = sum(1 for result in results if result["status"] == "PASS")
    payload = {"total": len(results), "passed": passed, "failed": len(results) - passed, "results": results}
    write_json(output_dir / "D4-03_dhairya_replay.json", payload)
    write_text(output_dir / "D4-03_dhairya_replay.md", render_dhairya_replay(payload))
    return {"summary": {"total": payload["total"], "passed": passed, "failed": payload["failed"]}}


def write_contact_constraint_report(engine: Engine, output_dir: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {"existing_invalid_rows": {}, "write_tests": {}}
    with engine.connect() as conn:
        for column_name, pattern in CONTACT_CHECKS.items():
            invalid_count = conn.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM researchers
                    WHERE "{column_name}" IS NOT NULL
                      AND "{column_name}" !~* :pattern
                    """
                ),
                {"pattern": pattern},
            ).scalar()
            payload["existing_invalid_rows"][column_name] = int(invalid_count or 0)

    payload["write_tests"]["invalid_email_rejected"] = invalid_contact_insert_rejected(
        engine, email="not-an-email", phone="+919876543210"
    )
    payload["write_tests"]["invalid_phone_rejected"] = invalid_contact_insert_rejected(
        engine, email=f"valid-{uuid.uuid4().hex}@example.com", phone="bad-phone"
    )
    payload["write_tests"]["valid_contact_accepted_then_rolled_back"] = valid_contact_insert_accepted(engine)
    payload["summary"] = {
        "invalid_email_rejected": payload["write_tests"]["invalid_email_rejected"],
        "invalid_phone_rejected": payload["write_tests"]["invalid_phone_rejected"],
        "valid_contact_accepted_then_rolled_back": payload["write_tests"][
            "valid_contact_accepted_then_rolled_back"
        ],
        "existing_invalid_email_rows": payload["existing_invalid_rows"]["email"],
        "existing_invalid_phone_rows": payload["existing_invalid_rows"]["phone"],
    }
    write_json(output_dir / "D4-04_contact_constraints.json", payload)
    write_text(output_dir / "D4-04_contact_constraints.md", render_contact_constraints(payload))
    return {"summary": payload["summary"]}


def write_fk_orphan_report(engine: Engine, output_dir: Path) -> dict[str, Any]:
    inspector = inspect(engine)
    table_columns = {
        table_name: {column["name"] for column in inspector.get_columns(table_name, schema="public")}
        for table_name in inspector.get_table_names(schema="public")
    }
    fk_constraints = {
        table_name: inspector.get_foreign_keys(table_name, schema="public")
        for table_name in table_columns
    }

    relationships = []
    with engine.connect() as conn:
        for child_table, child_col, parent_table, parent_col in FK_RELATIONSHIPS:
            row: dict[str, Any] = {
                "child_table": child_table,
                "child_column": child_col,
                "parent_table": parent_table,
                "parent_column": parent_col,
            }
            if child_col not in table_columns.get(child_table, set()) or parent_col not in table_columns.get(
                parent_table, set()
            ):
                row.update({"status": "SKIPPED", "reason": "missing table or column"})
            else:
                row["constraint_present"] = has_fk_constraint(
                    fk_constraints.get(child_table, []), child_col, parent_table, parent_col
                )
                try:
                    row["orphan_count"] = orphan_count(conn, child_table, child_col, parent_table, parent_col)
                    row["status"] = "PASS" if row["orphan_count"] == 0 else "FAIL"
                except SQLAlchemyError as exc:
                    conn.rollback()
                    row.update({"status": "FAIL", "error": str(exc)})
            relationships.append(row)

    failing = [row for row in relationships if row["status"] == "FAIL"]
    missing_constraints = [
        row for row in relationships if row.get("status") == "PASS" and not row.get("constraint_present")
    ]
    payload = {
        "relationships": relationships,
        "summary": {
            "relationships_checked": len(relationships),
            "failing_relationships": len(failing),
            "missing_constraints_on_clean_relationships": len(missing_constraints),
        },
    }
    write_json(output_dir / "D4-05_fk_orphans.json", payload)
    write_text(output_dir / "D4-05_fk_orphans.md", render_fk_orphans(payload))
    return {"summary": payload["summary"]}


def write_partition_and_index_report(engine: Engine, output_dir: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "time_series": {},
        "indexes": {},
        "hot_path_query_timings": {},
    }
    with engine.connect() as conn:
        for table_name in ("audit_events", "query_logs"):
            payload["time_series"][table_name] = time_series_table_state(conn, table_name)
        for table_name in (
            "researchers",
            "publications",
            "funding_records",
            "labs",
            "projects",
            "patents",
            "collaborations",
            "research_documents",
            "audit_events",
        ):
            payload["indexes"][table_name] = list_indexes(conn, table_name)
        for query_name, sql in HOT_PATH_QUERIES:
            payload["hot_path_query_timings"][query_name] = timed_query(conn, sql)
        payload["partition_pruning_explain"] = audit_events_partition_pruning(conn)

    timings = [
        item["elapsed_ms"]
        for item in payload["hot_path_query_timings"].values()
        if item.get("status") == "PASS" and item.get("elapsed_ms") is not None
    ]
    payload["summary"] = {
        "audit_events_partitioned": payload["time_series"]["audit_events"].get("partitioned"),
        "query_logs_exists": payload["time_series"]["query_logs"].get("exists"),
        "partition_pruning_relations": payload["partition_pruning_explain"].get("relation_names", []),
        "hot_path_timing_max_ms": max(timings) if timings else None,
        "hot_path_timing_under_200ms": bool(timings) and max(timings) < 200,
    }
    write_json(output_dir / "D4-06_D4-08_partition_indexes.json", payload)
    write_text(output_dir / "D4-06_D4-08_partition_indexes.md", render_partition_indexes(payload))
    return {"summary": payload["summary"]}


def write_migration_audit(output_dir: Path) -> dict[str, Any]:
    migration_dir = REPO_ROOT / "src" / "migrations" / "versions"
    migrations = []
    revisions: dict[str, str | list[str] | None] = {}
    referenced: set[str] = set()

    for path in sorted(migration_dir.glob("*.py")):
        source = path.read_text()
        revision = read_module_constant(source, "revision")
        down_revision = read_module_constant(source, "down_revision")
        if revision:
            revisions[str(revision)] = down_revision
        referenced.update(iter_down_revisions(down_revision))
        migrations.append(
            {
                "file": str(path.relative_to(REPO_ROOT)),
                "revision": revision,
                "down_revision": down_revision,
                "upgrade_risk_markers": upgrade_risk_markers(source),
            }
        )

    heads = sorted(str(revision) for revision in revisions if revision not in referenced)
    risky = [item for item in migrations if item["upgrade_risk_markers"]]
    payload = {
        "migration_count": len(migrations),
        "heads": heads,
        "risky_upgrade_count": len(risky),
        "migrations": migrations,
        "summary": {
            "migration_count": len(migrations),
            "heads": heads,
            "single_head": len(heads) == 1,
            "risky_upgrade_count": len(risky),
        },
    }
    write_json(output_dir / "D4-11_migration_audit.json", payload)
    write_text(output_dir / "D4-11_migration_audit.md", render_migration_audit(payload))
    return {"summary": payload["summary"]}


def safe_count(conn: Connection, table_name: str) -> int | str:
    try:
        return int(conn.execute(text(f'SELECT COUNT(*) FROM public."{table_name}"')).scalar() or 0)
    except SQLAlchemyError as exc:
        conn.rollback()
        return f"ERROR: {exc}"


def table_reference_frequency(table_names: set[str]) -> dict[str, int]:
    frequency = {table_name: 0 for table_name in table_names}
    for root_name in SCAN_DIRS:
        root = REPO_ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in TEXT_EXTENSIONS:
                continue
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            try:
                content = path.read_text(errors="ignore").lower()
            except OSError:
                continue
            for table_name in table_names:
                frequency[table_name] += len(re.findall(rf"\b{re.escape(table_name.lower())}\b", content))
    return frequency


def extract_dhairya_expected_queries() -> list[dict[str, str]]:
    report = (REPO_ROOT / "docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md").read_text()
    pattern = re.compile(
        r"### Q(?P<id>\d+).*?\*\*Question:\*\*\s*(?P<question>.*?)\n\n"
        r".*?\*\*Actual Query \(Expected\):\*\*\s*```sql\s*(?P<sql>.*?)```",
        re.DOTALL,
    )
    return [
        {
            "id": match.group("id"),
            "question": re.sub(r"\s+", " ", match.group("question")).strip(),
            "sql": match.group("sql").strip(),
        }
        for match in pattern.finditer(report)
    ]


def executable_sql(sql: str) -> str:
    stripped_lines = []
    for line in sql.splitlines():
        stripped_lines.append(line.split("--", 1)[0])
    return "\n".join(stripped_lines).strip().rstrip(";")


def invalid_contact_insert_rejected(engine: Engine, *, email: str, phone: str) -> bool:
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                insert_researcher(conn, email=email, phone=phone)
                trans.rollback()
                return False
            except SQLAlchemyError:
                trans.rollback()
                return True
    except SQLAlchemyError:
        return False


def valid_contact_insert_accepted(engine: Engine) -> bool:
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            insert_researcher(
                conn,
                email=f"valid-{uuid.uuid4().hex}@example.com",
                phone="+919876543210",
            )
            trans.rollback()
            return True
        except SQLAlchemyError:
            trans.rollback()
            return False


def insert_researcher(conn: Connection, *, email: str, phone: str) -> None:
    conn.execute(
        text(
            """
            INSERT INTO researchers (
                researcher_id,
                name,
                email,
                phone,
                state,
                research_area,
                year_joined,
                access_tier
            )
            VALUES (
                :researcher_id,
                :name,
                :email,
                :phone,
                :state,
                :research_area,
                :year_joined,
                :access_tier
            )
            """
        ),
        {
            "researcher_id": str(uuid.uuid4()),
            "name": "Batch 4 Constraint Probe",
            "email": email,
            "phone": phone,
            "state": "GJ",
            "research_area": "Schema Audit",
            "year_joined": 2026,
            "access_tier": 1,
        },
    )


def has_fk_constraint(
    foreign_keys: list[dict[str, Any]], child_col: str, parent_table: str, parent_col: str
) -> bool:
    return any(
        fk.get("referred_table") == parent_table
        and fk.get("constrained_columns") == [child_col]
        and fk.get("referred_columns") == [parent_col]
        for fk in foreign_keys
    )


def orphan_count(
    conn: Connection, child_table: str, child_col: str, parent_table: str, parent_col: str
) -> int:
    return int(
        conn.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM "{child_table}" child_rows
                LEFT JOIN "{parent_table}" parent_rows
                  ON child_rows."{child_col}" = parent_rows."{parent_col}"
                WHERE child_rows."{child_col}" IS NOT NULL
                  AND parent_rows."{parent_col}" IS NULL
                """
            )
        ).scalar()
        or 0
    )


def time_series_table_state(conn: Connection, table_name: str) -> dict[str, Any]:
    exists = bool(conn.execute(text("SELECT to_regclass(:name)"), {"name": f"public.{table_name}"}).scalar())
    if not exists:
        return {"exists": False, "partitioned": False}
    relkind = conn.execute(
        text(
            """
            SELECT cls.relkind
            FROM pg_class cls
            JOIN pg_namespace nsp ON nsp.oid = cls.relnamespace
            WHERE nsp.nspname = 'public'
              AND cls.relname = :table_name
            """
        ),
        {"table_name": table_name},
    ).scalar()
    partitions = conn.execute(
        text(
            """
            SELECT COUNT(*)
            FROM pg_inherits inh
            JOIN pg_class parent ON parent.oid = inh.inhparent
            JOIN pg_namespace nsp ON nsp.oid = parent.relnamespace
            WHERE nsp.nspname = 'public'
              AND parent.relname = :table_name
            """
        ),
        {"table_name": table_name},
    ).scalar()
    return {"exists": True, "partitioned": relkind == "p", "child_partition_count": int(partitions or 0)}


def list_indexes(conn: Connection, table_name: str) -> list[dict[str, str]]:
    rows = conn.execute(
        text(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = :table_name
            ORDER BY indexname
            """
        ),
        {"table_name": table_name},
    ).mappings()
    return [{"name": row["indexname"], "definition": row["indexdef"]} for row in rows]


def timed_query(conn: Connection, sql: str) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = conn.execute(text(sql)).scalar()
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        return {"status": "PASS", "elapsed_ms": elapsed_ms, "result": json_safe(result)}
    except SQLAlchemyError as exc:
        conn.rollback()
        return {"status": "FAIL", "error": str(exc)}


def audit_events_partition_pruning(conn: Connection) -> dict[str, Any]:
    state = time_series_table_state(conn, "audit_events")
    if not state.get("partitioned"):
        return {"status": "SKIPPED", "reason": "audit_events is not partitioned"}
    sql = """
        EXPLAIN (ANALYZE, VERBOSE, FORMAT JSON)
        SELECT COUNT(*)
        FROM audit_events
        WHERE created_at >= TIMESTAMP '2026-01-01'
          AND created_at < TIMESTAMP '2027-01-01'
    """
    try:
        plan_value = conn.execute(text(sql)).scalar()
        plan = plan_value if isinstance(plan_value, list) else json.loads(plan_value)
        relation_names = sorted(set(collect_plan_relations(plan[0]["Plan"])))
        return {
            "status": "PASS",
            "query": "created_at >= 2026-01-01 AND created_at < 2027-01-01",
            "relation_names": relation_names,
            "plan": json_safe(plan),
        }
    except (SQLAlchemyError, json.JSONDecodeError, KeyError, TypeError) as exc:
        conn.rollback()
        return {"status": "FAIL", "error": str(exc)}


def collect_plan_relations(node: dict[str, Any]) -> list[str]:
    relation_names = []
    relation_name = node.get("Relation Name")
    if relation_name:
        relation_names.append(str(relation_name))
    for child in node.get("Plans", []):
        relation_names.extend(collect_plan_relations(child))
    return relation_names


def read_module_constant(source: str, name: str) -> str | list[str] | None:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                continue
            return ast.literal_eval(node.value)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            return ast.literal_eval(node.value)
    return None


def iter_down_revisions(value: str | list[str] | tuple[str, ...] | None) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value}
    return {str(item) for item in value if item}


def upgrade_risk_markers(source: str) -> list[str]:
    upgrade_match = re.search(
        r"def\s+upgrade\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:(.*?)(?:\ndef\s+downgrade|\Z)",
        source,
        re.DOTALL,
    )
    if not upgrade_match:
        return ["missing_upgrade_function"]
    upgrade_body = upgrade_match.group(1).lower()
    markers = []
    for marker in ("drop_table", "drop_column", "truncate", "delete from", "drop constraint"):
        if marker in upgrade_body:
            markers.append(marker)
    if re.search(r"alter\s+table.*\s+drop\s+", upgrade_body):
        markers.append("alter_table_drop")
    return sorted(set(markers))


def json_safe(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(json.dumps(json_safe(payload), sort_keys=True).encode()).hexdigest()


def redact_database_url(database_url: str) -> str:
    return re.sub(r"://([^:/@]+):([^@]+)@", r"://\1:***@", database_url)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(json_safe(payload), indent=2, sort_keys=True) + "\n")


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n")


def render_table_profiles(payload: dict[str, Any]) -> str:
    lines = [
        "# D4-01 Table Profiles",
        "",
        f"- Live tables: {payload['live_table_count']}",
        f"- db_struct.sql tables: {payload['db_struct_table_count']}",
        f"- Zero-row live tables: {payload['zero_row_table_count']}",
        f"- Non-zero live tables: {payload['nonzero_table_count']}",
        "",
        "| Priority | Table | Rows | In db_struct.sql | Reference frequency |",
        "|---:|---|---:|---|---:|",
    ]
    for index, row in enumerate(payload["priority_by_reference_frequency"], start=1):
        lines.append(
            f"| {index} | `{row['table']}` | {row['rows']} | "
            f"{row['in_db_struct']} | {row['reference_frequency']} |"
        )
    return "\n".join(lines)


def render_zero_rows(payload: dict[str, Any]) -> str:
    lines = ["# D4-01 Zero-Row Tables", "", "| Table | In db_struct.sql | Reference frequency |", "|---|---|---:|"]
    for row in payload["zero_row_tables"]:
        lines.append(f"| `{row['table']}` | {row['in_db_struct']} | {row['reference_frequency']} |")
    return "\n".join(lines)


def render_dhairya_replay(payload: dict[str, Any]) -> str:
    lines = [
        "# D4-03 Dhairya Query Replay",
        "",
        f"- Passed: {payload['passed']}/{payload['total']}",
        f"- Failed: {payload['failed']}",
        "",
        "| Q | Status | Rows | Elapsed ms | Result hash / Error |",
        "|---:|---|---:|---:|---|",
    ]
    for result in payload["results"]:
        detail = result.get("result_hash") or result.get("error", "")
        lines.append(
            f"| {result['id']} | {result['status']} | {result.get('row_count', '')} | "
            f"{result.get('elapsed_ms', '')} | `{str(detail)[:96]}` |"
        )
    return "\n".join(lines)


def render_contact_constraints(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# D4-04 Researcher Contact Constraints",
            "",
            f"- Invalid email insert rejected: {summary['invalid_email_rejected']}",
            f"- Invalid phone insert rejected: {summary['invalid_phone_rejected']}",
            f"- Valid contact insert accepted then rolled back: {summary['valid_contact_accepted_then_rolled_back']}",
            f"- Existing invalid email rows: {summary['existing_invalid_email_rows']}",
            f"- Existing invalid phone rows: {summary['existing_invalid_phone_rows']}",
        ]
    )


def render_fk_orphans(payload: dict[str, Any]) -> str:
    lines = [
        "# D4-05 Foreign Key Orphan Report",
        "",
        "| Child | Parent | Constraint present | Orphans | Status |",
        "|---|---|---|---:|---|",
    ]
    for row in payload["relationships"]:
        lines.append(
            f"| `{row['child_table']}.{row['child_column']}` | "
            f"`{row['parent_table']}.{row['parent_column']}` | "
            f"{row.get('constraint_present', '')} | {row.get('orphan_count', '')} | {row['status']} |"
        )
    return "\n".join(lines)


def render_partition_indexes(payload: dict[str, Any]) -> str:
    lines = [
        "# D4-06 / D4-08 Partition and Index Report",
        "",
        "## Time-Series Tables",
        "",
        "| Table | Exists | Partitioned | Child partitions |",
        "|---|---|---|---:|",
    ]
    for table_name, state in payload["time_series"].items():
        lines.append(
            f"| `{table_name}` | {state.get('exists')} | {state.get('partitioned')} | "
            f"{state.get('child_partition_count', 0)} |"
        )
    lines.extend(["", "## Hot-Path Timings", "", "| Query | Status | Elapsed ms | Result |", "|---|---|---:|---:|"])
    for query_name, timing in payload["hot_path_query_timings"].items():
        lines.append(
            f"| `{query_name}` | {timing['status']} | {timing.get('elapsed_ms', '')} | "
            f"{timing.get('result', '')} |"
        )
    lines.extend(["", "## Index Counts", "", "| Table | Index count |", "|---|---:|"])
    for table_name, indexes in payload["indexes"].items():
        lines.append(f"| `{table_name}` | {len(indexes)} |")
    explain = payload.get("partition_pruning_explain", {})
    lines.extend(
        [
            "",
            "## Partition Pruning",
            "",
            f"- Status: {explain.get('status')}",
            f"- Relations in plan: {', '.join(explain.get('relation_names', []))}",
        ]
    )
    return "\n".join(lines)


def render_migration_audit(payload: dict[str, Any]) -> str:
    lines = [
        "# D4-11 Migration Audit",
        "",
        f"- Migration files: {payload['migration_count']}",
        f"- Heads: {', '.join(payload['heads'])}",
        f"- Risky upgrade marker count: {payload['risky_upgrade_count']}",
        "",
        "| File | Revision | Down revision | Upgrade risk markers |",
        "|---|---|---|---|",
    ]
    for migration in payload["migrations"]:
        markers = ", ".join(migration["upgrade_risk_markers"])
        lines.append(
            f"| `{migration['file']}` | `{migration['revision']}` | "
            f"`{migration['down_revision']}` | {markers} |"
        )
    return "\n".join(lines)


def render_summary(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Batch 4 Data / SQL / Schema Summary",
            "",
            f"- Generated at: {summary['generated_at']}",
            f"- Database: `{summary['database']}`",
            f"- D4-01 live tables: {summary['table_profiles']['live_table_count']}",
            f"- D4-02 schema drift: {summary['schema_sync']['has_drift']}",
            f"- D4-03 Dhairya replay: {summary['dhairya_replay']['passed']}/"
            f"{summary['dhairya_replay']['total']} passed",
            f"- D4-04 invalid email rejected: {summary['contact_constraints']['invalid_email_rejected']}",
            f"- D4-04 invalid phone rejected: {summary['contact_constraints']['invalid_phone_rejected']}",
            f"- D4-05 FK failing relationships: {summary['foreign_keys']['failing_relationships']}",
            f"- D4-06 audit_events partitioned: {summary['partition_and_indexes']['audit_events_partitioned']}",
            f"- D4-08 hot-path under 200ms: {summary['partition_and_indexes']['hot_path_timing_under_200ms']}",
            f"- D4-11 single migration head: {summary['migration_audit']['single_head']}",
            f"- D4-11 risky upgrade markers: {summary['migration_audit']['risky_upgrade_count']}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
