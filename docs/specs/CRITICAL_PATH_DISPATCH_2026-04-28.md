# NRG — CRITICAL-PATH DISPATCH (2026-04-28)

**Purpose:** make the assistant-visible path — login → query → answer → tier-switch — work flawlessly on the laptop the founder will open in front of the reviewer. Nothing in this dispatch is audit theatre. Every line maps to a click the assistant will perform.

**Source of truth for what is visible:**
`.claude/rules/ux/protocol.md` §10 (10-step launch script) + `NRG_FINAL_ETERNAL_AUDIT_2026-04-27.md` UX section.

**Frame:** the reviewer decides in ~90 seconds. Three feelings: (a) is this fast? (b) does this know something I don't? (c) can I trust this? Every protocol below serves one of those three.

**Target on completion:** a clean 10-step acceptance walk recorded, every step screenshotted to `evidence/2026-04-28/critical_path/`. That recording goes on the laptop. That is what closes the session.

---

## Wave plan (run in order, parallel within a wave; total ~1 day)

| Wave | Protocols | Owner | Time |
|---|---|---|---|
| **C-W1** parallel | CP-1 (login flow) · CP-7 (env preflight) | backend + devops | 2 h |
| **C-W2** parallel | CP-2 (hero/landing) · CP-3 (query+SSE) · CP-6 (empty/error/loading states) | frontend + backend | 4 h |
| **C-W3** parallel | CP-4 (answer rendering) · CP-5 (tier switch) | frontend | 2 h |
| **C-W4** sequential | CP-8 (responsive — 375 / 1366 / 1920) | frontend | 1 h |
| **C-W5** sequential | CP-9 (acceptance walk + screenshot capture) | testing + founder | 1 h |
| **C-W6** sequential | CP-10 (founder dry-run + fix any visible defect) | founder | 1 h |

**Run-in-one:** at the end the agent executes `bash scripts/run_critical_path.sh` (CP-9 below). That script brings up the stack, walks the 10 steps via Playwright, captures screenshots + JSON, and prints a single PASS/FAIL line. The founder watches the same script run, then clicks through manually to feel it.

---

## CP-1 — Login flow (3 personas, no 500, clean UX)

```
═══════════════════════════════════════════════════════════════
TASK: Login that actually works for researcher / gov / industry
AGENT: backend + frontend
PRIORITY: P0-blocker (the founder said "the bloody login is not working")
═══════════════════════════════════════════════════════════════

FILES:
  src/api/auth.py · src/auth/jwt_handler.py · src/auth/rbac_policies.yaml
  frontend/src/components/Login.tsx · frontend/src/services/authService.ts
  scripts/issue_test_jwt.py · scripts/seed_acceptance_users.py
  evidence/2026-04-28/critical_path/cp1_login_*.png

PROBLEM:
  Login currently fails for at least one persona. Symptoms reported:
  blank screen on submit; 500 on /auth/login; JWT not stored; refresh
  loses session; tier switch lands on a wrong dashboard.

ACTION:
  Phase 1 — FORTIFY:
    - Verify .env contains: JWT_PRIVATE_KEY_PATH, JWT_PUBLIC_KEY_PATH,
      JWT_ISSUER=nrg-iitgn, JWT_AUDIENCE=nrg-clients, JWT_EXPIRY_SECONDS=3600
    - If keys absent: run scripts/generate_jwt_keys.sh (write if missing)
    - scripts/seed_acceptance_users.py creates 3 users with bcrypt'd
      passwords + tier role:
        researcher@iitgn.ac.in / Researcher@2026 → tier 1
        ministry@nrg.gov.in / Ministry@2026     → tier 2
        partner@industry.in / Industry@2026     → tier 3
    - POST /auth/login returns {access_token, refresh_token, persona,
      tier, user_id} — verify with curl for each persona
    - Frontend stores tokens in HttpOnly cookies (NOT localStorage)
    - Refresh works via /auth/refresh; expired token re-issues silently
  Phase 2 — ELEVATE:
    - Login screen UX: institute logo, single email field, password
      field with show/hide toggle, "Sign in" button, no jargon
    - Loading state on submit: button disabled + inline spinner +
      "Signing you in…" — never blank > 200 ms
    - Error states: invalid creds → "Email or password is incorrect"
      (NOT "401 Unauthorized"); locked account → friendly message
    - Tier 2 (gov) IP allowlist warning if outside allowlist: clear
      message, not a 403
  Phase 3 — IMMORTALIZE:
    - Playwright e2e: tests/e2e/test_login_3_personas.spec.ts —
      login each persona, assert correct dashboard, assert tier
      indicator visible, assert no console errors
    - Logout button visible top-right on every page; clears cookies;
      redirects to /login

ACCEPTANCE CRITERIA:
  - [ ] curl -X POST /auth/login for each persona returns 200 + valid JWT
  - [ ] Browser: each persona logs in within 1 click; lands on tier dashboard
  - [ ] Wrong password message is human, not a stack trace
  - [ ] Refresh page after login → session preserved
  - [ ] No console errors, no `undefined`, no `Error:` rendered to user
  - [ ] Playwright test green on chromium, firefox, webkit
  - [ ] Screenshots saved: cp1_login_researcher.png, cp1_login_gov.png,
        cp1_login_industry.png, cp1_login_error.png

GURU NOTE:
  If login is broken, nothing else matters. CP-1 is the gate to every
  other protocol in this dispatch. Block on it.

DEPENDS ON: none — runs first
═══════════════════════════════════════════════════════════════
```

