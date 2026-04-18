# NRG Orchestration Specification v1.0

## State Schema

```python
# src/orchestration/state.py
from typing import TypedDict, Optional
from datetime import datetime

class NRGState(TypedDict):
    query_id: str
    user_query: str
    user_tier: int
    session_id: str
    timestamp: str
    intent: Optional[str]
    routing_decision: Optional[str]
    skill_plan: Optional[dict]
    sql_query: Optional[str]
    sql_result: Optional[list]
    vector_query: Optional[str]
    vector_results: Optional[list]
    synthesized_response: Optional[str]
    verification_status: Optional[str]
    error: Optional[str]
    conversation_history: list[dict]
```

## Node Contract

| Node | Input | Output | Retry Policy | Error Taxonomy |
|------|-------|--------|-------------|----------------|
| `receiver` | user_query | normalized_query, intent | 3× exponential | ValidationError |
| `router` | intent | routing_decision, skill_plan | 2× exponential | RouteNotFound |
| `executor` | skill_plan | sql_result, vector_results | 3× linear | ExecutionError |
| `synthesizer` | sql_result + vector_results | synthesized_response | 2× exponential | SynthesisError |
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

# src/orchestration/nodes/router.py
def router_node(state: NRGState) -> NRGState:
    """Route to appropriate skill (text-to-sql or RAG)."""
    # 1. Classify intent
    # 2. Select skill
    # 3. Generate plan
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
```

## Edge Conditions

```python
# Graph definition
workflow.set_entry_point("receiver")
workflow.add_edge("receiver", "router")
workflow.add_edge("router", "executor")
workflow.add_edge("executor", "synthesizer")
workflow.add_edge("synthesizer", END)

# Conditional edges for errors
def should_retry(state: NRGState) -> bool:
    return state.get("error") is not None

workflow.add_conditional_edge(
    "synthesizer",
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