import React, { lazy, Suspense } from 'react'
import { ResearcherDashboard } from './views/ResearcherDashboard'
import { GovernmentDashboard } from './views/GovernmentDashboard'
import { IndustryDashboard } from './views/IndustryDashboard'
import Login from './components/Login'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { SkeletonLoader } from './components/SkeletonLoader'
import { TierBadge } from './components/TierBadge'

// Loading fallback for Suspense
const DashboardLoading = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100">
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-2 animate-pulse" />
        <div className="h-4 bg-gray-100 rounded w-1/4 animate-pulse" />
      </div>
    </header>
    <main className="max-w-7xl mx-auto px-4 py-8">
      <SkeletonLoader type="card" count={3} />
    </main>
  </div>
)

const AppShell: React.FC = () => {
  const { isLoading, login, loginError, user } = useAuth()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <div className="rounded-2xl border border-white/10 bg-white/5 px-6 py-4 text-sm tracking-[0.2em] text-cyan-300">
          LOADING SECURE SESSION
        </div>
      </div>
    )
  }

  if (!user) {
    return <Login onLogin={login} error={loginError} />
  }

  return (
    <div>
      {user.role === 'government' && <GovernmentDashboard />}
      {user.role === 'industry' && <IndustryDashboard />}
      {user.role === 'researcher' && <ResearcherDashboard />}
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
