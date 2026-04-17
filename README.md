# National Research Graph - Phase 3 Complete

## Overview

This repository contains the **complete Phase 3 implementation** of the National Research Intelligence Platform for India - a sovereign AI system for querying 600GB of confidential research data with zero data leakage.

**Status**: ✅ Phase 3 Complete - Production Ready

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

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for full deployment)
- Node.js 18+ (for frontend)

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

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
docker-compose -f docker-compose-production.yml up -d

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
- **51** Researchers
- **10** Institutions (IIT Bombay, Delhi, Madras, etc.)
- **80** Publications
- **20** Research Labs
- **40** Funding Records

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

## Phase 3 Deliverables

| Component | Status |
|-----------|--------|
| Kong AI Gateway (DLP, Rate Limiting, Audit) | ✅ Complete |
| React Frontend (3 Persona Views) | ✅ Complete |
| DPDP 2023 Compliance (12 clauses) | ✅ Complete |
| Red-team Security Testing | ✅ Complete |
| UAT (50 scenarios, 3 personas) | ✅ Complete |
| National Pitch Deck | ✅ Complete |
| Export Blueprint | ✅ Complete |
| Architecture Report | ✅ Complete |

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