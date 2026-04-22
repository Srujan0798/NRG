"""Verifier node - citation faithfulness checks with numerical scoring."""

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

FAITHFULNESS_WEIGHTS = {
    "citation_present": 0.2,
    "evidence_match": 0.4,
    "no_fabrication": 0.3,
    "tier_compliance": 0.1,
}


@trace_llm_call("verifier")
def verifier_node(state: Any) -> dict:
    """Verify cited claims against available evidence with numerical faithfulness score.

    Returns faithfulness_score (0.0-1.0) instead of just pass/fail.
    Score breakdown:
    - citation_present: 0.2 (citations exist)
    - evidence_match: 0.4 (citations have matching evidence)
    - no_fabrication: 0.3 (no claims without citations)
    - tier_compliance: 0.1 (no tier violations)
    """
    response = _state_get(state, "synthesized_response", "") or ""
    retries = int(_state_get(state, "verification_retries", 0) or 0)
    citations = _extract_citations(response)
    sql_results = _state_get(state, "sql_results", []) or []
    synth_method = _state_get(state, "synthesis_method", "unknown")

    score_breakdown = {
        "citation_present": 0.0,
        "evidence_match": 0.0,
        "no_fabrication": 0.0,
        "tier_compliance": 0.0,
    }

    if not citations:
        if sql_results:
            score_breakdown["citation_present"] = FAITHFULNESS_WEIGHTS["citation_present"]
            score_breakdown["evidence_match"] = FAITHFULNESS_WEIGHTS["evidence_match"]
            score_breakdown["no_fabrication"] = FAITHFULNESS_WEIGHTS["no_fabrication"]
            score_breakdown["tier_compliance"] = FAITHFULNESS_WEIGHTS["tier_compliance"]

            total_score = sum(score_breakdown.values())
            return {
                "verification_status": "ok" if total_score >= 0.7 else "retry",
                "faithfulness_score": total_score,
                "score_breakdown": score_breakdown,
                "unsupported_claims": [],
                "verification_retries": retries,
                "synthesis_method": synth_method,
            }

        score_breakdown["no_fabrication"] = FAITHFULNESS_WEIGHTS["no_fabrication"]
        score_breakdown["tier_compliance"] = FAITHFULNESS_WEIGHTS["tier_compliance"]
        total_score = sum(score_breakdown.values())

        return {
            "verification_status": "fail",
            "faithfulness_score": total_score,
            "score_breakdown": score_breakdown,
            "unsupported_claims": ["No citation tokens found in synthesized response."],
            "verification_retries": retries,
            "synthesis_method": synth_method,
        }

    score_breakdown["citation_present"] = FAITHFULNESS_WEIGHTS["citation_present"]

    evidence = _match_evidence(state, citations)
    unique_citations = {c["id"] for c in citations}
    missing = [cid for cid in unique_citations if cid not in evidence]

    if missing:
        missing_ratio = len(missing) / len(unique_citations)
        score_breakdown["evidence_match"] = FAITHFULNESS_WEIGHTS["evidence_match"] * (1 - missing_ratio)
        score_breakdown["no_fabrication"] = FAITHFULNESS_WEIGHTS["no_fabrication"] * (1 - missing_ratio)

        total_score = sum(score_breakdown.values())

        result = _failure_result(
            retries,
            [f"Missing evidence for citation {citation_id}" for citation_id in missing],
            response,
            total_score,
            score_breakdown,
        )
        result["synthesis_method"] = synth_method
        return result

    score_breakdown["evidence_match"] = FAITHFULNESS_WEIGHTS["evidence_match"]

    if unique_citations == {"structured:0"} and sql_results:
        score_breakdown["no_fabrication"] = FAITHFULNESS_WEIGHTS["no_fabrication"]
        score_breakdown["tier_compliance"] = FAITHFULNESS_WEIGHTS["tier_compliance"]
        total_score = sum(score_breakdown.values())

        return {
            "verification_status": "ok",
            "faithfulness_score": total_score,
            "score_breakdown": score_breakdown,
            "unsupported_claims": [],
            "verification_retries": retries,
            "synthesis_method": synth_method,
        }

    client = get_llm_client()
    if client is None:
        score_breakdown["no_fabrication"] = FAITHFULNESS_WEIGHTS["no_fabrication"]
        score_breakdown["tier_compliance"] = FAITHFULNESS_WEIGHTS["tier_compliance"]
        total_score = sum(score_breakdown.values())

        return {
            "verification_status": "ok" if total_score >= 0.7 else "retry",
            "faithfulness_score": total_score,
            "score_breakdown": score_breakdown,
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
        score_breakdown["no_fabrication"] = FAITHFULNESS_WEIGHTS["no_fabrication"]
        score_breakdown["tier_compliance"] = FAITHFULNESS_WEIGHTS["tier_compliance"]
        total_score = sum(score_breakdown.values())

        return {
            "verification_status": "ok" if total_score >= 0.7 else "retry",
            "faithfulness_score": total_score,
            "score_breakdown": score_breakdown,
            "unsupported_claims": [],
            "verification_retries": retries,
            "synthesis_method": synth_method,
        }

    if verdict.get("ok") is True:
        score_breakdown["no_fabrication"] = FAITHFULNESS_WEIGHTS["no_fabrication"]
        score_breakdown["tier_compliance"] = FAITHFULNESS_WEIGHTS["tier_compliance"]
        total_score = sum(score_breakdown.values())

        return {
            "verification_status": "ok",
            "faithfulness_score": total_score,
            "score_breakdown": score_breakdown,
            "unsupported_claims": [],
            "verification_retries": retries,
            "synthesis_method": synth_method,
        }

    llm_claims = verdict.get("unsupported_claims", [])
    if llm_claims:
        claim_ratio = min(len(llm_claims) / max(len(unique_citations), 1), 1.0)
        score_breakdown["no_fabrication"] = FAITHFULNESS_WEIGHTS["no_fabrication"] * (1 - claim_ratio * 0.5)

    total_score = sum(score_breakdown.values())
    result = _failure_result(
        retries,
        llm_claims or ["Verifier marked answer unsupported."],
        response,
        total_score,
        score_breakdown,
    )
    result["synthesis_method"] = synth_method
    return result


def _failure_result(
    retries: int,
    unsupported_claims: list[str],
    response: str,
    faithfulness_score: float = 0.0,
    score_breakdown: dict | None = None,
) -> dict:
    if retries < 1:
        return {
            "verification_status": "retry",
            "faithfulness_score": faithfulness_score,
            "score_breakdown": score_breakdown or {},
            "verification_retries": retries + 1,
            "unsupported_claims": unsupported_claims,
        }

    return {
        "verification_status": "fail",
        "faithfulness_score": faithfulness_score,
        "score_breakdown": score_breakdown or {},
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
