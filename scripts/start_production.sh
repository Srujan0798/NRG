#!/bin/bash

# National Research Graph - Production Startup Script

echo "🚀 Starting National Research Graph Production Environment"
echo "======================================================"

# Kill any existing processes
echo "Stopping existing services..."
pkill -f "python3 -m src.api.main" 2>/dev/null
pkill -f "vite" 2>/dev/null

# Initialize fresh database
echo "Initializing database..."
cd "$(dirname "$0")/.."
rm -f nrg_research.db
python3 src/data/database.py

# Start API server
echo "Starting API server..."
nohup uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-4}" > api.log 2>&1 &

# Wait for API to start
sleep 3

# Test API
echo "Testing API..."
curl -s http://localhost:8000/health

# Build frontend
echo "Building frontend..."
cd frontend
rm -rf dist
npx vite build

# Start frontend preview
echo "Starting frontend..."
nohup npx vite preview --host > ../frontend.log 2>&1 &

sleep 2

echo ""
echo "✅ Production Environment Ready!"
echo "API: http://localhost:8000"
echo "Frontend: http://localhost:4173"
echo ""
echo "📋 Available Endpoints:"
echo "  GET /health              - System health"
echo "  GET /researchers          - List all researchers"
echo "  GET /researchers/{id}     - Get specific researcher"
echo "  POST /researchers         - Create new researcher"
echo "  POST /query               - Query researchers with filters"
echo ""
echo "📊 Database: SQLite (nrg_research.db)"
echo "🎯 Skills: .agents/skills/ (Model-agnostic)"
echo ""
echo "Use 'curl http://localhost:8000/researchers' to test data access"
