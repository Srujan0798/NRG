"""Synthesizer Node - LLM synthesis of retrieved data."""

import logging
from typing import TypedDict

from src.config.llm_config import get_llm_client
from src.config.local_llm import get_local_llm_client, rule_based_synthesis

logger = logging.getLogger(__name__)


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

    data_sources = []

    if sql_results:
        data_sources.append(f"Structured data: {len(sql_results)} records")

    if retrieved_chunks:
        data_sources.append(f"Unstructured data: {len(retrieved_chunks)} chunks")

    context_summary = _build_context_summary(conversation_history)

    if not data_sources:
        synthesized = _fallback_response(user_query, context_summary)
        verification = False
    else:
        # IITGN Agentic Verification
        client = get_llm_client()
        if client:
            verification_prompt = f"Verify this claim against data: {sql_results[:3]}"
            try:
                # Use query as user_prompt for context
                verification_resp = client.generate(verification_prompt, user_query, _coerce_history(context_summary))
                if "UNCERTAIN" in verification_resp.upper():
                    return {
                        "synthesized_response": "IITGN AI requires more data to verify.",
                        "verification_status": False,
                        "context_summary": context_summary,
                    }
            except Exception as e:
                logger.warning(f"Verification step failed: {e}")

        synthesized = _synthesize(
            user_query,
            data_sources,
            sql_results,
            retrieved_chunks,
            user_tier,
            context_summary,
        )
        verification = True

    return {
        "synthesized_response": synthesized,
        "verification_status": verification,
        "context_summary": context_summary,
    }

def _synthesize(
    query: str,
    sources: list,
    sql_results: list,
    chunks: list,
    user_tier: int,
    context_summary: str,
) -> str:
    """Synthesize data into response using cloud LLM, local LLM, or rule-based fallback."""
    # Try 1: Cloud LLM
    client = get_llm_client()
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
            return client.generate(
                system_prompt,
                user_prompt,
                conversation_history=_coerce_history(context_summary),
            )
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
            return local_client.generate(
                system_prompt,
                user_prompt,
                conversation_history=_coerce_history(context_summary),
            )
        except Exception as e:
            logger.warning(f"Local LLM failed: {e}, using rule-based synthesis")

    # Try 3: Rule-based synthesis (always works)
    logger.info("Using rule-based synthesis")
    return rule_based_synthesis(query, sql_results, chunks, user_tier)


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
    return f"""You are the National Research Graph AI.
Synthesize a response for a Tier {user_tier} user.
Use only the provided data. If no data is provided, say so.
Prior Session Context: {context_summary or "none"}
Data Sources: {sources}
SQL Results: {sql_results}
Document Chunks: {chunks}
"""


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
) -> str:
    """Enhanced fallback that shows actual data when LLM is unavailable."""
    msg = f"**Research Intelligence Result**\n\n"
    msg += f"**Query:** {query}\n\n"

    if sql_results:
        msg += _format_sql_results(sql_results)
    elif chunks:
        msg += f"Found {len(chunks)} document excerpts:\n"
        for i, chunk in enumerate(chunks[:5], 1):
            msg += f"{i}. {chunk[:100]}...\n\n"
    else:
        msg += "No data found for this query.\n\n"
        msg += "Note: The AI synthesis engine is currently in fallback mode. "
        msg += "You are seeing raw database results."

    if context_summary:
        msg += f"\n**Session Context:** {context_summary}"

    return msg
