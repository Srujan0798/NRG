# NRG Architecture — Technical Specification

## For IIT-GN Ops Team and NIC Engineers

**Version:** 1.0  
**Date:** 2026-04-24  
**Classification:** Internal — Technical  
**Cross-Reference:** Core_Idea_Clean.md  

---

## 1. System Overview

The National Research Graph (NRG) is a sovereign AI platform providing tier-filtered access to India's research database across 3 personas: Researcher (Tier 1), Government (Tier 2), Industry (Tier 3).

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NATIONAL RESEARCH GRAPH                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                   │
│  │ Researcher  │    │ Government  │    │  Industry   │    ← 3 Personas   │
│  │   (Tier 1)  │    │   (Tier 2)  │    │   (Tier 3)  │                   │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                   │
│         │                   │                   │                         │
│         └───────────────────┬───────────────────┘                         │
│                            ▼                                               │
│              ┌─────────────────────────────┐                              │
│              │   Tier-Aware Middleware    │ ← RBAC + PII filtering        │
│              └─────────────────────────────┘                              │
│                            │                                               │
│         ┌─────────────────┼─────────────────┐                              │
│         ▼                 ▼                 ▼                              │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐                    │
│  │  LangGraph │    │   PII      │    │   Audit    │  ← Security Layers  │
│  │ Pipeline   │    │ Sanitizer  │    │ Chain(HMAC)│                    │
│  └────────────┘    └────────────┘    └────────────┘                    │
│         │                                                       │
│    ┌────┴────┐                                                      │
│    ▼         ▼                                                      │
│  ┌────────┐  ┌────────┐                                           │
│  │ SQL    │  │  RAG   │  ← Data Sources                              │
│  │Skill   │  │ Skill  │                                           │
│  └────────┘  └────────┘                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The 5-Layer Architecture

*(Cross-reference: Core_Idea_Clean.md — "The 5-Layer Architecture")*

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
│  ⚠️ NO raw data sent to cloud — only retrieved facts   │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  LAYER 3: RETRIEVAL                                     │
│  Dual-path search:                                       │
│  • Text-to-SQL → structured database queries            │
│  • RAG → semantic vector search in documents            │
│  • Hybrid → both paths combined                         │
│  Intent router decides which path(s) to take            │
└────────────────────────────┬────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  LAYER 2: KNOWLEDGE                                     │
│  Structured data: researchers, labs, publications,      │
│  institutions, funding, keywords, collaborations        │
│  Future: knowledge graph (who collaborates with whom)   │
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

## 3. The 6-Node Query Pipeline

*(Cross-reference: Core_Idea_Clean.md — "The LangGraph Pipeline")*

### 3.1 Node Overview

```
USER QUERY
     │
     ▼
┌──────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐   ┌──────────┐
│ RECEIVER │──▶│ PLANNER │──▶│  ROUTER  │──▶│ EXECUTOR │──▶│ SYNTHESIZER │──▶│ VERIFIER │
└──────────┘   └─────────┘   └──────────┘   └──────────┘   └─────────────┘   └──────────┘
     │              │              │              │                │                │
  Assigns ID   Decomposes    Classifies:    Runs skills:     Writes answer:   Checks citations
  Loads session query into   • structured   • Text-to-SQL   1st: Cloud LLM   against evidence
  history      sub-queries   • unstructured  • RAG           2nd: Local SLM   Retries if
                + schema     • hybrid        • Both          3rd: Rule-based  unsupported
```

### 3.2 Node Details

#### RECEIVER Node
- Assigns unique query ID
- Loads session history
- Validates JWT token
- Checks user tier
- Logs entry to audit chain

#### PLANNER Node
- Decomposes complex queries into sub-queries
- Loads schema context (58 tables in PostgreSQL)
- Generates execution DAG
- Handles multi-hop queries like "compare Gujarat and Karnataka's AI research over 5 years"

#### ROUTER Node
- Classifies query intent:
  - **structured**: Words like "find", "list", "count", "how many" → Text-to-SQL
  - **unstructured**: Words like "trends", "explain", "what are" → RAG
  - **hybrid**: Words like "synthesize", "combine" → Both paths

#### EXECUTOR Node
- **Text-to-SQL Path**: Extracts entities (states, research areas, years) → builds SQL → executes in read-only sandbox → returns rows
- **RAG Path**: Embeds query → searches Qdrant → returns relevant document chunks
- Both paths run independently; failures are caught and logged

#### SYNTHESIZER Node
- Combines SQL results + document chunks
- **3-tier cascade**:
  1. Cloud LLM (Gemini/Claude) — most intelligent
  2. Local SLM (Llama 3 8B) — fully offline
  3. Rule-based formatting — always works, no AI needed
