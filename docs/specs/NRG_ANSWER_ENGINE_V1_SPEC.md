# NRG Answer Engine v1 Spec

**Status:** Draft implementation spec
**Depends on:** `docs/specs/NRG_PRODUCT_STRATEGY_LOCKED.md`
**Goal:** Build the first general answer-engine milestone: any authorized user asks a natural research-intelligence question, and NRG returns a verified, cited, tier-safe answer with visible proof.

---

## 1. Scope

Answer Engine v1 includes:

- authenticated roles
- query-first Ask workspace
- natural-language planner/router
- safe Text-to-SQL
- scoped RAG
- SQL + RAG hybrid answers
- conversational answer synthesis
- verifier and confidence
- citations and source drawer
- SQL/computation drawer
- audit drawer
- saved answer records
- tier-safe export brief
- acceptance examples as tests, not hardcoded answers

Answer Engine v1 excludes:

- full graph retrieval engine
- full multilingual query/response
- fine-tuned local SLM as primary
- full 600GB production ingest
- external internet browsing/connectors
- full policy-report builder
- complex admin portal
- advanced real-time collaboration

---

## 2. Product Contract

User promise:

> Type a research-intelligence question in natural language. NRG figures out the plan, retrieves evidence, answers conversationally, and proves where the answer came from.

System rule:

> The LLM may plan and explain, but only approved evidence may support factual claims.

If the system cannot prove a complete answer, it must return the best supported partial answer, state missing evidence, and ask one useful clarification if needed.

---

## 3. Architecture

v1 architecture:

```text
User question
  -> Receiver
  -> Sanitizer
  -> Planner
  -> Router
  -> Schema/context retriever
  -> Executor
       -> SQL tool
       -> RAG tool
  -> Synthesizer
  -> Verifier
  -> Response filter
  -> Audit log
  -> UI proof layer
```

Node responsibilities:

| Node | Responsibility | Must output |
|------|----------------|-------------|
| Receiver | Attach user, tier, session, query ID, history | `query_id`, `session_id`, `tier`, `raw_question` |
| Sanitizer | Block PII, prompt injection, unsafe export, tier-unsafe intent | clean query or blocked response |
| Planner | Interpret intent, defaults, sub-questions, follow-up context | plan, assumptions, active domain |
| Router | Choose SQL, RAG, or hybrid | route, route confidence |
| Schema retriever | Provide only relevant schema/context to SQL generator | tables, columns, joins, business terms |
| Executor | Run read-only SQL and/or vector search | source rows/chunks and metadata |
| Synthesizer | Write conversational answer from evidence | answer draft with citations |
| Verifier | Check grounding, tier safety, citations, confidence | verified answer or repair/clarify result |
| Response filter | Apply final tier shape and masking | tier-safe payload |
| Audit | Persist tamper-evident event | `audit_event_id`, chain status |

---

## 4. Query Lifecycle

Every successful query should follow this lifecycle:

1. User submits natural language.
2. UI shows progress within 200 ms.
3. Sanitizer blocks unsafe input before retrieval.
4. Planner infers defaults where safe.
5. Router selects SQL, RAG, or hybrid.
6. Executor retrieves evidence.
7. Synthesizer writes answer from evidence only.
8. Verifier checks grounding and tier safety.
9. Response filter masks/removes forbidden fields.
10. Audit event is persisted.
11. UI renders answer plus proof controls.
12. Answer Record is saved for history/follow-up.

Human progress labels:

- Understanding your question
- Planning retrieval
- Searching research records
- Checking documents
- Synthesizing answer
- Verifying sources

No query should show a blank state after submit.

---

## 5. Retrieval Routing

| Route | Use when | Examples |
|-------|----------|----------|
| SQL | Exact data, counts, rankings, filters, trends | "Top institutes by clean-energy funding" |
| RAG | Abstracts, reports, summaries, themes, explanations | "What themes appear in hydrogen catalysis abstracts?" |
| Hybrid | Structured ranking plus document meaning | "Who has clean-energy capability and recent funded projects?" |
| Clarify | Query is materially ambiguous or unsafe to answer | "Best by what metric?" only when no safe default exists |
| Block | PII request, prompt injection, forbidden export, tier violation | "Show researcher phone numbers" |

Default ambiguity rules:

- "best" = transparent composite score unless user specifies metric.
- missing time range = recent five years.
- broad query = scoped answer plus refinement chips.
- restricted query = safe aggregate alternative when possible.

---

## 6. SQL Safety

AI-generated SQL must never run directly without checks.

Required safeguards:

- read-only execution
- allowlisted statements only
- no destructive commands
- timeout
- row limit
- identifier validation
- schema-aware generation
- tier column allowlist
- PII column denylist
- parameterization where possible
- audit of SQL text and result metadata

SQL output must be shaped by tier before it reaches the frontend.

---

## 7. RAG Scope

v1 RAG should index a controlled document set:

- abstracts
- publication snippets where legally available
- project summaries
- policy/report snippets where available

Each chunk must have:

- source document ID
- title
- chunk ID
- text excerpt
- metadata
- access classification
- index timestamp

RAG can support explanation and thematic synthesis. It must not override structured DB totals for exact numbers.

---

## 8. Answer Payload

All answer endpoints should converge on this payload shape, even if streaming delivers it in phases:

```json
{
  "query_id": "string",
  "answer_id": "string",
  "audit_event_id": "string",
  "tier": "researcher|government|industry",
  "question": "string",
  "interpreted_question": "string",
  "assumptions": ["string"],
  "route": "sql|rag|hybrid|clarify|blocked",
  "final_answer": "string",
  "confidence": {
    "level": "high|medium|low|needs_clarification",
    "reason": "string"
  },
  "citations": [
    {
      "id": "1",
      "source_type": "sql_row|document_chunk|graph_edge",
      "label": "string",
      "source_id": "string",
      "masked": false
    }
  ],
  "source_data": {
    "sql_query": "string|null",
    "rows": [],
    "documents": []
  },
  "freshness": {
    "database_snapshot": "string|null",
    "document_indexed_at": "string|null",
    "warning": "string|null"
  },
  "caveats": ["string"],
  "follow_up_suggestions": ["string"],
  "query_time_ms": 0
}
```

Blocked responses must use the same envelope where possible, with `route = "blocked"` and a safe `final_answer`.

---

## 9. Verifier And Confidence

Confidence is evidence quality.

| Level | Meaning |
|-------|---------|
| High | Sources are complete, citations present, verifier passes, no material caveats |
| Medium | Answer is supported, but coverage or freshness is imperfect |
| Low | Partial evidence only; answer must be cautious |
| Needs clarification | Safe useful answer is not possible without user input |

Verifier checks:

- every numeric claim is present in evidence or computed from evidence
- every factual claim has a citation when appropriate
- answer does not claim beyond the data
- SQL columns match tier allowlist
- source rows/chunks are accessible to the tier
- PII is masked or removed
- low/empty results produce honest caveats
- material SQL/RAG conflicts appear as caveats

---

## 10. UI Contract

Primary navigation:

- Ask
- Answers
- Sources
- Graph Preview
- Audit
- Settings

Default landing after login: Ask workspace.

Ask workspace must show:

- product name
- tier badge
- one large natural-language query input
- tier-specific suggestion chips
- real scale/freshness strip
- recent/saved answer records below

Answer page must show:

- original question
- interpreted assumptions
- confidence
- conversational answer
- citations
- useful table/chart when relevant
- Source Data button
- View SQL/Computation button
- View Audit Event button
- follow-up input

Proof drawers must open without navigating away from the answer.

---

## 11. Tier Rules

Tier filtering must happen before data reaches the frontend.

| Tier | v1 behavior |
|------|-------------|
| Researcher | Show research details and limited personal information only when policy allows |
| Government | Show aggregates plus named institutions/labs; avoid individual personal details by default |
| Industry | Show institution/lab capability and partnership signals; show researcher names/emails only when explicitly allowed |

PII requests should return safe alternatives:

> I cannot show personal contact data for this role. I can show institutions, labs, public contact routes, or aggregate counts instead.

Blocked queries must be audited without storing unnecessary raw sensitive values.

---

## 12. Saved Answers, Follow-Ups, And Exports

Every successful answer becomes an Answer Record:

- original question
- interpreted question
- assumptions
- final answer
- citations
- route
- confidence
- tier
- audit event ID
- freshness
- timestamp
- follow-up thread

Follow-ups preserve topic, tier, filters, and source context. They re-query when facts or filters change.

Exports:

- PDF brief
- CSV for visible rows only
- citation bundle
- audit summary

Exports must be tier-safe.

---

## 13. Observability

Track:

- query count
- route distribution
- query latency
- confidence distribution
- blocked query count
- tier denial count
- citation failure count
- verifier failure count
- LLM provider latency/errors
- cache hit rate
- stale data warnings
- audit chain verification status

Users see confidence, freshness, and audit status. Admins see full operational dashboards.

---

## 14. Performance Targets

v1 targets:

- UI feedback after submit: under 200 ms
- login: under 2 s
- Ask workspace: under 3 s
- warm answer start: under 1 s
- warm answer complete: under 3 s
- cold answer: progress immediately, target under 8 s
- source drawer: under 500 ms
- audit drawer: under 500 ms

Heavy queries may take longer only if progress is visible and cancellation/retry are available.

Cache keys must include tier and policy context.

---

## 15. Acceptance Tests

v1 acceptance examples are tests, not hardcoded product limits:

- TRL bottleneck: "Where are clean-energy innovations getting stuck before commercialization?"
- Patent efficiency: "Which institutes produce the most granted patents per INR 10 Cr government funding?"
- Funding-output mismatch: "Which institutes received more funding but produced fewer outputs over 5 years?"
- Hidden collaboration network: "Which institutions connect hydrogen catalysis researchers across states?"
- Underfunded strength: "Which states have strong AI publication growth but low funding support?"

Weekly test walk:

- run at least 10 natural-language questions
- at least 7 produce good answers with proof
- Tier 1 and Tier 3 outputs differ safely
- blocked PII query is handled cleanly
- no raw JSON, traceback, `undefined`, `null`, or `NaN` appears
- citations/source drawer/audit drawer work
- confidence and freshness render
- screenshots or recording saved

Good answer criteria:

- directly answers the question
- states assumptions
- uses the right route
- cites claims
- formats numbers clearly
- includes confidence
- shows caveats
- respects tier
- suggests useful follow-up
- contains no hallucinated facts

Failure criteria:

- unsupported factual answer
- missing proof path
- wrong tier leakage
- misleading confidence
- wrong retrieval route when evidence exists
- long silent wait
- raw error visible to user

---

## 16. Evidence Requirements

For v1 completion, capture:

- login screenshot for each tier
- Ask workspace screenshot
- streaming/progress screenshot or recording
- final answer screenshot
- source drawer screenshot
- SQL/computation drawer screenshot
- audit drawer screenshot
- Tier 1 vs Tier 3 same-query comparison
- blocked PII query screenshot
- weekly acceptance report
- test command outputs

No completion claim should be made without fresh evidence.
