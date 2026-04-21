.PHONY: bootstrap up down test seed lint fmt e2e clean ingest benchmark venv spacy-model migrate migrate-create clean-db local-llm local-llm-stop local-llm-status

PYTHON := .venv/bin/python

help:
	@echo "NRG Makefile Commands"
	@echo "==================="
	@echo "make bootstrap - Install dependencies and setup environment"
	@echo "make up - Start all services (docker)"
	@echo "make down - Stop all services"
	@echo "make test - Run test suite"
	@echo "make seed - Seed database with sample data"
	@echo "make lint - Run linters"
	@echo "make fmt - Format code"
	@echo "make clean - Remove generated files"

bootstrap: venv

venv:
	@bash scripts/bootstrap.sh

test:
	@$(PYTHON) -m pytest -q

fmt:
	@$(PYTHON) -m black src tests
	@$(PYTHON) -m ruff check --fix src tests

lint:
	@$(PYTHON) -m ruff check src tests

typecheck:
	@$(PYTHON) -m mypy src

up:
	docker compose --profile dev up -d
	@echo "Services started. API: http://localhost:8000, UI: http://localhost:3000"

down:
	docker compose down --volumes --remove-orphans 2>/dev/null || true
	@echo "Services stopped."

seed:
	@echo "Seeding database..."
	@$(PYTHON) scripts/seed_relations.py
	@echo "Database seeded."

clean:
	rm -rf .venv
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete."

dev:
	@$(PYTHON) -m uvicorn src.api.main:app --reload --port 8000

ingest-sqlite:
	@echo "Ingesting NRG data into SQLite..."
	@$(PYTHON) scripts/ingest_nrg_db.py
	@echo "SQLite ingest complete."

ingest-qdrant:
	@echo "Ingesting research documents into Qdrant..."
	@$(PYTHON) scripts/ingest_qdrant.py --fallback-model
	@echo "Qdrant ingest complete."

ingest-all: ingest-sqlite ingest-qdrant

qdrant-up:
	@docker run -d --name qdrant -p 6333:6333 qdrant/qdrant 2>/dev/null || echo "Qdrant already running or Docker unavailable"

qdrant-down:
	@docker stop qdrant 2>/dev/null && docker rm qdrant 2>/dev/null || echo "Qdrant not running"

api-test:
	@$(PYTHON) -m pytest tests/api/ -v --tb=short

coverage:
	@$(PYTHON) -m pytest tests/ -q --cov=src --cov-report=term-missing --ignore=tests/e2e --ignore=tests/frontend -k "not (test_rag_tier_filtering or test_tier_filtering_rag)"

spacy-model:
	@$(PYTHON) -m spacy download en_core_web_sm

migrate:
	@DATABASE_URL=sqlite:///src/data/nrg_research.db $(PYTHON) -m alembic upgrade head

migrate-create:
	@DATABASE_URL=$(DATABASE_URL) $(PYTHON) -m alembic revision --autogenerate -m "$(MSG)"

migrate-down:
	@DATABASE_URL=sqlite:///src/data/nrg_research.db $(PYTHON) -m alembic downgrade -1

clean-db:
	@rm -f src/data/nrg_research.db && echo "Database removed."

local-llm:
	@echo "Starting local LLM server (Gemma-2B Q4_K_M on :8080)..."
	@mkdir -p logs
	@.venv/bin/python scripts/start_local_llm.py --daemon
	@sleep 2
	@for i in $$(seq 1 30); do \
		if curl -s http://localhost:8080/health | grep -q healthy; then \
			echo "Local LLM ready."; exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "Timeout waiting for local LLM."

local-llm-stop:
	@pkill -f "start_local_llm.py" 2>/dev/null && echo "Local LLM stopped." || echo "Local LLM not running."

local-llm-status:
	@curl -s http://localhost:8080/health 2>/dev/null || echo "Local LLM not responding on :8080"

.DEFAULT_GOAL := help
