#!/usr/bin/env python3
"""Collect API evidence for the founder laptop sanity check."""

from __future__ import annotations

import json
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence" / "2026-04-26"
API_BASE = "http://127.0.0.1:8000"

TIERS = {
    "t1": {"username": "researcher_user", "password": "researcher-pass", "label": "researcher"},
    "t2": {"username": "gov_user", "password": "government-pass", "label": "government"},
    "t3": {"username": "industry_user", "password": "industry-pass", "label": "industry"},
}

KILLER_QUERIES = [
    {
        "id": "KILLER-01",
        "query": "Which IIT has the highest total innovation credits in FY 2022-23, and how far above the national average is it?",
    },
    {
        "id": "KILLER-02",
        "query": "For IIT Madras, what % of innovations moved from Lab Validation (Level 4) to Market Ready (Level 9) in the last 3 years, and which stage is the biggest bottleneck?",
    },
    {
        "id": "KILLER-03",
        "query": "Identify 3 institutes that cut grants >40% YoY yet increased granted patents — who is doing more with less?",
    },
]


def http_json(method: str, path: str, payload: dict[str, Any] | None = None, token: str | None = None) -> tuple[int, dict[str, Any], int]:
    body = json.dumps(payload or {}).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(f"{API_BASE}{path}", data=body, headers=headers, method=method)
    started = time.perf_counter()
    try:
        with request.urlopen(req, timeout=20) as resp:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw), elapsed_ms
    except error.HTTPError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        raw = exc.read().decode("utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"raw": raw}
        return exc.code, data, elapsed_ms


def safe_subset(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "audit_event_id": payload.get("audit_event_id"),
        "query_id": payload.get("query_id"),
        "status": payload.get("status"),
        "tier": payload.get("tier"),
        "verification_status": payload.get("verification_status"),
        "citation_count": len(payload.get("citations") or []),
        "answer_confidence": payload.get("answer_confidence"),
        "answer_confidence_score": payload.get("answer_confidence_score"),
        "sql_query": payload.get("sql_query"),
        "sql_result_count": len(payload.get("sql_results") or []),
        "sql_results": (payload.get("sql_results") or [])[:5],
        "warnings": payload.get("warnings") or [],
    }


def result_keys(payload: dict[str, Any]) -> set[str]:
    rows = payload.get("sql_results") or []
    if not rows:
        return set()
    return set(rows[0].keys())


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {
        "captured_at": datetime.now(UTC).isoformat(),
        "api_base": API_BASE,
        "queries": {},
        "latencies_ms": [],
        "tier_diffs": {},
        "failures": [],
    }

    tokens: dict[str, str] = {}
    for tier, creds in TIERS.items():
        status, payload, elapsed_ms = http_json(
            "POST",
            "/login",
            {"username": creds["username"], "password": creds["password"]},
        )
        summary.setdefault("logins", {})[tier] = {"status": status, "elapsed_ms": elapsed_ms}
        if status != 200 or "access_token" not in payload:
            summary["failures"].append({"tier": tier, "stage": "login", "status": status, "payload": payload})
            continue
        tokens[tier] = payload["access_token"]

    raw_results: dict[str, dict[str, dict[str, Any]]] = {}
    for item in KILLER_QUERIES:
        qid = item["id"]
        raw_results[qid] = {}
        summary["queries"][qid] = {}
        for tier in TIERS:
            token = tokens.get(tier)
            if not token:
                continue
            status, payload, elapsed_ms = http_json(
                "POST",
                "/query",
                {"query": item["query"], "session_id": f"founder-laptop-{tier}-{qid}"},
                token=token,
            )
            summary["latencies_ms"].append(elapsed_ms)
            payload["_http_status"] = status
            payload["_elapsed_ms"] = elapsed_ms
            payload["_query_id_expected"] = qid
            raw_results[qid][tier] = payload

            evidence_payload = {
                "captured_at": datetime.now(UTC).isoformat(),
                "tier": tier,
                "persona": TIERS[tier]["label"],
                "query_id": qid,
                "query": item["query"],
                "http_status": status,
                "elapsed_ms": elapsed_ms,
                "response": payload,
                "evidence_subset": safe_subset(payload),
            }
            path = EVIDENCE_DIR / f"founder_laptop_sanity_{tier}_{qid}.json"
            path.write_text(json.dumps(evidence_payload, indent=2, sort_keys=True, default=str) + "\n")

            summary["queries"][qid][tier] = {
                "status": status,
                "elapsed_ms": elapsed_ms,
                "sql_rows": len(payload.get("sql_results") or []),
                "citations": len(payload.get("citations") or []),
                "answer_confidence": payload.get("answer_confidence"),
                "fields": sorted(result_keys(payload)),
                "evidence": str(path.relative_to(ROOT)),
            }
            if status != 200 or not payload.get("citations") or len(payload.get("sql_results") or []) < 1:
                summary["failures"].append(
                    {
                        "tier": tier,
                        "query_id": qid,
                        "stage": "query",
                        "status": status,
                        "sql_rows": len(payload.get("sql_results") or []),
                        "citations": len(payload.get("citations") or []),
                    }
                )

    for qid, tiers in raw_results.items():
        t1 = result_keys(tiers.get("t1", {}))
        t3 = result_keys(tiers.get("t3", {}))
        diff = sorted(t1.symmetric_difference(t3))
        summary["tier_diffs"][qid] = {
            "t1_fields": sorted(t1),
            "t3_fields": sorted(t3),
            "differing_field_count": len(diff),
            "differing_fields": diff,
            "meets_four_column_gate": len(diff) >= 4,
        }

    if summary["latencies_ms"]:
        summary["p95_ms"] = int(statistics.quantiles(summary["latencies_ms"], n=20, method="inclusive")[18])
        summary["max_ms"] = max(summary["latencies_ms"])
    else:
        summary["p95_ms"] = None
        summary["max_ms"] = None

    summary["acceptance"] = {
        "all_queries_have_cited_rows": not summary["failures"],
        "p95_under_4000_ms": summary["p95_ms"] is not None and summary["p95_ms"] < 4000,
        "tier_shape_gate": all(item["meets_four_column_gate"] for item in summary["tier_diffs"].values()),
    }
    out = EVIDENCE_DIR / "founder_laptop_query_summary.json"
    out.write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0 if all(summary["acceptance"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
