"""Regression checks for query answer-engine ownership."""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
API_MAIN = REPO_ROOT / "src/api/main.py"
QUERY_SERVICE = REPO_ROOT / "src/api/query_service.py"


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text())


def _class_names(tree: ast.Module) -> set[str]:
    return {node.name for node in tree.body if isinstance(node, ast.ClassDef)}


def _function_line_span(tree: ast.Module, name: str) -> int:
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef) and node.name == name:
            return (node.end_lineno or node.lineno) - node.lineno + 1
    raise AssertionError(f"function not found: {name}")


def test_query_answer_engine_has_service_module() -> None:
    assert QUERY_SERVICE.exists()
    tree = _tree(QUERY_SERVICE)

    assert {"QueryAnswerService", "QueryServiceDependencies"}.issubset(_class_names(tree))


def test_main_keeps_only_thin_query_compatibility_wrappers() -> None:
    tree = _tree(API_MAIN)

    assert "_query_answer_service" in API_MAIN.read_text()
    assert _function_line_span(tree, "_build_stream_answer_payload") <= 12
    assert _function_line_span(tree, "_query_stream_response") <= 12
    assert _function_line_span(tree, "_query_with_langgraph_impl") <= 12
