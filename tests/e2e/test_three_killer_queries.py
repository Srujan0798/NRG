"""LB-3 end-to-end checks for the three canonical killer queries."""

from __future__ import annotations

import math
import os
import time
from pathlib import Path
from typing import Any

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "tests/benchmarks/killer_queries.yaml"
RUNS = int(os.getenv("NRG_KILLER_QUERY_RUNS", "20"))
ROLES = {
    "researcher": ("researcher_user", "researcher-pass", 1),
    "government": ("gov_user", "government-pass", 2),
    "industry": ("industry_user", "industry-pass", 3),
}


def _load_queries() -> list[dict[str, Any]]:
    return list((yaml.safe_load(CORPUS.read_text()) or {}).get("killer_queries", []))


class _LocalClient:
    def __init__(self):
        os.environ["DATABASE_URL"] = f"sqlite:///{ROOT / 'nrg_research.db'}"
        os.environ["TESTING"] = "true"
        from src.config.database import DatabaseManager

        DatabaseManager._instance = None
        from fastapi.testclient import TestClient
        from src.api import main as api_main

        api_main._db_instance = None
        self._client = TestClient(api_main.app)

    def post(self, path: str, **kwargs):
        return self._client.post(path, **kwargs)


class _RemoteClient:
    def __init__(self, base_url: str):
        import requests

        self._requests = requests
        self._base_url = base_url.rstrip("/")

    def post(self, path: str, **kwargs):
        return self._requests.post(f"{self._base_url}{path}", **kwargs)


@pytest.fixture(scope="module")
def api_client():
    base_url = os.getenv("NRG_API_URL")
    return _RemoteClient(base_url) if base_url else _LocalClient()


def _login(client, username: str, password: str) -> str:
    response = client.post("/login", json={"username": username, "password": password}, timeout=15)
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _query(client, token: str, query: str, session_id: str) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    response = client.post(
        "/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query, "session_id": session_id},
        timeout=30,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert response.status_code == 200, response.text
    return response.json(), elapsed_ms


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]


def _assert_expected_sql_shape(sql: str, case: dict[str, Any]) -> None:
    sql_lower = sql.lower()
    for needle in case.get("must_contain", []):
        needle_lower = needle.lower()
        if needle_lower == "split_part" and "split_part" not in sql_lower:
            assert "total_credit_score" in sql_lower
            assert "substr" in sql_lower or "substring" in sql_lower
            assert "instr" in sql_lower
            continue
        assert needle_lower in sql_lower, sql
    for forbidden in case.get("must_not_contain", []):
        assert forbidden.lower() not in sql_lower, sql


@pytest.mark.e2e
@pytest.mark.parametrize("case", _load_queries(), ids=lambda item: item["id"])
def test_killer_query_returns_cited_rows_and_meets_latency(api_client, case):
    tokens = {
        role: _login(api_client, username, password)
        for role, (username, password, _tier) in ROLES.items()
    }

    tier_payloads = {}
    for role, token in tokens.items():
        payload, _elapsed = _query(api_client, token, case["nl"], f"lb3-{case['id']}-{role}")
        tier_payloads[role] = payload
        assert payload.get("audit_event_id"), payload
        assert payload.get("citations"), payload
        assert len(payload.get("sql_results") or []) >= int(case.get("expected_min_rows", 1)), payload
        assert "[cite:" in payload.get("response", ""), payload

    for role in ("researcher", "government"):
        sql = tier_payloads[role].get("sql_query") or " ".join(tier_payloads[role].get("sql_queries") or [])
        assert sql, tier_payloads[role]
        _assert_expected_sql_shape(sql, case)

    timings = []
    researcher_token = tokens["researcher"]
    for idx in range(RUNS):
        payload, elapsed_ms = _query(
            api_client,
            researcher_token,
            case["nl"],
            f"lb3-{case['id']}-latency-{idx}",
        )
        assert len(payload.get("sql_results") or []) >= int(case.get("expected_min_rows", 1)), payload
        timings.append(elapsed_ms)

    assert _p95(timings) < float(case.get("p95_latency_ms", 4000)), timings
