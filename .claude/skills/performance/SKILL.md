---
name: performance
description: Performance benchmarking and regression detection. Use /performance to benchmark the current system.
allowed-tools: Bash(.venv/bin/python *) Bash(curl *) Bash(time *) Bash(docker *) Read Grep
---

# Performance Benchmark

Measure and track system performance. Compare against baselines.

## Benchmarks

### 1. API Response Time
```bash
API_URL=${ARGUMENTS:-http://localhost:8000}

# Login time
time curl -sf -X POST "$API_URL/login" -H "Content-Type: application/json" -d '{"username":"researcher_user","password":"researcher-pass"}' -o /dev/null

# Health endpoint (should be <50ms)
time curl -sf "$API_URL/health" -o /dev/null

# Get token for query test
TOKEN=$(curl -sf -X POST "$API_URL/login" -H "Content-Type: application/json" -d '{"username":"researcher_user","password":"researcher-pass"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Query response time (the main metric)
time curl -sf -X POST "$API_URL/query" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"query":"AI researchers in Gujarat"}' -o /dev/null
```

### 2. Test Suite Speed
```bash
cd /Users/srujansai/Desktop/NRG && time PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -q --tb=no 2>&1 | tail -3
```

### 3. Import Time (startup cost)
```bash
cd /Users/srujansai/Desktop/NRG && time .venv/bin/python -c "from src.api.main import app; print('API loaded')"
time .venv/bin/python -c "from src.orchestration.graph import run; print('Graph loaded')"
time .venv/bin/python -c "from src.skills.rag.embedder import Embedder; print('Embedder loaded')"
```

### 4. Database Query Speed
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -c "
import time, sqlite3
conn = sqlite3.connect('src/data/nrg_research.db')
queries = [
    'SELECT COUNT(*) FROM researchers',
    'SELECT * FROM researchers WHERE state=\"Maharashtra\" LIMIT 10',
    'SELECT r.name, p.title FROM researchers r JOIN researcher_publications rp ON r.id=rp.researcher_id JOIN publications p ON p.id=rp.publication_id LIMIT 20',
]
for q in queries:
    start = time.time()
    conn.execute(q).fetchall()
    ms = (time.time()-start)*1000
    print(f'  {ms:.1f}ms — {q[:60]}')
conn.close()
"
```

## Output
```
PERFORMANCE REPORT
  Login:        Xms (target: <200ms)
  Health:       Xms (target: <50ms)
  Query:        Xms (target: <5000ms)
  Test suite:   Xs  (target: <120s)
  API startup:  Xs  (target: <5s)
  DB queries:   Xms (target: <100ms each)

VERDICT: ON TARGET / REGRESSION DETECTED [details]
```

Update memory/perf_baselines.md with current numbers for future comparison.
