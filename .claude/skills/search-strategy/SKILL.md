---
name: search-strategy
description: Query decomposition and multi-source search orchestration. Breaks natural language questions into targeted searches per source, translates queries into source-specific syntax, ranks results by relevance, and handles ambiguity and fallback strategies.
user-invocable: false
model-agnostic: true
---

# Search Strategy

> **Model-agnostic:** Works with any LLM that supports tool use (Claude, GPT-4, Gemini, Grok, local models).
> Source connectors are denoted as `[source-type]` — replace with whatever data sources are connected.

The core intelligence behind multi-source search. Transforms a single natural language question into parallel, source-specific searches and produces ranked, deduplicated results.

## For NRG Specifically

NRG sources:
- `[sql]` — PostgreSQL 58-table schema (structured queries via Text-to-SQL)
- `[rag]` — Qdrant vector search (semantic/unstructured)
- `[hybrid]` — combined SQL + RAG (complex multi-hop)

The NRG query pipeline already implements this pattern in `src/orchestration/nodes/planner.py` and `src/skills/text_to_sql/`. Use this skill to guide query decomposition decisions.

## The Goal

Turn this:
```
"What did we decide about the API migration timeline?"
```

Into targeted searches across every connected source:
```
[sql]:  structured query on relevant tables
[rag]:  semantic search "API migration timeline decision"
[docs]: text search "API migration" in relevant workspace
```

Then synthesize results into a single coherent answer (see `knowledge-synthesis` skill).

## Query Decomposition

### Step 1: Identify Query Type

| Query Type | Example | Strategy |
|-----------|---------|----------|
| **Decision** | "What did we decide about X?" | Prioritize conversations, look for conclusion signals |
| **Status** | "What's the status of Project Y?" | Prioritize recent activity, task trackers |
| **Document** | "Where's the spec for Z?" | Prioritize docs, knowledge base |
| **Person** | "Who's working on X?" | Search assignments, authors, collaborators |
| **Factual** | "What's our policy on X?" | Prioritize official docs, then confirmatory sources |
| **Temporal** | "When did X happen?" | Search with broad date range, look for timestamps |
| **Exploratory** | "What do we know about X?" | Broad search across all sources |

### Step 2: Extract Search Components

From the query, extract:
- **Keywords**: Core terms that must appear in results
- **Entities**: People, projects, teams, systems
- **Intent signals**: Decision words, status words, temporal markers
- **Constraints**: Time ranges, source hints, author filters
- **Negations**: Things to exclude

### Step 3: Generate Sub-Queries Per Source

**Prefer semantic/vector search for:**
- Conceptual questions ("What do we think about...")
- Questions where exact keywords are unknown
- Exploratory queries

**Prefer keyword/structured search for:**
- Known terms, project names, IDs
- Exact phrases the user quoted
- Filter-heavy queries

**Generate multiple query variants** when topic may be referred to differently:
```
User: "Kubernetes setup"
Queries: "Kubernetes", "k8s", "cluster", "container orchestration"
```

## Result Ranking

### Relevance Scoring

Score each result (weights by query type):

| Factor | Decision | Status | Document | Factual |
|--------|----------|--------|----------|---------|
| Keyword match | 0.3 | 0.2 | 0.4 | 0.3 |
| Freshness | 0.3 | 0.4 | 0.2 | 0.1 |
| Authority | 0.2 | 0.1 | 0.3 | 0.4 |
| Completeness | 0.2 | 0.3 | 0.1 | 0.2 |

### Authority Hierarchy

**For factual/policy questions:**
```
Official docs > Shared documents > Email announcements > Chat messages
```

**For decision questions:**
```
Meeting notes > Thread conclusions > Email confirmations > Chat messages
```

**For status questions:**
```
Task tracker > Recent activity > Status docs > Updates
```

## Handling Ambiguity

Prefer one focused clarifying question over guessing:

```
Ambiguous: "search for the migration"
→ "I found references to a few migrations. Are you looking for:
   1. The database migration (Project Phoenix)
   2. The cloud migration (AWS → GCP)
   3. The data pipeline migration"
```

Only ask for clarification when:
- There are genuinely distinct interpretations that produce very different results
- The ambiguity significantly affects which sources to search

Do NOT ask when:
- The query is clear enough to produce useful results
- Minor ambiguity can be resolved by returning results from multiple interpretations

## Fallback Strategies

When a source is unavailable or returns no results:

1. **Source unavailable**: Skip it, search remaining sources, note the gap
2. **No results**: Try broader query terms, remove date filters, try alternate keywords
3. **All sources empty**: Suggest query modifications to the user
4. **Rate limited**: Return results from other sources, suggest retrying

### Query Broadening

If initial queries return too few results:
```
Original: "PostgreSQL migration Q2 timeline decision"
Broader:  "PostgreSQL migration"
Broader:  "database migration"
Broadest: "migration"
```

Remove constraints in this order:
1. Date filters
2. Source/location filters
3. Less important keywords
4. Keep only core entity/topic terms

## Parallel Execution

Always execute searches across sources in parallel, never sequentially. Total time ≈ slowest single source, not the sum.

```
[User query]
     ↓ decompose
[source-A query] [source-B query] [source-C query] [source-D query]
     ↓                ↓                ↓                ↓
              (parallel execution)
                       ↓
          [Merge + Rank + Deduplicate]
                       ↓
              [Synthesized answer]
              (→ use knowledge-synthesis skill)
```

## NRG Query Classification Examples

| NRG query | Type | Primary source | Secondary |
|---|---|---|---|
| "Who is doing the best work in solar energy?" | Exploratory | `[rag]` semantic | `[sql]` publication counts |
| "How many patents did IIT Bombay file in 2023?" | Factual | `[sql]` structured | — |
| "Compare Gujarat and Karnataka AI research output" | Temporal + Multi-hop | `[sql]` CTE | `[rag]` context |
| "What TRL stage is most hydrogen research at?" | Status | `[sql]` trl_stages VIEW | `[rag]` context |
| "Find collaborators in nano-materials" | Person | `[rag]` semantic | `[sql]` researchers table |
