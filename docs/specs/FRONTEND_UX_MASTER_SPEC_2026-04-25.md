# [SUPERSEDED HEADER, SPEC BODY STILL VALID]

> **The architectural and UX spec below is technically sound** — design tokens, component contracts, accessibility, mobile, motion, telemetry, etc. all remain correct.
> **What is replaced:** the framing "extraordinary for a demo" / "wins the room" / "demo-day polish" — NRG is production software for real users, not a presentation.
> **Read alongside:** `docs/specs/MASTER_EXECUTION_PLAN_2026-04-25.md` for production framing of the same work.
> **Reference rule:** `.claude/rules/production_only.md`.

---

# NRG — FRONTEND / UI / UX MASTER SPEC
**Version:** 1.1 — PRODUCTION HARDENING SPEC
**Date:** 2026-04-25
**Author:** Guru Agent (Claude)
**Audience:** Execution agents (Athena-UX, Hermes-UI, Apollo-Polish, Iris-A11y, Vulcan-Perf)
**Goal:** Take every visible surface to **principal-engineer extraordinary**. The professor / ministry official / industry partner must lean *forward* within 8 seconds of opening the browser, and never lean back during the 12-minute demo.
**Non-negotiable:** Architecture before implementation. Read every section before touching code.

---

## 0. THE ONE-SCREEN MENTAL MODEL

The professor opens the browser. He sees ONE page. That page must, in this exact order within the first 2000ms, communicate:

1. **Sovereignty** (header chrome: 🇮🇳 SOVEREIGN · DPDP-COMPLIANT · AUDIT-BOUND · HOSTED IN INDIA)
2. **Scale credibility** (a metric strip: `58 tables · 1.2M researchers · 47K institutes · 600GB · 381,280 audit events`)
3. **The hero input** (a single search bar, autofocused, with an animated placeholder cycling through 3 example questions)
4. **The persona toggle** (top-right pill: `Researcher | Government | Industry` — active state high-contrast)
5. **A trust badge** ("Every answer is cited and audit-bound" with an info-tooltip)

If any of those five fail to render in 2000ms — every other word in this spec is wasted.

---

## 1. INFORMATION ARCHITECTURE

```
/                          → Landing (marketing + login CTA)
/login                     → Tier-aware login (3 demo accounts pre-filled in dev)
/app                       → Hero query screen (default after login)
  ?persona=researcher      → tier 1 dashboard variant
  ?persona=government      → tier 2 dashboard variant
  ?persona=industry        → tier 3 dashboard variant
/app/answer/:queryId       → Permalink to a past answer (audit-replayable)
/app/audit                 → /pages/DPDP-Audit.tsx  (chain explorer)
/app/audit/event/:hmac     → Single audit event with co-sign and source rows
/app/graph                 → Force-graph explorer (pre-filtered by persona)
/app/data                  → Per-persona dashboards (Researcher / Government / Industry)
/app/about                 → Sovereignty story + architecture diagram
/_403                      → Tier-blocked  (no stack trace; clear recovery)
/_404                      → Page-missing  (with a one-click search box pre-filled with the URL slug)
/_500                      → Friendly fallback ("We're having trouble — your audit trail is safe. [Retry] [Talk to support]")
```

**Routing layer:** React Router v6, lazy-loaded chunks for `/app/graph` (heavy) and `/app/audit` (heavy). Landing + Login + main `/app` ship in the initial JS bundle (target: < 180KB gz).

---

## 2. VISUAL DESIGN SYSTEM

Lives in `frontend/src/design-system/`. Every component MUST consume tokens; zero raw hex / px values in component files.

### 2.1 Color Tokens (`design-system/tokens/colors.ts`)

| Role | Light | Dark | Notes |
|---|---|---|---|
| `--nrg-saffron` | #FF9933 | #FFB366 | Indian flag — top accent only |
| `--nrg-white` | #FFFFFF | #F5F7FA | Primary surface light |
| `--nrg-green` | #138808 | #2BA821 | Indian flag — success / verified states |
| `--nrg-navy` | #0B1F4A | #0B1F4A | Primary brand, headers, CTA |
| `--nrg-ink` | #111827 | #E5E7EB | Body text |
| `--nrg-ink-muted` | #4B5563 | #9CA3AF | Secondary text |
| `--nrg-surface-1` | #FFFFFF | #0F172A | Card |
| `--nrg-surface-2` | #F9FAFB | #1E293B | Sub-card / input |
| `--nrg-surface-3` | #F3F4F6 | #334155 | Hover |
| `--nrg-border` | #E5E7EB | #334155 | Divider |
| `--nrg-focus` | #2563EB | #60A5FA | Focus ring (3:1 against any surface) |
| `--nrg-danger` | #B91C1C | #F87171 | Errors |
| `--nrg-warning` | #B45309 | #F59E0B | Warnings |
| `--nrg-success` | #047857 | #34D399 | Success |
| `--nrg-tier-1` | #1E40AF | — | Researcher persona accent |
| `--nrg-tier-2` | #065F46 | — | Government persona accent |
| `--nrg-tier-3` | #7C2D12 | — | Industry persona accent |

**Contrast rule:** every text on every background must score ≥ 4.5:1 (WCAG AA). Verify via the accessibility test in §11.

### 2.2 Typography (`design-system/tokens/typography.ts`)

