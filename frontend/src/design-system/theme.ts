import { colors } from './tokens/colors'
import { shadows } from './tokens/spacing'

export const lightTheme = {
  name: 'light',
  colors: {
    bg: colors.role.surface2.light,
    surface: colors.role.surface1.light,
    text: colors.role.ink.light,
    muted: colors.role.inkMuted.light,
    border: colors.role.border.light,
    shadow: 'rgba(26, 39, 68, 0.08)',
    saffron: colors.saffron,
    navy: colors.navy,
    gold: colors.gold,
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
  },
  glass: {
    bg: 'rgba(255, 255, 255, 0.82)',
    border: 'rgba(255, 255, 255, 0.5)',
    shadow: shadows.md,
    blur: '20px',
  },
}

export const darkTheme = {
  name: 'dark',
  colors: {
    bg: colors.role.surface1.dark,
    surface: colors.role.surface2.dark,
    text: colors.role.ink.dark,
    muted: colors.role.inkMuted.dark,
    border: colors.role.border.dark,
    shadow: 'rgba(0, 0, 0, 0.3)',
    saffron: colors.saffron,
    navy: colors.navy,
    gold: colors.gold,
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
  },
  glass: {
    bg: 'rgba(26, 39, 68, 0.7)',
    border: 'rgba(255, 255, 255, 0.06)',
    shadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
    blur: '20px',
  },
}

export type Theme = typeof lightTheme | typeof darkTheme

export const printDesignTokenCss = `
  :root {
    --nrg-saffron: ${colors.role.saffron.light};
    --nrg-saffron-soft: ${colors.saffron[400]};
    --nrg-white: ${colors.role.white.light};
    --nrg-ink: ${colors.role.ink.light};
    --nrg-ink-muted: ${colors.role.inkMuted.light};
    --nrg-surface-1: ${colors.role.surface1.light};
    --nrg-surface-2: ${colors.role.surface2.light};
    --nrg-border: ${colors.role.border.light};
    --nrg-chart-1: ${colors.role.saffron.light};
    --nrg-font-sans: 'Sohne Display', system-ui, sans-serif;
    --nrg-space-0: 1px;
    --nrg-space-1: 4px;
    --nrg-space-2: 8px;
    --nrg-space-3: 12px;
    --nrg-space-4: 16px;
    --nrg-space-5: 20px;
    --nrg-space-6: 24px;
    --nrg-space-7: 30px;
    --nrg-space-10: 40px;
    --nrg-space-12: 48px;
    --nrg-space-three-quarter: 3px;
    --nrg-export-width: 800px;
    --nrg-type-body-line: 24px;
    --nrg-type-body-size: 16px;
    --nrg-type-body-s-size: 14px;
    --nrg-type-caption-size: 12px;
    --nrg-type-caption-tight: 11px;
    --nrg-type-export-body: 13px;
  }
`
