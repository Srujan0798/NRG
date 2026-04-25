# TP-A1 — Demo Script Walkthrough + Screen Recording

**Owner:** TESTER  
**Estimated Duration:** 2–3 hours  
**Blockers:** None  
**Reference:** `.claude/rules/ux_audit_protocol.md` Section 10

---

## Objective

Execute the exact 10-step professor demo script in a real browser. Record everything. Note every failure, every console error, every layout issue, every delay >3 seconds. This is the single most important test for the ₹50L demo.

---

## Fortify Phase (Setup)

1. Ensure backend is running: `uvicorn src.api.main:app --port 8000`
2. Ensure frontend is running: `cd frontend && npm run dev`
3. Open Chrome in **Incognito/Private** window — no cached state, no extensions
4. Open DevTools → Console (keep open during entire walkthrough)
5. Open DevTools → Network (keep open during entire walkthrough)
6. Start screen recording (OBS, QuickTime, or similar)

---

## Elevate Phase (Execute The 10 Steps)

Execute EXACTLY these steps in order. Pause the recording to note any failure.

### STEP 1 — OPEN THE APP
- Navigate to `http://localhost:5173` (or production URL)
- **PASS if:** Page loads in <2 seconds, no console errors
- **FAIL if:** Blank page, console errors, >2s load

### STEP 2 — LOGIN AS RESEARCHER (Tier 1)
- Enter researcher credentials
- **PASS if:** Dashboard appears in <3 seconds, stats are real numbers
- **FAIL if:** Blank page, 404, stats show 0/null/undefined

### STEP 3 — RUN THE KEY DEMO QUERY
- Type: "Which institutes in India have the highest grant amount in renewable energy?"
- **PASS if:** Loading indicator appears, answer in <10 seconds, readable prose, citations visible, numbers formatted (₹ with commas)
- **FAIL if:** No loading indicator, >10s, raw JSON, no citations, unformatted numbers

### STEP 4 — FOLLOW-UP QUERY
- Type: "Now show the same for computer science"
- **PASS if:** Context maintained, different result, not repeated
- **FAIL if:** Same answer repeated, no context reference

### STEP 5 — SHOW SECURITY (PII BLOCK)
- Type: "Show all researchers with Aadhaar 1234 5678 9012"
- **PASS if:** Clean blocked message, professional notice
- **FAIL if:** Stack trace, raw error, red scary message

### STEP 6 — LOGOUT AND LOGIN AS INDUSTRY (Tier 3)
- Click logout, login as industry user
- **PASS if:** Redirected cleanly, dashboard looks visibly different
- **FAIL if:** Broken redirect, same dashboard as Tier 1

### STEP 7 — RUN SAME QUERY AS TIER 3
- Type the same query from Step 3
- **PASS if:** Answer more restricted, "Access restricted" visible
- **FAIL if:** Same detailed answer as Tier 1

### STEP 8 — SHOW AUDIT TRAIL
- Navigate to Audit / Activity / History section
- **PASS if:** Recent queries visible with timestamps, integrity check shows intact
- **FAIL if:** Blank page, no queries listed

### STEP 9 — KNOWLEDGE GRAPH (if in UI)
- Type: "Show me the research network around hydrogen fuel cells"
- **PASS if:** Visual graph appears
- **FAIL if:** Error, raw JSON, blank page

### STEP 10 — CLOSE AND REOPEN
- Close tab, reopen, navigate back
- **PASS if:** Prompted to log in, no broken state
- **FAIL if:** Still logged in (if should be expired), blank page

---

## Immortalize Phase (Evidence & Report)

1. Save screen recording to:
   ```
   evidence/2026-04-25/demo_sprint/A1_demo_walkthrough.mp4
   ```

2. Create failure log:
   ```
   evidence/2026-04-25/demo_sprint/A1_demo_failures.md
   ```
   Format:
   ```markdown
   # Demo Script Failures
   | Step | Test | Status | Issue | Severity |
   |------|------|--------|-------|----------|
   | 3 | Query response <10s | FAIL | Took 18s | HIGH |
   ```

3. Create console error log:
   ```
   evidence/2026-04-25/demo_sprint/A1_console_errors.log
   ```
   Copy every red error from DevTools Console.

4. Create network failure log:
   ```
   evidence/2026-04-25/demo_sprint/A1_network_failures.log
   ```
   List every 4xx/5xx request.

---

## Acceptance Criteria

- [ ] Screen recording exists and shows all 10 steps
- [ ] Failure log documents every deviation from PASS criteria
- [ ] Console error log lists every red error (target: 0)
- [ ] Network failure log lists every failed request (target: 0)
- [ ] If any Step has HIGH severity failure, it is reported immediately for fixing

---

## Rollback Plan

This is a testing task — no code changes. Safe to re-run anytime.
