# POINTER: Design System

> **Do not trust this file as the source of truth.** Read the actual files listed below and verify against `Core_Idea_Clean.md` UX requirements.

## Where to Read

| Topic | Actual Source Files | What to Verify |
|-------|--------------------|----------------|
| **Theme** | `frontend/src/design-system/ThemeProvider.tsx` | Light/dark mode, system preference |
| **Styles** | `frontend/src/index.css`, `frontend/src/styles/` | Tailwind, design tokens |
| **Components** | `frontend/src/components/` | Reusable UI components |
| **Accessibility** | `frontend/src/components/SkipLink/`, `frontend/src/hooks/useReducedMotion.ts` | WCAG 2.1 AA |

## Verification Commands

```bash
# Check design system
ls frontend/src/design-system/

# Check styles
cat frontend/tailwind.config.js 2>/dev/null || echo "Check vite config for tailwind"

# Check components
ls frontend/src/components/ | head -20

# Check accessibility components
ls frontend/src/components/SkipLink/ frontend/src/components/ErrorBoundary/

# Check reduced motion hook
ls frontend/src/hooks/useReducedMotion.ts
```

## Requirements to Verify Against

From `Core_Idea_Clean.md`:
- Visible-experience rule: no stack traces, no undefined, no blank skeleton > 200ms
- Accessibility: keyboard navigation, screen reader support, focus indicators

**Read the actual source files. Do not trust this pointer.**
