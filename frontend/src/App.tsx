import React, { lazy, Suspense } from 'react'
import Login from './components/Login'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { SkeletonLoader } from './components/Skeleton'
import { ErrorBoundary } from './components/ErrorBoundary'
import { useTheme } from './design-system/ThemeProvider'

const ResearcherDashboard = lazy(() => import('./views/ResearcherDashboard'))
const GovernmentDashboard = lazy(() => import('./views/GovernmentDashboard'))
const IndustryDashboard = lazy(() => import('./views/IndustryDashboard'))
const FounderDashboard = lazy(() => import('./views/FounderDashboard'))

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
    <main className="max-w-7xl mx-auto px-4 py-8 relative z-10">
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

const App: React.FC = () => {
  if (window.location.pathname === '/founder') {
    return (
      <Suspense fallback={<DashboardLoading />}>
        <FounderDashboard />
      </Suspense>
    )
  }

  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  )
}

export default App
export { AppShell }
