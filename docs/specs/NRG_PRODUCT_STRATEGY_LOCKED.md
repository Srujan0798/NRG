# NRG Product Strategy - Locked Direction

**Status:** Locked strategy baseline
**Purpose:** Keep the product direction clear before implementation work continues.

---

## 1. Product Definition

NRG is a **general AI research-intelligence answer engine** over national research data.

It is not a fixed prewritten-query product, chatbot, dashboard, or Google clone. The user can type a natural-language question, and NRG decides how to answer it using approved data, retrieval tools, verification, role-based access, and visible proof.

**Product promise:** Ask any research-intelligence question. NRG finds the evidence, explains the answer, and proves where it came from.

**Internal mission:** Build the system where any authorized user can ask India's research database a natural question and receive a verified, cited, tier-safe answer.

**External pitch:** NRG turns India's research data into verified, sovereign intelligence for researchers, government, and industry.

---

## 2. Core Mental Model

**The user asks like a human. NRG thinks like an analyst. The answer comes back like an audited report.**

Architecture slogan:

> LLM plans. Tools retrieve. Verifier proves. UI explains.

Safety slogan:

> The model may reason, but only evidence may speak.

UX slogan:

> Ask like chat. Trust like audit. Use like intelligence software.

---

## 3. Non-Negotiable Principles

- The user should be able to type any natural research-intelligence question.
- The LLM plans, reasons, routes, and explains; it is not the factual source of truth.
- Factual claims must come from approved evidence: SQL rows, RAG chunks, graph relationships, or controlled source connectors.
- If evidence is complete, NRG answers directly.
- If evidence is partial, NRG gives the partial answer, states what is missing, and asks one useful clarification if needed.
- If the query is unsafe or restricted, NRG blocks it, explains plainly, and offers a safe alternative.
- Tier restrictions are enforced in the database/API/backend first. The frontend explains restrictions; it is not the privacy boundary.
- Every serious answer must expose proof: citations, confidence, assumptions, source data, freshness, and audit event.
- Dashboards support the answer engine; they do not replace it.
- Fine-tuning is a future optimization, not the Phase 1 foundation.

---

## 4. Users And Access

| Tier | Primary job | Default visibility | Restricted by default |
|------|-------------|--------------------|-----------------------|
| Tier 1 Researcher | Find peers, collaborators, publications, labs, and institution standing | Researcher names, institutions, research areas, publications, labs, collaborations, limited contact details only if allowed | Aadhaar, PAN, phone numbers, unnecessary sensitive personal fields |
| Tier 2 Government | Understand policy trends, funding gaps, institution capacity, and commercialization pipeline | Aggregates, named institutions/labs, state trends, funding amounts, project counts, TRL stages | Individual personal details unless explicitly authorized |
| Tier 3 Industry | Discover capability and partnership opportunities | Institution/lab names, capability areas, TRL/patent signals, official contact route | Personal contact dumps, sensitive personal data, unrestricted raw rows |

Industry can see researcher names/emails only when licensing, consent, or official policy explicitly permits it.

---

## 5. Answer Behavior

NRG should answer conversationally on top and show proof underneath.

Default answer shape:

- direct conversational answer
- assumptions/defaults used
- citations
- confidence pill
- freshness indicator
- caveats when needed
- table or chart only when useful
- buttons for Source Data, SQL/Computation, and Audit Event
- follow-up input

Ambiguity policy:

- "best" becomes a transparent scoring method.
- Missing time range defaults to recent five years unless context says otherwise.
- Broad queries get a scoped answer plus refinement options.
- The system asks clarifying questions only when answering would be unsafe, misleading, or materially ambiguous.

Confidence means **evidence quality**, not model confidence.

---

## 6. Retrieval And Intelligence

The north-star intelligence core has five retrieval/knowledge paths:

1. **SQL retriever** - exact structured data, counts, trends, rankings, records.
2. **RAG retriever** - documents, abstracts, reports, project descriptions, and textual meaning.
3. **Graph retriever** - collaborations, capability clusters, funding-to-output paths, TRL progression, institutional networks.
4. **Model memory** - future fine-tuned local model that understands NRG patterns and schema.
5. **Controlled connectors** - future official external sources only, labeled and cited.

All paths feed the synthesizer, verifier, proof UI, and audit chain.

Structured DB is the source of truth for exact numbers. RAG can explain document meaning. If SQL and RAG disagree on exact numbers, SQL wins and the disagreement appears as a caveat when material.

---

## 7. UX Direction

Visual feel: **premium enterprise intelligence tool with query-first AI simplicity**.

The product should not feel like:

- a government form
- a casual chatbot
- a dashboard cluttered with cards
- a marketing landing page

The first authenticated screen should show:

- National Research Graph
- "Sovereign intelligence over India's research ecosystem"
- current tier badge
- one large query box: "Ask India's research database anything..."
- tier-specific suggestion chips
- scale/freshness strip with real counts

Product behavior:

> Ask like chat, retrieve like search/database/graph, answer like a report.

---

## 8. Roadmap

### v1 - NRG Answer Engine

Build the core loop:

- login and roles
- Ask workspace
- planner/router
- safe Text-to-SQL
- scoped RAG
- hybrid SQL + RAG answers
- conversational synthesis
- verifier
- citations
- source drawer
- SQL/computation drawer
- audit drawer
- confidence and freshness
- saved answer records
- tier-safe outputs
- export brief
- acceptance examples as tests only

v1 excludes full graph, full multilingual, fine-tuned SLM, full 600GB ingest, full policy-report builder, external connectors, complex admin portal, and advanced collaboration.

### v2 - NRG Graph Intelligence

Add graph retrieval and graph answers for collaboration, capability, funding, TRL, and network questions.

### v3 - NRG Multilingual + Policy Reports

Add Indian language query/response, policy report generation, report templates, and stronger government workflows.

### v4 - NRG Sovereign Model

Add local SLM primary mode, fine-tuned NRG model, shadow evaluation, cost/latency optimization, and strict sovereign model governance.

### v5 - NRG Production Sovereign Platform

Add controlled deployment, real data ingestion, monitoring, alerts, backup/restore, red-team testing, operations runbooks, signed handover, formal UAT, and compliance evidence.

---

## 9. First Build Priority

The first build workstream is:

> Ask -> Answer -> Proof

Build/refine this before graph UI, landing pages, fine-tuning, multilingual UI, complex dashboards, or production deployment.

Minimum weekly acceptance walk:

- Ask 10 natural questions.
- At least 7 answer well with proof.
- No PII leakage.
- No raw errors.
- Tier outputs differ safely.
- Source/audit inspection works.
- Latency is acceptable and progress is visible.
- Evidence is recorded with screenshots or video.

---

## 10. Canonical Docs

Use this order as the project truth hierarchy:

1. `Core_Idea_Clean.md` - first-read master idea.
2. `docs/specs/NRG_PRODUCT_STRATEGY_LOCKED.md` - locked product decisions.
3. `docs/specs/NRG_ANSWER_ENGINE_V1_SPEC.md` - implementation-ready v1 spec.
4. Implementation plans under `docs/superpowers/plans/`.
5. Evidence reports under `evidence/`.

Older specs should be marked active, superseded, or reference-only before deletion is considered.
