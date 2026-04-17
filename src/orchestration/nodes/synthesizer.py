"""Synthesizer Node - LLM synthesis of retrieved data."""

import logging
from typing import TypedDict

from src.config.llm_config import get_llm_client

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
    """Synthesize data into response using the configured cloud LLM."""
    client = get_llm_client()
    if client is None:
        return _fallback_synthesis(query, sql_results, chunks, context_summary)

    system_prompt = _build_system_prompt(
        user_tier=user_tier,
        sources=sources,
        sql_results=sql_results,
        chunks=chunks,
        context_summary=context_summary,
    )
    user_prompt = f"User Query: {query}"

    try:
        return client.generate(
            system_prompt,
            user_prompt,
            conversation_history=_coerce_history(context_summary),
        )
    except Exception:
        return _fallback_synthesis(query, sql_results, chunks, context_summary)


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


def _fallback_synthesis(
    query: str,
    sql_results: list,
    chunks: list,
    context_summary: str,
) -> str:
    """Truthful fallback when LLM is unavailable."""
    msg = f"National Research Graph (Service Mode: Fallback)\n\n"
    msg += f"The synthesis engine is currently unavailable. "
    msg += f"However, the following data was retrieved for your query '{query}':\n"
    if sql_results:
        msg += f"- {len(sql_results)} structured research records found.\n"
    if chunks:
        msg += f"- {len(chunks)} document excerpts identified.\n"
    if context_summary:
        msg += f"\nPrior Session Context: {context_summary}"
    
    msg += "\n\nPlease try again later or contact support if the issue persists."
    return msg
