# NRG — National Research Graph

## The One-Line Version

> A professor types "Who is doing the best research in hydrogen catalysis?" — and the system figures out everything else on its own, from a 600GB government database, without leaking a single byte.

---

## Origin

This project comes from a real conversation at IIT Gandhinagar. A stakeholder said:

> "We can't expect the user to know everything. They'll just ask 'who is working best in hydrogen catalysis?' — it could be all-time, could be last five years. The AI has to figure that out. Can you build it?"

That's the core challenge. Not a chatbot. Not a search engine. A system that **understands ambiguous questions** and gives **verified, structured, cited answers** from India's national research database.

---

## What This Project Is

**NOT**: A chatbot, a Google clone, or a simple database query tool.

**YES**: A **National Research Intelligence Platform** — the "Research OS of India."

- **Dataset**: 600GB confidential database of researchers, labs, publications, funding across India
- **Backing**: IIT Gandhinagar as execution node, ~40 crore government funding (Gujarat)
- **Mandate**: Build the interface that unlocks this data securely and intelligently
- **National alignment**: IndiaAI Mission, ANRF (Anusandhan National Research Foundation), Sovereign AI initiative

---

## The 3 Users

The same database serves three audiences. Each sees only what they're allowed to see — like three windows into the same room.

| Persona | What they ask | What they see |
|---------|--------------|---------------|
| **Researcher** (Tier 1) | "Show me peers in my field, their papers, contact info" | Full details — names, emails, publications, lab info |
| **Government** (Tier 2) | "State-wise research trends, funding gaps, institutional capacity" | Aggregated stats, anonymized summaries, policy-ready reports |
| **Industry** (Tier 3) | "Who has capability in X for partnership?" | Names and research areas only — no personal info, licensed access |

---

## How It Works (Plain English)

When a user asks a question, six things happen:

### Step 1 — Identity Check
The user logs in with their role (researcher / government / industry). The system gives them a digital pass (JWT token) that expires in 1 hour. This pass determines what data they can see.

### Step 2 — Safety Scan
Before touching any data, the system scans the question:
- Contains Aadhaar, PAN, phone number, or email? → **Blocked** (PII protection)
- Trying to trick the AI ("ignore all rules")? → **Blocked** (injection detection)
- Clean question? → Proceed

### Step 3 — Understanding the Question
The system reads the question and classifies it:
- **"Find researchers in Gujarat"** → Looking for specific data → **Search the database**
- **"What are the trends in AI research?"** → Looking for knowledge → **Search research documents**
- **"Synthesize robotics funding data"** → Both → **Search database AND documents**

### Step 4 — Fetching the Data
Two parallel paths:
- **Structured path (Text-to-SQL)**: Automatically writes a database query from natural language. "Find robotics researchers in Gujarat" becomes `SELECT * FROM researchers WHERE state='Gujarat' AND research_area='Robotics'`
- **Unstructured path (RAG)**: Searches inside research papers and abstracts using semantic similarity (vector search)

### Step 5 — Writing the Answer
Three-tier cascade — tries the best option, falls back gracefully:
1. **Cloud LLM** (Gemini/Claude) — natural language synthesis (data never leaves, only retrieved facts go out)
2. **Local SLM** (Llama 3 8B on our own machine) — simpler but fully offline
3. **Rule-based formatting** — organized tables, always works, no AI needed

### Step 6 — Verification + Delivery
A verification step cross-references the answer against source data to catch hallucinations. The verified answer appears on the user's dashboard. Every step is recorded in a tamper-proof audit log.

---

