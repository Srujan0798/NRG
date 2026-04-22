import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { lightTheme, darkTheme, Theme } from './theme'

interface ThemeContextValue {
  theme: Theme
  themeName: 'light' | 'dark'
  toggleTheme: () => void
  setTheme: (name: 'light' | 'dark') => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [themeName, setThemeName] = useState<'light' | 'dark'>(() => {
    if (typeof window === 'undefined') return 'light'
    const stored = localStorage.getItem('nrg-theme') as 'light' | 'dark' | null
    if (stored) return stored
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  useEffect(() => {
    const root = document.documentElement
    if (themeName === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem('nrg-theme', themeName)
  }, [themeName])

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => {
      const stored = localStorage.getItem('nrg-theme')
      if (!stored) {
        setThemeName(e.matches ? 'dark' : 'light')
      }
    }
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  const toggleTheme = useCallback(() => {
    setThemeName(prev => prev === 'light' ? 'dark' : 'light')
  }, [])

  const setTheme = useCallback((name: 'light' | 'dark') => {
    setThemeName(name)
  }, [])

  const theme = themeName === 'dark' ? darkTheme : lightTheme

  return (
    <ThemeContext.Provider value={{ theme, themeName, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
