# NRG — National Research Graph

**Sovereign AI-powered research intelligence platform for India's national research database.**

A production-grade system that enables natural language queries against structured research data (researchers, publications, institutions, labs, funding) with full DPDP-2023 compliance, tiered access control, and tamper-proof audit trails.

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **Node.js 18+** (for frontend development)
- **4GB RAM minimum** (8GB recommended)

### Production Setup (Single Command)

```bash
git clone https://github.com/your-org/nrg.git
cd nrg
docker compose --profile prod up -d

# Wait for services to be healthy (~30 seconds)
docker compose ps

# Access the system:
# - Frontend: http://localhost (or http://localhost:3000 directly)
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Local Development Setup

```bash
# 1. Clone and enter directory
git clone https://github.com/your-org/nrg.git
cd nrg

# 2. Set up Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Download NLP model (required for PII detection)
python -m spacy download en_core_web_sm

# 5. Copy and configure environment
cp .env.example .env
# Edit .env with your configuration

# 6. Start infrastructure services
docker compose --profile dev up -d postgres redis qdrant

# 7. Run database migrations
alembic upgrade head

# 8. Seed with sample data
python scripts/seed_release_data.py

# 9. Start the API server
uvicorn src.api.main:app --reload --port 8000

# 10. In a new terminal, start the frontend
cd frontend && npm install && npm run dev
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     NRG Research Platform                         │
├─────────────────────────────────────────────────────────────────┤
│  FRONTEND (React + Vite + Tailwind)                            │
│  ├── Researcher Dashboard (Tier 1 - Full access)                │
│  ├── Government Dashboard (Tier 2 - Aggregated analytics)      │
│  └── Industry Dashboard (Tier 3 - Anonymized partnership view)  │
├─────────────────────────────────────────────────────────────────┤
│  API GATEWAY (FastAPI)                                          │
│  ├── JWT Authentication with RS256 signing                      │
│  ├── Tier-based Response Shaping                               │
│  ├── PII Detection & Blocking                                   │
│  └── Prompt Injection Prevention                                │
├─────────────────────────────────────────────────────────────────┤
│  ORCHESTRATION LAYER (LangGraph)                               │
│  ├── Receiver → Planner → Router → Executor → Synthesizer     │
│  ├── Multi-hop Query Decomposition                             │
│  └── Self-correction with Result Validation                     │
├─────────────────────────────────────────────────────────────────┤
│  SKILLS LAYER                                                   │
│  ├── Text-to-SQL (Natural language → PostgreSQL)               │
│  ├── RAG (Vector similarity search via Qdrant)                  │
│  └── Hybrid (Combined structured + semantic retrieval)           │
├─────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                     │
│  ├── PostgreSQL (58 tables, full schema)                       │
│  ├── Qdrant (Vector embeddings for semantic search)             │
│  ├── Redis (Query caching, rate limiting)                      │
│  └── HMAC-Chained Audit Log (Tamper-proof)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### Security & Compliance

- **DPDP-2023 Compliant**: Indian PII detection (Aadhaar, PAN, mobile, email, GSTIN, passport, bank accounts)
- **Tiered Access Control (RBAC)**: Three personas with different data visibility
  - **Researcher (Tier 1)**: Full researcher profiles, publications, contact information
  - **Government (Tier 2)**: Aggregated statistics, institutional analytics, policy reports
  - **Industry (Tier 3)**: Anonymized research areas, anonymized collaboration opportunities
- **Tamper-Proof Audit**: HMAC-SHA256 chained audit log with per-user binding
- **Prompt Injection Prevention**: Guards against adversarial inputs

### Query Capabilities

- **Natural Language to SQL**: Ask questions in plain English, get structured SQL results
- **Semantic Search**: Find related research using vector similarity
- **Multi-hop Reasoning**: Complex queries decomposed into dependency graphs
- **Self-Correction**: Automatic retry on failed or empty results

---

## User Personas

| Persona | Access Level | Sample Queries |
|---------|-------------|----------------|
| **Researcher** | Tier 1 - Full | "Show me researchers in Gujarat working on AI" |
| **Government** | Tier 2 - Aggregated | "What are the state-wise research trends in renewable energy?" |
| **Industry** | Tier 3 - Anonymized | "Who has capability in hydrogen fuel cell research?" |

---

## Database Schema

The system uses a comprehensive 58-table PostgreSQL schema covering:

- **Researchers**: Profiles, contact info, affiliations (200+ records in seed data)
- **Publications**: Titles, abstracts, authors, citations (12,000+ records)
- **Institutions**: Universities, research labs, government bodies (24+ records)
- **Funding**: Grants, agencies, disbursements (1,000+ records)
- **Academic Courses**: Innovation courses, TRL levels, outcomes (5,000+ records)
- **And 50+ additional tables** for complete research metadata

