# National Research Graph

## Quick Start (5 min)

```bash
git clone <this-repo-url>
# Or: git clone ~/Desktop/NRG (local development)
cd National-Research-Graph
make bootstrap   # Install deps
make up         # Start services
make seed       # Seed database
```

Now visit http://localhost:8000 for the API, http://localhost:3000 for UI.

## Architecture

`Core_Idea_Clean.md` is the product source of truth. The current implementation is a Phase 1 sovereign research-intelligence PoC with controlled cloud synthesis disabled by default.

The system has three primary layers:

1. **Orchestration Layer** - LangGraph-based agentic workflow
2. **Local Retrieval Layer** - SQLite today, with Qdrant/RAG wiring available when configured
3. **Security Layer** - API-side prompt/PII controls, JWT/RBAC, and audit chain

## Directory Structure

```
National-Research-Graph/
├── src/
│   ├── orchestration/       # LangGraph workflow
│   ├── skills/               # Text-to-SQL and RAG skills
│   ├── security/            # Security gateway, RBAC, PII
│   │   ├── gateway/          # Prompt sanitiser
│   │   └── pii/              # Tokenizer, FPE, Presidio
│   └── api/                  # FastAPI endpoints
├── tests/
│   ├── security/             # Security test suite
│   │   └── redteam/           # Red-team attack suites
│   ├── skills/               # Skill tests
│   └── uat/                  # User acceptance tests
├── scripts/                   # Deployment & utilities
├── docs/
│   ├── compliance/           # DPDP 2023 compliance
│   ├── security/             # Security documentation
│   ├── strategy/             # Pitch deck, blueprints
│   ├── technical/             # Architecture reports
│   └── uat/                  # UAT reports
├── frontend/                 # React UI (3 personas)
└── infrastructure/
    └── kong/                 # Kong Gateway configs
```

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for full deployment)
- Node.js 18+ (for frontend)

### Local Development

```bash
# Install dependencies
pip install -e .

# Start API server
python3 -m src.api.main

# Or use the health check script
bash scripts/health_check.sh

# API available at: http://localhost:8000
# API Docs at: http://localhost:8000/docs
```

### With Docker

```bash
# Deploy all services
docker-compose up -d

# Or use Kong Gateway
docker-compose -f infrastructure/kong/docker-compose.yml up -d
```

## Key Features

### Zero Data Leakage
- Raw research data stays inside the local deployment boundary.
- Cloud synthesis is disabled unless `CLOUD_SYNTHESIS_ALLOWED=true`.
- When cloud synthesis is enabled, only minimized sanitized evidence packets may be sent.
- Query responses expose warnings, retrieval sources, and synthesis provenance.

### Security Controls
- API-side PII and prompt-injection checks are active.
- JWT authentication and 3-persona tier behavior are wired.
- HMAC audit logging exists for query and LLM-call events.
- Kong gateway, formal compliance attestation, production rate limits, and full DPDP workflows are roadmap items unless verified by executable tests.

### Three User Personas
1. **Researcher** - Granular data access
2. **Government** - Analytics & trends
3. **Industry** - Partnership opportunities

### Skills
- **Text-to-SQL**: Natural language to SQL with schema-only prompts
- **RAG**: Local embeddings with Qdrant retrieval
- Both include RBAC filtering and audit logging

## Database

Current data:
- **200** Researchers
- **24** Institutions
- **500** Publications
- **50** Labs
- **100** Funding Records

## Testing

```bash
# Run security tests
pytest tests/security/test_gateway.py -v

# Run PII compliance tests  
pytest tests/security/test_pii_compliance.py -v

# Run UAT tests
python tests/uat/run_all_personas.py

# Run all tests
pytest tests/ -v
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

## Project Status

### Phase 1 — PoC (Current)

| Component | Status |
|-----------|--------|
| FastAPI backend routes | Wired |
| JWT authentication and persona shaping | Wired |
| LangGraph orchestration pipeline | Wired |
| Text-to-SQL sandbox | Wired, still being hardened |
| Query warnings/provenance metadata | Wired |
| Root database path determinism | Wired through `DATABASE_URL` |
| `/query/graph` | DB-backed PoC endpoint |
| Qdrant/RAG | Config-normalized; requires Qdrant and embeddings |
| Local SLM | Optional setup |
| Cloud synthesis | Explicit opt-in with minimized evidence |

### Phase 2 — Scaling (Planned)

| Component | Status |
|-----------|--------|
| PostgreSQL migration (from SQLite) | ⬜ Pending |
| Qdrant vector DB with real embeddings | ⬜ Pending |
| Local SLM (Llama 3 8B) synthesis | ⬜ Pending |
| Kong Gateway production deployment | ⬜ Pending |
| 600GB data ingestion pipeline | ⬜ Pending |

### Phase 3 — Production (Planned)

| Component | Status |
|-----------|--------|
| Bare-metal sovereign deployment | ⬜ Pending |
| UAT with real stakeholders | ⬜ Pending |
| Performance benchmarking under load | ⬜ Pending |

See [Core_Idea_Clean.md](Core_Idea_Clean.md) and [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) for the current architecture. Older reports are historical unless backed by current tests.

## Honest Status (What Works / What Doesn't)

### Working Today
- JWT authentication with 3-tier RBAC (researcher, government, industry)
- Text-to-SQL path with read-only SQLite sandbox
- PII detection (Aadhaar, PAN, phone, email) with blocking
- Prompt injection detection with narrowed high-confidence patterns
- Immutable HMAC-SHA256 audit log with chain verification
- FastAPI backend with /login, /query, /researchers, /stats, /publications, and /query/graph endpoints
- React frontend with persona-specific views
- SQLite database with 200 researchers, 500 publications, 24 institutions

### NOT Working Today (Requires Setup)
- **Cloud LLM Synthesis**: Requires provider key and `CLOUD_SYNTHESIS_ALLOWED=true`; otherwise local/rule-based fallback is used
- **Qdrant/RAG**: Requires Qdrant service plus embedding build
- **Local SLM**: Requires llama.cpp/local model setup
- **Kong Gateway**: Not a Phase 1 runtime requirement
- **PostgreSQL**: Using SQLite for PoC — migration to PostgreSQL pending

## License

Confidential - Government of India / IIT Gandhinagar

## Contact

For questions or issues, contact the project team at IIT Gandhinagar.