## The 5-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: INTERFACE                                     │
│  React web app — login, dashboards, natural language     │
│  search bar, structured results, visualizations          │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  LAYER 4: REASONING                                     │
│  LLM synthesis (cloud or local) — interprets data,      │
│  writes answers, verifies claims against evidence        │
│  ⚠️ NO raw data sent to cloud — only retrieved facts    │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  LAYER 3: RETRIEVAL                                     │
│  Dual-path search:                                       │
│  • Text-to-SQL → structured database queries             │
│  • RAG → semantic vector search in documents             │
│  • Hybrid → both paths combined                          │
│  Intent router decides which path(s) to take             │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  LAYER 2: KNOWLEDGE                                     │
│  Structured data: researchers, labs, publications,       │
│  institutions, funding, keywords, collaborations         │
│  Future: knowledge graph (who collaborates with whom)    │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  LAYER 1: DATA                                          │
│  600GB raw dataset — lives on IIT-GN / gov servers      │
│  Never leaves controlled infrastructure                  │
│  Cleaning, structuring, indexing                         │
└─────────────────────────────────────────────────────────┘
```

---

## Security Model: Zero-Data-Leakage

The core principle: **"The 600GB repository resides exclusively on Indian servers. The system is architecturally incapable of uploading data to the internet."**

Think of it like a government building:

| Layer | What it does | Analogy |
|-------|-------------|---------|
| **Front gate** | JWT login — verify identity | Show your ID card |
| **Bag scan** | PII detection + prompt injection blocking | Security screening |
| **Floor access** | RBAC — tier 1/2/3 see different data | Badge color decides which floors you enter |
| **CCTV** | HMAC-chained audit log — every action recorded, tamper-proof | Every door you open is logged |
| **Data vault** | Data never leaves local servers — cloud LLM gets only retrieved facts, not raw data | Vault stays locked, you get photocopies |

### What NEVER leaves the local boundary:
- The 600GB research database
- Retrieved facts and document chunks
- Synthesized content
- Researcher PII (Aadhaar, phone, email)

### What goes to cloud LLM (when used):
- Only: the user's question + retrieved facts for synthesis
- NOT: raw database, schemas, or sensitive metadata
- The local SLM option sends nothing outside at all

### Regulatory compliance:
- DPDP Act 2023 (Digital Personal Data Protection)
- Data minimization, purpose limitation, consent
- Role-based access at database level

---

## Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Orchestration** | LangGraph | Deterministic graph-based workflows, state persistence, error recovery |
| **Backend** | FastAPI (Python) | High-performance async API |
| **Frontend** | React + Vite + Tailwind | Modern, fast, component-based UI |
| **Relational DB** | SQLite (Phase 1) → PostgreSQL (Phase 2) | ACID-compliant structured data |
| **Vector DB** | Qdrant | Rust-based, sub-20ms latency, native metadata filtering |
| **Cloud LLM** | Gemini / Claude / GPT-4o / NVIDIA (mesh with fallback) | Reasoning and synthesis |
| **Local SLM** | Llama 3 8B (quantized, via llama.cpp) | Fully offline synthesis |
| **Auth** | JWT RS256 | Asymmetric token signing |
| **API Gateway** | Kong | DLP, rate limiting, prompt inspection |
| **Embeddings** | sentence-transformers (local) | Offline vector generation |
| **Audit** | HMAC-SHA256 chained log | Tamper-proof, immutable |
| **Caching** | Redis | Query result caching (graceful degradation) |
| **PII Detection** | Custom regex (Aadhaar, PAN, phone, email) | Indian-specific PII patterns |

---

## The LangGraph Pipeline

Every query flows through 6 nodes in sequence:

```
USER QUERY
    │
    ▼
┌──────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐   ┌──────────┐
│ RECEIVER │──▶│ PLANNER │──▶│  ROUTER  │──▶│ EXECUTOR │──▶│ SYNTHESIZER │──▶│ VERIFIER │
└──────────┘   └─────────┘   └──────────┘   └──────────┘   └─────────────┘   └──────────┘
     │              │              │              │                │                │
  Assigns ID   Decomposes    Classifies:    Runs skills:     Writes answer:   Checks citations
  Loads session query into   • structured   • Text-to-SQL    1st: Cloud LLM   against evidence
  history      sub-queries   • unstructured • RAG            2nd: Local SLM   Retries if
               + schema      • hybrid       • Both           3rd: Rule-based  unsupported
```

### Router Logic:
- Words like "find", "list", "count", "how many" → **structured** → Text-to-SQL
- Words like "trends", "explain", "what are" → **unstructured** → RAG
- Words like "synthesize", "combine" → **hybrid** → Both paths

### Executor:
- **Text-to-SQL**: Extracts states, research areas, years from query → builds SQL → executes in read-only sandbox → returns rows
- **RAG**: Embeds query → searches Qdrant → returns relevant document chunks
- Both paths run independently, failures are caught and logged

### Synthesizer:
- Combines SQL results + document chunks
- Tries cloud LLM → local SLM → rule-based tables (always succeeds)
- Verification step checks for hallucinations
- Every synthesis path is audit-logged

---

## Data Model

```
researchers (200)          publications (500)        institutions (24)
├── researcher_id          ├── publication_id         ├── institution_id
├── name                   ├── title                  ├── name
├── email                  ├── year                   ├── state
├── phone                  ├── authors                └── type
├── state                  └── abstract
├── research_area
├── institution_id         labs (50)                  funding_records (100)
└── year_joined            ├── lab_id                 ├── funding_id
                           ├── name                   ├── amount
