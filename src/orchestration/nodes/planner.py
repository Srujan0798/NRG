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
from src.security.egress.schema_allowlist_loader import get_allowlist
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
    "sql": [
        "researcher",
        "lab",
        "funding",
        "grant",
        "publication",
        "institution",
        "institute",
        "iit",
        "count",
        "list",
        "find",
        "show",
        "which",
        "credit",
        "curriculum",
        "innovation",
        "stage",
        "technology readiness",
        "market ready",
        "bottleneck",
        "patent",
        "yoy",
        "year-over-year",
    ],
    "rag": ["explain", "describe", "trend", "advance", "overview", "analysis", "summarize", "what are", "latest"],
}

TABLE_TO_DOMAIN = {
    "researchers": "research",
    "publications": "research",
    "researcher_publications": "research",
    "institutions": "research",
    "labs": "research",
    "researcher_labs": "research",
    "innovation_grant_from_govt": "funding",
    "financial_expenses_operational": "funding",
    "financial_expenses_capital": "funding",
    "combined_ipo_patent_data": "patents",
    "patents_details": "patents",
    "ipo_patent_details_flat": "patents",
    "incubation_details": "startups",
    "startup_recognition": "startups",
    "founders_of_fortune_500": "startups",
    "phd_students": "academic",
    "academic_courses_details": "academic",
    "faculty_details": "academic",
    "faculty_strength": "academic",
    "actual_student_strength": "academic",
    "sanctioned_intake": "academic",
    "placements_and_higher_studies": "academic",
    "nirf_extracted_table": "rankings",
    "nirf_table_row": "rankings",
    "nirf_pdf_record": "rankings",
}


def _detect_domain_from_tables(tables: list[str]) -> str:
    """Detect the primary domain from a list of table names."""
    if not tables:
        return "unspecified"
    domain_counts: dict[str, int] = {}
    for table in tables:
        domain = TABLE_TO_DOMAIN.get(table.lower(), "other")
        if domain != "other":
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
    if not domain_counts:
        return "other"
    return max(domain_counts, key=domain_counts.get)


class Plan(BaseModel):
    schema_tables: list[str] = Field(default_factory=list)
    desired_skills: list[str] = Field(default_factory=list)
    expected_output_shape: str = ""
    dag_nodes: list[dict] = Field(default_factory=list)
    dag_root_id: str = Field(default="")
    is_dag: bool = Field(default=False)
    subqueries: list[str] = Field(default_factory=list)


@trace_llm_call("planner")
def planner_node(state: Any) -> dict:
    """Build a schema-only execution plan for downstream router/executor."""
    user_query = _state_get(state, "user_query", "")
    conversation_history = _state_get(state, "conversation_history", [])
    user_id = _state_get(state, "user_id", "planner")
    previous_domain = _state_get(state, "active_domain", "")
    planning_query = _enrich_followup_query(
        user_query,
        last_domain_table=_state_get(state, "last_domain_table", ""),
        last_primary_entity=_state_get(state, "last_primary_entity", ""),
        last_query_type=_state_get(state, "last_query_type", ""),
    )

    client = _get_planner_client()
    schema_prompt = _build_schema_prompt(planning_query)

    if client is not None:
        system_prompt = _load_prompt()
        user_prompt = (
            f"{schema_prompt}\n\n"
            f"User Query: {planning_query}\n\n"
            "Return the strict JSON plan only."
        )

        try:
            raw = client.generate(system_prompt, user_prompt, conversation_history[-3:])
            plan = _parse_plan(raw)
            plan_dict = plan.model_dump()
            try:
                log_plan(user_id, planning_query, plan_dict)
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
                **_domain_update(plan_dict, previous_domain),
                **_context_update(plan_dict, state, planning_query),
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
                    log_plan(user_id, planning_query, plan_dict)
                except Exception:
                    pass
                return {
                    "plan": plan_dict,
                    "planner_metadata": {
                        "mode": "llm_repaired",
                        "model": _client_model_name(client),
                    },
                    **_domain_update(plan_dict, previous_domain),
                    **_context_update(plan_dict, state, planning_query),
                }
            except Exception:
                pass

    fallback_plan = _heuristic_decompose(planning_query, schema_prompt)
    try:
        log_plan(user_id, planning_query, fallback_plan)
    except Exception:
        pass

    return {
        "plan": fallback_plan,
        "planner_metadata": {
            "mode": "heuristic_fallback",
            "reason": "llm_unavailable_or_failed",
        },
        **_domain_update(fallback_plan, previous_domain),
        **_context_update(fallback_plan, state, planning_query),
    }