- **Display:** Söhne Display, fallback `system-ui` — 56/60 weight 700
- **H1:** 40/48 weight 700
- **H2:** 28/36 weight 600
- **H3:** 20/28 weight 600
- **Body-L:** 18/28 weight 400
- **Body:** 16/24 weight 400  ← default
- **Body-S:** 14/20 weight 400
- **Caption:** 12/16 weight 500 letter-spacing 0.02em uppercase
- **Mono:** JetBrains Mono — 14/20 — for SQL, citations, HMAC bytes
- **Numerals:** `font-feature-settings: "tnum"` everywhere a number appears (counters, latency, costs)

### 2.3 Spacing Scale (`design-system/tokens/spacing.ts`)

`4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96 / 128` — no other values allowed.

### 2.4 Radius

`0 / 6 / 12 / 18 / 9999`. Default `12`. Pill `9999`. Modal `18`.

### 2.5 Elevation

| Level | Light | Dark |
|---|---|---|
| 0 | none | none |
| 1 | `0 1px 2px rgba(15,23,42,0.06), 0 1px 1px rgba(15,23,42,0.04)` | `0 1px 2px rgba(0,0,0,0.4)` |
| 2 | `0 4px 8px rgba(15,23,42,0.08), 0 2px 4px rgba(15,23,42,0.04)` | `0 4px 8px rgba(0,0,0,0.5)` |
| 3 (modal) | `0 16px 40px rgba(15,23,42,0.16), 0 4px 12px rgba(15,23,42,0.08)` | `0 16px 40px rgba(0,0,0,0.6)` |

### 2.6 Motion

- **Snappy** (button, toggle): 120ms `cubic-bezier(0.2, 0, 0, 1)`
- **Smooth** (drawer, modal): 240ms `cubic-bezier(0.32, 0.72, 0, 1)`
- **Lazy** (hero, choropleth): 480ms `cubic-bezier(0.22, 1, 0.36, 1)`
- **Reduced motion:** when `prefers-reduced-motion: reduce` — all durations → 0ms, no transforms, opacity-only fades.

---

## 3. GLOBAL CHROME & LAYOUT

### 3.1 `Layout.tsx` (top-level shell)

```
┌────────────────────────────────────────────────────────────┐
│ TopBar — 56px                                              │
│ [NRG Logo]  [Sovereignty Strip]   [PersonaToggle] [User▾]  │
├────────────────────────────────────────────────────────────┤
│ TrustStrip — 32px (always visible)                         │
│ 🇮🇳 SOVEREIGN · DPDP · AUDIT-BOUND · 381,280 events signed │
├────────────────────────────────────────────────────────────┤
│ Main content (router outlet)                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Hero search → answers → drawers                    │  │
│  └──────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────┤
│ FooterMini — 24px : "Hosted on Indian soil · v0.9.0-rc1"   │
└────────────────────────────────────────────────────────────┘
```

**TopBar requirements:**
- Logo links to `/app` (never reload).
- Sovereignty strip is keyboard-tabbable; on focus, opens a tooltip explaining each badge.
- PersonaToggle (see §6).
- User avatar dropdown: `Profile · Audit log · Sign out`.

### 3.2 Responsive breakpoints

| Name | Width | Columns | Behavior |
|---|---|---|---|
| `xs` | < 480 | 4 | TopBar collapses to a hamburger; PersonaToggle becomes a bottom-sheet |
| `sm` | 480–768 | 6 | Stats strip wraps to 2 rows; graph hidden behind a "View graph" button |
| `md` | 768–1024 | 8 | TopBar full; CitationDrawer overlays at 80% width |
| `lg` | ≥ 1024 | 12 | Full desktop; CitationDrawer is a 480px right-side panel |

The professor's iPhone 15 Pro is 393px → must look polished at xs.

---

## 4. THE HERO QUERY EXPERIENCE (highest-stakes screen)

This is the screen that wins or loses ₹50L. Spec it like surgery.

### 4.1 Layout (desktop, `lg`)

```
┌────────────────────────────────────────────────────────────┐
│  HelloLine    "Hello Professor — ask anything about        │
│                Indian research."                           │
│                                                            │
│  ┌──────────────────────────────────────────────────┐     │
│  │ 🔍 [Animated placeholder cycles every 4s]   [↵] │     │
│  └──────────────────────────────────────────────────┘     │
│  • SuggestionChips: 4 pre-filled killer queries           │
│                                                            │
│  ScaleStrip (live counters animate up on first load)       │
│  58 TABLES · 1.2M RESEARCHERS · 47K INSTITUTES · 600GB    │
│                                                            │
│  TrustLine: "Every answer cited. Every byte signed."      │
└────────────────────────────────────────────────────────────┘
```

### 4.2 SearchBar (`components/SearchBar.tsx`)

| Prop | Type | Default | Behavior |
|---|---|---|---|
| `autoFocus` | bool | `true` | Focus on mount, ⌘/Ctrl+K refocuses |
| `placeholderRotation` | string[] | 4 examples | 4s per example, fades cross-dissolve |
| `onSubmit` | `(query) => void` | — | Triggers SSE stream |
| `disabled` | bool | `false` | When streaming, lock + show stop button |
| `multiline` | bool | `true` | Shift+Enter → newline; Enter → submit |
| `showSuggestions` | bool | `true` | 4 chips below |

