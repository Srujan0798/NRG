# Frontend Design Evidence — NRG Component Redesign

**Skill**: frontend-design
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/31_FRONTEND_DESIGN.md`

---

## Frontend Design: NRG — A Bold Direction

### Design Philosophy

The NRG "National Research Intelligence" platform deserves a visual identity that reflects the **gravity and scale of India's research ecosystem**. Currently it looks like a generic SaaS dashboard. The proposed redesign draws from:

- **Editorial/magazine aesthetics** — Think Nature or Science journals meets modern data viz
- **Brutalist data presentation** — Bold typography, high contrast, unapologetic about showing data
- **Warm earth tones** — India-inspired palette moving away from cold corporate blues

---

## Component Redesign: ResearchMetricsCard

A redesigned metrics card that replaces the generic `StatsCard` with something memorable.

### Current Implementation (StatsCard.tsx)
```tsx
// Current — generic, forgettable
<div className="bg-white rounded-lg shadow-sm p-6">
  <p className="text-sm text-gray-500">Publications</p>
  <p className="text-3xl font-bold text-gray-900">12,847</p>
  <p className="text-sm text-green-600">+23%</p>
</div>
```

### Redesigned Implementation

```tsx
// evidence/components/ResearchMetricsCard.tsx
import React from 'react';

interface ResearchMetricsCardProps {
  label: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
  accent: string;
  icon: React.ReactNode;
}

const COLORS = {
  indigo: { bg: '#1e1b4b', accent: '#6366f1', text: '#e0e7ff' },
  emerald: { bg: '#064e3b', accent: '#10b981', text: '#d1fae5' },
  amber: { bg: '#451a03', accent: '#f59e0b', text: '#fef3c7' },
};

export function ResearchMetricsCard({
  label,
  value,
  change,
  accent = 'indigo',
  icon,
}: ResearchMetricsCardProps) {
  const colors = COLORS[accent as keyof typeof COLORS] || COLORS.indigo;
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;

  return (
    <div
      className="relative overflow-hidden rounded-2xl p-6 transition-all duration-300 hover:scale-[1.02] hover:shadow-xl cursor-pointer group"
      style={{ backgroundColor: colors.bg }}
    >
      {/* Decorative geometric element */}
      <div
        className="absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-20 blur-2xl transition-opacity duration-300 group-hover:opacity-30"
        style={{ backgroundColor: colors.accent }}
      />

      {/* Diagonal stripe texture */}
      <div
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: `repeating-linear-gradient(
            45deg,
            transparent,
            transparent 10px,
            ${colors.accent} 10px,
            ${colors.accent} 11px
          )`,
        }}
      />

      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <span
            className="text-xs font-semibold tracking-widest uppercase"
            style={{ color: colors.text, opacity: 0.7 }}
          >
            {label}
          </span>
          <div
            className="p-2 rounded-xl transition-transform duration-200 group-hover:scale-110"
            style={{ backgroundColor: colors.accent, color: colors.bg }}
          >
            {icon}
          </div>
        </div>

        <div className="flex items-end gap-3">
          <span
            className="text-5xl font-black tracking-tight"
            style={{ color: '#ffffff' }}
          >
            {typeof value === 'number' ? value.toLocaleString() : value}
          </span>
        </div>

        {change !== undefined && (
          <div className="mt-4 flex items-center gap-2">
            <span
              className={`inline-flex items-center gap-1 text-sm font-semibold px-2 py-1 rounded-lg ${
                isPositive
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : isNegative
                  ? 'bg-red-500/20 text-red-400'
                  : 'bg-gray-500/20 text-gray-400'
              }`}
            >
              {isPositive && (
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 15l7-7 7 7" />
                </svg>
              )}
              {isNegative && (
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M19 9l-7 7-7-7" />
                </svg>
              )}
              {Math.abs(change)}%
            </span>
            <span style={{ color: colors.text, opacity: 0.5 }} className="text-xs">
              vs last quarter
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
```

### Usage Example

```tsx
// Example usage in ResearcherDashboard
<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
  <ResearchMetricsCard
    label="Publications"
    value={12847}
    change={23}
    accent="indigo"
    icon={<BookOpenIcon className="w-5 h-5" />}
  />
  <ResearchMetricsCard
    label="Researchers"
    value={8432}
    change={12}
    accent="emerald"
    icon={<UserGroupIcon className="w-5 h-5" />}
  />
  <ResearchMetricsCard
    label="Citations"
    value={98421}
    change={-3}
    accent="amber"
    icon={<SparklesIcon className="w-5 h-5" />}
  />
</div>
```

### Design Choices

| Choice | Rationale |
|---------|-----------|
| Dark background (`#1e1b4b`) | Editorial gravitas, distinguishes from generic dashboards |
| Giant number (5xl font) | Data should feel important, not cramped |
| Geometric decoration | Adds visual interest without being distracting |
| Hover scale + shadow | Micro-interaction feedback on interaction |
| Color-coded accents | Each metric type has its own identity |
| Trend indicator with arrows | At-a-glance direction without parsing numbers |

---

## Typography Upgrade

**Current**: System fonts (detectably Arial)
**Proposed**: "Instrument Serif" for headings + "DM Sans" for body

```tsx
// Add to index.css or App.tsx
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@400;500;600;700&display=swap');

export function App() {
  return (
    <style>
      {`
        h1, h2, h3, h4 {
          font-family: 'Instrument Serif', Georgia, serif;
        }
        body, p, span, button, input {
          font-family: 'DM Sans', system-ui, sans-serif;
        }
      `}
    </style>
  );
}
```

---

## Color Palette (India-Inspired)

| Name | Hex | Usage |
|------|-----|-------|
| Midnight Indigo | `#1e1b4b` | Card backgrounds, header |
| Saffron | `#f59e0b` | Industry tier, alerts |
| Emerald | `#10b981` | Government tier, positive trends |
| Deep Blue | `#3b82f6` | Researcher tier, links |
| Warm Gray | `#f5f5f4` | Page background |
| Charcoal | `#1c1917` | Primary text |

---

## Skill Deliverable

**Status**: COMPLETED

Bold redesign direction for NRG frontend:
1. **ResearchMetricsCard** component — Editorial dark-card aesthetic with giant numbers, decorative geometry, and micro-interactions
2. **Typography** — "Instrument Serif" + "DM Sans" pairing for gravitas
3. **Color palette** — India-inspired palette moving away from generic Tailwind blues
4. **Design principles** — Data should feel important, not cramped; micro-interactions for feedback
