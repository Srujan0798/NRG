import React, { createContext, startTransition, useContext, useEffect, useRef, useState } from 'react'
import { AuthSession, AuthUser, authService } from '../services/authService'
import { fetchWithTimeout } from '../utils/fetchWithTimeout'

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

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<AuthSession | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loginError, setLoginError] = useState<string | null>(null)
  const [backendAvailable, setBackendAvailable] = useState(true)
  const [_consecutiveFailures, setConsecutiveFailures] = useState(0)
  const authRevisionRef = useRef(0)

  useEffect(() => {
    let mounted = true
    const restoreRevision = authRevisionRef.current
    const restoreStillCurrent = () => mounted && authRevisionRef.current === restoreRevision

    const restoreSession = async () => {
      const storedSession = authService.getStoredSession()
      if (window.location.pathname === '/login' && !storedSession) {
        startTransition(() => {
          if (!restoreStillCurrent()) return
          setSession(null)
          setIsLoading(false)
        })
        return
      }

      if (storedSession) {
        startTransition(() => {
          if (!restoreStillCurrent()) return
          setSession(storedSession)
          setIsLoading(false)
        })
        return
      }

      try {
        const cookieSession = await authService.fetchSession()
        startTransition(() => {
          if (!restoreStillCurrent()) return
          setSession(cookieSession)
          setIsLoading(false)
        })
      } catch {
        startTransition(() => {
          if (!restoreStillCurrent()) return
          setSession(null)
          setIsLoading(false)
        })
      }
    }

    void restoreSession()
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    let mounted = true

    const checkBackend = async () => {
      if (!mounted) return

      try {
        const res = await fetchWithTimeout('/health/db', { timeoutMs: 5000 })
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
    authRevisionRef.current += 1
    setLoginError(null)

    try {
      const nextSession = await authService.login(username, password)
      startTransition(() => {
        setSession(nextSession)
        setIsLoading(false)
      })
      return true
    } catch (error: any) {
      const status = error?.response?.status
      const detail = error?.response?.data?.detail
      const message = status === 401
        ? 'Email or password is incorrect'
        : status === 429
          ? 'Too many login attempts. Please wait a moment and try again.'
          : detail || 'Unable to sign in. Please check the API server and try again.'
      setLoginError(message)
      setIsLoading(false)
      return false
    }
  }

  const logout = async (): Promise<void> => {
    authRevisionRef.current += 1
    await authService.logout(session)
    startTransition(() => {
      setSession(null)
      setLoginError(null)
      setIsLoading(false)
    })
  }

  const refreshSession = async (): Promise<AuthSession | null> => {
    try {
      const nextSession = await authService.refreshSession(session?.refreshToken)
      authRevisionRef.current += 1
      startTransition(() => {
        setSession(nextSession)
        setIsLoading(false)
      })
      return nextSession
    } catch {
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