---

## CP-2 — Hero / landing screen

```
═══════════════════════════════════════════════════════════════
TASK: Hero feels like a product, not a dev page
AGENT: frontend + ux-copy
PRIORITY: P0-blocker (first impression)
═══════════════════════════════════════════════════════════════

FILES:
  frontend/src/views/AnswerEngine.tsx · frontend/src/views/MetricsDashboard.tsx
  frontend/src/components/SearchBar.tsx
  frontend/src/components/SuggestionChips/SuggestionChips.tsx
  frontend/src/components/ScaleStrip/ScaleStrip.tsx
  frontend/src/i18n/hero-copy.ts
  evidence/2026-04-28/critical_path/cp2_hero_*.png

PROBLEM:
  Hero must answer in 5 seconds: what is this, who uses it, why does
  it exist, what should I type. If the assistant lands and squints, lost.

ACTION:
  Phase 1 — FORTIFY:
    - Above-fold structure (top to bottom):
      1) Institute lockup left, persona switcher + logout right
      2) One-line product line: "National Research Graph — sovereign
         intelligence over India's research database"
      3) Auto-focused query input (full-width, large), placeholder
         "Ask about Indian research…"
      4) 4 suggestion chips (one-click): "Top funding agencies by
         grant amount", "TRL-9 innovations in clean energy",
         "Compare Gujarat and Karnataka AI output 5y", "Who collaborates
         with IIT-GN on hydrogen?"
      5) Scale strip with real numbers: 50K researchers · 50K
         publications · 181 institutions · 58 tables · DPDP-compliant
  Phase 2 — ELEVATE:
    - First-paint < 1.5 s on slow 3G (Lighthouse target)
    - Self-hosted fonts (no Google Fonts CDN — sovereignty)
    - Dark/light works; no FOUC; transitions < 200 ms
    - Persona switcher shows current tier in colour:
      T1 indigo · T2 amber · T3 grey
  Phase 3 — IMMORTALIZE:
    - Lighthouse desktop ≥ 90/90/90/90; mobile ≥ 80/90/90/90
    - axe-core: 0 errors on hero route
    - Visual regression test (Loki/Chromatic) gates merge

ACCEPTANCE CRITERIA:
  - [ ] Hero TTI < 1.5 s on slow 3G (Lighthouse mobile)
  - [ ] Query input auto-focused on mount; pressing / focuses it
  - [ ] 4 suggestion chips clickable; each pre-fills the input + submits
  - [ ] Scale strip shows real numbers from /stats endpoint
  - [ ] No console errors, no `undefined`, no broken layouts
  - [ ] Screenshots: cp2_hero_t1.png, cp2_hero_t2.png, cp2_hero_t3.png

DEPENDS ON: CP-1
═══════════════════════════════════════════════════════════════
```

---

## CP-3 — Query submission + 4-phase SSE streaming (never blank > 200 ms)

