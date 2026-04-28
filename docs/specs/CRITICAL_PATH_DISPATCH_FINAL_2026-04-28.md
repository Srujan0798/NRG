# NRG — CRITICAL-PATH DISPATCH (FINAL · 2026-04-28)

**Reads alongside:** `CRITICAL_PATH_DISPATCH_2026-04-28.md` (CP-1..CP-10).
**This file adds the four protocols the prior dispatch did not cover:**

- **CP-0** — AI response quality (MiniMax is wired but answers are weak)
- **CP-FE-AUDIT** — forensic frontend audit (catalogue every visible defect)
- **CP-FE-FIX** — single-design-system rewrite of the frontend
- **CP-LOGIN-FIX** — root-cause-debug the login that is not working

**Verified facts (from a live grep, 2026-04-28):**

| Claim | Reality |
|---|---|
| MiniMax not wired | FALSE. `.env:10 LLM_PROVIDER=minimax`, `MINIMAX_API_KEY` set, model `minimax-m2.7`, fallback `minimax,nvidia`. Client at `src/config/llm_config.py:101-109, 594-653`. |
| Streaming missing | FALSE. `/api/query/stream` at `src/api/main.py:2391` emits `phase` events (`intent_detection`, `retrieval`, `synthesis`) + token chunks + citation events. |
| Login + StreamingAnswerPanel components missing | FALSE. Both exist in `frontend/src/components/`. |
| Frontend design system absent | TRUE. `frontend/tailwind.config.js` exists but no `frontend/src/styles/` token package; component CSS scattered. **This is the source of the mixed-cat-buffalo feeling.** |

**So the gap is quality, not absence.** The agent's job is not to add features — it's to make the existing pieces feel like one product.

---

## Wave plan (final, ~1 day at 1 senior frontend + 1 backend agent)

| Wave | Protocols | Owner | Time |
|---|---|---|---|
| **F-W1** parallel | CP-LOGIN-FIX (debug + fix the actual login bug) · CP-0 (MiniMax quality bar) | backend | 2 h |
| **F-W2** sequential | CP-FE-AUDIT (forensic catalogue of every visible defect) | senior frontend | 2 h |
| **F-W3** parallel | CP-FE-FIX (apply single design system; fix every catalogued defect) · CP-AI-PROMPT-FIX (system prompt + retrieval injection rewrite, see CP-0 §3) | senior frontend + ml | 4 h |
| **F-W4** sequential | CP-1..CP-10 walk from the prior dispatch | testing + founder | 1 h |
| **F-W5** sequential | CP-FOUNDER-DRYRUN — founder runs the laptop end-to-end; any felt defect → fix on the spot; loop until founder says "ready" | founder | 1 h |

**Final entry-point:** `bash scripts/run_critical_path_final.sh` brings the full stack up, applies the design system, runs the 10-step walk, records the video + screenshots, and prints PASS/FAIL.

---

## CP-LOGIN-FIX — root-cause-debug the login

