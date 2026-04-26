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

const ResearcherDashboard = lazy(() => import('./views/ResearcherDashboard'))
const GovernmentDashboard = lazy(() => import('./views/GovernmentDashboard'))
const IndustryDashboard = lazy(() => import('./views/IndustryDashboard'))
const FounderDashboard = lazy(() => import('./views/FounderDashboard'))
const Hero = lazy(() => import('./views/Hero'))
const DPDPAudit = lazy(() => import('./pages/DPDP-Audit'))
const AuditEvent = lazy(() => import('./pages/AuditEvent'))

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

const App: React.FC = () => {
  const reducedMotion = useReducedMotion()
  const [pathname, setPathname] = React.useState(window.location.pathname)

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
    if (pathname === '/app') document.title = 'NRG · Ask National Research Graph'
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
  } else if (pathname.startsWith('/app/audit/event/')) {
    content = (
      <AuthProvider>
        <AuthenticatedRoute>
          <Suspense fallback={<DashboardLoading />}>
            <AuditEvent />
          </Suspense>
        </AuthenticatedRoute>
      </AuthProvider>
    )
  } else if (pathname === '/app/audit') {
    content = (
      <AuthProvider>
        <AuthenticatedRoute>
          <Suspense fallback={<DashboardLoading />}>
            <DPDPAudit />
          </Suspense>
        </AuthenticatedRoute>
      </AuthProvider>
    )
  } else if (pathname === '/app') {
    content = (
      <AuthProvider>
        <AuthenticatedRoute>
          <Suspense fallback={<DashboardLoading />}>
            <Hero />
          </Suspense>
        </AuthenticatedRoute>
      </AuthProvider>
    )
  } else {
    content = (
      <AuthProvider>
        <AppShell />
      </AuthProvider>
    )
  }

  return (
    <>
      <SkipLink />
      <NetworkStatusBanner />
      <div data-reduced-motion={reducedMotion ? 'true' : 'false'}>
        <ErrorBoundary title="NRG could not render this page">
          {content}
        </ErrorBoundary>
      </div>
    </>
  )
}

export default App
export { AppShell }
