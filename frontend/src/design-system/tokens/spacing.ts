export const spacing = {
  0: '0',
  px4: '4px',
  px8: '8px',
  px12: '12px',
  px16: '16px',
  px24: '24px',
  px32: '32px',
  px48: '48px',
  px64: '64px',
  px96: '96px',
  px128: '128px',
  1: '0.25rem',
  2: '0.5rem',
  3: '0.75rem',
  4: '1rem',
  5: '1.25rem',
  6: '1.5rem',
  8: '2rem',
  10: '2.5rem',
  12: '3rem',
  16: '4rem',
  20: '5rem',
  24: '6rem',
  32: '8rem',
} as const

export const borderRadius = {
  none: '0',
  sm: '6px',
  md: '12px',
  lg: '18px',
  xl: '18px',
  full: '9999px',
} as const

export const shadows = {
  none: 'none',
  sm: '0 1px 2px rgba(15,23,42,0.06), 0 1px 1px rgba(15,23,42,0.04)',
  md: '0 4px 8px rgba(15,23,42,0.08), 0 2px 4px rgba(15,23,42,0.04)',
  lg: '0 16px 40px rgba(15,23,42,0.16), 0 4px 12px rgba(15,23,42,0.08)',
  glow: '0 0 20px rgba(255, 153, 51, 0.3)',
} as const

export const transitions = {
  snappy: '120ms cubic-bezier(0.2, 0, 0, 1)',
  smooth: '240ms cubic-bezier(0.32, 0.72, 0, 1)',
  lazy: '480ms cubic-bezier(0.22, 1, 0.36, 1)',
  fast: '120ms cubic-bezier(0.2, 0, 0, 1)',
  base: '240ms cubic-bezier(0.32, 0.72, 0, 1)',
  spring: '240ms cubic-bezier(0.32, 0.72, 0, 1)',
  slow: '480ms cubic-bezier(0.22, 1, 0.36, 1)',
} as const

export type SpacingToken = typeof spacing
export type BorderRadiusToken = typeof borderRadius
export type ShadowToken = typeof shadows
export type TransitionToken = typeof transitions