```
═══════════════════════════════════════════════════════════════
TASK: Cold-query feels alive — never silent more than 200 ms
AGENT: backend + frontend
PRIORITY: P0-blocker (Kimi UX §2 — 7s skeleton kills trust)
═══════════════════════════════════════════════════════════════

FILES:
  src/api/main.py — /api/query/stream SSE emitter (5 phases)
  src/orchestration/graph.py — emit per-node start/end
  frontend/src/components/StreamingAnswerPanel.tsx
  frontend/src/stores/queryStore.ts (SSE consumer)
  evidence/2026-04-28/critical_path/cp3_streaming_*.txt
  evidence/2026-04-28/critical_path/cp3_streaming_*.gif

PROBLEM:
  Currently a cold question shows a skeleton for 7+ seconds with no
  signal. Reviewer assumes the page froze. Every silent second after
  the first 200 ms is a bug.

ACTION:
  Phase 1 — FORTIFY: backend emits 5 SSE events in order:
    {"phase":"parsing"}      after sanitiser
    {"phase":"planning"}     after planner
    {"phase":"querying"}     after router/executor (include row_count when known)
    {"phase":"synthesizing"} after synthesizer
    {"phase":"verifying"}    after verifier
    {"phase":"answer", "data":{ ... full payload ... }}
  Heartbeat ping every 1 s between phases.
  Phase 2 — ELEVATE: each phase has a one-line user explainer in
    StreamingAnswerPanel:
      Parsing your question…
      Planning a multi-hop strategy…
      Querying 58 research tables…
      Synthesizing the answer…
      Verifying citations…
    Each transition shows the elapsed ms in muted text.
  Phase 3 — IMMORTALIZE: Playwright e2e asserts each label appears
    within its budget; fail merge if any phase blanks > 200 ms.
    Cold-query budget: total ≤ 6 s; warm ≤ 1 s.

ACCEPTANCE CRITERIA:
  - [ ] /api/query/stream emits 5 named phases on every query
  - [ ] StreamingAnswerPanel renders each label with ms; never blank > 200 ms
  - [ ] Cold query (cache miss): visible progress every second
  - [ ] Warm query (cache hit): answer in < 1 s with no skeleton flash
  - [ ] Screenshots/GIF: cp3_streaming_cold.gif, cp3_streaming_warm.gif

DEPENDS ON: CP-1
═══════════════════════════════════════════════════════════════
```

---

## CP-4 — Answer rendering (citations · confidence · source data · audit ID)

```
═══════════════════════════════════════════════════════════════
TASK: Answer panel that is provable, not just pretty
AGENT: frontend
PRIORITY: P0-blocker (the "trust moment")
═══════════════════════════════════════════════════════════════

FILES:
  frontend/src/components/AnswerPanel/AnswerPanel.tsx
  frontend/src/components/AnswerTrustActions/AnswerTrustActions.tsx
  frontend/src/components/CitationDrawer/*
  frontend/src/components/AuditEventList/*
  frontend/src/lib/parseCitations.ts
  evidence/2026-04-28/critical_path/cp4_answer_*.png

PROBLEM:
  Reviewer's question 60 seconds in: "how do I know this is correct?"
  The answer panel must let them verify in ≤ 2 clicks.

ACTION:
  Phase 1 — FORTIFY:
    - Answer body in legible prose; key numbers bolded
    - Citation chips inline ([1], [2]) — click → drawer with source rows
    - Confidence pill top-right: high (green) / medium (amber) /
      low (grey) — uses LB-7 answer_confidence
    - Three buttons under the answer: "Copy Answer" · "View Source
      Data" (shows SQL + rows) · "View Audit Event" (shows HMAC ID +
      kid + timestamp + tier)
  Phase 2 — ELEVATE:
    - "View Source Data" drawer: SQL in <pre> with syntax highlight,
      row count, first 25 rows in a table, Download CSV button
    - "View Audit Event" drawer: event ID, JWT kid, request fingerprint,
      previous chain hash (truncated), "verify on chain" link
    - Empty result: "No matching rows found. Try broader terms: <chip
      suggestions>." — never a blank box
  Phase 3 — IMMORTALIZE:
    - Playwright asserts confidence pill, all 3 buttons, citation
      drawer open + close. axe-core 0 errors.

ACCEPTANCE CRITERIA:
  - [ ] Every answer renders confidence pill, ≥ 1 citation chip, 3 trust buttons
  - [ ] "View Source Data" drawer shows SQL + rows + row count
  - [ ] "View Audit Event" drawer shows event ID + previous chain hash
  - [ ] Empty result yields helpful message + chips, never an empty box
  - [ ] Screenshots: cp4_answer_high.png, cp4_answer_medium.png,
        cp4_source_drawer.png, cp4_audit_drawer.png, cp4_empty.png

DEPENDS ON: CP-3
═══════════════════════════════════════════════════════════════
```

