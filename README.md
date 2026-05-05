# NRG — National Research Graph

**Sovereign AI-powered research intelligence platform for India's national research database.**

NRG lets authenticated users ask natural-language questions over structured research data and receive SQL-visible, tier-filtered, audit-bound answers. The local release path is validated with the 58-table schema bridge, Dhairya SQL regression coverage, role-based response shaping, and HMAC audit-chain verification.

Current local status is documented in `docs/PRODUCTION_READINESS_SUMMARY.md`. Sovereign-cluster load testing, populated Qdrant baseline establishment, and real 600GB intake require the target environment and are tracked separately instead of being claimed from a laptop run.

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **Node.js 18+** (for frontend development)
- **4GB RAM minimum** (8GB recommended)

### Container Setup

```bash
git clone <repository-url>
cd nrg
docker compose up -d

# Wait for services to become healthy.
docker compose ps

# Access the system:
# - Frontend: http://localhost (or http://localhost:3000 directly)
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Local Development Setup

```bash
# 1. Clone and enter directory
git clone <repository-url>
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

# 8. Seed the local reference dataset
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

The system uses a 58-table PostgreSQL schema parsed from `db_struct.sql`. The local volumetric reference database used by the 2026-04-26 evidence contains at least:

- `academic_courses_details`: 50,000 rows
- `innovations_at_various_stages_of_technology_readiness_level`: 10,000 rows
- `innovation_grant_from_govt`: 30,000 rows
- `combined_ipo_patent_data`: 20,000 rows
- `publications`: 100,000 rows
- `researchers`: 5,615 rows

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
  -d '{"query": "How many publications are there?"}'

# Response includes:
# - audit_event_id: For audit trail verification
# - sql_query: The generated SQL
# - sql_results: Query results (tier-filtered)
# - response: Natural language response
# - citations: Source references
```

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Authenticate and get JWT |
| POST | `/query` | Natural language query |
| GET | `/researchers` | List researchers (tier-filtered) |
| GET | `/publications` | List publications |
| GET | `/stats` | Aggregated statistics |
| GET | `/health` | System health check |
| GET | `/health/all` | Full health with audit chain |

The complete route inventory is maintained in
`docs/specs/API_ENDPOINT_MATRIX.md` and guarded by
`tests/api/test_api_endpoint_matrix.py`.

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

### Data Source (Corpus Ingestion)

The research document corpus lives outside the repo (600GB on production).
On a fresh clone, set the path before running ingestion scripts:

```bash
# Option A: place the corpus at the default location
mkdir -p data/National_Research_Database
# copy CSV/text files there

# Option B: point to wherever the corpus lives
export NRG_DATA_SOURCE_DIR=/path/to/National_Research_Database
python scripts/ingest_nrg_db.py
python scripts/ingest_qdrant.py
```

### Switching LLM Providers

NRG is model-agnostic. Change `LLM_PROVIDER` in `.env` (no code changes needed):

| Provider | `.env` value | Required key |
|----------|-------------|--------------|
| Gemini | `gemini` | `GEMINI_API_KEY` |
| OpenAI | `openai` | `OPENAI_API_KEY` |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` |
| NVIDIA | `nvidia` | `NVIDIA_API_KEY` |
| Local LLaMA | `local_llama` | none (set `LLAMA_CPP_URL`) |

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
# Fast local gate used for handoff evidence
MAX_FAST_SECONDS=900 PYTEST_WORKERS=auto scripts/run_test_suite.sh --fast

# Specific test categories
.venv/bin/pytest tests/security/ -q
.venv/bin/pytest tests/benchmarks/ -q
.venv/bin/pytest tests/api/ -q
```

### Critical Query Benchmarks

```bash
# Run Dhairya SQL benchmark (17 queries)
pytest tests/benchmarks/test_dhairya_regression.py -v

# Capture the three critical query evidence artifacts
.venv/bin/python scripts/capture_killer_query_evidence.py
```

### Security Testing

```bash
# Run PII compliance tests
pytest tests/security/test_pii_compliance.py -v

# Run the full local red-team replay with bounded startup
DATABASE_URL=sqlite:///$PWD/data/nrg_research.db \
  .venv/bin/python scripts/red_team_live_replay.py \
  --start-api \
  --api-base http://127.0.0.1:8045 \
  --startup-timeout 60 \
  --timeout 30 \
  --workers 1 \
  --chunk-size 5 \
  --evidence evidence/$(date +%F)/red_team_replay.md
```

---

## Production Deployment

### Docker Compose (Recommended)

```bash
# Full local container stack
docker compose up -d

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

## Verified Local Performance

The 2026-04-26 local evidence uses the volumetric SQLite proxy, not the sovereign PostgreSQL cluster:

- Critical query P95: 25.04ms, 52.95ms, and 22.8ms
- Fast test-suite gate: 1572 passed, 63 skipped, 219 deselected in 250.34s
- Frontend production build: passes with Vite/TypeScript
- Compose configuration: `docker compose config --quiet` passes

The 1000-user P99 SLO must be executed on the sovereign Kubernetes target with PostgreSQL and Qdrant populated.

---

## Documentation

| Document | Description |
|----------|-------------|
| `Core_Idea_Clean.md` | Product specification and vision |
| `docs/SCHEMA.md` | Complete parsed table and column reference |
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

**Built for sovereign AI infrastructure with reproducible local evidence and explicit external-gate tracking.**
