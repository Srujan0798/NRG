# NRG — UI/UX OVERHAUL DISPATCH (2026-04-28)

**Reads alone.** Backend, AI, login auth, MiniMax, schema, audit chain — all out of scope. This dispatch is *only* the visible surface: pages, buttons, query input, answer rendering, dashboards, states.

**The bar:** when the reviewer opens the laptop, the product must feel like Linear, Vercel, Anthropic Claude.ai — calm, dense, confident. Not a dashboard-widget soup. Not a "research tool". An **answer engine**.

**The mental model:** NRG is a product whose centre of gravity is one large query box and one beautifully streamed answer. Everything else (dashboards, audit, graph) is supporting cast. Every pixel that does not serve "ask → answer" is removed or demoted.

**Single deliverable:** 8 polished screens (login, hero, answer-streaming, answer-final, T1/T2/T3 dashboard, audit list) captured at 1366×768 + 375 px mobile, axe-clean, Lighthouse ≥ 90. Before/after gallery committed to `evidence/2026-04-28/ui_ux/`.

---

## 1. Reference points (read these before writing CSS)

| Inspiration | Take this | Reject this |
|---|---|---|
| **anthropic.com** + Claude.ai | calm typography, generous whitespace, soft gradients, single accent colour | playful illustrations |
| **linear.app** | dense information without clutter, tiny but legible labels, sharp focus rings | dark-only |
| **vercel.com** | command-bar feel of the query input, monospaced numbers, tight buttons | brutalist black |
| **stripe.com docs** | the way numbers are bolded inline, code block typography, drawer interactions | marketing carousel |
| **notion.so** | empty-state copy, "click here to start" affordances, friendly nudges | emoji-everywhere |

**Forbidden patterns** (visible in current build, must not survive this overhaul):
- Multiple font families on one screen (system-ui in nav, Inter in body, serif in headings)
- Mixed hex colours (`#3b82f6` and `#4f46e5` in buttons of the same hierarchy)
- "Loading…" with no progress, no time, no signal
- Cards full of placeholder numbers ("12,345" hard-coded)
- Buttons with no hover/focus/active states
- Skeletons that show > 200 ms of nothing
- `<pre>{JSON.stringify(error)}</pre>` rendered to user
- Dashboard widgets that don't lead anywhere

---

## 2. THE single ═══ protocol (one agent, one pass)

