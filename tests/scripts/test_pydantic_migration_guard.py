from __future__ import annotations

from pathlib import Path

from scripts.check_pydantic_migration_guard import (
    find_direct_v1_imports,
    validate_ci_python_guard,
)


def test_ci_guard_requires_required_jobs_to_pin_below_python_314(tmp_path: Path) -> None:
    workflow = tmp_path / "ci.yml"
    workflow.write_text(
        """
jobs:
  unit:
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: "3.14"
  python-314-compat:
    continue-on-error: true
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: "3.14"
""",
        encoding="utf-8",
    )

    violations = validate_ci_python_guard(workflow)

    assert any("unit" in violation for violation in violations)


def test_ci_guard_accepts_pinned_jobs_and_allowed_failure_314_lane(tmp_path: Path) -> None:
    workflow = tmp_path / "ci.yml"
    workflow.write_text(
        """
jobs:
  unit:
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
  python-314-compat:
    continue-on-error: true
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: "3.14"
""",
        encoding="utf-8",
    )

    assert validate_ci_python_guard(workflow) == []


def test_direct_pydantic_v1_import_inventory_ignores_docs_and_reports_code(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "src" / "bad.py").write_text("from pydantic.v1 import BaseModel\n")
    (tmp_path / "docs" / "note.md").write_text("from pydantic.v1 import BaseModel\n")

    imports = find_direct_v1_imports(tmp_path)

    assert imports == [Path("src/bad.py")]
