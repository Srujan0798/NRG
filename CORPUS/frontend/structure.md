# NRG Frontend Structure

## Overview

React SPA built with Vite. TypeScript. Tailwind CSS. Design system in `frontend/src/design-system/`.

## Entry Point

`frontend/src/main.tsx` → mounts App.tsx

## Routing (App.tsx)

| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | AnswerEngineHome | Landing + query input |
| `/login` | AnswerEngineLogin | Login page |
| `/app/researcher` | ResearcherDashboard (lazy) | Full data dashboard |
| `/app/government` | GovernmentDashboard (lazy) | Aggregated dashboard |
| `/app/industry` | IndustryDashboard (lazy) | Anonymized dashboard |
| `/app/answer/latest` | AnswerEngineAnswer | Latest query result |
| `/app/answer/audit` | AnswerEngineAudit | Audit drawer |
| `/audit/:eventId` | AuditEvent (lazy) | Single audit event detail |
| `/workspace` | ProductionWorkspace (lazy) | Production tools |

## Key Directories

| Directory | Contents |
|-----------|----------|
| `views/` | Dashboard views per persona (ResearcherDashboard, GovernmentDashboard, IndustryDashboard, FounderDashboard) |
| `pages/` | Standalone pages (AuditEvent, ProductionWorkspace) |
| `components/` | 50+ reusable components (Login, Skeleton, ErrorBoundary, SkipLink, NetworkStatusBanner, etc.) |
| `hooks/` | Custom hooks (useAuth, useTheme, useReducedMotion) |
| `services/` | API clients (authService, dataService) |
| `stores/` | State management |
| `design-system/` | ThemeProvider, design tokens, base styles |
| `lib/` | Utilities (telemetry, helpers) |
| `types/` | TypeScript type definitions |
| `styles/` | Global styles, Tailwind config |
| `assets/` | Static assets |
| `i18n/` | Internationalization |

## Lazy Loading

Dashboards and heavy pages are lazy-loaded to keep entry chunk small:
```typescript
const ResearcherDashboard = lazy(() => import('./views/ResearcherDashboard'))
const GovernmentDashboard = lazy(() => import('./views/GovernmentDashboard'))
const IndustryDashboard = lazy(() => import('./views/IndustryDashboard'))
```

## Key Features

- **Tier-aware UI:** Different dashboards per persona
- **Blocked prompt detection:** Frontend blocks PII queries before sending
- **Streaming answers:** `/api/query/stream` for progressive response
- **Audit drawer:** Shows SQL, citations, source data, audit ID
- **Accessibility:** Skip links, reduced motion, contrast checks
- **Telemetry:** First paint tracking, client telemetry to `/api/telemetry`

## Build

```bash
cd frontend
npm run build    # production build
npm run dev      # dev server
npm run test     # Jest tests
npm run lint     # ESLint
```
