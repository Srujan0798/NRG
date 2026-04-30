import React, { lazy, Suspense, useEffect } from 'react'
import Login from './components/Login'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { SkeletonLoader } from './components/Skeleton/SkeletonLoader'
import { ErrorBoundary } from './components/ErrorBoundary/ErrorBoundary'
import { useTheme } from './design-system/ThemeProvider'
import SkipLink from './components/SkipLink/SkipLink'
import { useReducedMotion } from './hooks/useReducedMotion'
import { trackFirstPaint } from './lib/telemetry'
import NetworkStatusBanner from './components/NetworkStatusBanner'
import { authService, type PersonaRole } from './services/authService'
import {
  AnswerEngineAnswer,
  AnswerEngineAudit,
  AnswerEngineDashboard,
  AnswerEngineHome,
  AnswerEngineLogin,
} from './views/AnswerEngine'

const ResearcherDashboard = lazy(() => import('./views/ResearcherDashboard'))
const GovernmentDashboard = lazy(() => import('./views/GovernmentDashboard'))
const IndustryDashboard = lazy(() => import('./views/IndustryDashboard'))
const FounderDashboard = lazy(() => import('./views/FounderDashboard'))
const AuditEvent = lazy(() => import('./pages/AuditEvent'))
const ProductionWorkspace = lazy(() => import('./pages/ProductionWorkspace'))

const ROLE_TIER: Record<PersonaRole, number> = {
  researcher: 1,
  government: 2,
  industry: 3,
}

const ROLE_DASHBOARD: Record<PersonaRole, string> = {
  researcher: '/app/researcher',
  government: '/app/government',
  industry: '/app/industry',
}

const LOGIN_ROLE_BY_USERNAME: Record<string, PersonaRole> = {
  'researcher@iitgn.ac.in': 'researcher',
  'ministry@nrg.gov.in': 'government',
  'partner@industry.in': 'industry',
}

const isBlockedPrompt = (query: string) => /\b(aadhaar|pan|passport|bank account|gstin|email|phone)\b/i.test(query)

const consumeInitialPathname = () => {
  const currentPath = window.location.pathname
  const bootQuery = window.__nrgBootSubmit ? window.__nrgBootQuery?.trim() : ''

  if (!bootQuery) return currentPath

  sessionStorage.setItem('nrg.lastQuery', bootQuery)
  const nextPath = isBlockedPrompt(bootQuery) ? '/app/answer/blocked' : '/app/answer/latest'
  if (nextPath === '/app/answer/blocked') {
    sessionStorage.setItem('nrg.blockedQuery', bootQuery)
  } else {
    sessionStorage.removeItem('nrg.blockedQuery')
  }

  window.__nrgBootSubmit = false
  if (currentPath !== nextPath) {
    window.history.replaceState({}, '', nextPath)
  }
  return nextPath
}

const DashboardLoading = () => (
  <div className="nrg-app-canvas min-h-screen">
    <header className="bg-[var(--glass-bg)] border-b border-nrg-border sticky top-0 z-40 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-saffron-500 to-saffron-600 flex items-center justify-center shadow-lg">
            <span className="text-white font-display text-lg">न</span>
          </div>
          <div>
            <h2 className="text-base font-bold text-nrg-text font-devanagari">राष्ट्रीय गवेषण मंच</h2>
            <p className="text-xs uppercase tracking-[0.16em] text-nrg-muted">National Research Intelligence Platform</p>
          </div>
        </div>
      </div>
    </header>
    <main id="main-content" tabIndex={-1} className="max-w-7xl mx-auto px-4 py-8 relative z-10">
      <SkeletonLoader type="stats" />
    </main>
  </div>
)

