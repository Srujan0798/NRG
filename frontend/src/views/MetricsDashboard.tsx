import React, { useState, useCallback, useMemo } from 'react'
import { motion } from 'framer-motion'
import { StatsCard } from '../components/StatsCard'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { useAuth } from '../hooks/useAuth'
import { useQuery } from '@tanstack/react-query'
import {
  Activity, Zap, Shield, Database, Clock, TrendingUp,
  AlertTriangle, CheckCircle, Server, Cpu, HardDrive, Users
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
const formatPct = (v: number) => `${v.toFixed(1)}%`

const SectionHeader: React.FC<{ icon: React.ReactNode; title: string; subtitle?: string }> = ({ icon, title, subtitle }) => (
  <div className="flex items-center gap-3 mb-4">
    <div className="w-9 h-9 rounded-xl bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center text-violet-600 dark:text-violet-400">
      {icon}
    </div>
    <div>
      <h2 className="text-base font-semibold text-slate-900 dark:text-white">{title}</h2>
      {subtitle && <p className="text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>}
    </div>
  </div>
)

const TierBadge: React.FC<{ tier: number }> = ({ tier }) => {
  const colors = { 1: 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400', 2: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', 3: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' }
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[tier as keyof typeof colors] || colors[1]}`}>Tier {tier}</span>
}

function MetricsSkeleton() {
  return (
    <div className="space-y-6 p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 rounded-2xl bg-slate-200 dark:bg-navy-700 animate-pulse" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-48 rounded-2xl bg-slate-200 dark:bg-navy-700 animate-pulse" />
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
  const sloColor = sloPercent >= 95 ? '#10b981' : sloPercent >= 80 ? '#c49538' : '#ef4444'

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
      <div className="min-h-screen bg-slate-50 dark:bg-navy-900 flex items-center justify-center">
        <div className="text-center">
          <Shield size={48} className="mx-auto mb-4 text-slate-400" />
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Admin Access Required</h2>
          <p className="text-sm text-slate-500">Only Tier 1 (Researcher) administrators can view system metrics.</p>
        </div>
      </div>
    )
  }

  if (isLoading) return <MetricsSkeleton />

  return (
    <ErrorBoundary title="Metrics Dashboard failed to load">
      <div className="min-h-screen bg-slate-50 dark:bg-navy-900">
        <header className="sticky top-0 z-40 bg-white/95 dark:bg-navy-800/95 backdrop-blur-md border-b border-slate-200 dark:border-navy-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center shadow-lg">
                <Activity size={20} className="text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-900 dark:text-white font-devanagari">System Metrics</h1>
                <p className="text-xs text-slate-500 dark:text-slate-400">Admin Dashboard · System Observability</p>
              </div>
            </div>
            <button
              onClick={() => refetch()}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400 hover:bg-violet-200 transition-colors"
            >
              <Clock size={16} />
              Refresh
            </button>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
          {error && (
            <div className="rounded-xl p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 flex items-center gap-3">
              <AlertTriangle size={20} className="text-red-500 shrink-0" />
              <p className="text-sm text-red-700 dark:text-red-400">{(error as Error).message}</p>
              <button onClick={() => refetch()} className="ml-auto text-sm text-red-600 dark:text-red-300 underline">Retry</button>
            </div>
          )}

          {/* SLO + Cache overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard
              label="SLO Compliance"
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
              label="Cache Hit Rate"
              labelHi="कैश हिट दर"
              value={Math.round(cacheHitRate * 100)}
              sublabel={`${data?.cache?.total_hits ?? 0} hits / ${(data?.cache?.total_hits ?? 0) + (data?.cache?.total_misses ?? 0)} total`}
              icon={<HardDrive size={20} />}
              accentColor={cacheHitRate > 0.7 ? '#10b981' : '#c49538'}
              delay={100}
              format="number"
              data-testid="cache-hit-rate"
            />
            <StatsCard
              label="Training Pairs"
              labelHi="प्रशिक्षण जोड़े"
              value={data?.training?.total_pairs ?? 0}
              sublabel={`${data?.training?.exported ?? 0} exported`}
              icon={<Database size={20} />}
              accentColor="#6366f1"
              delay={200}
              format="number"
              data-testid="training-pairs"
            />
            <StatsCard
              label="Active Circuits"
              labelHi="सक्रिय सर्किट"
              value={circuitTrips.length}
              sublabel={circuitTrips.length > 0 ? `Breaker trips: ${circuitTrips.join(', ')}` : 'All providers nominal'}
              icon={<Zap size={20} />}
              accentColor={circuitTrips.length > 0 ? '#ef4444' : '#10b981'}
              delay={300}
              format="number"
              data-testid="active-circuits"
            />
          </div>

          {/* Query latency */}
          <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md p-5">
            <SectionHeader
              icon={<Activity size={18} />}
              title="Query Latency"
              subtitle="End-to-end latency percentiles"
            />
            <div className="grid grid-cols-3 gap-6">
              <div className="text-center">
                <p className="text-3xl font-bold text-slate-900 dark:text-white font-mono">
                  {formatMs(data?.queries?.latency_p50_ms)}
                </p>
                <p className="text-xs text-slate-500 mt-1">P50</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-slate-900 dark:text-white font-mono">
                  {formatMs(data?.queries?.latency_p95_ms)}
                </p>
                <p className="text-xs text-slate-500 mt-1">P95</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-slate-900 dark:text-white font-mono">
                  {formatMs(data?.queries?.latency_p99_ms)}
                </p>
                <p className="text-xs text-slate-500 mt-1">P99</p>
              </div>
            </div>
            {data?.queries?.counts?.by_tier && (
              <div className="mt-4 pt-4 border-t border-slate-100 dark:border-navy-700">
                <div className="flex gap-4 justify-center">
                  {Object.entries(data.queries.counts.by_tier).sort().map(([tier, count]) => (
                    <div key={tier} className="flex items-center gap-2">
                      <TierBadge tier={parseInt(tier)} />
                      <span className="text-sm font-mono text-slate-700 dark:text-slate-300">{Number(count).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Provider health */}
          <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md p-5">
            <SectionHeader
              icon={<Server size={18} />}
              title="Provider Health"
              subtitle="LLM provider call stats and circuit breaker state"
            />
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-navy-700">
                    <th className="text-left py-2 text-xs font-medium text-slate-500 uppercase">Provider</th>
                    <th className="text-center py-2 text-xs font-medium text-slate-500 uppercase">Health</th>
                    <th className="text-right py-2 text-xs font-medium text-slate-500 uppercase">Calls</th>
                    <th className="text-right py-2 text-xs font-medium text-slate-500 uppercase">Failures</th>
                    <th className="text-right py-2 text-xs font-medium text-slate-500 uppercase">Avg Latency</th>
                    <th className="text-right py-2 text-xs font-medium text-slate-500 uppercase">Failure Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {providerHealth.map(({ name, health, calls, failures, avgLatency, failureRate }) => (
                    <tr key={name} className="border-b border-slate-50 dark:border-navy-700/50 last:border-0">
                      <td className="py-2.5 font-medium text-slate-900 dark:text-white">{name}</td>
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
                      <td className="py-2.5 text-right font-mono text-slate-600 dark:text-slate-400">{calls.toLocaleString()}</td>
                      <td className="py-2.5 text-right font-mono text-slate-600 dark:text-slate-400">{failures.toLocaleString()}</td>
                      <td className="py-2.5 text-right font-mono text-slate-600 dark:text-slate-400">{formatMs(avgLatency)}</td>
                      <td className="py-2.5 text-right">
                        <span className={`font-mono ${failureRate > 10 ? 'text-red-600 dark:text-red-400' : failureRate > 5 ? 'text-amber-600 dark:text-amber-400' : 'text-green-600 dark:text-green-400'}`}>
                          {failureRate.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                  {providerHealth.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-4 text-center text-slate-400 text-sm">No provider data available</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Training data */}
          <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md p-5">
            <SectionHeader
              icon={<Cpu size={18} />}
              title="Training Pipeline"
              subtitle="Fine-tuning data quality distribution"
            />
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {data?.training?.by_grade && Object.entries(data.training.by_grade).map(([grade, count]) => {
                const gradeColors: Record<string, string> = { gold: '#ffd700', silver: '#c0c0c0', bronze: '#cd7f32', reject: '#ef4444', ungraded: '#94a3b8' }
                const color = gradeColors[grade] || '#94a3b8'
                return (
                  <div key={grade} className="rounded-xl p-4 text-center" style={{ background: `${color}15` }}>
                    <p className="text-2xl font-bold" style={{ color }}>{Number(count).toLocaleString()}</p>
                    <p className="text-xs font-medium capitalize mt-1 text-slate-600 dark:text-slate-400">{grade}</p>
                  </div>
                )
              })}
            </div>
            {data?.training?.avg_feedback != null && (
              <p className="mt-4 text-xs text-slate-500 text-center">Average feedback score: <span className="font-mono text-slate-700 dark:text-slate-300">{data.training.avg_feedback.toFixed(2)}</span></p>
            )}
          </div>

          {/* Node latency */}
          {data?.node_latency && Object.keys(data.node_latency).length > 0 && (
            <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md p-5">
              <SectionHeader
                icon={<Clock size={18} />}
                title="Node Latency"
                subtitle="Orchestration node timing breakdown"
              />
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {Object.entries(data.node_latency)
                  .sort((a, b) => (b[1].avg_ms ?? 0) - (a[1].avg_ms ?? 0))
                  .map(([node, stats]) => (
                    <div key={node} className="rounded-xl p-4 border border-slate-100 dark:border-navy-700">
                      <p className="text-sm font-medium text-slate-900 dark:text-white mb-2 truncate">{node}</p>
                      <p className="text-xl font-bold font-mono text-slate-900 dark:text-white">{formatMs(stats.avg_ms)}</p>
                      <p className="text-xs text-slate-400 mt-0.5">avg · {stats.calls.toLocaleString()} calls</p>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Audit chain */}
          <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md p-5">
            <SectionHeader
              icon={<Shield size={18} />}
              title="Audit Chain"
              subtitle="Tampering detection and chain integrity"
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
                <p className="text-xs text-slate-500 mt-0.5">{data?.audit?.chain_length ?? 0} entries · Valid: {data?.audit?.chain_valid ? 'Yes' : 'No'}</p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </ErrorBoundary>
  )
}