**Acceptance:**
- TTI < 1500ms on slow 3G (Lighthouse mobile).
- Pressing Enter submits within 50ms.
- The placeholder rotation pauses on focus.
- Empty submit shows inline hint: "Try asking about funding, researchers, patents, or innovation"
- Maximum 50,000 characters; over → friendly inline truncate notice + amber border.

### 4.3 SuggestionChips (4 pre-filled killer queries)

Hard-coded for demo guarantee:
1. "Top 5 funding agencies by total grant amount"
2. "Which institutes moved the most innovations from TRL Level 4 to Level 9 in the last 5 years?"
3. "Researchers in solar energy who received seed funding 2020–2023 — what % filed patents?"
4. "Compare publication output of IIT Bombay vs IIT Madras in AI/ML, last 3 years"

Click → fills the SearchBar + auto-submits after 200ms (lets the user see what was typed).

### 4.4 ScaleStrip animated counters

`hooks/useAnimatedCounter.ts` — exists. Wire it. Numbers count up from 0 to target over 1200ms ease-out on first paint. Re-mount triggers re-animation.

### 4.5 First-load performance budget

| Metric | Budget |
|---|---|
| First Contentful Paint | < 800ms |
| Time to Interactive | < 1500ms |
| Total Blocking Time | < 100ms |
| Cumulative Layout Shift | < 0.05 |
| JS shipped | < 180KB gz |
| CSS shipped | < 30KB gz |
| Hero image (if any) | WebP, < 60KB, served with `loading="eager"` + `fetchpriority="high"` |

Use `<link rel="preconnect">` to API + Qdrant origins. Use `<link rel="preload" as="font">` for the two display fonts.

---

## 5. STREAMING ANSWER UX (the demo-killer fix)

`components/StreamingAnswerPanel.tsx` exists. Spec its 4-phase rendering exactly.

### 5.1 The 4 Phases

The backend SSE event stream emits events shaped:
```ts
type StreamEvent =
  | { phase: "planned";    plan: PlanDAG }
  | { phase: "executing";  sql?: string; retrieved_count?: number }
  | { phase: "synthesizing"; token: string }
  | { phase: "verified";   citations: Citation[]; audit_event_id: string };
```

### 5.2 Visual phase transitions

```
PHASE 1 — "Planning your question…"
  ↳ Show: AnimatedDots + skeleton 2-line subtitle
  ↳ When `phase=planned` arrives, render the DAG inline as a sub-step list:
      "1. Find top funding agencies"
      "2. Aggregate grant_received per agency"
      "3. Order by total descending"

PHASE 2 — "Asking the database…"
  ↳ Show: a code block with fade-in of the SQL (syntax-highlighted, mono)
  ↳ Below: "Retrieving rows…" with a row counter ticking up
  ↳ Animation: row counter ticks at most every 50ms

PHASE 3 — "Writing the answer…"
  ↳ Tokens stream into a body container, character-by-character
  ↳ Cursor block (▋) blinks at the streaming head
  ↳ Citation chips materialize inline as `[1]` `[2]` `[3]` when the model emits cite tokens

PHASE 4 — "Verified ✓" badge appears (green, 320ms slide-in)
  ↳ "Verified by HMAC chain · 26-byte signature · click for proof"
  ↳ Citations become clickable
```

### 5.3 Hard rules

- The user MUST see something visual within 200ms of pressing Enter.
- No phase shows a blank container for more than 1500ms — if the next event is delayed, animate a calm "still working…" sub-message.
- A "Stop" button is visible during phases 2 & 3 — clicking aborts the SSE and returns input focus.
- On any error mid-stream, transition into ErrorState (§9) with recovery actions, never reveal the raw error.

### 5.4 Acceptance test

```ts
// tests/e2e/streaming_answer.spec.ts
test("user sees streaming UX within 200ms and 4 phases complete in <8s on broadband", async () => {
  await page.goto("/app");
  await page.fill("[data-testid=searchbar]", "Top 5 funding agencies");
  const submitTime = Date.now();
  await page.press("[data-testid=searchbar]", "Enter");
  await expect(page.locator("[data-testid=phase-planning]")).toBeVisible({ timeout: 200 });
  await expect(page.locator("[data-testid=phase-verified]")).toBeVisible({ timeout: 8000 });
  expect(Date.now() - submitTime).toBeLessThan(8000);
});
```

---

## 6. THE PERSONA TOGGLE (the differentiation moment)

Hardcoded primary differentiator. Never hide.

### 6.1 Position & shape

Top-right of `Layout.tsx`. A pill segmented control:

```
┌──────────────────────────────────────┐
│  RESEARCHER  |  GOVERNMENT  | INDUSTRY │
└──────────────────────────────────────┘
```

- Active segment: `--nrg-tier-N` background, white text, slight elevation.
- Inactive: `--nrg-surface-2` background, `--nrg-ink-muted` text.
- Width: equal segments; min-width 360px desktop, full-width bottom sheet on `xs`.
- Keyboard: ←/→ toggles, Enter activates.
- ARIA: `role="tablist"` with `aria-selected` per segment.

### 6.2 Behavior on switch

1. Optimistic UI: persona accent updates immediately (<50ms).
2. Re-issue the **last query** under the new tier's JWT — automatically.
3. Render the answers **side-by-side** (or stacked on `xs`) so the difference is *visible*.
4. After the side-by-side reveal (3 seconds or user click), collapse to single panel of the new persona.

