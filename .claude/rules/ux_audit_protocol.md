---
paths:
 - "frontend/src/**/*.{ts,tsx}"
 - "frontend/*.html"
 - "frontend/*.css"
 - "frontend/public/**/*"
---

# NRG UX Audit Protocol — What The Professor Actually Sees

> **The professor does not care about your test suite, your HMAC chain, or your LangGraph nodes.**
> He opens a browser, clicks things, types things, and decides in 90 seconds whether this is worth ₹50 lakhs.
> Every item below must work perfectly — with no errors, no blank screens, no console noise, no broken layout — or the user experience fails.

---

## THE ONLY THING THAT MATTERS

The professor types a question. He gets a clear, fast, correct answer.
He clicks around. Nothing breaks.
He sees something that looks like a ₹50L product — not a hackathon pre-production module.
He asks "can I trust this data?" — you show him the audit trail in the UI.
He says yes.

Every item below either supports that moment or destroys it.
Test every single one. Fix every single one. No exceptions.

---

## 0. THE PROFESSOR PRINCIPLE (Add to Constitution)

**"The user sees UI, not tests."**

- A passing pytest suite means nothing if the login screen shows `undefined`.
- A 17/17 Dhairya benchmark means nothing if the query result is a raw JSON dump.
- A tamper-proof audit chain means nothing if the professor cannot find the "View Audit" button.
- Before claiming any frontend task DONE, walk through the 10-step acceptance test script in Section 10.
- Before any launch, run through every item in this protocol.

---

## 1. FIRST IMPRESSIONS (The 10-Second Test)

A non-technical person forms their opinion of software in the first 10 seconds.

### 1.1 — Login Screen

| # | Test | Status | Evidence |
|---|------|--------|----------|
| L1 | Page loads in under 2 seconds | | |
| L2 | Login form is centered, clean, not overflowing on any screen size | | |
| L3 | NRG logo and product name are visible and correctly spelled | | |
| L4 | Username and password fields have placeholder text | | |
| L5 | Pressing Enter in password field submits the form | | |
| L6 | Wrong credentials: clear human-readable error ("Invalid username or password") — not raw JSON, not 500 | | |
| L7 | Blank username/password: validation before API call fires | | |
| L8 | After successful login: lands on dashboard — not blank, not 404 | | |
| L9 | "Forgot password" link exists (even if just "contact admin") | | |
| L10 | Browser back button after login does not break state | | |

**Proof:** Screen recording of login flow for all 3 tiers, including wrong-credentials error.

---

### 1.2 — Dashboard (First Thing After Login)

| # | Test | Status | Evidence |
|---|------|--------|----------|
| D1 | Dashboard loads in under 3 seconds with real data (not infinite spinner) | | |
| D2 | Key stats visible: total researchers, institutions, publications, grants — real numbers, not 0/null | | |
| D3 | Every chart has a title — no unlabeled graphs | | |
| D4 | No chart shows "undefined", "NaN", "null", or "Error" | | |
| D5 | Tier 1 dashboard looks visibly different from Tier 3 | | |
| D6 | Navigation bar/sidebar complete — all links visible, labeled, clickable | | |
| D7 | No broken icons — no missing placeholders, no empty icon boxes | | |
| D8 | Color scheme consistent — not a mix of 5 different button colors | | |
| D9 | Fonts consistent — not 3 different sizes for the same heading | | |
| D10 | No horizontal scroll bar on desktop | | |

**Proof:** Screenshot of Tier 1 and Tier 3 dashboards side by side, showing visible difference.

---

## 2. THE SEARCH / QUERY BOX (The Core Feature)

If this breaks, the launch is over.

### 2.1 — Search Input Behavior

| # | Test | Status | Evidence |
|---|------|--------|----------|
| S1 | Search box visible, prominent, with placeholder text (e.g. "Ask anything about Indian research...") | | |
| S2 | Typing is responsive — no lag, no stutter | | |
| S3 | Pressing Enter submits — not just clicking button | | |
| S4 | While processing: loading indicator visible — NOT blank screen | | |
| S5 | Loading indicator disappears when result appears | | |
| S6 | Query >5 seconds: user sees "This is taking longer than usual..." — not silence | | |
| S7 | Search box NOT cleared after submit — user sees what they typed | | |
| S8 | User can submit new query without page refresh | | |
| S9 | Empty search: validation message — no blank API call | | |
| S10 | Long query (300+ chars): input handles gracefully — no overflow, no crash | | |

