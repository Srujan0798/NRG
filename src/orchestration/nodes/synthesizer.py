"""Synthesizer Node - LLM synthesis of retrieved data."""

import logging
import os
import re
from typing import TypedDict
from pathlib import Path

from src.config.llm_config import get_llm_client
from src.config.local_llm import get_local_llm_client
from src.audit import log_llm_call

logger = logging.getLogger(__name__)
SYNTH_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "synth_system.md"
CITATION_PATTERN = re.compile(r"\[cite:([^:\]]+):([^\]]+)\]")

SENSITIVE_KEY_TERMS = (
    "email",
    "phone",
    "mobile",
    "address",
    "full_text",
    "fulltext",
    "full_abstract",
    "abstract",
    "raw_db_dump",
    "secret",
    "api_key",
    "password",
    "private_key",
    "access_token",
    "refresh_token",
)

REDACTION_PATTERNS = (
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\+?\d[\d\s().-]{8,}\d"),
    re.compile(r"\b(?:sk|nvapi|AIza|xox[baprs])-?[A-Za-z0-9._-]{8,}\b", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
)


class SynthesizerState(TypedDict):
    """State passed from synthesizer node."""

    synthesized_response: str
    verification_status: bool


def synthesizer_node(state):
    """Synthesize retrieved data into coherent response."""
    # Extract user query from state object
    if hasattr(state, "user_query"):
        user_query = state.user_query
    elif isinstance(state, dict):
        user_query = state.get("user_query", "")
    else:
        user_query = ""

    # Extract other state values
    if hasattr(state, "sql_results"):
        sql_results = state.sql_results
    elif isinstance(state, dict):
        sql_results = state.get("sql_results", [])
    else:
        sql_results = []

    if hasattr(state, "retrieved_chunks"):
        retrieved_chunks = state.retrieved_chunks
    elif isinstance(state, dict):
        retrieved_chunks = state.get("retrieved_chunks", [])
    else:
        retrieved_chunks = []

    if hasattr(state, "user_tier"):
        user_tier = state.user_tier
    elif isinstance(state, dict):
        user_tier = state.get("user_tier", 1)
    else:
        user_tier = 1

    if hasattr(state, "conversation_history"):
        conversation_history = state.conversation_history
    elif isinstance(state, dict):
        conversation_history = state.get("conversation_history", [])
    else:
        conversation_history = []

    if hasattr(state, "intent"):
        intent = state.intent
    elif isinstance(state, dict):
        intent = state.get("intent", "")
    else:
        intent = ""

    if hasattr(state, "routing_decision"):
        routing_decision = state.routing_decision
    elif isinstance(state, dict):
        routing_decision = state.get("routing_decision", "")
    else:
        routing_decision = ""

    data_sources = []

    if sql_results:
        data_sources.append(f"Structured data: {len(sql_results)} records")

    if retrieved_chunks:
        data_sources.append(f"Unstructured data: {len(retrieved_chunks)} chunks")

    context_summary = _build_context_summary(conversation_history)

    if not data_sources:
        synthesized = _fallback_response(user_query, context_summary)
        verification = False
        provenance = {"synth": "rule_based", "cloud_synthesis_used": False}
    else:
        # Cloud verification is gated the same way as cloud synthesis.
        cloud_allowed = os.getenv("CLOUD_SYNTHESIS_ALLOWED", "false").lower() == "true"
        client = get_llm_client() if cloud_allowed else None
        if client:
            verification_prompt = (
                "Verify this claim against minimized evidence only: "
                f"{_minimise_sql_results(sql_results[:3])}"
            )
            try:
                # Use query as user_prompt for context
                verification_resp = client.generate(verification_prompt, user_query, _coerce_history(context_summary))
                # Audit: log verification LLM call
                try:
                    log_llm_call(
                        "synthesizer",
                        verification_prompt,
                        {
                            "response": verification_resp[:500] if verification_resp else "",
                            "cloud_synthesis_used": False,
                            "mode": "cloud_verification",
                            "evidence_counts": {
                                "sql_rows": len(sql_results),
                                "chunks": len(retrieved_chunks),
                            },
                            "redaction_counts": _redaction_counts(sql_results, retrieved_chunks),
                        },
                        getattr(client, "model", "unknown"),
                    )
                except Exception:
                    logger.warning("Audit log_llm_call failed for verification", exc_info=True)
                if "UNCERTAIN" in verification_resp.upper():
                    return {
                        "synthesized_response": "IITGN AI requires more data to verify.",
                        "verification_status": False,
                        "context_summary": context_summary,
                        "provenance": {
                            "synth": "cloud_verification",
                            "cloud_synthesis_used": False,
                        },
                    }
            except Exception as e:
                logger.warning(f"Verification step failed: {e}")

        synthesized, provenance = _synthesize(
            user_query,
            data_sources,
            sql_results,
            retrieved_chunks,
            user_tier,
            context_summary,
            intent,
            routing_decision,
        )
        verification = True

    return {
        "synthesized_response": synthesized,
        "citations": _extract_citations(synthesized),
        "verification_status": verification,
        "context_summary": context_summary,
        "provenance": provenance,
    }

def _synthesize(
    query: str,
    sources: list,
    sql_results: list,
    chunks: list,
    user_tier: int,
    context_summary: str,
    intent: str = "",
    routing_decision: str = "",
) -> tuple[str, dict]:
    """Synthesize data into response using cloud LLM, local LLM, or rule-based fallback."""
    cloud_allowed = os.getenv("CLOUD_SYNTHESIS_ALLOWED", "false").lower() == "true"

    # Try 1: Cloud LLM, only when explicitly allowed.
    client = get_llm_client() if cloud_allowed else None
    if client:
        system_prompt = _build_system_prompt(
            user_tier=user_tier,
            sources=sources,
            sql_results=sql_results,
            chunks=chunks,
            context_summary=context_summary,
        )
        user_prompt = f"User Query: {query}"
        try:
            logger.info("Using cloud LLM for synthesis")
            response = client.generate(
                system_prompt,
                user_prompt,
                conversation_history=_coerce_history(context_summary),
            )
            # Audit: log cloud LLM synthesis call
            try:
                log_llm_call(
                    "synthesizer",
                    system_prompt[:1000],
                    {
                        "response": response[:500] if response else "",
                        "cloud_synthesis_used": True,
                        "mode": "cloud_synthesis",
                        "evidence_counts": {
                            "sql_rows": len(sql_results),
                            "chunks": len(chunks),
                        },
                        "redaction_counts": _redaction_counts(sql_results, chunks),
                    },
                    getattr(client, "model", "cloud-llm"),
                )
            except Exception:
                logger.warning("Audit log_llm_call failed for cloud LLM", exc_info=True)
            return response, {"synth": "cloud_llm", "cloud_synthesis_used": True}
        except Exception as e:
            logger.warning(f"Cloud LLM failed: {e}, trying local LLM")

# Try 2: Local SLM
    local_client = get_local_llm_client()
    if local_client:
        system_prompt = _build_system_prompt(
            user_tier=user_tier,
            sources=sources,
            sql_results=sql_results,
            chunks=chunks,
            context_summary=context_summary,
        )
        user_prompt = f"User Query: {query}"
        try:
            logger.info("Using local LLM for synthesis")
            response = local_client.generate(
                system_prompt,
                user_prompt,
                conversation_history=_coerce_history(context_summary),
            )
            # Audit: log local LLM synthesis call
            try:
                log_llm_call(
                    "synthesizer",
                    system_prompt[:1000],
                    {"response": response[:500] if response else ""},
                    getattr(local_client, "model", "local-slm"),
                )
            except Exception:
                logger.warning("Audit log_llm_call failed for local LLM", exc_info=True)
            return response, {"synth": "local_llm", "cloud_synthesis_used": False}
        except Exception as e:
            logger.warning(f"Local LLM failed: {e}")

    # Try 3: Rule-based synthesis (always works)
    logger.info("Using rule-based synthesis")
    response = _fallback_synthesis(query, sql_results, chunks, context_summary, intent, routing_decision, user_tier)
    # Audit: log rule-based fallback as an LLM call
    try:
        log_llm_call(
            "synthesizer",
            query,
            {"response": response[:500] if response else ""},
            "rule-based",
        )
    except Exception:
        logger.warning("Audit log_llm_call failed for rule-based synthesis", exc_info=True)
    return response, {"synth": "rule_based", "cloud_synthesis_used": False}


def _build_context_summary(conversation_history: list) -> str:
    if not conversation_history:
        return ""

    recent_turns = conversation_history[-3:]
    return " | ".join(
        f"Q: {turn.get('query', '')} A: {turn.get('response', '')}"
        for turn in recent_turns
    )


def _fallback_response(query: str, context_summary: str) -> str:
    if context_summary:
        return (
            f"No new data found for '{query}'. Prior research context: {context_summary}"
        )
    return f"No data found for your query: '{query}'."


def _build_system_prompt(
    user_tier: int,
    sources: list,
    sql_results: list,
    chunks: list,
    context_summary: str,
) -> str:
    safe_sql_results = _minimise_sql_results(sql_results)
    safe_chunks = _minimise_chunks(chunks)
    base_prompt = (
        SYNTH_PROMPT_PATH.read_text()
        if SYNTH_PROMPT_PATH.exists()
        else "You are the National Research Graph AI."
    )
    return f"""{base_prompt}

Synthesize a response for a Tier {user_tier} user.
Use only the provided data. If no data is provided, say so.
Every factual claim MUST be followed by a citation token [cite:pub_id:chunk_id]
drawn from the provided evidence list. Never fabricate citations.
Prior Session Context: {context_summary or "none"}
Data Sources: {sources}
SQL Evidence: {safe_sql_results}
Document Evidence: {safe_chunks}
"""


def _minimise_sql_results(sql_results: list) -> list:
    """Reduce structured evidence before any LLM prompt is built."""
    safe_rows = []
    for row in sql_results[:10]:
        if not isinstance(row, dict):
            safe_rows.append(_redact_text(str(row))[:300])
            continue
        safe_rows.append(
            {
                key: _redact_text(str(value))[:300]
                for key, value in row.items()
                if not _is_sensitive_key(str(key)) and value is not None
            }
        )
    return safe_rows


def _minimise_chunks(chunks: list) -> list:
    """Send bounded excerpts, never full documents, to synthesis prompts."""
    safe_chunks = []
    for idx, chunk in enumerate(chunks[:5], 1):
        if isinstance(chunk, dict):
            content = chunk.get("chunk_text") or chunk.get("content") or chunk.get("text") or ""
            safe_chunks.append(
                {
                    "chunk_id": chunk.get("chunk_id", f"chunk_{idx}"),
                    "publication_id": chunk.get("publication_id") or chunk.get("source_id"),
                    "title": _redact_text(str(chunk.get("title") or "")),
                    "excerpt": _redact_text(str(content))[:700],
                }
            )
        else:
            safe_chunks.append({"chunk_id": f"chunk_{idx}", "excerpt": _redact_text(str(chunk))[:700]})
    return safe_chunks


def _is_sensitive_key(key: str) -> bool:
    key_lower = key.lower()
    return any(term in key_lower for term in SENSITIVE_KEY_TERMS)


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in REDACTION_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _redaction_counts(sql_results: list, chunks: list) -> dict:
    sensitive_keys = 0
    text_matches = 0

    for row in sql_results[:10]:
        if isinstance(row, dict):
            for key, value in row.items():
                if _is_sensitive_key(str(key)):
                    sensitive_keys += 1
                if value is not None:
                    text_matches += _count_redactions(str(value))
        else:
            text_matches += _count_redactions(str(row))

    for chunk in chunks[:5]:
        if isinstance(chunk, dict):
            for value in chunk.values():
                if value is not None:
                    text_matches += _count_redactions(str(value))
        else:
            text_matches += _count_redactions(str(chunk))

    return {"sensitive_keys": sensitive_keys, "text_matches": text_matches}


def _count_redactions(value: str) -> int:
    return sum(len(pattern.findall(value)) for pattern in REDACTION_PATTERNS)


def _coerce_history(context_summary: str) -> list[dict]:
    if not context_summary:
        return []
    return [{"query": "Prior Session Context", "response": context_summary}]


def _format_sql_results(sql_results: list) -> str:
    """Format SQL results for display in fallback mode."""
    if not sql_results:
        return "No structured data found."

    lines = []
    lines.append(f"Found {len(sql_results)} research records:\n")

    for i, row in enumerate(sql_results[:10], 1):  # Show first 10
        if isinstance(row, dict):
            # Format based on table type
            if 'name' in row:
                lines.append(f"{i}. {row.get('name', 'Unknown')}")
                if 'research_area' in row:
                    lines.append(f"   Research Area: {row.get('research_area')}")
                if 'state' in row:
                    lines.append(f"   State: {row.get('state')}")
                if 'institution_id' in row:
                    lines.append(f"   Institution: {row.get('institution_id')}")
                lines.append("")
            elif 'title' in row:
                lines.append(f"{i}. {row.get('title', 'Unknown')}")
                if 'year' in row:
                    lines.append(f"   Year: {row.get('year')}")
                lines.append("")
            else:
                # Generic formatting
                for key, value in row.items():
                    if value and key not in ['created_at', 'updated_at', 'researcher_id', 'institution_id']:
                        lines.append(f"   {key}: {value}")
                lines.append("")

    if len(sql_results) > 10:
        lines.append(f"... and {len(sql_results) - 10} more records")

    return "\n".join(lines)


def _fallback_synthesis(
    query: str,
    sql_results: list,
    chunks: list,
    context_summary: str,
    intent: str = "",
    routing_decision: str = "",
    user_tier: int = 1,
) -> str:
    """Intelligent fallback that formats data beautifully without LLM.

    Produces structured, readable output that feels like a real research tool.
    """
    lines = []

    lines.append("═" * 60)
    lines.append("  NATIONAL RESEARCH GRAPH — Research Intelligence Report")
    lines.append("═" * 60)
    lines.append("")
    lines.append(f"Query: {query}")
    lines.append("")

    if intent or routing_decision:
        lines.append("┌─ Query Classification")
        if intent:
            lines.append(f"│  Intent: {intent}")
        if routing_decision:
            lines.append(f"│  Routed to: {routing_decision}")
        lines.append("└" + "─" * 40)
        lines.append("")

    if sql_results:
        lines.append(f"┌─ Structured Data Results")
        lines.append(f"│  Found {len(sql_results)} research record{'s' if len(sql_results) != 1 else ''}")
        lines.append("└" + "─" * 40)
        lines.append("")

        if _is_researcher_results(sql_results):
            lines = _format_researcher_table(lines, sql_results, user_tier)
        elif _is_publication_results(sql_results):
            lines = _format_publication_table(lines, sql_results)
        else:
            lines = _format_generic_table(lines, sql_results)

    if chunks and not sql_results:
        lines.append(f"┌─ Document Analysis")
        lines.append(f"│  Found {len(chunks)} relevant excerpt{'s' if len(chunks) != 1 else ''}")
        lines.append("└" + "─" * 40)
        lines.append("")
        lines = _format_chunks(lines, chunks)

    if context_summary:
        lines.append("")
        lines.append(f"┌─ Session Context")
        lines.append(f"│  {context_summary}")
        lines.append("└" + "─" * 40)

    lines.append("")
    lines.append("─" * 60)
    if sql_results or chunks:
        lines.append("  [Fallback Mode: Intelligent formatting without cloud LLM]")
    else:
        lines.append("  No data found for this query.")
    lines.append("─" * 60)

    return "\n".join(lines)


def _is_researcher_results(sql_results: list) -> bool:
    if not sql_results:
        return False
    sample = sql_results[0]
    return isinstance(sample, dict) and (
        "name" in sample or
        ("researcher_id" in sample and "research_area" not in sample)
    )


def _is_publication_results(sql_results: list) -> bool:
    if not sql_results:
        return False
    sample = sql_results[0]
    return isinstance(sample, dict) and "title" in sample


def _format_researcher_table(lines: list, sql_results: list, user_tier: int) -> list:
    lines.append("  RESEARCHERS")
    lines.append("  " + "-" * 56)

    shown = 0
    for i, row in enumerate(sql_results[:20], 1):
        if not isinstance(row, dict):
            continue

        name = row.get("name", "Unknown Researcher")
        area = row.get("research_area", "N/A")
        state = row.get("state", "N/A")
        institution = row.get("institution_id", row.get("institution", "N/A"))
        citation = _citation_for_row(row)

        if shown == 0:
            lines.append(f"  #  {'Name':<30} {'Area':<15} {'Location'}")
            lines.append("  " + "-" * 56)

        lines.append(f"  {i:2}. {name:<30} {area:<15} {state} {citation}")

        if user_tier == 1 and institution != "N/A":
            lines.append(f"      Institution: {institution}")

        if "email" in row and user_tier == 1 and row.get("email"):
            lines.append(f"      Email: {row['email']}")

        shown += 1

    if len(sql_results) > 20:
        lines.append(f"  ... and {len(sql_results) - 20} more researchers")

    lines.append("")
    lines.append(f"  Total: {len(sql_results)} researcher{'s' if len(sql_results) != 1 else ''}")
    return lines


def _format_publication_table(lines: list, sql_results: list) -> list:
    lines.append("  PUBLICATIONS")
    lines.append("  " + "-" * 56)

    for i, row in enumerate(sql_results[:15], 1):
        if not isinstance(row, dict):
            continue

        title = row.get("title", "Unknown Title")
        year = row.get("year", "N/A")
        authors = row.get("authors", row.get("author", "N/A"))
        citation = _citation_for_row(row)

        if len(title) > 50:
            title = title[:47] + "..."

        lines.append(f"  {i}. {title} {citation}")
        lines.append(f"      Year: {year} | Authors: {authors}")

    if len(sql_results) > 15:
        lines.append(f"  ... and {len(sql_results) - 15} more publications")

    lines.append("")
    return lines


def _format_generic_table(lines: list, sql_results: list) -> list:
    for i, row in enumerate(sql_results[:15], 1):
        if not isinstance(row, dict):
            lines.append(f"  {i}. {row}")
            continue

        parts = []
        for key, value in row.items():
            if key in ("created_at", "updated_at", "id", "researcher_id", "institution_id"):
                continue
            if value:
                parts.append(f"{key}: {value}")

        if parts:
            lines.append(f"  {i}. " + " | ".join(parts[:4]) + f" {_citation_for_row(row)}")
        lines.append("")

    if len(sql_results) > 15:
        lines.append(f"  ... and {len(sql_results) - 15} more records")

    return lines


def _format_chunks(lines: list, chunks: list) -> list:
    for i, chunk in enumerate(chunks[:3], 1):
        content = chunk.get("content", chunk) if isinstance(chunk, dict) else chunk
        if len(content) > 200:
            content = content[:197] + "..."
        lines.append(f"  Excerpt {i}:")
        lines.append(f"    {content} {_citation_for_chunk(chunk, i)}")
        lines.append("")

    if len(chunks) > 3:
        lines.append(f"  [+ {len(chunks) - 3} more excerpts available]")
    return lines


def _citation_for_row(row: dict) -> str:
    for key in ("publication_id", "researcher_id", "funding_id", "lab_id", "institution_id"):
        if row.get(key):
            return f"[cite:{row[key]}:0]"
    return "[cite:structured:0]"


def _citation_for_chunk(chunk, index: int) -> str:
    if isinstance(chunk, dict):
        pub_id = chunk.get("publication_id") or chunk.get("pub_id") or chunk.get("source_id") or f"chunk_{index}"
        chunk_id = chunk.get("chunk_id") or chunk.get("id") or str(index)
        return f"[cite:{pub_id}:{chunk_id}]"
    return f"[cite:chunk_{index}:{index}]"


def _extract_citations(response: str) -> list[dict]:
    """Regex-extract [cite:...] tokens and build Citation objects."""
    return [
        {"id": f"{pub_id}:{chunk_id}", "pub_id": pub_id, "chunk_id": chunk_id}
        for pub_id, chunk_id in CITATION_PATTERN.findall(response or "")
    ]
