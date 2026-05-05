# POINTER: Frontend Structure

> **Do not trust this file as the source of truth.** Read the actual files listed below and verify against `Core_Idea_Clean.md` UX requirements.

## Where to Read

| Topic | Actual Source Files | What to Verify |
|-------|--------------------|----------------|
| **Entry Point** | `frontend/src/main.tsx`, `frontend/src/App.tsx` | Router, auth provider, theme |
| **Routes** | `frontend/src/App.tsx` | All routes defined, lazy loading |
| **Dashboards** | `frontend/src/views/ResearcherDashboard.tsx`, `GovernmentDashboard.tsx`, `IndustryDashboard.tsx` | Tier-specific views exist |
| **Answer Panel** | `frontend/src/views/AnswerEngine/` | Answer display, citations, SQL, audit ID |
| **Components** | `frontend/src/components/` | Login, Skeleton, ErrorBoundary, SkipLink, NetworkStatusBanner |
| **Auth Hook** | `frontend/src/hooks/useAuth.ts` | Token management, persona state |
| **API Services** | `frontend/src/services/authService.ts`, `dataService.ts` | API clients |
| **Tests** | `frontend/src/__tests__/`, `frontend/tests/e2e/` | Jest + Playwright tests |

## Verification Commands

```bash
# Check App.tsx routes
grep -n "Route\|path=" frontend/src/App.tsx | head -20

# Check dashboards exist
ls frontend/src/views/ResearcherDashboard.tsx frontend/src/views/GovernmentDashboard.tsx frontend/src/views/IndustryDashboard.tsx

# Check answer engine views
ls frontend/src/views/AnswerEngine/

# Check components
ls frontend/src/components/ | head -20

# Check hooks
ls frontend/src/hooks/

# Check services
ls frontend/src/services/

# Check tests
ls frontend/src/__tests__/ frontend/tests/e2e/ | head -10
```

## Requirements to Verify Against

From `Core_Idea_Clean.md`:
- Login screen → query input → answer panel → audit drawer
- Tier-aware UI (different dashboards per persona)
- No stack traces, no `undefined`, no blank skeleton > 200ms
- Answer must show: citations, SQL, source data, audit proof
- Accessibility: keyboard nav, screen reader, reduced motion

**Read the actual source files. Do not trust this pointer.**
