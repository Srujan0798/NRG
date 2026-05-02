"""Bounded AI synthesis for tier-safe query payloads."""

from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, cast

from src.api.logging_config import get_logger

logger = get_logger(__name__)

_AI_SYNTH_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="nrg-ai-synth")
JSONDict = dict[str, Any]


def _enabled() -> bool:
    if os.getenv("CLOUD_SYNTHESIS_ALLOWED", "false").lower() != "true":
        return False
    return os.getenv("NRG_AI_SYNTHESIZE_FAST_PATHS", "false").lower() == "true"


def _timeout_seconds() -> float:
    try:
        return max(1.0, float(os.getenv("NRG_AI_SYNTHESIS_TIMEOUT_SECONDS", "2")))
    except ValueError:
        return 2.0


def _tier_voice(user_tier: int) -> str:
    if user_tier >= 3:
        return (
            "Industry partner voice. Use anonymized capability language, partnership opportunities, "
            "and no personal identifiers or raw contacts."
        )
    if user_tier == 2:
        return (
            "Government policy voice. Use aggregate cohorts, state or institution trends, policy impact, "
            "and no individual-level personal details."
        )
    return "Researcher voice. Be specific, technical where useful, and preserve source-backed details."


def _safe_json(value: Any, *, limit: int = 6000) -> str:
    text = json.dumps(value, ensure_ascii=False, default=str)
    return text[:limit]


def _list_any(value: Any) -> list[Any]:
    return cast(list[Any], value) if isinstance(value, list) else []


def _build_system_prompt(payload: JSONDict, *, user_tier: int) -> str:
    citations = _list_any(payload.get("citations"))
    sql_results = _list_any(payload.get("sql_results"))
    source_tables = _list_any(payload.get("retrieval_sources"))
    sql_query = payload.get("sql_query") or ""
    confidence = payload.get("answer_confidence") or payload.get("confidence") or "medium"
    return "\n".join(
        [
            "You are the National Research Graph answer engine.",
            "Write the final visible answer using ONLY the tier-safe evidence below.",
            _tier_voice(user_tier),
            "Return exactly four short paragraphs:",
            "1. Headline finding with the most important source-backed numbers.",
            "2. Plain-English explanation of what the data means.",
            "3. Why this matters for this user's tier.",
            "4. Caveats and confidence.",
            "Rules:",
            "- Do not invent numbers, names, emails, phone numbers, IDs, tables, or citations.",
            "- Every number you mention must already appear in the evidence.",
            "- Include citation markers already present in the evidence, such as [cite:table:row].",
            "- If evidence is thin, say so plainly instead of speculating.",
            f"Confidence label to preserve: {confidence}.",
            f"Source tables: {_safe_json(source_tables, limit=1200)}",
            f"SQL query: {sql_query[:1600]}",
            f"Tier-safe rows: {_safe_json(sql_results[:12], limit=5000)}",
            f"Citations: {_safe_json(citations[:12], limit=2200)}",
        ]
    )


def _primary_citation_marker(payload: JSONDict) -> str:
    citations = _list_any(payload.get("citations"))
    if citations:
        first_citation = cast(JSONDict, citations[0]) if isinstance(citations[0], dict) else {}
        citation_id = first_citation.get("id") or first_citation.get("pub_id")
        if citation_id:
            return f"[cite:{citation_id}]"
    sources = _list_any(payload.get("retrieval_sources"))
    if sources:
        return f"[cite:{sources[0]}:aggregate]"
    return "[cite:nrg:evidence]"


def _ensure_cited_numbers(text: str, payload: JSONDict) -> str:
    if not re.search(r"\d", text):
        return text
    if "[cite:" in text or re.search(r"\[\d+\]", text):
        return text
    paragraphs = text.split("\n\n")
    paragraphs[0] = f"{paragraphs[0].rstrip()} {_primary_citation_marker(payload)}"
    return "\n\n".join(paragraphs)


def _with_ai_latency(payload: JSONDict, elapsed_ms: float) -> int:
    try:
        base_ms = float(payload.get("query_time_ms") or 0)
    except (TypeError, ValueError):
        base_ms = 0
    return int(round(max(0.0, base_ms) + elapsed_ms))


def synthesize_payload_with_ai(
    payload: JSONDict,
    *,
    query: str,
    user_tier: int,
) -> JSONDict:
    """Use MiniMax/mesh for visible answer prose after API-tier filtering.

    Deterministic SQL/results remain the source of truth. This function only
    rewrites the human answer and records provenance when the cloud synthesis
    path succeeds.
    """
    if not _enabled():
        return payload

    provenance = dict(payload.get("provenance") or {})
    if provenance.get("cloud_synthesis_used") is True:
        return payload

    if not (payload.get("sql_results") or payload.get("citations") or payload.get("retrieval_sources")):
        return payload

    original_answer = payload.get("final_answer") or payload.get("response") or ""
    system_prompt = _build_system_prompt(payload, user_tier=user_tier)
    user_prompt = f"User question: {query}\n\nCurrent deterministic answer:\n{str(original_answer)[:3000]}"

    started = time.perf_counter()
    try:
        from src.config.llm_config import get_llm_mesh

        mesh = get_llm_mesh()
        future = _AI_SYNTH_EXECUTOR.submit(mesh.generate, system_prompt, user_prompt, [])
        answer = future.result(timeout=_timeout_seconds())
    except TimeoutError:
        logger.warning(f"AI fast-path synthesis timed out after {_timeout_seconds():.1f}s")
        return payload
    except Exception as exc:
        logger.warning(f"AI fast-path synthesis failed; using deterministic answer: {exc}")
        return payload

    answer = re.sub(r"<think>.*?</think>", "", str(answer), flags=re.DOTALL).strip()
    answer = _ensure_cited_numbers(answer, payload)
    if len(answer) < 80:
        logger.warning("AI fast-path synthesis rejected due to weak answer contract")
        return payload

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    provenance.update(
        {
            "synth": "cloud_llm_fast_path",
            "cloud_synthesis_used": True,
            "ai_provider": os.getenv("LLM_PROVIDER", "minimax"),
            "ai_model": os.getenv("MINIMAX_MODEL") or os.getenv("LLM_MODEL") or "minimax",
            "ai_synthesis_latency_ms": elapsed_ms,
            "deterministic_retrieval_preserved": True,
        }
    )

    updated = dict(payload)
    updated["response"] = answer
    updated["final_answer"] = answer
    updated["synthesis_method"] = "cloud_llm_fast_path"
    updated["provenance"] = provenance
    updated["warnings"] = [
        warning
        for warning in updated.get("warnings", [])
        if "deterministic" not in str(warning).lower() and "rule_based" not in str(warning).lower()
    ]
    updated["query_time_ms"] = _with_ai_latency(payload, elapsed_ms)
    updated["ai_provider"] = provenance["ai_provider"]
    updated["ai_model"] = provenance["ai_model"]
    return updated
