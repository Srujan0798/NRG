import React from 'react'
import { t } from '../i18n'
import {
  AlertTriangle,
  ArrowUpRight,
  CircleDot,
  Database,
  FileCheck2,
  GitCommit,
  Gauge,
  IndianRupee,
  KeyRound,
  ShieldCheck,
  TimerReset,
  TrendingUp,
  XCircle,
} from 'lucide-react'

type Status = 'pass' | 'partial' | 'fail' | 'blocked'

interface MetricCard {
  label: string
  value: string
  unit?: string
  delta: string
  status: Status
  icon: React.ReactNode
}

interface EvidenceGate {
  gate: string
  value: string
  target: string
  status: Status
}

const statusStyles: Record<Status, { text: string; bg: string; border: string; bar: string; label: string }> = {
  pass: {
    text: 'text-emerald-700',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    bar: 'bg-emerald-500',
    label: 'PASS',
  },
  partial: {
    text: 'text-amber-700',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    bar: 'bg-amber-500',
    label: 'PARTIAL',
  },
  fail: {
    text: 'text-rose-700',
    bg: 'bg-rose-50',
    border: 'border-rose-200',
    bar: 'bg-rose-500',
    label: 'FAIL',
  },
  blocked: {
    text: 'text-stone-700',
    bg: 'bg-stone-100',
    border: 'border-stone-300',
    bar: 'bg-stone-500',
    label: 'BLOCKED',
  },
}

const operatingMetrics: MetricCard[] = [
  {
    label: 'Production readiness',
    value: '6.0',
    unit: '/10',
    delta: 'No UAT sign-off',
    status: 'partial',
    icon: <Gauge size={18} />,
  },
  {
    label: 'Dhairya SQL suite',
    value: '43',
    unit: '/43',
    delta: 'Original 17/17 retained',
    status: 'pass',
    icon: <Database size={18} />,
  },
  {
    label: 'Quality bar',
    value: '5',
    unit: '/6',
    delta: 'C4 SLO skipped',
    status: 'partial',
    icon: <ShieldCheck size={18} />,
  },
  {
    label: 'Security attacks allowed',
    value: '0',
    unit: '/25',
    delta: 'Security set blocked/downgraded',
    status: 'pass',
    icon: <KeyRound size={18} />,
  },
  {
    label: 'Audit chain',
    value: '1',
    unit: 'break',
    delta: 'Hash mismatch remains',
    status: 'fail',
    icon: <XCircle size={18} />,
  },
  {
    label: 'Variable cost',
    value: '₹48',
    unit: '/1k',
    delta: 'Planning estimate',
    status: 'partial',
    icon: <IndianRupee size={18} />,
  },
]

const evidenceGates: EvidenceGate[] = [
  { gate: 'PII security', value: '10 passed', target: '10/10', status: 'pass' },
  { gate: 'Audit binding unit tests', value: '29 passed', target: '29/29', status: 'pass' },
  { gate: 'Egress allowlist', value: '35 passed', target: '35/35', status: 'pass' },
  { gate: 'Multi-hop planner', value: '28 passed', target: '28/28', status: 'pass' },
  { gate: 'Full test suite', value: 'failed + stalled', target: 'green', status: 'fail' },
  { gate: 'C4 load proof', value: '0 requests', target: 'P99 <500ms', status: 'fail' },
  { gate: 'Tier response shaping', value: 'same structure', target: 'distinct T1/T2/T3', status: 'partial' },
]

const trainingRows = [
  { grade: 'Gold', count: 688, color: 'bg-amber-400', share: 18 },
  { grade: 'Silver', count: 417, color: 'bg-slate-400', share: 11 },
  { grade: 'Bronze', count: 2574, color: 'bg-orange-500', share: 66 },
  { grade: 'Reject', count: 240, color: 'bg-rose-500', share: 6 },
]

const blockers = [
  'Repair audit chain hash mismatch from a known-good chain head',
  'Make full test suite green; provider/e2e checks currently fail',
  'Fix Locust task request-context bug so load proof issues real HTTP calls',
  'Make T1/T2/T3 query payloads structurally different at the API layer',
  'Fix LLM mesh typo and run a live provider-kill circuit-breaker proof',
]

const commits = [
  { hash: 'b873b713', label: 'GAP-A DB co-sign trigger' },
  { hash: '527af236', label: 'GAP-B 60s drift scheduler' },
  { hash: '4c743b84', label: 'GAP-C Hall of Shame' },
  { hash: 'bbe6102b', label: 'Red-team closure' },
  { hash: '4d2b2d6a', label: 'v4.1 evidence report' },
]

const goNoGo = [
  { label: 'Professor demo', state: 'Hold', reason: 'audit chain false' },
  { label: 'Ministry red-team', state: 'Hold', reason: 'full suite not green' },
  { label: 'Industry UAT', state: 'Hold', reason: 'tier payloads not distinct' },
  { label: 'Founder dry run', state: 'Go', reason: 'evidence package exists' },
]

const barWidths = {
  readiness: '60%',
  sql: '100%',
  quality: '83%',
  security: '100%',
}

