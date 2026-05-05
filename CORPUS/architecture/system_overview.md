# NRG System Overview

## Executive Summary

NRG is a sovereign research-intelligence platform. Phase 1 is a truthful, runnable, deterministic PoC with a path toward a fine-tuned local model.

## Runtime Architecture

```text
React Dashboards (frontend/src/)
  -> FastAPI Routes (/login, /query, /stats, /publications, /query/graph)
  -> LangGraph Workflow (src/orchestration/)
  -> SQL Skill + RAG Skill (src/skills/)
  -> Synthesizer Cascade: cloud-gated -> local -> rule-based
  -> Response Metadata: warnings, retrieval_sources, provenance
```

## Backend Structure

| Module | Path | Purpose |
|--------|------|---------|
| API | `src/api/` | FastAPI routes, middleware, main app |
| Auth | `src/auth/` | JWT, RBAC, tier enforcement |
| Security | `src/security/` | PII detection, egress guard, DPDP compliance |
| Audit | `src/audit/` | HMAC-signed audit chain, per-user binding |
| Orchestration | `src/orchestration/` | LangGraph planner, multi-hop DAG, nodes |
| Skills | `src/skills/` | text_to_sql, rag, query helpers |
| Data | `src/data/` | schema hints, synonyms, business glossary |
| Observability | `src/observability/` | metrics, vector drift, data quality |
| Config | `src/config/` | database manager, settings |

## Frontend Structure

| Layer | Path | Purpose |
|-------|------|---------|
| Views | `frontend/src/views/` | Dashboard per persona (researcher/government/industry) |
| Pages | `frontend/src/pages/` | AuditEvent, ProductionWorkspace |
| Components | `frontend/src/components/` | Reusable UI components |
| Hooks | `frontend/src/hooks/` | useAuth, useTheme, useReducedMotion |
| Services | `frontend/src/services/` | API clients |
| Design System | `frontend/src/design-system/` | ThemeProvider, tokens |

## Infrastructure

| Service | Tech | Purpose |
|---------|------|---------|
| API | FastAPI + Uvicorn | Backend server |
| Frontend | React + Vite | SPA |
| Database | PostgreSQL 16 | Primary data store |
| Vector Store | Qdrant | Embedding search |
| Cache | Redis | Session, rate limit |
| Proxy | Nginx | Reverse proxy, static files |
| Gateway | Kong | API gateway, JWT validation |
| Monitoring | Prometheus + Grafana | Metrics, alerting |
| Orchestration | Kubernetes (sovereign cluster) | Production deployment |

## Data Boundary

Allowed external LLM payloads (only when `CLOUD_SYNTHESIS_ALLOWED=true`):
- User query
- Minimal retrieved evidence packet
- Bounded excerpts, not full documents
- Citation/source identifiers
- Redaction and evidence-count metadata

Blocked external LLM payloads:
- Raw 600 GB corpus data
- Full abstracts or full-text documents
- Emails, phone numbers, addresses, IDs, secrets
- Raw SQL dumps or unrestricted schema exports

## Synthesis Modes

| Mode | Status | Boundary |
|------|--------|----------|
| `cloud_synthesis` | Optional, explicit | Minimized, sanitized evidence packets only |
| `local_slm` | Sovereign/offline path | Retrieved evidence inside deployment boundary |
| `rule_based` | Always-available fallback | Formats local SQL/RAG output without external calls |

## Key Constraints

- Cloud synthesis disabled by default
- JWT auth with RS256 asymmetric signing
- 3 user tiers: researcher (full), government (aggregated), industry (anonymized)
- DPDP-2023 compliant: consent, erasure, export
- Audit chain: HMAC-signed, per-user binding, tamper-proof
