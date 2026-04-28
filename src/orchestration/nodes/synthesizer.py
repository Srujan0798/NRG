"""Synthesizer Node - LLM synthesis of retrieved data with streaming and token budgeting."""

from __future__ import annotations

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, TypedDict, Generator
from pathlib import Path

from src.config.llm_config import get_llm_mesh
from src.config.local_llm import get_local_llm_client, LlamaCppClient
from src.audit import log_llm_call
from src.observability.langfuse_tracer import trace_llm_call
from src.auth.rbac import get_policy_engine

logger = logging.getLogger(__name__)
SYNTH_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "synth_system.md"
LOCAL_SYNTH_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "synth_system_local.md"
CITATION_PATTERN = re.compile(r"\[cite:([^:\]]+):([^\]]+)\]")
ALTERNATE_CITATION_PATTERN = re.compile(r"\[ref:([^:\]]+):([^\]]+)\]")
PLAIN_PUB_ID_PATTERN = re.compile(r"\b(PUB[-\s]?\d+)\b", re.IGNORECASE)
BRACKETED_CITE_PATTERN = re.compile(r"\[[^\]]*\]")
_LLM_TIMEOUT_EXECUTOR = ThreadPoolExecutor(
    max_workers=max(1, int(os.getenv("SYNTHESIS_LLM_TIMEOUT_WORKERS", "4"))),
    thread_name_prefix="synthesis-timeout",
)

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

TOKEN_BUDGET_CONFIG = {
    "max_input_tokens": 4000,
    "max_output_tokens": 800,
    "warning_threshold": 0.8,
}

_context_window_sizes = {
    "nvidia": 8192,
    "openai": 128000,
    "anthropic": 200000,
    "azure": 128000,
    "gemini": 128000,
    "minimax": 128000,
    "local": 4096,
}


def _synthesis_timeout_seconds() -> float:
    return max(0.001, float(os.getenv("SYNTHESIS_LLM_TIMEOUT_SECONDS", "5.0")))


def _call_llm_with_timeout(label: str, func, *args, **kwargs):
    timeout = _synthesis_timeout_seconds()
    future = _LLM_TIMEOUT_EXECUTOR.submit(func, *args, **kwargs)
    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError as exc:
        future.cancel()
        raise TimeoutError(f"{label} exceeded {timeout:.2f}s synthesis timeout") from exc


