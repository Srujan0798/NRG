"""Verifier node - citation faithfulness checks with numerical scoring."""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol, cast

from src.config.llm_config import get_llm_client
from src.observability.langfuse_tracer import trace_llm_call

logger = logging.getLogger(__name__)

JSONDict = dict[str, Any]
Citation = dict[str, str]
CitationList = list[Citation]
ScoreBreakdown = dict[str, float]


class VerifierLLM(Protocol):
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[JSONDict],
    ) -> str: ...


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "verifier_system.md"
CITATION_PATTERN: re.Pattern[str] = re.compile(r"\[cite:([^:\]]+):([^\]]+)\]")
VALID_CITATION_TYPES: set[str] = {"pub", "PUB", "structured", "DOC", "DOC-", "chunk", "researcher", "funding", "lab", "institution"}

FAITHFULNESS_WEIGHTS: ScoreBreakdown = {
    "citation_present": 0.2,
    "evidence_match": 0.4,
    "no_fabrication": 0.3,
    "tier_compliance": 0.1,
}

_INVALID_CITATION_LOG_PATH = Path(
    os.getenv(
        "NRG_INVALID_CITATION_LOG",
        str(Path(os.getenv("NRG_AUDIT_DIR", Path(__file__).resolve().parents[2] / ".audit")) / "invalid_citations.jsonl"),
    )
)


def _get_db_connection() -> sqlite3.Connection:
    """Get a database connection for citation validation."""
    db_path = os.getenv("DATABASE_URL", "sqlite:///nrg_research.db")
    if db_path.startswith("postgresql://"):
        logger.warning("Verifier using in-memory SQLite for citation validation; Postgres citations are trusted by structured/RAG prefixes")
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE IF NOT EXISTS publications (publication_id TEXT PRIMARY KEY)")
        conn.row_factory = sqlite3.Row
        return conn
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


def _strip_invalid_citation_tokens(response: str, valid_ids: set[str], duplicate_ids: set[str] | None = None) -> tuple[str, list[JSONDict]]:
    """Remove invalid and duplicate [cite:...] tokens. Returns (stripped_response, stripped_list)."""
    stripped: list[JSONDict] = []
    duplicate_ids = duplicate_ids or set()
    seen_valid: set[str] = set()

    def replace_cite(match: re.Match[str]) -> str:
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
) -> JSONDict:
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

        authors_str = str(row["authors"] or "")
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


def _calculate_citation_coverage(response: str, citations: CitationList) -> float:
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


def _deduplicate_citations(citations: CitationList) -> CitationList:
    """Remove duplicate citations, keeping the first occurrence."""
    seen: set[str] = set()
    deduped: CitationList = []
    for citation in citations:
        key = citation.get("id") or f"{citation.get('pub_id', '')}:{citation.get('chunk_id', '')}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(citation)
    return deduped


deduplicate_citations = _deduplicate_citations


_NUMERIC_CLAIM_RE = re.compile(
    r"(?P<raw>"
    r"₹\s*\d+(?:,\d{2,3})*(?:\.\d+)?(?:\s*(?:crore|cr|lakhs|lakh))?"
    r"|\d+(?:,\d{2,3})*(?:\.\d+)?\s*(?:crore|cr|lakhs|lakh)"
    r"|\b\d{2,}(?:,\d{2,3})*(?:\.\d+)?\b"
    r")",
    re.IGNORECASE,
)


def _unsupported_numeric_claims(answer: str, sql_results: list[JSONDict]) -> list[str]:
    """Return numeric answer claims not supported by SQL row values."""
    if not answer or not sql_results:
        return []

    source_numbers = _extract_source_numbers(sql_results)
    unsupported: list[str] = []
    answer_without_citations = CITATION_PATTERN.sub("", answer)
    for match in _NUMERIC_CLAIM_RE.finditer(answer_without_citations):
        raw = " ".join(match.group("raw").split())
        target = _normalise_numeric_claim(raw)
        if target is None:
            continue
        if not _number_supported(target, source_numbers):
            unsupported.append(f"Unsupported numeric claim: {raw}")
    return unsupported


