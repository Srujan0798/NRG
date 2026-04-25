# TP-A2 — Dashboard Data Binding Verification

**Owner:** FRONTEND  
**Estimated Duration:** 2–3 hours  
**Blockers:** None  
**Reference:** `.claude/rules/ux_audit_protocol.md` Section 1.2

---

## Objective

Verify that dashboard data is actually bound to live API responses for all 3 tiers. The dashboard must show real numbers, different data per tier, and handle empty/null states gracefully.

---

## Current State

- `/researchers` endpoint returns wrapped `{"results": [...]}`
- Frontend may expect flat array `[]`
- Dashboards render shells but live API binding is unverified in browser
- Tier 1, Tier 2, Tier 3 dashboards exist but differentiation is unverified

---

## Fortify Phase (Read & Audit)

1. Read the dashboard components:
   ```bash
   find frontend/src -name "*Dashboard*" -o -name "*dashboard*" | grep -v node_modules
   ```
2. Read the API service layer:
   ```bash
   find frontend/src/services -type f
   ```
3. Check what `/stats` or `/researchers` returns for each tier:
   ```bash
   curl -s http://localhost:8000/stats -H "Authorization: Bearer $T1_TOKEN" | python -m json.tool
   curl -s http://localhost:8000/stats -H "Authorization: Bearer $T3_TOKEN" | python -m json.tool
   ```
4. Open browser DevTools → Network tab. Load dashboard. Check if API calls fire and what they return.

---

## Elevate Phase (Fix & Verify)

1. **Verify API response shape matches frontend expectation:**
   - If API returns `{"results": [...]}` but frontend expects `[]`, fix the frontend parser OR the API wrapper
   - Add console logging temporarily to see what arrives: `console.log("API response:", data)`

2. **Ensure all 3 tiers show DIFFERENT data:**
   - Tier 1 (Researcher): full details, names, emails, institutions
   - Tier 2 (Government): aggregated stats, policy view
   - Tier 3 (Industry): limited, anonymized
   - If all 3 look identical, the RBAC filtering is not reaching the frontend

3. **Handle empty/null/undefined states:**
   - Every stat card must show "0" or "No data" explicitly — never blank
   - Every chart must have an empty-state message
   - Add null-coalescing: `value ?? 0`, `data?.length ?? 0`

4. **Verify real numbers (not hardcoded):**
   - Check that dashboard numbers change when backend data changes
   - Add a new researcher via API, refresh dashboard, verify count increments

5. **Test error states:**
   - Kill backend mid-request — dashboard should show error message, not infinite spinner
   - Return 403 from API — dashboard should show tier-restricted message

---

## Immortalize Phase (Evidence)

1. Screenshots for each tier:
   ```
   evidence/2026-04-25/demo_sprint/A2_tier1_dashboard.png
   evidence/2026-04-25/demo_sprint/A2_tier2_dashboard.png
   evidence/2026-04-25/demo_sprint/A2_tier3_dashboard.png
   ```

2. API response comparison:
   ```
   evidence/2026-04-25/demo_sprint/A2_api_responses.json
   ```
   Contains the raw JSON from `/stats` for all 3 tiers, showing they are different.

3. Fix log:
   ```
   evidence/2026-04-25/demo_sprint/A2_fixes.md
   ```
   List every fix made, file changed, before/after behavior.

---

## Acceptance Criteria

- [ ] Tier 1 dashboard shows real numbers from API (not hardcoded)
- [ ] Tier 3 dashboard is visibly different from Tier 1 (different cards, different data)
- [ ] Empty states exist for every widget that can have no data
- [ ] No `undefined` / `null` / `NaN` visible anywhere on dashboard
- [ ] API response comparison shows different JSON for each tier
- [ ] `npm run build` passes with 0 ESLint errors

---

## Rollback Plan

If dashboard breaks completely, revert the changed component files. Keep backup of working state before changes.