```
═══════════════════════════════════════════════════════════════
TASK: Find why login is broken; fix it; never lie about it again
AGENT: backend (no frontend assumptions yet)
PRIORITY: P0-blocker — nothing else matters if login fails
═══════════════════════════════════════════════════════════════

DEBUG PROTOCOL (run in order; stop at the first error and fix):

  1. .venv/bin/python -c "from src.config.llm_config import load_llm_settings; print(load_llm_settings())"
     → must succeed. If it raises LLMConfigError, .env is missing
       a key the agent must add before continuing.

  2. .venv/bin/uvicorn src.api.main:app --reload --port 8000
     → server must start without traceback. Capture stderr; common
       failures: missing alembic migration, DB schema drift, JWT
       key path absent.

  3. curl -sS -X POST http://localhost:8000/auth/login \
       -H 'Content-Type: application/json' \
       -d '{"email":"researcher@iitgn.ac.in","password":"Researcher@2026"}'
     → expect HTTP 200 with {access_token, refresh_token, persona,
       tier}. If 4xx/5xx, read the response body — it says exactly
       what's wrong (user not seeded, password mismatch, JWT key
       absent, DB unreachable).

  4. If user not seeded:
       .venv/bin/python scripts/seed_acceptance_users.py
     If JWT keys absent:
       bash scripts/generate_jwt_keys.sh    # create if missing
     If DB schema drift:
       .venv/bin/alembic upgrade head

  5. Re-run step 3 → must return 200 + valid JWT.

  6. Repeat steps 3–5 for ministry@nrg.gov.in / Ministry@2026
     (tier 2) and partner@industry.in / Industry@2026 (tier 3).

  7. Browser test:
       cd frontend && npm run dev
       Open http://localhost:5173, click "Sign in", enter T1 creds.
       Open DevTools → Network tab.
       On submit, verify: POST /auth/login returns 200, the
       Set-Cookie header contains HttpOnly + SameSite=Strict, the
       cookie name matches what authService reads.

  8. Refresh the page. Session must survive. If it doesn't, the
     cookie domain/path is wrong — fix in src/api/auth.py.

  9. Click logout. Cookie must clear. Redirect to /login.

ROOT-CAUSE TABLE (most likely culprits, in order):

  R1 — JWT_PRIVATE_KEY_PATH points to a file that doesn't exist
       → bash scripts/generate_jwt_keys.sh
  R2 — Acceptance users not seeded
       → .venv/bin/python scripts/seed_acceptance_users.py
  R3 — Frontend reads from localStorage but backend sets HttpOnly cookie
       → fix authService.ts to use credentials: 'include'
  R4 — CORS blocks the cookie
       → src/api/main.py CORS allow_credentials=True, allow_origins=[exact frontend origin]
  R5 — Password hash format mismatch (bcrypt vs argon2)
       → align hash function in seed + login

OUTPUT (commit when each step passes):

  - evidence/2026-04-28/critical_path/cp_login_curl_t1.txt
  - evidence/2026-04-28/critical_path/cp_login_curl_t2.txt
  - evidence/2026-04-28/critical_path/cp_login_curl_t3.txt
  - evidence/2026-04-28/critical_path/cp_login_browser_devtools.png
  - evidence/2026-04-28/critical_path/cp_login_session_persists.png

ACCEPTANCE:
  - [ ] All 3 personas log in via curl (200 + JWT)
  - [ ] All 3 personas log in via browser, land on tier dashboard
  - [ ] Session survives page refresh
  - [ ] Logout clears cookies + redirects /login
  - [ ] No console errors, no `undefined`, no stack trace visible to user

DEPENDS ON: nothing — runs FIRST
═══════════════════════════════════════════════════════════════
```

---

## CP-0 — AI response quality (MiniMax is wired; the answers are weak)

```
═══════════════════════════════════════════════════════════════
TASK: Make MiniMax responses feel like a senior researcher's brief
AGENT: ml + backend
PRIORITY: P0-blocker (Kimi UX §2 — slow + shallow answer kills trust)
═══════════════════════════════════════════════════════════════

VERIFIED:
  - LLM_PROVIDER=minimax (.env:10)
  - MINIMAX_API_KEY=sk-cp-… (.env:14)
  - MINIMAX_MODEL=minimax-m2.7 (.env:15)
  - Client at src/config/llm_config.py:594 (MinimaxClient)
  - Streaming at src/config/llm_config.py:653

THE SEVEN ANSWER-QUALITY DEFECTS (each is a fix):

  Q1 — Shallow synthesis: model returns 2-line answer
       Cause: synthesizer prompt does not require structure
       Fix: src/orchestration/nodes/synthesizer.py system prompt:
         "Return a 4-paragraph answer:
            (a) headline number/finding,
            (b) explanation in plain English (no jargon),
            (c) why it matters to the user's tier,
            (d) caveats and source confidence.
          Cite every number with a [n] marker mapped to retrieved rows."

  Q2 — Hallucinated numbers: cites figures not in retrieved rows
       Cause: synthesizer doesn't validate against sql_results
       Fix: verifier node (src/orchestration/nodes/verifier.py)
         must regex-extract every number in the draft and assert
         it appears in retrieved_facts; if not, refuse to ship,
         set answer_confidence=low, surface "Insufficient data".

  Q3 — Wrong tier voice: gov user gets researcher-style answer
       Cause: synthesizer prompt does not branch on tier
       Fix: prepend tier-specific persona block:
         T1 → "You are advising a senior researcher; be technical."
         T2 → "You are advising a ministry official; be policy-framed,
              cite cohort sizes and aggregated trends, never individuals."
         T3 → "You are advising an industry partner under NDA; surface
              partnership opportunities and anonymized capability maps;
              never PII."

  Q4 — High latency on cold queries: 7–12 s feels broken
       Cause: full DDL prompt + lazy embedding load
       Fix: enable schema-RAG (top-k DDL retrieval — already coded
         at src/skills/text_to_sql/schema_retriever.py); preload
         embedding models at app startup, not on first query.
       Target: cold P95 < 4 s; warm P95 < 1 s.

  Q5 — No citations rendered: model says "according to the data"
       without [n] markers
       Cause: synthesizer prompt allows it; verifier doesn't enforce
       Fix: verifier rejects any sentence containing a number without
         a citation marker. Frontend renders [n] as a click-to-drawer chip.

  Q6 — Repetitive answers across follow-ups: model forgets context
       Cause: NRGState.active_domain not used in synthesizer prompt
       Fix: pass active_domain + last 2 turns into the prompt;
         test with a 4-turn fixture in tests/orchestration/test_followup_context.py.

  Q7 — MiniMax model temperature too high: stylistic drift
       Cause: default temperature 1.0
       Fix: src/config/llm_config.py MinimaxClient — set temperature=0.2,
         top_p=0.9 for synthesizer calls; temperature=0.0 for SQL generation.

ACCEPTANCE (golden answer set — 5 questions, hand-graded):
  Each of these must produce a 4-paragraph answer with cited numbers
  and the correct tier voice:
    G1: "Top 5 funding agencies by total grant amount last 5 years"
    G2: "Compare Gujarat and Karnataka AI research output 5y; show gap"
    G3: "Which IITs collaborate most on hydrogen catalysis?"
    G4: "How many TRL-9 innovations exist in clean energy by state?"
    G5: "Show me institutes that doubled grant size between FY22 and FY24"
  Save evidence/2026-04-28/critical_path/cp0_golden_answers.md
  Each question × each tier → 15 cells; senior PI eyeballs and
  accepts/rejects. Target ≥ 13/15 accept.

OBSERVABILITY:
  - Add nrg_minimax_request_seconds, nrg_minimax_tokens_total,
    nrg_minimax_errors_total Prometheus metrics
  - Log every MiniMax call with: question hash, tier, latency, tokens,
    confidence_score, was_corrected (anomaly detector path)
  - Surface a "AI provider: MiniMax (m2.7) · 2.3 s · 412 tokens"
    pill at the bottom of every answer so the reviewer can see it

DEPENDS ON: CP-LOGIN-FIX (need a working session to test)
═══════════════════════════════════════════════════════════════
```

