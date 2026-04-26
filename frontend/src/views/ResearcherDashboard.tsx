import React, { useState, useCallback, useEffect } from 'react'
import { motion } from 'framer-motion'
import { TierBadge } from '../components/TierBadge'
import { SkeletonLoader } from '../components/Skeleton/SkeletonLoader'
import { DPDPConsentDialog } from '../components/DPDPConsentDialog'
import { DPDPAuditLog } from '../components/DPDPAuditLog'
import { SecurityMonitor } from '../components/SecurityMonitor'
import { ConsentBanner } from '../components/ConsentBanner'
import { DPDPPanel } from '../components/DPDPPanel'
import { GlassCard } from '../components/GlassCard'
import { AnswerPanel } from '../components/AnswerPanel/AnswerPanel'
import { EmptyState } from '../components/EmptyState/EmptyState'
import { GraphView } from '../components/GraphView/GraphView'
import { PersonaToggle } from '../components/PersonaToggle'
import { QueryPhaseProgress } from '../components/QueryPhaseProgress'
import { StatsCard } from '../components/StatsCard/StatsCard'
import { ErrorState } from '../components/ErrorState/ErrorState'
import { ErrorBoundary, WidgetErrorBoundary } from '../components/ErrorBoundary/ErrorBoundary'
import { ResearchAreasBarChart } from '../components/DataViz/ResearchAreasBarChart'
import { useAuth } from '../hooks/useAuth'
import MetricsDashboard from './MetricsDashboard'
import { useQueryStore } from '../stores/queryStore'
import { useDPDPStore } from '../stores/dpdpStore'
import { queryService, GraphNode, QueryResponse } from '../services/queryService'
import { getDashboardDocumentTitle, getQueryStatusCopy } from '../utils/dashboardCopy'
import { buildRelaxedQuery, isEmptyResultResponse } from '../utils/emptyResults'
import { useQuery } from '@tanstack/react-query'
import {
  Search, Users, FileText, Building,
  Sun as SunIcon, Moon as MoonIcon, BookOpen, History, LogOut
} from 'lucide-react'
import type { Theme } from '../hooks/useTheme'
import { t } from '../i18n'

interface ResearcherDashboardProps {
  onThemeToggle: () => void
  theme: Theme
}

const TABS = [
  { key: 'dashboard', label: 'Dashboard', labelHi: 'डैशबोर्ड', icon: '📊' },
  { key: 'graph', label: 'Knowledge Graph', labelHi: 'ज्ञान ग्राफ', icon: '🕸️' },
  { key: 'dpdp', label: 'Data Rights', labelHi: 'डेटा अधिकार', icon: '🔒' },
  { key: 'audit', label: 'Audit Log', labelHi: 'ऑडिट लॉग', icon: '📋' },
  { key: 'admin', label: 'Admin', labelHi: 'एडमिन', icon: '📈', tier: 1 },
] as const

const DEMO_QUERY_SUGGESTIONS = [
  'Which institutes in India have the highest grant amount in renewable energy?',
  'Compare AI research output between Gujarat and Karnataka over the last 5 years',
  'Show me the research network around hydrogen fuel cells',
]

const SaffronSpinner = ({ style }: { style?: React.CSSProperties }) => (
  <div
    className="w-9 h-9 rounded-full border-3 border-saffron-200 border-t-saffron-500 animate-spin"
    style={style}
  />
)

const toFriendlyQueryError = (err: any): string => {
  const status = err?.response?.status
  const detail = String(err?.response?.data?.detail || err?.message || '')
  const lower = detail.toLowerCase()
  if (status === 403) return 'Access restricted for your tier. This data is not available in your workspace.'
  if (status === 422 || lower.includes('pii') || lower.includes('aadhaar') || lower.includes('security violation')) {
    return 'This query contains sensitive information that cannot be processed.'
  }
  if (status === 429) return "You've made too many requests. Please wait a moment."
  if (status >= 500) return 'NRG could not complete this request. Your audit trail is safe; refine the query or retry.'
  if (lower.includes('network') || lower.includes('timeout')) return 'NRG cannot reach the evidence service right now. Your audit trail is safe.'
  return detail || 'NRG could not complete this request. Your audit trail is safe; refine the query or retry.'
}

