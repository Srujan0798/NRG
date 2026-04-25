import React, { useMemo } from 'react'
import { StatsCard } from '../components/StatsCard'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { useAuth } from '../hooks/useAuth'
import { useQuery } from '@tanstack/react-query'
import { t } from '../i18n'
import {
  Activity, Zap, Shield, Database, Clock, TrendingUp,
  AlertTriangle, CheckCircle, Server, Cpu, HardDrive
} from 'lucide-react'

interface MetricsData {
  queries: {
    counts: { by_tier: Record<string, number>; by_intent: Record<string, number>; by_status: Record<string, number> }
    latency_p50_ms: number; latency_p95_ms: number; latency_p99_ms: number
  }
  cache: { hit_rate: number; total_hits: number; total_misses: number }
  mesh: { providers: Record<string, { health: string; calls: number; failures: number; avg_latency_ms: number }>; circuit_trips: Record<string, string> }
  training: { total_pairs: number; by_grade: Record<string, number>; avg_feedback: number | null; exported: number }
  audit: { chain_length: number; chain_valid: boolean }
  slo: { queries_within_sla: number; total_queries: number; compliance_percent: number }
  node_latency: Record<string, { avg_ms: number; p50_ms: number; p95_ms: number; calls: number }>
  infrastructure: { database_pool: { active: number; idle: number; max_size: number }; redis_connected: boolean; qdrant_vectors: number | null }
}

const formatMs = (v: number | undefined) => v !== undefined ? `${v.toFixed(1)}ms` : '—'

const SectionHeader: React.FC<{ icon: React.ReactNode; title: string; subtitle?: string }> = ({ icon, title, subtitle }) => (
  <div className="flex items-center gap-3 mb-4">
    <div className="w-9 h-9 rounded-xl bg-violet-100/80 dark:bg-violet-900/30 border border-violet-200/70 dark:border-violet-700/50 flex items-center justify-center text-violet-600 dark:text-violet-300">
      {icon}
    </div>
    <div>
      <h2 className="text-base font-semibold text-nrg-text">{title}</h2>
      {subtitle && <p className="text-xs text-nrg-muted">{subtitle}</p>}
    </div>
  </div>
)