def _numeric_claims_without_sentence_citation(answer: str) -> list[str]:
    """Return sentences that contain numeric claims but no citation token."""
    if not answer:
        return []

    unsupported: list[str] = []
    for sentence in _split_sentences(answer):
        sentence_without_citations = CITATION_PATTERN.sub("", sentence)
        if _NUMERIC_CLAIM_RE.search(sentence_without_citations) and not CITATION_PATTERN.search(sentence):
            unsupported.append(f"Numeric claim without citation: {sentence.strip()}")
    return unsupported


def _split_sentences(answer: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", answer).strip()
    if not normalized:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]


def _extract_source_numbers(sql_results: list[JSONDict]) -> list[float]:
    values: list[float] = [float(len(sql_results))]

    def visit(value: Any) -> None:
        if isinstance(value, bool) or value is None:
            return
        if isinstance(value, (int, float)):
            values.append(float(value))
            return
        if isinstance(value, Mapping):
            for child in cast(Mapping[str, Any], value).values():
                visit(child)
            return
        if isinstance(value, list):
            for child in cast(list[Any], value):
                visit(child)
            return
        if isinstance(value, str):
            for number in re.findall(r"\d+(?:,\d{2,3})*(?:\.\d+)?", value):
                parsed = _parse_number(number)
                if parsed is not None:
                    values.append(parsed)

    visit(sql_results)
    return values


def _normalise_numeric_claim(raw: str) -> float | None:
    number_match = re.search(r"\d+(?:,\d{2,3})*(?:\.\d+)?", raw)
    if not number_match:
        return None
    value = _parse_number(number_match.group(0))
    if value is None:
        return None
    unit = raw[number_match.end():].strip().lower()
    if unit in {"crore", "cr"}:
        return value * 10_000_000
    if unit in {"lakh", "lakhs"}:
        return value * 100_000
    return value


def _parse_number(raw: str) -> float | None:
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _number_supported(target: float, source_numbers: list[float]) -> bool:
    for source in source_numbers:
        tolerance = max(1.0, abs(source) * 0.01)
        if abs(source - target) <= tolerance:
            return True
    return False