class TokenBudget:
    """Track and limit per-query token spend."""

    def __init__(self, max_input: int = 4000, max_output: int = 800):
        self.max_input_tokens = max_input
        self.max_output_tokens = max_output
        self.input_tokens_used = 0
        self.output_tokens_used = 0
        self.total_cost = 0.0
        self.provider = "unknown"
        self.model = "unknown"

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars)."""
        return len(text) // 4

    def check_budget(self, prompt: str, estimated_response_tokens: int = 200) -> tuple[bool, str]:
        """Check if request fits within budget."""
        prompt_tokens = self.estimate_tokens(prompt)

        if prompt_tokens > self.max_input_tokens:
            return False, f"Prompt exceeds budget: {prompt_tokens} > {self.max_input_tokens}"
        if estimated_response_tokens > self.max_output_tokens:
            return False, f"Response exceeds budget: {estimated_response_tokens} > {self.max_output_tokens}"
        return True, "ok"

    def record_usage(self, input_tokens: int, output_tokens: int, cost: float = 0.0):
        """Record actual token usage."""
        self.input_tokens_used = input_tokens
        self.output_tokens_used = output_tokens
        self.total_cost += cost

    def to_dict(self) -> dict:
        return {
            "input_tokens_used": self.input_tokens_used,
            "output_tokens_used": self.output_tokens_used,
            "total_tokens": self.input_tokens_used + self.output_tokens_used,
            "total_cost_usd": self.total_cost,
            "provider": self.provider,
            "model": self.model,
            "budget_remaining": {
                "input": self.max_input_tokens - self.input_tokens_used,
                "output": self.max_output_tokens - self.output_tokens_used,
            },
        }


class ContextWindowManager:
    """Intelligently manage conversation history within context window limits."""

    def __init__(self, max_context_tokens: int = 4096):
        self.max_context_tokens = max_context_tokens
        self.current_tokens = 0

    def estimate_turn_tokens(self, turn: dict) -> int:
        """Estimate tokens for a conversation turn."""
        query_len = len(turn.get("query", "") or "")
        response_len = len(turn.get("response", "") or "")
        return (query_len + response_len) // 4

    def trim_history(self, history: list[dict], system_prompt: str = "", user_query: str = "") -> list[dict]:
        """Intelligently trim conversation history to fit context window."""
        if not history:
            return []

        system_tokens = self.estimate_turn_tokens({"query": "", "response": system_prompt})
        query_tokens = self.estimate_turn_tokens({"query": user_query, "response": ""})

        available = self.max_context_tokens - system_tokens - query_tokens - 500

        trimmed: list[dict] = []
        total_tokens = 0

        for turn in reversed(history):
            turn_tokens = self.estimate_turn_tokens(turn)
            if total_tokens + turn_tokens <= available:
                trimmed.insert(0, turn)
                total_tokens += turn_tokens
            else:
                if len(trimmed) == 0 and turn_tokens < available:
                    trimmed.insert(0, turn)
                break

        if len(trimmed) < len(history):
            logger.info("Context trimmed: %d turns -> %d turns", len(history), len(trimmed))

        return trimmed

    def summarize_old_turns(self, history: list[dict], max_turns: int = 3) -> list[dict]:
        """Summarize older turns while keeping recent ones intact."""
        if len(history) <= max_turns:
            return history

        recent = history[-max_turns:]
        older = history[:-max_turns]

        summary = {
            "query": f"[Summary of {len(older)} earlier turns]",
            "response": _summarize_turns(older) if older else "",
        }

        return [summary] + recent


def _summarize_turns(turns: list[dict]) -> str:
    """Create a brief summary of older turns."""
    if not turns:
        return ""
    topics = []
    for turn in turns:
        q = turn.get("query", "")[:50]
        if q:
            topics.append(q)
    return f"Previously discussed: {'; '.join(topics[:3])}"


class SynthesizerState(TypedDict):
    """State passed from synthesizer node."""

    synthesized_response: str
    verification_status: bool


@trace_llm_call("synthesizer")
def synthesizer_node(state):
    """Synthesize retrieved data into coherent response."""
    if hasattr(state, "user_query"):
        user_query = state.user_query
    elif isinstance(state, dict):
        user_query = state.get("user_query", "")
    else:
        user_query = ""

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

    complexity = "moderate"
    if hasattr(state, "complexity"):
        complexity = getattr(state, "complexity", "moderate")
    elif isinstance(state, dict):
        complexity = state.get("complexity", "moderate")

    if not data_sources:
        synthesized = _fallback_response(user_query, context_summary)
        verification = False
        provenance = {"synth": "rule_based", "cloud_synthesis_used": False}
    else:
        synthesized, provenance = _synthesize(
            user_query,
            data_sources,
            sql_results,
            retrieved_chunks,
            user_tier,
            context_summary,
            intent,
            routing_decision,
            complexity,
        )
        verification = True

    return {
        "synthesized_response": synthesized,
        "citations": _extract_citations(synthesized),
        "verification_status": verification,
        "context_summary": context_summary,
        "provenance": provenance,
        "synthesis_method": provenance.get("synth", "unknown"),
    }


def synthesizer_node_streaming(state) -> Generator[dict, None, dict]:
    """Streaming synthesizer that yields SSE events for progressive response delivery.

    Yields dicts with 'event' and 'data' keys for SSE formatting:
    - event: 'token', 'done', 'error'
    - data: token text, final response, or error message
    """
    if hasattr(state, "user_query"):
        user_query = state.user_query
    elif isinstance(state, dict):
        user_query = state.get("user_query", "")
    else:
        user_query = ""

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
        yield {"event": "done", "data": synthesized}
        return {
            "synthesized_response": synthesized,
            "citations": _extract_citations(synthesized),
            "verification_status": False,
            "context_summary": context_summary,
            "provenance": {"synth": "rule_based", "cloud_synthesis_used": False},
            "synthesis_method": "rule_based",
        }

    budget = TokenBudget(
        max_input=int(TOKEN_BUDGET_CONFIG["max_input_tokens"]),
        max_output=int(TOKEN_BUDGET_CONFIG["max_output_tokens"]),
    )

    context_manager = ContextWindowManager(max_context_tokens=_context_window_sizes.get("openai", 4096))
    trimmed_history = context_manager.trim_history(
        conversation_history,
        system_prompt="synthesis prompt",
        user_query=user_query,
    )

    cloud_allowed = os.getenv("CLOUD_SYNTHESIS_ALLOWED", "false").lower() == "true"
    mesh = get_llm_mesh() if cloud_allowed else None

    streaming_response = ""

    if mesh:
        system_prompt = _build_system_prompt(
            user_tier=user_tier,
            sources=data_sources,
            sql_results=sql_results,
            chunks=retrieved_chunks,
            context_summary=context_summary,
        )

        budget.provider = "sovereign-mesh"
        budget.model = "mesh"

        within_budget, budget_msg = budget.check_budget(system_prompt + user_query)
        if not within_budget:
            logger.warning("Budget exceeded: %s, falling back to local", budget_msg)

        if hasattr(mesh, "generate_streaming"):
            try:
                for token in mesh.generate_streaming(
                    system_prompt,
                    user_query,
                    trimmed_history,
                ):
                    streaming_response += token
                    yield {"event": "token", "data": token}

                yield {"event": "done", "data": streaming_response}
                return {
                    "synthesized_response": streaming_response,
                    "citations": _extract_citations(streaming_response),
                    "verification_status": True,
                    "context_summary": context_summary,
                    "provenance": {"synth": "cloud_llm_streaming", "cloud_synthesis_used": True},
                    "synthesis_method": "cloud_llm_streaming",
                    "token_budget": budget.to_dict(),
                }
            except Exception as e:
                logger.warning("Streaming failed: %s, trying non-streaming", e)

        try:
            response = mesh.generate(
                system_prompt,
                user_query,
                trimmed_history,
            )
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
            streaming_response = response
            yield {"event": "done", "data": response}
            return {
                "synthesized_response": response,
                "citations": _extract_citations(response),
                "verification_status": True,
                "context_summary": context_summary,
                "provenance": {"synth": "cloud_llm", "cloud_synthesis_used": True},
                "synthesis_method": "cloud_llm",
                "token_budget": budget.to_dict(),
            }
        except Exception as e:
            logger.warning("Cloud LLM failed: %s", e)

    local_client = get_local_llm_client()
    if local_client and isinstance(local_client, LlamaCppClient):
        system_prompt = _build_system_prompt(
            user_tier=user_tier,
            sources=data_sources,
            sql_results=sql_results,
            chunks=retrieved_chunks,
            context_summary=context_summary,
            use_local_prompt=True,
        )

        budget.provider = "local"
        budget.model = "llama.cpp"

        try:
            for token in local_client.generate_streaming(
                system_prompt,
                user_query,
                trimmed_history,
            ):
                streaming_response += token
                yield {"event": "token", "data": token}

            yield {"event": "done", "data": streaming_response}
            return {
                "synthesized_response": streaming_response,
                "citations": _extract_citations(streaming_response),
                "verification_status": True,
                "context_summary": context_summary,
                "provenance": {"synth": "local_llm_streaming", "cloud_synthesis_used": False},
                "synthesis_method": "local_llm_streaming",
                "token_budget": budget.to_dict(),
            }
        except Exception as e:
            logger.warning("Local streaming failed: %s", e)

    synthesized = _fallback_synthesis(
        user_query, sql_results, retrieved_chunks, context_summary, intent, routing_decision, user_tier,
        warning="All LLM providers failed (cloud + local). Using rule-based template synthesis.",
    )
    yield {"event": "done", "data": synthesized}
    return {
        "synthesized_response": synthesized,
        "citations": _extract_citations(synthesized),
        "verification_status": True,
        "context_summary": context_summary,
        "provenance": {"synth": "rule_based", "cloud_synthesis_used": False},
        "synthesis_method": "rule_based",
        "token_budget": budget.to_dict(),
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
    complexity: str = "moderate",
) -> tuple[str, dict]:
    """Synthesize data into response using cloud LLM, local LLM, or rule-based fallback.

    Phase 2 cost-aware routing:
    - complexity=trivial → rule-based (no LLM cost)
    - complexity=simple → local SLM (lowest cost)
    - complexity=moderate → cloud LLM standard model
    - complexity=complex/synthesis_heavy → cloud LLM best model, parallel racing top-3

    Returns (response, provenance_dict) where provenance_dict includes:
    - 'synth': synthesis path used
    - 'cloud_synthesis_used': bool
    - 'provider': actual provider used (for CostGuard record_cost)
    - 'block_reason': str if blocked
    """
    import uuid

    if _is_sql_only_fast_path(sql_results, chunks, routing_decision):
        response = _fallback_synthesis(
            query,
            sql_results,
            chunks,
            context_summary,
            intent,
            routing_decision,
            user_tier,
            warning="SQL-only analytical response formatted without LLM to meet latency SLO.",
        )
        try:
            log_llm_call(
                "synthesizer",
                query,
                {"response": response[:500] if response else "", "mode": "sql_only_fast_path"},
                "rule-based-sql-fast-path",
            )
        except Exception:
            pass
        return response, {"synth": "rule_based_sql_fast_path", "cloud_synthesis_used": False}

    from src.config.llm_config import CostGuard

    cost_guard = CostGuard.get_instance()
    persona_map = {1: "researcher", 2: "government", 3: "industry"}
    persona = persona_map.get(user_tier, "researcher")

    system_prompt = _build_system_prompt(
        user_tier=user_tier,
        sources=sources,
        sql_results=sql_results,
        chunks=chunks,
        context_summary=context_summary,
    )
    tokens_in, tokens_out_est = cost_guard.estimate_tokens(query, len(chunks))
    estimated_cost = cost_guard.estimate_cost(
        complexity=complexity,
        provider="minimax",
        tokens_in=tokens_in,
        tokens_out=tokens_out_est,
    )

    allowed, reason = cost_guard.check_budget(user_tier, complexity, estimated_cost)
    if not allowed:
        logger.warning("CostGuard blocked %s query (est=₹%.2f): %s", complexity, estimated_cost, reason)
        return (
            f"[Cost governance: {reason}]",
            {
                "synth": "blocked",
                "cloud_synthesis_used": False,
                "block_reason": reason,
                "provider": None,
                "estimated_cost": estimated_cost,
            },
        )

    cloud_allowed = os.getenv("CLOUD_SYNTHESIS_ALLOWED", "false").lower() == "true"
    actual_provider = None

    if complexity == "trivial":
        logger.info("Complexity=trivial — using rule-based synthesis")
        response = _fallback_synthesis(query, sql_results, chunks, context_summary, intent, routing_decision, user_tier,
            warning="Complexity=trivial — using rule-based template synthesis (no LLM cost).",
        )
        actual_provider = "rule_based"
        try:
            log_llm_call("synthesizer", query, {"response": response[:500] if response else ""}, "rule-based-trivial")
        except Exception:
            pass
        return response, {"synth": "rule_based_trivial", "cloud_synthesis_used": False}

    if complexity == "simple":
        local_client = get_local_llm_client()
        if local_client:
            user_prompt = f"User Query: {query}"
            try:
                logger.info("Complexity=simple — using local SLM for synthesis")
                response = _call_llm_with_timeout(
                    "local simple synthesis",
                    local_client.generate,
                    system_prompt,
                    user_prompt,
                    conversation_history=_coerce_history(context_summary),
                )
                response = response.rstrip() + "\n\n[Response generated using local model for faster service]"
                actual_provider = "local"
                cost_guard.record_cost(
                    query_id=str(uuid.uuid4())[:8],
                    provider=actual_provider,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out_est,
                    cost_inr=0.0,
                    persona=persona,
                    complexity=complexity,
                    route_decision="local_llm_simple",
                )
                try:
                    log_llm_call("synthesizer", system_prompt[:1000], {"response": response[:500] if response else ""}, "local-slm")
                except Exception:
                    pass
                return response, {"synth": "local_llm_simple", "cloud_synthesis_used": False}
            except Exception as e:
                logger.warning(f"Local LLM for simple query failed: {e}")
        cloud_allowed = True

    if cloud_allowed:
        try:
            mesh = get_llm_mesh()
            user_prompt = f"User Query: {query}"
            logger.info(
                "Using SovereignLLMMesh for synthesis "
                "(complexity=%s, %.1fs timeout, health-weighted)",
                complexity,
                _synthesis_timeout_seconds(),
            )
            response = _call_llm_with_timeout(
                "cloud synthesis",
                mesh.generate,
                system_prompt,
                user_prompt,
                conversation_history=_coerce_history(context_summary),
                complexity=complexity,
            )
            response = re.sub(r'<think>.*?', '', response, flags=re.DOTALL).strip()
            actual_provider = "sovereign_mesh"

            tokens_in_actual = len(system_prompt) // 4
            tokens_out_actual = len(response) // 4
            actual_cost = cost_guard.estimate_cost(complexity, "minimax", tokens_in_actual, tokens_out_actual)
            cost_guard.record_cost(
                query_id=str(uuid.uuid4())[:8],
                provider="minimax",
                tokens_in=tokens_in_actual,
                tokens_out=tokens_out_actual,
                cost_inr=actual_cost,
                persona=persona,
                complexity=complexity,
                route_decision="cloud_llm",
            )

            try:
                log_llm_call(
                    "synthesizer",
                    system_prompt[:1000],
                    {
                        "response": response[:500] if response else "",
                        "cloud_synthesis_used": True,
                        "mode": "cloud_synthesis",
                        "complexity": complexity,
                        "cost_inr": actual_cost,
                        "evidence_counts": {"sql_rows": len(sql_results), "chunks": len(chunks)},
                        "redaction_counts": _redaction_counts(sql_results, chunks),
                    },
                    "sovereign-mesh",
                )
            except Exception:
                logger.warning("Audit log_llm_call failed for cloud LLM", exc_info=True)
            return response, {"synth": "cloud_llm", "cloud_synthesis_used": True}
        except Exception as e:
            logger.warning(f"Cloud LLM mesh failed: {e}, trying local LLM")

    local_client = get_local_llm_client()
    if local_client:
        user_prompt = f"User Query: {query}"
        try:
            logger.info("Using local LLM for synthesis")
            response = _call_llm_with_timeout(
                "local synthesis",
                local_client.generate,
                system_prompt,
                user_prompt,
                conversation_history=_coerce_history(context_summary),
            )
            response = response.rstrip() + "\n\n[Note: Response generated using local model for faster service]"
            actual_provider = "local"
            cost_guard.record_cost(
                query_id=str(uuid.uuid4())[:8],
                provider=actual_provider,
                tokens_in=tokens_in,
                tokens_out=tokens_out_est,
                cost_inr=0.0,
                persona=persona,
                complexity=complexity,
                route_decision="local_llm",
            )
            try:
                log_llm_call(
                    "synthesizer",
                    system_prompt[:1000],
                    {"response": response[:500] if response else ""},
                    "local-slm",
                )
            except Exception:
                logger.warning("Audit log_llm_call failed for local LLM", exc_info=True)
            return response, {"synth": "local_llm", "cloud_synthesis_used": False}
        except Exception as e:
            logger.warning(f"Local LLM failed: {e}")

    logger.info("Using rule-based synthesis after cloud and local LLM failures")
    response = _fallback_synthesis(query, sql_results, chunks, context_summary, intent, routing_decision, user_tier,
        warning="Cloud LLM mesh and local llama.cpp both failed. Using rule-based template synthesis.",
    )
    actual_provider = "rule_based"
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


def _is_sql_only_fast_path(sql_results: list, chunks: list, routing_decision: str = "") -> bool:
    """Bypass LLM synthesis when structured evidence already answers the query."""
    if not sql_results:
        return False
    if chunks:
        return False
    return routing_decision in ("", "text_to_sql", "sql")


def _build_context_summary(conversation_history: list) -> str:
    if not conversation_history:
        return ""

    recent_turns = conversation_history[-3:]
    return " | ".join(
        f"Q: {turn.get('query', '')} A: {turn.get('response', '')}"
        for turn in recent_turns
    )


def _fallback_response(query: str, context_summary: str) -> str:
    suggestions = _generate_search_suggestions(query)
    suggestion_text = f"\n\n**Search suggestions:**\n{suggestions}" if suggestions else ""

    if context_summary:
        return (
            f"No new data found for '{query}'. Prior research context: {context_summary}"
            + suggestion_text
        )
    return f"No data found for your query: '{query}'.{suggestion_text}"


def _generate_search_suggestions(query: str) -> str:
    """Generate helpful search suggestions when a query returns no results."""
    import re
    suggestions = []

    terms = re.findall(r'\b[a-z]{3,}\b', query.lower())
    if terms:
        suggestions.append(f"• Try broader terms: {' or '.join(terms[:3])}")
        suggestions.append(f"• Use partial matches: '{terms[0][:4]}*'")
        suggestions.append("• Search by author name or institution")

    suggest_terms = [
        ("machine learning", "deep learning OR neural networks"),
        ("AI", "artificial intelligence OR machine learning"),
        ("cancer", "oncology OR tumor OR chemotherapy"),
        ("climate", "environment OR global warming OR carbon"),
        ("quantum", "computing OR physics OR cryptography"),
    ]

    for q_term, replacement in suggest_terms:
        if q_term.lower() in query.lower():
            suggestions.append(f"• Related: try searching for '{replacement}'")
            break

    if len(query.split()) < 3:
        suggestions.append("• Add more context: include institution, year, or research area")

    return "\n".join(suggestions[:4]) if suggestions else ""


def _format_sql_results(query: str, sql_results: list) -> str:
    """Format SQL results as markdown for structured-query fast-path."""
    if not sql_results:
        return "No matching records found."

    # Single aggregate (COUNT/SUM/AVG) result
    if len(sql_results) == 1 and len(sql_results[0]) == 1:
        key = list(sql_results[0].keys())[0]
        return f"**{key}:** {sql_results[0][key]}"

    # Build markdown table
    headers = list(sql_results[0].keys())
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in sql_results[:50]:  # Cap at 50 rows
        lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")

    if len(sql_results) > 50:
        lines.append(f"\n*... and {len(sql_results) - 50} more rows*")

    return "\n".join(lines)


def _build_system_prompt(
    user_tier: int,
    sources: list,
    sql_results: list,
    chunks: list,
    context_summary: str,
    use_local_prompt: bool = False,
    user_policy: Any = None,
) -> str:
    safe_sql_results = _minimise_sql_results(sql_results)
    safe_chunks = _minimise_chunks(chunks)

    if use_local_prompt and LOCAL_SYNTH_PROMPT_PATH.exists():
        base_prompt = LOCAL_SYNTH_PROMPT_PATH.read_text()
    else:
        base_prompt = (
            SYNTH_PROMPT_PATH.read_text()
            if SYNTH_PROMPT_PATH.exists()
            else "You are the National Research Graph AI."
        )

    output_format = "full"
    policy_note = f"Tier {user_tier}"
    if user_policy is None:
        engine = get_policy_engine()
        try:
            user_policy = engine.get_policy(tier=user_tier)
        except KeyError:
            user_policy = None

    if user_policy is not None:
        output_format = user_policy.output_format
        policy_note = f"Persona: {user_policy.name} (tier {user_policy.tier})"

    format_instruction = ""
    if output_format == "aggregated":
        format_instruction = (
            "OUTPUT FORMAT: Aggregate results into counts, sums, averages. "
            "Do NOT return individual-level records. Summarize findings statistically."
        )
    elif output_format == "anonymized":
        format_instruction = (
            "OUTPUT FORMAT: Anonymized summaries only. No individual names, emails, "
            "or PII. Return only aggregated or anonymized insights."
        )
    else:
        format_instruction = "OUTPUT FORMAT: Full detail with appropriate citations."

    return f"""{base_prompt}