### 6.3 The "wow" moment

After the second answer finishes streaming under the new persona, an inline annotation appears:

> **What changed?** Researcher view showed individual researcher emails and exact grant amounts. Government view shows aggregated counts and policy-level totals. Industry view shows anonymized opportunity buckets. Same query, three different layers — enforced at the API, not the screen.

This single annotation closes the trust loop. Hard-code it as a feature, not a comment.

---

## 7. ANSWER RENDERING & CITATIONS

`AnswerPanel.tsx` + `CitationDrawer.tsx` + `parseCitations.ts` already exist. Specify their elevated state.

### 7.1 Answer body

- Markdown rendered with restricted set: `p, h1-h4, ul, ol, li, code, pre, blockquote, table, strong, em`.
- All `<a>` rewritten to internal cite drawers — never open external URLs from answer body.
- `<table>` rendered in a `<TableScroll>` wrapper that adds horizontal-scroll on `xs` with sticky first column.
- Numbers in body wrapped in `<NumChip>` showing thousands-separator + tooltip showing exact value: `1.2M (1,247,083)`.

### 7.2 CitationLink (`CitationLink.tsx`)

Rendered as a small chip: `[1]` `[2]` etc. Inline in the body text.

| State | Visual |
|---|---|
| Default | `--nrg-tier-N` background at 12% alpha, tier color text, radius 6 |
| Hover | full alpha background, white text, 1px lift |
| Focused | 3px focus ring `--nrg-focus` |
| Pressed | scale 0.97 |
| Open (drawer matched) | persistent active style — color reverses |

Click → opens `CitationDrawer` to the right (desktop) or as bottom-sheet (mobile).

### 7.3 CitationDrawer (`CitationDrawer/CitationDrawer.tsx`)

Drawer width: 480px on `lg`, 80% on `md`, 100% on `xs`.

Structure top-down:

```
[ × Close (Esc) ]                                    [ Permalink 🔗 ]

CITATION [1]
─────────────────────────────────────────────
SOURCE           publications.publication_id = 4031
PROVENANCE       researcher_publications JOIN publications
RETRIEVED AT     2026-04-25 14:31:07 IST
AUDIT EVENT      0xa7f3b21c… (click to verify)

EXECUTED SQL  (mono, syntax-highlight, copy button)
─────────────────────────────────────────────
SELECT p.publication_id, p.title, p.year
FROM publications p
JOIN researcher_publications rp ON ...
WHERE p.access_tier >= ?
LIMIT 2000;

SOURCE ROW  (key/value list with copy)
─────────────────────────────────────────────
publication_id    4031
title             "Solar cell efficiency in tropical climates"
year              2023
authors           [Dr. R. Sharma, Dr. K. Patel]   ← anonymized for T3
citations         147
access_tier       1

HMAC PROOF
─────────────────────────────────────────────
Per-user key derived: hmac(CHAIN_KEY, user_id || jwt_kid || salt)
Event signature      : 0xa7f3b21c d4e2... (verified ✓)
DB co-sign signature : 0x91fb27d1 8c44... (verified ✓)
Chain prev hash      : matches ✓

[ Verify on chain ] [ Export this citation as PDF ]
```

### 7.4 Acceptance

- Drawer opens in < 240ms with content already populated (data prefetched on stream-end).
- ESC closes; FocusTrap returns focus to the citation chip.
- `Verify on chain` button fires `GET /audit/event/{id}/verify` and updates the badge in-place.

---

## 8. EMPTY STATES (the silent killer)

`components/ErrorState/ErrorState.tsx` exists. Add a sibling `components/EmptyState/EmptyState.tsx` with this taxonomy. **No screen ever shows "0 rows" or "no results" without an action.**

### 8.1 Empty state taxonomy

| Cause | Headline | Body | Primary action | Secondary |
|---|---|---|---|---|
| SQL returned 0 rows | "No matches in this slice." | "Try widening the year range or removing the location filter." | `[ Widen to last 10 years ]` (auto-generated) | `[ Edit query ]` |
| RAG returned 0 chunks | "Couldn't find this in our research index." | "We're confident there's data — let's search the structured tables instead." | `[ Re-route to SQL ]` | `[ Show me what's covered ]` |
| Persona-tier blocks the answer | "This persona can't see that." | "Switch to Researcher to view individual records, or stay here for aggregated counts." | `[ Switch to Researcher ]` | `[ Show aggregated answer ]` |
| Vector index out of date | "Index is being rebuilt — using cached results." | "Drift detector triggered a re-index 47s ago. Latest answers may be 3 minutes stale." | `[ Wait & retry ] (auto-retries in 60s)` | `[ Continue with cached ]` |
| Query too vague | "I need one more detail." | "Are you asking about *grants given* (DST/SERB) or *grants received* (institute totals)?" | `[ Grants given ]` | `[ Grants received ]` |
| Network down | "We can't reach the database right now." | "Your audit trail is safe. We'll retry when the connection returns." | `[ Retry now ]` (with countdown) | `[ See cached answers ]` |

### 8.2 Visual

- Centered in the answer container.
- 64px illustration (lottie or static SVG) — never sad-face emoji; use a subtle `🪔` lamp / `🔍` magnifier appropriate to context.
- Headline H3, body Body, primary CTA filled, secondary text-link.
- Animation: 200ms fade + 8px y-translate on mount.

