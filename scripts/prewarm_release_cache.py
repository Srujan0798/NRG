#!/usr/bin/env python3
"""Prewarm NRG query cache with canonical production acceptance questions."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Awaitable, Callable

import httpx


DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_SESSION_PREFIX = "release-prewarm"


@dataclass(frozen=True)
class PrewarmResult:
    """Result for one cache prewarm request."""

    query: str
    elapsed_seconds: float
    rows_returned: int
    audit_event_id: str | None
    status: str


PostFn = Callable[..., Awaitable[Any]]


def default_release_queries() -> list[str]:
    """Return canonical queries that must be hot before acceptance use."""
    return [
        (
            "For IIT Madras, trace the TRL pipeline: what percent of innovations "
            "started at Lab Validation Level 4 reached Market Ready Level 9 in "
            "the last 3 years, and which stage lost the most projects?"
        ),
        "Calculate the cost per patent granted for institutes with more than 10 crore grants.",
        (
            "Identify institutes where grant funding dropped more than 40 percent "
            "year over year yet increased granted patents."
        ),
        "Top 5 funding agencies by total grant amount.",
        "Show innovation progression at IIT Madras.",
    ]


def load_queries(path: str | None = None) -> list[str]:
    """Load release queries from a text file or use the built-in canonical set."""
    if not path:
        return default_release_queries()

    with open(path, "r", encoding="utf-8") as handle:
        queries = [line.strip() for line in handle if line.strip() and not line.startswith("#")]
    if not queries:
        raise ValueError(f"No queries found in {path}")
    return queries


def build_query_payload(query: str, session_id: str) -> dict[str, str]:
    """Build payload using the production `/query` contract."""
    return {"query": query, "session_id": session_id}


async def _httpx_post(url: str, *, headers: dict[str, str], json: dict[str, str], timeout: float):
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.post(url, headers=headers, json=json)


async def prewarm_queries(
    queries: list[str],
    *,
    token: str,
    api_url: str = DEFAULT_API_URL,
    session_prefix: str = DEFAULT_SESSION_PREFIX,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    post_fn: PostFn = _httpx_post,
) -> list[PrewarmResult]:
    """Send each query through `/query` so application cache is warm."""
    if not token:
        raise ValueError("token is required")

    endpoint = f"{api_url.rstrip('/')}/query"
    headers = {"Authorization": f"Bearer {token}"}
    results: list[PrewarmResult] = []

    for index, query in enumerate(queries, start=1):
        response = await post_fn(
            endpoint,
            headers=headers,
            json=build_query_payload(query, f"{session_prefix}-{index}"),
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("sql_results") or []
        elapsed = response.elapsed.total_seconds()
        results.append(
            PrewarmResult(
                query=query,
                elapsed_seconds=round(float(elapsed), 3),
                rows_returned=len(rows) if isinstance(rows, list) else 0,
                audit_event_id=payload.get("audit_event_id"),
                status=str(payload.get("status", "unknown")),
            )
        )

    return results


def _resolve_token(args: argparse.Namespace) -> str:
    if args.token:
        return args.token
    return os.environ.get(args.token_env, "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prewarm NRG release query cache")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--queries-file")
    parser.add_argument("--token")
    parser.add_argument("--token-env", default="NRG_RELEASE_TOKEN")
    parser.add_argument("--session-prefix", default=DEFAULT_SESSION_PREFIX)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    queries = load_queries(args.queries_file)
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "query_count": len(queries), "queries": queries}, indent=2))
        return 0

    token = _resolve_token(args)
    if not token:
        raise SystemExit(f"Missing token. Pass --token or set {args.token_env}.")

    results = asyncio.run(
        prewarm_queries(
            queries,
            token=token,
            api_url=args.api_url,
            session_prefix=args.session_prefix,
        )
    )
    print(json.dumps([asdict(result) for result in results], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