Junction tables:           ├── research_area          ├── source
• researcher_publications  └── institution_id         └── researcher_id
• researcher_labs
• publication_keywords
• keywords
```

Currently: SQLite with synthetic data (200 researchers, 500 publications).
Production: PostgreSQL with 600GB real data, Row-Level Security, full-text search.

---

## What's the Difference vs Google/Wikipedia?

| Aspect | Google / Wikipedia | NRG |
|--------|-------------------|-----|
| **Data** | Public, unverified | Curated, government-backed, confidential |
| **Structure** | Unstructured links | Structured profiles, tables, insights |
| **Trust** | Low — anyone can edit | High — IIT-backed, audit-trailed |
| **Output** | Links and dumps | Verified answers with citations |
| **Ownership** | External (US companies) | National (Indian servers) |
| **Intelligence** | Keyword matching | Semantic understanding + reasoning |

---

## Roadmap

### Phase 1: Working Demo (Months 1-2) — **WE ARE HERE**
- [x] LangGraph pipeline (receiver → router → executor → synthesizer)
- [x] Text-to-SQL with fallback SQL generation
- [x] JWT RS256 auth with 3 tiers
- [x] RBAC middleware (different views per role)
- [x] Security: PII detection, prompt injection blocking
- [x] HMAC audit chain
- [x] React frontend with 3 dashboards
- [x] Redis caching (graceful degradation)
- [x] Rule-based synthesis (always works without LLM)
- [ ] Real LLM API key for intelligent synthesis
- [ ] RAG path (Qdrant + embeddings)
- [ ] Ambiguity resolution (the core AI challenge)

### Phase 2: Full Data + Intelligence (Months 3-5)
- [ ] Migrate to PostgreSQL with RLS
- [ ] Ingest 600GB real dataset
- [ ] Qdrant cluster + semantic chunking + batch embedding
- [ ] Knowledge graph (researcher collaborations, topic networks)
- [ ] LLM-powered SQL generation (replace regex fallback)
- [ ] Citation engine (every claim linked to source)
- [ ] Local Llama 3 8B for fully offline synthesis
- [ ] Verifier node (faithfulness judge)

### Phase 3: Production Deployment (Months 6-8)
- [ ] Kong API Gateway (DLP, rate limiting)
- [ ] Deploy on sovereign infrastructure (NIC/MeitY)
- [ ] Red-team security testing
- [ ] UAT with all three user groups
- [ ] Performance: sub-second latency, 1000+ concurrent users
- [ ] Multi-language support (Hindi, Tamil, etc.)
- [ ] Documentation, pitch deck, proposal for national scale

---

## The Core AI Challenge (What Makes This Hard)

The person who commissioned this said the AI must "figure it out" on its own. This means:

1. **Ambiguity resolution**: "Who is best in hydrogen catalysis?" → Best by what metric? All-time or recent? Which institutions? The system must decide.

2. **Multi-hop reasoning**: "Compare Gujarat and Karnataka's AI research output over 5 years" → needs multiple database queries, aggregation, and synthesis.

3. **Verification**: Every claim must trace back to source data. No hallucinations allowed — this is government-backed, trusted data.

4. **Zero leakage**: 600GB of confidential data must never leave Indian servers. Cloud AI is used for reasoning only, never for storage.

These are unsolved-in-production problems. The architecture handles them, but the intelligence layer (LLM + knowledge graph + verification) is what turns this from a database tool into a research intelligence platform.

---

## The Endgame Vision: A Fine-Tuned Model That "Lives Inside" the Data

The current architecture (RAG + Text-to-SQL + cloud LLM) is the **Phase 1-3 approach** — it works, it's safe, it ships fast. But the long-term vision is fundamentally different and more ambitious:

> **We don't want a system that looks things up every time. We want a model that has deeply internalized the entire dataset — its structure, relationships, and content — the way Claude knows its training data. Then it uses live database access only for precise, up-to-date specifics.**

### Why RAG Alone Won't Scale

At the full scale of this project (~1 TB of data, thousands of queries/day), pure retrieval-based approaches hit hard walls:

| Problem | RAG/Retrieval Approach | Fine-Tuned Model |
|---------|----------------------|------------------|
| **Latency** | Every query = embed + search + retrieve + synthesize | Instant — knowledge is in the weights |
| **Cost** | Cloud LLM API calls on every query, every day | One-time training cost, then local inference |
| **Reliability** | Depends on retrieval quality, chunk boundaries, embedding drift | Robust — understanding is baked in |
| **Reasoning** | Can only reason over what was retrieved | Can reason over the entire dataset holistically |
| **Ambiguity** | Struggles with vague questions (what to retrieve?) | Understands the data well enough to infer intent |

### The "Expert Salesman" Mental Model

Think of the ideal system like an **expert salesman who has worked with the product catalog for 20 years**:

- **Ask them a general question** ("What's our strongest offering in renewable energy?") → They answer instantly from deep knowledge, no need to look anything up.
- **Ask them for exact specs** ("What's the precise h-index and publication list for Dr. Sharma?") → They pull up the exact record from the system and give you the full specification card.

**Built-in intuition for the whole dataset + seamless live retrieval when precision matters.**

### Architecture: Two-Brain System

```
┌─────────────────────────────────────────────────────────────┐
│                     USER QUESTION                           │
│     "Who is leading hydrogen catalysis research?"           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   FINE-TUNED LOCAL MODEL                     │
│              (Internalized 1TB of data knowledge)            │
│                                                              │
│  The model ALREADY KNOWS:                                    │
│  • Which researchers work on what                            │
│  • Which institutions are strong in which areas              │
│  • Collaboration networks, funding patterns                  │
│  • Historical trends, geographic distribution                │
│                                                              │
│  It answers general/analytical questions INSTANTLY            │
│  from its internalized knowledge — no retrieval needed        │
└──────────────────────┬───────────────────────────────────────┘
                       │
          Does the question need exact/live data?
                       │
            ┌──────────┴──────────┐
            │ NO                  │ YES
            │ General/analytical  │ Specific record,
            │ question            │ exact stats, live data
            ▼                     ▼
   ┌──────────────┐    ┌──────────────────────────┐
   │ DIRECT ANSWER │    │ LIVE DATABASE RETRIEVAL   │
   │ from model's  │    │ SQL query for exact data  │
   │ internalized  │    │ Returns specification     │
   │ knowledge     │    │ card / precise facts      │
   └──────────────┘    └──────────────────────────┘
            │                     │
            └──────────┬──────────┘
                       ▼
              ┌────────────────┐
              │ MERGED ANSWER  │
              │ Deep insight + │
              │ exact evidence │
              └────────────────┘
