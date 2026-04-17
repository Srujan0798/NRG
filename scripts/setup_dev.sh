#!/bin/bash

echo "Setting up NRG Phase 2 Development Environment..."

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    exit 1
fi

echo "Creating Python virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Creating necessary directories..."
mkdir -p .protocol
mkdir -p logs
mkdir -p data

echo "Setting up environment variables..."
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
DATABASE_URL=postgresql://nrg_user:nrg_password@localhost:5432/nrg_research
QDRANT_HOST=localhost
QDRANT_PORT=6333
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LOG_LEVEL=INFO
EOF
fi

echo "Running basic validation..."
python3 -c "from src.orchestration.graph import NRGWorkflow; print('✓ Orchestration module OK')"
python3 -c "from src.skills.text_to_sql.skill import TextToSQLSkill; print('✓ Text-to-SQL skill OK')"
python3 -c "from src.skills.rag.skill import RAGSkill; print('✓ RAG skill OK')"

echo ""
echo "====================================="
echo "Setup Complete!"
echo "====================================="
echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start the services (requires Docker):"
echo "  docker-compose up -d"
echo ""
echo "To run tests:"
echo "  pytest tests/"
echo ""
echo "To run demo:"
echo "  python src/orchestration/graph.py --test-mode"
