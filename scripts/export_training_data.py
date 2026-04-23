#!/usr/bin/env python3
"""
Export Training Data for Fine-Tuning — Task #22 Phase 3

Usage:
    python scripts/export_training_data.py --format jsonl --min-grade silver
    python scripts/export_training_data.py --format alpaca --min-grade gold --route text_to_sql
    python scripts/export_training_data.py --format sharegpt --min-grade silver --dry-run
    python scripts/export_training_data.py --format sql --min-grade bronze

SKILLS: /python-backend (FastAPI async patterns), /data-visualization (progress bars)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Export training data for fine-tuning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/export_training_data.py --format jsonl --min-grade silver
  python scripts/export_training_data.py --format alpaca --min-grade gold
  python scripts/export_training_data.py --format sql --route text_to_sql --min-grade bronze
  python scripts/export_training_data.py --format sharegpt --dry-run
        """,
    )
    parser.add_argument(
        "--format",
        default="jsonl",
        choices=["jsonl", "alpaca", "sharegpt", "sql", "chat"],
        help="Output format (jsonl=Alpaca, sharegpt=chat, sql=text-to-SQL)",
    )
    parser.add_argument(
        "--min-grade",
        default="silver",
        choices=["gold", "silver", "bronze"],
        help="Minimum quality grade to export",
    )
    parser.add_argument(
        "--route",
        default=None,
        choices=["text_to_sql", "rag", "hybrid", None],
        help="Filter by route type (default: all routes)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: data/training/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate pairs without writing files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("  NRG Training Data Export Pipeline")
    logger.info("=" * 60)
    logger.info(f"  Format:       {args.format}")
    logger.info(f"  Min grade:    {args.min_grade}")
    logger.info(f"  Route:        {args.route or 'all'}")
    logger.info(f"  Output dir:   {args.output_dir or 'data/training/'}")
    logger.info(f"  Dry run:     {args.dry_run}")
    logger.info("=" * 60)

    from src.training.export import run_export

    try:
        stats = run_export(
            fmt=args.format,
            min_grade=args.min_grade,
            route=args.route,
            output_dir=args.output_dir,
            dry_run=args.dry_run,
        )

        print()
        print("=" * 60)
        print("  EXPORT REPORT")
        print("=" * 60)
        print(f"  Version:      {stats['version']}")
        print(f"  Pairs read:  {stats['pairs_read']}")
        print(f"  Dedup/filter:{stats['pairs_filtered']}")
        print(f"  Pairs kept:  {stats['pairs_kept']}")
        print(f"  Pairs export:{stats['pairs_exported']}")
        print()
        print(f"  By original grade:")
        for grade, count in stats.get("by_original_grade", {}).items():
            print(f"    {grade:10s}: {count}")
        print()
        by_filter = stats.get("by_filter_grade", {})
        print(f"  After filter (gold+silver only):")
        print(f"    gold:  {by_filter.get('gold', 0)}")
        print(f"    silver:{by_filter.get('silver', 0)}")
        print(f"    bronze:{by_filter.get('bronze', 0)}")
        print()
        if not args.dry_run:
            print(f"  Output:       {stats['filename']}")
        else:
            print(f"  Output:       (dry run)")
        print("=" * 60)

        if stats["pairs_exported"] == 0:
            logger.warning("No pairs exported — check quality grades in database")
            sys.exit(1)
        return 0

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
