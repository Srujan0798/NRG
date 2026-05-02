"""Regression checks for async query handler blocking boundaries."""

from __future__ import annotations

import ast
from pathlib import Path


QUERY_SERVICE = Path(__file__).resolve().parents[2] / "src/api/query_service.py"


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _async_method(tree: ast.Module, class_name: str, name: str) -> ast.AsyncFunctionDef:
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for item in node.body:
            if isinstance(item, ast.AsyncFunctionDef) and item.name == name:
                return item
    raise AssertionError(f"async method not found: {class_name}.{name}")


def _to_thread_targets(function_node: ast.AsyncFunctionDef) -> set[str]:
    targets: set[str] = set()
    for node in ast.walk(function_node):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node.func) != "asyncio.to_thread" or not node.args:
            continue
        targets.add(_call_name(node.args[0]) or "")
    return targets


def _direct_calls(function_node: ast.AsyncFunctionDef, names: set[str]) -> set[str]:
    calls: set[str] = set()
    for node in ast.walk(function_node):
        if isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name in names:
                calls.add(name)
    return calls


def test_query_handler_keeps_blocking_answer_paths_off_event_loop() -> None:
    tree = ast.parse(QUERY_SERVICE.read_text())
    query_impl = _async_method(tree, "QueryAnswerService", "query_with_langgraph")

    blocking_paths = {
        "self.deps.c4_read_model_response",
        "self.deps.fast_query_response",
        "self.deps.academic_follow_up_response",
        "self.deps.killer_query_response",
        "self.deps.advanced_adversarial_response",
        "self.deps.run_workflow",
    }

    assert _direct_calls(query_impl, blocking_paths) == set()
    assert blocking_paths.issubset(_to_thread_targets(query_impl))


def test_stream_handler_builds_answer_payload_off_event_loop() -> None:
    tree = ast.parse(QUERY_SERVICE.read_text())
    stream_impl = _async_method(tree, "QueryAnswerService", "query_stream_response")

    assert "self.build_stream_answer_payload" in _to_thread_targets(stream_impl)
