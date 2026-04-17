/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // IITGN Persona Accent Colors
        researcher: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
        },
        government: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        industry: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b',
        },
        sovereign: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
      },
      fontFamily: {
        devanagari: ['"Noto Sans Devanagari"', 'system-ui', 'sans-serif'],
      },
      animation: {
        'glass-shimmer': 'glass-shimmer 3s ease-in-out infinite',
        'tier-pulse': 'tier-pulse 2s ease-in-out infinite',
        'dpdp-glow': 'dpdp-glow 1.5s ease-in-out infinite',
      },
      keyframes: {
        'glass-shimmer': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        'tier-pulse': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.8', transform: 'scale(0.98)' },
        },
        'dpdp-glow': {
          '0%, 100%': { boxShadow: '0 0 4px rgba(245, 158, 11, 0.3)' },
          '50%': { boxShadow: '0 0 12px rgba(245, 158, 11, 0.6)' },
        },
      },
      backgroundImage: {
        'glass-gradient': 'linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))',
        'persona-researcher': 'linear-gradient(135deg, #eef2ff 0%, #c7d2fe 100%)',
        'persona-government': 'linear-gradient(135deg, #eff6ff 0%, #bfdbfe 100%)',
        'persona-industry': 'linear-gradient(135deg, #ecfdf5 0%, #a7f3d0 100%)',
      },
    },
  },
  plugins: [],
}
