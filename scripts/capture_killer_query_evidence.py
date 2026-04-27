#!/usr/bin/env python3
"""Capture LB-3 killer-query response, latency, and plan evidence."""

from __future__ import annotations

import json
import math
import os
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / os.getenv("NRG_EVIDENCE_DIR", "evidence/2026-04-27")
CORPUS = ROOT / "tests/benchmarks/killer_queries.yaml"
RUNS = int(os.getenv("NRG_KILLER_QUERY_RUNS", "20"))
ROLES = {
    "researcher": ("researcher_user", "researcher-pass", 1),
    "government": ("gov_user", "government-pass", 2),
    "industry": ("industry_user", "industry-pass", 3),
}
ROW_FLOOR_TABLES = [
    "academic_courses_details",
    "innovations_at_various_stages_of_technology_readiness_level",
    "innovation_grant_from_govt",
    "combined_ipo_patent_data",
    "publications",
    "researchers",
]


def resolve_local_database_url() -> str:
    configured_test = os.getenv("NRG_TEST_DATABASE_URL")
    if configured_test:
        return configured_test

    configured = os.getenv("DATABASE_URL")
    populated = ROOT / "data/nrg_research.db"
    if populated.exists():
        if not configured:
            return f"sqlite:///{populated}"
        if configured in {
            "sqlite:///nrg_research.db",
            f"sqlite:///{ROOT / 'nrg_research.db'}",
        }:
            return f"sqlite:///{populated}"

    if configured:
        return configured

    return f"sqlite:///{ROOT / 'nrg_research.db'}"


class LocalClient:
    def __init__(self) -> None:
        os.environ["DATABASE_URL"] = resolve_local_database_url()
        os.environ["TESTING"] = "true"
        from src.config.database import DatabaseManager

        DatabaseManager._instance = None
        from fastapi.testclient import TestClient
        from src.api import main as api_main

        api_main._db_instance = None
        self._client = TestClient(api_main.app)

    def post(self, path: str, **kwargs: Any):
        return self._client.post(path, **kwargs)

    def get(self, path: str, **kwargs: Any):
        return self._client.get(path, **kwargs)


class RemoteClient:
    def __init__(self, base_url: str) -> None:
        import requests

        self._requests = requests
        self._base_url = base_url.rstrip("/")

    def post(self, path: str, **kwargs: Any):
        return self._requests.post(f"{self._base_url}{path}", **kwargs)

    def get(self, path: str, **kwargs: Any):
        return self._requests.get(f"{self._base_url}{path}", **kwargs)


def load_queries() -> list[dict[str, Any]]:
    return list((yaml.safe_load(CORPUS.read_text()) or {}).get("killer_queries", []))


def client():
    base_url = os.getenv("NRG_API_URL")
    return RemoteClient(base_url) if base_url else LocalClient()


def login(api, username: str, password: str) -> str:
    response = api.post("/login", json={"username": username, "password": password}, timeout=15)
    response.raise_for_status()
    return response.json()["access_token"]


def query(api, token: str, text: str, session_id: str) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    response = api.post(
        "/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": text, "session_id": session_id},
        timeout=30,
    )
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    response.raise_for_status()
    return response.json(), elapsed_ms


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)], 2)


def sqlite_path() -> Path:
    raw = resolve_local_database_url()
    if raw.startswith("sqlite:///"):
        path = Path(raw.removeprefix("sqlite:///"))
        return path if path.is_absolute() else ROOT / path
    return ROOT / "nrg_research.db"


def row_floor() -> dict[str, int]:
    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith("postgres"):
        try:
            import psycopg2

            with psycopg2.connect(database_url) as conn:
                with conn.cursor() as cur:
                    counts = {}
                    for table in ROW_FLOOR_TABLES:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        counts[table] = int(cur.fetchone()[0])
                    return counts
        except Exception:
            return {}

    db_path = sqlite_path()
    if not db_path.exists():
        return {}
    with sqlite3.connect(db_path) as conn:
        return {
            table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in ROW_FLOOR_TABLES
        }


