import React, { startTransition, useEffect, useState } from 'react'
import { BuildingIcon, LoaderIcon, LogOutIcon, SearchIcon, ShieldCheckIcon, SparklesIcon } from '../components/Icons'
import SearchBar from '../components/SearchBar'
import { useAuth } from '../hooks/useAuth'
import { authService } from '../services/authService'
import { QueryResponse, queryService } from '../services/queryService'

type LicensedResearcher = {
  researcher_id: string
  name: string
  institution_id: string
  state: string
  research_area: string | null
  year_joined: number | null
  licensed: boolean
}

type IndustryPayload = {
  role: string
  results: LicensedResearcher[]
}

const IndustryView: React.FC = () => {
  const { logout, user } = useAuth()
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null)
  const [licensedResearchers, setLicensedResearchers] = useState<LicensedResearcher[]>([])
  const [error, setError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | undefined>(undefined)
  const [isQuerying, setIsQuerying] = useState(false)
  const [isLoadingLicensedData, setIsLoadingLicensedData] = useState(true)

  useEffect(() => {
    let cancelled = false

    const loadLicensedData = async () => {
      setIsLoadingLicensedData(true)
      try {
        const payload = await authService.fetchResearchers() as IndustryPayload
        if (!cancelled) {
          setLicensedResearchers(payload.results)
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : 'Failed to load licensed data')
        }
      } finally {
        if (!cancelled) {
          setIsLoadingLicensedData(false)
        }
      }
    }

    void loadLicensedData()

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

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,_#faf5ff_0%,_#f8fafc_28%,_#ffffff_100%)] text-slate-900">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-violet-600">Tier 3 Access</p>
            <h1 className="mt-1 flex items-center gap-3 text-3xl font-semibold">
              <BuildingIcon className="h-7 w-7 text-violet-600" />
              Industry Partnership Console
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-violet-50 px-4 py-2 text-sm text-violet-700">
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
                <p className="text-sm font-medium text-slate-500">Licensed capability search</p>
                <h2 className="mt-1 text-2xl font-semibold text-slate-900">Submit real queries through Kong</h2>
              </div>
              <div className="rounded-2xl bg-violet-50 p-3 text-violet-600">
                <SearchIcon className="h-5 w-5" />
              </div>
            </div>

            <SearchBar
              onSearch={handleSearch}
              isLoading={isQuerying}
              placeholder="Ask about licensed capabilities, partner institutions, or innovation domains..."
            />

            {error ? (
              <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            ) : null}

            <div className="mt-6 rounded-3xl bg-slate-950 p-6 text-slate-100">
              {isQuerying ? (
                <div className="flex items-center gap-3">
                  <LoaderIcon className="h-5 w-5 animate-spin text-violet-300" />
                  <span>Generating an industry-safe answer...</span>
                </div>
              ) : queryResult ? (
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-3 text-xs uppercase tracking-[0.2em] text-violet-300">
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
                  Results here reflect the licensed, limited view served by the actual JWT-protected API.
                </p>
              )}
            </div>
          </div>
        </section>

        <aside className="space-y-6">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-3">
              <SparklesIcon className="h-5 w-5 text-violet-600" />
              <h3 className="text-lg font-semibold">Licensed records</h3>
            </div>

            {isLoadingLicensedData ? (
              <div className="flex items-center gap-3 text-sm text-slate-500">
                <LoaderIcon className="h-4 w-4 animate-spin" />
                Loading industry-safe data...
              </div>
            ) : (
              <div className="space-y-3">
                {licensedResearchers.slice(0, 4).map((researcher) => (
                  <article key={researcher.researcher_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <h4 className="font-medium text-slate-900">{researcher.name}</h4>
                      <span className="rounded-full bg-violet-100 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-violet-700">
                        Licensed
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{researcher.research_area || 'Research area not specified'}</p>
                    <p className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-500">
                      {researcher.state} • {researcher.institution_id}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-3">
              <ShieldCheckIcon className="h-5 w-5 text-amber-600" />
              <h3 className="text-lg font-semibold">Persona flow</h3>
            </div>
            <ul className="space-y-3 text-sm text-slate-600">
              <li>Frontend stores JWT pairs and refreshes them against the real API.</li>
              <li>Industry view only sees licensed researcher records from `/researchers`.</li>
              <li>Search requests use the same Kong proxy path as the other personas.</li>
            </ul>
          </div>
        </aside>
      </main>
    </div>
  )
}

export default IndustryView
