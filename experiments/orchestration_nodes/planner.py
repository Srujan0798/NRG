"""Planner Node - LLM-based query planning with schema awareness."""

import json
import logging
import re
from typing import TypedDict, Optional, Any
from pydantic import BaseModel, Field
from src.config.llm_config import get_llm_client
from src.audit import log_plan

logger = logging.getLogger(__name__)


class Plan(BaseModel):
    """Planner output: structured query decomposition."""
    intent: str = Field(description="One of: factual_lookup, semantic_search, relational, compound, out_of_scope")
    subqueries: list[str] = Field(description="Decomposed sub-queries")
    schema_tables: list[str] = Field(description="Tables needed: researchers, publications, labs, funding_records, etc.")
    desired_skills: list[str] = Field(description="Skills to dispatch: text_to_sql, rag, kg")
    output_shape: str = Field(description="Expected response format")
    reasoning: str = Field(description="Brief reasoning for routing decision")


class PlannerState(TypedDict):
    """State passed from planner node."""
    intent: str
    routing_decision: Optional[str]
    plan: Optional[dict]
    context_summary: Optional[str]


SCHEMA_PROMPT = """You are a research query planner for the National Research Graph (NRG) platform.

DATABASE SCHEMA:
- researchers(researcher_id, name, email, orcid, institution_id, research_area, state, year_joined, access_tier)
- institutions(institution_id, name, type, state, city, established)
- publications(publication_id, title, venue, year, doi, abstract, access_tier)
- labs(lab_id, name, institution_id, focus_area, pi_researcher_id)
- funding_record(funding_id, agency, amount_inr, start_date, end_date, researcher_id, title)
- researcher_publications(researcher_id, publication_id, author_position, corresponding_author)
- researcher_labs(researcher_id, lab_id, role)
- publication_keywords(publication_id, keyword_id)
- keywords(keyword_id, term, kind)

TIER ACCESS:
- Tier 1 (researcher): Full access to public data + own private data
- Tier 2 (government): Aggregated views only, no individual-level private data
- Tier 3 (industry): Licensed data only, no individual contacts

IMPORTANT RULES:
1. NEVER include raw publication full_text in plan
2. Only schema metadata goes to cloud LLM planners
3. Cloud synthesis, if enabled elsewhere, must use minimized sanitized evidence only
4. Respond ONLY with valid JSON matching the schema

Output JSON format:
{
  "intent": "factual_lookup|semantic_search|relational|compound|out_of_scope",
  "subqueries": ["sub-query 1", "sub-query 2"],
  "schema_tables": ["table1", "table2"],
  "desired_skills": ["text_to_sql", "rag", "kg"],
  "output_shape": "list|table|summary|graph",
  "reasoning": "brief explanation"
}
"""


