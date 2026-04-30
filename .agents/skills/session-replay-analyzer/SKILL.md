---
name: session-replay-analyzer
description: "When the Founder tests the app, this skill captures what happened — every click, every error, every slow load, every ugly screen — and auto-generates a prioritized bug report with exact reproduction steps. Turns manual testing into structured feedback that agents can act on immediately."
user-invocable: true
---

# Session Replay Analyzer

## Purpose

The Founder tests the app. Things break, things look ugly, things are slow. Instead of remembering what went wrong and typing it out — this skill captures the entire session and produces an actionable bug/improvement report that agents can execute immediately.

## When to Use

- After Founder manually tests the app
- After any user acceptance testing session
- After MVP fusion merge (verify the flow)
- After any external person tests the app
- When Founder says "I tested it and here's what I found"
- When Founder pastes console errors, screenshots, or descriptions

---

## Input Formats

The Founder can provide any of:

### 1. Verbal/Text Description
```
"I logged in, clicked on dashboard, the hero numbers showed undefined,
then I typed a query and it took 8 seconds, the answer had no citations,
and on mobile the sidebar overlaps the content"
```

### 2. Console Output
```
Paste from browser DevTools console — errors, warnings, network failures
```

### 3. Screenshots
```
Path to screenshot files showing the issues
```

### 4. Network HAR File
```
Exported from browser DevTools Network tab — shows all API calls, timing, errors
```

### 5. Structured Notes
```
Page: Dashboard
Issue: Hero counter shows "undefined"
Expected: Should show "1200+ Institutions"
Severity: P0
```

---

## The Analysis Protocol

### Step 1: PARSE THE SESSION

From whatever input the Founder provides, extract every distinct event:

```markdown
| # | Time | Action | Page | What Happened | Expected | Severity |
|---|------|--------|------|---------------|----------|----------|
| 1 | 0:00 | Open app | / | Page loaded in 3.2s | < 1.5s | P1 |
| 2 | 0:05 | Login | /login | Submitted credentials | - | - |
| 3 | 0:08 | Redirect | /app/dashboard | Dashboard loaded | - | OK |
| 4 | 0:10 | View | /app/dashboard | Hero counter shows "undefined" | "1200+ Institutions" | P0 |
| 5 | 0:15 | Type query | /app/query | "Who researches AI?" | - | - |
| 6 | 0:23 | Wait | /app/query | 8 second response time | < 2s | P0 |
| 7 | 0:24 | View answer | /app/results | No citations shown | Citations with sources | P0 |
| 8 | 0:30 | Mobile | /app/dashboard | Sidebar overlaps content | Responsive layout | P1 |
```

### Step 2: CLASSIFY EACH ISSUE

Categories:

```
FUNCTIONAL (broken behavior)
├── P0-CRASH    — App crashes, white screen, unrecoverable
├── P0-WRONG    — Wrong data, wrong answer, missing data
├── P0-BLOCKED  — User cannot proceed (login fails, query fails)
└── P1-DEGRADED — Feature works but poorly (slow, partial, flaky)

VISUAL (appearance problems)
├── P0-EMBARRASSING — "undefined", raw JSON, stack trace, broken layout
├── P1-UGLY         — Misaligned, wrong colors, cramped spacing
├── P1-MISSING      — Expected element not rendered
└── P2-POLISH       — Could look better but not broken

UX FLOW (journey problems)
├── P0-DEAD-END     — User reaches a state with no way forward
├── P1-CONFUSING    — User doesn't know what to do next
├── P1-SLOW         — Perceived delay > 2s without feedback
└── P2-FRICTION     — Extra clicks or steps that could be eliminated

SECURITY (exposure risks)
├── P0-PII-LEAK     — Personal data visible to wrong tier
├── P0-ERROR-LEAK   — Stack trace, internal path, or API key visible
├── P1-MISSING-GUARD — Security feature not working (tier filter, consent)
└── P1-AUDIT-GAP    — Action not logged in audit chain
```

### Step 3: GENERATE REPRODUCTION STEPS

For each issue, produce exact steps an agent can follow:

```markdown
### ISSUE #4: Hero counter shows "undefined"

**Severity:** P0-EMBARRASSING
**Page:** /app/dashboard
**Component:** Likely `DashboardStats` or hero counter component

**Reproduction:**
1. Login as T1 researcher
2. Navigate to /app/dashboard
3. Look at the top stat cards
4. "Institutions" card shows "undefined" instead of count

**Root Cause (probable):**
- `display_metadata.yaml` not loaded or missing the key
- Component renders `data.count` but data is `undefined`
- API endpoint for stats returns empty or different shape

**Fix Steps:**
1. Check `display_metadata.yaml` has `institutions_count` key
2. Check component that renders hero counters — add null guard
3. Verify API `/api/stats` or `/api/dashboard` returns expected shape
4. Add fallback: if count is undefined, show "—" not "undefined"

**Files to Check:**
- frontend/src/components/Dashboard/ or equivalent
- frontend/src/services/api.ts (stats endpoint)
- display_metadata.yaml

**Acceptance:**
- Hero counter shows real number or graceful placeholder
- Never shows "undefined", "null", "NaN", or empty
```