```

### How to Build This: Reinforcement Learning Loop

The model doesn't just memorize — it **learns to understand** via an RL loop:

```
┌─────────────────────────────────────────────────────┐
│            REINFORCEMENT LEARNING LOOP               │
│                                                     │
│  1. EXPLORE                                         │
│     Model interacts with data + schema repeatedly    │
│     Generates Q&A pairs, explores relationships      │
│                                                     │
│  2. EVALUATE                                        │
│     Each answer is checked against ground truth:     │
│     • Did it get the structure right?               │
│     • Did it infer correct relationships?           │
│     • Did it handle edge cases?                     │
│     • Is the answer factually accurate?             │
│                                                     │
│  3. REWARD                                          │
│     Correct understanding     → positive signal     │
│     Hallucination / wrong     → negative signal     │
│     Novel insight from data   → bonus reward        │
│                                                     │
│  4. ITERATE                                         │
│     Model improves over cycles                      │
│     Develops genuine comprehension                   │
│     Eventually "lives inside" the dataset            │
└─────────────────────────────────────────────────────┘
```

### Candidate Base Models for Fine-Tuning

| Model | Parameters | Why Consider |
|-------|-----------|-------------|
| **Llama 3.1 70B** | 70B | Strong reasoning, open-weights, fits on multi-GPU |
| **Qwen 2.5 72B** | 72B | Excellent at structured data, long context |
| **Mistral Large** | 123B | Top reasoning, but heavier |
| **Llama 3.1 8B** (lighter option) | 8B | Faster inference, good for Phase 1 experiments |

Fine-tuning approach: **LoRA/QLoRA** for efficiency → full fine-tune for final model.

### Practical Challenges at 1TB Scale

| Challenge | Mitigation |
|-----------|-----------|
| 1TB won't fit in context or fine-tuning data directly | Structured sampling: schema-aware chunking, relationship-preserving splits |
| Model may memorize rather than understand | RL loop with adversarial questions, held-out test sets, paraphrase robustness |
| Training compute cost | Start with 8B model on data subset, validate approach, then scale to 70B |
| Knowledge goes stale as DB updates | Periodic re-training + live retrieval for freshness-critical queries |
| Hallucination risk on specific facts | Two-brain: model for intuition, live DB for precision — verify every specific claim |

### How This Connects to Current Architecture

The current system (Phase 1-3) is **not throwaway work**. It becomes the scaffolding:

```
CURRENT (Phase 1-3)                    ENDGAME (Phase 4+)
─────────────────────                  ────────────────────
Cloud LLM for synthesis        →       Fine-tuned local model
Regex router for intent        →       Model understands intent natively
Text-to-SQL fallback           →       Model writes SQL from deep schema knowledge
RAG for document search        →       Model knows documents, uses RAG for precision only
Rule-based formatting          →       Model generates natural, cited responses
Redis cache for speed          →       Model is fast by default (local inference)
Audit chain                    →       Audit chain stays (still need accountability)
RBAC / PII / Security          →       Security layer stays (still need access control)
```

The security, audit, RBAC, and frontend layers remain. Only the **intelligence core** evolves from "retrieve and synthesize" to "already knows, retrieves only when needed."

### Roadmap to Endgame

```
Phase 1-3 (NOW → Month 8):     Ship the working platform with retrieval-based AI
Phase 4 (Month 9-12):          Collect query logs, build training dataset from real usage
Phase 5 (Month 12-16):         Fine-tune base model on schema + data + Q&A pairs
Phase 6 (Month 16-20):         RL loop — model learns to reason over data
Phase 7 (Month 20-24):         Deploy fine-tuned model as primary, RAG as precision fallback
```

**The current architecture is the bridge. The fine-tuned model is the destination.**

---

## For Agents: Quick Reference

```
Repo:           ~/Desktop/NRG
Python:         3.11 (venv at .venv/)
Backend:        FastAPI → src/api/main.py → port 8000
Frontend:       React + Vite → frontend/ → port 3000 (proxy to 8000)
Database:       SQLite → nrg_research.db (PostgreSQL planned)
Orchestration:  LangGraph → src/orchestration/graph.py
Auth:           JWT RS256 → src/auth/jwt_handler.py
                Keys at infrastructure/kong/ssl/jwt_rsa.key/.pub
