"""
Training Data Export Pipeline — Task #22 Phase 3
Reads GOLD+SILVER pairs, applies quality filter, formats, writes versioned files.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from src.training.data_collector import get_training_collector
from src.training.data_formatter import DataFormatter, pairs_to_jsonl
from src.training.quality_filter import QualityFilter

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "training"
SUPPORTED_FORMATS = {"jsonl", "alpaca", "sharegpt", "sql", "chat"}


class ExportPipeline:
    """Export pipeline for fine-tuning data.

    Reads pairs from the training_pairs table, filters quality,
    formats into the desired output format, and writes versioned files.

    Version naming: v001, v002, ... (auto-incremented from existing files)
    """

    def __init__(
        self,
        output_dir: Path | str | None = None,
        min_grade: str = "silver",
    ):
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.min_grade = min_grade
        self.collector = get_training_collector()
        self.formatter = DataFormatter(include_metadata=True)
        self.filter = QualityFilter()

    def _get_next_version(self) -> str:
        """Determine the next export version (v001, v002, ...)."""
        existing = sorted(
            [p.name for p in self.output_dir.glob("v*.jsonl")],
            key=lambda x: int(x[1:4]) if x[1:4].isdigit() else 0,
        )
        if not existing:
            return "v001"
        last = int(existing[-1][1:4])
        return f"v{last + 1:03d}"

    def _get_export_filename(self, version: str, fmt: str) -> str:
        """Get filename for an export version and format."""
        return f"{version}_{fmt}.jsonl"

    def export(
        self,
        fmt: Literal["jsonl", "alpaca", "sharegpt", "sql", "chat"] = "jsonl",
        route: str | None = None,
        dry_run: bool = False,
    ) -> dict:
        """Run the full export pipeline.

        Returns a stats dict with:
        - version: export version tag
        - pairs_read: total pairs from DB
        - pairs_kept: after quality filter
        - pairs_exported: written to file
        - by_grade: breakdown by grade
        - filename: output file path
        """
        if fmt == "alpaca":
            fmt_internal = "alpaca"
        elif fmt in ("sharegpt", "chat"):
            fmt_internal = "sharegpt"
        elif fmt == "sql":
            fmt_internal = "sql"
        else:
            fmt_internal = "jsonl"

        version = self._get_next_version()
        pairs = self.collector.get_training_pairs(
            min_grade=self.min_grade,
            limit=100000,
            route=route,
        )

        grade_stats = {"gold": 0, "silver": 0, "bronze": 0, "reject": 0, "ungraded": 0}
        for p in pairs:
            g = p.get("quality_grade", "ungraded")
            grade_stats[g] = grade_stats.get(g, 0) + 1

        kept_pairs, filter_stats = self.filter.filter_pairs(pairs)

        formatted_pairs = self.formatter.format_batch(kept_pairs, fmt_internal)
        if route == "text_to_sql" and fmt_internal != "sql":
            formatted_pairs = [p for p in formatted_pairs if p.get("sql_query")]
        elif route == "rag":
            formatted_pairs = [p for p in formatted_pairs if not p.get("sql_query")]

        export_stats = {
            "version": version,
            "timestamp": datetime.now(UTC).isoformat(),
            "format": fmt,
            "min_grade": self.min_grade,
            "route_filter": route,
            "pairs_read": len(pairs),
            "pairs_filtered": filter_stats.get("dedup_removed", 0),
            "pairs_kept": len(kept_pairs),
            "pairs_exported": len(formatted_pairs),
            "by_original_grade": grade_stats,
            "by_filter_grade": {
                "gold": len([p for p in kept_pairs if p.get("quality_grade") == "gold"]),
                "silver": len([p for p in kept_pairs if p.get("quality_grade") == "silver"]),
                "bronze": len([p for p in kept_pairs if p.get("quality_grade") == "bronze"]),
            },
        }

        if not dry_run:
            output_file = self.output_dir / self._get_export_filename(version, fmt)
            count = pairs_to_jsonl(formatted_pairs, output_file)
            export_stats["filename"] = str(output_file)

            exported_ids = [p.get("id") for p in kept_pairs if p.get("id")]
            self.collector.mark_exported(exported_ids, version)

            manifest_path = self.output_dir / f"{version}_manifest.json"
            manifest_path.write_text(json.dumps(export_stats, indent=2, default=str))

            logger.info(f"Export complete: {export_stats}")
        else:
            export_stats["filename"] = "(dry run, no file written)"

        return export_stats

    def get_export_history(self) -> list[dict]:
        """Return all previous exports from manifest files."""
        manifests = sorted(self.output_dir.glob("v*_manifest.json"))
        exports = []
        for m in manifests:
            try:
                exports.append(json.loads(m.read_text()))
            except Exception as e:
                logger.warning(f"Could not read manifest {m}: {e}")
        return exports


def run_export(
    fmt: str = "jsonl",
    min_grade: str = "silver",
    route: str | None = None,
    output_dir: str | None = None,
    dry_run: bool = False,
) -> dict:
    """CLI-friendly export runner."""
    pipeline = ExportPipeline(output_dir=output_dir, min_grade=min_grade)
    return pipeline.export(fmt=fmt, route=route, dry_run=dry_run)
