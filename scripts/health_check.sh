#!/bin/bash
# Health check script for NRG

echo "=== National Research Graph - Health Check ==="
echo ""

# Check API
echo "1. API Server:"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Running"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "   Status: OK"
else
    echo "   ❌ Not running (start with: python3 -m src.api.main)"
fi

# Check Database
echo ""
echo "2. Database:"
DB_PATH=$(python3 -c "from src.data.database import resolve_database_path; print(resolve_database_path())" 2>/dev/null)
if [ -n "$DB_PATH" ] && [ -f "$DB_PATH" ]; then
    COUNT=$(python3 -c "from src.data.database import get_sqlite_connection; c=get_sqlite_connection().cursor(); c.execute('SELECT COUNT(*) FROM researchers'); print(c.fetchone()[0])" 2>/dev/null)
    echo "   ✅ Exists ($COUNT researchers)"
else
    echo "   ❌ Not found"
fi

# Check Phase 3 files
echo ""
echo "3. Phase 3 Components:"
[ -d "infrastructure/kong" ] && echo "   ✅ Kong Gateway" || echo "   ❌ Kong Gateway"
[ -d "src/security/pii" ] && echo "   ✅ PII Security" || echo "   ❌ PII Security"
[ -d "tests/security/redteam" ] && echo "   ✅ Red-team Tests" || echo "   ❌ Red-team Tests"
[ -d "tests/uat" ] && echo "   ✅ UAT Tests" || echo "   ❌ UAT Tests"
[ -d "docs/strategy" ] && echo "   ✅ Strategy Docs" || echo "   ❌ Strategy Docs"

echo ""
echo "=== Health Check Complete ==="
