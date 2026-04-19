#!/bin/bash
# Launch NRG Dashboard - Starts API and Frontend

set -e

echo "🚀 NRG Dashboard Launcher"
echo "========================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if already running
API_PID=$(lsof -ti:8000 2>/dev/null || true)
FRONTEND_PID=$(lsof -ti:3000 2>/dev/null || true)

if [ -n "$API_PID" ]; then
    echo "⚠️  API already running on port 8000 (PID: $API_PID)"
else
    echo "📡 Starting API server on port 8000..."
    source .venv/bin/activate
    python -m uvicorn src.api.main:app --reload --port 8000 &
    API_PID=$!
    echo $API_PID > /tmp/nrg_api.pid
    sleep 3
    echo -e "${GREEN}✅ API started${NC}"
fi

if [ -n "$FRONTEND_PID" ]; then
    echo "⚠️  Frontend already running on port 3000 (PID: $FRONTEND_PID)"
else
    echo "🎨 Starting frontend on port 3000..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/nrg_frontend.pid
    cd ..
    sleep 5
    echo -e "${GREEN}✅ Frontend started${NC}"
fi

echo ""
echo "🌐 Dashboard URLs:"
echo -e "${BLUE}  http://localhost:3000${NC} - Main Dashboard"
echo -e "${BLUE}  http://localhost:8000/docs${NC} - API Documentation"
echo -e "${BLUE}  http://localhost:8000/redoc${NC} - API Reference"
echo ""
echo "👤 Login Credentials:"
echo "  Username: researcher_user"
echo "  Password: researcher-pass"
echo ""
echo "  Username: gov_user"
echo "  Password: gov-pass"
echo "  "
echo "  Username: industry_user"
echo "  Password: industry-pass"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for interrupt
trap 'echo ""; echo "🛑 Stopping services..."; kill $API_PID $FRONTEND_PID 2>/dev/null || true; exit 0' INT
wait