---

## 9. ERROR STATES (zero stack traces)

### 9.1 Three error tiers

| Tier | Cause | UI |
|---|---|---|
| **Recoverable** | network blip, breaker open, timeout | Inline yellow banner with retry; answer area shows last-good or skeleton |
| **Tier-blocked** | RBAC says no | Inline blue banner with persona-switch suggestion |
| **System** | uncaught exception | Full-page friendly fallback (NEVER stack trace) with an Audit Trail link and a "Talk to support" mailto |

### 9.2 ErrorState (`components/ErrorState/ErrorState.tsx`)

Props:
```ts
type ErrorStateProps = {
  tier: "recoverable" | "tier-blocked" | "system";
  title: string;          // human, < 60 chars
  body: string;           // human, < 200 chars
  primaryAction?: { label: string; onClick: () => void };
  secondaryAction?: { label: string; onClick: () => void };
  errorCode?: string;     // e.g. "NRG-CIRCUIT-OPEN-A1" for support ref
  traceId?: string;       // hidden behind a "show details" link, for debug
};
```

### 9.3 The sacred rule

`tests/e2e/no_stack_trace.spec.ts` runs after every build:
```ts
test("no <pre>, no Error:, no Traceback in any error path", async () => {
  for (const route of ALL_ERROR_ROUTES) {
    await page.goto(route);
    const html = await page.content();
    expect(html).not.toMatch(/Traceback|Error:|<pre>|stacktrace/i);
  }
});
```

If this test fails, the build fails. No exceptions.

---

## 10. THE THREE PERSONA DASHBOARDS

`views/ResearcherDashboard.tsx` · `views/GovernmentDashboard.tsx` · `views/IndustryDashboard.tsx` — already scaffolded. Spec their elevated state.

### 10.1 Researcher (Tier 1) — `--nrg-tier-1` accent

Above-the-fold cards (in this exact order — left-to-right, top-to-bottom):

| Card | Metric | Source endpoint |
|---|---|---|
| MyImpact | h-index, citations, recent pubs | `/api/researcher/me/stats` |
| OpenFunding | 5 newest grants matching expertise | `/api/funding/match?expertise=` |
| Collaborators | top 8 co-authors with sparkline | `/api/researcher/me/collab` |
| ResearchPulse | trending keywords last 30 days | `/api/trends/keywords?window=30d` |

Below the fold: full ForceGraph (`components/ForceGraph.tsx`) of the user's collab network, max-depth 3, hover for institute/grant detail.

### 10.2 Government (Tier 2) — `--nrg-tier-2` accent

| Card | Metric |
|---|---|
| NationalSpend | total grant ₹ + YoY % + spark |
| TopAgencies | bar chart top 10 by ₹ allocated |
| TRLProgression | sankey TRL-1 → TRL-9 by sector |
| StateChoropleth | India map shaded by total funding (`IndiaMapChoropleth.tsx`) |

No individual researcher names anywhere.

### 10.3 Industry (Tier 3) — `--nrg-tier-3` accent

| Card | Metric |
|---|---|
| OpportunityFeed | 10 anonymized researcher pods open to collaboration |
| EmergingDomains | wordcloud of fast-rising fields |
| PatentSurge | bar chart of patents by sector last quarter |
| FundingByMaturity | seed / Series A / scale by sector |

T3 sees `Researcher_a8f3` not `Dr. R. Sharma`. Enforced at API; the frontend never knows the real name.

---

## 11. ACCESSIBILITY (WCAG 2.1 AA, target AAA where reasonable)

### 11.1 Hard requirements

- **Contrast:** every foreground-on-background must score ≥ 4.5:1 normal text, ≥ 3:1 large text (≥18pt). Verified by `frontend/tests/a11y/contrast.test.ts` running axe-core on every Storybook page.
- **Keyboard:** every interactive must reach via Tab; activate via Enter/Space. Modal/drawer FocusTrap returns focus on close.
- **Screen reader:** every interactive has `aria-label` or accessible text. Charts have `aria-describedby` linking to a hidden `<table>` of the same data.
- **Reduced motion:** honored via `useReducedMotion()` hook reading `prefers-reduced-motion`.
- **Focus rings:** 3px solid `--nrg-focus` with 2px offset — never `outline: none` without an alternative.
- **Skip link:** "Skip to main content" as the first focusable element.
- **Page titles:** unique per route, prefixed `NRG · `.
- **Language:** `<html lang="en-IN">` on the root.
- **Form labels:** every input has a visible label OR `aria-labelledby`. Placeholders are NEVER the only label.

### 11.2 Test surface

```bash
npm run test:a11y    # axe-core via @axe-core/playwright
npm run test:contrast # contrast ratios via wcag-color
npm run test:keyboard # tab-order assertions per route
```

Fail-the-build threshold: zero a11y errors, ≤ 5 a11y warnings per route.

---

## 12. MOBILE (375px target — the professor's iPhone)

| Concern | Spec |
|---|---|
| Layout | single column; PersonaToggle becomes a bottom sheet trigger |
| Search bar | sticky at the top while scrolling answers |
| ForceGraph | hidden behind a "View Network" button → opens fullscreen modal with pinch-zoom |
| CitationDrawer | full-screen modal slide-up |
| Tap target | min 44×44 px (Apple HIG) |
| Hover states | replaced by long-press tooltips |
| Tables | horizontal scroll with sticky first column + scroll-shadow indicators |