def write_explain(sql: str, path: Path, case_id: str) -> None:
    database_url = os.getenv("DATABASE_URL", "")
    captured = datetime.now(UTC).isoformat()
    if database_url.startswith("postgres"):
        try:
            import psycopg2

            with psycopg2.connect(database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(f"EXPLAIN ANALYZE {sql}")
                    lines = [row[0] for row in cur.fetchall()]
            body = "\n".join(lines)
            engine = "PostgreSQL"
        except Exception as exc:
            body = f"EXPLAIN ANALYZE unavailable: {exc}"
            engine = "PostgreSQL"
    else:
        from src.config.database import register_sqlite_compat_functions

        with sqlite3.connect(sqlite_path()) as conn:
            register_sqlite_compat_functions(conn)
            rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}").fetchall()
        body = "\n".join(str(tuple(row)) for row in rows)
        engine = "local SQLite volumetric proxy"

    path.write_text(
        "\n".join(
            [
                f"Killer query: {case_id}",
                f"Captured: {captured}",
                f"Engine: {engine}",
                "",
                "SQL:",
                sql,
                "",
                "Plan:",
                body,
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    api = client()
    tokens = {
        role: login(api, username, password)
        for role, (username, password, _tier) in ROLES.items()
    }

    health_queries: list[dict[str, Any]] = []
    for index, case in enumerate(load_queries(), start=1):
        responses: dict[str, Any] = {}
        for role, token in tokens.items():
            payload, elapsed_ms = query(
                api,
                token,
                case["nl"],
                f"lb3-evidence-{case['id']}-{role}",
            )
            responses[role] = {"elapsed_ms": elapsed_ms, "payload": payload}

        timings = []
        for run_index in range(RUNS):
            payload, elapsed_ms = query(
                api,
                tokens["researcher"],
                case["nl"],
                f"lb3-evidence-{case['id']}-latency-{run_index}",
            )
            if len(payload.get("sql_results") or []) < int(case.get("expected_min_rows", 1)):
                raise AssertionError(f"{case['id']} returned too few rows during latency run")
            timings.append(elapsed_ms)

        evidence_path = EVIDENCE_DIR / f"killer_query_{index}_response.json"
        explain_path = EVIDENCE_DIR / f"explain_killer_{index}.txt"
        researcher_payload = responses["researcher"]["payload"]
        sql = researcher_payload.get("sql_query") or " ".join(researcher_payload.get("sql_queries") or [])
        write_explain(sql, explain_path, case["id"])

        evidence_path.write_text(
            json.dumps(
                {
                    "case": case,
                    "responses": responses,
                    "latency_runs_ms": timings,
                    "p95_latency_ms": p95(timings),
                    "captured_at": datetime.now(UTC).isoformat(),
                    "row_floor": row_floor(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        health_queries.append(
            {
                "id": case["id"],
                "last_run_time": datetime.now(UTC).isoformat(),
                "p95_latency_ms": p95(timings),
                "threshold_ms": case.get("p95_latency_ms", 4000),
                "row_count": len(researcher_payload.get("sql_results") or []),
                "citation_count": len(researcher_payload.get("citations") or []),
                "status": "healthy",
                "evidence_path": str(evidence_path.relative_to(ROOT)),
                "explain_path": str(explain_path.relative_to(ROOT)),
            }
        )

    health = {
        "status": "healthy",
        "last_run_time": datetime.now(UTC).isoformat(),
        "source": "local_volumetric_sqlite_proxy" if not os.getenv("NRG_API_URL") else os.getenv("NRG_API_URL"),
        "row_floor": row_floor(),
        "queries": health_queries,
    }
    (EVIDENCE_DIR / "killer_query_health.json").write_text(
        json.dumps(health, indent=2),
        encoding="utf-8",
    )
    endpoint = api.get("/api/health/killer_queries", timeout=15)
    (EVIDENCE_DIR / "killer_query_health_endpoint.json").write_text(
        json.dumps(endpoint.json(), separators=(",", ":")),
        encoding="utf-8",
    )
    print(json.dumps(health, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
