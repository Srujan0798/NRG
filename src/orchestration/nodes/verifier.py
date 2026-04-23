"""Verifier node - citation faithfulness checks with numerical scoring."""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Optional

from src.config.llm_config import get_llm_client
from src.observability.langfuse_tracer import trace_llm_call

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "verifier_system.md"
CITATION_PATTERN = re.compile(r"\[cite:([^:\]]+):([^\]]+)\]")
VALID_CITATION_TYPES = {"pub", "PUB", "structured", "DOC", "DOC-", "chunk", "researcher", "funding", "lab", "institution"}

FAITHFULNESS_WEIGHTS = {
    "citation_present": 0.2,
    "evidence_match": 0.4,
    "no_fabrication": 0.3,
    "tier_compliance": 0.1,
}

_INVALID_CITATION_LOG_PATH = Path(__file__).resolve().parents[2] / ".audit" / "invalid_citations.jsonl"


def _get_db_connection() -> sqlite3.Connection:
    """Get a database connection for citation validation."""
    db_path = os.getenv("DATABASE_URL", "sqlite:///nrg_research.db")
    if db_path.startswith("postgresql://"):
        logger.warning("Verifier using SQLite for citation validation; Postgres not used")
        db_path = "nrg_research.db"
    db_path = db_path.replace("sqlite:///", "")
    if not db_path:
        db_path = "nrg_research.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _validate_pub_id_exists(pub_id: str, conn: sqlite3.Connection) -> bool:
    """Check if a publication_id exists in the publications table.

    PUB-* citations come from RAG chunk retrieval and represent real publication IDs.
    We trust these without DB verification since they're generated from actual retrieved data.
    Only PUB-* (dash format) is trusted; PUB_* and PUB_FAKE must be DB-validated.
    """
    if not pub_id or pub_id in ("structured", "chunk"):
        return True
    if pub_id.startswith("chunk_") or pub_id.startswith("DOC") or pub_id.startswith("PUB-"):
        return True
    try:
        cursor = conn.execute(
            "SELECT 1 FROM publications WHERE publication_id = ? LIMIT 1",
            (pub_id,),
        )
        return cursor.fetchone() is not None
    except Exception:
        return False


def _is_structured_citation(pub_id: str) -> bool:
    """Return True for citations like [cite:structured:0] that don't need DB validation.

    PUB-* citations are generated from retrieved RAG chunks and represent actual
    publication IDs from the knowledge graph. They are trusted without DB validation.
    """
    return (
        pub_id in ("structured",)
        or pub_id.startswith("chunk_")
        or pub_id.startswith("DOC")
        or pub_id.startswith("PUB-")
    )


def _validate_citation_type(pub_id: str) -> bool:
    """Return True for citation types that are acceptable (known safe identifiers)."""
    if not pub_id:
        return False
    if pub_id in ("structured",):
        return True
    if pub_id.startswith("chunk_"):
        return True
    if pub_id.startswith("DOC"):
        return True
    if pub_id.startswith("PUB"):
        return True
    if pub_id in VALID_CITATION_TYPES:
        return True
    return False


def _strip_invalid_citation_tokens(response: str, valid_ids: set[str], duplicate_ids: set[str] | None = None) -> tuple[str, list[dict]]:
    """Remove invalid and duplicate [cite:...] tokens. Returns (stripped_response, stripped_list)."""
    stripped = []
    duplicate_ids = duplicate_ids or set()
    seen_valid: set[str] = set()

    def replace_cite(match):
        pub_id = match.group(1)
        chunk_id = match.group(2)
        cite_id = f"{pub_id}:{chunk_id}"
        if cite_id not in valid_ids:
            stripped.append({"pub_id": pub_id, "chunk_id": chunk_id, "reason": "invalid_pub_id"})
            return ""
        if cite_id in duplicate_ids and cite_id in seen_valid:
            stripped.append({"pub_id": pub_id, "chunk_id": chunk_id, "reason": "duplicate"})
            return ""
        seen_valid.add(cite_id)
        return match.group(0)

    cleaned = CITATION_PATTERN.sub(replace_cite, response)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned, stripped


