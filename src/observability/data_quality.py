"""Seven-pillar data quality scorecard for NRG database drift monitoring."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url

PILLAR_NAMES = (
    "schema_coverage",
    "referential_integrity",
    "null_rate",
    "freshness",
    "completeness",
    "consistency",
    "pii_sanitization",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPECTED_TABLE_COUNT = 58
DEFAULT_CORE_TABLES = {
    "academic_courses_details",
    "actual_student_strength",
    "combined_ipo_patent_data",
    "faculty_details",
    "financial_expenses_capital",
    "financial_expenses_operational",
    "innovation_grant_from_govt",
    "innovations_at_various_stages_of_technology_readiness_level",
    "patents_details",
    "phd_students",
    "placements_and_higher_studies",
    "research_consultancy_details_consultancy",
    "research_consultancy_details_sponsered",
    "sanctioned_intake",
    "startup_recognition",
    "tb_institute_mstr",
}
PII_TABLE_HINTS = {
    "user",
    "profile",
    "consent",
    "researcher",
    "faculty",
    "expertise",
    "registration",
}
PII_COLUMN_HINTS = {
    "aadhaar",
    "address",
    "email",
    "mobile",
    "name",
    "orcid",
    "pan",
    "phone",
    "user",
}
FRESHNESS_COLUMN_HINTS = (
    "updated_at",
    "created_at",
    "modified_at",
    "ingested_at",
    "loaded_at",
    "last_updated",
    "timestamp",
    "date",
)
PII_PATTERNS = {
    "aadhaar": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
    "pan": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "phone": re.compile(r"(?:\+91[-\s]?)?\b[6-9]\d{9}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "gstin": re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b"),
}


@dataclass(frozen=True)
class DataQualityThresholds:
    expected_table_count: int = DEFAULT_EXPECTED_TABLE_COUNT
    referential_integrity_min: float = 0.99
    referential_integrity_p0: float = 0.90
    max_null_rate: float = 0.05
    max_freshness_days: int = 7
    min_core_rows: int = 1000
    pii_sample_limit: int = 1000


@dataclass(frozen=True)
class DataQualityAlert:
    severity: str
    pillar: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "pillar": self.pillar, "message": self.message}


@dataclass(frozen=True)
class PillarResult:
    name: str
    status: str
    score: float
    threshold: str
    observed: dict[str, Any]
    severity: str | None = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "score": self.score,
            "threshold": self.threshold,
            "observed": self.observed,
            "severity": self.severity,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class DataQualityScorecard:
    generated_at: str
    database_url: str
    overall_status: str
    overall_score: float
    pillars: list[PillarResult] = field(default_factory=list)
    alerts: list[DataQualityAlert] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.overall_status == "PASS"

    def pillar(self, name: str) -> PillarResult:
        for result in self.pillars:
            if result.name == name:
                return result
        raise KeyError(f"Unknown data quality pillar: {name}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "generated_at": self.generated_at,
            "database_url": self.database_url,
            "overall_status": self.overall_status,
            "overall_score": self.overall_score,
            "pillars": {result.name: result.to_dict() for result in self.pillars},
            "alerts": [alert.to_dict() for alert in self.alerts],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    def to_markdown(self) -> str:
        lines = [
            "# Data Quality Scorecard",
            "",
            f"- Generated: `{self.generated_at}`",
            f"- Database: `{self.database_url}`",
            f"- Overall: `{self.overall_status}` ({self.overall_score:.3f})",
            "",
            "| Pillar | Status | Score | Threshold | Detail |",
            "| --- | --- | ---: | --- | --- |",
        ]
        for result in self.pillars:
            detail = result.detail.replace("|", "\\|")
            lines.append(
                f"| `{result.name}` | {result.status} | {result.score:.3f} | "
                f"{result.threshold} | {detail} |"
            )

        if self.alerts:
            lines.extend(["", "## Alerts", ""])
            for alert in self.alerts:
                lines.append(f"- **{alert.severity}** `{alert.pillar}`: {alert.message}")

        return "\n".join(lines) + "\n"


class DataQualityMonitor:
    """Run data quality checks against a SQLAlchemy-supported database."""

    def __init__(
        self,
        engine_or_url: Engine | str,
        *,
        expected_tables: set[str] | None = None,
        core_tables: set[str] | None = None,
        non_pii_tables: set[str] | None = None,
        thresholds: DataQualityThresholds | None = None,
        consistency_relationships: dict[tuple[str, str], tuple[str, str]] | None = None,
    ) -> None:
        self.engine = create_engine(engine_or_url, pool_pre_ping=True) if isinstance(engine_or_url, str) else engine_or_url
        self.database_url = _redact_database_url(str(engine_or_url.url if isinstance(engine_or_url, Engine) else engine_or_url))
        self.expected_tables = expected_tables if expected_tables is not None else load_expected_tables()
        self.core_tables = core_tables if core_tables is not None else DEFAULT_CORE_TABLES
        self.non_pii_tables = non_pii_tables
        self.thresholds = thresholds or DataQualityThresholds()
        self.consistency_relationships = consistency_relationships or {}

    def run(self, *, publish_metrics: bool = True) -> DataQualityScorecard:
        inspector = inspect(self.engine)
        tables = set(inspector.get_table_names())
        results = [
            self._schema_coverage(tables),
            self._referential_integrity(inspector, tables),
            self._null_rate(inspector, tables),
            self._freshness(inspector, tables),
            self._completeness(tables),
            self._consistency(inspector, tables),
            self._pii_sanitization(inspector, tables),
        ]
        alerts = self._alerts(results)
        overall_status = "FAIL" if any(result.status == "FAIL" for result in results) else "PASS"
        overall_score = _round_score(sum(result.score for result in results) / len(results))
        scorecard = DataQualityScorecard(
            generated_at=datetime.now(UTC).isoformat(),
            database_url=self.database_url,
            overall_status=overall_status,
            overall_score=overall_score,
            pillars=results,
            alerts=alerts,
        )
        if publish_metrics:
            publish_data_quality_metrics(scorecard)
        return scorecard

    def _schema_coverage(self, tables: set[str]) -> PillarResult:
        if self.expected_tables:
            present = sorted(tables & self.expected_tables)
            missing = sorted(self.expected_tables - tables)
            expected_count = len(self.expected_tables)
        else:
            present = sorted(tables)
            missing = []
            expected_count = self.thresholds.expected_table_count

        present_count = len(present)
        score = _round_score(min(1.0, present_count / max(expected_count, 1)))
        status = "PASS" if present_count >= expected_count and not missing else "FAIL"
        return PillarResult(
            name="schema_coverage",
            status=status,
            score=score,
            threshold=f">= {expected_count} expected tables present",
            observed={
                "present_tables": present_count,
                "expected_tables": expected_count,
                "missing_tables": missing[:50],
                "live_tables": len(tables),
            },
            severity=None if status == "PASS" else "P1",
            detail=f"{present_count}/{expected_count} expected tables present",
        )

    def _referential_integrity(self, inspector: Any, tables: set[str]) -> PillarResult:
        relationships = self._foreign_key_relationships(inspector, tables)
        relationships.update(self._configured_relationships(tables))
        total, orphaned, examples = self._count_relationship_orphans(relationships)
        score = 1.0 if total == 0 else _round_score((total - orphaned) / total)
        status = "PASS" if score >= self.thresholds.referential_integrity_min else "FAIL"
        severity = None
        if status == "FAIL":
            severity = "P0" if score < self.thresholds.referential_integrity_p0 else "P1"
        return PillarResult(
            name="referential_integrity",
            status=status,
            score=score,
            threshold=f">= {self.thresholds.referential_integrity_min:.2%} valid references",
            observed={
                "relationships_checked": len(relationships),
                "references_checked": total,
                "orphaned_references": orphaned,
                "examples": examples[:20],
            },
            severity=severity,
            detail=f"{orphaned} orphaned references across {total} checked",
        )

    def _null_rate(self, inspector: Any, tables: set[str]) -> PillarResult:
        worst_rate = 0.0
        checked_columns = 0
        skipped_nullable = 0
        examples: list[dict[str, Any]] = []
        for table in sorted(tables):
            row_count = self._count_rows(table)
            if row_count == 0:
                continue
            for column in inspector.get_columns(table):
                if column.get("nullable") and not column.get("primary_key"):
                    skipped_nullable += 1
                    continue
                column_name = column["name"]
                null_count = self._count_nulls(table, column_name)
                rate = null_count / row_count
                checked_columns += 1
                if rate > worst_rate:
                    worst_rate = rate
                if rate > self.thresholds.max_null_rate:
                    examples.append(
                        {
                            "table": table,
                            "column": column_name,
                            "null_rate": _round_score(rate),
                            "null_count": null_count,
                            "rows": row_count,
                        }
                    )

        score = _round_score(max(0.0, 1.0 - worst_rate))
        status = "PASS" if worst_rate <= self.thresholds.max_null_rate else "FAIL"
        return PillarResult(
            name="null_rate",
            status=status,
            score=score,
            threshold=f"<= {self.thresholds.max_null_rate:.2%} nulls in any measured column",
            observed={
                "columns_checked": checked_columns,
                "columns_skipped_nullable": skipped_nullable,
                "worst_null_rate": _round_score(worst_rate),
                "violations": examples[:20],
            },
            severity=None if status == "PASS" else "P1",
            detail=f"worst column null rate {_round_score(worst_rate):.3f}",
        )

    def _freshness(self, inspector: Any, tables: set[str]) -> PillarResult:
        now = datetime.now(UTC)
        worst_age_days = 0.0
        checked_tables = 0
        stale: list[dict[str, Any]] = []
        invalid: list[dict[str, str]] = []

        for table in sorted(tables):
            column_name = _freshness_column(inspector.get_columns(table))
            if not column_name or self._count_rows(table) == 0:
                continue
            raw_value = self._max_value(table, column_name)
            parsed = _parse_datetime(raw_value)
            if parsed is None:
                invalid.append({"table": table, "column": column_name, "value": str(raw_value)})
                continue

            checked_tables += 1
            age_days = max(0.0, (now - parsed).total_seconds() / 86400)
            worst_age_days = max(worst_age_days, age_days)
            if age_days > self.thresholds.max_freshness_days:
                stale.append(
                    {
                        "table": table,
                        "column": column_name,
                        "age_days": _round_measurement(age_days),
                        "max_value": str(raw_value),
                    }
                )

        if checked_tables == 0:
            return PillarResult(
                name="freshness",
                status="FAIL",
                score=0.0,
                threshold=f"<= {self.thresholds.max_freshness_days} days since latest update",
                observed={"tables_checked": 0, "stale_tables": [], "invalid_values": invalid[:20]},
                severity="P1",
                detail="no freshness columns found",
            )

        score = _round_score(max(0.0, 1.0 - (worst_age_days / max(self.thresholds.max_freshness_days, 1))))
        status = "PASS" if not stale and not invalid else "FAIL"
        return PillarResult(
            name="freshness",
            status=status,
            score=score,
            threshold=f"<= {self.thresholds.max_freshness_days} days since latest update",
            observed={
                "tables_checked": checked_tables,
                "worst_age_days": _round_measurement(worst_age_days),
                "stale_tables": stale[:20],
                "invalid_values": invalid[:20],
            },
            severity=None if status == "PASS" else "P1",
            detail=f"worst table age {_round_measurement(worst_age_days):.3f} days",
        )

    def _completeness(self, tables: set[str]) -> PillarResult:
        core_tables = sorted(self.core_tables)
        counts: dict[str, int] = {}
        low: list[dict[str, Any]] = []
        for table in core_tables:
            row_count = self._count_rows(table) if table in tables else 0
            counts[table] = row_count
            if row_count < self.thresholds.min_core_rows:
                low.append({"table": table, "rows": row_count})

        if not core_tables:
            score = 1.0
        else:
            table_scores = [
                min(1.0, counts[table] / max(self.thresholds.min_core_rows, 1)) for table in core_tables
            ]
            score = _round_score(sum(table_scores) / len(table_scores))

        status = "PASS" if not low else "FAIL"
        return PillarResult(
            name="completeness",
            status=status,
            score=score,
            threshold=f">= {self.thresholds.min_core_rows} rows in every core table",
            observed={"core_tables": len(core_tables), "row_counts": counts, "violations": low[:50]},
            severity=None if status == "PASS" else "P1",
            detail=f"{len(low)} core tables below minimum row count",
        )

    def _consistency(self, inspector: Any, tables: set[str]) -> PillarResult:
        relationships = self._configured_relationships(tables)
        relationships.update(self._inferred_relationships(inspector, tables))
        total, orphaned, examples = self._count_relationship_orphans(relationships)
        score = 1.0 if total == 0 else _round_score((total - orphaned) / total)
        status = "PASS" if orphaned == 0 else "FAIL"
        return PillarResult(
            name="consistency",
            status=status,
            score=score,
            threshold="cross-table validations have zero orphaned references",
            observed={
                "rules_checked": len(relationships),
                "records_checked": total,
                "violations": orphaned,
                "examples": examples[:20],
            },
            severity=None if status == "PASS" else "P1",
            detail=f"{orphaned} cross-table consistency violations",
        )

    def _pii_sanitization(self, inspector: Any, tables: set[str]) -> PillarResult:
        scan_tables = sorted(self.non_pii_tables if self.non_pii_tables is not None else _default_non_pii_tables(tables))
        findings: list[dict[str, Any]] = []
        scanned_columns = 0

        for table in scan_tables:
            if table not in tables:
                continue
            columns = [
                column["name"]
                for column in inspector.get_columns(table)
                if _is_text_column(column) and not _is_pii_column(column["name"])
            ]
            if not columns:
                continue
            scanned_columns += len(columns)
            findings.extend(self._scan_table_for_pii(table, columns))
            if len(findings) >= 20:
                findings = findings[:20]
                break

        status = "PASS" if not findings else "FAIL"
        score = 1.0 if not findings else 0.0
        return PillarResult(
            name="pii_sanitization",
            status=status,
            score=score,
            threshold="0 PII findings in non-PII tables",
            observed={
                "tables_scanned": len(scan_tables),
                "columns_scanned": scanned_columns,
                "findings": findings,
            },
            severity=None if status == "PASS" else "P0",
            detail=f"{len(findings)} PII findings in non-PII tables",
        )

    def _alerts(self, results: list[PillarResult]) -> list[DataQualityAlert]:
        alerts: list[DataQualityAlert] = []
        for result in results:
            if result.status == "PASS":
                continue
            severity = result.severity or "P1"
            alerts.append(
                DataQualityAlert(
                    severity=severity,
                    pillar=result.name,
                    message=f"{result.name} failed: {result.detail}",
                )
            )
        return alerts

    def _foreign_key_relationships(self, inspector: Any, tables: set[str]) -> set[tuple[str, str, str, str]]:
        relationships: set[tuple[str, str, str, str]] = set()
        for table in tables:
            for fk in inspector.get_foreign_keys(table):
                parent_table = fk.get("referred_table")
                child_columns = fk.get("constrained_columns") or []
                parent_columns = fk.get("referred_columns") or []
                if not parent_table or parent_table not in tables:
                    continue
                for child_column, parent_column in zip(child_columns, parent_columns):
                    relationships.add((table, child_column, parent_table, parent_column))
        return relationships

    def _configured_relationships(self, tables: set[str]) -> set[tuple[str, str, str, str]]:
        relationships: set[tuple[str, str, str, str]] = set()
        for (child_table, child_column), (parent_table, parent_column) in self.consistency_relationships.items():
            if child_table in tables and parent_table in tables:
                relationships.add((child_table, child_column, parent_table, parent_column))
        return relationships

    def _inferred_relationships(self, inspector: Any, tables: set[str]) -> set[tuple[str, str, str, str]]:
        relationships: set[tuple[str, str, str, str]] = set()
        columns_by_table = {table: {column["name"] for column in inspector.get_columns(table)} for table in tables}
        for child_table, columns in columns_by_table.items():
            for child_column in columns:
                if child_column == "id" or not child_column.endswith("_id"):
                    continue
                prefix = child_column[: -len("_id")]
                candidates = (prefix, f"{prefix}s", f"{prefix}es")
                for parent_table in candidates:
                    if parent_table in tables and "id" in columns_by_table[parent_table]:
                        relationships.add((child_table, child_column, parent_table, "id"))
                        break
        return relationships

    def _count_relationship_orphans(
        self, relationships: set[tuple[str, str, str, str]]
    ) -> tuple[int, int, list[dict[str, Any]]]:
        total = 0
        orphaned = 0
        examples: list[dict[str, Any]] = []
        for child_table, child_column, parent_table, parent_column in sorted(relationships):
            child = self._quote(child_table)
            parent = self._quote(parent_table)
            child_col = self._quote(child_column)
            parent_col = self._quote(parent_column)
            total_query = text(f"SELECT COUNT(*) FROM {child} WHERE {child_col} IS NOT NULL")
            orphan_query = text(
                f"SELECT COUNT(*) FROM {child} c "
                f"LEFT JOIN {parent} p ON c.{child_col} = p.{parent_col} "
                f"WHERE c.{child_col} IS NOT NULL AND p.{parent_col} IS NULL"
            )
            with self.engine.connect() as conn:
                relationship_total = int(conn.execute(total_query).scalar_one() or 0)
                relationship_orphans = int(conn.execute(orphan_query).scalar_one() or 0)
            total += relationship_total
            orphaned += relationship_orphans
            if relationship_orphans:
                examples.append(
                    {
                        "child_table": child_table,
                        "child_column": child_column,
                        "parent_table": parent_table,
                        "parent_column": parent_column,
                        "orphaned": relationship_orphans,
                    }
                )
        return total, orphaned, examples

    def _scan_table_for_pii(self, table: str, columns: list[str]) -> list[dict[str, Any]]:
        selected = ", ".join(self._quote(column) for column in columns)
        query = text(f"SELECT {selected} FROM {self._quote(table)} LIMIT :limit")
        findings: list[dict[str, Any]] = []
        with self.engine.connect() as conn:
            rows = conn.execute(query, {"limit": self.thresholds.pii_sample_limit}).mappings()
            for row_number, row in enumerate(rows, start=1):
                for column in columns:
                    value = row.get(column)
                    if not isinstance(value, str) or not value:
                        continue
                    for pii_type, pattern in PII_PATTERNS.items():
                        if pattern.search(value):
                            findings.append(
                                {
                                    "table": table,
                                    "column": column,
                                    "row_number": row_number,
                                    "pii_type": pii_type,
                                }
                            )
                            if len(findings) >= 20:
                                return findings
        return findings

    def _count_rows(self, table: str) -> int:
        with self.engine.connect() as conn:
            return int(conn.execute(text(f"SELECT COUNT(*) FROM {self._quote(table)}")).scalar_one() or 0)

    def _count_nulls(self, table: str, column: str) -> int:
        with self.engine.connect() as conn:
            return int(
                conn.execute(
                    text(
                        f"SELECT COUNT(*) FROM {self._quote(table)} "
                        f"WHERE {self._quote(column)} IS NULL"
                    )
                ).scalar_one()
                or 0
            )

    def _max_value(self, table: str, column: str) -> Any:
        with self.engine.connect() as conn:
            return conn.execute(
                text(f"SELECT MAX({self._quote(column)}) FROM {self._quote(table)}")
            ).scalar_one_or_none()

    def _quote(self, identifier: str) -> str:
        return self.engine.dialect.identifier_preparer.quote(identifier)


def run_data_quality_scorecard(
    *,
    database_url: str,
    json_output: Path | str,
    markdown_output: Path | str,
    expected_tables: set[str] | None = None,
    core_tables: set[str] | None = None,
    non_pii_tables: set[str] | None = None,
    thresholds: DataQualityThresholds | None = None,
    publish_metrics: bool = True,
) -> DataQualityScorecard:
    monitor = DataQualityMonitor(
        database_url,
        expected_tables=expected_tables,
        core_tables=core_tables,
        non_pii_tables=non_pii_tables,
        thresholds=thresholds,
    )
    scorecard = monitor.run(publish_metrics=publish_metrics)
    json_path = Path(json_output)
    markdown_path = Path(markdown_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(scorecard.to_json())
    markdown_path.write_text(scorecard.to_markdown())
    return scorecard


def load_expected_tables(db_struct_path: Path | None = None) -> set[str]:
    path = db_struct_path or REPO_ROOT / "db_struct.sql"
    if not path.exists():
        return set()
    content = path.read_text()
    return set(re.findall(r"CREATE TABLE public\.([A-Za-z_][A-Za-z0-9_]*)", content))


def publish_data_quality_metrics(scorecard: DataQualityScorecard) -> None:
    try:
        from src.observability import metrics
    except Exception:
        return

    for result in scorecard.pillars:
        if hasattr(metrics, "nrg_data_quality_pillar_status"):
            metrics.nrg_data_quality_pillar_status.labels(pillar=result.name).set(
                1 if result.status == "PASS" else 0
            )
        if hasattr(metrics, "nrg_data_quality_pillar_score"):
            metrics.nrg_data_quality_pillar_score.labels(pillar=result.name).set(result.score)
    if hasattr(metrics, "nrg_data_quality_p0_alerts"):
        metrics.nrg_data_quality_p0_alerts.set(sum(1 for alert in scorecard.alerts if alert.severity == "P0"))


def _default_non_pii_tables(tables: set[str]) -> set[str]:
    return {table for table in tables if not any(hint in table.lower() for hint in PII_TABLE_HINTS)}


def _is_text_column(column: dict[str, Any]) -> bool:
    type_name = str(column.get("type", "")).lower()
    return any(token in type_name for token in ("char", "clob", "json", "string", "text", "varchar"))


def _is_pii_column(column_name: str) -> bool:
    lowered = column_name.lower()
    return any(hint in lowered for hint in PII_COLUMN_HINTS)


def _freshness_column(columns: list[dict[str, Any]]) -> str | None:
    column_names = [column["name"] for column in columns]
    lowered = {name.lower(): name for name in column_names}
    for hint in FRESHNESS_COLUMN_HINTS:
        if hint in lowered:
            return lowered[hint]
    for name in column_names:
        lowered_name = name.lower()
        if lowered_name.endswith("_at") or lowered_name.endswith("_date"):
            return name
    return None


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        if candidate.endswith("Z"):
            candidate = f"{candidate[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _round_score(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return round(max(0.0, min(1.0, value)), 4)


def _round_measurement(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return round(max(0.0, value), 4)


def _redact_database_url(database_url: str) -> str:
    try:
        url = make_url(database_url)
        if url.password:
            url = url.set(password="***")
        return str(url)
    except Exception:
        return database_url