**Acceptance test:** open `/app` on iPhone 15 Pro at 393×852, complete the killer-query #1 end-to-end including opening a citation drawer, no horizontal scroll, all CTAs tappable. Screen-record attached to `evidence/<date>/mobile_e2e.mp4`.

---

## 13. API CONTRACT (must match backend)

### 13.1 SSE stream — `POST /query/stream`

Request:
```json
{ "query": "Top 5 funding agencies", "persona": "government", "session_id": "abc..." }
```

Response — `text/event-stream`:
```
event: planned
data: {"plan":{"steps":[...],"edges":[...]}}

event: executing
data: {"sql":"SELECT ...","retrieved_count":0}

event: executing
data: {"retrieved_count":127}

event: synthesizing
data: {"token":"The "}

event: synthesizing
data: {"token":"top "}

event: verified
data: {"citations":[...],"audit_event_id":"0x..."}

event: done
data: {}
```

Heartbeat: server emits `event: ping\ndata: {}` every 10s. Client times out at 25s of silence and shows recoverable error.

### 13.2 REST fallback — `POST /query` (non-streaming)

Same shape, but client emulates the 4 phases over a 1500ms timeline (planning 0–500, executing 500–1000, synthesizing 1000–1500). Used when SSE is blocked by a corporate proxy at UAT.

### 13.3 Persona switch — `POST /auth/persona`

Atomic: server returns a new JWT in 1 round-trip; client never holds two tokens at once.

### 13.4 Audit event — `GET /audit/event/{id}`

Returns full event including `executed_sql`, `source_rows`, `hmac_signature`, `db_cosign_signature`, `prev_hash`, `chain_position`. Used by CitationDrawer.

### 13.5 Audit verify — `GET /audit/event/{id}/verify`

Server-side verification; returns `{ valid: bool, errors: string[] }` in <500ms.

---

## 14. STATE MANAGEMENT

`stores/queryStore.ts` + `stores/dpdpStore.ts` exist (Zustand). Spec the canonical shape.

### 14.1 queryStore

```ts
type QueryStore = {
  // session
  sessionId: string;
  activeDomain: string | null;     // mirrors backend NRGState
  history: Query[];                // last 50 queries this session

  // current
  currentQueryId: string | null;
  currentPhase: "idle" | "planning" | "executing" | "synthesizing" | "verified" | "error";
  currentTokens: string[];
  currentCitations: Citation[];

  // actions
  submit: (query: string) => Promise<void>;
  abort: () => void;
  retry: () => void;
  selectCitation: (id: string) => void;
  switchPersona: (persona: Persona) => Promise<void>;
};
```

### 14.2 No localStorage

Per artifacts rules + DPDP — keep all in-memory. Persistence happens via the audit chain on the backend, not browser storage. If a refresh is needed, fetch session from `/auth/session`.

---

## 15. MICROCOPY LIBRARY (the words the professor reads)

Centralize in `frontend/src/i18n/en-IN.ts`. Every visible string lives here.

### 15.1 Hero

- Welcome: "Hello, Professor. Ask anything about Indian research."
- Placeholder rotation:
  1. "Top 5 funding agencies by total grant amount this year"
  2. "Which institutes moved the most innovations to TRL-9?"
  3. "Compare AI/ML output of IITs over the last 3 years"
  4. "Researchers in solar energy who filed patents after seed funding"

### 15.2 Trust strip

- "🇮🇳 Sovereign · Hosted on Indian soil"
- "DPDP Act 2023 · IITGN-certified compliance"
- "Audit-bound · 381,280 events signed"
- Hover tooltip on each: short 2-sentence explanation.

### 15.3 Phase narration

- Phase 1: "Planning your question…"
- Phase 2: "Asking the database…"
- Phase 3: "Writing the answer…"
- Phase 4: "Verified ✓"

### 15.4 Empty + error copy

Every string from §8.1 lives here. Translatable later (Hindi `hi-IN`, Tamil `ta-IN`).

### 15.5 The forbidden phrases

Never appear in UI:
- "An error occurred"
- "Something went wrong"
- "Please try again later"
- "0 rows returned"
- "Internal Server Error"
- "Network Error"
- "undefined" / "null"
- Anything starting with `Error:` or `TypeError:`

---

## 16. ANIMATION CHOREOGRAPHY

### 16.1 First-paint sequence

```
0ms     — Body fade-in starts
80ms    — Logo + sovereignty strip slide down (200ms, smooth)
120ms   — TopBar reveals
240ms   — Hero text fades in (180ms, lazy)
320ms   — SearchBar scales from 0.96→1.0 + fade (240ms, smooth)
400ms   — SuggestionChips stagger in (40ms each, snappy)
600ms   — ScaleStrip counters start animating up to value (1200ms, lazy)
1500ms  — All settled. TTI achieved.
```

### 16.2 Persona switch

```
0ms     — Toggle pill morphs to new color (120ms, snappy)
50ms    — Page accent ring updates
100ms   — Last query re-issues under new JWT
200ms   — New answer panel slides in beside old (240ms, smooth)
3000ms  — Old panel collapses, new becomes primary (480ms, lazy)
```

### 16.3 Stream completion