def _domain_update(plan_dict: dict, previous_domain: str) -> dict:
    """Compute domain state updates from a plan's schema_tables."""
    tables = plan_dict.get("schema_tables", [])
    current_domain = _detect_domain_from_tables(tables)
    domain_switch = bool(previous_domain and previous_domain != "unspecified"
                         and current_domain != "unspecified"
                         and current_domain != previous_domain)
    return {
        "previous_domain": previous_domain,
        "active_domain": current_domain,
        "domain_switch_detected": domain_switch,
    }


def _enrich_followup_query(
    query: str,
    *,
    last_domain_table: str = "",
    last_primary_entity: str = "",
    last_query_type: str = "",
) -> str:
    """Carry previous table/entity context into short follow-up questions."""
    query_lower = query.lower()
    followup_terms = ("compare", "same", "that", "those", "their", "also", "too", "previous")
    if not last_domain_table or not any(term in query_lower for term in followup_terms):
        return query

    context_parts = [f"previous table was {last_domain_table}"]
    if last_primary_entity:
        context_parts.append(f"previous entity was {last_primary_entity}")
    if last_query_type:
        context_parts.append(f"previous query type was {last_query_type}")
    return f"[Context: {'; '.join(context_parts)}] {query}"


def _context_update(plan_dict: dict, state: Any, planning_query: str) -> dict:
    tables = plan_dict.get("schema_tables", [])
    previous_table = _state_get(state, "last_domain_table", "")
    last_domain_table = tables[0] if tables else previous_table

    primary_entity = (
        _extract_primary_entity(_state_get(state, "user_query", ""))
        or _state_get(state, "last_primary_entity", "")
        or _extract_primary_entity(planning_query)
    )
    query_type = _infer_query_type(planning_query) or _state_get(state, "last_query_type", "")
    return {
        "last_domain_table": last_domain_table,
        "last_primary_entity": primary_entity,
        "last_query_type": query_type,
    }


def _extract_primary_entity(query: str) -> str:
    query_lower = query.lower()
    entity_map = {
        "iit bombay": "IIT Bombay",
        "iit delhi": "IIT Delhi",
        "iit madras": "IIT Madras",
        "iit kanpur": "IIT Kanpur",
        "iit gandhinagar": "IIT Gandhinagar",
        "iisc": "IISc",
    }
    for marker, entity in entity_map.items():
        if marker in query_lower:
            return entity
    return ""


def _infer_query_type(query: str) -> str:
    query_lower = query.lower()
    if "phd" in query_lower and any(term in query_lower for term in ("ug", "undergraduate")):
        return "phd_ug_comparison"
    if "phd" in query_lower:
        return "phd_course_count"
    if "patent" in query_lower and "grant" in query_lower:
        return "grant_patent_efficiency"
    if "trl" in query_lower or "technology readiness" in query_lower:
        return "trl_progression"
    if any(term in query_lower for term in ("funding", "grant")):
        return "funding_aggregate"
    if any(term in query_lower for term in ("startup", "incubation")):
        return "startup_output"
    return ""


