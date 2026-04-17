"""NRG State Management - Immutable state with serialization for LangGraph."""

from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from datetime import datetime
import json
from pathlib import Path


@dataclass
class NRGState:
    """Central state object for National Research Graph orchestration."""

    query_id: str = ""
    session_id: str = ""
    user_query: str = ""
    conversation_history: list = field(default_factory=list)
    intent: str = ""
    routing_decision: Optional[str] = None
    context_summary: Optional[str] = None

    sql_query: Optional[str] = None
    sql_results: list = field(default_factory=list)

    retrieved_chunks: list = field(default_factory=list)
    retrieval_metadata: list = field(default_factory=list)

    synthesized_response: Optional[str] = None
    verification_status: bool = False

    trace: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    user_tier: int = 1
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_trace(self, node: str, event: str, data: Optional[dict] = None):
        self.trace.append(
            {
                "node": node,
                "event": event,
                "data": data or {},
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        self.updated_at = datetime.utcnow().isoformat()

    def add_error(self, node: str, error: str):
        self.errors.append(
            {"node": node, "error": error, "timestamp": datetime.utcnow().isoformat()}
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
