# NRG Orchestration Specification v1.0

## State Schema

```python
# src/orchestration/state.py
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class NRGState:
    query_id: str
    user_query: str
    user_tier: int = 1
    session_id: str = ""
    timestamp: str = ""
    intent: Optional[str] = None
    routing_decision: Optional[str] = None
    plan: Optional[dict] = None
    planner_metadata: Optional[dict] = None
    sql_query: Optional[str] = None
    sql_results: Optional[list] = None
    retrieved_chunks: Optional[list] = None
    chunk_metadata: Optional[list] = None
    synthesized_response: Optional[str] = None
    verification_status: Optional[bool] = None
    verification_retries: int = 0
    citations: Optional[list] = None
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    trace: list = field(default_factory=list)
    retrieval_sources: Optional[list] = None
    provenance: Optional[dict] = None
    unsupported_claims: list = field(default_factory=list)
    conversation_history: list = field(default_factory=list)
```

## Node Contract

| Node | Input | Output | Retry Policy | Error Taxonomy |
|------|-------|--------|-------------|----------------|
| `receiver` | user_query | query_id, session_id | 3× exponential | ValidationError |
| `planner` | user_query | plan, planner_metadata | 2× exponential | PlanError |
| `router` | plan | routing_decision, intent | 2× exponential | RouteNotFound |
| `executor` | routing_decision | sql_results, retrieved_chunks | 3× linear | ExecutionError |
| `synthesizer` | sql_results + retrieved_chunks | synthesized_response | 2× exponential | SynthesisError |
| `verifier` | synthesized_response | verification_status, citations | 2× linear | VerificationError |
| `reflector` (optional) | response | reflection | 1× linear | ReflectionError |
| `retry_handler` | error | retry_action | - | - |

### Node Definitions

```python
# src/orchestration/nodes/receiver.py
def receiver_node(state: NRGState) -> NRGState:
    """Normalize and validate user query."""
    # 1. Sanitize input
    # 2. Extract intent
    # 3. Set defaults
    return state

# src/orchestration/nodes/planner.py
def planner_node(state: NRGState) -> NRGState:
    """Decompose query into sub-queries using schema-only LLM prompt."""
    # 1. Build schema-only prompt
    # 2. Call LLM for plan
    # 3. Parse JSON plan
    return state

# src/orchestration/nodes/router.py
def router_node(state: NRGState) -> NRGState:
    """Route to appropriate skill (text-to-sql or RAG)."""
    # 1. Classify intent
    # 2. Detect ambiguity, add clarifications
    # 3. Select skill
    return state

# src/orchestration/nodes/executor.py
def executor_node(state: NRGState) -> NRGState:
    """Execute skill and retrieve data."""
    # 1. Execute skill (text-to-sql or RAG)
    # 2. Apply RBAC filters
    # 3. Return results
    return state

# src/orchestration/nodes/synthesizer.py
def synthesizer_node(state: NRGState) -> NRGState:
    """Synthesize results into response."""
    # 1. Combine SQL + vector results
    # 2. Run local SLM synthesis
    # 3. Verify against sources
    return state

# src/orchestration/nodes/verifier.py
def verifier_node(state: NRGState) -> NRGState:
    """Verify synthesized response against sources."""
    # 1. Check citation coverage
    # 2. Flag unsupported claims
    # 3. Set verification_status
    return state
```

## Edge Conditions

```python
# Graph definition
workflow.set_entry_point("receiver")
workflow.add_edge("receiver", "planner")
workflow.add_edge("planner", "router")
workflow.add_edge("router", "executor")
workflow.add_edge("executor", "synthesizer")
workflow.add_edge("synthesizer", "verifier")
workflow.add_edge("verifier", END)

# Conditional edges for errors
def should_retry(state: NRGState) -> bool:
    return len(state.errors) > 0

workflow.add_conditional_edge(
    "verifier",
    should_retry,
    {
        True: "retry_handler",
        False: END
    }
)
```

## Retry Policy

| Node | Max Retries | Backoff | On Failure |
|------|-----------|--------|----------|
| `receiver` | 3 | exponential | return error |
| `router` | 2 | exponential | fallback routing |
| `executor` | 3 | linear | return partial results |
| `synthesizer` | 2 | exponential | return raw results |

## Error Taxonomy

```python
class ValidationError(Exception):
    """Invalid input query."""
    code = "VALIDATION_001"

class RouteNotFound(Exception):
    """No skill matches intent."""
    code = "ROUTE_001"

class ExecutionError(Exception):
    """Skill execution failed."""
    code = "EXEC_001"

class SynthesisError(Exception):
    """Synthesis failed."""
    code = "SYNTH_001"

class ReflectionError(Exception):
    """Self-reflection failed."""
    code = "REFLECT_001"
```

## Sequence Diagram

```
User Query
    │
    ▼
┌─────────────┐
│  receiver   │ ──→ Normalize, intent detection
└─────────────┘
    │
    ▼
┌─────────────┐
│   router    │ ──→ Skill selection, plan generation
└─────────────┘
    │
    ▼
┌─────────────┐
│  executor   │ ──→ Execute text-to-sql OR RAG
└─────────────┘
    │
    ▼
┌─────────────┐
│ synthesizer │ ──→ Local SLM synthesis, verification
└─────────────┘
    │
    ▼
┌─────────────┐
│  reflector  │ (optional) ──→ Self-reflection
└─────────────┘
    │
    ▼
   User
```

## Adding a New Skill

1. Add skill file in `src/skills/{skill_name}/skill.py`
2. Add node in `src/orchestration/nodes/{skill_name}.py`
3. Register in `router_node` skill registry
4. Add edge in `graph.py`
5. Add tests in `tests/skills/`

---

*Add a skill in <2 hours by following this contract.*