export function ResearcherDashboard({ onThemeToggle, theme }: ResearcherDashboardProps) {
  const { user, logout } = useAuth()
  const {
    history, currentQuery, isSearching,
    setCurrentQuery, addToHistory, setIsSearching, setLastResult,
  } = useQueryStore()
  const { grantConsent, addAuditEntry, getConsentStatus } = useDPDPStore()

  const hasExistingConsent = getConsentStatus('research_access')?.granted
  const [showDPDPConsent, setShowDPDPConsent] = useState(!hasExistingConsent)
  const [activeTab, setActiveTab] = useState<typeof TABS[number]['key']>('dashboard')
  const [graphData, setGraphData] = useState(queryService.emptyGraphData())
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [queryError, setQueryError] = useState<string | null>(null)
  const [queryValidation, setQueryValidation] = useState<string | null>(null)
  const [isSlowQuery, setIsSlowQuery] = useState(false)
  const [conversationTurns, setConversationTurns] = useState<Array<{ query: string; result: QueryResponse }>>([])
  const [graphTopic, setGraphTopic] = useState('machine learning')

  const { data: publicationsData, isLoading: pubsLoading } = useQuery({
    queryKey: ['publications', user?.id],
    queryFn: () => queryService.fetchPublications(10),
    staleTime: 5 * 60 * 1000,
    enabled: !!user,
  })

  const { data: statsData } = useQuery({
    queryKey: ['stats', user?.id],
    queryFn: () => queryService.fetchStats(),
    staleTime: 30 * 1000,
    enabled: !!user,
  })

  const { data: graphApiData } = useQuery({
    queryKey: ['graph', graphTopic, user?.id],
    queryFn: () => queryService.fetchGraphData(graphTopic),
    staleTime: 30 * 1000,
    enabled: !!user && activeTab === 'graph',
  })

  useEffect(() => {
    if (graphApiData) {
      setGraphData(graphApiData)
    }
  }, [graphApiData])

  useEffect(() => {
    document.title = getDashboardDocumentTitle('researcher', activeTab)
  }, [activeTab])

  const publications = publicationsData?.publications || []

  const consentExpiringCount = useDPDPStore((s) => {
    const threshold = Date.now() + 30 * 24 * 60 * 60 * 1000;
    return Object.values(s.consents).filter((c) => c.expiresAt && c.expiresAt < threshold && c.granted).length;
  })

  const handleSearch = useCallback(async () => {
    const submittedQuery = currentQuery.trim()
    if (!submittedQuery) {
      setQueryValidation('Enter a research question before searching.')
      return
    }
    setQueryValidation(null)
    if (/research network|knowledge graph|graph around|network around/i.test(submittedQuery)) {
      setGraphTopic(submittedQuery.replace(/show me|research network around|knowledge graph around/gi, '').trim() || submittedQuery)
      setActiveTab('graph')
      addToHistory({ query: submittedQuery, persona: 'researcher', resultsCount: 1 })
      addAuditEntry({ action: 'data_accessed', persona: 'researcher', details: `Graph query: ${submittedQuery}` })
      return
    }
    setIsSearching(true)
    setQueryError(null)
    setIsSlowQuery(false)
    const slowTimer = window.setTimeout(() => setIsSlowQuery(true), 5000)
    try {
      const result = await queryService.query({ query: submittedQuery })
      setConversationTurns((turns) => [...turns, { query: submittedQuery, result }])
      setLastResult(result)
      addToHistory({ query: submittedQuery, persona: 'researcher', resultsCount: result.verification_status ? 10 : 0 })
      addAuditEntry({ action: 'data_accessed', persona: 'researcher', details: `Query: ${submittedQuery}` })
    } catch (err: any) {
      const message = toFriendlyQueryError(err)
      setQueryError(message)
      addToHistory({ query: submittedQuery, persona: 'researcher', resultsCount: 0, error: message })
    } finally {
      window.clearTimeout(slowTimer)
      setIsSearching(false)
      setIsSlowQuery(false)
    }
  }, [currentQuery, addToHistory, addAuditEntry, setIsSearching, setLastResult])

  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node)
    setCurrentQuery(node.label)
  }, [setCurrentQuery])

  const handleRetry = useCallback(() => {
    setQueryError(null)
    handleSearch()
  }, [handleSearch])

  const pieColors = ['var(--nrg-chart-1)', 'var(--nrg-chart-2)', 'var(--nrg-chart-3)', 'var(--nrg-chart-4)', 'var(--nrg-chart-5)']
  const researchAreaChartData = (statsData?.research_area_distribution || []).slice(0, 6).map((a: any) => ({
    area: a.area?.length > 12 ? a.area.slice(0, 10) + '…' : a.area,
    count: a.count,
  }))

  return (
    <ErrorBoundary title={t("auto.views.ResearcherDashboard.1")}>
      <div className="nrg-app-canvas min-h-screen">
      <header className="sticky top-0 z-40 bg-[var(--glass-bg)] backdrop-blur-xl border-b border-nrg-border">
        <div className="h-1 w-full bg-gradient-to-r from-violet-600 via-violet-400 to-navy-300" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <motion.div
              className="w-11 h-11 rounded-2xl bg-gradient-to-br from-violet-500 via-violet-600 to-navy-500 flex items-center justify-center shadow-lg"
              whileHover={{ scale: 1.05, rotate: 4 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
            >
              <span className="text-white font-display text-lg">न</span>
            </motion.div>
            <div>
              <h1 className="text-lg font-bold text-nrg-text font-devanagari">राष्ट्रीय गवेषण मंच</h1>
              <p className="text-xs uppercase tracking-[0.16em] text-nrg-muted">{t("auto.views.ResearcherDashboard.2")}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <PersonaToggle />
            {user && <TierBadge tier={user.tier} role={user.role} />}
            <motion.button
              onClick={onThemeToggle}
              className="w-10 h-10 rounded-xl border border-nrg-border flex items-center justify-center text-nrg-muted hover:text-violet-500 hover:border-violet-300 transition-all duration-200"
              aria-label={t("auto.views.ResearcherDashboard.3")}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
            </motion.button>
            <motion.button
              onClick={logout}
              className="h-10 px-3 rounded-xl border border-nrg-border flex items-center gap-2 text-sm font-semibold text-nrg-muted hover:text-rose-600 hover:border-rose-300 transition-all duration-200"
              aria-label={t("auto.views.ResearcherDashboard.4")}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <LogOut size={16} />
              <span className="hidden sm:inline">{t("auto.views.ResearcherDashboard.5")}</span>
            </motion.button>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-2 -mb-px overflow-x-auto pb-1">
          {TABS.map((tab) => {
            if ('tier' in tab && tab.tier !== undefined && (user?.tier ?? 0) < tab.tier) return null
            return (
              <motion.button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                aria-label={`${tab.label}, ${tab.labelHi} tab`}
                aria-current={activeTab === tab.key ? 'page' : undefined}
                className={`nrg-tab flex items-center gap-1.5 whitespace-nowrap rounded-t-xl ${
                  activeTab === tab.key
                    ? 'active'
                    : 'text-nrg-muted hover:text-nrg-text'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                data-testid={`tab-${tab.key}`}
              >
                <span aria-hidden="true">{tab.icon}</span>
                {tab.label}
                <span className="text-xs font-devanagari text-nrg-muted ml-1">{tab.labelHi}</span>
              </motion.button>
            )
          })}
        </div>
      </header>

      <ConsentBanner
        role="researcher"
        onManageConsent={() => setActiveTab('dpdp')}
        expiringCount={consentExpiringCount}
      />

      <main id="main-content" tabIndex={-1} className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 relative z-10">
        {activeTab === 'dashboard' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="nrg-panel p-4 sm:p-5">
              <div className="mb-4 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div className="flex items-center gap-2">
                  <Search size={18} className="text-violet-500" />
                  <div>
                    <h2 className="text-sm font-semibold text-nrg-text">{t("auto.views.ResearcherDashboard.6")}</h2>
                    <p className="text-xs text-nrg-muted">{t("auto.views.ResearcherDashboard.7")}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2" aria-label={t("auto.views.ResearcherDashboard.8")}>
                  {DEMO_QUERY_SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => {
                        setCurrentQuery(suggestion)
                        setQueryValidation(null)
                      }}
                      className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1.5 text-xs font-medium text-violet-700 transition hover:border-violet-300 hover:bg-violet-100 dark:border-violet-800 dark:bg-violet-950/30 dark:text-violet-200"
                    >
                      {suggestion.length > 58 ? `${suggestion.slice(0, 56)}...` : suggestion}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row">
                <label htmlFor="researcher-search-input" className="sr-only">{t("auto.views.ResearcherDashboard.9")}</label>
                <input
                  id="researcher-search-input"
                  type="text"
                  value={currentQuery}
                  onChange={(e) => {
                    setCurrentQuery(e.target.value)
                    if (queryValidation) setQueryValidation(null)
                  }}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder={t("auto.views.ResearcherDashboard.10")}
                  className="nrg-input min-h-12 flex-1"
                  data-testid="researcher-search-input"
                />
                <motion.button
                  onClick={handleSearch}
                  disabled={isSearching || !currentQuery.trim()}
                  className="nrg-btn-primary min-h-12 w-full px-6 py-3 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  data-testid="researcher-search-submit"
                >
                  {isSearching ? (
                    <span className="flex items-center gap-2">
                      <SaffronSpinner style={{ width: 16, height: 16, borderWidth: 2 }} />
                      {t("auto.views.ResearcherDashboard.11")}</span>
                  ) : (
                    'Search'
                  )}
                </motion.button>
              </div>
              {queryValidation && (
                <p className="mt-2 text-sm text-rose-600" role="alert">{queryValidation}</p>
              )}

              {isSearching && (
                <div className="mt-4" aria-label={t("auto.views.ResearcherDashboard.12")}>
                  <QueryPhaseProgress domain="research" isSlowQuery={isSlowQuery} />
                  <p className="mt-2 text-xs text-nrg-muted">{getQueryStatusCopy({ isSlowQuery, domain: 'research' })}</p>
                </div>
              )}

              {queryError && (
                <div className="mt-4">
                  <ErrorState
                    title={t("auto.views.ResearcherDashboard.13")}
                    message={queryError}
                    severity="error"
                    onRetry={handleRetry}
                  />
                </div>
              )}

              {conversationTurns.length > 0 && !queryError && (
                <div className="mt-4 space-y-4">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-nrg-text">{t("auto.views.ResearcherDashboard.14")}</h3>
                      <p className="text-xs text-nrg-muted">{t("auto.views.ResearcherDashboard.15")}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setConversationTurns([])
                        setQueryError(null)
                        setCurrentQuery('')
                      }}
                      className="min-h-10 rounded-lg border border-nrg-border px-3 py-1.5 text-xs font-medium text-nrg-muted transition-colors hover:border-violet-300 hover:text-violet-600"
                    >
                      {t("auto.views.ResearcherDashboard.16")}</button>
                  </div>
                  {conversationTurns.map((turn, index) => (
                    <div key={`${turn.result.query_id}-${index}`} className="rounded-2xl border border-nrg-border overflow-hidden">
                      <div className="px-4 py-3 bg-[var(--glass-bg)] border-b border-nrg-border">
                        <p className="text-xs font-semibold text-nrg-muted">{t("auto.views.ResearcherDashboard.17")}{index + 1}</p>
                        <p className="text-sm text-nrg-text">{turn.query}</p>
                      </div>
                      <div className="p-4">
                        {isEmptyResultResponse(turn.result.response) ? (
                          <EmptyState
                            onPrimary={() => setCurrentQuery(buildRelaxedQuery(turn.query))}
                            onSecondary={() => setCurrentQuery(turn.query)}
                          />
                        ) : (
                          <AnswerPanel
                            response={turn.result.response}
                            citations={turn.result.citations || []}
                            provenance={turn.result.provenance}
                            warnings={turn.result.warnings}
                            verification_status={turn.result.verification_status}
                            answer_confidence={turn.result.answer_confidence}
                          />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <WidgetErrorBoundary title={t("auto.views.ResearcherDashboard.18")}>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatsCard
                  label={t("auto.views.ResearcherDashboard.19")}
                  labelHi="कुल शोधकर्ता"
                  value={statsData?.total_researchers ?? 5615}
                  sublabel="Across 181 institutions"
                  accentColor="var(--nrg-chart-5)"
                  icon={<Users size={20} />}
                  delay={0}
                  data-testid="stat-researchers"
                />
                <StatsCard
                  label={t("auto.views.ResearcherDashboard.20")}
                  labelHi="प्रकाशन"
                  value={statsData?.total_publications ?? 12847}
                  sublabel="Peer-reviewed works"
                  accentColor="var(--nrg-chart-2)"
                  icon={<FileText size={20} />}
                  delay={100}
                  data-testid="stat-publications"
                />
                <StatsCard
                  label={t("auto.views.ResearcherDashboard.21")}
                  labelHi="संस्थान"
                  value={statsData?.total_institutions ?? 181}
                  sublabel="Academic + Research"
                  accentColor="var(--nrg-chart-3)"
                  icon={<Building size={20} />}
                  delay={200}
                  data-testid="stat-institutions"
                />
                <StatsCard
                  label={t("auto.views.ResearcherDashboard.22")}
                  labelHi="आपके प्रश्न"
                  value={history.length}
                  sublabel="This session"
                  accentColor="var(--nrg-chart-1)"
                  icon={<History size={20} />}
                  delay={300}
                  data-testid="stat-queries"
                />
              </div>
            </WidgetErrorBoundary>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="space-y-4">
                <GlassCard accent="researcher" title={t("auto.views.ResearcherDashboard.23")} description={t("auto.views.ResearcherDashboard.24")}>
                  {pubsLoading ? (
                    <SkeletonLoader type="list" count={4} />
                  ) : publications.length > 0 ? (
                    <div className="space-y-2 max-h-64 overflow-y-auto scrollbar-nrg">
                      {publications.map((pub: any, i: number) => (
                        <motion.div
                          key={i}
                          className="flex items-center gap-3 p-3 rounded-xl border border-nrg-border/60 bg-[var(--glass-bg)] hover:border-violet-200 hover:bg-violet-50/50 dark:hover:border-violet-700 transition-all cursor-pointer"
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.06 }}
                          whileHover={{ x: 4 }}
                        >
                          <div className="w-8 h-8 rounded-lg bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400 flex items-center justify-center text-sm font-bold">
                            {pub.year?.toString().slice(-2) || '?'}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-nrg-text truncate">{pub.title}</p>
                            <p className="text-xs text-nrg-muted">{typeof pub.authors === 'string' ? pub.authors.split(',').slice(0, 2).join(', ') : Array.isArray(pub.authors) ? pub.authors.slice(0, 2).join(', ') : ''}</p>
                          </div>
                          <div className="text-right shrink-0">
                            <p className="text-xs font-semibold text-violet-600 dark:text-violet-400">{pub.citations || 0}</p>
                            <p className="text-xs text-nrg-muted">{t("auto.views.ResearcherDashboard.25")}</p>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-10 text-nrg-muted">
                      <BookOpen size={40} className="mx-auto mb-3 opacity-50" />
                      <p className="text-sm">{t("auto.views.ResearcherDashboard.26")}</p>
                    </div>
                  )}
                </GlassCard>
              </div>

              <div className="lg:col-span-2 space-y-4">
                {researchAreaChartData.length > 0 && (
                  <ResearchAreasBarChart
                    data={researchAreaChartData.map((d, i) => ({ ...d, color: pieColors[i % pieColors.length] }))}
                    title={t("auto.views.ResearcherDashboard.27")}
                    titleHi="शीर्ष शोध क्षेत्र"
                    subtitle={t("auto.views.ResearcherDashboard.28")}
                  />
                )}

                {history.length > 0 && (
                  <GlassCard accent="sovereign" title={t("auto.views.ResearcherDashboard.29")} description={t("auto.views.ResearcherDashboard.30")}>
                    <div className="space-y-2 max-h-48 overflow-y-auto scrollbar-nrg">
                      {history.slice(0, 6).map((entry) => (
                        <div key={entry.id} className="flex items-center gap-3 py-2 border-b border-nrg-border/40 last:border-0">
                          <div className={`w-2 h-2 rounded-full shrink-0 ${entry.error ? 'bg-red-400' : 'bg-violet-400'}`} />
                          <span className="flex-1 text-sm text-nrg-text truncate font-medium">{entry.query}</span>
                          <span className="text-xs text-nrg-muted shrink-0">
                            {new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                          <span className={`text-xs font-medium shrink-0 ${entry.error ? 'text-red-500' : 'text-green-600'}`}>
                            {entry.error ? 'Failed' : `${entry.resultsCount} results`}
                          </span>
                        </div>
                      ))}
                    </div>
                  </GlassCard>
                )}
              </div>
            </div>

            <SecurityMonitor />
          </motion.div>
        )}

        {activeTab === 'graph' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <WidgetErrorBoundary title={t("auto.views.ResearcherDashboard.31")}>
              <GraphView
                data={graphData}
                width={1100}
                height={600}
                onNodeClick={handleNodeClick}
                availableYears={[2019, 2020, 2021, 2022, 2023, 2024]}
                availableTopics={['machine learning', 'biotechnology', 'quantum computing', 'neural networks', 'renewable energy']}
              />

            {selectedNode && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-3 p-4 rounded-xl bg-[var(--glass-bg)] border border-nrg-border"
              >
                <div className="w-10 h-10 rounded-lg bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400 flex items-center justify-center text-sm font-bold">
                  {selectedNode.label[0]?.toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-nrg-text truncate">{selectedNode.label}</p>
                  <p className="text-xs text-nrg-muted capitalize">
                    {selectedNode.type}
                    {selectedNode.year && ` · FY${selectedNode.year}`}
                    {selectedNode.citations !== undefined && ` · ${selectedNode.citations} citations`}
                  </p>
                </div>
                <motion.button
                  onClick={() => setCurrentQuery(selectedNode.label)}
                  className="px-4 py-2 rounded-xl text-xs font-medium bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400 hover:bg-violet-200 transition-colors"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {t("auto.views.ResearcherDashboard.32")}</motion.button>
              </motion.div>
            )}
            </WidgetErrorBoundary>
          </motion.div>
        )}

        {activeTab === 'dpdp' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <WidgetErrorBoundary title={t("auto.views.ResearcherDashboard.33")}>
              <DPDPPanel role="researcher" />
            </WidgetErrorBoundary>
          </motion.div>
        )}

        {activeTab === 'audit' && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <WidgetErrorBoundary title={t("auto.views.ResearcherDashboard.34")}>
              <DPDPAuditLog />
            </WidgetErrorBoundary>
          </motion.div>
        )}

        {activeTab === 'admin' && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <MetricsDashboard />
          </motion.div>
        )}
      </main>

      <DPDPConsentDialog
        isOpen={showDPDPConsent}
        onApprove={() => { grantConsent('research_access', 365); setShowDPDPConsent(false) }}
        onDeny={() => setShowDPDPConsent(false)}
      />
    </div>
    </ErrorBoundary>
  )
}

export default ResearcherDashboard
