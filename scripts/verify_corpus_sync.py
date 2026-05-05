#!/usr/bin/env python3
"""Verify that CORPUS mirror files match their canonical sources."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MIRRORS = [
    ("Core_Idea_Clean.md", "CORPUS/Core_Idea_Clean.md"),
    ("db_struct.sql", "CORPUS/db_struct.sql"),
    ("docs/reports/SQL_AUDIT_RAW_dhairya.sql", "CORPUS/SQL_AUDIT_RAW_dhairya.sql"),
    ("tests/benchmarks/killer_queries.yaml", "CORPUS/killer_queries.yaml"),
    ("src/data/schema/business_term_glossary.yaml", "CORPUS/schema/business_term_glossary.yaml"),
    ("src/data/schema/nrg_full_schema.sql", "CORPUS/schema/nrg_full_schema.sql"),
    ("src/data/schema/production_schema.sql", "CORPUS/schema/production_schema.sql"),
    ("src/data/schema/schema_hints.md", "CORPUS/schema/schema_hints.md"),
    ("src/data/schema/schema_value_synonyms.md", "CORPUS/schema/schema_value_synonyms.md"),
    ("src/data/schema/sqlite_schema.sql", "CORPUS/schema/sqlite_schema.sql"),
    ("docs/specs/API_ENDPOINT_MATRIX.md", "CORPUS/api/endpoint_matrix.md"),
    (".claude/quality-bar.md", "CORPUS/quality/quality_bar.md"),
    (".claude/CURRENT_STATE.md", "CORPUS/state/current_state.md"),
    ("docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md", "CORPUS/state/source_of_truth_map.md"),
    ("docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md", "CORPUS/SQL_AUDIT_REPORT_DHAIRYA.md"),
]

DERIVED = [
    "CORPUS/SQL_AUDIT_REPORT_CLEAN.md",
    "CORPUS/CORPUS_INDEX.md",
    "CORPUS/README.md",
    "CORPUS/VERIFY.md",
    "CORPUS/architecture/system_overview.md",
    "CORPUS/architecture/data_pipeline.md",
    "CORPUS/architecture/security_model.md",
    "CORPUS/api/auth_flow.md",
    "CORPUS/frontend/structure.md",
    "CORPUS/frontend/design_system.md",
    "CORPUS/quality/testing_strategy.md",
    "CORPUS/tech_stack.md",
    "CORPUS/deployment/docker_compose.md",
    "CORPUS/deployment/infrastructure.md",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    results: list[dict[str, object]] = []
    ok = True

    for canonical_rel, mirror_rel in MIRRORS:
        canonical = ROOT / canonical_rel
        mirror = ROOT / mirror_rel
        if not canonical.exists() or not mirror.exists():
            ok = False
            results.append(
                {
                    "canonical": canonical_rel,
                    "mirror": mirror_rel,
                    "status": "missing",
                    "canonical_exists": canonical.exists(),
                    "mirror_exists": mirror.exists(),
                }
            )
            continue

        canonical_hash = sha256(canonical)
        mirror_hash = sha256(mirror)
        match = canonical_hash == mirror_hash
        ok = ok and match
        results.append(
            {
                "canonical": canonical_rel,
                "mirror": mirror_rel,
                "status": "match" if match else "mismatch",
                "sha256": canonical_hash,
                "mirror_sha256": mirror_hash,
            }
        )

    for derived_rel in DERIVED:
        path = ROOT / derived_rel
        if not path.exists():
            ok = False
            results.append({"derived": derived_rel, "status": "missing"})
        else:
            results.append({"derived": derived_rel, "status": "present", "sha256": sha256(path)})

    print(json.dumps({"ok": ok, "results": results}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
