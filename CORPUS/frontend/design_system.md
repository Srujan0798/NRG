# NRG Design System

## Overview

Custom design system built on Tailwind CSS. Theme-aware, accessible, responsive.

## Theme Provider

`frontend/src/design-system/ThemeProvider.tsx`

- Light/dark mode support
- CSS custom properties for colors, spacing, typography
- System preference detection + manual toggle

## Design Tokens

### Colors
- Primary: brand color for CTAs, links
- Secondary: muted actions
- Success: positive states
- Warning: caution states
- Error: failure states
- Background: page and card backgrounds
- Surface: elevated surfaces
- Text: primary, secondary, muted text colors

### Typography
- Font family: system sans-serif stack
- Sizes: xs, sm, base, lg, xl, 2xl, 3xl, 4xl
- Weights: normal, medium, semibold, bold

### Spacing
- Based on 4px grid (Tailwind default)
- Component padding: 16px, 24px
- Card padding: 20px
- Section gaps: 32px, 48px

### Border Radius
- Small: 4px (inputs, badges)
- Medium: 8px (cards, buttons)
- Large: 12px (modals, drawers)
- Full: 9999px (pills, avatars)

## Components

### Layout
- `SkeletonLoader` — loading placeholder
- `ErrorBoundary` — error catching
- `SkipLink` — accessibility skip navigation
- `NetworkStatusBanner` — offline indicator

### Forms
- `Login` — authentication form
- Input fields with validation states

### Data Display
- Dashboard cards
- Tables with sorting
- Charts (if applicable)

### Feedback
- Toast notifications
- Modal dialogs
- Drawer panels (citations, source data, audit proof)

## Accessibility

- WCAG 2.1 AA target
- Keyboard navigation
- Screen reader support
- Focus indicators
- Reduced motion support (`useReducedMotion`)
- Color contrast compliance

## Responsive Breakpoints

- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

Dashboards adapt layout per breakpoint.
