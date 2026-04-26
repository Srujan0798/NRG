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

## UX & Production Readiness (Non-Negotiable)

The professor sees UI, not tests. Every frontend deliverable must pass these before claiming DONE:

- **Zero console errors** — Chrome DevTools Console must be empty during normal use
- **Zero undefined/NaN/null visible** — every data field has null-checking before render
- **No raw JSON shown to users** — API responses parsed and formatted into readable prose
- **All error messages in plain English** — no stack traces, no error codes, no raw HTTP status
- **Mobile responsive at 375px** — Chrome DevTools iPhone SE simulation, no horizontal scroll
- **Lighthouse Performance ≥ 70, Accessibility ≥ 70**
- **Every button click has visual feedback** — loading state or immediate confirmation
- **All API calls have loading states** — skeleton, spinner, or "Thinking..." text
- **Empty states exist** — every table/chart that can be empty shows a message, not blank
- **No placeholder text** — `grep -ri "TODO\|FIXME\|lorem" frontend/src/` must return 0
- **Browser tab titles meaningful** — dynamic `<title>` per route, not "React App"
- **Tier differentiation visible** — Tier 1 and Tier 3 dashboards must LOOK different
- **No `alert()` anywhere** — use custom toast/modal components
- **Before claiming DONE**: run the 10-step acceptance test script from `.claude/rules/ux_audit/protocol.md` Section 10
