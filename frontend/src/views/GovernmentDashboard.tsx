import React, { useState, useCallback, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import { GovernmentHeader } from '../components/Government/GovernmentHeader'
import { SummaryCard, MinistrySummaryCard, AlertCard } from '../components/Government/SummaryCards'
import { DataTable } from '../components/Government/DataTables'
import { StatsCard } from '../components/StatsCard'
import { SkeletonLoader } from '../components/Skeleton'
import { ErrorState } from '../components/ErrorState'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { WidgetErrorBoundary } from '../components/WidgetErrorBoundary'
import { AnswerPanel } from '../components/AnswerPanel'
import { GraphView } from '../components/GraphView'
import { DPDPConsentDialog } from '../components/DPDPConsentDialog'
import { ConsentBanner } from '../components/ConsentBanner'
import { DPDPPanel } from '../components/DPDPPanel'
import { ResearchAreasBarChart } from '../components/DataViz'
import { FundingTrendsLineChart } from '../components/DataViz'
import { IndiaMapChoropleth } from '../components/DataViz'
import { useAuth } from '../hooks/useAuth'
import { useQueryStore } from '../stores/queryStore'
import { useDPDPStore } from '../stores/dpdpStore'
import { queryService, GraphNode, QueryResponse } from '../services/queryService'
import { useQuery } from '@tanstack/react-query'
import { Building, Users, GraduationCap, FileText, Shield, AlertTriangle, TrendingUp, Search } from 'lucide-react'
import type { Theme } from '../hooks/useTheme'

interface GovernmentDashboardProps {
  onThemeToggle: () => void
  theme: Theme
}

const TABS = [
  { key: 'overview', label: 'Overview', labelHi: 'अवलोकन' },
  { key: 'policy', label: 'Policy Analysis', labelHi: 'नीति विश्लेषण' },
  { key: 'institutions', label: 'Institutions', labelHi: 'संस्थान' },
  { key: 'graph', label: 'Knowledge Graph', labelHi: 'ज्ञान ग्राफ' },
  { key: 'rights', label: 'Data Rights', labelHi: 'डेटा अधिकार' },
] as const

export function GovernmentDashboard({ onThemeToggle, theme }: GovernmentDashboardProps) {
  const { user } = useAuth()
  const { addAuditEntry, grantConsent, getConsentStatus } = useDPDPStore()
  const hasExistingConsent = getConsentStatus('Research data analysis')?.granted
  const [showDPDPConsent, setShowDPDPConsent] = useState(!hasExistingConsent)
  const [activeTab, setActiveTab] = useState<typeof TABS[number]['key']>('overview')
  const [currentQuery, setCurrentQuery] = useState('')
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null)
  const [queryError, setQueryError] = useState<string | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [graphData, setGraphData] = useState(queryService.emptyGraphData())
  const [graphTopic, setGraphTopic] = useState('AI')
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', user?.id],
    queryFn: () => queryService.fetchStats(),
    staleTime: 30 * 1000,
    enabled: !!user,
  })

  const { data: publicationsData } = useQuery({
    queryKey: ['publications', user?.id],
    queryFn: () => queryService.fetchPublications(100),
    staleTime: 5 * 60 * 1000,
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

  const handleSearch = useCallback(async () => {
    if (!currentQuery.trim()) return
    setIsSearching(true)
    setQueryError(null)
    try {
      const result = await queryService.query({ query: currentQuery })
      setQueryResult(result)
      addAuditEntry({ action: 'data_accessed', persona: 'government', details: `Query: ${currentQuery}` })
    } catch (err: any) {
      setQueryError(err.message || 'Search failed')
    } finally {
      setIsSearching(false)
    }
  }, [currentQuery, addAuditEntry])

  const ministryData = [
    { ministry: 'Ministry of Education', ministryHi: 'शिक्षा मंत्रालय', institutionCount: 45, researcherCount: 1234, fundingCr: 250, topArea: 'AI/ML' },
    { ministry: 'Ministry of Science & Technology', ministryHi: 'विज्ञान और प्रौद्योगिकी मंत्रालय', institutionCount: 32, researcherCount: 892, fundingCr: 180, topArea: 'Biotechnology' },
    { ministry: 'Ministry of Defence', ministryHi: 'रक्षा मंत्रालय', institutionCount: 18, researcherCount: 567, fundingCr: 320, topArea: 'Aerospace' },
    { ministry: 'Ministry of Health', ministryHi: 'स्वास्थ्य मंत्रालय', institutionCount: 28, researcherCount: 745, fundingCr: 150, topArea: 'Medical Research' },
  ]

  const AREA_COLORS = ['#ff6b35', '#2563eb', '#10b981', '#c49538', '#6366f1', '#ec4899', '#8b5cf6', '#f59e0b', '#06b6d4', '#84cc16']

  const stateData = useMemo(() => {
    if (statsData?.state_distribution?.length) {
      const hiNames: Record<string, string> = {
        'Gujarat': 'गुजरात', 'Maharashtra': 'महाराष्ट्र', 'Delhi': 'दिल्ली',
        'Karnataka': 'कर्नाटक', 'Tamil Nadu': 'तमिलनाडु', 'Telangana': 'तेलंगाना',
        'West Bengal': 'पश्चिम बंगाल', 'Uttar Pradesh': 'उत्तर प्रदेश', 'Kerala': 'केरल', 'Punjab': 'पंजाब',
      }
      return statsData.state_distribution.map((s: { state: string; count: number }) => ({
        state: s.state,
        stateHi: hiNames[s.state] || s.state,
        count: s.count,
      }))
    }
    return [
      { state: 'Gujarat', stateHi: 'गुजरात', count: 886 },
      { state: 'Delhi', stateHi: 'दिल्ली', count: 710 },
      { state: 'Maharashtra', stateHi: 'महाराष्ट्र', count: 625 },
      { state: 'Karnataka', stateHi: 'कर्नाटक', count: 555 },
      { state: 'Tamil Nadu', stateHi: 'तमिलनाडु', count: 491 },
    ]
  }, [statsData?.state_distribution])

  const researchAreaData = useMemo(() => {
    if (statsData?.research_area_distribution?.length) {
      return statsData.research_area_distribution.map((r: { area: string; count: number }, i: number) => ({
        area: r.area,
        count: r.count,
        color: AREA_COLORS[i % AREA_COLORS.length],
      }))
    }
    return [
      { area: 'AI/ML', count: 239, color: '#ff6b35' },
      { area: 'Sustainable Energy', count: 224, color: '#2563eb' },
      { area: 'Robotics', count: 209, color: '#10b981' },
      { area: 'Advanced Materials', count: 198, color: '#c49538' },
      { area: 'NLP', count: 198, color: '#6366f1' },
    ]
  }, [statsData?.research_area_distribution])

  const fundingTrendData = useMemo(() => [
    { year: 2019, funding: 450, publications: 1200 },
    { year: 2020, funding: 520, publications: 1450 },
    { year: 2021, funding: 680, publications: 1680 },
    { year: 2022, funding: 750, publications: 1920 },
    { year: 2023, funding: 890, publications: 2150 },
    { year: 2024, funding: 1050, publications: 2480 },
  ], [])

  const consentExpiringCount = useDPDPStore((s) => {
    const threshold = Date.now() + 30 * 24 * 60 * 60 * 1000;
    return Object.values(s.consents).filter((c) => c.expiresAt && c.expiresAt < threshold && c.granted).length;
  })

  return (
    <ErrorBoundary title="Government Dashboard failed to load">
      <div className="min-h-screen bg-slate-50 dark:bg-navy-900">
        <GovernmentHeader onThemeToggle={onThemeToggle} theme={theme} />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-1 -mb-px overflow-x-auto border-b border-slate-200 dark:border-navy-700">
          {TABS.map((tab) => (
            <motion.button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 whitespace-nowrap ${
                activeTab === tab.key
                  ? 'border-saffron-500 text-saffron-600 dark:text-saffron-400'
                  : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:border-slate-300 dark:hover:border-navy-600'
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              data-testid={`tab-${tab.key}`}
            >
              {tab.label}
              <span className="text-xs font-devanagari text-slate-400 ml-1">{tab.labelHi}</span>
            </motion.button>
          ))}
        </div>

        <ConsentBanner
          role="government"
          expiringCount={consentExpiringCount}
        />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {activeTab === 'overview' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <WidgetErrorBoundary title="Stats cards failed to load" description="Could not load dashboard statistics">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {statsLoading ? (
                    <SkeletonLoader type="stats" />
                  ) : (
                    <>
                      <StatsCard
                        label="Total Researchers"
                        labelHi="कुल शोधकर्ता"
                        value={statsData?.total_researchers ?? 0}
                        sublabel="Across government institutions"
                        accentColor="#ff6b35"
                        icon={<Users size={20} />}
                        delay={0}
                        data-testid="stat-researchers"
                      />
                      <StatsCard
                        label="Publications"
                        labelHi="प्रकाशन"
                        value={statsData?.total_publications ?? 0}
                        sublabel="Peer-reviewed works"
                        accentColor="#2563eb"
                        icon={<FileText size={20} />}
                        delay={100}
                        data-testid="stat-publications"
                      />
                      <StatsCard
                        label="Research Labs"
                        labelHi="शोध प्रयोगशालाएं"
                        value={statsData?.total_labs ?? 0}
                        sublabel="Across institutions"
                        accentColor="#10b981"
                        icon={<Building size={20} />}
                        delay={200}
                        data-testid="stat-labs"
                      />
                      <StatsCard
                        label="Institutions"
                        labelHi="संस्थान"
                        value={statsData?.total_institutions ?? 0}
                        sublabel="Government affiliated"
                        accentColor="#c49538"
                        icon={<Shield size={20} />}
                        delay={300}
                        data-testid="stat-institutions"
                      />
                    </>
                  )}
                </div>
              </WidgetErrorBoundary>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <WidgetErrorBoundary title="Research area chart failed to load">
                  <div className="lg:col-span-2">
                    {statsLoading ? (
                      <SkeletonLoader type="chart" />
                    ) : (
                      <ResearchAreasBarChart
                        data={researchAreaData}
                        title="Research Area Distribution"
                        titleHi="शोध क्षेत्र वितरण"
                        subtitle="Top research areas across government institutions"
                      />
                    )}
                  </div>
                </WidgetErrorBoundary>
                <WidgetErrorBoundary title="State map failed to load">
                  {statsLoading ? (
                    <SkeletonLoader type="chart" />
                  ) : (
                    <IndiaMapChoropleth
                      data={stateData}
                      title="State Distribution"
                      titleHi="राज्य वितरण"
                      subtitle="Research activity by state"
                    />
                  )}
                </WidgetErrorBoundary>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <WidgetErrorBoundary title="Funding trends chart failed to load">
                  <FundingTrendsLineChart
                    data={fundingTrendData}
                    title="Funding Trends"
                    titleHi="वित्तीय रुझान"
                    subtitle="Research funding over time (in Crores)"
                  />
                </WidgetErrorBoundary>

                <WidgetErrorBoundary title="Quick query panel failed to load">
                  <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md p-5">
                    <div className="mb-4">
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Quick Query</h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400 font-devanagari">त्वरित प्रश्न</p>
                    </div>
                    <div className="flex gap-3">
                      <input
                        type="text"
                        value={currentQuery}
                        onChange={(e) => setCurrentQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        placeholder="Enter policy query..."
                        className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-navy-600 bg-white dark:bg-navy-800 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:border-saffron-500"
                        data-testid="policy-query-input"
                      />
                      <motion.button
                        onClick={handleSearch}
                        disabled={isSearching}
                        className="px-5 py-2.5 rounded-xl text-sm font-medium bg-gradient-to-r from-saffron-500 to-saffron-600 text-white shadow-md hover:shadow-lg disabled:opacity-50"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        data-testid="policy-query-submit"
                      >
                        {isSearching ? 'Searching...' : 'Query'}
                      </motion.button>
                    </div>
                    {queryResult && (
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
                    {queryError && (
                      <div className="mt-4">
                        <ErrorState
                          title="Query Failed"
                          message={queryError}
                          severity="error"
                          onRetry={handleSearch}
                        />
                      </div>
                    )}
                  </div>
                </WidgetErrorBoundary>
              </div>

              <WidgetErrorBoundary title="Ministry summary failed to load">
                <div className="space-y-4">
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                    Ministry Summary
                    <span className="text-sm font-normal text-slate-500 ml-2 font-devanagari">मंत्रालय सारांश</span>
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {ministryData.map((m, i) => (
                      <MinistrySummaryCard key={i} {...m} />
                    ))}
                  </div>
                </div>
              </WidgetErrorBoundary>
            </motion.div>
          )}

          {activeTab === 'institutions' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <WidgetErrorBoundary title="Institution table failed to load">
                <DataTable
                  title="Institution Directory"
                  titleHi="संस्थान निर्देशिका"
                  columns={[
                    { key: 'institution', label: 'Institution' },
                    { key: 'type', label: 'Type' },
                    { key: 'researchers', label: 'Researchers', align: 'right' },
                    { key: 'publications', label: 'Publications', align: 'right' },
                    { key: 'funding', label: 'Funding (₹Cr)', align: 'right' },
                    { key: 'grade', label: 'NIRF Grade' },
                  ]}
                  data={[
                    { institution: 'Indian Institute of Technology Delhi', type: 'IIT', researchers: 1245, publications: 3420, funding: 180, grade: 'AAA+' },
                    { institution: 'Indian Institute of Science Bangalore', type: 'IISc', researchers: 892, publications: 2890, funding: 150, grade: 'AAA+' },
                    { institution: 'National Institute of Technology', type: 'NIT', researchers: 756, publications: 1234, funding: 85, grade: 'AA+' },
                    { institution: 'All India Institute of Medical Sciences', type: 'AIIMS', researchers: 567, publications: 1567, funding: 120, grade: 'AAA' },
                    { institution: 'Indian Institute of Technology Bombay', type: 'IIT', researchers: 1456, publications: 3980, funding: 210, grade: 'AAA+' },
                  ]}
                />
              </WidgetErrorBoundary>
            </motion.div>
          )}

          {activeTab === 'graph' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              <WidgetErrorBoundary title="Knowledge graph failed to load">
                <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md p-5">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 flex gap-3">
                      <div className="relative flex-1 max-w-sm">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                        <input
                          type="text"
                          value={graphTopic}
                          onChange={(e) => setGraphTopic(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && setGraphTopic(graphTopic)}
                          placeholder="Enter topic for knowledge graph..."
                          className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-navy-600 bg-white dark:bg-navy-800 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:border-saffron-500"
                          data-testid="graph-topic-input"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {graphLoading ? (
                  <SkeletonLoader type="chart" />
                ) : (
                  <GraphView
                    data={graphData}
                    width={1100}
                    height={600}
                    onNodeClick={(node) => setSelectedNode(node)}
                    availableYears={[2019, 2020, 2021, 2022, 2023, 2024]}
                    availableTopics={['AI', 'Biotechnology', 'Aerospace', 'Medical', 'Energy']}
                  />
                )}

                {selectedNode && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-3 p-4 rounded-xl bg-white dark:bg-navy-700 border border-slate-200 dark:border-navy-600"
                  >
                    <div className="w-10 h-10 rounded-lg bg-saffron-100 dark:bg-saffron-900/30 text-saffron-600 dark:text-saffron-400 flex items-center justify-center text-sm font-bold">
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
                  </motion.div>
                )}
              </WidgetErrorBoundary>
            </motion.div>
          )}

          {activeTab === 'rights' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <WidgetErrorBoundary title="Data rights panel failed to load">
                <DPDPPanel role="government" />
              </WidgetErrorBoundary>
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

export default GovernmentDashboard
