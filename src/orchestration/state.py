"""NRG State Management - Immutable state with serialization for LangGraph."""

from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from datetime import datetime, UTC
import json
from pathlib import Path


@dataclass
class QueryDAGNode:
    """Single node in a multi-hop query DAG."""
    id: str
    subquery: str
    skill: str  # "sql" | "rag" | "hybrid"
    depends_on: list[str] = field(default_factory=list)  # parent node IDs
    tables: list[str] = field(default_factory=list)
    output_shape: str = "mixed_summary"
    optional: bool = False  # True if this node can be skipped on failure

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class QueryDAG:
    """Directed Acyclic Graph for multi-hop query decomposition."""
    nodes: list[QueryDAGNode] = field(default_factory=list)
    root_id: str = ""  # ID of the entry node

    def to_dict(self) -> dict:
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
    conversation_history: list = field(default_factory=list)
    intent: str = ""
    plan: Optional[dict] = None
    planner_metadata: dict = field(default_factory=dict)
    routing_decision: Optional[str] = None
    routing_confidence: float = 0.0
    routing_rationale: list = field(default_factory=list)
    context_summary: Optional[str] = None

    sql_query: Optional[str] = None
    sql_results: list = field(default_factory=list)

    retrieved_chunks: list = field(default_factory=list)
    retrieval_metadata: list = field(default_factory=list)

    synthesized_response: Optional[str] = None
    citations: list = field(default_factory=list)
    verification_status: Any = False
    verification_retries: int = 0
    unsupported_claims: list = field(default_factory=list)
    faithfulness_score: float = 0.0
    score_breakdown: dict = field(default_factory=dict)

    trace: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    retrieval_sources: list = field(default_factory=list)
    provenance: dict = field(default_factory=dict)
    synthesis_method: str = "unknown"
    token_budget: dict = field(default_factory=dict)
    execution_time_ms: dict = field(default_factory=dict)
    node_timings: dict = field(default_factory=dict)

    user_tier: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def add_trace(self, node: str, event: str, data: Optional[dict] = None):
        self.trace.append(
            {
                "node": node,
                "event": event,
                "data": data or {},
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        self.updated_at = datetime.now(UTC).isoformat()

    def add_error(self, node: str, error: str):
        self.errors.append(
            {"node": node, "error": error, "timestamp": datetime.now(UTC).isoformat()}
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "NRGState":
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "NRGState":
        return cls.from_dict(json.loads(json_str))

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "NRGState":
        with open(path, "r") as f:
            return cls.from_json(f.read())
