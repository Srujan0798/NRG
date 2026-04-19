#!/bin/bash
# NRG Smoke Test Script
# Quick health check for the full stack

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
DEMO_RESEARCHER_PASSWORD="${DEMO_RESEARCHER_PASSWORD:-researcher-pass}"

echo "🧪 NRG Smoke Tests"
echo "=================="
echo "Testing: $BASE_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected=$3
    local data=$4
    local auth=$5
    
    echo -n "Testing $method $endpoint... "
    
    if [ -n "$data" ]; then
        if [ -n "$auth" ]; then
            response=$(curl -s -w "%{http_code}" -X "$method" "$BASE_URL$endpoint" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $auth" \
                -d "$data")
        else
            response=$(curl -s -w "%{http_code}" -X "$method" "$BASE_URL$endpoint" \
                -H "Content-Type: application/json" \
                -d "$data")
        fi
    else
        if [ -n "$auth" ]; then
            response=$(curl -s -w "%{http_code}" "$BASE_URL$endpoint" \
                -H "Authorization: Bearer $auth")
        else
            response=$(curl -s -w "%{http_code}" "$BASE_URL$endpoint")
        fi
    fi
    
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" = "$expected" ]; then
        echo -e "${GREEN}✓ $http_code${NC}"
        return 0
    else
        echo -e "${RED}✗ Got $http_code, expected $expected${NC}"
        echo "Response: $body"
        return 1
    fi
}

# Test health endpoint
test_endpoint "GET" "/health" "200"

# Test login
echo -n "Testing POST /login... "
login_response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"researcher_user","password":"'"$DEMO_RESEARCHER_PASSWORD"'"}')
http_code="${login_response: -3}"
body="${login_response%???}"

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ $http_code${NC}"
    TOKEN=$(echo "$body" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "  Got access token: ${TOKEN:0:20}..."
else
    echo -e "${RED}✗ Login failed: $http_code${NC}"
    echo "Response: $body"
    exit 1
fi

# Test authenticated endpoints
test_endpoint "GET" "/researchers" "200" "" "$TOKEN"
test_endpoint "GET" "/stats" "200" "" "$TOKEN"
test_endpoint "GET" "/publications?limit=5" "200" "" "$TOKEN"

# Test query endpoint
echo -n "Testing POST /query... "
query_response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/query" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"query":"find researchers in Gujarat"}')
http_code="${query_response: -3}"

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ $http_code${NC}"
else
    echo -e "${RED}✗ Query failed: $http_code${NC}"
    exit 1
fi

# Test LLM health
test_endpoint "GET" "/health/llm" "200" "" "$TOKEN"

echo ""
echo -e "${GREEN}✅ All smoke tests passed!${NC}"
