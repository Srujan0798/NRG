# National Research Graph — Architecture Blueprint

**Version:** 1.0  
**Date:** 2026-04-21  
**Classification:** Internal — Technical

---

## 1. System Overview

The National Research Graph (NRG) is a sovereign AI platform for India's research intelligence. It provides tier-filtered access to 50K+ research records across 3 personas: Researcher, Government, and Industry.

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
│         └───────────────────┬�───────────────────┘                         │
│                           ▼                                               │
│              ┌─────────────────────────────┐                              │
│              │   Tier-Aware Middleware    │ ← RBAC + PII filtering        │
│              └─────────────────────────────┘                              │
│                           │                                               │
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

## 2. Data Flow Diagram

### 2.1 Query Flow (Happy Path)

```
User Query ─► Auth (JWT) ─► Tier Check ─►Sanitizer ─► LangGraph
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
            │  VERIFIER    │ ← Citation faithfulness check
            └───────┬───────┘
                   ▼
            Response + Audit Log (HMAC)
```

### 2.2 Security Flow

```
Request ─► CORS Check ─► Rate Limit ─► Auth Verify ─► PII Scan ─► Tier Filter
     │         │           │            │          │            │
     └─────────┴─────────┴────────────┴────────────┴────────────┘
                                                              ▼
                                              Allow / Block / Challenge
```

---

## 3. Component Architecture

### 3.1 Core Services

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| API Gateway | HTTP, Auth, Rate limiting | FastAPI |
| LangGraph | Query orchestration | LangGraph |
| TextToSQL | SQL generation + execution | sqlglot + sandbox |
| RAG | Semantic search | Qdrant + bge-m3 |
| Synthesizer | Response generation | NVIDIA/OpenAI/Local |
| Verifier | Citation check | Local LLM |
| Audit | Immutable ledger | HMAC-SHA256 |
| PII Filter | Sensitive data block | Presidio + regex |

### 3.2 Data Stores

| Store | Purpose | Technology |
|-------|---------|-------------|
| SQLite/PostgreSQL | Structured data | SQLAlchemy |
| Qdrant | Vector embeddings | Qdrant |
| Redis | Caching, rate limits | Redis |
| File system | Audit logs | JSONL |

---

## 4. Security Boundaries

### 4.1 Network Zones

```
┌─────────────────────────────────────────────────────────────────┐
│                         PUBLIC ZONE                             │
│   Port 3000 (Frontend)  │  Port 8000 (API)  │  Port 8080 (Kong) │
└──────��──────────────────────────────────────────────────────────┘
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
│     ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│     │ API Server│  │ LangGraph │  │  Worker   │  │ Metrics   │  │
│     └───────────┘  └───────────┘  └───────────┘  └───────────┘  │
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

### 4.2 Tier Access Matrix

| Data Type | Tier 1 (Researcher) | Tier 2 (Government) | Tier 3 (Industry) |
|----------|-------------------|-------------------|-------------------|
| Researcher emails | ✓ | ✗ | ✗ |
| Full publications | ✓ | Abstract only | ✗ |
| Funding amounts | ✓ | Aggregate only | ✗ |
| Raw abstracts | ✓ | ✓ (limited) | ✗ |
| Statistics | ✓ | ✓ | Limited |

---

## 5. Technology Stack

### 5.1 Production

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python 3.11) |
| Frontend | React + TypeScript + Tailwind |
| Database | PostgreSQL 16 |
| Vector DB | Qdrant v1.11 |
| Cache | Redis 7 |
| Gateway | Kong 3.6 |
| LLM | NVIDIA → OpenAI → Anthropic → Azure → Gemini |
| Auth | JWT RS256 |
| Audit | HMAC-SHA256 |

### 5.2 Development

| Tool | Purpose |
|-----|---------|
| Docker | Containers |
| Alembic | Migrations |
| Pytest | Testing |
| Playwright | E2E |
| Langfuse | Observability |

---

## 6. Deployment Architecture

```
                                         ┌─────────────────────┐
                                         │   Load Balancer      │
                                         │   (Kong 3.6)        │
                                         └──────────┬──────────┘
                                                    │
                          ┌─────────────────────────┼─────────────────────────┐
                          ▼                         ▼                         ▼
                   ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
                   │   API Pod   │          │   API Pod   │          │   API Pod   │
                   │ (FastAPI)  │          │ (FastAPI)  │          │ (FastAPI)  │
                   └─────────────┘          └─────────────┘          └─────────────┘
                          │                         │                         │
         ┌────────────────┼────────────────────────┼────────────────────────┤
         ▼                ▼                        ▼                        ▼
   ┌──────────┐    ┌──────────┐           ┌──────────┐          ┌──────────┐
   │PostgreSQL│    │ Qdrant   │           │  Redis   │          │  Worker  │
   │ Primary  │    │ (3 nodes)│           │ Cluster │          │(Async)  │
   └──────────┘    └──────────┘           └──────────┘          └──────────┘
```

---

## 7. Scaling Strategy

| Component | Current | Scale Target |
|-----------|---------|--------------|
| API | 2 pods | 20 pods |
| Qdrant | 3 nodes | 10 nodes |
| Redis | 1 | 6 cluster |
| Database | 1 primary | Read replicas |

---

## 8. Monitoring Stack

| Metric | Tool | Alert Threshold |
|--------|------|----------------|
| API latency P95 | Prometheus | > 5s |
| Error rate | Prometheus | > 1% |
| Token usage | Langfuse | > 80% quota |
| Audit chain | Custom | Break detected |

---

**Author:** Architect Agent  
**Next Review:** 2026-05-21