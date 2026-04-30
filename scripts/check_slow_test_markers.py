#!/usr/bin/env python3
"""Detect long-timeout pytest tests that are missing a slow marker."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

MAX_UNMARKED_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class SlowMarkerViolation:
    path: Path
    node_name: str
    timeout_seconds: float
    line: int


def _mark_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _mark_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _decorator_mark_name(decorator: ast.AST) -> str | None:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    name = _mark_name(target)
    if name and name.startswith("pytest.mark."):
        return name.removeprefix("pytest.mark.")
    return name


def _decorator_timeout_seconds(decorator: ast.AST) -> float | None:
    if not isinstance(decorator, ast.Call):
        return None
    if _decorator_mark_name(decorator) != "timeout":
        return None
    if not decorator.args:
        return None
    value = decorator.args[0]
    if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)):
        return float(value.value)
    return None


def _has_slow_decorator(decorators: list[ast.expr]) -> bool:
    return any(_decorator_mark_name(decorator) == "slow" for decorator in decorators)


def _module_has_slow_marker(tree: ast.Module) -> bool:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "pytestmark" for target in node.targets):
            continue
        value = node.value
        if _mark_name(value) == "pytest.mark.slow":
            return True
        if isinstance(value, (ast.List, ast.Tuple)):
            if any(_mark_name(item) == "pytest.mark.slow" for item in value.elts):
                return True
    return False


def check_path(path: Path, max_unmarked_timeout: int = MAX_UNMARKED_TIMEOUT_SECONDS) -> list[SlowMarkerViolation]:
    """Return long-timeout test functions that do not have slow coverage."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    module_slow = _module_has_slow_marker(tree)
    violations: list[SlowMarkerViolation] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue
        if module_slow or _has_slow_decorator(node.decorator_list):
            continue
        for decorator in node.decorator_list:
            timeout = _decorator_timeout_seconds(decorator)
            if timeout is not None and timeout > max_unmarked_timeout:
                violations.append(
                    SlowMarkerViolation(
                        path=path,
                        node_name=node.name,
                        timeout_seconds=timeout,
                        line=node.lineno,
                    )
                )
                break
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--max-seconds", type=int, default=MAX_UNMARKED_TIMEOUT_SECONDS)
    args = parser.parse_args()

    violations: list[SlowMarkerViolation] = []
    for root in args.paths:
        candidates = [root] if root.is_file() else sorted(root.rglob("test_*.py"))
        for path in candidates:
            violations.extend(check_path(path, max_unmarked_timeout=args.max_seconds))

    for violation in violations:
        print(
            f"{violation.path}:{violation.line}: {violation.node_name} "
            f"uses timeout({violation.timeout_seconds:g}) without @pytest.mark.slow"
        )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
