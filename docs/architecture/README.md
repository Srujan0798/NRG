# National Research Graph (NRG)

**Sovereign AI Platform for Indian Research Intelligence**

---

## Quick Start (5 Minutes to Running)

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for full deployment)

### 1. Clone the Repository

```bash
git clone https://github.com/nrg/nrg
cd nrg
```

### 2. Install Dependencies

```bash
# Python dependencies
pip install -e .

# Install spaCy English model (PII scanner enrichment)
python -m spacy download en_core_web_sm

# Frontend dependencies
cd frontend && npm install && cd ..
```

### 3. Configure Environment

```bash
# Copy example environment
cp .env.example .env

# For development, defaults work with SQLite
# For production, set PostgreSQL and other values
```

### 4. Start Services

```bash
# Option A: Docker Compose (full stack)
docker-compose up -d

# Option B: Manual (API only)
python -m uvicorn src.api.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm run dev
```

### 5. Verify

```bash
# Health check
curl http://localhost:8000/health

# Full health (all services)
curl http://localhost:8000/health/all

# API docs
open http://localhost:8000/docs
```

**Expected Output:**
```json
{"status": "healthy", "timestamp": "2026-04-21T10:30:00Z"}
```

---

## Architecture Overview

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Layer                                 │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│   │   Web App   │  │   Mobile    │  │   API CLI   │                │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │
└──────────┼────────────────┼────────────────┼────────────────────────┘
           │                │                │
           └────────────────┼────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Security Gateway                                │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│   │    Kong     │  │    WAF      │  │   Auth      │                │
│   │   Gateway   │  │  (DDoS)     │  │  (JWT)      │                │
│   └─────────────┘  └─────────────┘  └─────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       API Layer (FastAPI)                            │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐               │
│   │  /query │  │  /auth  │  │  /data  │  │ /admin  │               │
│   │ (Graph) │  │         │  │         │  │         │               │
│   └────┬────┘  └─────────┘  └─────────┘  └─────────┘               │
└────────┼─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  LangGraph Orchestration                             │
│   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐      │
│   │Planner │→│ Router │→│Executor│→│Synth   │→│Verifier│→Response│
│   └────────┘  └────────┘  └────────┘  └────────┘  └────────┘      │
└─────────────────────────────────────────────────────────────────────┘
         │
         ├────────────────────────────────┬────────────────────────────┐
         │                                │                            │
         ▼                                ▼                            ▼
┌─────────────────┐            ┌─────────────────┐         ┌─────────────────┐
│  Skills Layer   │            │  LLM Pipeline   │         │    Audit       │
│ ┌─────────────┐ │            │ ┌─────────────┐ │         │ ┌─────────────┐ │
│ │Text-to-SQL  │ │            │ │   NVIDIA    │ │         │ │    HMAC     │ │
│ │     RAG     │ │            │ │   Local     │ │         │ │   Chain     │ │
│ │     KG      │ │            │ │  Rule-based │ │         │ └─────────────┘ │
│ └─────────────┘ │            │ └─────────────┘ │         └─────────────────┘
└─────────────────┘            └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Data Layer                                     │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
│   │PostgreSQL │  │  Qdrant   │  │   Redis   │  │   Neo4j   │       │
│   │   (DB)    │  │ (Vector)  │  │  (Cache)  │  │   (Graph) │       │
│   └───────────┘  └───────────┘  └───────────┘  └───────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Query → Kong Gateway → FastAPI → LangGraph Pipeline
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
              Planner                  Router                Executor
           (Intent Parse)           (Route Select)         (Skill Exec)
                    │                      │                      │
                    │                      │          ┌───────────┴───────────┐
                    │                      │          │                       │
                    ▼                      ▼          ▼                       ▼
              Context                 Route        SQL Skill              RAG Skill
               Update                               or                   or
                                                  KG Skill              VectorDB
                    │                      │          │                       │
                    │                      │          └───────────┬───────────┘
                    │                      │                      │
                    ▼                      ▼                      ▼
              Verifier ←──────────── Synthesizer ←───────── Results
               │                           │
               │                           ▼
               │                      LLM Pipeline
               │                 (NVIDIA → Local → Rule)
               │                           │
               ▼                           ▼
           Reflector ←────────────── Response
               │
               ▼
        Audit Chain
        (HMAC-SHA256)
```

---

## Development Setup

### Environment Variables

```bash
# .env.example (copy to .env)
DATABASE_URL=sqlite:///nrg_research.db  # Dev: SQLite
# Production: postgresql://user:pass@host/db

