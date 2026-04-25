#!/usr/bin/env python3
"""Pre-commit guard for tests that declare long runtimes without slow markers."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_THRESHOLD_SECONDS = 30


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    node_name: str
    timeout_seconds: float


def _is_test_path(path: Path) -> bool:
    return path.suffix == ".py" and "tests" in path.parts and (
        path.name.startswith("test_") or path.name == "conftest.py"
    )


def _marker_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _marker_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _marker_name(node.func)
    return ""


def _has_slow_marker(decorators: Sequence[ast.expr]) -> bool:
    return any(_marker_name(decorator).endswith("mark.slow") for decorator in decorators)


def _timeout_seconds(decorators: Sequence[ast.expr]) -> float | None:
    for decorator in decorators:
        if not isinstance(decorator, ast.Call):
            continue
        if not _marker_name(decorator.func).endswith("mark.timeout"):
            continue
        if not decorator.args:
            continue
        value = decorator.args[0]
        if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)):
            return float(value.value)
    return None


def _module_has_slow_marker(tree: ast.Module) -> bool:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "pytestmark" for target in node.targets):
            continue
        if _marker_name(node.value).endswith("mark.slow"):
            return True
        if isinstance(node.value, (ast.List, ast.Tuple)):
            if any(_marker_name(element).endswith("mark.slow") for element in node.value.elts):
                return True
    return False


def _path_has_slow_conftest(path: Path) -> bool:
    for parent in [path.parent, *path.parents]:
        conftest = parent / "conftest.py"
        if not conftest.exists():
            continue
        text = conftest.read_text(encoding="utf-8", errors="replace")
        if "add_marker(pytest.mark.slow" in text or "pytestmark = pytest.mark.slow" in text:
            return True
        if parent.name == "tests":
            break
    return False


def check_path(path: Path, threshold_seconds: float = DEFAULT_THRESHOLD_SECONDS) -> list[Violation]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [Violation(path=path, line=exc.lineno or 1, node_name="<syntax>", timeout_seconds=0)]

    module_is_slow = _module_has_slow_marker(tree) or _path_has_slow_conftest(path)
    violations: list[Violation] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        timeout = _timeout_seconds(node.decorator_list)
        if timeout is None or timeout <= threshold_seconds:
            continue
        if module_is_slow or _has_slow_marker(node.decorator_list):
            continue
        violations.append(
            Violation(
                path=path,
                line=node.lineno,
                node_name=node.name,
                timeout_seconds=timeout,
            )
        )

    return violations


def iter_test_paths(paths: Iterable[str]) -> list[Path]:
    selected: list[Path] = []
    raw_paths = [Path(path) for path in paths]
    if not raw_paths:
        raw_paths = [Path("tests")]

    for path in raw_paths:
        if not path.exists():
            continue
        if path.is_dir():
            selected.extend(candidate for candidate in path.rglob("*.py") if _is_test_path(candidate))
        elif _is_test_path(path):
            selected.append(path)

    return sorted(set(selected))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--max-seconds", type=float, default=DEFAULT_THRESHOLD_SECONDS)
    args = parser.parse_args(argv)

    violations: list[Violation] = []
    for path in iter_test_paths(args.paths):
        violations.extend(check_path(path, threshold_seconds=args.max_seconds))

    if not violations:
        return 0

    print("Tests with timeout markers above the local gate threshold must also use @pytest.mark.slow:")
    for violation in violations:
        print(
            f"{violation.path}:{violation.line}: {violation.node_name} "
            f"declares {violation.timeout_seconds:g}s"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
