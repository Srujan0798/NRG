---
paths:
  - "frontend/src/**/*.{ts,tsx}"
---

# Frontend Rules

- React with TypeScript, functional components only (no class components)
- Three persona dashboards: Researcher, Government, Industry
- API calls go through services/ layer (queryService.ts, etc.)
- Auth state managed by hooks/useAuth.ts
- Backend runs on localhost:8000, frontend on localhost:3000
- Vite proxies /api/* to backend
- Citation tokens format: [cite:pub_id:chunk_id] — render via CitationDrawer
