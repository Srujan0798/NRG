#!/bin/bash

echo "Starting NRG Phase 2 Deployment..."

echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        echo "Docker Compose is not available."
        exit 1
    fi
else
    COMPOSE_CMD="docker-compose"
fi

echo "Building Docker images..."
$COMPOSE_CMD -f docker-compose.yml build

echo "Starting services..."
$COMPOSE_CMD -f docker-compose.yml up -d

echo "Waiting for services to be ready..."
sleep 10

echo "Checking service health..."
curl -s http://localhost:6333/health || echo "Qdrant not ready"
curl -s http://localhost:5432 || echo "PostgreSQL not ready"

echo ""
echo "====================================="
echo "Deployment Complete!"
echo "====================================="
echo ""
echo "Services:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Qdrant: localhost:6333"
echo "  - Kong Gateway: localhost:8000"
echo ""
echo "Next steps:"
echo "  1. Initialize database: python scripts/init_db.py"
echo "  2. Ingest synthetic data: python scripts/ingest_synthetic.py"
echo "  3. Run tests: pytest tests/"
