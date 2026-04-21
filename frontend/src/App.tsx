import React, { lazy, Suspense } from 'react'
import Login from './components/Login'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { SkeletonLoader } from './components/Skeleton'
import { ErrorBoundary } from './components/ErrorBoundary'
import { useTheme } from './design-system/ThemeProvider'

const ResearcherDashboard = lazy(() => import('./views/ResearcherDashboard'))
const GovernmentDashboard = lazy(() => import('./views/GovernmentDashboard'))
const IndustryDashboard = lazy(() => import('./views/IndustryDashboard'))

const DashboardLoading = () => (
  <div className="min-h-screen bg-slate-50 dark:bg-navy-900">
    <header className="bg-white dark:bg-navy-800 border-b border-slate-200 dark:border-navy-700 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-saffron-500 to-saffron-600 flex items-center justify-center shadow-lg">
            <span className="text-white font-bold text-lg font-devanagari">न</span>
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white font-devanagari">राष्ट्रीय गवेषण मंच</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">National Research Intelligence Platform</p>
          </div>
        </div>
      </div>
    </header>
    <main className="max-w-7xl mx-auto px-4 py-8">
      <SkeletonLoader type="stats" />
    </main>
  </div>
)

const AppShell: React.FC = () => {
  const { isLoading, login, loginError, user, backendAvailable } = useAuth()
  const { themeName, toggleTheme } = useTheme()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-navy-900 text-white">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-3 border-saffron-200 border-t-saffron-500 animate-spin" />
          <p className="text-sm tracking-[0.25em] text-saffron-600 dark:text-saffron-400 uppercase">Loading Secure Session</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Login onLogin={login} error={loginError} backendAvailable={backendAvailable} />
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-navy-900 transition-colors duration-300">
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

const App: React.FC = () => (
  <AuthProvider>
    <AppShell />
  </AuthProvider>
)

export default App
export { AppShell }
