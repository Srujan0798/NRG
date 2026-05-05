#!/usr/bin/env bash
set -euo pipefail

# NRG Remote Setup - one-command setup for new machines
# Usage: bash scripts/nrg-remote-setup.sh

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "============================================"
echo "NRG Remote Setup"
echo "============================================"
echo "Repo: $REPO_ROOT"
echo ""

# 1. Check Python
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo "ERROR: Python not found. Install Python 3.11+ first."
    exit 1
fi

PY_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
echo "Python: $PY_VERSION"

# 2. Check Node
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "Node: $NODE_VERSION"
else
    echo "WARNING: Node not found. Frontend will not build."
fi

# 3. Create venv if missing
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    $PYTHON -m venv .venv
fi

# 4. Install Python deps
echo "Installing Python dependencies..."
.venv/bin/pip install --quiet --upgrade pip
if [ -f "requirements.txt" ]; then
    .venv/bin/pip install --quiet -r requirements.txt
elif [ -f "pyproject.toml" ]; then
    .venv/bin/pip install --quiet -e ".[dev]"
else
    echo "WARNING: No requirements.txt or pyproject.toml found."
fi

# 5. Install frontend deps
if [ -d "frontend" ] && command -v npm &> /dev/null; then
    echo "Installing frontend dependencies..."
    cd frontend
    if [ -f "package-lock.json" ]; then
        npm ci --silent
    else
        npm install --silent
    fi
    cd ..
fi

# 6. Start services if Docker is available
if command -v docker &> /dev/null && [ -f "docker-compose.yml" ]; then
    echo "Starting Docker services (PostgreSQL, Qdrant, Redis)..."
    docker compose up -d --quiet-pull postgres qdrant redis 2>/dev/null || echo "WARNING: docker compose up failed. You may need to start services manually."
else
    echo "WARNING: Docker not available. Start PostgreSQL/Qdrant/Redis manually."
fi

# 7. Verify workflow
echo ""
echo "Running workflow verification..."
if [ -x ".venv/bin/python" ]; then
    .venv/bin/python .claude/scripts/nrg-verify-workflow.py
else
    "$PYTHON" .claude/scripts/nrg-verify-workflow.py
fi

echo ""
echo "============================================"
echo "Setup complete."
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and fill secrets"
echo "  2. Start backend:  .venv/bin/python -m uvicorn src.api.main:app --reload --port 8000"
echo "  3. Start frontend: cd frontend && npm run dev"
echo "  4. Run tests:      bash scripts/run_test_suite.sh"
echo ""
echo "Remote sync: git fetch nrg && git rev-list --left-right --count main...nrg/main && .venv/bin/python .claude/scripts/nrg-verify-workflow.py"
echo "============================================"