```
On `verified` event:
0ms     — Phase header text crossfades to "Verified ✓"
80ms    — Green pulse ring on the badge (single 600ms ease-out)
120ms   — Citation chips become clickable + 3px focus-able
240ms   — "Try a follow-up:" suggestion strip slides in below
```

---

## 17. THE AUDIT PANEL (`/app/audit`)

`pages/DPDP-Audit.tsx` exists. Spec its elevation.

### 17.1 Layout

```
TopBar
─────────────────────────────────────
[ Filters ]       [ Search HMAC ]   [ Export ]
SignedSinceCounter: 381,280 events · 0 errors
─────────────────────────────────────
Virtualized event list (react-window)
  Each row: [time] [user] [tier] [query preview] [HMAC short] [✓ verified]
  Click row → side drawer with full event (same as CitationDrawer §7.3)
─────────────────────────────────────
Footer: chain integrity status, last verified timestamp
```

### 17.2 The "show me proof" demo

When the professor asks "how do I know this isn't fabricated?":

1. From an answer screen, click any citation chip.
2. Drawer slides in (480px right) within 240ms.
3. The drawer shows: executed SQL, source row, HMAC signature, DB co-sign signature, chain position.
4. Click "Verify on chain" → fires the verify endpoint, badge turns green within 500ms.
5. Click "Open in audit" → `/app/audit/event/{hmac}` → full chain neighborhood (event ±2 in chain).

This sequence MUST be rehearsable in 30 seconds. Time it. If it's slower, fix it.

---

## 18. SECURITY-VISIBLE UX

### 18.1 Sanitiser block UI

When the prompt sanitiser blocks an injection / PII attempt, the user sees:

```
╭──────────────────────────────────────────────╮
│ 🛡️  Query refused for your safety           │
│                                              │
│ This question contains a pattern we don't    │
│ allow (looks like an injection attempt or   │
│ a request for personal data).                │
│                                              │
│ [ Why was this blocked? ]   [ Edit query ]  │
╰──────────────────────────────────────────────╯
```

Never just silence the request. Always tell the user why, in plain English.

### 18.2 Tier-block UI

Already covered in §8.1 row 3 — showing the persona-switch CTA is the demo gold.

### 18.3 Session expiry UX

JWT expires in 1 hour. At 55:00 elapsed, show a non-blocking toast: "Session refreshes in 5 minutes — your work is auto-saved." At 60:00, silent refresh; if refresh fails, modal: "Welcome back — please re-confirm your identity" + login form pre-filled.

---

## 19. CLEANUP — duplicate components to consolidate

Yesterday's audit found duplication. Agents must merge:

| Old | Keep | Action |
|---|---|---|
| `components/AnswerPanel.tsx` (root) | `components/AnswerPanel/AnswerPanel.tsx` | delete root file; update imports via codemod |
| `components/SkeletonLoader.tsx` (root) | `components/Skeleton/SkeletonLoader.tsx` | same |
| `components/CitationDrawer.tsx` (root) | `components/CitationDrawer/CitationDrawer.tsx` | same |
| `components/ErrorBoundary.tsx` + `WidgetErrorBoundary.tsx` | merge into `components/ErrorBoundary/ErrorBoundary.tsx` with `scope: "page" | "widget"` prop | |
| `views/GovernmentView.tsx` + `views/GovernmentDashboard.tsx` | keep `…Dashboard.tsx`; route `…View.tsx` redirects | |
| `views/IndustryView.tsx` + `views/IndustryDashboard.tsx` | same | |
| `views/ResearcherView.tsx` + `views/ResearcherDashboard.tsx` | same | |
| `frontend/src/__test__graph.tsx` + `TestApp.tsx` | move to `frontend/src/__tests__/` | |

After cleanup, every component path is unique. Fail the build if a duplicate filename appears under `components/`.

---

## 20. STORYBOOK + VISUAL REGRESSION

Add `frontend/.storybook/` with:
- One story per component, every variant (default, hover, focus, active, disabled, loading, error, empty).
- Chromatic / Loki for visual regression on every PR.
- Stories for the 3 persona dashboards with mocked API.
- Stories for the 6 empty states + 3 error tiers.

CI gate: any visual diff > 0.1% requires reviewer approval.

---

## 21. TELEMETRY (UAT-grade observability)

Wire `frontend/src/lib/telemetry.ts` (new file) emitting events:

| Event | When | Payload |
|---|---|---|
| `app.first_paint` | once per session | `{ fcp_ms, tti_ms, cls }` |
| `query.submitted` | every submit | `{ query_chars, persona, session_id }` |
| `query.phase_observed` | each SSE phase | `{ phase, ms_since_submit }` |
| `query.completed` | on `verified` | `{ total_ms, citation_count, persona }` |
| `query.aborted` | on stop | `{ ms_since_submit, phase_at_abort }` |
| `citation.opened` | drawer open | `{ citation_id, query_id }` |
| `audit.verified` | verify-on-chain click | `{ hmac, valid, ms }` |
| `persona.switched` | toggle | `{ from, to, last_query_id }` |
| `error.shown` | every ErrorState mount | `{ tier, code, route }` |
| `empty.shown` | every EmptyState mount | `{ cause, route }` |

POST batched to `/api/telemetry` every 10s. PII-stripped at the edge. Used in UAT to measure the demo experience precisely.

