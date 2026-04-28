import React, { useMemo } from 'react'
import {
  BarChart3,
  BookOpen,
  Building2,
  SlidersHorizontal,
  Users,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { AuthUser } from '../services/authService'
import { t } from '../i18n'
import {
  productionWorkspaceRoutes,
  type ProductionWorkspaceScreen,
  type ProductionWorkspaceRoute,
} from './productionWorkspaceConfig'
import { WorkspaceTable } from './components/WorkspaceTable'
import { RestrictedPanel, StatePanel } from './components/StatePanel'
import { ScreenHeader } from './components/ScreenHeader'
import { useWorkspaceData, type ProductionWorkspaceData } from './useWorkspaceData'
import { parseMetricNumber } from './productionWorkspaceData'

function canAccessRoute(user: AuthUser, route: ProductionWorkspaceRoute): boolean {
  return user.tier <= route.minimumTier
}

function getRoute(screen: ProductionWorkspaceScreen): ProductionWorkspaceRoute {
  return productionWorkspaceRoutes.find((route) => route.screen === screen) || productionWorkspaceRoutes[0]
}

const iconMap = { BookOpen, Users, BarChart3, Building2, SlidersHorizontal }

function formatNumber(value?: number | string | null): string {
  const numericValue = parseMetricNumber(value)
  if (numericValue === null) return t('productionWorkspace.common.notAvailable')
  return numericValue.toLocaleString('en-IN')
}

function PublicationsScreen({ data, onRetry }: { data: ProductionWorkspaceData; onRetry: () => void }) {
  const rows = data.publications.rows || []
  return (
    <section className="space-y-4">
      <StatePanel status={data.publications.status} message={data.publications.message} onRetry={onRetry} />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-nrg-muted">{t('productionWorkspace.publications.count', { count: rows.length })}</p>
      </div>
      <WorkspaceTable
        caption={t('productionWorkspace.publications.tableCaption')}
        exportFilename="nrg-publications.csv"
        headers={[
          t('productionWorkspace.publications.title'),
          t('productionWorkspace.publications.area'),
          t('productionWorkspace.publications.year'),
          t('productionWorkspace.publications.citations'),
          t('productionWorkspace.publications.venue'),
        ]}
        rows={rows.map((row) => [
          row.title || '',
          row.research_area || '',
          formatNumber(row.year),
          formatNumber(row.citations),
          row.venue || '',
        ])}
      />
    </section>
  )
}

function ResearchersScreen({
  user,
  data,
  onRetry,
}: {
  user: AuthUser
  data: ProductionWorkspaceData
  onRetry: () => void
}) {
  if (user.tier > 1) return <RestrictedPanel user={user} />

  const rows = data.researchers.rows || []
  return (
    <section className="space-y-4">
      <StatePanel status={data.researchers.status} message={data.researchers.message} onRetry={onRetry} />
      <WorkspaceTable
        caption={t('productionWorkspace.researchers.tableCaption')}
        exportFilename="nrg-researchers.csv"
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

function ReportsScreen({ data, onRetry }: { data: ProductionWorkspaceData; onRetry: () => void }) {
  const stats = data.stats.value
  const areaRows = stats?.research_area_distribution?.length
    ? stats.research_area_distribution
    : [
        { area: t('productionWorkspace.reports.researchers'), count: stats?.total_researchers || 0 },
        { area: t('productionWorkspace.reports.publications'), count: stats?.total_publications || 0 },
      ]
  const stateRows = stats?.state_distribution?.length
    ? stats.state_distribution
    : [{ state: t('productionWorkspace.reports.national'), count: stats?.total_institutions || 0 }]

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
          <article
            key={label as string}
            className="rounded-2xl border border-nrg-border bg-[var(--nrg-surface)] p-5 shadow-sm"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-nrg-muted">{label as string}</p>
            <p className="mt-3 text-2xl font-bold text-nrg-text">{value}</p>
          </article>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <WorkspaceTable
          caption={t('productionWorkspace.reports.areaCaption')}
          exportFilename="nrg-government-research-areas.csv"
          headers={[t('productionWorkspace.reports.area'), t('productionWorkspace.reports.count')]}
          rows={areaRows.slice(0, 8).map((row) => [row.area, formatNumber(row.count)])}
        />
        <WorkspaceTable
          caption={t('productionWorkspace.reports.stateCaption')}
          exportFilename="nrg-government-state-distribution.csv"
          headers={[t('productionWorkspace.reports.state'), t('productionWorkspace.reports.count')]}
          rows={stateRows.slice(0, 8).map((row) => [row.state, formatNumber(row.count)])}
        />
      </div>
    </section>
  )
}

function IndustryScreen({ data, onRetry }: { data: ProductionWorkspaceData; onRetry: () => void }) {
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
        exportFilename="nrg-industry-capability.csv"
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

function SettingsScreen({
  user,
  data,
  onRetry,
  onLogout,
}: {
  user: AuthUser
  data: ProductionWorkspaceData
  onRetry: () => void
  onLogout: () => void
}) {
  const events = data.audit.rows || []

  return (
    <section className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <article className="rounded-3xl border border-nrg-border bg-[var(--nrg-surface)] p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <svg className="h-6 w-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042.133-2.482.478-3.623z" />
          </svg>
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
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            {t('productionWorkspace.common.refresh')}
          </button>
        </div>
        <div className="mt-5">
          <StatePanel status={data.audit.status} message={data.audit.message} onRetry={onRetry} />
          <WorkspaceTable
            caption={t('productionWorkspace.settings.auditCaption')}
            exportFilename="nrg-audit-events.csv"
            headers={[
              t('productionWorkspace.settings.event'),
              t('productionWorkspace.settings.action'),
              t('productionWorkspace.settings.status'),
              t('productionWorkspace.settings.integrity'),
            ]}
            rows={events.slice(0, 8).map((event) => [
              event.id || '',
              event.action || '',
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
          <a
            href="/"
            className="flex min-h-11 items-center gap-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-[var(--nrg-focus)]"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-saffron-600 text-lg font-bold text-white">N</div>
            <div>
              <p className="text-sm font-bold text-nrg-text">{t('productionWorkspace.header.product')}</p>
              <p className="text-xs uppercase tracking-[0.16em] text-nrg-muted">{t('productionWorkspace.header.subtitle')}</p>
            </div>
          </a>
          <div className="flex flex-wrap gap-2 text-xs font-semibold text-nrg-muted">
            {[
              t('productionWorkspace.common.staysInIndia'),
              t('productionWorkspace.common.auditActive'),
              t('productionWorkspace.common.sourceBound'),
            ].map((label) => (
              <span
                key={label}
                className="inline-flex min-h-8 items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 text-emerald-800"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042.133-2.482.478-3.623z"
                  />
                </svg>
                {label}
              </span>
            ))}
          </div>
          <nav aria-label={t('productionWorkspace.header.navLabel')} className="flex gap-2 overflow-x-auto">
            {visibleRoutes.map((route) => {
              const Icon = iconMap[route.screen] || BookOpen
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
        {activeRouteAllowed && screen === 'publications' && (
          <PublicationsScreen data={data} onRetry={() => onRetry('publications')} />
        )}
        {activeRouteAllowed && screen === 'researchers' && (
          <ResearchersScreen user={user} data={data} onRetry={() => onRetry('researchers')} />
        )}
        {activeRouteAllowed && screen === 'reports' && (
          <ReportsScreen data={data} onRetry={() => onRetry('reports')} />
        )}
        {activeRouteAllowed && screen === 'industry' && (
          <IndustryScreen data={data} onRetry={() => onRetry('industry')} />
        )}
        {activeRouteAllowed && screen === 'settings' && (
          <SettingsScreen user={user} data={data} onRetry={() => onRetry('settings')} onLogout={onLogout} />
        )}
      </main>
    </div>
  )
}

export const ProductionWorkspace: React.FC<{ screen: ProductionWorkspaceScreen }> = ({ screen }) => {
  const { user, logout } = useAuth()
  const { data, handleRetry } = useWorkspaceData(screen, user)

  const safeUser = useMemo<AuthUser>(
    () =>
      user || {
        id: 'unknown',
        username: 'unknown',
        role: 'industry',
        tier: 3,
      },
    [user],
  )

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