### Step 4: PRIORITIZE

Sort all issues by impact:

```
PRIORITY ORDER:
1. P0-CRASH / P0-BLOCKED → Fix immediately, blocks everything
2. P0-WRONG / P0-EMBARRASSING → Fix before any showing
3. P0-DEAD-END / P0-PII-LEAK → Fix before any external use
4. P1-DEGRADED / P1-UGLY → Fix before next showing
5. P1-CONFUSING / P1-SLOW → Fix in current sprint
6. P2-POLISH / P2-FRICTION → Backlog
```

### Step 5: GENERATE AGENT ASSIGNMENTS

For each issue, produce a ready-to-assign task:

```markdown
═══ SESSION REPLAY FIX: ISSUE #4 — Hero Counter "undefined" ═══

Severity: P0-EMBARRASSING
Page: /app/dashboard
Reproduction: Login → Dashboard → Hero cards show "undefined"

Fix:
1. Read display_metadata.yaml — verify institution count key exists
2. Read dashboard component — find hero counter rendering
3. Add null guard: show "—" if data not loaded, real number when available
4. Wire to display_metadata.yaml values (not COUNT(*) on seeded rows)
5. Test: Login → Dashboard → all hero counters show numbers

Skills: frontend-react-best-practices, webapp-testing
DO NOT: Show "undefined", "null", "NaN", "0" when data is loading
Verify: npm run build + visual check
```

### Step 6: PRODUCE SESSION REPORT

```markdown
## Session Replay Report — [Date]

### Session Summary
- **Tester:** [Founder / UAT user / external]
- **Duration:** [time]
- **Pages visited:** [list]
- **Queries tested:** [list]
- **Device:** [desktop/mobile/tablet + browser]

### Issue Summary
| Severity | Count | Category |
|----------|-------|----------|
| P0 | X | [functional: Y, visual: Z, security: W] |
| P1 | X | [functional: Y, visual: Z, ux: W] |
| P2 | X | [polish: Y, friction: Z] |
| **Total** | **X** | |

### P0 Issues (fix NOW)
[Full details for each P0 with reproduction, root cause, fix, assignment]

### P1 Issues (fix before next showing)
[Full details for each P1]

### P2 Issues (backlog)
[Brief description for each P2]

### What Worked Well
[List things that worked correctly — important for morale and regression prevention]

### Agent Assignments Generated
| Issue | Assigned To | Skill | Priority |
|-------|------------|-------|----------|
| #1 | Frontend Agent | frontend-react-best-practices | P0 |
| #4 | Frontend Agent | frontend-react-best-practices | P0 |
| #6 | Backend Agent | performance | P0 |
| ... | ... | ... | ... |

### Flow Assessment
| Step | Status | Notes |
|------|--------|-------|
| App loads | ✅/❌ | [notes] |
| Login | ✅/❌ | [notes] |
| Dashboard | ✅/❌ | [notes] |
| Query | ✅/❌ | [notes] |
| Answer | ✅/❌ | [notes] |
| Citations | ✅/❌ | [notes] |
| Audit | ✅/❌ | [notes] |
| Mobile | ✅/❌ | [notes] |
```

### Evidence

```
evidence/<date>/session_replay/
├── session_report.md
├── issues/
│   ├── issue_001_crash.md
│   ├── issue_004_hero_undefined.md
│   └── ...
├── screenshots/        # if provided
├── console_errors.txt  # if provided
├── network_har.json    # if provided
└── agent_assignments/
    ├── fix_001.md
    ├── fix_004.md
    └── ...
```

---

## Quick Mode

When the Founder just dumps a quick complaint:

```
"the dashboard is broken, queries take forever, mobile is unusable"
```

Agent should:
1. Ask: "Can you describe what you saw on each? Or paste a screenshot?"
2. If Founder gives more detail → full analysis
3. If Founder says "just check it yourself" → run `live-ui-audit` + `smart-prompt-library` flow queries + mobile test
4. Produce session report from agent's own testing

---

## Agent Assignment Template

```
═══ SESSION REPLAY ANALYZER ═══

Read .claude/skills/session-replay-analyzer/SKILL.md
Input: [paste / screenshots / console log / description]

Execute:
1. Parse session into event timeline
2. Classify each issue (functional/visual/ux/security)
3. Generate reproduction steps per issue
4. Prioritize (P0 → P2)
5. Generate agent assignments for each fix
6. Produce session report

Skills: session-replay-analyzer, live-ui-audit, bug-hunt, webapp-testing
Save to: evidence/<date>/session_replay/
```