```
═══════════════════════════════════════════════════════════════
TASK: UI/UX overhaul — answer-engine grade
AGENT: senior frontend (one owner, end-to-end)
PRIORITY: P0-blocker (this is what the reviewer sees)
DURATION: 1–2 days, single agent, focused
═══════════════════════════════════════════════════════════════

FILES (every visible file in frontend/):
  frontend/tailwind.config.js
  frontend/src/styles/tokens.css                       — NEW (CSS variables)
  frontend/src/styles/typography.css                   — NEW (font-face self-hosted)
  frontend/src/components/ui/                           — NEW (12 atoms, see §3)
  frontend/src/components/Login.tsx                    — REWRITE
  frontend/src/views/Hero.tsx                          — REWRITE
  frontend/src/components/SearchBar.tsx                — REWRITE (command-bar feel)
  frontend/src/components/SuggestionChips/             — REWRITE
  frontend/src/components/StreamingAnswerPanel.tsx     — REWRITE (4-phase progress)
  frontend/src/components/AnswerPanel/AnswerPanel.tsx  — REWRITE
  frontend/src/components/AnswerTrustActions/          — REWRITE
  frontend/src/components/CitationDrawer/              — REWRITE
  frontend/src/components/AuditEventList/              — REWRITE
  frontend/src/components/PersonaToggle.tsx            — REWRITE
  frontend/src/components/EmptyState/                  — REWRITE (one component, friendly copy)
  frontend/src/components/ErrorState/                  — REWRITE (no stack traces)
  frontend/src/views/{Researcher,Government,Industry}Dashboard.tsx  — REWRITE
  frontend/src/views/MetricsDashboard.tsx              — REWRITE or DELETE
  frontend/src/views/FounderDashboard.tsx              — DELETE (out of scope)
  frontend/public/fonts/                               — NEW (Inter + JetBrains Mono self-hosted)

PROBLEM:
  Current frontend is a dashboard-widget soup with mixed fonts, mixed
  colours, broken focus rings, empty/error states that leak stack
  traces, and a query-answer flow that feels like a dev page. Backend
  works; the surface is what the reviewer judges.

ACTION (3 phases, in order):

  Phase 1 — TOKENS + ATOMS (4 h)

    1.1 Self-host two fonts only:
        - Inter (Variable) for sans
        - JetBrains Mono (Variable) for mono
        Drop Google Fonts CDN entirely. Files in frontend/public/fonts/.

    1.2 Write frontend/src/styles/tokens.css — only CSS variables:

        :root {
          /* type */
          --font-sans: "Inter", system-ui, sans-serif;
          --font-mono: "JetBrains Mono", ui-monospace, monospace;
          --text-xs: 12px; --text-sm: 13px; --text-base: 14px;
          --text-md: 16px; --text-lg: 20px; --text-xl: 28px;
          --text-2xl: 40px;
          --leading-tight: 1.2; --leading-normal: 1.5;
          --tracking-tight: -0.01em;

          /* spacing — 4 px scale */
          --space-1: 4px; --space-2: 8px; --space-3: 12px;
          --space-4: 16px; --space-5: 20px; --space-6: 24px;
          --space-8: 32px; --space-10: 40px; --space-12: 64px;

          /* radius */
          --radius-sm: 6px; --radius-md: 10px; --radius-lg: 14px;
          --radius-pill: 999px;

          /* colour — light */
          --color-bg: 250 250 250;       /* near-white, warm */
          --color-bg-elevated: 255 255 255;
          --color-bg-subtle: 244 244 245;
          --color-fg: 24 24 27;           /* near-black */
          --color-fg-muted: 113 113 122;
          --color-fg-subtle: 161 161 170;
          --color-border: 228 228 231;
          --color-ring: 99 102 241;

          /* one accent (re-themed by tier via [data-tier]) */
          --color-accent: 99 102 241;     /* indigo default = T1 */
          --color-accent-hover: 79 70 229;
          --color-accent-fg: 255 255 255;

          --color-success: 22 163 74;
          --color-warning: 234 88 12;
          --color-danger: 220 38 38;

          /* shadow */
          --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.04);
          --shadow-md: 0 4px 12px rgb(0 0 0 / 0.06);
          --shadow-lg: 0 12px 32px rgb(0 0 0 / 0.08);

          /* motion */
          --duration-fast: 120ms; --duration-normal: 200ms;
          --ease-standard: cubic-bezier(0.2, 0, 0, 1);
        }

        :root[data-theme="dark"] {
          --color-bg: 9 9 11;
          --color-bg-elevated: 24 24 27;
          --color-bg-subtle: 39 39 42;
          --color-fg: 250 250 250;
          --color-fg-muted: 161 161 170;
          --color-fg-subtle: 113 113 122;
          --color-border: 39 39 42;
        }

        :root[data-tier="t2"] { --color-accent: 217 119 6;  --color-accent-hover: 180 83 9; }
        :root[data-tier="t3"] { --color-accent: 82 82 91;   --color-accent-hover: 63 63 70; }

    1.3 Wire tailwind.config.js to read from these tokens:
          colors: {
            bg:       'rgb(var(--color-bg) / <alpha-value>)',
            fg:       'rgb(var(--color-fg) / <alpha-value>)',
            'fg-muted': 'rgb(var(--color-fg-muted) / <alpha-value>)',
            accent:   'rgb(var(--color-accent) / <alpha-value>)',
            ...
          }
        Build-time grep that fails if any frontend/src/**/*.{tsx,css}
        contains a literal `#[0-9a-f]{3,8}` outside tokens.css.

    1.4 Build 12 atomic components in frontend/src/components/ui/.
        Each gets a Storybook story (3 variants × light/dark × reduced-motion).
        ONE design language. Atoms:

          Button         — 3 sizes (sm/md/lg) × 4 variants (primary/secondary/ghost/danger)
                           States: default / hover / focus-visible / active / loading / disabled
                           Loading: spinner replaces label, button stays the same width
          Input          — text/email/password; labelled; error variant; show-password toggle
          Textarea       — auto-grow option
          Select         — same hover/focus/disabled rhythm
          Checkbox / Radio — accessible, real focus ring
          Card           — 3 paddings, optional header/footer, no shadow drift
          Pill           — small badge (high/med/low confidence, tier indicator)
          Drawer         — right-side slide-over, focus-trapped, ESC closes
          Modal          — centred, dim background, focus-trapped
          Toast          — top-right, auto-dismiss, polite ARIA
          Skeleton       — shimmer ≤ 1.5 s; never solo > 200 ms
          Spinner        — 16/20/24 px, accessible aria-label

        Every atom passes axe-core 0 errors and respects
        prefers-reduced-motion.

  Phase 2 — REWRITE 8 SCREENS (8 h, single agent, route by route)

    Order of rewrite (lowest blast-radius first):
      a) /login
      b) / (Hero)
      c) /app/researcher
      d) /app/government
      e) /app/industry
      f) /app/answer/<id> (streaming + final)
      g) /app/audit
      h) Empty / Error / Blocked states (cross-cutting)

    Each screen specification — see §3 for exact layouts.

    Rules during rewrite:
      - Replace every <div className="..."> with atom imports where applicable
      - Delete any decorative card whose value is < 1 sentence
      - Every page has exactly ONE primary CTA above the fold
      - No raw `Error.message` — wrap in human language
      - Every async action has a loading state ≤ 200 ms blank
      - Every empty state has a friendly explanation + one suggested next step

  Phase 3 — POLISH + PROOF (4 h)

    3.1 Lighthouse desktop: ≥ 90 / 90 / 90 / 90 on /, /login, /app/researcher
    3.2 Lighthouse mobile (iPhone 12): ≥ 80 / 90 / 90 / 90
    3.3 axe-core: 0 errors on every route
    3.4 Playwright e2e: tests/e2e/ui_ux_walk.spec.ts walks the 8 screens,
        captures one PNG per screen at 1366×768 and 375 px
    3.5 Visual regression baseline (Storybook + Loki or Chromatic) — gates merge
    3.6 Build the before/after gallery:
        evidence/2026-04-28/ui_ux/before/<screen>.png
        evidence/2026-04-28/ui_ux/after/<screen>.png
        evidence/2026-04-28/ui_ux/GALLERY.md  (side-by-side index)