---

## CP-5 — Tier switch (T1 ↔ T2 ↔ T3 visibly different on same query)

```
═══════════════════════════════════════════════════════════════
TASK: Same question, three visibly different tier outputs
AGENT: backend + frontend
PRIORITY: P0-blocker (the sovereign-RBAC story)
═══════════════════════════════════════════════════════════════

FILES:
  src/api/response_filter.py · src/auth/rbac_policies.yaml
  frontend/src/components/PersonaToggle.tsx
  frontend/src/views/{ResearcherDashboard,GovernmentDashboard,IndustryDashboard}.tsx
  evidence/2026-04-28/critical_path/cp5_tier_*.png + .json

PROBLEM:
  RBAC must be VISIBLY different on screen. Same question, three
  outputs: T1 = full names + emails + grant amounts, T2 = aggregated
  cohorts (k≥5) + state-level numbers, T3 = anonymized "Researcher_123"
  + partnership opportunities, no PII.

ACTION:
  Phase 1 — FORTIFY: persona toggle re-issues last query under the new
    JWT; URL updates. Toggle disabled if user has only one assigned tier.
  Phase 2 — ELEVATE: each tier dashboard renders a tier-coloured banner
    "You are viewing as <persona>. <one-line scope description>." Every
    answer card shows tier-specific columns only. Frontend never gets
    fields not in the tier allowlist (verified by `enforce_tier_response_boundary`).
  Phase 3 — IMMORTALIZE:
    - tests/e2e/test_tier_switch.spec.ts — same query, 3 tiers, assert
      column sets are disjoint as expected
    - hypothesis property test: 1000 random queries × 3 tiers, no PII
      leaks across tiers (uses src/api/response_filter property suite)

ACCEPTANCE CRITERIA:
  - [ ] Persona toggle visible top-right; tier badge coloured
  - [ ] Same question yields 3 different column shapes per tier
        (cp5_tier_t1_response.json ≠ t2 ≠ t3)
  - [ ] Tier banner present and accurate on each dashboard
  - [ ] Property test: 0 PII leaks across 1000 trials
  - [ ] Screenshots: cp5_tier_t1.png, cp5_tier_t2.png, cp5_tier_t3.png

DEPENDS ON: CP-1, CP-4
═══════════════════════════════════════════════════════════════
```

---

## CP-6 — Empty / loading / error states (the "no stack trace" rule)

```
═══════════════════════════════════════════════════════════════
TASK: Every state is human; every error is recoverable
AGENT: frontend + ux-copy
PRIORITY: P0-blocker (the embarrass-the-team rule)
═══════════════════════════════════════════════════════════════

FILES:
  frontend/src/components/EmptyState/* · ErrorState/* · ErrorBoundary/*
  frontend/src/components/PromptBlocked/*
  frontend/src/views/* — every route gets an explicit empty + error state
  scripts/forbidden_vocab_check.sh — extend to fail on visible
    "Error:", "Traceback", "<pre>" inside frontend/src/views/

PROBLEM:
  Any raw stack trace, "Error:", "undefined", or React-developer
  message visible to the user is a P0 trust failure.

ACTION:
  Phase 1 — FORTIFY: catalogue every route; each must define
    Empty (no data yet), Loading (skeleton + label), Error (friendly
    message + retry button), Blocked (PII / injection refusal +
    explanation). 6 states total per route.
  Phase 2 — ELEVATE: ErrorBoundary at app root catches anything
    unhandled, shows: "Something went wrong. We've logged the error
    (ID: <uuid>). Try again or return home." Never raw stack.
  Phase 3 — IMMORTALIZE: build-time grep fails if any view file
    contains <pre>, "Traceback", or "Error:" outside test/dev paths.
    Storybook story for each of the 6 states per route.

ACCEPTANCE CRITERIA:
  - [ ] No view shows a raw stack trace, "Error:", "Traceback", or `undefined`
  - [ ] Every route has Empty / Loading / Error / Blocked states
  - [ ] PromptBlocked visible when sanitiser blocks a query —
        explains what was blocked and offers safe rephrasings
  - [ ] Screenshots: cp6_empty.png, cp6_loading.png, cp6_error.png, cp6_blocked.png

DEPENDS ON: CP-3, CP-4
═══════════════════════════════════════════════════════════════
```