Users:          researcher_user / gov_user / industry_user
Passwords:      From .env (RESEARCHER_PASSWORD, GOV_PASSWORD, INDUSTRY_PASSWORD)
LLM Config:     src/config/llm_config.py (5 providers + mesh fallback)
Local SLM:      src/config/local_llm.py (Phi-2 / Llama)
Security:       src/security/gateway/prompt_sanitiser.py (PII + injection)
Audit:          src/audit/__init__.py (HMAC-SHA256 chain → .audit/)
Cache:          src/caching/redis_layer.py (graceful degradation)
Skills:         src/skills/text_to_sql/ and src/skills/rag/
State:          src/orchestration/state.py (NRGState dataclass)
Pipeline:       receiver → planner → router → executor → synthesizer → verifier → END
Skills:         .claude/skills/ (24 Claude skills) + .agents/skills/ (35 agent skills)
Workflow:       GURU_PROTOCOL.md (strategy) + AGENT_WARFARE.md (execution system)
```

---

## The Opportunity

**What we have**: Massive dataset (rare) + institutional backing (rare) + government funding (very rare).

**What we're building**: Sovereign AI infrastructure for India's research ecosystem.

**The goal**: A professor opens a browser, logs in, types a research question in plain English, and gets back a verified, structured, cited answer — in seconds, from 600GB of national data, without a single byte leaving Indian servers.

**Whoever defines the architecture controls the project.**