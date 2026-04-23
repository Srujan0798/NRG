import React, { useState, useCallback, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import { PermissionBoundary } from '../components/PermissionBoundary'
import { TierBadge } from '../components/TierBadge'
import { SkeletonLoader } from '../components/Skeleton'
import { DPDPConsentDialog } from '../components/DPDPConsentDialog'
import { DPDPAuditLog } from '../components/DPDPAuditLog'
import { DPDPWithdrawalPanel } from '../components/DPDPWithdrawalPanel'
import { SecurityMonitor } from '../components/SecurityMonitor'
import { ConsentBanner } from '../components/ConsentBanner'
import { DPDPPanel } from '../components/DPDPPanel'
import { GlassCard } from '../components/GlassCard'
import { AnswerPanel } from '../components/AnswerPanel'
import { GraphView } from '../components/GraphView'
import { StatsCard } from '../components/StatsCard'
import { ErrorState } from '../components/ErrorState'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { WidgetErrorBoundary } from '../components/WidgetErrorBoundary'
import { ResearchAreasBarChart } from '../components/DataViz'
import { useAuth } from '../hooks/useAuth'
import MetricsDashboard from './MetricsDashboard'
import { useQueryStore } from '../stores/queryStore'
import { useDPDPStore } from '../stores/dpdpStore'
import { queryService, GraphNode, QueryResponse } from '../services/queryService'
import { useQuery } from '@tanstack/react-query'
import {
  Search, Users, FileText, Building, TrendingUp, Shield,
  Sun as SunIcon, Moon as MoonIcon, BookOpen, History, RefreshCw
} from 'lucide-react'
import type { Theme } from '../hooks/useTheme'

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

const SaffronSpinner = ({ style }: { style?: React.CSSProperties }) => (
  <div
    className="w-9 h-9 rounded-full border-3 border-saffron-200 border-t-saffron-500 animate-spin"
    style={style}
  />
)

export function ResearcherDashboard({ onThemeToggle, theme }: ResearcherDashboardProps) {
  const { user } = useAuth()
  const {
    history, currentQuery, isSearching,
    setCurrentQuery, addToHistory, setIsSearching, setLastResult,
  } = useQueryStore()
  const { grantConsent, addAuditEntry, getConsentStatus } = useDPDPStore()

  const hasExistingConsent = getConsentStatus('Research data analysis')?.granted
  const [showDPDPConsent, setShowDPDPConsent] = useState(!hasExistingConsent)
  const [activeTab, setActiveTab] = useState<typeof TABS[number]['key']>('dashboard')
  const [graphData, setGraphData] = useState(queryService.emptyGraphData())
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null)
  const [queryError, setQueryError] = useState<string | null>(null)
  const [graphTopic, setGraphTopic] = useState('machine learning')

  const { data: publicationsData, isLoading: pubsLoading } = useQuery({
    queryKey: ['publications', user?.id],
    queryFn: () => queryService.fetchPublications(10),
    staleTime: 5 * 60 * 1000,
    enabled: !!user,
  })

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', user?.id],
    queryFn: () => queryService.fetchStats(),
    staleTime: 30 * 1000,
    enabled: !!user,
  })

  const { data: graphApiData, isLoading: graphLoading } = useQuery({
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

  const publications = publicationsData?.publications || []

  const consentExpiringCount = useDPDPStore((s) => {
    const threshold = Date.now() + 30 * 24 * 60 * 60 * 1000;
    return Object.values(s.consents).filter((c) => c.expiresAt && c.expiresAt < threshold && c.granted).length;
  })

  const handleSearch = useCallback(async () => {
    if (!currentQuery.trim()) return
    setIsSearching(true)
    setQueryResult(null)
    setQueryError(null)
    try {
      const result = await queryService.query({ query: currentQuery })
      setQueryResult(result)
      setLastResult(result)
      addToHistory({ query: currentQuery, persona: 'researcher', resultsCount: result.verification_status ? 10 : 0 })
      addAuditEntry({ action: 'data_accessed', persona: 'researcher', details: `Query: ${currentQuery}` })
    } catch (err: any) {
      const message = err.response?.data?.detail || err.response?.data?.message || err.message || 'Search failed'
      setQueryError(message)
      addToHistory({ query: currentQuery, persona: 'researcher', resultsCount: 0, error: message })
    } finally {
      setIsSearching(false)
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

  const pieColors = ['#ff6b35', '#2563eb', '#10b981', '#c49538', '#6366f1']
  const researchAreaChartData = (statsData?.research_area_distribution || []).slice(0, 6).map((a: any) => ({
    area: a.area?.length > 12 ? a.area.slice(0, 10) + '…' : a.area,
    count: a.count,
  }))

  return (
    <ErrorBoundary title="Researcher Dashboard failed to load">
      <div className="min-h-screen bg-slate-50 dark:bg-navy-900">
      <header className="sticky top-0 z-40 bg-white/95 dark:bg-navy-800/95 backdrop-blur-md border-b border-slate-200 dark:border-navy-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <motion.div
              className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center shadow-lg"
              whileHover={{ scale: 1.05, rotate: 2 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
            >
              <span className="text-white font-bold text-lg">न</span>
            </motion.div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 dark:text-white font-devanagari">राष्ट्रीय गवेषण मंच</h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">Researcher Workspace · शोधकर्ता कार्यस्थान</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {user && <TierBadge tier={user.tier} role={user.role} />}
            <motion.button
              onClick={onThemeToggle}
              className="w-9 h-9 rounded-xl border border-slate-200 dark:border-navy-600 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-violet-500 hover:border-violet-300 transition-all duration-200"
              aria-label="Toggle theme"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
            </motion.button>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-1 -mb-px overflow-x-auto">
          {TABS.map((tab) => {
            if ('tier' in tab && tab.tier !== undefined && (user?.tier ?? 0) < tab.tier) return null
            return (
              <motion.button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 whitespace-nowrap ${
                  activeTab === tab.key
                    ? 'border-violet-500 text-violet-600 dark:text-violet-400'
                    : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:border-slate-300 dark:hover:border-navy-600'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                data-testid={`tab-${tab.key}`}
              >
                <span>{tab.icon}</span>
                {tab.label}
                <span className="text-xs font-devanagari text-slate-400 ml-1">{tab.labelHi}</span>
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

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md p-5">
              <div className="flex items-center gap-2 mb-4">
                <Search size={18} className="text-violet-500" />
                <div>
                  <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Knowledge Graph Query</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-devanagari">ज्ञान ग्राफ प्रश्न</p>
                </div>
              </div>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={currentQuery}
                  onChange={(e) => setCurrentQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Enter research topic, author, institution, or DOI…"
                  className="flex-1 px-4 py-3 rounded-xl border border-slate-200 dark:border-navy-600 bg-white dark:bg-navy-800 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20 transition-all"
                  data-testid="researcher-search-input"
                />
                <motion.button
                  onClick={handleSearch}
                  disabled={isSearching || !currentQuery.trim()}
                  className="px-6 py-3 rounded-xl text-sm font-medium bg-gradient-to-r from-violet-500 to-violet-600 text-white shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  data-testid="researcher-search-submit"
                >
                  {isSearching ? (
                    <span className="flex items-center gap-2">
                      <SaffronSpinner style={{ width: 16, height: 16, borderWidth: 2 }} />
                      Processing…
                    </span>
                  ) : (
                    'Search'
                  )}
                </motion.button>
              </div>

              {isSearching && (
                <div className="mt-4 flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
                  <SaffronSpinner />
                  <span>Processing query through NRG LangGraph orchestration…</span>
                </div>
              )}

              {queryError && (
                <div className="mt-4">
                  <ErrorState
                    title="Query Failed"
                    message={queryError}
                    severity="error"
                    onRetry={handleRetry}
                  />
                </div>
              )}

              {queryResult && !queryError && (
                <div className="mt-4">
                  <AnswerPanel
                    response={queryResult.response}
                    citations={queryResult.citations || []}
                    provenance={queryResult.provenance}
                    warnings={queryResult.warnings}
                    verification_status={queryResult.verification_status}
                  />
                </div>
              )}
            </div>

            <WidgetErrorBoundary title="Stats cards failed to load">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatsCard
                  label="Total Researchers"
                  labelHi="कुल शोधकर्ता"
                  value={statsData?.total_researchers ?? 5615}
                  sublabel="Across 181 institutions"
                  accentColor="#6366f1"
                  icon={<Users size={20} />}
                  delay={0}
                  data-testid="stat-researchers"
                />
                <StatsCard
                  label="Publications"
                  labelHi="प्रकाशन"
                  value={statsData?.total_publications ?? 12847}
                  sublabel="Peer-reviewed works"
                  accentColor="#2563eb"
                  icon={<FileText size={20} />}
                  delay={100}
                  data-testid="stat-publications"
                />
                <StatsCard
                  label="Institutions"
                  labelHi="संस्थान"
                  value={statsData?.total_institutions ?? 181}
                  sublabel="Academic + Research"
                  accentColor="#10b981"
                  icon={<Building size={20} />}
                  delay={200}
                  data-testid="stat-institutions"
                />
                <StatsCard
                  label="Your Queries"
                  labelHi="आपके प्रश्न"
                  value={history.length}
                  sublabel="This session"
                  accentColor="#ff6b35"
                  icon={<History size={20} />}
                  delay={300}
                  data-testid="stat-queries"
                />
              </div>
            </WidgetErrorBoundary>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="space-y-4">
                <GlassCard accent="researcher" title="My Publications" description="Recent works from your profile">
                  {pubsLoading ? (
                    <SkeletonLoader type="list" count={4} />
                  ) : publications.length > 0 ? (
                    <div className="space-y-2 max-h-64 overflow-y-auto scrollbar-nrg">
                      {publications.map((pub: any, i: number) => (
                        <motion.div
                          key={i}
                          className="flex items-center gap-3 p-3 rounded-xl border border-slate-100 dark:border-navy-700 bg-slate-50 dark:bg-navy-700/30 hover:border-violet-200 hover:bg-violet-50/50 dark:hover:border-violet-700 transition-all cursor-pointer"
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.06 }}
                          whileHover={{ x: 4 }}
                        >
                          <div className="w-8 h-8 rounded-lg bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400 flex items-center justify-center text-sm font-bold">
                            {pub.year?.toString().slice(-2) || '?'}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{pub.title}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">{typeof pub.authors === 'string' ? pub.authors.split(',').slice(0, 2).join(', ') : Array.isArray(pub.authors) ? pub.authors.slice(0, 2).join(', ') : ''}</p>
                          </div>
                          <div className="text-right shrink-0">
                            <p className="text-xs font-semibold text-violet-600 dark:text-violet-400">{pub.citations || 0}</p>
                            <p className="text-xs text-slate-400 dark:text-slate-500">citations</p>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-10 text-slate-400 dark:text-slate-500">
                      <BookOpen size={40} className="mx-auto mb-3 opacity-50" />
                      <p className="text-sm">No publications found.</p>
                    </div>
                  )}
                </GlassCard>
              </div>

              <div className="lg:col-span-2 space-y-4">
                {researchAreaChartData.length > 0 && (
                  <ResearchAreasBarChart
                    data={researchAreaChartData.map((d, i) => ({ ...d, color: pieColors[i % pieColors.length] }))}
                    title="Top Research Areas"
                    titleHi="शीर्ष शोध क्षेत्र"
                    subtitle="Distribution by specialization"
                  />
                )}

                {history.length > 0 && (
                  <GlassCard accent="sovereign" title="Recent Queries" description="Your query history this session">
                    <div className="space-y-2 max-h-48 overflow-y-auto scrollbar-nrg">
                      {history.slice(0, 6).map((entry) => (
                        <div key={entry.id} className="flex items-center gap-3 py-2 border-b border-slate-100 dark:border-navy-700/50 last:border-0">
                          <div className={`w-2 h-2 rounded-full shrink-0 ${entry.error ? 'bg-red-400' : 'bg-violet-400'}`} />
                          <span className="flex-1 text-sm text-slate-900 dark:text-slate-100 truncate font-medium">{entry.query}</span>
                          <span className="text-xs text-slate-500 shrink-0">
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
            <WidgetErrorBoundary title="Knowledge graph failed to load">
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
                className="flex items-center gap-3 p-4 rounded-xl bg-white dark:bg-navy-700 border border-slate-200 dark:border-navy-600"
              >
                <div className="w-10 h-10 rounded-lg bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400 flex items-center justify-center text-sm font-bold">
                  {selectedNode.label[0]?.toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">{selectedNode.label}</p>
                  <p className="text-xs text-slate-500 capitalize">
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
                  Query
                </motion.button>
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
            <WidgetErrorBoundary title="Data rights panel failed to load">
              <DPDPPanel role="researcher" />
            </WidgetErrorBoundary>
          </motion.div>
        )}

        {activeTab === 'audit' && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <WidgetErrorBoundary title="Audit log failed to load">
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
        onApprove={() => { grantConsent('Research data analysis', 365); setShowDPDPConsent(false) }}
        onDeny={() => setShowDPDPConsent(false)}
      />
    </div>
    </ErrorBoundary>
  )
}

export default ResearcherDashboard
