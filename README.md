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

The system implements a zero-data-leakage architecture with three primary layers:

1. **Orchestration Layer** - LangGraph-based agentic workflow
2. **Local Retrieval Layer** - PostgreSQL + Qdrant vector database  
3. **Security Layer** - Kong Gateway + DLP protection + DPDP 2023 compliance

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
- All research data stays in local PostgreSQL/Qdrant
- Only schema metadata sent to LLM (no data values)
- Complete audit trail for all queries

### Security Controls (Phase 3)
- ✅ Kong AI Gateway with DLP protection
- ✅ PII detection (Aadhaar, PAN, phone, email)
- ✅ Prompt injection prevention
- ✅ Tier-based rate limiting (100/50/20 req/min)
- ✅ Immutable audit logging
- ✅ DPDP 2023 compliance (12/12 clauses)

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

### Phase 1 — PoC (Complete)

| Component | Status |
|-----------|--------|
| LangGraph Orchestration Pipeline | ✅ Complete |
| Text-to-SQL Sandbox (read-only) | ✅ Complete |
| Schema Extractor (metadata-only to LLM) | ✅ Complete |
| PII Tokenizer (Aadhaar, PAN, phone) | ✅ Complete |
| Prompt Injection Detection | ✅ Complete |
| HMAC-SHA256 Immutable Audit Log | ✅ Complete |
| RBAC Middleware (3-tier) | ✅ Complete |
| JWT Authentication | ✅ Complete |
| React Frontend (3 persona views) | ✅ Complete |
| FastAPI Backend | ✅ Complete |
| Security Test Suite + Red-team | ✅ Complete |
| DPDP 2023 Compliance Mapping | ✅ Complete |
| Architecture Report | ✅ Complete |

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

See [docs/reports/FINAL_STATUS_REPORT.md](docs/reports/FINAL_STATUS_REPORT.md) for full details.

## Test Results

```
✅ test_pii_detection_aadhaar - PASSED
✅ test_pii_detection_pan - PASSED
✅ test_pii_detection_phone - PASSED
✅ test_prompt_injection_detection - PASSED
✅ test_sanitisation - PASSED
✅ test_query_validation - PASSED
```

## License

Confidential - Government of India / IIT Gandhinagar

## Contact

For questions or issues, contact the project team at IIT Gandhinagar.