SKILLS TO USE:
  /frontend-react-best-practices  — composition + a11y patterns
  /typescript-advanced-types      — atom prop typing
  /webapp-testing                  — Playwright + visual regression
  /design-system                   — token discipline
  /ux-copy                         — empty/error microcopy
  /accessibility-review            — axe-core, keyboard, focus
  /performance                     — Lighthouse, CLS, LCP
  /code-review-and-quality

ACCEPTANCE CRITERIA (every box must be true):

  Tokens / build hygiene
    [ ] No literal hex colour in frontend/src/**/*.{tsx,ts,css} outside tokens.css
    [ ] Only 2 font families loaded (Inter, JetBrains Mono); both self-hosted
    [ ] Tailwind reads from CSS variables; theme switch via data-theme attr
    [ ] Tier theme switch via data-tier attr changes accent in < 100 ms

  Atoms
    [ ] 12 atoms exist with Storybook stories; each axe-clean
    [ ] Every atom has the 6 states catalogued above
    [ ] reduced-motion respected throughout

  Login (/login)
    [ ] Above-fold: institute lockup, single email, password+toggle, "Sign in"
    [ ] Submit shows inline spinner + "Signing you in…" within 200 ms
    [ ] Wrong-creds → friendly inline message, never "401 Unauthorized"
    [ ] Lighthouse mobile ≥ 90 perf

  Hero (/)
    [ ] Above-fold: tagline + huge query input (autofocus) + 4 chips + scale strip
    [ ] Pressing "/" anywhere focuses the query input
    [ ] Tagline reads: "Sovereign intelligence over India's research database"
    [ ] Scale strip pulls real numbers from /api/stats
    [ ] TTI < 1.5 s on slow 3G; LCP < 2.5 s

  Streaming answer (/app/answer/<id>)
    [ ] 5 named phases visible in order, each with elapsed ms
    [ ] First token visible < 1 s after submit on warm cache
    [ ] Cold-query has continuous progress every < 1 s; never blank > 200 ms
    [ ] At end: confidence pill (high/med/low), 3 trust buttons, citation chips
    [ ] "View Source Data" drawer: SQL highlighted + first 25 rows + Download CSV
    [ ] "View Audit Event" drawer: event ID, kid, prev hash, "verify on chain"
    [ ] "Ask follow-up" affordance always visible after answer

  Tier dashboards (/app/{researcher,government,industry})
    [ ] Same query yields visibly different responses per tier (column shape + tone)
    [ ] Tier banner colour matches accent (indigo / amber / slate)
    [ ] No widget without a working source — anything decorative is removed

  Audit list (/app/audit)
    [ ] Virtualised list handles 100k events smoothly
    [ ] Click row → drawer with full event metadata
    [ ] Filter by user / persona / time

  Empty / Error / Blocked
    [ ] No view shows "Error:", "Traceback", "<pre>", or `undefined`
    [ ] Every empty state has a friendly explanation + one suggested chip
    [ ] PromptBlocked component renders with explanation + 2 safe rephrasings

  Responsive
    [ ] All 8 screens render at 375 / 1366 / 1920 with no horizontal scroll
    [ ] Persona toggle collapses to icon at < 768 px
    [ ] CitationDrawer becomes full-screen modal at < 768 px

  Performance
    [ ] Lighthouse desktop ≥ 90/90/90/90 on /, /login, /app/researcher
    [ ] Lighthouse mobile ≥ 80/90/90/90 on the same
    [ ] Initial bundle gz < 250 KB; lazy chunks for /app/audit and /app/graph

  Accessibility
    [ ] axe-core 0 errors on every route
    [ ] Tab order works front-to-back on every page
    [ ] Focus ring visible (2 px ring at --color-ring)
    [ ] Keyboard shortcuts: "/" focuses query, ESC closes drawer/modal

  Evidence
    [ ] evidence/2026-04-28/ui_ux/after/<screen>.png × 8 × 2 viewports
    [ ] evidence/2026-04-28/ui_ux/GALLERY.md (before/after for each)
    [ ] evidence/2026-04-28/ui_ux/lighthouse.json
    [ ] evidence/2026-04-28/ui_ux/axe-report.json
    [ ] evidence/2026-04-28/ui_ux/walk_recording.mp4 (Playwright video)
    [ ] BACKLOG.md adds UI-1 row closed with commit hash

