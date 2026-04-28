---
name: knowledge-synthesis
description: Combines search results from multiple sources into coherent, deduplicated answers with source attribution. Handles confidence scoring based on freshness and authority, and summarizes large result sets effectively.
user-invocable: false
model-agnostic: true
---

# Knowledge Synthesis

The last mile of multi-source search. Takes raw results from multiple sources and produces a coherent, trustworthy answer.

> **Model-agnostic:** Works with any LLM that supports tool use (Claude, GPT-4, Gemini, Grok, local models).
> Source connectors are denoted as `[source-type]` — replace with whatever data sources are connected (database, vector store, chat logs, documents, APIs, etc.).

## The Goal

Transform this:
```
[chat] result: "Sarah said: 'let's go with REST, GraphQL is overkill for our use case'"
[email] result: "Subject: API Decision — Sarah's email confirming REST approach with rationale"
[documents] result: "API Design Doc v3 — updated section 2 to reflect REST decision"
[task-tracker] result: "Task: Finalize API approach — marked complete by Sarah"
```

Into this:
```
The team decided to go with REST over GraphQL for the API redesign. Sarah made the
call, noting that GraphQL was overkill for the current use case. This was discussed
in the engineering chat, confirmed via email, and the design doc has been updated.
The related task is marked complete.

Sources:
- [chat]: engineering thread (Jan 14)
- [email]: "API Decision" from Sarah (Jan 15)
- [documents]: "API Design Doc v3" (updated Jan 15)
- [task-tracker]: "Finalize API approach" (completed Jan 15)
```

## For NRG Specifically

When used in NRG, sources are:
- `[sql]` — PostgreSQL query results (58-table schema)
- `[rag]` — Qdrant vector search results
- `[audit]` — HMAC audit chain entries
- `[schema]` — db_struct.sql schema context

## Deduplication

### Cross-Source Deduplication

The same information often appears in multiple places. Merge duplicates:

**Signals that results are about the same thing:**
- Same or very similar text content
- Same author/sender
- Timestamps within a short window
- References to the same entity (project, document, decision)
- One source references another

**How to merge:**
- Combine into a single narrative item
- Cite all sources where it appeared
- Use the most complete version as the primary text
- Add unique details from each source

### Deduplication Priority

When the same information exists in multiple sources, prefer:
```
1. Most complete version (fullest context)
2. Most authoritative source (official doc > chat)
3. Most recent version (latest update wins for evolving info)
```

### What NOT to Deduplicate

Keep as separate items when:
- The same topic is discussed but with different conclusions
- Different people express different viewpoints
- Information evolved meaningfully between sources
- Different time periods are represented

## Citation and Source Attribution

Every claim in the synthesized answer must be attributable to a source.

### Attribution Format

Inline for direct references:
```
Sarah confirmed the REST approach in her email on Wednesday.
The design doc was updated to reflect this ([documents]: "API Design Doc v3").
```

Source list at the end:
```
Sources:
- [chat]: #engineering discussion (Jan 14) — initial decision thread
- [email]: "API Decision" from Sarah (Jan 15) — formal confirmation
- [documents]: "API Design Doc v3" last modified Jan 15 — updated specification
```

### Attribution Rules
- Always name the source type
- Include specific location (channel, folder, thread, table name)
- Include the date or relative time
- Include the author when relevant
- Include document/thread titles when available

## Confidence Levels

### Freshness

| Recency | Confidence impact |
|---------|------------------|
| Today / yesterday | High confidence for current state |
| This week | Good confidence |
| This month | Moderate — things may have changed |
| Older than a month | Lower — flag as potentially outdated |

For status queries: heavily weight freshness.
For policy/factual queries: freshness matters less.

### Authority

| Source type | Authority level |
|-------------|----------------|
| Official docs / knowledge base | Highest |
| Shared documents (final versions) | High |
| Email announcements | High |
| Meeting notes | Moderate-high |
| Chat conclusions | Moderate |
| Chat mid-thread | Lower |
| Draft documents | Low |

### Expressing Confidence

High confidence:
```
The team decided to use REST for the API redesign. [direct statement]
```

Moderate confidence:
```
Based on the discussion last month, the team was leaning toward REST.
This may have evolved since then.
```

Low confidence:
```
I found a reference from three months ago but couldn't find a formal decision document.
You may want to verify current status.
```

### Conflicting Information

Always surface conflicts rather than silently picking one:
```
I found conflicting information:
- The chat on Jan 10 suggested GraphQL
- But Sarah's email on Jan 15 confirmed REST
- The design doc (updated Jan 15) reflects REST

The most recent sources indicate REST was the final decision.
```

## Summarization Strategies

### Small Result Sets (1–5 results)
Present each result with context. No summarization needed.

### Medium Result Sets (5–15 results)
Group by theme, summarize each group. List top 3–5 most relevant sources.

### Large Result Sets (15+ results)
High-level synthesis with drill-down offer:
```
[Overall answer]

Summary:
- [Key finding 1] (supported by N sources)
- [Key finding 2] (supported by N sources)

Top sources: [list]
Found [total] results across [source list].
Want me to dig deeper into any specific aspect?
```

### Rules
- Lead with the answer, not the search process
- Do not list raw results — synthesize into narrative
- Group related items from different sources together
- Preserve important nuance and caveats
- Always offer to provide more detail for large result sets

## Synthesis Workflow

```
[Raw results from all sources]
          ↓
[1. Deduplicate — merge same info from different sources]
          ↓
[2. Cluster — group related results by theme/topic]
          ↓
[3. Rank — order by relevance to query]
          ↓
[4. Assess confidence — freshness × authority × agreement]
          ↓
[5. Synthesize — produce narrative answer with attribution]
          ↓
[6. Format — choose detail level for result count]
          ↓
[Coherent answer with sources]
```

## Anti-Patterns

**Do not:**
- List results source-by-source without synthesizing
- Include irrelevant results because they keyword-matched
- Bury the answer under methodology
- Present conflicting info without flagging the conflict
- Omit source attribution
- Present uncertain info with same confidence as well-supported facts
- Over-summarize so useful detail is lost

**Do:**
- Lead with the answer
- Group by topic, not by source
- Flag confidence levels when appropriate
- Surface conflicts explicitly
- Attribute all claims to sources
- Offer to go deeper when result sets are large