---

## CP-FE-AUDIT — forensic frontend audit (catalogue everything visible)

```
═══════════════════════════════════════════════════════════════
TASK: Walk every view + capture every visible defect
AGENT: senior frontend (this protocol produces a defect list, not fixes)
PRIORITY: P0-blocker (input to CP-FE-FIX)
═══════════════════════════════════════════════════════════════

PROCEDURE:
  1. Boot stack: bash scripts/run_critical_path.sh
  2. Open http://localhost:5173 in chromium with DevTools open
  3. For every route below, record:
     - Screenshot at 1366×768
     - Console errors (count + text)
     - Network 4xx/5xx (count + path)
     - Visible defects (free-form list — see below)

ROUTES TO AUDIT (12):
  /                                hero/landing
  /login                           login screen
  /app/researcher                  T1 dashboard
  /app/government                  T2 dashboard
  /app/industry                    T3 dashboard
  /app/answer/<id>                 answer detail with citations
  /app/audit                       audit event list
  /app/graph                       collaboration graph
  /app/settings                    user settings
  /404                             not found
  /app/answer/<id>?error=trigger  error state
  /app/answer/<id>?empty=trigger  empty state

VISIBLE DEFECTS TO LOOK FOR:
  D1 — mixed font families (e.g. system-ui in nav, Inter in body, serif in headings)
  D2 — inconsistent spacing (4px in one card, 12px in another)
  D3 — colour drift (#3b82f6 in one button, #4f46e5 in another)
  D4 — broken icons / unicode boxes / missing svg
  D5 — text overflow / horizontal scroll at 1366
  D6 — buttons without hover/focus state
  D7 — placeholder labels still visible ("Lorem ipsum", "TODO", "FIXME")
  D8 — images without alt text
  D9 — links that 404 or do nothing
  D10 — visible error-state classes leaking ("Error:", "<pre>", "Traceback")
  D11 — loader states that show > 200 ms blank
  D12 — keyboard focus ring missing or unreadable
  D13 — tab order skips important elements
  D14 — form fields without labels
  D15 — dark/light mode bleed (white text on white)

OUTPUT (single file):
  evidence/2026-04-28/critical_path/cp_fe_audit_defects.md
  Format per defect:
    - id: D-001
      route: /app/researcher
      defect: "Tier banner uses #4f46e5 but persona toggle uses #3b82f6"
      screenshot: cp_fe_audit_d-001.png
      severity: P0/P1/P2
      proposed_fix: "Use --color-primary token from new design system"

ACCEPTANCE:
  - [ ] 12 route screenshots saved
  - [ ] cp_fe_audit_defects.md catalogues every defect found (target: ≥30)
  - [ ] DevTools console-error count per route reported
  - [ ] Each defect has severity + proposed fix

DEPENDS ON: CP-LOGIN-FIX (need to be able to log in to audit dashboards)
═══════════════════════════════════════════════════════════════
```