GURU NOTE:
  This is the surface the reviewer touches. Backend is hidden. Audit
  signatures are hidden. The only thing visible is the design language,
  the rhythm of the screens, and the streaming answer. Get this wrong
  and the meeting ends in 90 seconds. Get it right and a working AI on
  Indian-soil infrastructure becomes credible. One agent, focused, one
  bar, no shortcuts.

DEPENDS ON: nothing — login + AI work is already done; this is pure surface
═══════════════════════════════════════════════════════════════
```

---

## 3. The 8 screens — exact layout spec

### 3.1 `/login`

```
┌───────────────────────────────────────────────────────────────┐
│                                                                │
│                       [IIT-GN lockup]                          │
│                                                                │
│              National Research Graph                           │
│              Sovereign intelligence over India's               │
│              research database                                 │
│                                                                │
│       ┌─────────────────────────────────────────────┐          │
│       │  email@iitgn.ac.in                          │          │
│       └─────────────────────────────────────────────┘          │
│       ┌─────────────────────────────────────────────┐          │
│       │  •••••••••••                          [👁]  │          │
│       └─────────────────────────────────────────────┘          │
│       ┌─────────────────────────────────────────────┐          │
│       │              Sign in                        │          │
│       └─────────────────────────────────────────────┘          │
│                                                                │
│         No credentials? Contact your IRPC officer.             │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

Centred at 480 px max-width. Subtle radial gradient background. ESC clears form. Enter submits. Loading state replaces button label with spinner; button stays same width.

### 3.2 `/` (Hero)