See `docs/SCHEMA.md` for complete documentation.

---

## API Reference

### Authentication

```bash
# Login and get JWT token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "researcher_user", "password": "your_password"}'

# Response includes access_token and refresh_token
```

### Query Endpoint

```bash
# Submit a natural language query
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many publications are there?"}'

# Response includes:
# - audit_event_id: For audit trail verification
# - sql_query: The generated SQL
# - sql_results: Query results (tier-filtered)
# - synthesized_answer: Natural language response
# - citations: Source references
```

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Authenticate and get JWT |
| POST | `/query` | Natural language query |
| GET | `/researchers` | List researchers (tier-filtered) |
| GET | `/researchers/{id}` | Researcher details |
| GET | `/publications` | List publications |
| GET | `/stats` | Aggregated statistics |
| GET | `/health` | System health check |
| GET | `/health/all` | Full health with audit chain |

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/nrg

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant Vector DB
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Authentication
JWT_SECRET_FILE=infrastructure/kong/ssl/jwt_rsa.key

# Tier passwords (change in production!)
RESEARCHER_PASSWORD=researcher_secure_password
GOV_PASSWORD=gov_secure_password
INDUSTRY_PASSWORD=industry_secure_password

# LLM Configuration (optional)
CLOUD_SYNTHESIS_ALLOWED=false  # Set true to enable cloud LLM
```

### Tier Test Users

| Username | Password | Tier |
|----------|----------|------|
| `researcher_user` | From `.env` | 1 (Full) |
| `gov_user` | From `.env` | 2 (Government) |
| `industry_user` | From `.env` | 3 (Industry) |

---

## Testing

### Run All Tests

```bash
# Full test suite (requires running services)
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test categories
pytest tests/security/ -v
pytest tests/benchmarks/ -v
pytest tests/api/ -v
```

### Critical Query Benchmarks

```bash
# Run Dhairya SQL benchmark (17 queries)
pytest tests/benchmarks/test_dhairya_regression.py -v

# Run killer queries against live API
python scripts/capture_killer_query_evidence.py
```

### Security Testing

```bash
# Run PII compliance tests
pytest tests/security/test_pii_compliance.py -v

# Run red-team suite
python scripts/red_team_live_replay.py
```

---

## Production Deployment

### Docker Compose (Recommended)

```bash
# Full production stack
docker compose --profile prod up -d

# Check status
docker compose ps

# View logs
docker compose logs -f api
```

### Database Migrations

```bash
# Run pending migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Check migration status
alembic current
```

### Health Checks

```bash
# Full system health
curl http://localhost:8000/health/all

# Verify audit chain
python scripts/audit_investigate.py
```

---

## Project Structure

```
nrg/
├── src/                    # Python source code
│   ├── api/               # FastAPI endpoints
│   ├── orchestration/     # LangGraph workflow nodes
│   ├── skills/            # Text-to-SQL and RAG skills
│   ├── security/          # PII, RBAC, rate limiting
│   ├── auth/              # JWT handling
│   ├── audit/             # HMAC audit chain
│   ├── caching/           # Redis layer
│   ├── observability/     # Metrics, tracing
│   └── data/              # Database connections
├── frontend/              # React application
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── views/         # Page views (Researcher, Gov, Industry)
│   │   ├── hooks/         # Custom React hooks
│   │   └── services/      # API client
│   └── tests/             # Frontend tests
├── tests/                 # Python test suite
│   ├── api/               # API endpoint tests
│   ├── security/          # Security tests
│   ├── benchmarks/        # Query benchmarks
│   ├── orchestration/     # Workflow tests
│   └── skills/            # Skill tests
├── scripts/               # Utility scripts
├── alembic/               # Database migrations
├── infrastructure/        # Docker, nginx, kong configs
├── docs/                  # Documentation
│   └── SCHEMA.md          # Database schema reference
├── evidence/              # Test evidence and reports
└── docker-compose.yml     # Container orchestration
```

---

## Performance

- **Query Latency**: P99 < 500ms for analytical queries
- **Frontend Load Time**: < 2 seconds on 4G
- **Concurrent Users**: 1000+ supported
- **Database**: Optimized with proper indexes, no N+1 queries

---

## Documentation

| Document | Description |
|----------|-------------|
| `Core_Idea_Clean.md` | Product specification and vision |
| `docs/SCHEMA.md` | Complete database schema reference |
| `docs/handover/` | Production handover artifacts |
| `evidence/` | Test evidence and audit reports |

---

## Support

For issues or questions:
1. Check the [API documentation](http://localhost:8000/docs)
2. Review test evidence in `evidence/`
3. Check audit logs in `.audit/chain.jsonl`

---

## License

Confidential — Government of India / IIT Gandhinagar

---

**Built with production-grade engineering practices for sovereign AI infrastructure.**
