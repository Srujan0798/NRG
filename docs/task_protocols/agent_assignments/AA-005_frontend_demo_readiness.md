# Frontend Demo Readiness Checklist
## Task AA-005: Frontend Agent Assignment

**Project:** National Research Graph (NRG) - Phase 3 Demo Verification
**Agent:** Frontend Specialist
**Est. Time:** 2.5 hours

---

## Preamble

The NRG demo must work flawlessly in front of the professor. This checklist ensures every frontend interaction is verified before the walk-through.

---

## Task 5.1: Clean Build
**Time:** 5 min

```bash
cd frontend
npm run build
```

**Success criteria:** Exit code 0, no TypeScript errors, `dist/` folder created.

---

## Task 5.2: Fix ESLint Warnings
**Time:** 15 min

Fix these 7 warnings from the lint report:
1. `ResearcherDashboard.tsx` - Missing key in map
2. `StreamingAnswerPanel.tsx` - Unused state variable
3. `QueryPhaseProgress.tsx` - Prop type mismatch
4-7. [Check full list in `.eslint-report.txt`]

**Success criteria:** `npm run lint` exits 0.

---

## Task 5.3: Verify API Connection
**Time:** 10 min

Test all API proxy paths in `vite.config.ts`:
- `/api/*` → `http://127.0.0.1:8000/api/*`
- `/health` → `http://127.0.0.1:8000/health`
- `/query` → `http://127.0.0.1:8000/query`

**Success criteria:** Browser DevTools shows 200 for all three endpoints.

---

## Task 5.4: Login Flow - All 3 Personas
**Time:** 15 min

Test login with each persona:

| Persona | Username | Password | Expected |
|---------|----------|----------|----------|
| T1 Researcher | `researcher_user` | `researcher-pass` | Redirect to dashboard |
| T2 Government | `gov_user` | `government-pass` | Redirect to dashboard |
| T3 Industry | `industry_user` | `industry-pass` | Redirect to dashboard |

**Success criteria:** All three logins work, JWT stored in localStorage.

---

## Task 5.5: Query Flow - All 3 Personas
**Time:** 20 min

For each persona, test the query flow:

**T1 Researcher:**
```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Authorization: Bearer <T1_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest advances in machine learning?"}'
```
Expected: Full response with citations

**T2 Government:**
```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Authorization: Bearer <T2_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show aggregate funding by state"}'
```
Expected: Regional aggregation with geographic map

**T3 Industry:**
```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Authorization: Bearer <T3_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the top funded research areas?"}'
```
Expected: Aggregated/anonymized response with no individual PII

**Success criteria:** All three queries return appropriate tier-filtered responses.

---

## Task 5.6: Tier Differentiation (Colors, Badges)
**Time:** 20 min

Verify visual differentiation between tiers:

**Researcher (T1):**
- Color: `#3B82F6` (blue)
- Badge: "Researcher"
- Access: Full individual data

**Government (T2):**
- Color: `#10B981` (green)
- Badge: "Government"
- Access: Regional/state-level aggregates

**Industry (T3):**
- Color: `#8B5CF6` (purple)
- Badge: "Industry"
- Access: Institution-level only, PII stripped

**Check:** Open DevTools, inspect header badge element, verify CSS variables.

---

## Task 5.7: Response Rendering - Cloud/Local/Rule-Based
**Time:** 20 min

Test response rendering in three states:

1. **Cloud LLM active:** (Set `NRG_USE_LOCAL=0`) - Response shows "Cloud synthesis" badge
2. **Local LLM active:** (Default) - Response shows "Local model" badge
3. **Rule-based fallback:** - Response shows "Template" badge

**Success criteria:** Correct badge appears for each state.

---

## Task 5.8: Error Handling (5 Scenarios)
**Time:** 15 min

Test these error states:

| Scenario | Trigger | Expected Behavior |
|----------|---------|-------------------|
| Rate limited | Submit 15+ queries rapidly | "Rate limit exceeded" toast |
| Invalid token | Use expired JWT | Redirect to login with message |
| Query too long | Send >2000 char query | "Query too long" error inline |
| Service unavailable | Stop API server | "Service unavailable" with retry button |
| Consent missing | Query without consent | "Consent required" dialog |

**Success criteria:** All five scenarios show user-friendly error messages.

---

## Task 5.9: Responsive Check
**Time:** 10 min

Test at these breakpoints:
- Desktop: 1920x1080 ✓
- Laptop: 1440x900 ✓
- Tablet: 768x1024 ✓
- Mobile: 390x844 ✓

**Check:** Chrome DevTools → Toggle device toolbar → Navigate main pages.

**Success criteria:** No horizontal scroll, readable text, tappable buttons ≥44px.

---

## Task 5.10: Performance Verification
**Time:** 10 min

Run these checks:

```bash
# Lighthouse
npx lighthouse http://localhost:5173 --view

# Check metrics:
# - FCP < 2.5s
# - LCP < 4s
# - CLS < 0.1
# - Bundle size < 500KB gzipped
```

**Also verify:**
- Initial page load < 3 seconds on localhost
- Query response appears within 5 seconds (excluding LLM)
- No memory leaks after 10 consecutive queries

**Success criteria:** All metrics green.

---

## Submission

When all 10 tasks pass, write evidence to:
```
evidence/2026-04-25/frontend_readiness/
├── build_success.log
├── lint_clean.log
├── api_connection_test.log
├── login_flow_test.log
├── query_flow_test.log
├── tier_visual_verification.png
├── error_handling_test.log
├── responsive_test.log
└── performance_metrics.json
```

---

## Notes

- Tasks 5.1-5.3 are prerequisites — complete these before 5.4+
- If you find a bug not on this list, fix it and document it
- If an API endpoint is broken, escalate to backend agent immediately