const AppShell: React.FC = () => {
  const { isLoading, login, loginError, user, backendAvailable } = useAuth()
  const { themeName, toggleTheme } = useTheme()

  if (isLoading) {
    return (
      <div className="nrg-app-canvas flex min-h-screen items-center justify-center text-white">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-3 border-saffron-200 border-t-saffron-500 animate-spin" />
          <p className="text-sm tracking-[0.25em] text-saffron-600 dark:text-saffron-300 uppercase">Loading Secure Session</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Login onLogin={login} error={loginError} backendAvailable={backendAvailable} />
  }

  return (
    <div className="nrg-app-canvas min-h-screen transition-colors duration-300">
      {user.role === 'government' && (
        <ErrorBoundary title="Government Dashboard Error">
          <Suspense fallback={<DashboardLoading />}>
            <GovernmentDashboard onThemeToggle={toggleTheme} theme={themeName} />
          </Suspense>
        </ErrorBoundary>
      )}
      {user.role === 'industry' && (
        <ErrorBoundary title="Industry Dashboard Error">
          <Suspense fallback={<DashboardLoading />}>
            <IndustryDashboard onThemeToggle={toggleTheme} theme={themeName} />
          </Suspense>
        </ErrorBoundary>
      )}
      {user.role === 'researcher' && (
        <ErrorBoundary title="Researcher Dashboard Error">
          <Suspense fallback={<DashboardLoading />}>
            <ResearcherDashboard onThemeToggle={toggleTheme} theme={themeName} />
          </Suspense>
        </ErrorBoundary>
      )}
    </div>
  )
}

const AuthenticatedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isLoading, login, loginError, user, backendAvailable } = useAuth()

  if (isLoading) return <DashboardLoading />

  if (!user) {
    return <Login onLogin={login} error={loginError} backendAvailable={backendAvailable} />
  }

  return <>{children}</>
}

interface AnswerEngineRouteProps {
  routeRole?: PersonaRole
  loginFirst?: boolean
  onNavigate: (path: string, mode?: 'push' | 'replace') => void
  children: (props: {
    role: PersonaRole
    tier: number
    username: string
    onLogout: () => void
    onPersonaChange: (role: PersonaRole) => void
    onNavigate: (path: string) => void
    onQuerySubmit: (query: string) => void
  }) => React.ReactNode
}

const AnswerEngineRoute: React.FC<AnswerEngineRouteProps> = ({ routeRole, loginFirst = false, onNavigate, children }) => {
  const { isLoading, login, loginError, user, backendAvailable, logout } = useAuth()

  const handleLogin = async (username: string, password: string) => {
    const ok = await login(username, password)
    if (!ok) return false

    const storedRole = authService.getStoredSession()?.user.role
    const nextRole = storedRole || LOGIN_ROLE_BY_USERNAME[username] || 'researcher'
    onNavigate(ROLE_DASHBOARD[nextRole], 'replace')
    return true
  }

  if (loginFirst && isLoading) {
    return (
      <AnswerEngineLogin
        onLogin={handleLogin}
        error={loginError}
        backendAvailable={backendAvailable}
      />
    )
  }

  if (isLoading) return <DashboardLoading />

  if (!user) {
    return (
      <AnswerEngineLogin
        onLogin={handleLogin}
        error={loginError}
        backendAvailable={backendAvailable}
      />
    )
  }

  const role = routeRole || user.role
  const tier = ROLE_TIER[role]

  const handleLogout = async () => {
    await logout()
    onNavigate('/login', 'replace')
  }

  const handlePersonaChange = (nextRole: PersonaRole) => {
    onNavigate(ROLE_DASHBOARD[nextRole])
  }

  const handleQuerySubmit = (query: string) => {
    const trimmed = query.trim()
    if (!trimmed) return

    sessionStorage.setItem('nrg.lastQuery', trimmed)
    if (isBlockedPrompt(trimmed)) {
      sessionStorage.setItem('nrg.blockedQuery', trimmed)
      onNavigate('/app/answer/blocked')
      return
    }
    sessionStorage.removeItem('nrg.blockedQuery')
    onNavigate('/app/answer/latest')
  }

  return (
    <>
      {children({
        role,
        tier,
        username: user.username,
        onLogout: handleLogout,
        onPersonaChange: handlePersonaChange,
        onNavigate,
        onQuerySubmit: handleQuerySubmit,
      })}
    </>
  )
}

