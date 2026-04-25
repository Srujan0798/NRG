# ADR-001: Hybrid Text-to-SQL + RAG Query Processing Architecture

**Status:** Accepted
**Date:** 2026-04-25
**Deciders:** NRG Engineering Team

## Context

NRG (National Research Graph) is a sovereign AI platform for India's 600GB research database. Users query research data through natural language, expecting accurate SQL-generated responses backed by citations. The system must handle two fundamentally different query types:

1. **Structured queries** - Requests for specific metrics, counts, aggregations that require exact SQL execution against the PostgreSQL database (e.g., "How many patents were filed in 2023?")
2. **Unstructured queries** - Requests for contextual information, summaries, or qualitative insights that require semantic search over vectorized documents (e.g., "What are the emerging research trends in AI?")

The Dhairya SQL Audit Report revealed 7/17 correct responses (41%) when using pure Text-to-SQL, indicating significant accuracy challenges. Meanwhile, pure RAG cannot satisfy the analytical requirements of government/industry stakeholders who need precise metrics.

### Forces at Play

- **Query diversity**: Research queries span structured analytics to unstructured exploration
- **Accuracy requirements**: Government/industry stakeholders need verifiable, citation-backed answers
- **Schema complexity**: 58 production tables with complex relationships (vs 18-table dev SQLite)
- **Sovereignty constraints**: All data must stay on Indian infrastructure
- **Performance**: Average 7.2s response time in baseline tests

## Decision

NRG implements a **Hybrid Text-to-SQL + RAG architecture** with an intelligent router that:

1. Classifies incoming queries into `structured`, `unstructured`, or `hybrid` intent
2. Routes to appropriate skill(s): `TextToSQLSkill` and/or `RAGSkill`
3. Uses parallel/DAG execution when both skills are needed
4. Synthesizes results through a 3-tier cascade (cloud LLM → local SLM → rule-based)

The 6-node LangGraph pipeline orchestrates this:
```
receiver → planner → router → executor → synthesizer → verifier → END
```

## Options Considered

### Option A: Pure Text-to-SQL

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Cost | Low (single LLM call per query) |
| Scalability | Limited by SQL generation quality |
| Team familiarity | High (well-understood pattern) |

**Pros:**
- Direct database access for exact metrics
- Full audit trail of SQL executed
- Simpler architecture with fewer components

**Cons:**
- 41% accuracy on Dhairya benchmark (7/17 correct)
- Struggles with complex JOINs across 58 tables
- Cannot handle qualitative/analytical questions
- SQL injection risk requires robust sanitization

### Option B: Pure RAG

| Dimension | Assessment |
|-----------|------------|
| Complexity | Medium |
| Cost | Medium (embedding + vector search + LLM) |
| Scalability | High (horizontal vector scaling) |
| Team familiarity | Medium |

**Pros:**
- Handles natural language gracefully
- No SQL generation errors
- Built-in citation via chunk references

**Cons:**
- Cannot produce exact metrics or aggregations
- Requires maintaining vector database (Qdrant)
- May hallucinate specific numbers
- Doesn't leverage relational schema richness

### Option C: Hybrid Text-to-SQL + RAG (CHOSEN)

| Dimension | Assessment |
|-----------|------------|
| Complexity | High |
| Cost | Medium-High |
| Scalability | High |
| Team familiarity | Medium |

**Pros:**
- Handles both structured and unstructured queries
- 3-tier synthesis provides graceful degradation
- Router achieves 51/51 tests passing for intent classification
- Parallel execution reduces latency for hybrid queries

**Cons:**
- Most complex architecture (6-node pipeline)
- Requires maintaining both SQL and vector pipelines
- Synthesis layer adds latency
- Higher operational overhead

## Trade-off Analysis

| Factor | Pure SQL | Pure RAG | Hybrid |
|--------|----------|----------|--------|
| Structured query accuracy | High* | Low | High |
| Unstructured comprehension | Low | High | High |
| Exact metrics | ✓ | ✗ | ✓ |
| Qualitative insights | ✗ | ✓ | ✓ |
| Implementation complexity | Low | Medium | High |
| Citation faithfulness | Via SQL log | Via chunk ID | Via verifier node |
| Graceful degradation | None | LLM fallback | 3-tier cascade |

*High only if SQL generation succeeds; Dhairya shows 41% success rate in practice.

The hybrid approach accepts higher complexity in exchange for:
- Broad query coverage (100% of query types)
- Accuracy on structured queries via SQL execution
- Rich contextual responses via RAG
- Verifiable citations via the verifier node

## Consequences

### What becomes easier:
- Supporting diverse user personas (researcher/government/industry)
- Handling multi-intent queries with sub-query decomposition
- Graceful degradation when cloud LLM is unavailable
- Adding new query types via router classification rules

### What becomes harder:
- Debugging cross-skill interactions in the executor
- Maintaining consistent latency across query types
- Ensuring citation faithfulness when synthesizing from multiple sources
- Local development (requires both SQLite and Qdrant)

### What we'll need to revisit:
- Router confidence thresholds may need tuning as query patterns evolve
- Schema hints for SQL generation may require updates as PostgreSQL schema changes
- The 3-tier synthesis cascade ratios (cloud/local/rule-based) need performance monitoring
- Parallel execution may need horizontal scaling for high concurrency

## Action Items

- [ ] Monitor Dhairya benchmark accuracy monthly; target >80% correct
- [ ] Instrument router confidence scores in Langfuse
- [ ] Benchmark hybrid vs parallel execution latency
- [ ] Document fallback behavior when SQL generation fails but RAG succeeds
- [ ] Evaluate whether local SLM can handle synthesis for Tier 3 (industry) queries
