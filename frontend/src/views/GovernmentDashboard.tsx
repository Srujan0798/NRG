import React, { useState, useCallback, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import { GovernmentHeader } from '../components/Government/GovernmentHeader'
import { MinistrySummaryCard } from '../components/Government/SummaryCards'
import { DataTable } from '../components/Government/DataTables'
import { StatsCard } from '../components/StatsCard'
import { SkeletonLoader } from '../components/Skeleton'
import { ErrorState } from '../components/ErrorState'
import { ErrorBoundary, WidgetErrorBoundary } from '../components/ErrorBoundary'
import { AnswerPanel } from '../components/AnswerPanel'
import { GraphView } from '../components/GraphView'
import { DPDPConsentDialog } from '../components/DPDPConsentDialog'
import { ConsentBanner } from '../components/ConsentBanner'
import { DPDPPanel } from '../components/DPDPPanel'
import { EmptyState } from '../components/EmptyState'
import { QueryPhaseProgress } from '../components/QueryPhaseProgress'
import { ResearchAreasBarChart } from '../components/DataViz'
import { FundingTrendsLineChart } from '../components/DataViz'
import { IndiaMapChoropleth } from '../components/DataViz'
import { useAuth } from '../hooks/useAuth'
import { useDPDPStore } from '../stores/dpdpStore'
import { queryService, GraphNode, QueryResponse } from '../services/queryService'
import { getDashboardDocumentTitle, getQueryStatusCopy } from '../utils/dashboardCopy'
import { buildRelaxedQuery, isEmptyResultResponse } from '../utils/emptyResults'
import { useQuery } from '@tanstack/react-query'
import { Building, Users, FileText, Shield, Search } from 'lucide-react'
import type { Theme } from '../hooks/useTheme'
import { t } from '../i18n'

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

const AREA_COLORS = ['var(--nrg-chart-1)', 'var(--nrg-chart-2)', 'var(--nrg-chart-3)', 'var(--nrg-chart-4)', 'var(--nrg-chart-5)', 'var(--nrg-chart-6)', 'var(--nrg-chart-7)', 'var(--nrg-warning)', 'var(--nrg-chart-9)', 'var(--nrg-chart-10)']

const POLICY_DEMO_QUERIES = [
  'Which states have the highest renewable energy research funding?',
  'Compare AI research output between Gujarat and Karnataka over the last 5 years',
  'Where should DST allocate the next clean energy research hub?',
]

export function GovernmentDashboard({ onThemeToggle, theme }: GovernmentDashboardProps) {
  const { user } = useAuth()
  const { addAuditEntry, grantConsent, getConsentStatus } = useDPDPStore()
  const hasExistingConsent = getConsentStatus('research_access')?.granted
  const [showDPDPConsent, setShowDPDPConsent] = useState(!hasExistingConsent)
  const [activeTab, setActiveTab] = useState<typeof TABS[number]['key']>('overview')
  const [currentQuery, setCurrentQuery] = useState('')
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null)
  const [queryError, setQueryError] = useState<string | null>(null)
  const [queryValidation, setQueryValidation] = useState<string | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [isSlowQuery, setIsSlowQuery] = useState(false)
  const [graphData, setGraphData] = useState(queryService.emptyGraphData())
  const [graphTopic, setGraphTopic] = useState('AI')
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', user?.id],
    queryFn: () => queryService.fetchStats(),
    staleTime: 30 * 1000,
    enabled: !!user,
  })

  const { data: _publicationsData } = useQuery({
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

  useEffect(() => {
    document.title = getDashboardDocumentTitle('government', activeTab)
  }, [activeTab])

  const handleSearch = useCallback(async () => {
    const submittedQuery = currentQuery.trim()
    if (!submittedQuery) {
      setQueryValidation('Enter a policy question before searching.')
      return
    }
    setQueryValidation(null)
    setIsSearching(true)
    setQueryError(null)
    setIsSlowQuery(false)
    const slowTimer = window.setTimeout(() => setIsSlowQuery(true), 5000)
    try {
      const result = await queryService.query({ query: submittedQuery })
      setQueryResult(result)
      addAuditEntry({ action: 'data_accessed', persona: 'government', details: `Query: ${submittedQuery}` })
    } catch (err: any) {
      setQueryError(err?.response?.status === 403
        ? 'Access restricted for this workspace. Aggregated policy data only is available.'
        : err?.message || 'Search failed. Please try again.')
    } finally {
      window.clearTimeout(slowTimer)
      setIsSearching(false)
      setIsSlowQuery(false)
    }
  }, [currentQuery, addAuditEntry])

  const ministryData = [
    { ministry: 'Ministry of Education', ministryHi: 'शिक्षा मंत्रालय', institutionCount: 45, researcherCount: 1234, fundingCr: 250, topArea: 'AI/ML' },
    { ministry: 'Ministry of Science & Technology', ministryHi: 'विज्ञान और प्रौद्योगिकी मंत्रालय', institutionCount: 32, researcherCount: 892, fundingCr: 180, topArea: 'Biotechnology' },
    { ministry: 'Ministry of Defence', ministryHi: 'रक्षा मंत्रालय', institutionCount: 18, researcherCount: 567, fundingCr: 320, topArea: 'Aerospace' },
    { ministry: 'Ministry of Health', ministryHi: 'स्वास्थ्य मंत्रालय', institutionCount: 28, researcherCount: 745, fundingCr: 150, topArea: 'Medical Research' },
  ]

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
      { area: 'AI/ML', count: 239, color: 'var(--nrg-chart-1)' },
      { area: 'Sustainable Energy', count: 224, color: 'var(--nrg-chart-2)' },
      { area: 'Robotics', count: 209, color: 'var(--nrg-chart-3)' },
      { area: 'Advanced Materials', count: 198, color: 'var(--nrg-chart-4)' },
      { area: 'NLP', count: 198, color: 'var(--nrg-chart-5)' },
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
    <ErrorBoundary title={t("auto.views.GovernmentDashboard.1")}>
      <div className="nrg-app-canvas min-h-screen">
        <GovernmentHeader onThemeToggle={onThemeToggle} theme={theme} />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-2 -mb-px overflow-x-auto border-b border-nrg-border">
          {TABS.map((tab) => (
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
              {tab.label}
              <span className="text-xs font-devanagari text-nrg-muted ml-1">{tab.labelHi}</span>
            </motion.button>
          ))}
        </div>

        <ConsentBanner
          role="government"
          expiringCount={consentExpiringCount}
        />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 relative z-10">
          {activeTab === 'overview' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <WidgetErrorBoundary title={t("auto.views.GovernmentDashboard.2")} description={t("auto.views.GovernmentDashboard.3")}>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {statsLoading ? (
                    <SkeletonLoader type="stats" />
                  ) : (
                    <>
                      <StatsCard
                        label={t("auto.views.GovernmentDashboard.4")}
                        labelHi="कुल शोधकर्ता"
                        value={statsData?.total_researchers ?? 0}
                        sublabel="Across government institutions"
                        accentColor="var(--nrg-chart-1)"
                        icon={<Users size={20} />}
                        delay={0}
                        data-testid="stat-researchers"
                      />
                      <StatsCard
                        label={t("auto.views.GovernmentDashboard.5")}
                        labelHi="प्रकाशन"
                        value={statsData?.total_publications ?? 0}
                        sublabel="Peer-reviewed works"
                        accentColor="var(--nrg-chart-2)"
                        icon={<FileText size={20} />}
                        delay={100}
                        data-testid="stat-publications"
                      />
                      <StatsCard
                        label={t("auto.views.GovernmentDashboard.6")}
                        labelHi="शोध प्रयोगशालाएं"
                        value={statsData?.total_labs ?? 0}
                        sublabel="Across institutions"
                        accentColor="var(--nrg-chart-3)"
                        icon={<Building size={20} />}
                        delay={200}
                        data-testid="stat-labs"
                      />
                      <StatsCard
                        label={t("auto.views.GovernmentDashboard.7")}
                        labelHi="संस्थान"
                        value={statsData?.total_institutions ?? 0}
                        sublabel="Government affiliated"
                        accentColor="var(--nrg-chart-4)"
                        icon={<Shield size={20} />}
                        delay={300}
                        data-testid="stat-institutions"
                      />
                    </>
                  )}
                </div>
              </WidgetErrorBoundary>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <WidgetErrorBoundary title={t("auto.views.GovernmentDashboard.8")}>
                  <div className="lg:col-span-2">
                    {statsLoading ? (
                      <SkeletonLoader type="chart" />
                    ) : (
                      <ResearchAreasBarChart
                        data={researchAreaData}
                        title={t("auto.views.GovernmentDashboard.9")}
                        titleHi="शोध क्षेत्र वितरण"
                        subtitle={t("auto.views.GovernmentDashboard.10")}
                      />
                    )}
                  </div>
                </WidgetErrorBoundary>
                <WidgetErrorBoundary title={t("auto.views.GovernmentDashboard.11")}>
                  {statsLoading ? (
                    <SkeletonLoader type="chart" />
                  ) : (
                    <IndiaMapChoropleth
                      data={stateData}
                      title={t("auto.views.GovernmentDashboard.12")}
                      titleHi="राज्य वितरण"
                      subtitle={t("auto.views.GovernmentDashboard.13")}
                    />
                  )}
                </WidgetErrorBoundary>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <WidgetErrorBoundary title={t("auto.views.GovernmentDashboard.14")}>
                  <FundingTrendsLineChart
                    data={fundingTrendData}
                    title={t("auto.views.GovernmentDashboard.15")}
                    titleHi="वित्तीय रुझान"
                    subtitle={t("auto.views.GovernmentDashboard.16")}
                  />
                </WidgetErrorBoundary>

                <WidgetErrorBoundary title={t("auto.views.GovernmentDashboard.17")}>
                  <div className="nrg-panel p-5">
                    <div className="mb-4">
                      <h3 className="text-sm font-semibold text-nrg-text">{t("auto.views.GovernmentDashboard.18")}</h3>
                      <p className="text-xs text-nrg-muted font-devanagari">त्वरित प्रश्न</p>
                    </div>
                    <div className="mb-3 flex flex-wrap gap-2">
                      {POLICY_DEMO_QUERIES.slice(0, 2).map((suggestion) => (
                        <button
                          key={suggestion}
                          type="button"
                          onClick={() => {
                            setCurrentQuery(suggestion)
                            setQueryValidation(null)
                          }}
                          className="rounded-full border border-saffron-200 bg-saffron-50 px-3 py-1.5 text-xs font-medium text-saffron-700 transition hover:border-saffron-300 hover:bg-saffron-100"
                        >
                          {suggestion.length > 54 ? `${suggestion.slice(0, 52)}...` : suggestion}
                        </button>
                      ))}
                    </div>
                    <div className="flex flex-col gap-3 sm:flex-row">
                      <label htmlFor="policy-query-input" className="sr-only">{t("auto.views.GovernmentDashboard.19")}</label>
                      <input
                        id="policy-query-input"
                        type="text"
                        value={currentQuery}
                        onChange={(e) => {
                          setCurrentQuery(e.target.value)
                          if (queryValidation) setQueryValidation(null)
                        }}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        placeholder={t("auto.views.GovernmentDashboard.20")}
                        className="min-h-12 flex-1 rounded-xl border border-nrg-border bg-[var(--nrg-surface)] px-4 py-2.5 text-sm text-nrg-text placeholder:text-nrg-muted focus:border-saffron-500 focus:outline-none"
                        data-testid="policy-query-input"
                      />
                      <motion.button
                        onClick={handleSearch}
                        disabled={isSearching || !currentQuery.trim()}
                        className="min-h-12 rounded-xl bg-gradient-to-r from-saffron-500 to-saffron-600 px-5 py-2.5 text-sm font-medium text-white shadow-md hover:shadow-lg disabled:opacity-50 sm:w-auto"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        data-testid="policy-query-submit"
                      >
                        {isSearching ? 'Searching...' : 'Query'}
                      </motion.button>
                    </div>
                    {queryValidation && (
                      <p className="mt-2 text-sm text-rose-600" role="alert">{queryValidation}</p>
                    )}
                    {isSearching && (
                      <div className="mt-4 rounded-xl border border-saffron-200 bg-saffron-50 px-4 py-3 text-sm text-saffron-800" aria-live="polite">
                        <QueryPhaseProgress domain="policy" isSlowQuery={isSlowQuery} />
                        <p className="mt-2 text-xs">{getQueryStatusCopy({ isSlowQuery, domain: 'policy' })}</p>
                      </div>
                    )}
                    {queryResult && (
                      <div className="mt-4">
                        {isEmptyResultResponse(queryResult.response) ? (
                          <EmptyState
                            onPrimary={() => setCurrentQuery(buildRelaxedQuery(currentQuery))}
                            onSecondary={() => setCurrentQuery(currentQuery)}
                          />
                        ) : (
                          <AnswerPanel
                            response={queryResult.response}
                            citations={queryResult.citations || []}
                            provenance={queryResult.provenance}
                            warnings={queryResult.warnings}
                            verification_status={queryResult.verification_status}
                          />
                        )}
                      </div>
                    )}
                    {queryError && (
                      <div className="mt-4">
                        <ErrorState
                          title={t("auto.views.GovernmentDashboard.21")}
                          message={queryError}
                          severity="error"
                          onRetry={handleSearch}
                        />
                      </div>
                    )}
                  </div>
                </WidgetErrorBoundary>
              </div>

              <WidgetErrorBoundary title={t("auto.views.GovernmentDashboard.22")}>
                <div className="space-y-4">
                  <h2 className="text-lg font-semibold text-nrg-text">
                    {t("auto.views.GovernmentDashboard.23")}<span className="text-sm font-normal text-nrg-muted ml-2 font-devanagari">मंत्रालय सारांश</span>
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

          {activeTab === 'policy' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <WidgetErrorBoundary title={t("auto.views.GovernmentDashboard.24")}>
                <div className="nrg-panel p-4 sm:p-5">
                  <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                    <div>
                      <h2 className="text-base font-semibold text-nrg-text">{t("auto.views.GovernmentDashboard.25")}</h2>
                      <p className="text-sm text-nrg-muted">{t("auto.views.GovernmentDashboard.26")}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {POLICY_DEMO_QUERIES.map((suggestion) => (
                        <button
                          key={suggestion}
                          type="button"
                          onClick={() => {
                            setCurrentQuery(suggestion)
                            setQueryValidation(null)
                          }}
                          className="rounded-full border border-saffron-200 bg-saffron-50 px-3 py-1.5 text-xs font-medium text-saffron-700 transition hover:border-saffron-300 hover:bg-saffron-100"
                        >
                          {suggestion.length > 56 ? `${suggestion.slice(0, 54)}...` : suggestion}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="flex flex-col gap-3 sm:flex-row">
                    <label htmlFor="policy-analysis-input" className="sr-only">{t("auto.views.GovernmentDashboard.27")}</label>
                    <input
                      id="policy-analysis-input"
                      type="text"
                      value={currentQuery}
                      onChange={(e) => {
                        setCurrentQuery(e.target.value)
                        if (queryValidation) setQueryValidation(null)
                      }}
                      onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                      placeholder={t("auto.views.GovernmentDashboard.28")}
                      className="nrg-input min-h-12 flex-1"
                      data-testid="policy-analysis-input"
                    />
                    <motion.button
                      onClick={handleSearch}
                      disabled={isSearching || !currentQuery.trim()}
                      className="nrg-btn-primary min-h-12 w-full px-6 py-3 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      data-testid="policy-analysis-submit"
                    >
                      {isSearching ? 'Searching...' : 'Run Analysis'}
                    </motion.button>
                  </div>

                  {queryValidation && (
                    <p className="mt-2 text-sm text-rose-600" role="alert">{queryValidation}</p>
                  )}
                  {isSearching && (
                    <div className="mt-4 rounded-xl border border-saffron-200 bg-saffron-50 px-4 py-3 text-sm text-saffron-800" aria-live="polite">
                      <QueryPhaseProgress domain="policy" isSlowQuery={isSlowQuery} />
                      <p className="mt-2 text-xs">{getQueryStatusCopy({ isSlowQuery, domain: 'policy' })}</p>
                    </div>
                  )}
                  {queryError && (
                    <div className="mt-4">
                      <ErrorState
                        title={t("auto.views.GovernmentDashboard.29")}
                        message={queryError}
                        severity="error"
                        onRetry={handleSearch}
                      />
                    </div>
                  )}
                  {queryResult && !queryError && (
                    <div className="mt-4">
                      {isEmptyResultResponse(queryResult.response) ? (
                        <EmptyState
                          onPrimary={() => setCurrentQuery(buildRelaxedQuery(currentQuery))}
                          onSecondary={() => setCurrentQuery(currentQuery)}
                        />
                      ) : (
                        <AnswerPanel
                          response={queryResult.response}
                          citations={queryResult.citations || []}
                          provenance={queryResult.provenance}
                          warnings={queryResult.warnings}
                          verification_status={queryResult.verification_status}
                        />
                      )}
                    </div>
                  )}
                </div>
              </WidgetErrorBoundary>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <WidgetErrorBoundary title={t("auto.views.GovernmentDashboard.30")}>
                  <FundingTrendsLineChart
                    data={fundingTrendData}
                    title={t("auto.views.GovernmentDashboard.31")}
                    titleHi="नीति वित्त संकेत"
                    subtitle={t("auto.views.GovernmentDashboard.32")}
                  />
                </WidgetErrorBoundary>
                <WidgetErrorBoundary title={t("auto.views.GovernmentDashboard.33")}>
                  <ResearchAreasBarChart
                    data={researchAreaData.slice(0, 6)}
                    title={t("auto.views.GovernmentDashboard.34")}
                    titleHi="रणनीतिक शोध क्षेत्र"
                    subtitle={t("auto.views.GovernmentDashboard.35")}
                  />
                </WidgetErrorBoundary>
              </div>
            </motion.div>
          )}

          {activeTab === 'institutions' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <WidgetErrorBoundary title={t("auto.views.GovernmentDashboard.36")}>
                <DataTable
                  title={t("auto.views.GovernmentDashboard.37")}
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
              <WidgetErrorBoundary title={t("auto.views.GovernmentDashboard.38")}>
                <div className="nrg-panel p-5">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 flex gap-3">
                      <div className="relative flex-1 max-w-sm">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                        <input
                          type="text"
                          value={graphTopic}
                          onChange={(e) => setGraphTopic(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && setGraphTopic(graphTopic)}
                          placeholder={t("auto.views.GovernmentDashboard.39")}
                          className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-nrg-border bg-[var(--nrg-surface)] text-sm text-nrg-text placeholder:text-nrg-muted focus:outline-none focus:border-saffron-500"
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
                    className="flex items-center gap-3 p-4 rounded-xl bg-[var(--glass-bg)] border border-nrg-border"
                  >
                    <div className="w-10 h-10 rounded-lg bg-saffron-100 dark:bg-saffron-900/30 text-saffron-600 dark:text-saffron-400 flex items-center justify-center text-sm font-bold">
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
              <WidgetErrorBoundary title={t("auto.views.GovernmentDashboard.40")}>
                <DPDPPanel role="government" />
              </WidgetErrorBoundary>
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

export default GovernmentDashboard
