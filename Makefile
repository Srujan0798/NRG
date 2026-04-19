.PHONY: bootstrap up down test seed lint fmt e2e clean ingest benchmark

PYTHON := .venv/bin/python
UV := uv
POSTGRES_CONTAINER := nrg-postgres

help:
	@echo "NRG Makefile Commands"
	@echo "==================="
	@echo "make bootstrap    - Install dependencies and setup environment"
	@echo "make up        - Start all services (docker)"
	@echo "make down      - Stop all services"
	@echo "make test     - Run test suite"
	@echo "make seed     - Seed database with sample data"
	@echo "make lint     - Run linters"
	@echo "make fmt      - Format code"
	@echo "make e2e      - Run E2E tests"
	@echo "make clean    - Remove generated files"
	@echo "make ingest  SOURCE=<path> - Run ingestion pipeline"
	@echo "make bench   - Run benchmark harness"

bootstrap:
	@echo "Bootstrapping NRG environment..."
	@bash scripts/bootstrap.sh
	@echo "Bootstrap complete."

venv:
	@bash scripts/bootstrap.sh

up:
	docker compose --profile dev up -d
	@echo "Services started. API: http://localhost:8000, UI: http://localhost:3000"

down:
	docker compose down --volumes --remove-orphans 2>/dev/null || true
	@echo "Services stopped."

test:
	$(PYTHON) -m pytest tests/ -v --tb=short

test-unit:
	$(PYTHON) -m pytest tests/unit/ -v

test-integration:
	$(PYTHON) -m pytest tests/integration_tests.py -v

test-security:
	$(PYTHON) -m pytest tests/security/ -v

test-redteam:
	$(PYTHON) -m pytest tests/security/redteam/ -v

test-e2e:
	$(PYTHON) -m pytest tests/e2e/ -v

seed:
	@echo "Seeding database..."
	$(PYTHON) -c "from src.db.seed import seed_database; seed_database()"
	@echo "Database seeded."

lint:
	ruff check src/ tests/

fmt:
	ruff format src/ tests/

typecheck:
	mypy src/ --ignore-missing-imports || true

clean:
	rm -rf .protocol/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete."

dev:
	$(PYTHON) -m uvicorn src.api.main:app --reload --port 8000

ingest:
	@echo "Running ingestion pipeline..."
	$(PYTHON) scripts/ingest.py --input $(SOURCE)

benchmark:
	@echo "Running benchmark harness..."
	$(PYTHON) scripts/bench.py

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	docker compose ps

restart:
	make down && make up

.DEFAULT_GOAL := help