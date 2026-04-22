export const colors = {
  saffron: {
    50: '#fff7ed',
    100: '#ffedd5',
    200: '#fed7aa',
    300: '#fdba74',
    400: '#ff8b4a',
    500: '#ff6b35',
    600: '#e85a1c',
    700: '#c44a14',
    800: '#9a3810',
    900: '#7c2d12',
  },
  navy: {
    50: '#e8edf5',
    100: '#c5d1e5',
    200: '#8fa5cc',
    300: '#5979b3',
    400: '#234d99',
    500: '#1a2744',
    600: '#15213c',
    700: '#101a34',
    800: '#0b1428',
    900: '#060e1c',
  },
  gold: {
    400: '#d4a857',
    500: '#c49538',
    600: '#a77c2c',
  },
  success: {
    50: '#f0fdf4',
    500: '#22c55e',
    600: '#16a34a',
  },
  warning: {
    50: '#fffbeb',
    500: '#f59e0b',
    600: '#d97706',
  },
  error: {
    50: '#fef2f2',
    500: '#ef4444',
    600: '#dc2626',
  },
  white: '#ffffff',
  black: '#000000',
} as const

export type ColorToken = typeof colors
export type SaffronShade = keyof typeof colors.saffron
export type NavyShade = keyof typeof colors.navy