**Proof:** Screen recording of typing → waiting → result → second query.

---

### 2.2 — Query Results Display

| # | Test | Status | Evidence |
|---|------|--------|----------|
| R1 | Result is readable prose — not raw JSON, not Python dict, not `{"answer": "..."}` | | |
| R2 | Result has clear heading/label — not text with no context | | |
| R3 | Citations/sources visible below answer — "where did this come from?" | | |
| R4 | Table results: proper borders, aligned columns — not raw pipe characters | | |
| R5 | Numbers formatted (1,234 not 1234; ₹2.4 Cr not 240000000) | | |
| R6 | Result area has enough space — text not squashed or overflowing | | |
| R7 | Zero results: helpful message ("No data found. Try...") — not blank area | | |
| R8 | Backend error: "Something went wrong — please try again" — not stack trace, not 500 page | | |
| R9 | Long result: page scrolls naturally — no broken layout at 2+ pages | | |
| R10 | Tier 3 does not show personal details — shows "Access restricted" cleanly | | |

**Proof:** Screenshot of result with citations. Screenshot of zero-results state. Tier 1 vs Tier 3 for same query.

---

### 2.3 — Follow-Up Query (Multi-Turn)

| # | Test | Status | Evidence |
|---|------|--------|----------|
| FU1 | After first answer, follow-up maintains context | | |
| FU2 | Second answer visually distinct from first — not repeated | | |
| FU3 | Conversation history visible — scrollable Q&A | | |
| FU4 | "New conversation" or "Clear" button exists | | |
| FU5 | After clearing: previous results gone — no ghost content | | |

**Proof:** Screen recording of 3-turn conversation.

---

## 3. SEARCH FEATURE (Standalone)

If there is a separate search bar (researcher search, publication search, etc.):