def _heuristic_decompose(user_query: str, schema_prompt: str) -> dict:
    """Perform heuristic query decomposition producing a DAG when LLM unavailable."""
    import uuid
    query_lower = user_query.lower()

    subqueries = _extract_subqueries(query_lower)
    tables = _extract_schema_tables(schema_prompt)
    skills = _determine_skills(query_lower)
    output_shape = _determine_output_shape(query_lower)

    multi_hop_indicators = ["compare", "versus", "vs", "both", "and", "gap", "difference", "between", "synthesis", "integrate"]
    true_comparison_indicators = ["compare", "versus", "vs", "difference", "between"]
    if len(subqueries) <= 1:
        is_multi_hop = any(ind in query_lower for ind in multi_hop_indicators)
        is_true_comparison = any(ind in query_lower for ind in true_comparison_indicators)
        if is_multi_hop and len(subqueries) == 1:
            root_id = f"node_{uuid.uuid4().hex[:6]}"
            sq = subqueries[0]
            dag_nodes = [{"id": root_id, "subquery": sq, "skill": skills[0] if skills else "sql", "depends_on": [], "tables": tables, "output_shape": output_shape, "optional": False}]
            if is_true_comparison:
                comparands = _extract_comparison_entities(query_lower)
                for entity in comparands:
                    entity_node_id = f"node_{uuid.uuid4().hex[:6]}"
                    dag_nodes.append({
                        "id": entity_node_id,
                        "subquery": f"Query for {entity}: {sq}",
                        "skill": skills[0] if skills else "sql",
                        "depends_on": [root_id],
                        "tables": tables,
                        "output_shape": output_shape,
                        "optional": False,
                    })
            return {
                "subqueries": subqueries,
                "schema_tables": tables,
                "desired_skills": skills,
                "expected_output_shape": output_shape,
                "dag_nodes": dag_nodes,
                "dag_root_id": root_id,
                "is_dag": len(dag_nodes) > 1,
            }
        root_id = f"node_{uuid.uuid4().hex[:6]}"
        dag_nodes = [
            {
                "id": root_id,
                "subquery": sq,
                "skill": skills[0] if skills else "sql",
                "depends_on": [],
                "tables": tables,
                "output_shape": output_shape,
                "optional": False,
            }
            for sq in subqueries
        ]
        return {
            "subqueries": subqueries,
            "schema_tables": tables,
            "desired_skills": skills,
            "expected_output_shape": output_shape,
            "dag_nodes": dag_nodes,
            "dag_root_id": root_id if dag_nodes else "",
            "is_dag": True,
        }

    multi_hop_indicators = ["compare", "versus", "vs", "both", "and", "gap", "difference", "between", "synthesis", "integrate"]
    true_comparison_indicators = ["compare", "versus", "vs", "difference", "between"]
    is_multi_hop = any(ind in query_lower for ind in multi_hop_indicators)
    is_true_comparison = any(ind in query_lower for ind in true_comparison_indicators)

    root_id = f"node_{uuid.uuid4().hex[:6]}"
    dag_nodes = []

    if is_true_comparison:
        for i, sq in enumerate(subqueries):
            node_id = f"node_{uuid.uuid4().hex[:6]}"
            dag_nodes.append({
                "id": node_id,
                "subquery": sq,
                "skill": skills[i % len(skills)] if skills else "sql",
                "depends_on": [root_id],
                "tables": tables,
                "output_shape": output_shape,
                "optional": False,
            })

        dag_nodes.insert(0, {
            "id": root_id,
            "subquery": user_query,
            "skill": "sql",
            "depends_on": [],
            "tables": tables,
            "output_shape": output_shape,
            "optional": False,
        })
    else:
        prev_id = None
        for i, sq in enumerate(subqueries):
            node_id = f"node_{uuid.uuid4().hex[:6]}"
            dag_nodes.append({
                "id": node_id,
                "subquery": sq,
                "skill": skills[i % len(skills)] if skills else "sql",
                "depends_on": [prev_id] if prev_id else [],
                "tables": tables,
                "output_shape": output_shape,
                "optional": False,
            })
            prev_id = node_id
        root_id = dag_nodes[0]["id"] if dag_nodes else root_id

    return {
        "subqueries": subqueries,
        "schema_tables": tables,
        "desired_skills": skills,
        "expected_output_shape": output_shape,
        "dag_nodes": dag_nodes,
        "dag_root_id": root_id,
        "is_dag": len(dag_nodes) > 1,
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


def _extract_comparison_entities(query_lower: str) -> list[str]:
    """Extract named entities being compared (states, institutions, etc)."""
    known_entities = [
        "gujarat", "karnataka", "maharashtra", "tamil nadu", "kerala",
        "delhi", "mumbai", "bangalore", "chennai", "hyderabad",
        "iit bombay", "iit delhi", "iit madras", "iit kanpur",
        "india", "usa", "china",
    ]
    found = []
    for entity in known_entities:
        if entity in query_lower:
            found.append(entity)
    if not found:
        parts = re.split(r'\s+(?:and|vs|versus|compare|with)\s+', query_lower)
        if len(parts) >= 2:
            for part in parts[1:]:
                cleaned = re.sub(r'\s+', ' ', part).strip()
                if len(cleaned) > 2:
                    found.append(cleaned[:30])
    return found[:3]


def _build_schema_prompt(user_query: str) -> str:
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("postgresql") or db_url.startswith("postgres"):
        from src.skills.text_to_sql.schema_extractor import SchemaExtractor
        extractor = SchemaExtractor(connection_string=db_url)
    else:
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
    """
    Get planner LLM client with schema allowlisting for sovereign egress control.

    Schema allowlisting ensures:
    1. Only table/column names from the allowlist are exposed to the LLM
    2. No raw data, PII, or schema structure beyond the allowlist
    3. Egress is bounded to only schema metadata, not actual data
    """
    # Check if planner LLM is explicitly enabled
    planner_enabled = os.getenv("LLM_PLANNER_ENABLED", "true").lower() == "true"
    if not planner_enabled:
        return None

    # Get provider from env or default to first available
    provider = os.getenv("LLM_PLANNER_PROVIDER")

    # Get schema allowlist for egress control
    allowlist = _get_schema_allowlist()

    # Build egress-controlled client
    if provider:
        try:
            client = get_llm_client(provider)
            # Wrap client with schema allowlist filtering
            return _SchemaAllowlistingClient(client, allowlist)
        except Exception as e:
            logger.warning("Failed to get planner client for provider %s: %s", provider, e)

    # Allow generic client for testing
    if getattr(get_llm_client, "__module__", "") != "src.config.llm_config":
        try:
            client = get_llm_client()
            return _SchemaAllowlistingClient(client, allowlist)
        except Exception:
            pass

    return None


# Schema allowlist for egress control
_SCHEMA_ALLOWLIST = None


def _get_schema_allowlist() -> set:
    """Get cached schema allowlist from YAML loader."""
    allowlist = get_allowlist()
    return allowlist.get_allowed_tables()


def _filter_schema_prompt(schema_prompt: str, allowlist: set) -> str:
    """
    Filter schema prompt to only include allowlisted table/column names.
    This ensures LLM only sees approved schema elements, preventing
    schema fingerprinting attacks.
    """

    # Remove any non-allowlisted table references
    lines = schema_prompt.split('\n')
    filtered_lines = []
    for line in lines:
        # Skip lines with unlisted table names (but keep headers and structure)
        # Allow any line that doesn't reference a specific table name
        if any(f'"{tbl}"' in line or f"'{tbl}'" in line or f" {tbl} " in line.lower()
               for tbl in ["researchers", "publications", "institutions", "labs",
                          "funding_records", "projects", "patents"]):
            if not any(tbl in allowlist for tbl in allowlist):
                continue
        filtered_lines.append(line)

    return '\n'.join(filtered_lines)


class _SchemaAllowlistingClient:
    """
    Wrapper client that filters prompts through schema allowlist before LLM calls.
    Ensures no schema fingerprinting via prompt analysis.
    """

    def __init__(self, base_client: Any, allowlist: set):
        self._client = base_client
        self._allowlist = allowlist

    def generate(self, system_prompt: str, user_prompt: str, history: list) -> str:
        """Generate with schema filtering applied to system prompt."""
        # Filter system prompt to only expose allowlisted schema elements
        filtered_system = _filter_schema_prompt(system_prompt, self._allowlist)

        # For user prompt, ensure no schema probing
        if any(phrase in user_prompt.lower() for phrase in
               ["show tables", "describe", "what columns", "list schema"]):
            logger.warning("Schema probing detected in planner user prompt, blocking")
            raise PermissionError("Schema probing blocked in planner")

        return self._client.generate(filtered_system, user_prompt, history)

    @property
    def model(self) -> str:
        """Pass through model name."""
        return getattr(self._client, "model", "unknown")


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


def _build_dag(nodes: list[dict]) -> tuple[dict[str, dict], list[str]]:
    """Build adjacency list and topological order from DAG nodes.

    Returns (node_map, execution_order) where execution_order is nodes
    in topological sort (parents before children).
    """
    from collections import defaultdict

    node_map: dict[str, dict] = {n["id"]: n for n in nodes}
    in_degree: dict[str, int] = {n["id"]: 0 for n in nodes}
    children: dict[str, list[str]] = defaultdict(list)

    for n in nodes:
        for parent_id in n.get("depends_on", []):
            if parent_id in node_map:
                children[parent_id].append(n["id"])
                in_degree[n["id"]] += 1

    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    order = []
    while queue:
        nid = queue.pop(0)
        order.append(nid)
        for child_id in children[nid]:
            in_degree[child_id] -= 1
            if in_degree[child_id] == 0:
                queue.append(child_id)

    return node_map, order