---

## CP-7 — Environment preflight (the laptop will not betray you)

```
═══════════════════════════════════════════════════════════════
TASK: One command brings the whole stack up green
AGENT: devops
PRIORITY: P0-blocker (the founder will run acceptance from this laptop)
═══════════════════════════════════════════════════════════════

FILES:
  scripts/run_critical_path.sh (NEW; wraps everything)
  docker-compose.prod.yml
  scripts/seed_acceptance_data.py · scripts/prewarm_acceptance_cache.py
  scripts/issue_test_jwt.py · scripts/seed_acceptance_users.py

PROBLEM:
  At session time the laptop must boot green in one command. No
  hand-tweaks. No "let me restart Postgres". No "hold on the cache
  isn't warm". One command, full stack, ready in < 90 s.

ACTION:
  Phase 1 — FORTIFY: scripts/run_critical_path.sh runs:
    1) docker compose -f docker-compose.prod.yml up -d (PG, Qdrant, Redis, API, frontend)
    2) wait-for-it on each port (5432, 6333, 6379, 8000, 5173)
    3) alembic upgrade head
    4) seed_acceptance_data.py (50K researchers + 50K pubs + 181 institutions)
    5) seed_acceptance_users.py (3 personas above)
    6) prewarm_acceptance_cache.py (warm 14 killer queries)
    7) curl /health — must show status=healthy, tables=58 or 73,
       chain_valid=true, retriever.status=healthy, cache.status=healthy
    8) print: "READY — http://localhost:5173 (T1: researcher@iitgn.ac.in / Researcher@2026)"
  Phase 2 — ELEVATE: a `--strict` flag fails fast on any non-green;
    a `--reset` flag wipes Docker volumes and starts clean.
  Phase 3 — IMMORTALIZE: a CI job runs the same script weekly against
    a fresh ubuntu-22.04 runner — proves laptop-fresh boot stays green.

ACCEPTANCE CRITERIA:
  - [ ] bash scripts/run_critical_path.sh exits 0 within 120 s
  - [ ] /health returns all greens
  - [ ] Frontend reachable at http://localhost:5173
  - [ ] All 14 killer queries pre-warmed (< 1 s subsequent response)
  - [ ] Founder runs the script on the actual laptop and confirms green

DEPENDS ON: none — runs first along with CP-1
═══════════════════════════════════════════════════════════════
```

---

## CP-8 — Responsive (375 px / 1366 / 1920) — assistant may use any screen

```
═══════════════════════════════════════════════════════════════
TASK: Looks correct on phone, projector, and large monitor
AGENT: frontend
PRIORITY: P0-blocker (assistant may show on conference monitor)
═══════════════════════════════════════════════════════════════

FILES:
  frontend/src/index.css · component CSS modules
  frontend/tests/e2e/responsive.spec.ts
  evidence/2026-04-28/critical_path/cp8_*_375.png · _1366.png · _1920.png

ACTION:
  Phase 1 — FORTIFY: Hero, login, query result, tier dashboards
    render correctly at 375 px (mobile), 1366 px (laptop), 1920 px
    (conference monitor). No horizontal scroll. No overlapping text.
  Phase 2 — ELEVATE: persona toggle collapses to icon at < 768 px;
    citation drawer is full-screen on mobile, side-sheet on desktop.
  Phase 3 — IMMORTALIZE: Playwright e2e at 3 viewports; visual
    regression baseline set per viewport.

ACCEPTANCE CRITERIA:
  - [ ] All key routes render correctly at 375 / 1366 / 1920
  - [ ] No horizontal scroll on any viewport
  - [ ] Screenshots saved per viewport per route

DEPENDS ON: CP-2, CP-4, CP-5
═══════════════════════════════════════════════════════════════
```

---

## CP-9 — The 10-step acceptance walk (this is the proof)