def _extract_json_from_response(text: str) -> Optional[dict]:
    """Extract JSON from planner response, handling common formats."""
    text = text.strip()

    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract from markdown code blocks
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object anywhere in text
    json_match = re.search(r"\{[^{}]*\}", text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Try brace matching for nested JSON
    start = text.find("{")
    if start != -1:
        depth = 0
        end = start
        for i, c in enumerate(text[start:], start):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

    return None


def _fallback_plan(query: str) -> dict:
    """Fallback rule-based planning when LLM is unavailable."""
    query_lower = query.lower()

    # Check for out-of-scope patterns
    out_of_scope = any(pattern in query_lower for pattern in [
        "generate", "create new", "insert", "update", "delete",
        "drop table", "exec ", "system ", "admin"
    ])
    if out_of_scope:
        return {
            "intent": "out_of_scope",
            "subqueries": [],
            "schema_tables": [],
            "desired_skills": [],
            "output_shape": "error",
            "reasoning": "Query violates安全 boundaries"
        }

    # Intent detection
    if any(w in query_lower for w in ["who", "list", "find", "show", "count", "how many"]):
        intent = "factual_lookup"
        desired_skills = ["text_to_sql"]
    elif any(w in query_lower for w in ["paper", "publication", "research about", "similar to"]):
        intent = "semantic_search"
        desired_skills = ["rag"]
    elif any(w in query_lower for w in ["collaborat", "co-author", "path", "connection"]):
        intent = "relational"
        desired_skills = ["text_to_sql", "kg"]
    else:
        intent = "compound"
        desired_skills = ["text_to_sql", "rag"]

    # Schema table detection
    tables = []
    if any(w in query_lower for w in ["researcher", "author", "scientist"]):
        tables.append("researchers")
    if any(w in query_lower for w in ["publication", "paper", "venue", "journal"]):
        tables.append("publications")
    if any(w in query_lower for w in ["lab", "laboratory"]):
        tables.append("labs")
    if any(w in query_lower for w in ["funding", "grant", "budget"]):
        tables.append("funding_records")

    return {
        "intent": intent,
        "subqueries": [query],
        "schema_tables": tables or ["researchers"],
        "desired_skills": desired_skills,
        "output_shape": "list",
        "reasoning": "Fallback rule-based plan"
    }


def planner_node(state) -> dict:
    """Plan query decomposition using LLM with schema awareness."""
    # Extract user query
    if hasattr(state, "user_query"):
        user_query = state.user_query
    elif isinstance(state, dict):
        user_query = state.get("user_query", "")
    else:
        user_query = ""

    if hasattr(state, "conversation_history"):
        conversation_history = state.conversation_history
    elif isinstance(state, dict):
        conversation_history = state.get("conversation_history", [])
    else:
        conversation_history = []

    if hasattr(state, "user_tier"):
        user_tier = state.user_tier
    elif isinstance(state, dict):
        user_tier = state.get("user_tier", 1)
    else:
        user_tier = 1

    # Build conversation context for prompt
    history_context = ""
    if conversation_history:
        turns = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
        history_context = "\n\nPrevious conversation:\n"
        for turn in turns:
            history_context += f"User: {turn.get('query', '')}\n"
            history_context += f"Assistant: {turn.get('response', '')[:200]}...\n"

    # Build full prompt
    full_prompt = f"""Query: {user_query}
Tier: {user_tier}
{history_context}

Produce a valid JSON plan:"""

    # Try to get LLM client
    llm_client = get_llm_client()
    plan_data = None

    if llm_client:
        try:
            response = llm_client.generate(
                system_prompt=SCHEMA_PROMPT,
                user_prompt=full_prompt,
                conversation_history=[]
            )
            plan_data = _extract_json_from_response(response)

            if plan_data:
                # Validate required fields
                required_fields = ["intent", "subqueries", "schema_tables", "desired_skills"]
                if not all(field in plan_data for field in required_fields):
                    logger.warning("Planner response missing required fields, using fallback")
                    plan_data = None
                else:
                    # Ensure desired_skills is a list
                    if isinstance(plan_data.get("desired_skills"), str):
                        plan_data["desired_skills"] = [plan_data["desired_skills"]]

        except Exception as exc:
            logger.warning("Planner LLM call failed: %s, using fallback", exc)

    # Fallback to rule-based planning
    if not plan_data:
        plan_data = _fallback_plan(user_query)

    # Build routing decision string
    skills = plan_data.get("desired_skills", [])
    routing_decision = "+".join(skills) if skills else "text_to_sql"

    # Add context summary
    context_summary = f"Intent: {plan_data.get('intent')}, Tables: {', '.join(plan_data.get('schema_tables', []))}"

    result = {
        "intent": plan_data.get("intent", "compound"),
        "routing_decision": routing_decision,
        "plan": plan_data,
        "context_summary": context_summary,
    }

    # Audit: log plan
    try:
        log_plan(
            user_id=state.get("user_id", "anonymous") if isinstance(state, dict) else "anonymous",
            plan=plan_data,
            query=user_query
        )
    except Exception:
        logger.warning("Audit log_plan failed", exc_info=True)

    return result
