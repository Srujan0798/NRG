# ADR-001: Use LangGraph for Query Orchestration

**Date:** 2026-04-21  
**Status:** Accepted  
**Author:** Architect Agent

## Context

NRG needs a system to orchestrate multi-step queries: decompose user intent → route to skills → execute → synthesize → verify.

## Decision

We will use **LangGraph** for query orchestration.

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **LangGraph** (chosen) | Native state management, cycles, checkpoints | New to team |
| Custom state machine | Full control | Reinventing wheel |
| AWS Step Functions | Managed | Vendor lock-in, costly |
| Temporal | Durable execution | Complex setup |

## Rationale

1. **State management**: LangGraph's state model maps directly to our 6-node pipeline
2. **Checkpoints**: Built-in session recovery for long-running queries
3. **Cycles**: Enables retry loops without external orchestration
4. **Agentic**: Future-proofs for agentic research assistants

## Consequences

### Positive
- Query pipeline becomes declarative
- Built-in retry/timeout handling
- Easy to add new nodes

### Negative
- Learning curve for team
- Additional dependency

## Implementation

```python
from langgraph.graph import StateGraph
graph = StateGraph(NRGState)
graph.add_node("planner", planner_node)
graph.add_node("router", router_node)
# ... etc
```

**Reviewed by:** Guardian Agent  
**Next Review:** 2026-07-21