import React, { createContext, startTransition, useContext, useEffect, useState } from 'react'
import { AuthSession, AuthUser, authService } from '../services/authService'

interface AuthContextType {
  user: AuthUser | null
  session: AuthSession | null
  isLoading: boolean
  loginError: string | null
  backendAvailable: boolean
  login: (username: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
  refreshSession: () => Promise<AuthSession | null>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<AuthSession | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loginError, setLoginError] = useState<string | null>(null)
  const [backendAvailable, setBackendAvailable] = useState(true)
  const [_consecutiveFailures, setConsecutiveFailures] = useState(0)

  useEffect(() => {
    const storedSession = authService.getStoredSession()

    startTransition(() => {
      setSession(storedSession)
      setIsLoading(false)
    })
  }, [])

  useEffect(() => {
    let mounted = true

    const checkBackend = async () => {
      if (!mounted) return

      try {
        const res = await fetch('/health', { signal: AbortSignal.timeout(10000) })
        if (!mounted) return

        if (res.ok) {
          setConsecutiveFailures(0)
          setBackendAvailable(true)
        } else {
          setConsecutiveFailures(prev => {
            const next = prev + 1
            if (next >= 3) setBackendAvailable(false)
            return next
          })
        }
      } catch {
        if (!mounted) return
        setConsecutiveFailures(prev => {
          const next = prev + 1
          if (next >= 3) setBackendAvailable(false)
          return next
        })
      }
    }

    checkBackend()
    const interval = setInterval(checkBackend, 15000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  const login = async (username: string, password: string): Promise<boolean> => {
    setLoginError(null)

    try {
      const nextSession = await authService.login(username, password)
      startTransition(() => {
        setSession(nextSession)
      })
      return true
    } catch (error: any) {
      const status = error?.response?.status
      const detail = error?.response?.data?.detail
      const message = status === 401
        ? 'Invalid username or password'
        : status === 429
          ? 'Too many login attempts. Please wait a moment and try again.'
          : detail || 'Unable to sign in. Please check the API server and try again.'
      setLoginError(message)
      return false
    }
  }

  const logout = async (): Promise<void> => {
    await authService.logout(session)
    startTransition(() => {
      setSession(null)
      setLoginError(null)
    })
  }

  const refreshSession = async (): Promise<AuthSession | null> => {
    try {
      const nextSession = await authService.refreshSession(session?.refreshToken)
      startTransition(() => {
        setSession(nextSession)
      })
      return nextSession
    } catch (_error) {
      await logout()
      return null
    }
  }

  const value: AuthContextType = {
    user: session?.user ?? null,
    session,
    isLoading,
    loginError,
    backendAvailable,
    login,
    logout,
    refreshSession
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
