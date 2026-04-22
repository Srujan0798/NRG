export const spacing = {
  0: '0',
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
  lg: '16px',
  xl: '24px',
  full: '9999px',
} as const

export const shadows = {
  sm: '0 1px 2px rgba(26, 39, 68, 0.06)',
  md: '0 4px 12px rgba(26, 39, 68, 0.08)',
  lg: '0 8px 32px rgba(26, 39, 68, 0.12)',
  xl: '0 16px 48px rgba(26, 39, 68, 0.16)',
  glow: '0 0 20px rgba(255, 107, 53, 0.3)',
} as const

export const transitions = {
  fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
  base: '250ms cubic-bezier(0.4, 0, 0.2, 1)',
  spring: '400ms cubic-bezier(0.16, 1, 0.3, 1)',
  slow: '500ms cubic-bezier(0.4, 0, 0.2, 1)',
} as const

export type SpacingToken = typeof spacing
export type BorderRadiusToken = typeof borderRadius
export type ShadowToken = typeof shadows
export type TransitionToken = typeof transitions
