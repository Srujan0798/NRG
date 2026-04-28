#!/usr/bin/env python3
"""Guardrails for the Pydantic V1 to V2 / Python 3.14 migration path."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


DEFAULT_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "docs",
    "htmlcov",
    "node_modules",
    "site-packages",
    "venv",
}


def _iter_job_blocks(workflow_text: str) -> Iterable[tuple[str, str]]:
    job_header = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$", re.MULTILINE)
    matches = list(job_header.finditer(workflow_text))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(workflow_text)
        yield match.group(1), workflow_text[start:end]


def _extract_python_versions(block: str) -> list[str]:
    versions: list[str] = []
    for raw_value in re.findall(r"python-version:\s*([^\n#]+)", block):
        value = raw_value.strip().strip("'\"")
        if value.startswith("${{"):
            continue
        versions.extend(re.findall(r"\d+\.\d+(?:-dev)?", value))
    return versions


def _is_python_314_or_newer(version: str) -> bool:
    numeric = version.removesuffix("-dev")
    try:
        major, minor = numeric.split(".", 1)
        return (int(major), int(minor)) >= (3, 14)
    except ValueError:
        return False


def validate_ci_python_guard(workflow_path: Path) -> list[str]:
    """Return violations for required CI jobs that are not pinned below Python 3.14."""

    text = workflow_path.read_text(encoding="utf-8")
    violations: list[str] = []
    compat_job_found = False

    for job_name, block in _iter_job_blocks(text):
        versions = _extract_python_versions(block)
        if job_name == "python-314-compat":
            compat_job_found = True
            if "continue-on-error: true" not in block:
                violations.append("python-314-compat must be continue-on-error: true")
            if not any(_is_python_314_or_newer(version) for version in versions):
                violations.append("python-314-compat must exercise Python 3.14 or newer")
            continue

        for version in versions:
            if _is_python_314_or_newer(version):
                violations.append(
                    f"{job_name} uses required Python {version}; pin required CI jobs below 3.14"
                )

    if not compat_job_found:
        violations.append("missing allowed-to-fail python-314-compat CI job")

    return violations


def find_direct_v1_imports(root: Path) -> list[Path]:
    """Return relative Python files with direct pydantic.v1 imports."""

    imports: list[Path] = []
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if any(part in DEFAULT_IGNORED_DIRS for part in relative.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if re.search(r"^\s*(from\s+pydantic\.v1\b|import\s+pydantic\.v1\b)", text, re.MULTILINE):
            imports.append(relative)
    return sorted(imports)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--workflow", type=Path, default=Path(".github/workflows/ci.yml"))
    parser.add_argument(
        "--migration-doc",
        type=Path,
        default=Path("docs/engineering/PYDANTIC_V2_MIGRATION_PLAN_2026-04-28.md"),
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable report")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    workflow = args.workflow if args.workflow.is_absolute() else repo_root / args.workflow
    migration_doc = (
        args.migration_doc if args.migration_doc.is_absolute() else repo_root / args.migration_doc
    )

    violations = validate_ci_python_guard(workflow)
    direct_imports = find_direct_v1_imports(repo_root)
    if direct_imports:
        violations.extend(f"direct pydantic.v1 import: {path}" for path in direct_imports)
    if not migration_doc.exists():
        violations.append(f"missing migration plan: {migration_doc.relative_to(repo_root)}")

    report = {
        "ok": not violations,
        "workflow": str(workflow.relative_to(repo_root)),
        "migration_doc": str(migration_doc.relative_to(repo_root)),
        "direct_pydantic_v1_imports": [str(path) for path in direct_imports],
        "violations": violations,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"ok: {str(report['ok']).lower()}")
        print(f"direct_pydantic_v1_imports: {len(direct_imports)}")
        for violation in violations:
            print(f"- {violation}")

    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
