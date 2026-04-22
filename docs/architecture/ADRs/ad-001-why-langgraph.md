# ADR-001: Why LangGraph for Orchestration

**Date:** 2026-04-21  
**Status:** Accepted  
**Deciders:** Architecture Team, Guardian Agent  
**Review:** 2026-07-21

---

## Context

NRG requires a system to orchestrate multi-step queries across multiple skills (Text-to-SQL, RAG, Knowledge Graph) with:
- Intent decomposition and routing
- State management across long-running queries
- Error handling and retry logic
- Audit trail integration
- Future support for agentic research assistants

---

## Decision

We will use **LangGraph** for query orchestration, implementing a 6-node pipeline:

```
Query → Planner → Router → Executor → Synthesizer → Verifier → Reflector → Response
```

---

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **LangGraph** (chosen) | Native state management, cycles, checkpoints, agentic future | Learning curve | ✅ Accepted |
| Custom state machine | Full control | Reinventing wheel, maintenance burden | ❌ Rejected |
| AWS Step Functions | Managed, reliable | Vendor lock-in, costly, cold starts | ❌ Rejected |
| Temporal | Durable execution, complex workflows | Complex setup, operational overhead | ❌ Rejected |
| LangChain | Pre-built abstractions | Higher abstraction, less flexibility | ⚠️ LangGraph preferred |

---

## Rationale

### 1. State Management
LangGraph's state model maps directly to our 6-node pipeline:

```python
@dataclass
class NRGState(TypedDict):
    query: str
    user_tier: int
    intent: str | None
    route: str | None
    results: list[Any] | None
    response: str | None
    citations: list[dict] | None
    warnings: list[str]
    verification: bool | None
    audit_hash: str | None
```

### 2. Checkpointing
Built-in session recovery for long-running queries via LangGraph checkpoints.

### 3. Cycles
Enables retry loops without external orchestration:
```python
graph.add_edge("executor", "verifier")
graph.add_conditional_edges(
    "verifier",
    lambda s: "executor" if not s["verification"] else "synthesizer"
)
```

### 4. Agentic Future
LangGraph provides a clear path to agentic research assistants with tool use, memory, and planning capabilities.

### 5. Integration with Langfuse
Native tracing integration for observability.

---

## Consequences

### Positive
- Query pipeline becomes declarative and maintainable
- Built-in retry/timeout handling per node
- Easy to add new nodes and skills
- Langfuse integration for distributed tracing
- Clear separation of concerns

### Negative
- Learning curve for team members unfamiliar with LangGraph
- Additional dependency to maintain
- Version upgrades may require code changes

### Risks
- LangGraph API changes could break pipeline nodes
- Mitigation: Pin version, review changelog before upgrades

---

## Implementation

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(NRGState)
graph.add_node("planner", planner_node)
graph.add_node("router", router_node)
graph.add_node("executor", executor_node)
graph.add_node("synthesizer", synthesizer_node)
graph.add_node("verifier", verifier_node)
graph.add_node("reflector", reflector_node)

graph.set_entry_point("planner")
graph.add_edge("planner", "router")
graph.add_edge("router", "executor")
graph.add_edge("executor", "synthesizer")
graph.add_edge("synthesizer", "verifier")
graph.add_edge("verifier", END)

compiled = graph.compile()
```

---

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [NRG Orchestration](docs/architecture/ORCHESTRATION.md)
- [Langfuse Tracing Setup](docs/OBSERVABILITY.md)

---

**Reviewed by:** Guardian Agent  
**Sign-off:** 2026-04-21