# ==============================================================================
# NRG Makefile - Development and Deployment Commands
# ==============================================================================

.PHONY: help install dev build test lint clean logs health

# Default target
help:
	@echo "NRG - National Research Graph"
	@echo ""
	@echo "Development:"
	@echo "  make install         Install dependencies"
	@echo "  make dev            Start development environment"
	@echo "  make dev-backend    Start backend only"
	@echo "  make dev-frontend   Start frontend only"
	@echo ""
	@echo "Build:"
	@echo "  make build          Build Docker images"
	@echo "  make build-api      Build API Docker image"
	@echo "  make build-frontend Build frontend Docker image"
	@echo ""
	@echo "Test:"
	@echo "  make test           Run all tests"
	@echo "  make test-python     Run Python tests"
	@echo "  make test-frontend   Run frontend tests"
	@echo "  make test-e2e       Run E2E tests"
	@echo "  make lint           Run linters"
	@echo ""
	@echo "Operations:"
	@echo "  make logs           View logs"
	@echo "  make health         Check health endpoints"
	@echo "  make clean          Clean up containers and volumes"
	@echo "  make seed           Seed database"
	@echo ""
	@echo "Production:"
	@echo "  make prod           Start production environment"
	@echo "  make prod-build     Build for production"
	@echo ""

# ==============================================================================
# Development
# ==============================================================================

install:
	pip install uv
	uv pip install -e ".[dev]"

dev:
	docker compose up -d
	@echo "Services started. API: http://localhost:8000, Frontend: http://localhost:3000"

dev-backend:
	docker compose up -d postgres qdrant redis api
	@echo "Backend running at http://localhost:8000"

dev-frontend:
	docker compose up -d frontend
	@echo "Frontend running at http://localhost:3000"

down:
	docker compose down

# ==============================================================================
# Building
# ==============================================================================

build:
	docker compose build

build-api:
	docker compose build api

build-frontend:
	docker compose build frontend

build-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# ==============================================================================
# Testing
# ==============================================================================

test:
	uv pip install pytest pytest-cov pytest-xdist
	pytest tests/ -v --tb=short -n auto

test-python:
	uv pip install pytest pytest-cov
	pytest tests/ -v --tb=short

test-frontend:
	cd frontend && npm run test

test-e2e:
	cd frontend && npm run test:e2e

lint:
	uv pip install ruff mypy
	ruff check src tests
	mypy src

# ==============================================================================
# Operations
# ==============================================================================

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-frontend:
	docker compose logs -f frontend

health:
	@echo "Checking health endpoints..."
	@curl -s http://localhost:8000/health || echo "API not responding"
	@curl -s http://localhost:8000/health/all || echo "Health check failed"
	@echo ""
	@echo "Frontend: $$(docker compose exec -T frontend wget -q --spider http://localhost/ && echo 'OK' || echo 'FAIL')"

clean:
	docker compose down -v --remove-orphans
	docker system prune -f

seed:
	python scripts/seed_database.py

# ==============================================================================
# Production
# ==============================================================================

prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production environment running"

prod-logs:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

prod-restart:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# ==============================================================================
# Database
# ==============================================================================

db-migrate:
	python scripts/migrate.py

db-reset:
	docker compose down -v
	docker compose up -d postgres
	@echo "Waiting for postgres..." && sleep 5
	python scripts/seed_database.py

# ==============================================================================
# Development helpers
# ==============================================================================

fmt:
	uv pip install black isort
	black src tests
	isort src tests

secure-scan:
	./gitleaks detect --no-banner --verbose

.DEFAULT_GOAL := help