REDIS_URL=redis://localhost:6379
QDRANT_HOST=localhost
QDRANT_PORT=6333

NVIDIA_API_KEY=your_key_here  # Optional for dev

# Security
JWT_PRIVATE_KEY_PATH=infrastructure/kong/ssl/jwtRS256.key
JWT_PUBLIC_KEY_PATH=infrastructure/kong/ssl/jwtRS256.key.pub

# Optional features
CLOUD_SYNTHESIS_ALLOWED=false  # Default: disabled for sovereignty
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run security tests
pytest tests/security/ -v

# Run skill tests
pytest tests/skills/ -v

# Run UAT tests
python tests/uat/run_all_personas.py
```

### Database Migrations

```bash
# Apply migrations (Alembic)
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback
alembic downgrade -1
```

---

## Testing Guide

### Test Categories

| Category | Location | Description |
|----------|----------|-------------|
| Unit Tests | `tests/unit/` | Individual component testing |
| Integration Tests | `tests/integration/` | Service-to-service |
| Security Tests | `tests/security/` | Auth, RBAC, PII detection |
| Red Team | `tests/security/redteam/` | Attack simulation |
| UAT | `tests/uat/` | End-to-end user flows |

### Running Specific Tests

```bash
# Security tests (RBAC, PII, Injection)
pytest tests/security/test_gateway.py -v
pytest tests/security/test_pii_compliance.py -v

# Skill tests (SQL, RAG, KG)
pytest tests/skills/ -v

# Query pipeline tests
pytest tests/test_query_pipeline.py -v
```

### Test Users

| Username | Password | Tier | Access |
|----------|----------|------|--------|
| researcher_user | researcher-pass | 1 | Full access |
| gov_user | gov-pass | 2 | Aggregate only |
| industry_user | industry-pass | 3 | Anonymized only |
| admin_user | admin-pass | Admin | System management |

---

## Deployment Guide

### Development

```bash
# Local with Docker
docker-compose up -d

# Without Docker
python -m uvicorn src.api.main:app --reload --port 8000
```

### Staging

```bash
# SSH and deploy
ssh ops@staging.nrg.gov.in
cd /opt/nrg
git pull
docker-compose -f docker-compose.staging.yml up -d
```

### Production

```bash
# Zero-downtime rolling update
ssh ops@api.nrg.gov.in

# Backup
docker-compose exec postgres pg_dump -U nrg > /backup/nrg_$(date +%Y%m%d).sql

# Deploy
docker-compose -f docker-compose.prod.yml up -d --remove-orphans

# Health check
curl https://api.nrg.gov.in/health/all
```

### Kubernetes

```bash
# Scale API pods
kubectl scale deployment nrg-api --replicas=5 -n nrg

# Check pod status
kubectl get pods -n nrg

# View logs
kubectl logs -n nrg -l app=nrg-api --tail=100

# Restart
kubectl rollout restart deployment/nrg-api -n nrg
```

---

## Project Structure

```
NRG/
├── src/
│   ├── api/                  # FastAPI routes and middleware
│   ├── orchestration/       # LangGraph workflow definition
│   │   └── nodes/           # Planner, Router, Executor, etc.
│   ├── skills/              # Text-to-SQL, RAG, KG skills
│   ├── security/             # Gateway, PII, RBAC
│   ├── observability/        # Langfuse, Prometheus metrics
│   └── db/                   # Database connections
├── frontend/                 # React TypeScript dashboard
├── tests/                    # Test suites
├── scripts/                  # Deployment and utility scripts
├── docs/                     # Documentation
│   ├── architecture/         # System design, ADRs, runbook
│   ├── specs/                # Feature specifications
│   ├── security/             # Security docs
│   └── compliance/           # DPDP compliance
├── infrastructure/          # Kong, monitoring configs
└── models/                   # Saved models
```

---

## License

**Confidential** - Government of India / IIT Gandhinagar

All rights reserved. This project and its documentation are proprietary to IIT Gandhinagar and the Government of India. Unauthorized reproduction, distribution, or use is strictly prohibited.

---

## Contact

| Role | Email |
|------|-------|
| Project Lead | nrg-project@iitgn.ac.in |
| Technical Lead | nrg-tech@iitgn.ac.in |
| Security Issues | security@iitgn.ac.in |
| General Inquiries | nrg-info@iitgn.ac.in |

---

**Version:** 2.0
**Last Updated:** 2026-04-21
**Documentation Maintainer:** Architecture Team