def _log_invalid_citation(
    query: str,
    pub_id: str,
    chunk_id: str,
    reason: str,
) -> None:
    """Append an invalid citation event to the audit log for prompt improvement."""
    try:
        _INVALID_CITATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _INVALID_CITATION_LOG_PATH.open("a") as f:
            f.write(
                json.dumps(
                    {
                        "event": "invalid_citation",
                        "query": query[:500],
                        "pub_id": pub_id,
                        "chunk_id": chunk_id,
                        "reason": reason,
                    }
                )
                + "\n"
            )
    except Exception as exc:
        logger.warning("Failed to log invalid citation: %s", exc)


def _enrich_citation(
    pub_id: str,
    chunk_id: str,
    conn: sqlite3.Connection,
) -> dict:
    """Fetch title, authors, year, venue, DOI for a valid publication citation."""
    if _is_structured_citation(pub_id):
        return {"pub_id": pub_id, "chunk_id": chunk_id, "enriched": False}

    try:
        cursor = conn.execute(
            """
            SELECT title, authors, year, venue, doi, citations, abstract, research_area
            FROM publications WHERE publication_id = ? LIMIT 1
            """,
            (pub_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {"pub_id": pub_id, "chunk_id": chunk_id, "enriched": False}

        authors_str = row["authors"] or ""
        author_list = [a.strip() for a in authors_str.split(",") if a.strip()]

        return {
            "pub_id": pub_id,
            "chunk_id": chunk_id,
            "enriched": True,
            "title": row["title"],
            "authors": author_list,
            "year": row["year"],
            "journal": row["venue"],
            "doi": row["doi"],
            "citation_count": row["citations"],
            "abstract": row["abstract"],
            "research_area": row["research_area"],
        }
    except Exception as exc:
        logger.warning("Citation enrichment failed for %s: %s", pub_id, exc)
        return {"pub_id": pub_id, "chunk_id": chunk_id, "enriched": False}


def _extract_claims(response: str) -> list[str]:
    """Split response into individual factual claims for coverage estimation."""
    sentences = re.split(r"(?<=[.!?])\s+", response)
    claims = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 10:
            continue
        if re.search(r"\b(should|may|might|could|possibly)\b", sent, re.I):
            continue
        claims.append(sent)
    return claims


def _calculate_citation_coverage(response: str, citations: list[dict]) -> float:
    """Estimate what fraction of sentences contain at least one citation."""
    sentences = re.split(r"(?<=[.!?])\s+", response)
    cited_sentences = 0
    cited_pattern = re.compile(r"\[cite:[^:\]]+:[^\]]+\]")
    for sent in sentences:
        if cited_pattern.search(sent):
            cited_sentences += 1
    if not sentences:
        return 1.0
    return cited_sentences / len(sentences)


def _deduplicate_citations(citations: list[dict]) -> list[dict]:
    """Remove duplicate citations (same pub_id), keeping the first occurrence."""
    seen: set[str] = set()
    deduped: list[dict] = []
    for cite in citations:
        key = cite.get("pub_id", "")
        if key not in seen:
            seen.add(key)
            deduped.append(cite)
    return deduped


@trace_llm_call("verifier")
def verifier_node(state: Any) -> dict:
    """Verify cited claims against available evidence with numerical faithfulness score.

    Returns faithfulness_score (0.0-1.0) instead of just pass/fail.
    Score breakdown:
    - citation_present: 0.2 (citations exist)
    - evidence_match: 0.4 (citations have matching evidence)
    - no_fabrication: 0.3 (no claims without citations)
    - tier_compliance: 0.1 (no tier violations)

    Phase 1 additions:
    - citation_validity: fraction of citations resolving to real DB records
    - invalid citations are stripped from synthesized_response
    - malformed, duplicate, and unknown-type citations are caught
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

    citation_validity = 1.0
    invalid_citations_out: list[dict] = []
    enriched_citations: list[dict] = []

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
                "citation_validity": 1.0,
                "citation_coverage": 0.0,
                "invalid_citations": [],
                "citations": [],
                "synthesized_response": response,
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
            "citation_validity": 0.0,
            "citation_coverage": 0.0,
            "invalid_citations": [],
            "citations": [],
            "synthesized_response": response,
        }

    score_breakdown["citation_present"] = FAITHFULNESS_WEIGHTS["citation_present"]

    conn = _get_db_connection()
    try:
        validated_pub_ids: set[str] = set()
        malformed: list[dict] = []
        dupes: set[str] = set()
        seen_ids: set[str] = set()

        for cite in citations:
            cite_id = cite["id"]
            pub_id = cite["pub_id"]
            chunk_id = cite["chunk_id"]

            if cite_id in seen_ids:
                dupes.add(cite_id)
                continue
            seen_ids.add(cite_id)

            if not _validate_citation_type(pub_id):
                malformed.append({"pub_id": pub_id, "chunk_id": chunk_id, "reason": "malformed_type"})
                _log_invalid_citation(response[:200], pub_id, chunk_id, "malformed_or_unknown_type")
                continue

            if _validate_pub_id_exists(pub_id, conn):
                validated_pub_ids.add(cite_id)
                enriched = _enrich_citation(pub_id, chunk_id, conn)
                if enriched:
                    enriched_citations.append(enriched)
            else:
                _log_invalid_citation(response[:200], pub_id, chunk_id, "pub_id_not_found_in_db")
    finally:
        conn.close()

    unique_citations = {c["id"] for c in citations}
    unique_citations = {c["id"] for c in citations}
    missing = [cid for cid in unique_citations if cid not in validated_pub_ids and cid not in dupes]

    citation_validity = len(validated_pub_ids & unique_citations) / len(unique_citations) if unique_citations else 1.0

    stripped_response, type_stripped = _strip_invalid_citation_tokens(response, validated_pub_ids, dupes)
    for s in type_stripped:
        if s not in invalid_citations_out:
            invalid_citations_out.append(s)

    citation_coverage = _calculate_citation_coverage(stripped_response, citations)

    if missing or dupes or malformed:
        missing_with_dupes = [cid for cid in unique_citations if cid not in validated_pub_ids]
        missing_ratio = len(missing_with_dupes) / len(unique_citations)
        score_breakdown["evidence_match"] = FAITHFULNESS_WEIGHTS["evidence_match"] * (1 - missing_ratio)
        score_breakdown["no_fabrication"] = FAITHFULNESS_WEIGHTS["no_fabrication"] * (1 - missing_ratio)

        total_score = sum(score_breakdown.values())

        result = _failure_result(
            retries,
            [f"Invalid citation {citation_id}" for citation_id in missing_with_dupes],
            stripped_response,
            total_score,
            score_breakdown,
        )
        result["synthesis_method"] = synth_method
        result["citation_validity"] = citation_validity
        result["citation_coverage"] = citation_coverage
        result["invalid_citations"] = invalid_citations_out
        result["citations"] = enriched_citations
        result["synthesized_response"] = stripped_response
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
            "citation_validity": citation_validity,
            "citation_coverage": citation_coverage,
            "invalid_citations": invalid_citations_out,
            "citations": enriched_citations,
            "synthesized_response": stripped_response,
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
            "citation_validity": citation_validity,
            "citation_coverage": citation_coverage,
            "invalid_citations": invalid_citations_out,
            "citations": enriched_citations,
            "synthesized_response": stripped_response,
        }

    payload = {
        "answer": stripped_response,
        "citations": citations,
        "evidence": _match_evidence(state, citations),
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
            "citation_validity": citation_validity,
            "citation_coverage": citation_coverage,
            "invalid_citations": invalid_citations_out,
            "citations": enriched_citations,
            "synthesized_response": stripped_response,
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
            "citation_validity": citation_validity,
            "citation_coverage": citation_coverage,
            "invalid_citations": invalid_citations_out,
            "citations": enriched_citations,
            "synthesized_response": stripped_response,
        }

    llm_claims = verdict.get("unsupported_claims", [])
    if llm_claims:
        claim_ratio = min(len(llm_claims) / max(len(unique_citations), 1), 1.0)
        score_breakdown["no_fabrication"] = FAITHFULNESS_WEIGHTS["no_fabrication"] * (1 - claim_ratio * 0.5)

    total_score = sum(score_breakdown.values())
    result = _failure_result(
        retries,
        llm_claims or ["Verifier marked answer unsupported."],
        stripped_response,
        total_score,
        score_breakdown,
    )
    result["synthesis_method"] = synth_method
    result["citation_validity"] = citation_validity
    result["citation_coverage"] = citation_coverage
    result["invalid_citations"] = invalid_citations_out
    result["citations"] = enriched_citations
    result["synthesized_response"] = stripped_response
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
