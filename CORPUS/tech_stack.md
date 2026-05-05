# NRG Tech Stack

## Backend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11 | Runtime |
| FastAPI | Latest | API framework |
| Uvicorn | Latest | ASGI server |
| SQLAlchemy | 2.x | ORM |
| PostgreSQL | 16 | Primary database |
| Pydantic | 2.x | Data validation |
| Pytest | Latest | Testing |
| JWT (PyJWT) | Latest | Authentication |
| Qdrant Client | Latest | Vector store client |
| Redis | Latest | Cache |
| LangGraph | Latest | Query orchestration |
| LangChain | Latest | LLM tooling |
| OpenAI / Anthropic SDK | Latest | LLM providers |

## Frontend

| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18 | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | 6 | Build tool |
| Tailwind CSS | 3.x | Styling |
| Jest | 30 | Testing |
| Playwright | Latest | E2E testing |

## Infrastructure

| Technology | Purpose |
|-----------|---------|
| Docker + Docker Compose | Local development |
| Nginx | Reverse proxy, static files |
| Kong | API gateway, JWT validation |
| Kubernetes | Production orchestration |
| Prometheus | Metrics collection |
| Grafana | Metrics visualization |
| Qdrant | Vector database |
| Redis | Cache, sessions, rate limiting |

## DevOps

| Technology | Purpose |
|-----------|---------|
| GitHub Actions | CI/CD |
| Alembic | Database migrations |
| Ruff | Python linting |
| ESLint | JavaScript/TypeScript linting |

## Key Configuration

| Env Var | Purpose |
|---------|---------|
| `DATABASE_URL` | PostgreSQL connection |
| `QDRANT_HOST` / `QDRANT_PORT` | Vector store |
| `REDIS_URL` | Cache |
| `JWT_PRIVATE_KEY` / `JWT_PUBLIC_KEY` | Auth signing |
| `CLOUD_SYNTHESIS_ALLOWED` | External LLM toggle |
| `NRG_API_URL` | API base URL |