```
┌───────────────────────────────────────────────────────────────┐
│  [IIT-GN] National Research Graph        [persona ▾]  [logout]│
│                                                                │
│                                                                │
│              What would you like to know about                 │
│              India's research ecosystem?                       │
│                                                                │
│       ╔══════════════════════════════════════════════╗         │
│       ║ Ask anything…                            ⏎  ║         │
│       ╚══════════════════════════════════════════════╝         │
│         press / to focus                                       │
│                                                                │
│       [Top funding agencies]  [TRL-9 in clean energy]          │
│       [Compare GJ vs KA AI 5y] [IIT-GN hydrogen collaborators] │
│                                                                │
│     50,123 researchers · 50,498 publications · 181 institutions │
│              · 58 schema tables · DPDP-2023 compliant          │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

Tagline `--text-2xl`, query input `--text-lg`, chips small. Scale-strip numbers monospace, pulled from `/api/stats`. No widgets, no sidebar.

### 3.3 `/app/answer/<id>` — streaming

```
┌───────────────────────────────────────────────────────────────┐
│  [back]  Top funding agencies by total grant amount           │
│                                                                │
│  ●  Parsing your question        120 ms                       │
│  ●  Planning a multi-hop strategy  340 ms                     │
│  ◐  Querying 58 research tables…  1,210 ms                   │
│                                                                │
│         (skeleton shimmer for the answer body)                 │
└───────────────────────────────────────────────────────────────┘
```

Each phase line replaces with a checkmark + final ms when complete. Heartbeat ping every 1 s if a phase takes > 1 s. Smooth ease-out transitions, never blank > 200 ms.

### 3.4 `/app/answer/<id>` — final

```
┌───────────────────────────────────────────────────────────────┐
│  [back]                                       confidence: high │
│                                                                │
│  Top funding agencies by total grant amount                   │
│                                                                │
│  Over the last five years, the **Department of Science and    │
│  Technology (DST)** has disbursed the largest cumulative grant │
│  amount at **₹4,872 crore [1]**, followed by SERB at ₹3,210   │
│  crore [2] and DBT at ₹2,640 crore [3].                       │
│                                                                │
│  In policy terms, this means the top three Central agencies   │
│  account for over **64% of all measured research outlay** in  │
│  the dataset…                                                  │
│                                                                │
│  Caveats: figures cover sanctioned (not disbursed) amounts;    │
│  cohort excludes private-sector grants.                        │
│                                                                │
│  ──────────────────────────────────────────────────────────    │
│  [Copy answer]  [View source data]  [View audit event]         │
│  Ask a follow-up question…                                     │
└───────────────────────────────────────────────────────────────┘
```

Citation chips inline; click → drawer. Caveat paragraph muted. Follow-up input restores hero feel. Confidence pill top-right matches level (green/amber/grey).

### 3.5–3.7 `/app/{researcher,government,industry}` — tier dashboards

Each renders **one** layout: tier banner + hero query input + 3 cards below ("Recent answers", "Saved queries", "Knowledge map"). No more, no less. Tier-coloured accent. Same query box as Hero. Nothing decorative.

### 3.8 `/app/audit`

Virtualised list, monospace event IDs, click-row drawer. Filter pills top: persona / time / outcome. Empty-state copy: *"No events yet for this filter. Try widening the time range."*

---

## 4. The runner

```bash
bash scripts/run_ui_ux_check.sh   # NEW (agent writes per Phase 3.4)
```

Steps:
1. `npm run build` (must succeed; bundle budget enforced)
2. `npx playwright test tests/e2e/ui_ux_walk.spec.ts` — 8 screens × 2 viewports, video recorded
3. `npx lighthouse http://localhost:5173/{,login,app/researcher} --output=json` × 6
4. `npx axe http://localhost:5173/{,login,app/researcher,app/answer/test,app/audit}` × 5
5. `node scripts/build_before_after_gallery.mjs`  (writes GALLERY.md)
6. Print PASS/FAIL summary; exit 0 only when every acceptance box above is green

---

## 5. Founder dry-run (final gate)

After the agent reports green:

```bash
bash scripts/run_critical_path_final.sh   # boot the full stack
open http://localhost:5173                 # walk the 8 screens manually
```

For each screen, ask once:

> *Would I be embarrassed showing this to a senior IIT-GN faculty member right now?*

If YES anywhere → file a defect on that screen → agent fixes → re-run. Loop until every screen is NO.

When every screen is NO, the laptop is the artefact. Open it in the meeting. That is the close.

---

## 6. Verdict

```
SCOPE:                 visible surface only — login, hero, query, answer, dashboards, states
OWNER:                 one senior frontend agent, end-to-end (no committee)
DURATION:              1–2 days focused
GATE:                  8 screens × 2 viewports × axe clean × Lighthouse ≥ 90/80
RISK IF SKIPPED:       backend wins on paper, the meeting ends in 90 seconds
RISK IF DONE:          a sovereign-AI product that visibly looks like Linear/Anthropic — the kind that earns the meeting
```

This is the only dispatch the founder needs to send to fix the visible product. Hand it to one frontend agent. Read no other dispatch until the 8 screens are green.