Synthesize a response for a {policy_note} user.
{_tier_voice_instruction(user_tier)}
Use only the provided data. If no data is provided, say so.
Every factual claim MUST be followed by a citation token [cite:pub_id:chunk_id]
drawn from the provided evidence list. Never fabricate citations.
Every sentence containing a number MUST include a citation marker mapped to the retrieved SQL row or document evidence.

{format_instruction}
{_answer_quality_contract()}

IMPORTANT:
- When SQL Evidence contains aggregate results (e.g., {{"count": 625}}), that IS the direct answer. State it clearly.
- For SQL-only results with no specific row ID, use citation [cite:structured:0].
- For document excerpts, use the citation shown in the Document Evidence (e.g., [cite:DOC-00123:0]).

Prior Session Context: {context_summary or "none"}
Data Sources: {sources}
SQL Evidence: {safe_sql_results}
Document Evidence: {safe_chunks}
"""


def _tier_voice_instruction(user_tier: int) -> str:
    """Return tier-specific answer voice guidance for synthesis prompts."""
    if user_tier == 1:
        return "Tier voice: You are advising a senior researcher; be technical and precise."
    if user_tier == 2:
        return (
            "Tier voice: You are advising a ministry official; be policy-framed, cite cohort "
            "sizes and aggregated trends, and never surface individuals."
        )
    if user_tier == 3:
        return (
            "Tier voice: You are advising an industry partner under NDA; surface partnership "
            "opportunities and anonymized capability maps, and never include PII."
        )
    return "Tier voice: Use a concise evidence-first research briefing voice."


def _answer_quality_contract() -> str:
    return """Return a 4-paragraph answer:
(a) headline number/finding,
(b) explanation in plain English with no jargon,
(c) why it matters to the user's tier,
(d) caveats and source confidence.
If the evidence cannot support a numeric claim, say "Insufficient data" instead of estimating."""


def _minimise_sql_results(sql_results: list) -> list:
    """Reduce structured evidence before any LLM prompt is built."""
    safe_rows: list[Any] = []
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


def _fallback_synthesis(
    query: str,
    sql_results: list,
    chunks: list,
    context_summary: str,
    intent: str = "",
    routing_decision: str = "",
    user_tier: int = 1,
    warning: str = "",
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

    if warning:
        lines.append("┌─ ⚠️  AI Synthesis Unavailable")
        lines.append(f"│  {warning}")
        lines.append("└" + "─" * 40)
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
        lines.append("┌─ Structured Data Results")
        lines.append(f"│  Found {len(sql_results)} research record{'s' if len(sql_results) != 1 else ''} [cite:structured:0]")
        lines.append("└" + "─" * 40)
        lines.append("")

        if _is_researcher_results(sql_results):
            lines = _format_researcher_table(lines, sql_results, user_tier)
        elif _is_publication_results(sql_results):
            lines = _format_publication_table(lines, sql_results)
        else:
            lines = _format_generic_table(lines, sql_results)

    if chunks:
        section_title = "Supplementary Document Analysis" if sql_results else "Document Analysis"
        lines.append(f"┌─ {section_title}")
        lines.append(f"│  Found {len(chunks)} relevant excerpt{'s' if len(chunks) != 1 else ''} [cite:structured:0]")
        lines.append("└" + "─" * 40)
        lines.append("")
        lines = _format_chunks(lines, chunks)

    if context_summary:
        lines.append("")
        lines.append("┌─ Session Context")
        lines.append(f"│  {context_summary}")
        lines.append("└" + "─" * 40)

    lines.append("")
    lines.append("─" * 60)
    if sql_results or chunks:
        lines.append("  [Note: Structured summary — AI synthesis temporarily unavailable] [cite:structured:0]")
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
    engine = get_policy_engine()
    try:
        policy = engine.get_policy(tier=user_tier)
    except KeyError:
        policy = None

    output_format = policy.output_format if policy else "full"
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

        if output_format == "anonymized":
            lines.append(f"  {i:2}. [REDACTED] {area:<15} {state}")
        else:
            lines.append(f"  {i:2}. {name:<30} {area:<15} {state} {citation}")

            if output_format == "full" and institution != "N/A":
                lines.append(f"      Institution: {institution}")

            if output_format == "full" and "email" in row and row.get("email"):
                lines.append(f"      Email: {row['email']}")

        shown += 1

    if len(sql_results) > 20:
        lines.append(f"  ... and {len(sql_results) - 20} more researchers [cite:structured:0]")

    lines.append("")
    lines.append(f"  Total: {len(sql_results)} researcher{'s' if len(sql_results) != 1 else ''} [cite:structured:0]")
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
        lines.append(f"  ... and {len(sql_results) - 15} more publications [cite:structured:0]")

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
        lines.append(f"  ... and {len(sql_results) - 15} more records [cite:structured:0]")

    return lines


def _format_chunks(lines: list, chunks: list) -> list:
    for i, chunk in enumerate(chunks[:3], 1):
        if isinstance(chunk, dict):
            content = chunk.get("content") or chunk.get("excerpt") or chunk.get("chunk_text") or ""
        else:
            content = str(chunk) if chunk else ""
        if len(content) > 200:
            content = content[:197] + "..."
        lines.append(f"  Excerpt {i}:")
        lines.append(f"    {content} {_citation_for_chunk(chunk, i)}")
        lines.append("")

    if len(chunks) > 3:
        lines.append(f"  [+ {len(chunks) - 3} more excerpts available] [cite:structured:0]")
    return lines


def _citation_for_row(row: dict) -> str:
    for key in ("publication_id", "funding_id"):
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
    """Regex-extract [cite:...], [ref:...], and plain PUB-ID tokens (not inside brackets)."""
    citations: list[dict] = []
    seen_ids: set[str] = set()

    for pub_id, chunk_id in CITATION_PATTERN.findall(response or ""):
        cite_id = f"{pub_id}:{chunk_id}"
        if cite_id not in seen_ids:
            seen_ids.add(cite_id)
            citations.append({"id": cite_id, "pub_id": pub_id, "chunk_id": chunk_id})

    for pub_id, chunk_id in ALTERNATE_CITATION_PATTERN.findall(response or ""):
        cite_id = f"{pub_id}:{chunk_id}"
        if cite_id not in seen_ids:
            seen_ids.add(cite_id)
            citations.append({"id": cite_id, "pub_id": pub_id, "chunk_id": chunk_id})

    text_without_brackets = BRACKETED_CITE_PATTERN.sub(" ", response or "")
    for match in PLAIN_PUB_ID_PATTERN.finditer(text_without_brackets):
        pub_id = match.group(1).replace(" ", "-").upper()
        cite_id = f"{pub_id}:0"
        if cite_id not in seen_ids:
            seen_ids.add(cite_id)
            citations.append({"id": cite_id, "pub_id": pub_id, "chunk_id": "0"})

    return citations


def build_adaptive_system_prompt(
    user_tier: int,
    sources: list,
    sql_results: list,
    chunks: list,
    context_summary: str,
    provider: str = "unknown",
    model: str = "unknown",
    user_policy: Any = None,
) -> str:
    """Build an adaptive system prompt based on the target LLM's context window.

    Smaller context models (local LLMs) get condensed prompts with less evidence
    and more direct instructions. Larger context models get full prompts.

    Uses RBAC policy output_format when available for persona-specific guidance.
    """
    context_size = _context_window_sizes.get(provider.lower(), 4096)

    safe_sql_results = _minimise_sql_results(sql_results)
    safe_chunks = _minimise_chunks(chunks)

    if context_size <= 4096:
        return _build_condensed_prompt(user_tier, sources, safe_sql_results, safe_chunks, context_summary, user_policy=user_policy)
    elif context_size <= 8192:
        return _build_standard_prompt(user_tier, sources, safe_sql_results, safe_chunks, context_summary, user_policy=user_policy)
    else:
        return _build_full_prompt(user_tier, sources, safe_sql_results, safe_chunks, context_summary, user_policy=user_policy)


def _build_condensed_prompt(
    user_tier: int,
    sources: list,
    sql_results: list,
    chunks: list,
    context_summary: str,
    user_policy: Any = None,
) -> str:
    """Condensed prompt for small context local LLMs (4K tokens or less)."""
    safe_sql = sql_results[:5] if sql_results else []
    safe_chunks = chunks[:3] if chunks else []

    sql_str = str(safe_sql)[:500] if safe_sql else "None"
    chunk_str = str(safe_chunks)[:500] if safe_chunks else "None"

    if user_policy is None:
        engine = get_policy_engine()
        try:
            user_policy = engine.get_policy(tier=user_tier)
        except KeyError:
            user_policy = None

    policy_note = f"Tier {user_tier}"
    format_note = ""
    if user_policy is not None:
        policy_note = f"Persona: {user_policy.name}"
        if user_policy.output_format == "anonymized":
            format_note = "- OUTPUT: Anonymized summaries only. No individual names or PII."
        elif user_policy.output_format == "aggregated":
            format_note = "- OUTPUT: Aggregate stats only. No individual records."

    return f"""You are NRG AI. Answer user queries using ONLY the provided data.
{_tier_voice_instruction(user_tier)}
If data is insufficient, say so. Cite sources as [cite:id:chunk].