- Enforces data minimization (max 10 rows to LLM)

#### VERIFIER Node
- Checks citations against source evidence
- Flags hallucinations
- Retries synthesis if faithfulness score is low
- Every verification is audit-logged

---

## 4. Data Flow Diagram

### 4.1 Query Flow (Happy Path)

```
User Query ─► Auth (JWT) ─► Tier Check ─► Sanitizer ─► LangGraph
                                                       │
                    ┌───────────────────────────────┘
                    ▼
            ┌───────────────┐
            │   PLANNER     │ ← Decomposes query
            └───────┬───────┘
                    ▼
            ┌───────────────┐
            │    ROUTER     │ ← text_to_sql / RAG / hybrid
            └───────┬───────┘
                    ▼
         ┌──────────┴──────────┐
         ▼                      ▼
   ┌──────────┐         ┌──────────┐
   │TextToSQL │         │   RAG    │ ← Parallel execution
   │ Skill    │         │  Skill   │
   └────┬─────┘         └────┬─────┘
        │                     │
        └──────────┬──────────┘
                   ▼
            ┌───────────────┐
            │ SYNTHESIZER   │ ← 3-tier cascade: Cloud → Local → Rule
            └───────┬───────┘
                   ▼
            ┌───────────────┐
            │  VERIFIER     │ ← Citation faithfulness check
            └───────┬───────┘
                   ▼
            Response + Audit Log (HMAC)
```

### 4.2 Security Flow

```
Request ─► CORS Check ─► Rate Limit ─► Auth Verify ─► PII Scan ─► Tier Filter
     │         │           │            │          │            │
     └─────────┴───────────┴────────────┴───────────┴────────────┘
                                                               ▼
                                               Allow / Block / Challenge
```

---

## 5. Network Zones (Security Boundaries)

```
┌─────────────────────────────────────────────────────────────────┐
│                         PUBLIC ZONE                             │
│   Port 3000 (Frontend)  │  Port 8000 (API)  │  Port 8080 (Kong) │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DMZ ZONE (Kong)                          │
│              Rate Limiting │ Auth │ WAF Rules                    │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION ZONE                            │
│     ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │
│     │ API Server│  │ LangGraph │  │  Worker   │  │ Metrics   │ │
│     └───────────┘  └───────────┘  └───────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA ZONE                                │
│    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│    │SQLite/PG │   │ Qdrant   │   │  Redis   │   │Audit Log │ │
│    └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Tier Access Matrix

| Data Type | Tier 1 (Researcher) | Tier 2 (Government) | Tier 3 (Industry) |
|-----------|---------------------|---------------------|-------------------|
| Researcher emails | ✓ | ✗ | ✗ |
| Full publications | ✓ | Abstract only | ✗ |
| Funding amounts | ✓ | Aggregate only | ✗ |
| Raw abstracts | ✓ | ✓ (limited) | ✗ |
| Statistics | ✓ | ✓ | Limited |

---

## 7. Security Model

*(Cross-reference: Core_Idea_Clean.md — "Security Model: Zero-Data-Leakage")*

### 7.1 Core Principle

> "The 600GB repository resides exclusively on Indian servers. The system is architecturally incapable of uploading data to the internet."

### 7.2 What NEVER Leaves the Local Boundary

- The 600GB research database
- Retrieved facts and document chunks
- Synthesized content
- Researcher PII (Aadhaar, phone, email)

### 7.3 What Goes to Cloud LLM (When Used)

- Only: the user's question + retrieved facts for synthesis
- NOT: raw database, schemas, or sensitive metadata

### 7.4 PII Detection Patterns

```python
PII_PATTERNS = {
    "aadhaar": r"\b[2-9]{1}[0-9]{11}\b",
    "pan": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",
    "phone": r"\b[6-9]{1}[0-9]{9}\b",
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
}
```

### 7.5 JWT RS256 Authentication Flow

```
User Credentials ─► /login ─► Validate ─► Sign RS256 JWT ─► Return token
                                                                 │
