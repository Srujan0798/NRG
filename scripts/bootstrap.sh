#!/usr/bin/env bash
set -euo pipefail

# NRG Bootstrap Script
# Creates a reproducible Python virtual environment

PY="${PYTHON:-python3.11}"
VENV_DIR="${VENV:-.venv}"

echo "🔧 NRG Bootstrap"
echo "================"

# Check Python version
if ! command -v "$PY" &> /dev/null; then
    echo "❌ Python 3.11 not found. Please install Python 3.11."
    echo "   macOS: brew install python@3.11"
    echo "   Ubuntu: sudo apt install python3.11 python3.11-venv"
    exit 1
fi

PYTHON_VERSION=$($PY --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
echo "✓ Found Python $PYTHON_VERSION"

# Remove old broken venvs
if [ -d ".venv311" ]; then
    echo "🗑️  Removing broken .venv311"
    rm -rf .venv311
fi

if [ -d "venv" ]; then
    echo "🗑️  Removing old venv"
    rm -rf venv
fi

# Create fresh venv
echo "📦 Creating virtual environment in $VENV_DIR"
"$PY" -m venv "$VENV_DIR"

# Activate and upgrade
source "$VENV_DIR/bin/activate"
pip install -U pip setuptools wheel

# Install project
echo "📥 Installing NRG and dependencies..."
pip install -e ".[dev]"

echo ""
echo "✅ Bootstrap complete!"
echo ""
echo "Activate with: source $VENV_DIR/bin/activate"
echo "Run tests with: make test"
