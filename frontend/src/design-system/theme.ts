import { colors } from './tokens/colors'

export const lightTheme = {
  name: 'light',
  colors: {
    bg: '#f7f9fc',
    surface: '#ffffff',
    text: '#0f172a',
    muted: '#64748b',
    border: '#e2e8f0',
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
    shadow: '0 8px 32px rgba(26, 39, 68, 0.06)',
    blur: '20px',
  },
}

export const darkTheme = {
  name: 'dark',
  colors: {
    bg: '#060e1c',
    surface: '#0f1729',
    text: '#f1f5f9',
    muted: '#94a3b8',
    border: 'rgba(255,255,255,0.08)',
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

export type Theme = typeof lightTheme