const TierBadge: React.FC<{ tier: number }> = ({ tier }) => {
  const colors = { 1: 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400', 2: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', 3: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' }
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[tier as keyof typeof colors] || colors[1]}`}>{t("auto.views.MetricsDashboard.1")}{tier}</span>
}

function MetricsSkeleton() {
  return (
    <div className="space-y-6 p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 rounded-2xl bg-[var(--nrg-border)] animate-pulse" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-48 rounded-2xl bg-[var(--nrg-border)] animate-pulse" />
        ))}
      </div>
    </div>
  )
}

export default function MetricsDashboard() {
  const { user } = useAuth()

  const { data, isLoading, error, refetch } = useQuery<MetricsData>({
    queryKey: ['admin-metrics'],
    queryFn: async () => {
      const response = await fetch('/api/metrics', {
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('nrg.auth.session') ? JSON.parse(localStorage.getItem('nrg.auth.session')!).accessToken : ''}`,
        },
      })
      if (!response.ok) throw new Error(`Failed to load metrics: ${response.status}`)
      return response.json()
    },
    refetchInterval: 30_000,
    staleTime: 15_000,
  })

  const sloPercent = data?.slo?.compliance_percent ?? 0
  const sloColor = sloPercent >= 95 ? 'var(--nrg-chart-3)' : sloPercent >= 80 ? 'var(--nrg-chart-4)' : 'var(--nrg-danger)'

  const cacheHitRate = data?.cache?.hit_rate ?? 0

  const providerHealth = useMemo(() => {
    if (!data?.mesh?.providers) return []
    return Object.entries(data.mesh.providers).map(([name, info]) => ({
      name,
      health: info.health,
      calls: info.calls,
      failures: info.failures,
      avgLatency: info.avg_latency_ms,
      failureRate: info.calls > 0 ? (info.failures / info.calls) * 100 : 0,
    }))
  }, [data])

  const circuitTrips = data?.mesh?.circuit_trips ? Object.keys(data.mesh.circuit_trips) : []

  if (!user || (user as any).tier !== 1) {
    return (
      <div className="min-h-screen nrg-app-canvas flex items-center justify-center">
        <div className="text-center">
          <Shield size={48} className="mx-auto mb-4 text-nrg-muted" />
          <h2 className="text-xl font-bold text-nrg-text mb-2">{t("auto.views.MetricsDashboard.2")}</h2>
          <p className="text-sm text-nrg-muted">{t("auto.views.MetricsDashboard.3")}</p>
        </div>
      </div>
    )
  }

  if (isLoading) return <MetricsSkeleton />

  return (
    <ErrorBoundary title={t("auto.views.MetricsDashboard.4")}>
      <div className="min-h-screen nrg-app-canvas">
        <header className="sticky top-0 z-40 bg-[var(--glass-bg)] backdrop-blur-md border-b border-nrg-border">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center shadow-lg">
                <Activity size={20} className="text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-nrg-text font-devanagari">{t("auto.views.MetricsDashboard.5")}</h1>
                <p className="text-xs text-nrg-muted">{t("auto.views.MetricsDashboard.6")}</p>
              </div>
            </div>
            <button
              onClick={() => refetch()}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border border-violet-200/80 dark:border-violet-700/60 bg-violet-100/70 dark:bg-violet-900/20 text-violet-700 dark:text-violet-300 hover:bg-violet-100 transition-colors"
            >
              <Clock size={16} />
              {t("auto.views.MetricsDashboard.7")}</button>
          </div>
        </header>

        <main id="main-content" tabIndex={-1} className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
          {error && (
            <div className="rounded-xl p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 flex items-center gap-3">
              <AlertTriangle size={20} className="text-red-500 shrink-0" />
              <p className="text-sm text-red-700 dark:text-red-400">{(error as Error).message}</p>
              <button onClick={() => refetch()} className="ml-auto text-sm text-red-600 dark:text-red-300 underline">{t("auto.views.MetricsDashboard.8")}</button>
            </div>
          )}

          {/* SLO + Cache overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard
              label={t("auto.views.MetricsDashboard.9")}
              labelHi="SLO अनुपालन"
              value={sloPercent}
              sublabel={`${data?.slo?.queries_within_sla ?? 0} queries within SLA`}
              icon={<TrendingUp size={20} />}
              accentColor={sloColor}
              delay={0}
              format="number"
              data-testid="slo-compliance"
            />
            <StatsCard
              label={t("auto.views.MetricsDashboard.10")}
              labelHi="कैश हिट दर"
              value={Math.round(cacheHitRate * 100)}
              sublabel={`${data?.cache?.total_hits ?? 0} hits / ${(data?.cache?.total_hits ?? 0) + (data?.cache?.total_misses ?? 0)} total`}
              icon={<HardDrive size={20} />}
              accentColor={cacheHitRate > 0.7 ? 'var(--nrg-chart-3)' : 'var(--nrg-chart-4)'}
              delay={100}
              format="number"
              data-testid="cache-hit-rate"
            />
            <StatsCard
              label={t("auto.views.MetricsDashboard.11")}
              labelHi="प्रशिक्षण जोड़े"
              value={data?.training?.total_pairs ?? 0}
              sublabel={`${data?.training?.exported ?? 0} exported`}
              icon={<Database size={20} />}
              accentColor="var(--nrg-chart-5)"
              delay={200}
              format="number"
              data-testid="training-pairs"
            />
            <StatsCard
              label={t("auto.views.MetricsDashboard.12")}
              labelHi="सक्रिय सर्किट"
              value={circuitTrips.length}
              sublabel={circuitTrips.length > 0 ? `Breaker trips: ${circuitTrips.join(', ')}` : 'All providers nominal'}
              icon={<Zap size={20} />}
              accentColor={circuitTrips.length > 0 ? 'var(--nrg-danger)' : 'var(--nrg-chart-3)'}
              delay={300}
              format="number"
              data-testid="active-circuits"
            />
          </div>

          {/* Query latency */}
          <div className="nrg-panel p-5">
            <SectionHeader
              icon={<Activity size={18} />}
              title={t("auto.views.MetricsDashboard.13")}
              subtitle={t("auto.views.MetricsDashboard.14")}
            />
            <div className="grid grid-cols-3 gap-6">
              <div className="text-center">
                  <p className="text-3xl font-bold text-nrg-text font-mono">
                  {formatMs(data?.queries?.latency_p50_ms)}
                </p>
                <p className="text-xs text-nrg-muted mt-1">P50</p>
              </div>
              <div className="text-center">
                  <p className="text-3xl font-bold text-nrg-text font-mono">
                  {formatMs(data?.queries?.latency_p95_ms)}
                </p>
                <p className="text-xs text-nrg-muted mt-1">P95</p>
              </div>
              <div className="text-center">
                  <p className="text-3xl font-bold text-nrg-text font-mono">
                  {formatMs(data?.queries?.latency_p99_ms)}
                </p>
                <p className="text-xs text-nrg-muted mt-1">P99</p>
              </div>
            </div>
            {data?.queries?.counts?.by_tier && (
              <div className="mt-4 pt-4 border-t border-nrg-border/40">
                <div className="flex gap-4 justify-center">
                  {Object.entries(data.queries.counts.by_tier).sort().map(([tier, count]) => (
                    <div key={tier} className="flex items-center gap-2">
                      <TierBadge tier={parseInt(tier)} />
                       <span className="text-sm font-mono text-nrg-text">{Number(count).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Provider health */}
          <div className="nrg-panel p-5">
            <SectionHeader
              icon={<Server size={18} />}
              title={t("auto.views.MetricsDashboard.15")}
              subtitle={t("auto.views.MetricsDashboard.16")}
            />
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-nrg-border/40">
                    <th className="text-left py-2 text-xs font-medium text-nrg-muted uppercase">{t("auto.views.MetricsDashboard.17")}</th>
                    <th className="text-center py-2 text-xs font-medium text-nrg-muted uppercase">{t("auto.views.MetricsDashboard.18")}</th>
                    <th className="text-right py-2 text-xs font-medium text-nrg-muted uppercase">{t("auto.views.MetricsDashboard.19")}</th>
                    <th className="text-right py-2 text-xs font-medium text-nrg-muted uppercase">{t("auto.views.MetricsDashboard.20")}</th>
                    <th className="text-right py-2 text-xs font-medium text-nrg-muted uppercase">{t("auto.views.MetricsDashboard.21")}</th>
                    <th className="text-right py-2 text-xs font-medium text-nrg-muted uppercase">{t("auto.views.MetricsDashboard.22")}</th>
                  </tr>
                </thead>
                <tbody>
                  {providerHealth.map(({ name, health, calls, failures, avgLatency, failureRate }) => (
                    <tr key={name} className="border-b border-nrg-border/30 last:border-0">
                      <td className="py-2.5 font-medium text-nrg-text">{name}</td>
                      <td className="py-2.5 text-center">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                          health === 'healthy' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                          health === 'degraded' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                          'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        }`}>
                          {health === 'healthy' ? <CheckCircle size={12} /> : <AlertTriangle size={12} />}
                          {health}
                        </span>
                      </td>
                      <td className="py-2.5 text-right font-mono text-nrg-muted">{calls.toLocaleString()}</td>
                      <td className="py-2.5 text-right font-mono text-nrg-muted">{failures.toLocaleString()}</td>
                      <td className="py-2.5 text-right font-mono text-nrg-muted">{formatMs(avgLatency)}</td>
                      <td className="py-2.5 text-right">
                        <span className={`font-mono ${failureRate > 10 ? 'text-red-600 dark:text-red-400' : failureRate > 5 ? 'text-amber-600 dark:text-amber-400' : 'text-green-600 dark:text-green-400'}`}>
                          {failureRate.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                  {providerHealth.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-4 text-center text-nrg-muted text-sm">{t("auto.views.MetricsDashboard.23")}</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Training data */}
          <div className="nrg-panel p-5">
            <SectionHeader
              icon={<Cpu size={18} />}
              title={t("auto.views.MetricsDashboard.24")}
              subtitle={t("auto.views.MetricsDashboard.25")}
            />
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {data?.training?.by_grade && Object.entries(data.training.by_grade).map(([grade, count]) => {
                const gradeColors: Record<string, string> = { gold: 'var(--nrg-grade-gold)', silver: 'var(--nrg-grade-silver)', bronze: 'var(--nrg-grade-bronze)', reject: 'var(--nrg-danger)', ungraded: 'var(--nrg-ink-muted)' }
                const color = gradeColors[grade] || 'var(--nrg-ink-muted)'
                return (
                  <div key={grade} className="rounded-xl p-4 text-center" style={{ background: `${color}15` }}>
                    <p className="text-2xl font-bold" style={{ color }}>{Number(count).toLocaleString()}</p>
                    <p className="text-xs font-medium capitalize mt-1 text-nrg-muted">{grade}</p>
                  </div>
                )
              })}
            </div>
            {data?.training?.avg_feedback != null && (
              <p className="mt-4 text-xs text-nrg-muted text-center">{t("auto.views.MetricsDashboard.26")}<span className="font-mono text-nrg-text">{data.training.avg_feedback.toFixed(2)}</span></p>
            )}
          </div>

          {/* Node latency */}
          {data?.node_latency && Object.keys(data.node_latency).length > 0 && (
            <div className="nrg-panel p-5">
              <SectionHeader
                icon={<Clock size={18} />}
                title={t("auto.views.MetricsDashboard.27")}
                subtitle={t("auto.views.MetricsDashboard.28")}
              />
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {Object.entries(data.node_latency)
                  .sort((a, b) => (b[1].avg_ms ?? 0) - (a[1].avg_ms ?? 0))
                  .map(([node, stats]) => (
                    <div key={node} className="rounded-xl p-4 border border-nrg-border/60 bg-[var(--glass-bg)]">
                      <p className="text-sm font-medium text-nrg-text mb-2 truncate">{node}</p>
                      <p className="text-xl font-bold font-mono text-nrg-text">{formatMs(stats.avg_ms)}</p>
                      <p className="text-xs text-nrg-muted mt-0.5">{t("auto.views.MetricsDashboard.29")}{stats.calls.toLocaleString()} {t("auto.views.MetricsDashboard.30")}</p>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Audit chain */}
          <div className="nrg-panel p-5">
            <SectionHeader
              icon={<Shield size={18} />}
              title={t("auto.views.MetricsDashboard.31")}
              subtitle={t("auto.views.MetricsDashboard.32")}
            />
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${data?.audit?.chain_valid ? 'bg-green-100' : 'bg-red-100'}`}>
                {data?.audit?.chain_valid
                  ? <CheckCircle size={24} className="text-green-600" />
                  : <AlertTriangle size={24} className="text-red-600" />}
              </div>
              <div>
                <p className={`text-sm font-semibold ${data?.audit?.chain_valid ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'}`}>
                  {data?.audit?.chain_valid ? 'Chain integrity verified' : 'Chain integrity compromised'}
                </p>
                <p className="text-xs text-nrg-muted mt-0.5">{data?.audit?.chain_length ?? 0} {t("auto.views.MetricsDashboard.33")}{data?.audit?.chain_valid ? 'Yes' : 'No'}</p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </ErrorBoundary>
  )
}