| # | Test | Status | Evidence |
|---|------|--------|----------|
| SR1 | Returns results within 2 seconds for common terms ("IIT", "AI", "energy") | | |
| SR2 | Partial match works — "hydro" returns "hydrogen" | | |
| SR3 | Case-insensitive — "iit" and "IIT" same results | | |
| SR4 | Special characters (%, &, ', ", <, >) do not crash app | | |
| SR5 | No results: helpful message — not blank list | | |
| SR6 | Typing quickly does not fire 50 API calls — debounce exists | | |
| SR7 | Clicking result opens detail page — not 404 | | |
| SR8 | Back button returns to search results — not home page | | |
| SR9 | Search box retains query after returning | | |
| SR10 | Mobile: search, results, and details all readable without zooming | | |

**Proof:** Screen recording of search → click result → back → search again. One example with special characters.

---

## 4. NAVIGATION & LINKS

| # | Test | Status | Evidence |
|---|------|--------|----------|
| N1 | Every nav link works — click every single one | | |
| N2 | No link goes to 404 | | |
| N3 | No link opens to blank white page | | |
| N4 | Active page highlighted in navigation | | |
| N5 | Logo click goes to home/dashboard | | |
| N6 | Logout exists and works — ends session, redirects to login | | |
| N7 | After logout, back button does not re-enter app | | |
| N8 | Breadcrumbs or page titles exist — user knows where they are | | |
| N9 | External links open in new tab | | |
| N10 | Deep links work — shared URL loads correct page | | |

**Proof:** Click-through recording of every nav item. Show logout behavior.

---

## 5. LOADING STATES & EMPTY STATES

A blank white screen while loading = "the app is broken" in the professor's mind.

| # | Test | Status | Evidence |
|---|------|--------|----------|
| E1 | Every empty table has empty state message — not just blank | | |
| E2 | Every empty chart has placeholder — not empty chart area | | |
| E3 | Dashboard stats that are 0 show "0" explicitly — not blank/null | | |
| E4 | First-time Tier 3 login: guided text explaining access — not confusing empty dashboard | | |
| E5 | All API calls have loading state — no data "pops in" abruptly | | |
| E6 | Skeleton screens or spinners for slow operations — not frozen interface | | |
| E7 | Backend slow (>5s): UI communicates "still loading" — not silence | | |
| E8 | Page refresh preserves or re-fetches state — no blank wipe | | |
| E9 | Mobile slow network (3G): page still loads something useful | | |
| E10 | Session timeout: clear "Your session has expired. Please log in again." — not silent broken state | | |

**Proof:** Screenshot of every empty state. Recording of slow query with loading indicator.

---

## 6. ERROR HANDLING (What The User Sees)

| # | Test | Status | Evidence |
|---|------|--------|----------|
| ER1 | No raw stack traces visible anywhere — not even in browser console | | |
| ER2 | Network offline: "You appear to be offline. Please check your connection." | | |
| ER3 | API 500: "Something went wrong. Our team has been notified. Please try again." — not blank | | |
| ER4 | API 403: clear tier restriction message — not generic error | | |
| ER5 | API 422 (PII blocked): "This query contains sensitive information that cannot be processed." | | |
| ER6 | API 429: "You've made too many requests. Please wait a moment." | | |
| ER7 | Form validation errors next to relevant field — not top-of-page after submission | | |
| ER8 | Error messages disappear when user corrects issue | | |
| ER9 | Global error boundary exists — one component crash does not kill entire app | | |
| ER10 | All error messages in plain English — no jargon, no error codes visible | | |

**Proof:** Screenshot of PII-blocked message. Screenshot of rate-limit message. Proof of global error boundary (temporarily break one component, show rest still works).

---

## 7. MOBILE & CROSS-BROWSER

| # | Test | Status | Evidence |
|---|------|--------|----------|
| M1 | Chrome desktop — current version | | |
| M2 | Firefox desktop — current version | | |
| M3 | Safari desktop — Mac compatibility | | |
| M4 | Chrome mobile at 375px (iPhone SE) | | |
| M5 | All text readable on mobile without zooming | | |
| M6 | All buttons tappable — minimum 44×44px touch target | | |
| M7 | Search box usable on mobile — full-width, keyboard does not cover it | | |
| M8 | Navigation collapses to hamburger on mobile — hamburger works | | |
| M9 | Tables scroll horizontally on mobile — layout does not break | | |
| M10 | No content cut off on mobile — no page-level horizontal scroll | | |

**Proof:** Screenshots of login, dashboard, query result on mobile (Chrome DevTools phone sim acceptable).

---

## 8. PERFORMANCE (What The Professor Feels)

| # | Test | Status | Evidence |
|---|------|--------|----------|
| P1 | First Contentful Paint (FCP) < 2 seconds — Lighthouse | | |
| P2 | Dashboard fully loaded with data < 4 seconds | | |
| P3 | Query response starts within 3 seconds (streaming start) | | |
| P4 | Zero JavaScript errors in browser console during normal use | | |
| P5 | Zero failed network requests in DevTools Network tab during normal use | | |
| P6 | No excessive re-renders — clicking one button does not flash whole page | | |
| P7 | No uncompressed images >500KB in Network tab | | |
| P8 | Fonts load immediately — no invisible text (FOIT) | | |
| P9 | Lighthouse Performance score ≥ 70 on desktop | | |
| P10 | Lighthouse Accessibility score ≥ 70 | | |

**Commands:**
```bash
# Chrome DevTools → Lighthouse → Generate report
# Console must be empty: no red errors, no yellow deprecation warnings
# Network tab during query: no 4xx/5xx, no requests hanging >10s
```

**Proof:** Lighthouse report screenshot. Clean Console screenshot. Clean Network tab during successful query.

---

## 9. CONTENT & COPY

| # | Test | Status | Evidence |
|---|------|--------|----------|
| C1 | Product name consistent everywhere — "NRG" or "National Research Graph", no typos | | |
| C2 | No placeholder text anywhere ("Lorem ipsum", "TODO", "FIXME", "test") | | |
| C3 | No hardcoded fake names in production ("John Doe", "Test User") | | |
| C4 | Button labels are action words ("Search", "View Details") — not vague ("Click here") | | |
| C5 | Tooltips on non-obvious icons | | |
| C6 | Date formats consistent — not mixed DD/MM/YYYY and MM-DD-YYYY | | |
| C7 | Number formats consistent — not mixed "1000" and "1,000" and "1K" | | |
| C8 | Currency always ₹ (not $, not "INR", not "Rs.") or one consistent format | | |
| C9 | Browser tab titles meaningful — not "React App" or "undefined" | | |
| C10 | Confirmation before destructive actions — "Are you sure?" before delete | | |

**Proof:** Screenshots of browser tab titles on 3 pages. Tooltip screenshot. `grep -ri "TODO\|FIXME\|lorem" frontend/src/` must return 0.

---

## 10. THE PROFESSOR'S ACCEPTANCE TEST SCRIPT (Run This Before Every Demo)

This is the exact sequence the professor will run. Walk through it end-to-end, in order, with all three tiers. Any failure = stop and fix before the evaluation.

```
STEP 1 — OPEN THE APP
 Open Chrome (private/incognito — no cached state)
 Navigate to app URL
 ✓ Login page loads cleanly, under 2 seconds
 ✓ No console errors in DevTools

STEP 2 — LOGIN AS RESEARCHER (Tier 1)
 Enter researcher credentials
 ✓ Dashboard appears within 3 seconds
 ✓ Stats are real numbers (not 0 or null)
 ✓ Navigation visible and complete

STEP 3 — RUN THE KEY DEMO QUERY
 Type: "Which institutes in India have the highest grant amount in renewable energy?"
 ✓ Loading indicator appears immediately
 ✓ Answer appears within 10 seconds
 ✓ Answer is readable prose, not raw JSON
 ✓ Citations visible below answer
 ✓ Numbers formatted (₹ with commas)

STEP 4 — FOLLOW-UP QUERY
 Type: "Now show the same for computer science"
 ✓ Context maintained — answer refers to previous result
 ✓ Different result appears — not repeated

STEP 5 — SHOW SECURITY (PII BLOCK)
 Type: "Show all researchers with Aadhaar 1234 5678 9012"
 ✓ System blocks with clean, user-friendly message
 ✓ Not red error, not stack trace — professional notice

STEP 6 — LOGOUT AND LOGIN AS INDUSTRY (Tier 3)
 Click logout
 ✓ Redirected to login cleanly
 Login as industry user
 ✓ Dashboard looks noticeably different — more restricted

STEP 7 — RUN SAME QUERY AS TIER 3
 Type: "Which institutes in India have the highest grant amount in renewable energy?"
 ✓ Answer is more restricted — no individual details
 ✓ "Access restricted" label or different fields vs Tier 1

STEP 8 — SHOW AUDIT TRAIL
 Navigate to Audit / Activity / History
 ✓ Recent queries appear with timestamps
 ✓ "Verify integrity" or equivalent shows chain intact

STEP 9 — KNOWLEDGE GRAPH (if in UI)
 Type: "Show me the research network around hydrogen fuel cells"
 ✓ Visual graph appears — not error, not raw JSON

STEP 10 — CLOSE AND REOPEN
 Close browser tab
 Reopen and navigate back
 ✓ Prompted to log in (session handled correctly)
 ✓ No broken state, no empty page
```

**Every step must pass. Record the full walkthrough. This recording IS the acceptance evidence.**

---

## 11. THINGS THAT WILL EMBARRASS YOU

| The Error | What The Professor Thinks | Fix |
|-----------|--------------------------|-----|
| Browser console full of red errors | "Even I can see it's broken" | Fix all console errors before launch |
| "undefined" anywhere on screen | "The developer didn't test this" | Null/undefined handling on every field |
| Page scrolls wrong after clicking | "It's glitchy" | Fix scroll behavior on route change |
| Button click with no visual feedback | "Did it work?" | Every click → loading state or confirmation |
| Form accepts any input but fails on submit | "Why didn't it tell me before?" | Real-time validation |
| Table squashed on 13-inch screen | "I can't read anything" | Test on 1366px width |
| Text overflows container | "Shoddy work" | Test every component with long strings |
| Spinner that never stops | "The app crashed" | All API calls have timeouts |
| Success message never disappears | "Something is wrong" | Auto-dismiss toasts after 3-4s |
| "NaN%" or "Infinity" in stat card | "The data is garbage" | Check every calculation |
| Two different fonts on same page | "No one designed this" | Enforce single font family |
| Button does nothing on second click | "The app froze" | Disable during loading, re-enable after |
| "Invalid Date" showing | "The data is broken" | Validate all dates before render |
| `alert()` popup (browser native) | "This is from 2005" | Replace with custom toast/modal |
| URL showing "localhost" in production | "This is their test version" | Correct environment variables |

---

## 12. UI/UX AUDIT REPORT TEMPLATE

After completing every test, produce:

**Filename:** `NRG_UI_UX_AUDIT_REPORT_<YYYY-MM-DD>.md`

```
NRG — REAL USER EXPERIENCE AUDIT REPORT
Date: <YYYY-MM-DD>
Auditor: [Agent Name]

PRODUCTION-READINESS SCORE: ___ / 10

1. FIRST IMPRESSIONS
  Login screen: PASS / FAIL — issues: [list]
  Dashboard: PASS / FAIL — issues: [list]

2. CORE QUERY FEATURE
  Search input: PASS / FAIL — issues: [list]
  Results display: PASS / FAIL — issues: [list]
  Multi-turn context: PASS / FAIL — issues: [list]

3. NAVIGATION & LINKS
  Broken links: [count] — [list]
  404 pages: [count] — [list]

4. EMPTY STATES & LOADING
  Missing empty states: [list]
  Missing loading indicators: [list]

5. ERROR HANDLING
  Raw errors shown to user: [list]
  Missing friendly messages: [list]

6. MOBILE
  Works on 375px: YES / NO — issues: [list]
  Chrome: YES / NO | Firefox: YES / NO | Safari: YES / NO

7. PERFORMANCE
  Lighthouse Performance: ___
  Lighthouse Accessibility: ___
  Console errors during evaluation: ___ (must be 0)
  Failed network requests: ___ (must be 0)

8. CONTENT & COPY
  Placeholder text: YES / NO — [list]
  Inconsistent terminology: YES / NO — [list]
  Broken page titles: YES / NO — [list]

9. ACCEPTANCE TEST SCRIPT RESULT
  Step 1 (App loads): PASS / FAIL
  Step 2 (Login Tier 1): PASS / FAIL
  Step 3 (Key query): PASS / FAIL
  Step 4 (Follow-up): PASS / FAIL
  Step 5 (PII block clean): PASS / FAIL
  Step 6 (Tier 3 login): PASS / FAIL
  Step 7 (Tier 3 restricted): PASS / FAIL
  Step 8 (Audit trail visible): PASS / FAIL
  Step 9 (Graph query): PASS / FAIL
  Step 10 (Session behavior): PASS / FAIL
  ACCEPTANCE TEST SCRIPT OVERALL: PASS / FAIL

10. ISSUES FIXED DURING AUDIT
  | Issue | Before | After | Fixed In |
  |-------|--------|-------|----------|
  |    |    |    |     |

11. AGENT SIGN-OFF
  "I have personally walked through every step in this document
  in a real browser. I have recorded the acceptance test script.
  
  I have not described what the UI should show.
  I have shown what it actually shows.
  
  If this app embarrasses the founder in front of the professor
  — that is on me."

  Agent Name: ________________
  Acceptance test recording: ________________
  Lighthouse report: ________________
  Date: <YYYY-MM-DD>
```

---

*This protocol is eternal. Update it after every UI sprint.*
*The professor sees UI. Not tests.*


---

## 13. DEMO RISK MAP

Map everything that could go wrong during the 12-minute evaluation. Include technical, UX, data, environment, and human risks.

| Risk | Probability | Impact | Prevention | Recovery |
|------|-------------|--------|------------|----------|
| Backend crashes mid-evaluation | Medium | Catastrophic | Pre-launch health check, restart API fresh | Have backup instance ready, switch URL instantly |
| Query takes >30 seconds | High | Serious | Warm up caches before launch, pre-run key queries | Have cached result ready, show "from cache" label |
| Frontend console shows red errors | High | Serious | Run through entire acceptance test script in incognito window | Have screenshot of clean console ready |
| Tier 3 and Tier 1 look identical | Medium | Catastrophic | Verify RBAC visual differentiation before launch | Have side-by-side screenshots ready |
| PII block shows stack trace | Low | Catastrophic | Test PII query in all 3 tiers before launch | Have correct screenshot ready to show instead |
| Professor asks a question system cannot answer | High | Serious | Prepare 5-10 anticipated questions with answers | "That's an excellent question — let me show you how NRG handles that with a follow-up..." |
| Mobile launch fails (professor pulls out phone) | Medium | Serious | Test on actual mobile device, not just DevTools | "Let me show you the desktop-optimized version first" |
| Network issues (projector, WiFi) | Medium | Serious | Have offline-capable acceptance test recording as backup | Play pre-recorded acceptance test recording |
| Data shows 0 or null on dashboard | Medium | Serious | Verify all API endpoints return real data before launch | Have "sample data mode" toggle |
| Professor clicks something you didn't plan | High | Minor | Walk through EVERY clickable element before launch | "Let's return to the main view" |
| Browser compatibility issue | Low | Serious | Test on professor's likely browser (ask ahead) | Have alternative browser ready |
| Session timeout during launch | Low | Serious | Extend session timeout for launch date | Re-login quickly, have credentials ready |
| Query returns raw JSON | Low | Catastrophic | Test every query type that will be shown | Have formatted version screenshot ready |
| "undefined" visible anywhere | Medium | Serious | Search every page for null/undefined | Have fallback content for all data fields |
| Audit trail page is blank | Low | Serious | Verify audit events are being written | Have sample audit events pre-seeded |
| Professor asks "how do I know this is correct?" | High | Serious | Prepare citation demonstration | Show audit chain + source SQL + retrieved rows |

---

## 14. KILLER DEMO QUERIES

Before any launch, prepare 3 queries that:
1. Cannot be answered by Google Scholar, Scopus, or Excel
2. Require crossing at least 3 tables from `db_struct.sql`
3. Produce a genuinely non-obvious insight
4. Would make a non-technical person say "show me that again"

### Template for each killer query:

```
Natural Language Question:
[The exact question the professor will type]

Expected SQL (based on real schema):
[The SQL that should be generated]

Why this is impossible without NRG:
[Explain why Google Scholar / Scopus / Excel cannot answer this]

What the answer reveals about Indian research:
[The non-obvious insight — the "aha" moment]

Tables crossed:
[List all tables from db_struct.sql that this query touches]

Risk if it fails:
[What happens if this query returns wrong data, null, or raw JSON]
```

### Example (adapt to current schema):

```
Natural Language Question:
"Which institutes have the highest gap between their innovation funding
and their actual commercialization outcomes, and how has that gap
changed over the last 5 years?"

Expected SQL:
WITH funding AS (
 SELECT institute_id, SUM(grant_received) as total_funding,
     financial_year
 FROM innovation_grant_from_govt
 WHERE financial_year BETWEEN 2021 AND 2025
 GROUP BY institute_id, financial_year
),
commercialization AS (
 SELECT i.institute_id, COUNT(p.patent_id) as patents_filed,
     COUNT(CASE WHEN p.commercialized = true THEN 1 END) as patents_commercialized,
     i.financial_year
 FROM innovations_at_various_stages_of_technology_readiness_level i
 LEFT JOIN patents_details p ON i.institute_id = p.institute_id
 WHERE i.financial_year BETWEEN 2021 AND 2025
 GROUP BY institute_id, financial_year
)
SELECT f.institute_id, f.total_funding, c.patents_filed,
    c.patents_commercialized,
    (f.total_funding / NULLIF(c.patents_commercialized, 0)) as funding_per_success,
    f.financial_year
FROM funding f
JOIN commercialization c ON f.institute_id = c.institute_id AND f.financial_year = c.financial_year
ORDER BY funding_per_success DESC
LIMIT 10;

Why impossible without NRG:
This requires joining government funding data with patent commercialization
records across 5 years — data that lives in separate government databases
and is not indexed together anywhere else.

What the answer reveals:
Institutes that receive high funding but have low commercialization
may indicate a policy gap where research is not translating to industry.
The ministry can use this to restructure funding incentives.

Tables crossed:
innovation_grant_from_govt, innovations_at_various_stages_of_technology_readiness_level, patents_details

Risk if it fails:
If this returns "undefined" or wrong numbers, the professor will
immediately distrust all other numbers in the system.
```

**Before every launch:**
- Pre-run all 3 killer queries
- Verify results are correct against known data
- Have fallback answers ready if query fails
- Time each query — if >10 seconds, have cached result ready

---

*The professor remembers one thing from the evaluation: the killer query that made him lean forward. Make sure it works.*
