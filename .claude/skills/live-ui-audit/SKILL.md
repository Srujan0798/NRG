---
name: live-ui-audit
description: "Auto-screenshot every page and critical flow in the NRG app, compare before/after changes, catch visual regressions, broken layouts, missing components, and embarrassing UI states. Runs against a live or dev server. Produces a visual audit report with pass/fail per screen."
user-invocable: true
---

# Live UI Audit

## Purpose

Catch every visual problem BEFORE the professor's assistant sees it. This skill screenshots every page, every tier, every state — and produces a pass/fail report.

## When to Use

- After any frontend change (merged MVP, component update, style change)
- Before any external session or showing
- After Hybrid MVP Fusion merge
- When Founder says "audit the UI" or "check how it looks"
- Nightly automated check

---

## The Audit Protocol

### Step 1: ENUMERATE ALL SCREENS

Every route in the app must be audited. Read `frontend/src/App.tsx` to get routes.

**Core screens (must exist and work):**

```
PAGE                          ROUTE                  TIERS
─────────────────────────────────────────────────────────
Login                         /login                 All
Researcher Dashboard          /app/dashboard         T1
Government Dashboard          /app/dashboard         T2
Industry Dashboard            /app/dashboard         T3
Query/Search                  /app/query             T1, T2, T3
Answer/Results                /app/results           T1, T2, T3
Researcher Profile            /app/researchers       T1
Publications                  /app/publications      T1
Audit Trail                   /app/audit             T1 (admin)
Settings                      /app/settings          All
Graph View                    /app/graph             T1
Reports                       /app/reports           T2
Industry View                 /app/industry          T3
```

### Step 2: CAPTURE STATES

For each screen, capture these states:

| State | What to Check |
|-------|--------------|
| **Loaded (with data)** | Layout correct, data renders, no overflow, no clipping |
| **Empty** | Empty state shows helpful message, not blank/broken |
| **Loading** | Skeleton or spinner visible, no flash of wrong content |
| **Error** | Friendly message, retry button, NO stack trace, NO raw error |
| **Mobile (393px)** | No horizontal scroll, touch targets ≥44px, readable text |
| **Tablet (768px)** | Layout adapts, nothing cramped |

### Step 3: VISUAL CHECKLIST PER SCREEN

For every screenshot, check:

```
LAYOUT
├── [ ] No horizontal overflow
├── [ ] No overlapping elements
├── [ ] No cut-off text
├── [ ] Proper spacing (no cramped, no excessive gaps)
├── [ ] Consistent margins/padding
└── [ ] Grid alignment (columns line up)

TYPOGRAPHY
├── [ ] Headings are distinct from body text
├── [ ] Font loads (no system font fallback flash)
├── [ ] No text smaller than 14px
├── [ ] Line height readable (1.4-1.6)
└── [ ] No orphaned words on their own line

COLOR & CONTRAST
├── [ ] Text meets WCAG AA contrast (4.5:1)
├── [ ] Interactive elements visually distinct
├── [ ] Active/selected states clear
├── [ ] Error states use red/warning colors
└── [ ] No raw hex in components (design tokens only)

COMPONENTS
├── [ ] All buttons have hover/active states
├── [ ] All inputs have focus rings
├── [ ] All cards have consistent styling
├── [ ] Icons render (not □ or missing)
├── [ ] Charts/graphs render with data
└── [ ] Tables are scrollable if wide

NRG-SPECIFIC
├── [ ] Tier badge visible (T1/T2/T3)
├── [ ] Confidence badge on answers
├── [ ] Audit ID visible on query results
├── [ ] Citation drawer opens
├── [ ] HMAC proof panel accessible
├── [ ] Consent banner for T2/T3
└── [ ] No forbidden vocabulary on any screen

EMBARRASSMENT GUARD
├── [ ] No "Lorem ipsum" or placeholder text
├── [ ] No "TODO", "FIXME", "test" visible to user
├── [ ] No console.log artifacts visible
├── [ ] No debug panels or dev tools visible
├── [ ] No broken images (no alt text showing)
├── [ ] No "undefined", "null", "NaN" displayed
├── [ ] No raw JSON in the UI
└── [ ] No English grammar errors in visible text
```

### Step 4: BEFORE/AFTER COMPARISON

If this is a post-change audit:

1. Capture current screenshots (AFTER)
2. Compare against baseline screenshots (BEFORE) from `evidence/<previous-date>/ui_audit/`
3. Flag any visual regressions: layout shifts, missing components, broken styling
4. Classify regressions:
   - **P0 REGRESSION** — Something that worked before is now broken
   - **P1 REGRESSION** — Something looks worse than before
   - **IMPROVEMENT** — Something looks better (from MVP merge, etc.)

### Step 5: AUTOMATED CHECKS

Run these commands:

```bash
# Frontend build (must pass)
cd frontend && npm run build

# Lint (must pass)
cd frontend && npm run lint

# Check for forbidden vocabulary in components
grep -rn "demo\|prototype\|MVP\|pitch" frontend/src/components/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v ".test."

# Check for embarrassing strings
grep -rn "TODO\|FIXME\|lorem\|placeholder\|test123\|undefined\|console.log" frontend/src/components/ --include="*.tsx" | grep -v node_modules | grep -v ".test."

# Check for raw hex colors
grep -rn "#[0-9a-fA-F]\{3,6\}" frontend/src/components/ --include="*.tsx" | grep -v node_modules | grep -v ".test." | grep -v "tailwind\|theme\|token"

# Check for stack trace patterns
grep -rn "<pre>\|Traceback\|Error:\|at Object\.\|at Module\." frontend/src/components/ --include="*.tsx" | grep -v node_modules | grep -v ErrorBoundary

# Accessibility check (if axe-core available)
# npx axe-cli http://localhost:3000 --exit
```

### Step 6: PRODUCE AUDIT REPORT

```markdown
## Live UI Audit Report — [Date]

### Summary
| Metric | Count |
|--------|-------|
| Screens audited | X |
| States checked | X |
| Issues found | X |
| P0 (must fix now) | X |
| P1 (fix before showing) | X |
| P2 (improvement opportunity) | X |

### Screen-by-Screen Results

#### Login (/login)
| Check | Status | Notes |
|-------|--------|-------|
| Layout | ✅/❌ | ... |
| Typography | ✅/❌ | ... |
| Mobile | ✅/❌ | ... |
| Screenshot | [path] | |

#### Dashboard — T1 (/app/dashboard)
| Check | Status | Notes |
|-------|--------|-------|
| ... | ... | ... |

[repeat for every screen]

### Issues Found
| ID | Screen | Severity | Description | Fix |
|----|--------|----------|-------------|-----|
| UI-001 | Dashboard | P0 | Hero counter shows "undefined" | Wire to display_metadata.yaml |
| UI-002 | Login | P1 | Submit button too small on mobile | Increase touch target to 44px |
| ... | ... | ... | ... | ... |

### Regressions (if post-change)
| Screen | What Changed | Was | Now | Verdict |
|--------|-------------|-----|-----|---------|
| ... | ... | ... | ... | REGRESSION/IMPROVEMENT |

### Automated Check Results
- [ ] `npm run build` — PASS/FAIL
- [ ] `npm run lint` — PASS/FAIL
- [ ] Forbidden vocabulary — CLEAN/[count] violations
- [ ] Embarrassing strings — CLEAN/[count] found
- [ ] Raw hex colors — CLEAN/[count] found
- [ ] Stack trace patterns — CLEAN/[count] found
```

### Evidence

Save screenshots and report to:
```
evidence/<date>/ui_audit/
├── screenshots/
│   ├── login_desktop.png
│   ├── login_mobile.png
│   ├── dashboard_t1_desktop.png
│   ├── dashboard_t1_mobile.png
│   ├── dashboard_t2_desktop.png
│   ├── dashboard_t3_desktop.png
│   ├── query_desktop.png
│   ├── query_mobile.png
│   ├── results_desktop.png
│   ├── results_mobile.png
│   ├── empty_state_*.png
│   └── error_state_*.png
├── UI_AUDIT_REPORT.md
└── automated_checks.log
```

---

## Agent Assignment Template

```
═══ LIVE UI AUDIT ═══

Read .claude/skills/live-ui-audit/SKILL.md
Server: [localhost:3000 or URL]
Context: [post-MVP-merge / pre-showing / routine]

Execute full visual audit:
1. Enumerate all screens from App.tsx
2. Capture all states (loaded, empty, loading, error, mobile)
3. Run visual checklist per screen
4. Run automated checks
5. Produce audit report with screenshots

Skills: live-ui-audit, webapp-testing, frontend-react-best-practices
Save evidence to: evidence/<date>/ui_audit/
```