const App: React.FC = () => {
  const reducedMotion = useReducedMotion()
  const [pathname, setPathname] = React.useState(consumeInitialPathname)

  const navigate = React.useCallback((path: string, mode: 'push' | 'replace' = 'push') => {
    if (window.location.pathname !== path) {
      if (mode === 'replace') {
        window.history.replaceState({}, '', path)
      } else {
        window.history.pushState({}, '', path)
      }
    }
    setPathname(path)
  }, [])

  useEffect(() => {
    const handlePopState = () => setPathname(window.location.pathname)
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  useEffect(() => {
    document.documentElement.dataset.reducedMotion = reducedMotion ? 'true' : 'false'
  }, [reducedMotion])

  useEffect(() => {
    trackFirstPaint()
  }, [])

  useEffect(() => {
    if (pathname === '/login') document.title = 'NRG · Sign in'
    if (pathname === '/app') document.title = 'NRG · Ask National Research Graph'
    if (pathname === '/app/researcher') document.title = 'NRG · Researcher Answer Engine'
    if (pathname === '/app/government') document.title = 'NRG · Government Answer Engine'
    if (pathname === '/app/answer/latest') document.title = 'NRG · Answer'
    if (pathname === '/app/answer/blocked') document.title = 'NRG · Prompt Blocked'
    if (pathname === '/app/publications') document.title = 'NRG · Publications Explorer'
    if (pathname === '/app/researchers') document.title = 'NRG · Researcher Profiles'
    if (pathname === '/app/reports') document.title = 'NRG · Government Reports'
    if (pathname === '/app/industry') document.title = 'NRG · Industry Answer Engine'
    if (pathname === '/app/settings') document.title = 'NRG · Settings and Audit'
    if (pathname === '/founder') document.title = 'NRG · Founder Readiness'
    if (pathname === '/app/audit') document.title = 'NRG · Audit Trail'
    if (pathname.startsWith('/app/audit/event/')) document.title = 'NRG · Audit Event'
  }, [pathname])

  let content: React.ReactNode

  if (pathname === '/founder') {
    content = (
      <Suspense fallback={<DashboardLoading />}>
        <FounderDashboard />
      </Suspense>
    )
  } else if (pathname === '/login') {
    content = (
      <AnswerEngineRoute loginFirst onNavigate={navigate}>
        {() => null}
      </AnswerEngineRoute>
    )
  } else if (pathname.startsWith('/app/audit/event/')) {
    content = (
      <AuthenticatedRoute>
        <Suspense fallback={<DashboardLoading />}>
          <AuditEvent />
        </Suspense>
      </AuthenticatedRoute>
    )
  } else if (pathname === '/app/audit') {
    content = (
      <AnswerEngineRoute onNavigate={navigate}>
        {(props) => <AnswerEngineAudit {...props} />}
      </AnswerEngineRoute>
    )
  } else if (pathname === '/app') {
    content = (
      <AnswerEngineRoute onNavigate={navigate}>
        {(props) => <AnswerEngineHome {...props} />}
      </AnswerEngineRoute>
    )
  } else if (pathname === '/app/researcher') {
    content = (
      <AnswerEngineRoute routeRole="researcher" onNavigate={navigate}>
        {(props) => <AnswerEngineDashboard {...props} />}
      </AnswerEngineRoute>
    )
  } else if (pathname === '/app/government') {
    content = (
      <AnswerEngineRoute routeRole="government" onNavigate={navigate}>
        {(props) => <AnswerEngineDashboard {...props} />}
      </AnswerEngineRoute>
    )
  } else if (pathname === '/app/industry') {
    content = (
      <AnswerEngineRoute routeRole="industry" onNavigate={navigate}>
        {(props) => <AnswerEngineDashboard {...props} />}
      </AnswerEngineRoute>
    )
  } else if (pathname === '/app/answer/latest' || pathname === '/app/answer/blocked') {
    content = (
      <AnswerEngineRoute onNavigate={navigate}>
        {(props) => <AnswerEngineAnswer {...props} />}
      </AnswerEngineRoute>
    )
  } else if (pathname === '/app/publications') {
    content = (
      <AuthenticatedRoute>
        <Suspense fallback={<DashboardLoading />}>
          <ProductionWorkspace screen="publications" />
        </Suspense>
      </AuthenticatedRoute>
    )
  } else if (pathname === '/app/researchers') {
    content = (
      <AuthenticatedRoute>
        <Suspense fallback={<DashboardLoading />}>
          <ProductionWorkspace screen="researchers" />
        </Suspense>
      </AuthenticatedRoute>
    )
  } else if (pathname === '/app/reports') {
    content = (
      <AuthenticatedRoute>
        <Suspense fallback={<DashboardLoading />}>
          <ProductionWorkspace screen="reports" />
        </Suspense>
      </AuthenticatedRoute>
    )
  } else if (pathname === '/app/settings') {
    content = (
      <AuthenticatedRoute>
        <Suspense fallback={<DashboardLoading />}>
          <ProductionWorkspace screen="settings" />
        </Suspense>
      </AuthenticatedRoute>
    )
  } else {
    content = (
      <AppShell />
    )
  }

  return (
    <AuthProvider>
      <SkipLink />
      <NetworkStatusBanner />
      <div data-reduced-motion={reducedMotion ? 'true' : 'false'}>
        <ErrorBoundary title="NRG could not render this page">
          {content}
        </ErrorBoundary>
      </div>
    </AuthProvider>
  )
}

export default App
export { AppShell }