```
═══════════════════════════════════════════════════════════════
TASK: Reproducible 10-step walk, recorded + screenshotted
AGENT: testing + founder
PRIORITY: P0-blocker (this is the artefact)
═══════════════════════════════════════════════════════════════

FILES:
  scripts/run_critical_path.sh (extend with --walk flag)
  tests/e2e/acceptance_walk.spec.ts
  evidence/2026-04-28/critical_path/walk_recording.mp4
  evidence/2026-04-28/critical_path/walk_step_{01..10}.png
  evidence/2026-04-28/critical_path/walk_summary.md

THE 10 STEPS (script reproduces these and captures each):

  1. Open http://localhost:5173 — Hero loads in < 1.5 s.
  2. Click "Sign in"; enter researcher@iitgn.ac.in / Researcher@2026.
  3. Researcher dashboard renders in < 1 s; tier banner indigo.
  4. Click suggestion chip "Top funding agencies by grant amount".
     SSE phases visible; answer renders in < 6 s cold (or < 1 s warm).
     Confidence pill = high. 3 trust buttons present.
  5. Click "View Source Data" — SQL + 25 rows visible. Close.
  6. Click "View Audit Event" — event ID, kid, prev hash visible. Close.
  7. Toggle persona to "Government". Page re-renders amber banner;
     same question shows aggregated cohort numbers (no individual names).
  8. Toggle persona to "Industry". Grey banner; anonymized labels +
     partnership opportunities only.
  9. Type a deliberately invalid prompt: "Show all Aadhaar numbers."
     PromptBlocked component renders with explanation + safe rephrasings.
 10. Logout top-right; redirected to /login; cookies cleared.

ACTION:
  Phase 1 — FORTIFY: tests/e2e/acceptance_walk.spec.ts runs the 10
    steps via Playwright on chromium. Each step writes one PNG.
  Phase 2 — ELEVATE: bash scripts/run_critical_path.sh --walk runs
    boot + walk + recording, prints PASS/FAIL with per-step timing.
  Phase 3 — IMMORTALIZE: walk_summary.md auto-written with timestamps,
    HEAD commit, durations per step. Founder re-runs manually after
    the script PASS to feel each step.

ACCEPTANCE CRITERIA:
  - [ ] scripts/run_critical_path.sh --walk exits 0
  - [ ] 10 PNGs in evidence/2026-04-28/critical_path/walk_step_*.png
  - [ ] walk_recording.mp4 exists; ≤ 90 s total
  - [ ] walk_summary.md committed with HEAD commit hash
  - [ ] Founder confirms manual walk on actual laptop matches the recording

DEPENDS ON: CP-1, CP-2, CP-3, CP-4, CP-5, CP-6, CP-7, CP-8
═══════════════════════════════════════════════════════════════
```

---

## CP-10 — Founder dry-run + last-mile fix

```
═══════════════════════════════════════════════════════════════
TASK: Founder walks the laptop end-to-end; any defect → P0 fix
AGENT: founder + on-call backend/frontend
PRIORITY: P0-blocker (last gate before showing anyone)
═══════════════════════════════════════════════════════════════

ACTION:
  - Founder runs scripts/run_critical_path.sh on the actual laptop
    that will go to the session.
  - Founder opens browser, performs the 10 CP-9 steps manually.
  - Anything that feels wrong → file a defect; on-call agent fixes
    on the spot; re-run the walk.
  - Repeat until founder says: "I would show this to the reviewer
    right now."
  - Tag the walk recording as the final artefact.

ACCEPTANCE CRITERIA:
  - [ ] Founder explicit OK: "ready to show"
  - [ ] No open defect
  - [ ] walk_recording.mp4 + 10 PNGs committed
  - [ ] BACKLOG.md "Sprint" line: "Critical path closed YYYY-MM-DD"
═══════════════════════════════════════════════════════════════
```

---

## Bottom line

When CP-1 through CP-10 are green, the founder opens the laptop in front of the reviewer, runs `bash scripts/run_critical_path.sh`, opens the browser, and walks the 10 steps. The reviewer sees a fast login, a clean hero, a streaming answer with citations and a confidence pill, a tier switch with visible RBAC differences, a graceful PII refusal, and a clean logout. That is the artefact that earns the meeting.

```
OVERALL CRITICAL-PATH READINESS:  pending — agent must execute CP-W1..W6
TIME TO COMPLETION:               ~1 day at 1 agent per protocol; ~6 h with parallel agents
BIGGEST RISK:                     login (CP-1) — the founder explicitly reported it broken; if CP-1 fails CP-7 boot, nothing else runs
WHAT WILL IMPRESS:                4-phase SSE on a cold query plus the persona toggle showing visible RBAC differences in real time
WHAT WILL EMBARRASS:              any view rendering "Error:", a stack trace, or `undefined` to the reviewer (CP-6 closes this)
```