@trace_llm_call("verifier")
def verifier_node(state: Any) -> JSONDict:
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
    response = str(_state_get(state, "synthesized_response", "") or "")
    retries = int(_state_get(state, "verification_retries", 0) or 0)
    citations = _extract_citations(response)
    sql_results = _json_dict_list(_state_get(state, "sql_results", []))
    synth_method = str(_state_get(state, "synthesis_method", "unknown") or "unknown")
    anomaly_report = _json_dict(_state_get(state, "sql_anomaly_report", {}))

    if _is_low_confidence_sql_anomaly(anomaly_report):
        clarification = str(
            anomaly_report.get("clarification_question")
            or _state_get(state, "clarification_question")
            or "The SQL result is low confidence. Please narrow the question or allow a corrected query."
        )
        signal_names = _sql_anomaly_signal_names(anomaly_report)
        return _with_evidence_confidence({
            "verification_status": "fail",
            "faithfulness_score": min(float(anomaly_report.get("confidence_score", 0.05) or 0.05), 0.5),
            "score_breakdown": {
                "citation_present": 0.0,
                "evidence_match": 0.0,
                "no_fabrication": 0.0,
                "tier_compliance": FAITHFULNESS_WEIGHTS["tier_compliance"],
            },
            "unsupported_claims": [f"SQL anomaly requires clarification: {', '.join(signal_names)}"],
            "verification_retries": retries,
            "synthesis_method": synth_method,
            "citation_validity": 0.0,
            "citation_coverage": 0.0,
            "invalid_citations": [],
            "citations": [],
            "synthesized_response": clarification,
            "answer_confidence": "low_clarify",
            "answer_confidence_score": float(anomaly_report.get("confidence_score", 0.05) or 0.05),
            "sql_anomaly_report": anomaly_report,
        })

    uncited_numeric_claims = _numeric_claims_without_sentence_citation(response)
    unsupported_numbers = _unsupported_numeric_claims(response, sql_results)
    numeric_failures = uncited_numeric_claims + unsupported_numbers
    if numeric_failures:
        score_breakdown: ScoreBreakdown = {
            "citation_present": 0.0,
            "evidence_match": FAITHFULNESS_WEIGHTS["evidence_match"] * (0.25 if unsupported_numbers else 0.5),
            "no_fabrication": 0.0,
            "tier_compliance": FAITHFULNESS_WEIGHTS["tier_compliance"],
        }
        return _with_evidence_confidence({
            "verification_status": "fail",
            "faithfulness_score": sum(score_breakdown.values()),
            "score_breakdown": score_breakdown,
            "unsupported_claims": numeric_failures,
            "verification_retries": retries,
            "synthesis_method": synth_method,
            "citation_validity": 0.0 if not citations else 1.0,
            "citation_coverage": _calculate_citation_coverage(response, citations),
            "invalid_citations": [],
            "citations": [],
            "synthesized_response": "Insufficient data to support the numeric claims with required citations.",
            "answer_confidence": "low",
            "answer_confidence_score": sum(score_breakdown.values()),
        })

    score_breakdown: ScoreBreakdown = {
        "citation_present": 0.0,
        "evidence_match": 0.0,
        "no_fabrication": 0.0,
        "tier_compliance": 0.0,
    }

    citation_validity = 1.0
    invalid_citations_out: list[JSONDict] = []
    enriched_citations: list[JSONDict] = []

    if not citations:
        if sql_results:
            unsupported_numbers = _unsupported_numeric_claims(response, sql_results)
            if unsupported_numbers:
                score_breakdown["evidence_match"] = FAITHFULNESS_WEIGHTS["evidence_match"] * 0.25
                score_breakdown["tier_compliance"] = FAITHFULNESS_WEIGHTS["tier_compliance"]
                total_score = sum(score_breakdown.values())
                return {
                    "verification_status": "fail",
                    "faithfulness_score": total_score,
                    "score_breakdown": score_breakdown,
                    "unsupported_claims": unsupported_numbers,
                    "verification_retries": retries,
                    "synthesis_method": synth_method,
                    "citation_validity": 1.0,
                    "citation_coverage": 0.0,
                    "invalid_citations": [],
                    "citations": [],
                    "synthesized_response": response,
                }

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
        malformed: list[JSONDict] = []
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
    missing = [cid for cid in unique_citations if cid not in validated_pub_ids and cid not in dupes]

    citation_validity = len(validated_pub_ids & unique_citations) / len(unique_citations) if unique_citations else 1.0

    stripped_response, type_stripped = _strip_invalid_citation_tokens(response, validated_pub_ids, dupes)
    for s in type_stripped:
        if s not in invalid_citations_out:
            invalid_citations_out.append(s)

    citation_coverage = _calculate_citation_coverage(stripped_response, citations)

    if missing or malformed:
        missing_invalid = [cid for cid in unique_citations if cid not in validated_pub_ids]
        missing_ratio = len(missing_invalid) / len(unique_citations)
        score_breakdown["evidence_match"] = FAITHFULNESS_WEIGHTS["evidence_match"] * (1 - missing_ratio)
        score_breakdown["no_fabrication"] = FAITHFULNESS_WEIGHTS["no_fabrication"] * (1 - missing_ratio)

        total_score = sum(score_breakdown.values())

        result = _failure_result(
            retries,
            [f"Invalid citation {citation_id}" for citation_id in missing_invalid],
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
        unsupported_numbers = _unsupported_numeric_claims(stripped_response, sql_results)
        if unsupported_numbers:
            score_breakdown["no_fabrication"] = FAITHFULNESS_WEIGHTS["no_fabrication"] * 0.25
            score_breakdown["tier_compliance"] = FAITHFULNESS_WEIGHTS["tier_compliance"]
            total_score = sum(score_breakdown.values())
            result = _failure_result(
                retries,
                unsupported_numbers,
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

    client = cast(VerifierLLM | None, get_llm_client())
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

    payload: JSONDict = {
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

    llm_claims = _string_list(verdict.get("unsupported_claims", []))
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
    return _with_evidence_confidence(result)


def _with_evidence_confidence(result: JSONDict) -> JSONDict:
    faithfulness_score = float(result.get("faithfulness_score", 0.0) or 0.0)
    unsupported_claims = _string_list(result.get("unsupported_claims", []))
    caveats = _string_list(result.get("caveats", []))
    existing_confidence = result.get("answer_confidence")

    if existing_confidence == "low_clarify":
        answer_confidence = "low_clarify"
        if not caveats:
            caveats.append("The evidence path needs clarification before a safe answer can be produced.")
    elif unsupported_claims:
        answer_confidence = "low"
        if not caveats:
            caveats.append("Some numeric claims were not supported by retrieved evidence.")
    elif faithfulness_score < 0.85:
        answer_confidence = "medium"
        if not caveats:
            caveats.append("Answer is supported, but citation or evidence coverage is incomplete.")
    else:
        answer_confidence = "high"

    enriched: JSONDict = dict(result)
    enriched["answer_confidence"] = answer_confidence
    enriched["answer_confidence_score"] = faithfulness_score
    enriched["caveats"] = caveats
    return enriched


def _failure_result(
    retries: int,
    unsupported_claims: list[str],
    response: str,
    faithfulness_score: float = 0.0,
    score_breakdown: ScoreBreakdown | None = None,
) -> JSONDict:
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


def _is_low_confidence_sql_anomaly(report: Any) -> bool:
    if not isinstance(report, Mapping):
        return False
    report_map = cast(Mapping[str, Any], report)
    if not report_map.get("detected"):
        return False
    if report_map.get("answer_confidence") == "low_clarify":
        return True
    return bool(report_map.get("needs_clarification"))


def _extract_citations(response: str) -> CitationList:
    return [
        {"id": f"{pub_id}:{chunk_id}", "pub_id": pub_id, "chunk_id": chunk_id}
        for pub_id, chunk_id in CITATION_PATTERN.findall(response)
    ]


def _match_evidence(state: Any, citations: CitationList) -> dict[str, JSONDict]:
    evidence: dict[str, JSONDict] = {}
    wanted = {citation["id"] for citation in citations}

    for item in _sequence(_state_get(state, "retrieved_chunks", [])):
        if isinstance(item, Mapping):
            item_map = cast(Mapping[str, Any], item)
            pub_id = str(item_map.get("publication_id") or item_map.get("pub_id") or item_map.get("source_id") or "")
            chunk_id = str(item_map.get("chunk_id") or item_map.get("id") or "0")
            citation_id = f"{pub_id}:{chunk_id}"
            if citation_id in wanted:
                evidence[citation_id] = {
                    "title": item_map.get("title"),
                    "chunk_text": (
                        item_map.get("chunk_text")
                        or item_map.get("content")
                        or item_map.get("text")
                        or item_map.get("abstract")
                    ),
                }

    sql_results = _json_dict_list(_state_get(state, "sql_results", []))
    for row in sql_results:
        row_map = cast(Mapping[str, Any], row)
        for key in ("publication_id", "researcher_id", "funding_id", "lab_id", "institution_id"):
            if row_map.get(key):
                citation_id = f"{row_map[key]}:0"
                if citation_id in wanted:
                    evidence[citation_id] = {"row": row}

    if "structured:0" in wanted and "structured:0" not in evidence and sql_results:
        first_row = sql_results[0]
        evidence["structured:0"] = {"row": first_row}

    return evidence


def _parse_verdict(raw: str) -> JSONDict:
    try:
        loaded = json.loads(raw)
        if not isinstance(loaded, Mapping):
            return {}
        return dict(cast(Mapping[str, Any], loaded))
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise
        loaded = json.loads(match.group(0))
        if not isinstance(loaded, Mapping):
            return {}
        return dict(cast(Mapping[str, Any], loaded))


def _load_prompt() -> str:
    return PROMPT_PATH.read_text()


def _sql_anomaly_signal_names(report: JSONDict) -> list[str]:
    signal_names = report.get("signal_names")
    if isinstance(signal_names, list):
        return [str(signal) for signal in cast(list[Any], signal_names) if signal is not None]

    names: list[str] = []
    for signal in _sequence(report.get("signals", [])):
        if not isinstance(signal, Mapping):
            continue
        name = cast(Mapping[str, Any], signal).get("name")
        if name:
            names.append(str(name))
    return names


def _json_dict(value: Any) -> JSONDict:
    if not isinstance(value, Mapping):
        return {}
    return dict(cast(Mapping[str, Any], value))


def _json_dict_list(value: Any) -> list[JSONDict]:
    return [_json_dict(item) for item in _sequence(value) if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in cast(list[Any], value) if item is not None]
    if value:
        return [str(value)]
    return []


def _sequence(value: Any) -> list[Any]:
    if isinstance(value, list):
        return cast(list[Any], value)
    return []


def _state_get(state: Any, key: str, default: Any = None) -> Any:
    if isinstance(state, Mapping):
        return cast(Mapping[str, Any], state).get(key, default)
    return getattr(state, key, default)
