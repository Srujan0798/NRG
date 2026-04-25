export const typography = {
  fontFamily: {
    sans: ['Sohne Display', 'system-ui', '-apple-system', 'sans-serif'],
    devanagari: ['Tiro Devanagari Hindi', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'Consolas', 'monospace'],
    display: ['Sohne Display', 'system-ui', 'sans-serif'],
  },
  roleScale: {
    display: { fontSize: '56px', lineHeight: '60px', fontWeight: '700' },
    h1: { fontSize: '40px', lineHeight: '48px', fontWeight: '700' },
    h2: { fontSize: '28px', lineHeight: '36px', fontWeight: '600' },
    h3: { fontSize: '20px', lineHeight: '28px', fontWeight: '600' },
    bodyL: { fontSize: '18px', lineHeight: '28px', fontWeight: '400' },
    body: { fontSize: '16px', lineHeight: '24px', fontWeight: '400' },
    bodyS: { fontSize: '14px', lineHeight: '20px', fontWeight: '400' },
    caption: { fontSize: '12px', lineHeight: '16px', fontWeight: '500', letterSpacing: '0.02em', textTransform: 'uppercase' },
    mono: { fontSize: '14px', lineHeight: '20px', fontWeight: '400' },
  },
  fontSize: {
    xs: ['0.75rem', { lineHeight: '1rem' }],
    sm: ['0.875rem', { lineHeight: '1.25rem' }],
    base: ['1rem', { lineHeight: '1.5rem' }],
    lg: ['1.125rem', { lineHeight: '1.75rem' }],
    xl: ['1.25rem', { lineHeight: '1.75rem' }],
    '2xl': ['1.5rem', { lineHeight: '2rem' }],
    '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
    '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
    '5xl': ['3rem', { lineHeight: '1.2' }],
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
  },
} as const

export type TypographyToken = typeof typography
