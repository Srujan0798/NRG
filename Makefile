.PHONY: bootstrap up down test seed lint fmt e2e clean ingest benchmark venv spacy-model migrate migrate-create clean-db

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

.DEFAULT_GOAL := help