Rules:
- Keep response under 200 words
- Return a 4-paragraph answer: (a) headline number/finding, (b) plain-English explanation, (c) why it matters to the user's tier, (d) caveats and source confidence
- Cite EVERY factual claim: [cite:pub_id:chunk_id] or [cite:structured:0]
- Every sentence containing a number MUST include a citation marker mapped to retrieved evidence
{format_note}

Data Sources: {sources}
SQL Data: {sql_str}
Document Data: {chunk_str}
Context: {context_summary or 'none'}
{policy_note}
"""


def _build_standard_prompt(
    user_tier: int,
    sources: list,
    sql_results: list,
    chunks: list,
    context_summary: str,
    user_policy: Any = None,
) -> str:
    """Standard prompt for medium context models (8K tokens)."""
    safe_sql = sql_results[:8] if sql_results else []
    safe_chunks = chunks[:4] if chunks else []

    if user_policy is None:
        engine = get_policy_engine()
        try:
            user_policy = engine.get_policy(tier=user_tier)
        except KeyError:
            user_policy = None

    policy_note = f"Tier {user_tier}"
    format_note = ""
    if user_policy is not None:
        policy_note = f"Persona: {user_policy.name} (tier {user_policy.tier})"
        if user_policy.output_format == "anonymized":
            format_note = "\n- OUTPUT: Anonymized summaries only. No individual names, emails, or PII."
        elif user_policy.output_format == "aggregated":
            format_note = "\n- OUTPUT: Aggregate stats only. No individual-level records."

    return f"""You are the National Research Graph AI. Answer research queries using ONLY the provided evidence.
{_tier_voice_instruction(user_tier)}

