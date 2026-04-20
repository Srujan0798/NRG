"""Planner node - schema-only cloud LLM query decomposition."""

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
from src.skills.text_to_sql.sqlite_schema_extractor import SQLiteSchemaExtractor

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "planner_system.md"


class Plan(BaseModel):
    subqueries: list[str] = Field(default_factory=list)
    schema_tables: list[str] = Field(default_factory=list)
    desired_skills: list[str] = Field(default_factory=list)
    expected_output_shape: str = ""


def planner_node(state: Any) -> dict:
    """Build a schema-only execution plan for downstream router/executor."""
    user_query = _state_get(state, "user_query", "")
    conversation_history = _state_get(state, "conversation_history", [])
    user_id = _state_get(state, "user_id", "planner")

    client = _get_planner_client()
    if client is None:
        return {
            "plan": None,
            "planner_metadata": {"mode": "heuristic_fallback", "reason": "llm_unavailable"},
        }

    schema_prompt = _build_schema_prompt(user_query)
    system_prompt = _load_prompt()
    user_prompt = (
        f"{schema_prompt}\n\n"
        f"User Query: {user_query}\n\n"
        "Return the strict JSON plan only."
    )

    try:
        raw = client.generate(system_prompt, user_prompt, conversation_history[-3:])
        plan = _parse_plan(raw)
    except Exception as first_error:
        logger.warning("Planner failed first parse/call: %s", first_error)
        try:
            repair_prompt = (
                "Repair this invalid planner output into strict JSON matching the required schema:\n"
                f"{locals().get('raw', '')}"
            )
            repaired = client.generate(system_prompt, repair_prompt, [])
            plan = _parse_plan(repaired)
        except Exception as repair_error:
            logger.warning("Planner repair failed: %s", repair_error)
            return {
                "plan": None,
                "planner_metadata": {
                    "mode": "heuristic_fallback",
                    "reason": type(repair_error).__name__,
                },
            }

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
