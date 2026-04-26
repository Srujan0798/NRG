import React, { useCallback, useEffect, useMemo, useState } from 'react'
import {
  BarChart3,
  BookOpen,
  Building2,
  Download,
  Lock,
  RefreshCw,
  ShieldCheck,
  SlidersHorizontal,
  Users,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { AuthUser } from '../services/authService'
import {
  AuditEventRecord,
  PublicationRow,
  StatsResponse,
  queryService,
} from '../services/queryService'
import { t } from '../i18n'
import {
  productionWorkspaceRoutes,
  type ProductionWorkspaceRoute,
  type ProductionWorkspaceScreen,
} from './productionWorkspaceConfig'

type Loadable<T> =
  | { status: 'idle' | 'loading'; rows?: T[]; value?: T; message?: string }
  | { status: 'loaded'; rows?: T[]; value?: T; message?: string }
  | { status: 'error'; rows?: T[]; value?: T; message: string }

export interface ResearcherProfileRow {
  researcher_id?: string
  name?: string
  institution_id?: string
  institution?: string
  state?: string
  research_area?: string
  email?: string
  phone?: string
}

export interface IndustryCapabilityRow {
  institution?: string
  institute?: string
  research_area?: string
  sector?: string
  patents?: number
  publications?: number
  match_score?: number
  year?: number
}

export interface ProductionWorkspaceData {
  publications: Loadable<PublicationRow>
  researchers: Loadable<ResearcherProfileRow>
  stats: Loadable<StatsResponse>
  industry: Loadable<IndustryCapabilityRow>
  audit: Loadable<AuditEventRecord>
}

const emptyData: ProductionWorkspaceData = {
  publications: { status: 'idle', rows: [] },
  researchers: { status: 'idle', rows: [] },
  stats: { status: 'idle' },
  industry: { status: 'idle', rows: [] },
  audit: { status: 'idle', rows: [] },
}

const routeIcons: Record<ProductionWorkspaceScreen, React.ElementType> = {
  publications: BookOpen,
  researchers: Users,
  reports: BarChart3,
  industry: Building2,
  settings: SlidersHorizontal,
}

function canAccessRoute(user: AuthUser, route: ProductionWorkspaceRoute): boolean {
  return user.tier <= route.minimumTier
}

function getRoute(screen: ProductionWorkspaceScreen): ProductionWorkspaceRoute {
  return productionWorkspaceRoutes.find((route) => route.screen === screen) || productionWorkspaceRoutes[0]
}

function formatNumber(value?: number | null): string {
  if (typeof value !== 'number') return t('productionWorkspace.common.notAvailable')
  return value.toLocaleString('en-IN')
}

function normaliseResearcherRows(payload: { results?: unknown[] } | unknown): ResearcherProfileRow[] {
  const rows = Array.isArray((payload as { results?: unknown[] })?.results)
    ? (payload as { results?: unknown[] }).results
    : Array.isArray(payload)
      ? payload
      : []

  return rows
    .filter((row): row is ResearcherProfileRow => Boolean(row && typeof row === 'object'))
    .slice(0, 12)
}

export function buildIndustryCapabilityRowsFromStats(stats: StatsResponse): IndustryCapabilityRow[] {
  const areas = stats.research_area_distribution || []
  const states = stats.state_distribution || []

  return areas.slice(0, 10).map((area, index) => {
    const state = states[index % Math.max(states.length, 1)]
    return {
      institution: state?.state
        ? t('productionWorkspace.industry.regionalCluster', { state: state.state })
        : t('productionWorkspace.industry.nationalCluster'),
      research_area: area.area,
      publications: area.count,
    }
  })
}

function downloadCsv(filename: string, rows: Array<Record<string, unknown>>): void {
  if (!rows.length) return
  const headers = Object.keys(rows[0])
  const csv = [
    headers.join(','),
    ...rows.map((row) => headers.map((header) => `"${String(row[header] ?? '').replace(/"/g, '""')}"`).join(',')),
  ].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = window.document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

const WorkspaceTable: React.FC<{
  caption: string
  headers: string[]
  rows: string[][]
}> = ({ caption, headers, rows }) => {
  if (!rows.length) {
    return (
      <div className="rounded-2xl border border-dashed border-nrg-border bg-[var(--glass-bg)] p-6 text-sm text-nrg-muted">
        {t('productionWorkspace.common.noRows')}
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-nrg-border bg-[var(--nrg-surface)] shadow-sm">
      <div className="max-w-full overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <caption className="sr-only">{caption}</caption>
          <thead className="bg-[var(--glass-bg)] text-xs uppercase tracking-[0.12em] text-nrg-muted">
            <tr>
              {headers.map((header) => (
                <th key={header} scope="col" className="border-b border-nrg-border px-4 py-3 font-semibold">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={`${row.join('|')}-${rowIndex}`} className="hover:bg-saffron-500/5">
                {row.map((cell, cellIndex) => (
                  <td key={`${cell}-${cellIndex}`} className="border-b border-nrg-border/40 px-4 py-3 text-nrg-text">
                    {cell || t('productionWorkspace.common.notAvailable')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const StatePanel: React.FC<{
  status: Loadable<unknown>['status']
  onRetry: () => void
  message?: string
}> = ({ status, onRetry, message }) => {
  if (status === 'loaded') return null

  const isLoading = status === 'loading' || status === 'idle'
  return (
    <div className="rounded-2xl border border-nrg-border bg-[var(--glass-bg)] p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-nrg-text">
            {isLoading ? t('productionWorkspace.common.loading') : t('productionWorkspace.common.errorTitle')}
          </p>
          <p className="mt-1 text-sm text-nrg-muted">
            {message || (isLoading ? t('productionWorkspace.common.loadingBody') : t('productionWorkspace.common.errorBody'))}
          </p>
        </div>
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-nrg-border bg-[var(--nrg-surface)] px-4 py-2 text-sm font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)] focus:outline-none focus:ring-2 focus:ring-[var(--nrg-focus)]"
        >
          <RefreshCw size={16} aria-hidden="true" />
          {t('productionWorkspace.common.retry')}
        </button>
      </div>
    </div>
  )
}

const RestrictedPanel: React.FC<{
  user: AuthUser
  titleKey?: string
  bodyKey?: string
}> = ({
  user,
  titleKey = 'productionWorkspace.researchers.restrictedTitle',
  bodyKey = 'productionWorkspace.researchers.restrictedBody',
}) => (
  <section className="rounded-3xl border border-nrg-border bg-[var(--nrg-surface)] p-8 shadow-sm">
    <div className="flex max-w-3xl flex-col gap-4">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--glass-bg)] text-nrg-text">
        <Lock size={22} aria-hidden="true" />
      </div>
      <div>
        <h2 className="text-2xl font-bold text-nrg-text">{t(titleKey)}</h2>
        <p className="mt-2 text-sm leading-6 text-nrg-muted">
          {t(bodyKey, { role: user.role })}
        </p>
      </div>
    </div>
  </section>
)

const ScreenHeader: React.FC<{
  screen: ProductionWorkspaceScreen
  user: AuthUser
}> = ({ screen, user }) => {
  const activeRoute = getRoute(screen)
  const Icon = routeIcons[screen]

  return (
    <section className="rounded-3xl border border-nrg-border bg-[var(--nrg-surface)] p-6 shadow-sm">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[var(--glass-bg)] text-nrg-text">
            <Icon size={24} aria-hidden="true" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-nrg-muted">
              {t('productionWorkspace.common.workspace')}
            </p>
            <h1 className="mt-2 text-3xl font-bold text-nrg-text">{t(activeRoute.labelKey)}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-nrg-muted">{t(activeRoute.descriptionKey)}</p>
          </div>
        </div>
        <div className="rounded-2xl border border-nrg-border bg-[var(--glass-bg)] px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-nrg-muted">
            {t('productionWorkspace.common.activeAccess')}
          </p>
          <p className="mt-1 text-sm font-semibold text-nrg-text">
            {t('productionWorkspace.common.tierLabel', { tier: user.tier, role: user.role })}
          </p>
        </div>
      </div>
    </section>
  )
}

const PublicationsScreen: React.FC<{
  data: ProductionWorkspaceData
  onRetry: () => void
}> = ({ data, onRetry }) => {
  const rows = data.publications.rows || []
  return (
    <section className="space-y-4">
      <StatePanel status={data.publications.status} message={data.publications.message} onRetry={onRetry} />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-nrg-muted">{t('productionWorkspace.publications.count', { count: rows.length })}</p>
        <button
          type="button"
          onClick={() => downloadCsv('nrg-publications.csv', rows.map((row) => ({ ...row })))}
          className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-nrg-border bg-[var(--nrg-surface)] px-4 py-2 text-sm font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)] focus:outline-none focus:ring-2 focus:ring-[var(--nrg-focus)]"
        >
          <Download size={16} aria-hidden="true" />
          {t('productionWorkspace.common.exportCsv')}
        </button>
      </div>
      <WorkspaceTable
        caption={t('productionWorkspace.publications.tableCaption')}
        headers={[
          t('productionWorkspace.publications.title'),
          t('productionWorkspace.publications.area'),
          t('productionWorkspace.publications.year'),
          t('productionWorkspace.publications.citations'),
          t('productionWorkspace.publications.venue'),
        ]}
        rows={rows.map((row) => [
          row.title,
          row.research_area || '',
          formatNumber(row.year),
          formatNumber(row.citations),
          row.venue || '',
        ])}
      />
    </section>
  )
}

const ResearchersScreen: React.FC<{
  user: AuthUser
  data: ProductionWorkspaceData
  onRetry: () => void
}> = ({ user, data, onRetry }) => {
  if (user.tier > 1) return <RestrictedPanel user={user} />

  const rows = data.researchers.rows || []
  return (
    <section className="space-y-4">
      <StatePanel status={data.researchers.status} message={data.researchers.message} onRetry={onRetry} />
      <WorkspaceTable
        caption={t('productionWorkspace.researchers.tableCaption')}
        headers={[
          t('productionWorkspace.researchers.name'),
          t('productionWorkspace.researchers.area'),
          t('productionWorkspace.researchers.institution'),
          t('productionWorkspace.researchers.state'),
          t('productionWorkspace.researchers.email'),
        ]}
        rows={rows.map((row) => [
          row.name || '',
          row.research_area || '',
          row.institution_id || row.institution || '',
          row.state || '',
          row.email || '',
        ])}
      />
    </section>
  )
}

const ReportsScreen: React.FC<{
  data: ProductionWorkspaceData
  onRetry: () => void
}> = ({ data, onRetry }) => {
  const stats = data.stats.value
  const areaRows = stats?.research_area_distribution || []
  const stateRows = stats?.state_distribution || []

  return (
    <section className="space-y-6">
      <StatePanel status={data.stats.status} message={data.stats.message} onRetry={onRetry} />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          [t('productionWorkspace.reports.researchers'), formatNumber(stats?.total_researchers)],
          [t('productionWorkspace.reports.publications'), formatNumber(stats?.total_publications)],
          [t('productionWorkspace.reports.institutions'), formatNumber(stats?.total_institutions)],
          [t('productionWorkspace.reports.labs'), formatNumber(stats?.total_labs)],
        ].map(([label, value]) => (
          <article key={label} className="rounded-2xl border border-nrg-border bg-[var(--nrg-surface)] p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-nrg-muted">{label}</p>
            <p className="mt-3 text-2xl font-bold text-nrg-text">{value}</p>
          </article>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <WorkspaceTable
          caption={t('productionWorkspace.reports.areaCaption')}
          headers={[t('productionWorkspace.reports.area'), t('productionWorkspace.reports.count')]}
          rows={areaRows.slice(0, 8).map((row) => [row.area, formatNumber(row.count)])}
        />
        <WorkspaceTable
          caption={t('productionWorkspace.reports.stateCaption')}
          headers={[t('productionWorkspace.reports.state'), t('productionWorkspace.reports.count')]}
          rows={stateRows.slice(0, 8).map((row) => [row.state, formatNumber(row.count)])}
        />
      </div>
    </section>
  )
}

const IndustryScreen: React.FC<{
  data: ProductionWorkspaceData
  onRetry: () => void
}> = ({ data, onRetry }) => {
  const rows = data.industry.rows || []

  return (
    <section className="space-y-4">
      <StatePanel status={data.industry.status} message={data.industry.message} onRetry={onRetry} />
      <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4">
        <p className="text-sm font-semibold text-nrg-text">{t('productionWorkspace.industry.noticeTitle')}</p>
        <p className="mt-1 text-sm text-nrg-muted">{t('productionWorkspace.industry.noticeBody')}</p>
      </div>
      <WorkspaceTable
        caption={t('productionWorkspace.industry.tableCaption')}
        headers={[
          t('productionWorkspace.industry.institution'),
          t('productionWorkspace.industry.area'),
          t('productionWorkspace.industry.patents'),
          t('productionWorkspace.industry.publications'),
          t('productionWorkspace.industry.match'),
        ]}
        rows={rows.map((row) => [
          row.institution || row.institute || '',
          row.research_area || row.sector || '',
          formatNumber(row.patents),
          formatNumber(row.publications),
          formatNumber(row.match_score),
        ])}
      />
    </section>
  )
}

const SettingsScreen: React.FC<{
  user: AuthUser
  data: ProductionWorkspaceData
  onRetry: () => void
  onLogout: () => void
}> = ({ user, data, onRetry, onLogout }) => {
  const events = data.audit.rows || []

  return (
    <section className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <article className="rounded-3xl border border-nrg-border bg-[var(--nrg-surface)] p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <ShieldCheck size={22} className="text-emerald-600" aria-hidden="true" />
          <h2 className="text-xl font-bold text-nrg-text">{t('productionWorkspace.settings.profileTitle')}</h2>
        </div>
        <dl className="mt-6 space-y-4 text-sm">
          <div>
            <dt className="text-nrg-muted">{t('productionWorkspace.settings.username')}</dt>
            <dd className="mt-1 font-semibold text-nrg-text">{user.username}</dd>
          </div>
          <div>
            <dt className="text-nrg-muted">{t('productionWorkspace.settings.role')}</dt>
            <dd className="mt-1 font-semibold text-nrg-text">{user.role}</dd>
          </div>
          <div>
            <dt className="text-nrg-muted">{t('productionWorkspace.settings.tier')}</dt>
            <dd className="mt-1 font-semibold text-nrg-text">{formatNumber(user.tier)}</dd>
          </div>
        </dl>
        <button
          type="button"
          onClick={onLogout}
          className="mt-6 inline-flex min-h-11 items-center justify-center rounded-xl bg-red-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-700"
        >
          {t('productionWorkspace.settings.logout')}
        </button>
      </article>

      <article className="rounded-3xl border border-nrg-border bg-[var(--nrg-surface)] p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-nrg-text">{t('productionWorkspace.settings.auditTitle')}</h2>
            <p className="mt-1 text-sm text-nrg-muted">{t('productionWorkspace.settings.auditBody')}</p>
          </div>
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-nrg-border bg-[var(--glass-bg)] px-4 py-2 text-sm font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)] focus:outline-none focus:ring-2 focus:ring-[var(--nrg-focus)]"
          >
            <RefreshCw size={16} aria-hidden="true" />
            {t('productionWorkspace.common.refresh')}
          </button>
        </div>
        <div className="mt-5">
          <StatePanel status={data.audit.status} message={data.audit.message} onRetry={onRetry} />
          <WorkspaceTable
            caption={t('productionWorkspace.settings.auditCaption')}
            headers={[
              t('productionWorkspace.settings.event'),
              t('productionWorkspace.settings.action'),
              t('productionWorkspace.settings.status'),
              t('productionWorkspace.settings.integrity'),
            ]}
            rows={events.slice(0, 8).map((event) => [
              event.id,
              event.action,
              event.status || '',
              event.integrity_status || '',
            ])}
          />
        </div>
      </article>
    </section>
  )
}

export const ProductionWorkspaceView: React.FC<{
  screen: ProductionWorkspaceScreen
  user: AuthUser
  data: ProductionWorkspaceData
  onRetry: (screen: ProductionWorkspaceScreen) => void
  onLogout: () => void
}> = ({ screen, user, data, onRetry, onLogout }) => {
  const activeRoute = getRoute(screen)
  const activeRouteAllowed = canAccessRoute(user, activeRoute)
  const visibleRoutes = productionWorkspaceRoutes.filter((route) => canAccessRoute(user, route))

  return (
    <div className="nrg-app-canvas min-h-screen">
      <header className="sticky top-0 z-40 border-b border-nrg-border bg-[var(--glass-bg)] backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 lg:flex-row lg:items-center lg:justify-between">
          <a href="/" className="flex min-h-11 items-center gap-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-[var(--nrg-focus)]">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-saffron-600 text-lg font-bold text-white">
              N
            </div>
            <div>
              <p className="text-sm font-bold text-nrg-text">{t('productionWorkspace.header.product')}</p>
              <p className="text-xs uppercase tracking-[0.16em] text-nrg-muted">{t('productionWorkspace.header.subtitle')}</p>
            </div>
          </a>
          <nav aria-label={t('productionWorkspace.header.navLabel')} className="flex gap-2 overflow-x-auto">
            {visibleRoutes.map((route) => {
              const Icon = routeIcons[route.screen]
              const active = route.screen === activeRoute.screen
              return (
                <a
                  key={route.href}
                  href={route.href}
                  aria-current={active ? 'page' : undefined}
                  className={`inline-flex min-h-11 shrink-0 items-center gap-2 rounded-xl border px-3 py-2 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-[var(--nrg-focus)] ${
                    active
                      ? 'border-saffron-600 bg-saffron-600 text-white'
                      : 'border-nrg-border bg-[var(--nrg-surface)] text-nrg-text hover:border-[var(--nrg-focus)]'
                  }`}
                >
                  <Icon size={16} aria-hidden="true" />
                  {t(route.labelKey)}
                </a>
              )
            })}
          </nav>
        </div>
      </header>

      <main id="main-content" className="mx-auto max-w-7xl space-y-6 px-4 py-8">
        <ScreenHeader screen={screen} user={user} />
        {!activeRouteAllowed && screen === 'researchers' && <RestrictedPanel user={user} />}
        {!activeRouteAllowed && screen !== 'researchers' && (
          <RestrictedPanel
            user={user}
            titleKey="productionWorkspace.common.restrictedTitle"
            bodyKey="productionWorkspace.common.restrictedBody"
          />
        )}
        {activeRouteAllowed && screen === 'publications' && <PublicationsScreen data={data} onRetry={() => onRetry('publications')} />}
        {activeRouteAllowed && screen === 'researchers' && <ResearchersScreen user={user} data={data} onRetry={() => onRetry('researchers')} />}
        {activeRouteAllowed && screen === 'reports' && <ReportsScreen data={data} onRetry={() => onRetry('reports')} />}
        {activeRouteAllowed && screen === 'industry' && <IndustryScreen data={data} onRetry={() => onRetry('industry')} />}
        {activeRouteAllowed && screen === 'settings' && (
          <SettingsScreen user={user} data={data} onRetry={() => onRetry('settings')} onLogout={onLogout} />
        )}
      </main>
    </div>
  )
}

export const ProductionWorkspace: React.FC<{ screen: ProductionWorkspaceScreen }> = ({ screen }) => {
  const { user, logout } = useAuth()
  const [data, setData] = useState<ProductionWorkspaceData>(emptyData)

  const setSection = useCallback(<K extends keyof ProductionWorkspaceData>(key: K, value: ProductionWorkspaceData[K]) => {
    setData((current) => ({ ...current, [key]: value }))
  }, [])

  const loadScreen = useCallback(async (nextScreen: ProductionWorkspaceScreen) => {
    if (!user) return
    const nextRoute = getRoute(nextScreen)
    if (!canAccessRoute(user, nextRoute)) return

    if (nextScreen === 'publications') {
      setSection('publications', { status: 'loading', rows: [] })
      try {
        const response = await queryService.fetchPublications(25)
        setSection('publications', { status: 'loaded', rows: response.publications || [] })
      } catch {
        setSection('publications', { status: 'error', rows: [], message: t('productionWorkspace.publications.error') })
      }
    }

    if (nextScreen === 'researchers') {
      if (user.tier > 1) return
      setSection('researchers', { status: 'loading', rows: [] })
      try {
        const response = await queryService.fetchResearchers()
        setSection('researchers', { status: 'loaded', rows: normaliseResearcherRows(response) })
      } catch {
        setSection('researchers', { status: 'error', rows: [], message: t('productionWorkspace.researchers.error') })
      }
    }

    if (nextScreen === 'reports') {
      setSection('stats', { status: 'loading' })
      try {
        const response = await queryService.fetchStats()
        setSection('stats', { status: 'loaded', value: response })
      } catch {
        setSection('stats', { status: 'error', message: t('productionWorkspace.reports.error') })
      }
    }

    if (nextScreen === 'industry') {
      setSection('industry', { status: 'loading', rows: [] })
      try {
        const response = await queryService.fetchStats()
        setSection('industry', { status: 'loaded', rows: buildIndustryCapabilityRowsFromStats(response) })
      } catch {
        setSection('industry', { status: 'error', rows: [], message: t('productionWorkspace.industry.error') })
      }
    }

    if (nextScreen === 'settings') {
      setSection('audit', { status: 'loading', rows: [] })
      try {
        const response = await queryService.listAuditEvents(20)
        setSection('audit', { status: 'loaded', rows: response.events })
      } catch {
        setSection('audit', { status: 'error', rows: [], message: t('productionWorkspace.settings.error') })
      }
    }
  }, [setSection, user])

  useEffect(() => {
    void loadScreen(screen)
  }, [loadScreen, screen])

  const handleRetry = useCallback((nextScreen: ProductionWorkspaceScreen) => {
    void loadScreen(nextScreen)
  }, [loadScreen])

  const safeUser = useMemo<AuthUser>(() => user || {
    id: 'unknown',
    username: 'unknown',
    role: 'industry',
    tier: 3,
  }, [user])

  return (
    <ProductionWorkspaceView
      screen={screen}
      user={safeUser}
      data={data}
      onRetry={handleRetry}
      onLogout={() => void logout()}
    />
  )
}

export default ProductionWorkspace