---

## CP-FE-FIX — single design system; fix every defect from the audit

```
═══════════════════════════════════════════════════════════════
TASK: Replace the mixed-component soup with one design system
AGENT: senior frontend
PRIORITY: P0-blocker (the founder's "dog cat buffalo" complaint)
═══════════════════════════════════════════════════════════════

THE DESIGN SYSTEM (single source of truth):
  frontend/src/styles/tokens.css — CSS variables only:
    --font-sans: "Inter", system-ui, sans-serif;
    --font-mono: "JetBrains Mono", ui-monospace, monospace;
    --color-bg, --color-bg-elevated, --color-fg, --color-fg-muted
    --color-primary, --color-primary-hover, --color-primary-fg
    --color-accent (T1=indigo, T2=amber, T3=slate via [data-tier] attr)
    --color-success, --color-warning, --color-danger
    --color-border, --color-ring
    --radius-sm/md/lg, --shadow-sm/md/lg
    --space-1..12 (4px scale)
    --duration-fast=120ms, --duration-normal=200ms

  frontend/tailwind.config.js — extend theme to read from CSS vars:
    colors: { primary: 'rgb(var(--color-primary) / <alpha-value>)', ... }

  frontend/src/components/ui/ — 12 atomic components, one design only:
    Button, Input, Select, Textarea, Checkbox, Radio,
    Card, Badge, Pill, Drawer, Modal, Toast

ACTION:
  Phase 1 — FORTIFY: ship tokens.css + 12 atomic components.
    Storybook story per component (3 variants × 2 themes × 1 reduced-motion).
  Phase 2 — ELEVATE: route-by-route, replace ad-hoc styling with
    atomic components. Order: /login → / (hero) → /app/researcher →
    /app/government → /app/industry → /app/answer → /app/audit →
    /app/graph → /app/settings.
    For each route, fix every defect catalogued in cp_fe_audit_defects.md.
  Phase 3 — IMMORTALIZE: build-time grep fails the build if any
    component sets a colour with a literal hex (`#[0-9a-f]{3,8}`)
    instead of `var(--color-…)`. Visual regression baseline set.

ACCEPTANCE:
  - [ ] No literal hex colours in frontend/src/components/ or views/
  - [ ] All 12 routes render with consistent typography + spacing + colour
  - [ ] Every defect in cp_fe_audit_defects.md is closed (audit re-run)
  - [ ] Lighthouse desktop ≥ 90/90/90/90 on / and /login
  - [ ] axe-core: 0 errors on every route
  - [ ] Storybook + visual regression CI gate green

DEPENDS ON: CP-FE-AUDIT (need the defect list)
═══════════════════════════════════════════════════════════════
```

---

## CP-FOUNDER-DRYRUN — final gate (founder feels the laptop)

```
═══════════════════════════════════════════════════════════════
TASK: Founder walks the laptop, fixes anything that feels wrong
AGENT: founder + on-call frontend/backend
PRIORITY: P0-blocker — last gate before showing anyone
═══════════════════════════════════════════════════════════════

PROCEDURE:
  1. Run: bash scripts/run_critical_path_final.sh
  2. Watch all green output. If any RED, agent fixes on the spot
     and the script is re-run.
  3. Open http://localhost:5173 and walk the 10 steps from
     CRITICAL_PATH_DISPATCH_2026-04-28.md §CP-9 manually.
  4. After every step ask: would I be embarrassed showing this
     to a senior IIT-GN faculty member right now? If YES, file
     a defect; on-call agent fixes; restart from step 1.
  5. Repeat until you can answer NO at every step.
  6. Tag walk_recording.mp4 as the artefact.

ACCEPTANCE:
  - [ ] Founder explicit OK: "I can show this right now"
  - [ ] No open defect
  - [ ] walk_recording.mp4 saved to evidence/2026-04-28/critical_path/
═══════════════════════════════════════════════════════════════
```

---

## The single command

When all five protocols above + CP-1..CP-10 are committed, the agent runs:

```bash
bash scripts/run_critical_path_final.sh
```

That script (file below) does the boot, applies the design tokens, runs the Playwright walk, captures the recording + 10 PNGs, eyeballs the 5 golden answers, and prints PASS/FAIL with a single summary line. The founder watches that run, then opens the browser and walks it manually. When both pass, the laptop is ready to be opened in front of the reviewer.
