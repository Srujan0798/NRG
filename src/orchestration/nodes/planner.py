"""Planner node - schema-only cloud LLM query decomposition with heuristic fallback."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from src.audit import log_llm_call, log_plan
from src.config.llm_config import get_llm_client
from src.observability.langfuse_tracer import trace_llm_call
from src.skills.text_to_sql.sqlite_schema_extractor import SQLiteSchemaExtractor

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "planner_system.md"

QUERY_DECOMPOSITION_PATTERNS = {
    "structured": [
        r"(list|find|show|get|count|how many|who has|which)",
        r"(researchers?|labs?|funding|publication|grant|institution)",
    ],
    "unstructured": [
        r"(what are|explain|describe|summarize|tell me about)",
        r"(trends?|advances?|latest|current|recent)",
        r"(overview|analysis|insights?)",
    ],
    "hybrid": [
        r"synthesize",
        r"combine.*with",
        r"integrat",
        r"correlat",
        r"both.*and",
    ],
}

SKILL_KEYWORDS = {
    "sql": ["researcher", "lab", "funding", "grant", "publication", "institution", "count", "list", "find", "show"],
    "rag": ["explain", "describe", "trend", "advance", "overview", "analysis", "summarize", "what are", "latest"],
}


class Plan(BaseModel):
    subqueries: list[str] = Field(default_factory=list)
    schema_tables: list[str] = Field(default_factory=list)
    desired_skills: list[str] = Field(default_factory=list)
    expected_output_shape: str = ""


@trace_llm_call("planner")
def planner_node(state: Any) -> dict:
    """Build a schema-only execution plan for downstream router/executor."""
    user_query = _state_get(state, "user_query", "")
    conversation_history = _state_get(state, "conversation_history", [])
    user_id = _state_get(state, "user_id", "planner")

    client = _get_planner_client()
    schema_prompt = _build_schema_prompt(user_query)

    if client is not None:
        system_prompt = _load_prompt()
        user_prompt = (
            f"{schema_prompt}\n\n"
            f"User Query: {user_query}\n\n"
            "Return the strict JSON plan only."
        )

        try:
            raw = client.generate(system_prompt, user_prompt, conversation_history[-3:])
            plan = _parse_plan(raw)
            plan_dict = plan.model_dump()
            try:
                log_plan(user_id, user_query, plan_dict)
                log_llm_call(
                    "planner",
                    user_prompt[:1000],
                    {"plan": plan_dict},
                    _client_model_name(client),
                )
            except Exception:
                logger.warning("Planner audit logging failed", exc_info=True)

            return {
                "plan": plan_dict,
                "planner_metadata": {
                    "mode": "llm",
                    "model": _client_model_name(client),
                },
            }
        except Exception as first_error:
            logger.warning("Planner failed first parse/call: %s", first_error)
            try:
                repair_prompt = (
                    "Repair this invalid planner output into strict JSON matching the required schema:\n"
                    f"{locals().get('raw', '')}"
                )
                repaired = client.generate(system_prompt, repair_prompt, [])
                plan = _parse_plan(repaired)
                plan_dict = plan.model_dump()
                try:
                    log_plan(user_id, user_query, plan_dict)
                except Exception:
                    pass
                return {
                    "plan": plan_dict,
                    "planner_metadata": {
                        "mode": "llm_repaired",
                        "model": _client_model_name(client),
                    },
                }
            except Exception:
                pass

    fallback_plan = _heuristic_decompose(user_query, schema_prompt)
    try:
        log_plan(user_id, user_query, fallback_plan)
    except Exception:
        pass

    return {
        "plan": fallback_plan,
        "planner_metadata": {
            "mode": "heuristic_fallback",
            "reason": "llm_unavailable_or_failed",
        },
    }


def _heuristic_decompose(user_query: str, schema_prompt: str) -> dict:
    """Perform actual heuristic query decomposition when LLM is unavailable.

    Extracts subqueries, relevant tables, desired skills, and expected output shape
    using pattern matching and keyword analysis.
    """
    query_lower = user_query.lower()

    subqueries = _extract_subqueries(query_lower)
    tables = _extract_schema_tables(schema_prompt)
    skills = _determine_skills(query_lower)
    output_shape = _determine_output_shape(query_lower)

    return {
        "subqueries": subqueries,
        "schema_tables": tables,
        "desired_skills": skills,
        "expected_output_shape": output_shape,
    }


def _extract_subqueries(query_lower: str) -> list[str]:
    """Extract potential subqueries from the user query using sentence segmentation."""
    sentences = re.split(r'[?,;]', query_lower)
    subqueries = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) > 10 and not sent.startswith(('list', 'find', 'show', 'what', 'how')):
            subqueries.append(sent)
    if not subqueries:
        subqueries = [query_lower]
    return subqueries


def _extract_schema_tables(schema_prompt: str) -> list[str]:
    """Extract table names from schema prompt."""
    table_pattern = r'(?:table|view):\s*(\w+)'
    tables = re.findall(table_pattern, schema_prompt.lower())
    return list(set(tables)) if tables else []


def _determine_skills(query_lower: str) -> list[str]:
    """Determine which skills are needed based on query keywords."""
    skills = set()

    for skill, keywords in SKILL_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                skills.add(skill)
                break

    if len(skills) == 2 or any(hybrid in query_lower for hybrid in ["synthesize", "combine", "integrate"]):
        return ["sql", "rag"]

    if "sql" in skills and "rag" not in skills:
        if any(word in query_lower for word in ["explain", "describe", "what are"]):
            return ["sql", "rag"]
    elif "rag" in skills and "sql" not in skills:
        if any(word in query_lower for word in ["count", "list", "find", "how many"]):
            return ["sql", "rag"]

    return list(skills) if skills else ["rag"]


def _determine_output_shape(query_lower: str) -> str:
    """Determine expected output shape based on query patterns."""
    if any(x in query_lower for x in ["count", "how many", "number of"]):
        return "numeric_single"
    if any(x in query_lower for x in ["list", "show all", "find all"]):
        return "list_table"
    if any(x in query_lower for x in ["who is", "who are", "name"]):
        return "person_list"
    if any(x in query_lower for x in ["trend", "over time", "history"]):
        return "time_series"
    if any(x in query_lower for x in ["compare", "versus", "vs"]):
        return "comparison"
    return "mixed_summary"


def _build_schema_prompt(user_query: str) -> str:
    extractor = SQLiteSchemaExtractor()
    try:
        tables = extractor.get_relevant_tables(user_query)
        schema = extractor.get_schema_metadata(tables)
        return extractor.generate_llm_prompt(schema)
    finally:
        extractor.close()


def _load_prompt() -> str:
    return PROMPT_PATH.read_text()


def _get_planner_client() -> Any | None:
    provider = os.getenv("LLM_PLANNER_PROVIDER")
    if provider:
        return get_llm_client(provider)

    # Do not let a generic synthesis/provider key accidentally drive planning.
    # Tests may monkeypatch get_llm_client directly; allow that explicit injection.
    if getattr(get_llm_client, "__module__", "") != "src.config.llm_config":
        return get_llm_client()

    return None


def _parse_plan(raw: str) -> Plan:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise
        payload = json.loads(match.group(0))

    try:
        return Plan.model_validate(payload)
    except ValidationError:
        logger.warning("Planner output failed validation: %s", payload)
        raise


def _client_model_name(client: Any) -> str:
    model = getattr(client, "model", None)
    if model:
        return str(model)

    settings = getattr(client, "settings", None)
    settings_model = getattr(settings, "model", None)
    if settings_model:
        return str(settings_model)

    return "unknown"


def _state_get(state: Any, key: str, default: Any = None) -> Any:
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)
