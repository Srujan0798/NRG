"""Regression checks for async query handler blocking boundaries."""

from __future__ import annotations

import ast
from pathlib import Path


API_MAIN = Path(__file__).resolve().parents[2] / "src/api/main.py"


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _async_function(tree: ast.Module, name: str) -> ast.AsyncFunctionDef:
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name:
            return node
    raise AssertionError(f"async function not found: {name}")


def _to_thread_targets(function_node: ast.AsyncFunctionDef) -> set[str]:
    targets: set[str] = set()
    for node in ast.walk(function_node):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node.func) != "asyncio.to_thread" or not node.args:
            continue
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Name):
            targets.add(first_arg.id)
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
    tree = ast.parse(API_MAIN.read_text())
    query_impl = _async_function(tree, "_query_with_langgraph_impl")

    blocking_paths = {
        "_c4_read_model_response",
        "_fast_query_response",
        "_academic_follow_up_response",
        "_killer_query_response",
        "_advanced_adversarial_response",
        "_run_workflow",
    }

    assert _direct_calls(query_impl, blocking_paths) == set()
    assert blocking_paths.issubset(_to_thread_targets(query_impl))


def test_stream_handler_builds_answer_payload_off_event_loop() -> None:
    tree = ast.parse(API_MAIN.read_text())
    stream_impl = _async_function(tree, "_query_stream_response")

    assert "_build_stream_answer_payload" in _to_thread_targets(stream_impl)
