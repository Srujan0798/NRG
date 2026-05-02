"""NRG State Management - Immutable state with serialization for LangGraph."""

from dataclasses import asdict, dataclass, field
from typing import Any, Optional, cast
from datetime import datetime, UTC
import json
from pathlib import Path

JSONDict = dict[str, Any]
JSONList = list[Any]


def _str_list() -> list[str]:
    return []


def _json_dict_list() -> list[JSONDict]:
    return []


def _json_dict() -> JSONDict:
    return {}


def _float_dict() -> dict[str, float]:
    return {}


@dataclass
class QueryDAGNode:
    """Single node in a multi-hop query DAG."""

    id: str
    subquery: str
    skill: str  # "sql" | "rag" | "hybrid"
    depends_on: list[str] = field(default_factory=_str_list)  # parent node IDs
    tables: list[str] = field(default_factory=_str_list)
    output_shape: str = "mixed_summary"
    optional: bool = False  # True if this node can be skipped on failure

    def to_dict(self) -> JSONDict:
        return asdict(self)


@dataclass
class QueryDAG:
    """Directed Acyclic Graph for multi-hop query decomposition."""

    nodes: list[QueryDAGNode] = field(default_factory=lambda: [])
    root_id: str = ""  # ID of the entry node

    def to_dict(self) -> JSONDict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "root_id": self.root_id,
            "edge_count": sum(len(n.depends_on) for n in self.nodes),
        }


@dataclass
class NRGState:
    """Central state object for National Research Graph orchestration."""

    query_id: str = ""
    session_id: str = ""
    user_query: str = ""
    interpreted_question: str = ""
    conversation_history: list[JSONDict] = field(default_factory=_json_dict_list)
    assumptions: list[str] = field(default_factory=_str_list)
    caveats: list[str] = field(default_factory=_str_list)
    follow_up_suggestions: list[str] = field(default_factory=_str_list)
    freshness: JSONDict = field(default_factory=_json_dict)
    source_data: JSONDict = field(default_factory=_json_dict)
    answer_id: str = ""
    intent: str = ""
    plan: Optional[JSONDict] = None
    planner_metadata: JSONDict = field(default_factory=_json_dict)
    routing_decision: Optional[str] = None
    routing_confidence: float = 0.0
    routing_rationale: list[str] = field(default_factory=_str_list)
    context_summary: Optional[str] = None
    catalog_route: str = ""
    catalog_confidence: float = 0.0
    catalog_matches: list[str] = field(default_factory=_str_list)
    matched_domains: list[str] = field(default_factory=_str_list)

    sql_query: Optional[str] = None
    sql_results: list[JSONDict] = field(default_factory=_json_dict_list)
    sql_anomaly_report: JSONDict = field(default_factory=_json_dict)
    answer_confidence: str = "high"
    answer_confidence_score: float = 0.95
    needs_clarification: bool = False
    clarification_question: Optional[str] = None

    retrieved_chunks: list[JSONDict] = field(default_factory=_json_dict_list)
    retrieval_metadata: list[JSONDict] = field(default_factory=_json_dict_list)

    synthesized_response: Optional[str] = None
    citations: list[JSONDict] = field(default_factory=_json_dict_list)
    verification_status: Any = False
    verification_retries: int = 0
    unsupported_claims: list[str] = field(default_factory=_str_list)
    faithfulness_score: float = 0.0
    score_breakdown: JSONDict = field(default_factory=_json_dict)

    trace: list[JSONDict] = field(default_factory=_json_dict_list)
    errors: list[JSONDict] = field(default_factory=_json_dict_list)
    warnings: list[str] = field(default_factory=_str_list)
    retrieval_sources: list[JSONDict] = field(default_factory=_json_dict_list)
    provenance: JSONDict = field(default_factory=_json_dict)
    synthesis_method: str = "unknown"
    token_budget: JSONDict = field(default_factory=_json_dict)
    execution_time_ms: dict[str, float] = field(default_factory=_float_dict)
    node_timings: dict[str, float] = field(default_factory=_float_dict)

    user_tier: int = 1
    active_domain: str = ""  # locks table context across follow-up turns
    last_domain_table: str = ""  # exact table context from the previous turn
    last_query_type: str = ""  # coarse query type for short follow-up turns
    last_primary_entity: str = ""  # institute/entity carried into follow-up turns
    previous_domain: str = ""  # tracks domain switches for cross-domain detection
    domain_switch_detected: bool = False  # True if current query switches domain
    complexity: str = (
        "moderate"  # LLM cost complexity: trivial/simple/moderate/complex/synthesis_heavy
    )
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def add_trace(self, node: str, event: str, data: Optional[JSONDict] = None) -> None:
        self.trace.append(
            {
                "node": node,
                "event": event,
                "data": data or {},
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        self.updated_at = datetime.now(UTC).isoformat()

    def add_error(self, node: str, error: str) -> None:
        self.errors.append(
            {"node": node, "error": error, "timestamp": datetime.now(UTC).isoformat()}
        )

    def to_dict(self) -> JSONDict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: JSONDict) -> "NRGState":
        return cls(**cast(Any, data))

    @classmethod
    def from_json(cls, json_str: str) -> "NRGState":
        return cls.from_dict(json.loads(json_str))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "NRGState":
        with open(path, "r") as f:
            return cls.from_json(f.read())
