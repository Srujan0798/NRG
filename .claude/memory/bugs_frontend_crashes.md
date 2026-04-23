---
name: Frontend Crash Patterns
description: Recurring frontend crash patterns found during recomposition audit — ThemeProvider missing, hooks in effects, string-vs-array API fields
type: project
---

Three bugs killed the frontend (2026-04-22):

1. **ThemeProvider missing from main.tsx** — App.tsx uses useTheme() but main.tsx didn't wrap with ThemeProvider. Result: blank white page.
   **Fix:** Added ThemeProvider wrapper in main.tsx around App component.

2. **useSpring hook called inside useEffect** (StatsCard.tsx:26) — Violates React Rules of Hooks. Result: "Invalid hook call" crash on dashboard.
   **Fix:** Removed dead useSpring call from inside useEffect.

3. **pub.authors is string, not array** — API returns "Author_1, Author_2" as string. Dashboard called .slice(0,2).join(', ') which crashes on strings.
   **Fix:** Added type check: string → split(',') first, array → use directly.

**Why:** Agents created components without testing the full render cycle. StatsCard was never rendered with real data.

**How to apply:** When agents create frontend components, require a Playwright screenshot test proving the component renders with real API data. Check any .join()/.slice()/.map() call against actual API response types.