Request + JWT ─► Verify RS256 signature ─► Extract tier ─► RBAC check
```

---

## 8. The 6 Hard Constraints (Quality Bar Scorecard)

*(Cross-reference: Core_Idea_Clean.md — "Phase 1: Working Acceptance" and Quality Bar Scorecard)*

| # | Constraint | Implementation | Status |
|---|------------|---------------|--------|
| C1 | **DPDP-Compliant Indian PII Detection** | Custom regex for Aadhaar, PAN, phone, email + Presidio | 8/8 (100%) ✅ |
| C2 | **Per-User Audit Binding (Non-Repudiation)** | HMAC-SHA256 chained log, every event tagged to user_id | 26/26 (100%) ✅ |
| C3 | **Multi-Hop Intent Decomposition (DAG Planner)** | LangGraph planner node decomposes complex queries | 24/24 (100%) ✅ |
| C4 | **Production SLOs (P99 <500ms, ≥1000 concurrent)** | Locust load test required | SKIP (needs live API) |
| C5 | **Vector Drift Monitoring + Auto-Retrain Trigger** | Qdrant cosine similarity monitoring | SKIP (needs Qdrant) |
| C6 | **Schema Allowlist Before Cloud LLM** | sqlglot schema validation, sandboxed execution | 35/35 (100%) ✅ |

**Overall: 4/6 passing, 2/6 require live infrastructure (C4, C5)**

Run the scorecard:
```bash
python scripts/quality_bar_scorecard.py
```

---

## 9. Technology Stack

### 9.1 Production

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python 3.11) |
| Frontend | React + TypeScript + Tailwind |
| Database | PostgreSQL 16 |
| Vector DB | Qdrant v1.11 |
| Cache | Redis 7 |
| Gateway | Kong 3.6 |
| LLM | NVIDIA → OpenAI → Anthropic → Azure → Gemini (mesh fallback) |
| Auth | JWT RS256 |
| Audit | HMAC-SHA256 |
| Orchestration | LangGraph |

### 9.2 Development

| Tool | Purpose |
|-----|---------|
| Docker | Containers |
| Alembic | Migrations |
| Pytest | Testing |
| Playwright | E2E |
| Langfuse | Observability |

---

## 10. Data Model

*(Cross-reference: Core_Idea_Clean.md — "Data Model")*

### 10.1 Schema Gap Warning

> **IMPORTANT**: Dev uses SQLite (18 tables). Production uses PostgreSQL (58 tables). 40 tables are missing in dev.

Always reference `db_struct.sql` (58-table production schema) for SQL queries.

### 10.2 Core Tables (Production PostgreSQL)

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

---

## 11. Deployment Architecture

```
                                          ┌─────────────────────┐
                                          │   Load Balancer      │
                                          │   (Kong 3.6)        │
                                          └──────────┬──────────┘
                                                     │
                          ┌──────────────────────────┼──────────────────────────┐
                          ▼                          ▼                          ▼
                   ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
                   │   API Pod   │          │   API Pod   │          │   API Pod   │
                   │ (FastAPI)  │          │ (FastAPI)  │          │ (FastAPI)  │
                   └─────────────┘          └─────────────┘          └─────────────┘
                          │                         │                         │
       ┌──────────────────┼──────────────────────────┼─────────────────────────┤
       ▼                  ▼                         ▼                        ▼
 ┌──────────┐      ┌──────────┐             ┌──────────┐             ┌──────────┐
 │PostgreSQL│      │ Qdrant   │             │  Redis   │             │  Worker  │
 │ Primary  │      │ (3 nodes)│             │ Cluster │             │(Async)   │
 └──────────┘      └──────────┘             └──────────┘             └──────────┘
```

---

## 12. Error Codes and Recovery

| Code | Meaning | Recovery |
|------|---------|----------|
| 401 | Invalid/missing JWT | Re-login |
| 403 | Tier insufficient | Request access or use appropriate tier |
| 429 | Rate limit exceeded | Wait 60 seconds |
| 500 | Internal error | Check logs, restart service |
| 503 | LLM unavailable | System falls back to local SLM → rule-based |

---

## 13. File Locations

| Component | Path |
|-----------|------|
| API | `src/api/main.py` |
| LangGraph | `src/orchestration/graph.py` |
| Auth | `src/auth/jwt_handler.py` |
| Security | `src/security/gateway/prompt_sanitiser.py` |
| Audit | `src/audit/__init__.py` |
| SQL Skill | `src/skills/text_to_sql/` |
| RAG Skill | `src/skills/rag/` |
| Frontend | `frontend/` |
| Config | `src/config/llm_config.py` |
| Schema | `db_struct.sql` (58 tables, PostgreSQL) |

---

## 14. Quick Commands

```bash
# Check health
curl http://localhost:8000/health/all

# Verify audit chain
curl http://localhost:8000/audit/verify

# Test login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"researcher_user","password":"researcher-pass"}'

# Run quality bar scorecard
python scripts/quality_bar_scorecard.py

# Restart API
pkill -f "uvicorn src.api.main" && uvicorn src.api.main:app --port 8000 &
```

---

*Document version: 1.0*  
*Last updated: 2026-04-24*  
*For technical questions: ops@nrg.iitgn.ac.in*