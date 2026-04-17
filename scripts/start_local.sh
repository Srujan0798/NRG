#!/bin/bash
# Local development deployment (no Docker required)

echo "=== NRG Local Deployment ==="

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt -q

# Start API
echo "Starting API server..."
python3 -c "
from src.api.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000)
" &

sleep 3

# Check status
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API running at http://localhost:8000"
    echo "   Docs: http://localhost:8000/docs"
else
    echo "❌ Failed to start API"
fi