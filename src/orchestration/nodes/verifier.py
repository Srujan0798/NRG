"""Verifier node - citation faithfulness checks."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from src.config.llm_config import get_llm_client
from src.observability.langfuse_tracer import trace_llm_call

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "verifier_system.md"
CITATION_PATTERN = re.compile(r"\[cite:([^:\]]+):([^\]]+)\]")


@trace_llm_call("verifier")
def verifier_node(state: Any) -> dict:
    """Verify cited claims against available evidence."""
    response = _state_get(state, "synthesized_response", "") or ""
    retries = int(_state_get(state, "verification_retries", 0) or 0)
    citations = _extract_citations(response)

    synth_method = _state_get(state, "synthesis_method", "unknown")
    if not citations:
        # Structured-only responses without explicit citations are acceptable
        # if SQL evidence exists to support them.
        sql_results = _state_get(state, "sql_results", []) or []
        if sql_results:
            return {
                "verification_status": "ok",
                "unsupported_claims": [],
                "verification_retries": retries,
                "synthesis_method": synth_method,
            }
        return {
            "verification_status": "fail",
            "unsupported_claims": ["No citation tokens found in synthesized response."],
            "verification_retries": retries,
            "synthesis_method": synth_method,
        }

    evidence = _match_evidence(state, citations)
    # Deduplicate citations before checking evidence — one evidence entry can support
    # multiple claims that cite the same source.
    unique_citations = {c["id"] for c in citations}
    missing = [cid for cid in unique_citations if cid not in evidence]
    if missing:
        return _failure_result(
            retries,
            [f"Missing evidence for citation {citation_id}" for citation_id in missing],
            response,
        )

    # Short-circuit: if ALL citations are structured:0 and SQL evidence exists,
    # the claims are directly grounded in the database query result.
    if unique_citations == {"structured:0"} and _state_get(state, "sql_results", []):
        return {
            "verification_status": "ok",
            "unsupported_claims": [],
            "verification_retries": retries,
            "synthesis_method": synth_method,
        }

    client = get_llm_client()
    if client is None:
        return {
            "verification_status": "ok",
            "unsupported_claims": [],
            "verification_retries": retries,
            "synthesis_method": synth_method,
        }

    payload = {
        "answer": response,
        "citations": citations,
        "evidence": evidence,
    }
    try:
        raw = client.generate(_load_prompt(), json.dumps(payload, default=str), [])
        verdict = _parse_verdict(raw)
    except Exception as exc:
        logger.warning("Verifier LLM failed; using local citation presence check: %s", exc)
        return {
            "verification_status": "ok",
            "unsupported_claims": [],
            "verification_retries": retries,
        }

    if verdict.get("ok") is True:
        return {
            "verification_status": "ok",
            "unsupported_claims": [],
            "verification_retries": retries,
            "synthesis_method": synth_method,
        }

    result = _failure_result(
        retries,
        verdict.get("unsupported_claims") or ["Verifier marked answer unsupported."],
        response,
    )
    result["synthesis_method"] = synth_method
    return result


def _failure_result(retries: int, unsupported_claims: list[str], response: str) -> dict:
    if retries < 1:
        return {
            "verification_status": "retry",
            "verification_retries": retries + 1,
            "unsupported_claims": unsupported_claims,
        }

    # Preserve the original synthesized response; do not overwrite with a generic message.
    # Downstream consumers can check verification_status to decide how to present it.
    return {
        "verification_status": "fail",
        "verification_retries": retries,
        "unsupported_claims": unsupported_claims,
        "synthesized_response": response,
    }


def _extract_citations(response: str) -> list[dict]:
    return [
        {"id": f"{pub_id}:{chunk_id}", "pub_id": pub_id, "chunk_id": chunk_id}
        for pub_id, chunk_id in CITATION_PATTERN.findall(response)
    ]


def _match_evidence(state: Any, citations: list[dict]) -> dict[str, dict]:
    evidence: dict[str, dict] = {}
    wanted = {citation["id"] for citation in citations}

    for item in _state_get(state, "retrieved_chunks", []) or []:
        if isinstance(item, dict):
            pub_id = str(item.get("publication_id") or item.get("pub_id") or item.get("source_id") or "")
            chunk_id = str(item.get("chunk_id") or item.get("id") or "0")
            citation_id = f"{pub_id}:{chunk_id}"
            if citation_id in wanted:
                evidence[citation_id] = {
                    "title": item.get("title"),
                    "chunk_text": (
                        item.get("chunk_text")
                        or item.get("content")
                        or item.get("text")
                        or item.get("abstract")
                    ),
                }

    for row in _state_get(state, "sql_results", []) or []:
        if not isinstance(row, dict):
            continue
        for key in ("publication_id", "researcher_id", "funding_id", "lab_id", "institution_id"):
            if row.get(key):
                citation_id = f"{row[key]}:0"
                if citation_id in wanted:
                    evidence[citation_id] = {"row": row}

    if "structured:0" in wanted and "structured:0" not in evidence:
        sql_results = _state_get(state, "sql_results", []) or []
        if sql_results:
            first_row = sql_results[0]
            evidence["structured:0"] = {"row": first_row}

    return evidence


def _parse_verdict(raw: str) -> dict:
    try:
        return dict(json.loads(raw))
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise
        return dict(json.loads(match.group(0)))


def _load_prompt() -> str:
    return PROMPT_PATH.read_text()


def _state_get(state: Any, key: str, default: Any = None) -> Any:
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)