IMPORTANT RULES:
- Every factual claim MUST be cited: [cite:pub_id:chunk_id] or [cite:structured:0]
- Every sentence containing a number MUST include a citation marker mapped to retrieved evidence
- Never fabricate or extrapolate beyond the evidence
- If evidence is insufficient, clearly state limitations
- SQL aggregate results (count, sum) ARE direct answers - state them clearly
{format_note}

Response format:
Return a 4-paragraph answer:
(a) headline number/finding,
(b) explanation in plain English with no jargon,
(c) why it matters to the user's tier,
(d) caveats and source confidence.
Use tables only when they make structured comparisons clearer.

{policy_note} access level applied.

Data Sources: {sources}
Evidence (SQL): {safe_sql}
Evidence (Documents): {safe_chunks}
Session Context: {context_summary or 'none'}
"""


def _build_full_prompt(
    user_tier: int,
    sources: list,
    sql_results: list,
    chunks: list,
    context_summary: str,
    user_policy: Any = None,
) -> str:
    """Full prompt for large context models (128K+ tokens)."""
    if user_policy is None:
        engine = get_policy_engine()
        try:
            user_policy = engine.get_policy(tier=user_tier)
        except KeyError:
            user_policy = None

    policy_note = f"Tier {user_tier}"
    format_instruction = ""
    if user_policy is not None:
        policy_note = f"Persona: {user_policy.name} (tier {user_policy.tier})"
        if user_policy.output_format == "anonymized":
            format_instruction = (
                "\nOUTPUT FORMAT: Anonymized summaries only. "
                "No individual names, emails, or PII. Return aggregated or anonymized insights only."
            )
        elif user_policy.output_format == "aggregated":
            format_instruction = (
                "\nOUTPUT FORMAT: Aggregate stats only. "
                "Do NOT return individual-level records. Summarize findings statistically."
            )
        else:
            format_instruction = "\nOUTPUT FORMAT: Full detail with appropriate citations."

    if LOCAL_SYNTH_PROMPT_PATH.exists():
        base_prompt = LOCAL_SYNTH_PROMPT_PATH.read_text()
    else:
        base_prompt = SYNTH_PROMPT_PATH.read_text() if SYNTH_PROMPT_PATH.exists() else "You are the National Research Graph AI."

    return f"""{base_prompt}

Synthesize a response for a {policy_note} user.
{_tier_voice_instruction(user_tier)}
Use only the provided data. If no data is provided, say so.
Every factual claim MUST be followed by a citation token [cite:pub_id:chunk_id]
drawn from the provided evidence list. Never fabricate citations.
Every sentence containing a number MUST include a citation marker mapped to retrieved evidence.
{_answer_quality_contract()}

IMPORTANT:
- When SQL Evidence contains aggregate results (e.g., {{"count": 625}}), that IS the direct answer. State it clearly.
- For SQL-only results with no specific row ID, use citation [cite:structured:0].
- For document excerpts, use the citation shown in the Document Evidence (e.g., [cite:DOC-00123:0]).
{format_instruction}

Prior Session Context: {context_summary or "none"}
Data Sources: {sources}
SQL Evidence: {sql_results}
Document Evidence: {chunks}
"""
