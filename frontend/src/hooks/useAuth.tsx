import React, { createContext, startTransition, useContext, useEffect, useState } from 'react'
import { AuthSession, AuthUser, authService } from '../services/authService'

interface AuthContextType {
  user: AuthUser | null
  session: AuthSession | null
  isLoading: boolean
  loginError: string | null
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

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<AuthSession | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loginError, setLoginError] = useState<string | null>(null)

  useEffect(() => {
    const storedSession = authService.getStoredSession()

    startTransition(() => {
      setSession(storedSession)
      setIsLoading(false)
    })
  }, [])

  const login = async (username: string, password: string): Promise<boolean> => {
    setLoginError(null)

    try {
      const nextSession = await authService.login(username, password)
      startTransition(() => {
        setSession(nextSession)
      })
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed'
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
