---
name: deploy-local
description: Start the full NRG stack locally (API + frontend + services). Use /deploy-local to run.
allowed-tools: Bash(docker-compose *) Bash(.venv/bin/python *) Bash(npm *) Bash(curl *)
---

# Local Deployment

Start the full NRG stack:

1. Check Docker is running:
```bash
docker info > /dev/null 2>&1 && echo "Docker OK" || echo "Docker not running"
```

2. Start infrastructure:
```bash
cd /Users/srujansai/Desktop/NRG && docker-compose up -d postgres qdrant redis
```

3. Start API:
```bash
cd /Users/srujansai/Desktop/NRG && .venv/bin/python -m uvicorn src.api.main:app --reload --port 8000 &
```

4. Start frontend:
```bash
cd /Users/srujansai/Desktop/NRG/frontend && npm run dev &
```

5. Health check:
```bash
sleep 3 && curl -s http://localhost:8000/health | python -m json.tool
```

6. Report: which services are up, which are down