const StatusPill = React.memo(function StatusPill({ status }: { status: Status }) {
  const style = statusStyles[status]
  return (
    <span className={`inline-flex h-7 items-center rounded-full border px-2.5 text-[0.6875rem] font-bold tracking-wide ${style.bg} ${style.border} ${style.text}`}>
      {style.label}
    </span>
  )
})

const MetricTile = React.memo(function MetricTile({ metric, index }: { metric: MetricCard; index: number }) {
  const style = statusStyles[metric.status]
  return (
    <article
      className={`relative min-h-[9.25rem] rounded-lg border bg-white p-4 shadow-sm opacity-0 animate-fade-in-up ${style.border}`}
      style={{ animationDelay: `${index * 45}ms` }}
      data-testid={`founder-metric-${metric.label.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <div className={`absolute left-0 top-0 h-full w-1 rounded-l-lg ${style.bar}`} />
      <div className="flex items-start justify-between gap-3">
        <div className={`flex h-9 w-9 items-center justify-center rounded-md ${style.bg} ${style.text}`}>
          {metric.icon}
        </div>
        <StatusPill status={metric.status} />
      </div>
      <div className="mt-5">
        <p className="text-xs font-semibold uppercase tracking-[0.08em] text-stone-500">{metric.label}</p>
        <div className="mt-1 flex items-baseline gap-1">
          <span className="font-mono text-3xl font-bold text-stone-950">{metric.value}</span>
          {metric.unit && <span className="font-mono text-sm font-semibold text-stone-500">{metric.unit}</span>}
        </div>
        <p className="mt-2 text-sm text-stone-600">{metric.delta}</p>
      </div>
    </article>
  )
})

const ProgressRow = ({ label, width, status }: { label: string; width: string; status: Status }) => (
  <div>
    <div className="mb-2 flex items-center justify-between gap-3">
      <span className="text-sm font-semibold text-stone-800">{label}</span>
      <span className="font-mono text-xs text-stone-500">{width}</span>
    </div>
    <div className="h-2.5 overflow-hidden rounded-full bg-stone-200">
      <div className={`h-full rounded-full ${statusStyles[status].bar}`} style={{ width }} />
    </div>
  </div>
)

export default function FounderDashboard() {
  return (
    <div className="min-h-screen bg-[var(--nrg-founder-paper)] text-stone-950">
      <div className="border-b border-stone-300 bg-[var(--nrg-founder-paper)]/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md border border-stone-900 bg-stone-950 text-sm font-black text-[var(--nrg-founder-paper)]">
              NRG
            </div>
            <div>
              <h1 className="font-display text-xl font-bold leading-tight text-stone-950">{t("auto.views.FounderDashboard.1")}</h1>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-stone-500">{t("auto.views.FounderDashboard.2")}</p>
            </div>
          </div>
          <div className="hidden items-center gap-2 sm:flex">
            <span className="rounded-full border border-rose-300 bg-rose-50 px-3 py-1 text-xs font-bold text-rose-700">{t("auto.views.FounderDashboard.3")}</span>
            <span className="rounded-full border border-stone-300 bg-white px-3 py-1 font-mono text-xs text-stone-600">{t("auto.views.FounderDashboard.4")}</span>
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-lg border border-stone-300 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-stone-500">{t("auto.views.FounderDashboard.5")}</p>
                <h2 className="mt-2 max-w-3xl font-display text-4xl font-bold leading-tight text-stone-950 md:text-5xl">
                  {t("auto.views.FounderDashboard.6")}</h2>
              </div>
              <div className="rounded-md border border-amber-300 bg-amber-50 p-4 md:w-64">
                <div className="flex items-center gap-2 text-amber-800">
                  <AlertTriangle size={18} />
                  <span className="text-sm font-bold">{t("auto.views.FounderDashboard.7")}</span>
                </div>
                <p className="mt-2 text-sm leading-5 text-amber-900">{t("auto.views.FounderDashboard.8")}</p>
              </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-4">
              <ProgressRow label={t("auto.views.FounderDashboard.9")} width={barWidths.readiness} status="partial" />
              <ProgressRow label={t("auto.views.FounderDashboard.10")} width={barWidths.sql} status="pass" />
              <ProgressRow label={t("auto.views.FounderDashboard.11")} width={barWidths.quality} status="partial" />
              <ProgressRow label={t("auto.views.FounderDashboard.12")} width={barWidths.security} status="pass" />
            </div>
          </div>

          <div className="rounded-lg border border-stone-900 bg-stone-950 p-5 text-[var(--nrg-founder-paper)] shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-stone-400">{t("auto.views.FounderDashboard.13")}</p>
                <p className="mt-2 font-mono text-4xl font-bold">₹48</p>
                <p className="text-sm text-stone-300">{t("auto.views.FounderDashboard.14")}</p>
              </div>
              <IndianRupee className="text-emerald-300" size={34} />
            </div>
            <div className="mt-6 grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-md border border-stone-700 p-3">
                <p className="font-mono text-lg font-bold">{t("auto.views.FounderDashboard.15")}</p>
                <p className="text-stone-400">{t("auto.views.FounderDashboard.16")}</p>
              </div>
              <div className="rounded-md border border-stone-700 p-3">
                <p className="font-mono text-lg font-bold">30%</p>
                <p className="text-stone-400">{t("auto.views.FounderDashboard.17")}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {operatingMetrics.map((metric, index) => (
            <MetricTile key={metric.label} metric={metric} index={index} />
          ))}
        </section>

        <section className="mt-4 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="rounded-lg border border-stone-300 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-stone-950">{t("auto.views.FounderDashboard.18")}</h2>
                <p className="text-sm text-stone-500">{t("auto.views.FounderDashboard.19")}</p>
              </div>
              <FileCheck2 className="text-stone-500" size={22} />
            </div>
            <div className="space-y-2">
              {evidenceGates.map((gate) => {
                const style = statusStyles[gate.status]
                return (
                  <div key={gate.gate} className="grid grid-cols-[1fr_auto_auto] items-center gap-3 border-b border-stone-100 py-2 last:border-b-0">
                    <span className="text-sm font-semibold text-stone-800">{gate.gate}</span>
                    <span className="font-mono text-xs text-stone-500">{gate.value}</span>
                    <span className={`rounded-full px-2 py-1 text-[0.625rem] font-bold ${style.bg} ${style.text}`}>{gate.target}</span>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="rounded-lg border border-stone-300 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-stone-950">{t("auto.views.FounderDashboard.20")}</h2>
                <p className="text-sm text-stone-500">{t("auto.views.FounderDashboard.21")}</p>
              </div>
              <CircleDot className="text-stone-500" size={22} />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {goNoGo.map((item) => {
                const isGo = item.state === 'Go'
                return (
                  <div key={item.label} className={`rounded-md border p-3 ${isGo ? 'border-emerald-200 bg-emerald-50' : 'border-rose-200 bg-rose-50'}`}>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-bold text-stone-900">{item.label}</span>
                      <span className={`font-mono text-xs font-bold ${isGo ? 'text-emerald-700' : 'text-rose-700'}`}>{item.state}</span>
                    </div>
                    <p className="mt-2 text-sm text-stone-600">{item.reason}</p>
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        <section className="mt-4 grid gap-4 lg:grid-cols-3">
          <div className="rounded-lg border border-stone-300 bg-white p-5 shadow-sm lg:col-span-2">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-stone-950">{t("auto.views.FounderDashboard.22")}</h2>
                <p className="text-sm text-stone-500">{t("auto.views.FounderDashboard.23")}</p>
              </div>
              <TrendingUp className="text-stone-500" size={22} />
            </div>
            <div className="flex h-10 overflow-hidden rounded-md bg-stone-200">
              {trainingRows.map((row) => (
                <div key={row.grade} className={`${row.color}`} style={{ width: `${row.share}%` }} />
              ))}
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {trainingRows.map((row) => (
                <div key={row.grade} className="flex items-center gap-2">
                  <span className={`h-3 w-3 rounded-sm ${row.color}`} />
                  <div>
                    <p className="font-mono text-sm font-bold text-stone-900">{row.count.toLocaleString()}</p>
                    <p className="text-xs text-stone-500">{row.grade}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-stone-300 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-stone-950">{t("auto.views.FounderDashboard.24")}</h2>
                <p className="text-sm text-stone-500">{t("auto.views.FounderDashboard.25")}</p>
              </div>
              <GitCommit className="text-stone-500" size={22} />
            </div>
            <div className="space-y-3">
              {commits.map((commit) => (
                <div key={commit.hash} className="flex items-start gap-3">
                  <span className="mt-1 h-2 w-2 rounded-full bg-stone-900" />
                  <div>
                    <p className="font-mono text-xs font-bold text-stone-900">{commit.hash}</p>
                    <p className="text-sm text-stone-600">{commit.label}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-4 rounded-lg border border-rose-300 bg-rose-50 p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2 text-rose-800">
            <TimerReset size={20} />
            <h2 className="text-lg font-bold">{t("auto.views.FounderDashboard.26")}</h2>
          </div>
          <div className="grid gap-3 md:grid-cols-5">
            {blockers.map((blocker, index) => (
              <div key={blocker} className="min-h-28 rounded-md border border-rose-200 bg-white p-3">
                <div className="mb-3 flex h-7 w-7 items-center justify-center rounded-full bg-rose-600 font-mono text-xs font-bold text-white">{index + 1}</div>
                <p className="text-sm font-semibold leading-5 text-stone-800">{blocker}</p>
              </div>
            ))}
          </div>
        </section>

        <footer className="flex flex-col gap-3 py-6 text-xs text-stone-500 sm:flex-row sm:items-center sm:justify-between">
          <span>{t("auto.views.FounderDashboard.27")}</span>
          <span className="inline-flex items-center gap-1 font-semibold text-stone-700">
            {t("auto.views.FounderDashboard.28")}<ArrowUpRight size={13} />
          </span>
        </footer>
      </main>
    </div>
  )
}