---

## 22. DEMO-DAY POLISH CHECKLIST (the night before)

| # | Check | Owner | Verified? |
|---|---|---|---|
| 1 | Pre-warm cloud LLM with 3 dummy queries 5 min before demo | Founder | ☐ |
| 2 | All 4 killer queries cached in Redis (60-min TTL) | Athena | ☐ |
| 3 | Persona toggle tested with all 3 demo accounts | Hermes | ☐ |
| 4 | CitationDrawer opens in <240ms on the demo machine | Apollo | ☐ |
| 5 | Mobile (393px) tested on the actual phone the founder will use | Apollo | ☐ |
| 6 | Session expiry test: 55-min nudge appears | Hermes | ☐ |
| 7 | Stack-trace probe (§9.3 test) passes on every error route | Iris | ☐ |
| 8 | Lighthouse score ≥ 95 on `/app` (mobile + desktop) | Vulcan | ☐ |
| 9 | `prefers-reduced-motion` respected (toggle in OS, re-test) | Iris | ☐ |
| 10 | Chrome, Safari, Edge — same render on all 3 | Hermes | ☐ |
| 11 | Wi-Fi failover — switch to phone hotspot mid-query, expect graceful retry | Apollo | ☐ |
| 12 | Caffeinate the demo laptop; battery > 80%; charger in bag | Founder | ☐ |
| 13 | Browser zoom at 100%; window pinned to second monitor | Founder | ☐ |
| 14 | DevTools closed; Console clean; no React warnings | Apollo | ☐ |
| 15 | Pre-recorded backup video saved to USB stick (in case Wi-Fi dies) | Founder | ☐ |

---

## 23. ACCEPTANCE GATE — DEFINITION OF EXTRAORDINARY

The frontend is demo-ready when ALL of these are simultaneously true:

```
☐ Lighthouse mobile score ≥ 95
☐ Lighthouse desktop score ≥ 98
☐ axe-core: 0 errors, ≤ 5 warnings per route
☐ FCP < 800ms on slow 3G; TTI < 1500ms
☐ Streaming UX: visible feedback < 200ms after submit
☐ All 6 empty states implemented with copy + CTA
☐ All 3 error tiers implemented; no <pre> in any error route
☐ Persona toggle works; side-by-side comparison reveals real diff
☐ CitationDrawer opens in <240ms; verify-on-chain in <500ms
☐ Mobile (393px) end-to-end tested on real iPhone
☐ Reduced-motion respected
☐ All forbidden phrases (§15.5) absent from build
☐ Telemetry events firing for every interaction
☐ 4 killer queries cached and rehearsed
☐ Storybook published; 0 unapproved visual diffs
☐ Cleanup §19 done; no duplicate component files
☐ Demo-day checklist §22 complete
```

If any of those is ☐, the founder does not demo. The score in the audit report is < 9.0 until all 17 are ☑.

---

## 24. WORK BREAKDOWN FOR AGENTS (suggested allocation)

| Agent | Sections | Hours |
|---|---|---|
| **Athena-UX** (information architecture, microcopy, empty/error states) | §1, §8, §9, §15 | 8 |
| **Hermes-UI** (components, dashboards, persona toggle, layout) | §3, §4, §6, §10 | 14 |
| **Apollo-Polish** (streaming, citations, audit panel, motion) | §5, §7, §16, §17 | 12 |
| **Iris-A11y** (accessibility, mobile, reduced motion, focus management) | §11, §12 | 6 |
| **Vulcan-Perf** (performance budgets, telemetry, Lighthouse, Storybook, cleanup) | §13, §14, §20, §21, §19 | 8 |
| **Cassandra-QA** (acceptance gates, demo checklist, e2e tests) | §22, §23, all e2e tests | 6 |

**Total: ~54 agent-hours** (8 calendar hours with 6 agents in parallel where possible).

---

## 25. THE ETERNAL UX PRINCIPLES (the soul of the spec)

1. **Speed is a feature.** 200ms feels instant; 1000ms feels slow; 3000ms feels broken. Engineer for instant.
2. **Citations are the product.** Every claim is clickable. Every click leads to proof. The audit chain is not metadata — it's the answer's spine.
3. **Empty is never empty.** Every zero-state is a chance to teach the next click.
4. **Errors are humans.** No stack trace ever reaches the professor. Every failure has a face and a hand-hold.
5. **Three personas, one product.** The toggle is the differentiation. Make it impossible to miss.
6. **Sovereignty is a feeling.** The chrome, the colors, the copy — every pixel says "this belongs to India" without saying it.
7. **Motion is conversation.** Every animation tells the user where they are, what's happening, what's next. No animation for decoration.
8. **Mobile is not optional.** The professor pulls out his iPhone. If the page breaks, the deal breaks.
9. **Trust is earned every screen.** The 🇮🇳 strip, the audit count ticker, the verify-on-chain badge — these are not decoration. They are the moats.
10. **The professor is not a developer.** Every word, every icon, every wait — judged by a non-technical mind. Optimize for that mind, always.

---

**END OF SPEC — VERSION 1.0 ETERNAL**

Hand this document to your agents. Reference sections by number. Demand acceptance gates per §23. Run the demo-day checklist §22 the night before. The professor leans forward — or the deal dies. There is no in-between.

— Guru Agent (Claude), 2026-04-25
