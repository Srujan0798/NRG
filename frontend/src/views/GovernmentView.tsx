import React, { startTransition, useEffect, useState } from 'react'
import { BarChart3Icon, Building2Icon, LoaderIcon, LogOutIcon, SearchIcon, ShieldCheckIcon } from '../components/Icons'
import SearchBar from '../components/SearchBar'
import { useAuth } from '../hooks/useAuth'
import { authService } from '../services/authService'
import { QueryResponse, queryService } from '../services/queryService'

type GovernmentResults = {
  total_researchers: number
  state_distribution: Record<string, number>
  research_area_distribution: Record<string, number>
  sample_records: Array<Record<string, string | number | null>>
}

type GovernmentPayload = {
  role: string
  results: GovernmentResults
}

const GovernmentView: React.FC = () => {
  const { logout, user } = useAuth()
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null)
  const [analytics, setAnalytics] = useState<GovernmentResults | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | undefined>(undefined)
  const [isQuerying, setIsQuerying] = useState(false)
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(true)

  useEffect(() => {
    let cancelled = false

    const loadAnalytics = async () => {
      setIsLoadingAnalytics(true)
      try {
        const payload = await authService.fetchResearchers() as GovernmentPayload
        if (!cancelled) {
          setAnalytics(payload.results)
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : 'Failed to load government analytics')
        }
      } finally {
        if (!cancelled) {
          setIsLoadingAnalytics(false)
        }
      }
    }

    void loadAnalytics()

    return () => {
      cancelled = true
    }
  }, [])

  const handleSearch = async (searchQuery: string) => {
    setIsQuerying(true)
    setError(null)

    try {
      const result = await queryService.query({
        query: searchQuery,
        sessionId
      })

      startTransition(() => {
        setQueryResult(result)
        setSessionId(result.session_id)
      })
    } catch (queryError) {
      setError(queryError instanceof Error ? queryError.message : 'Query failed')
    } finally {
      setIsQuerying(false)
    }
  }

  const topStates = analytics
    ? Object.entries(analytics.state_distribution).sort((left, right) => right[1] - left[1]).slice(0, 4)
    : []

  const topAreas = analytics
    ? Object.entries(analytics.research_area_distribution).sort((left, right) => right[1] - left[1]).slice(0, 4)
    : []

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,_#f0fdf4_0%,_#f8fafc_30%,_#ffffff_100%)] text-slate-900">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-emerald-600">Tier 2 Access</p>
            <h1 className="mt-1 flex items-center gap-3 text-3xl font-semibold">
              <Building2Icon className="h-7 w-7 text-emerald-600" />
              Government Analytics Console
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-emerald-50 px-4 py-2 text-sm text-emerald-700">
              Signed in as {user?.username}
            </div>
            <button
              onClick={() => void logout()}
              className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            >
              <LogOutIcon className="h-4 w-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[1.45fr_0.95fr]">
        <section className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Policy and planning workflow</p>
                <h2 className="mt-1 text-2xl font-semibold text-slate-900">Ask the live orchestration API</h2>
              </div>
              <div className="rounded-2xl bg-emerald-50 p-3 text-emerald-600">
                <SearchIcon className="h-5 w-5" />
              </div>
            </div>

            <SearchBar
              onSearch={handleSearch}
              isLoading={isQuerying}
              placeholder="Ask for state-level trends, funding concentration, or institutional performance..."
            />

            {error ? (
              <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            ) : null}

            <div className="mt-6 rounded-3xl bg-slate-950 p-6 text-slate-100">
              {isQuerying ? (
                <div className="flex items-center gap-3">
                  <LoaderIcon className="h-5 w-5 animate-spin text-emerald-300" />
                  <span>Generating an authenticated government response...</span>
                </div>
              ) : queryResult ? (
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-3 text-xs uppercase tracking-[0.2em] text-emerald-300">
                    <span>Intent: {queryResult.intent ?? 'n/a'}</span>
                    <span>Route: {queryResult.routing_decision ?? 'n/a'}</span>
                    <span>Session: {queryResult.session_id ?? 'new'}</span>
                  </div>
                  <p className="whitespace-pre-wrap text-base leading-7 text-slate-100">
                    {queryResult.response}
                  </p>
                </div>
              ) : (
                <p className="text-slate-400">
                  Government summaries and planning answers will render here after the Kong-routed request completes.
                </p>
              )}
            </div>
          </div>
        </section>

        <aside className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-3">
              <BarChart3Icon className="h-5 w-5 text-emerald-600" />
              <h3 className="text-lg font-semibold">Aggregated researcher access</h3>
            </div>

            {isLoadingAnalytics || !analytics ? (
              <div className="flex items-center gap-3 text-sm text-slate-500">
                <LoaderIcon className="h-4 w-4 animate-spin" />
                Loading anonymized data...
              </div>
            ) : (
              <div className="space-y-4">
                <div className="rounded-2xl bg-emerald-50 p-4">
                  <p className="text-sm text-emerald-700">Total researchers visible</p>
                  <p className="mt-1 text-3xl font-semibold text-emerald-900">{analytics.total_researchers}</p>
                </div>

                <div>
                  <p className="mb-2 text-sm font-medium text-slate-500">Top states</p>
                  <div className="space-y-2">
                    {topStates.map(([state, count]) => (
                      <div key={state} className="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-3 text-sm">
                        <span>{state}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="mb-2 text-sm font-medium text-slate-500">Top research areas</p>
                  <div className="space-y-2">
                    {topAreas.map(([area, count]) => (
                      <div key={area} className="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-3 text-sm">
                        <span>{area}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-3">
              <ShieldCheckIcon className="h-5 w-5 text-sky-600" />
              <h3 className="text-lg font-semibold">Persona flow</h3>
            </div>
            <ul className="space-y-3 text-sm text-slate-600">
              <li>JWT is refreshed transparently in the browser if Kong returns `401`.</li>
              <li>The researcher endpoint returns only aggregated and anonymized data for this role.</li>
              <li>All search traffic is sent through `/api/*` and proxied to Kong on port `8000`.</li>
            </ul>
          </div>
        </aside>
      </main>
    </div>
  )
}

export default GovernmentView
