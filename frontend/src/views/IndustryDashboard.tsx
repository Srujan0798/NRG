import React, { useState, useCallback, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import { IndustryHeader } from '../components/Industry/IndustryHeader'
import { OpportunityCard, CollaborationPotentialCard } from '../components/Industry/OpportunityCards'
import { StatsCard } from '../components/StatsCard/StatsCard'
import { ErrorState } from '../components/ErrorState/ErrorState'
import { ErrorBoundary, WidgetErrorBoundary } from '../components/ErrorBoundary/ErrorBoundary'
import { AnswerPanel } from '../components/AnswerPanel/AnswerPanel'
import { DPDPConsentDialog } from '../components/DPDPConsentDialog'
import { ConsentBanner } from '../components/ConsentBanner'
import { DPDPPanel } from '../components/DPDPPanel'
import { EmptyState } from '../components/EmptyState/EmptyState'
import { QueryPhaseProgress } from '../components/QueryPhaseProgress'
import { ResearchAreasBarChart } from '../components/DataViz/ResearchAreasBarChart'
import { TierDataNotice } from '../components/TierDataNotice'
import { useAuth } from '../hooks/useAuth'
import { useDPDPStore } from '../stores/dpdpStore'
import { queryService, QueryResponse } from '../services/queryService'
import { getDashboardDocumentTitle, getQueryStatusCopy } from '../utils/dashboardCopy'
import { buildRelaxedQuery, isEmptyResultResponse } from '../utils/emptyResults'
import { useQuery } from '@tanstack/react-query'
import { Building2, Users, FileText, HeartHandshake, Search } from 'lucide-react'
import type { Theme } from '../hooks/useTheme'
import { t } from '../i18n'

interface IndustryDashboardProps {
  onThemeToggle: () => void
  theme: Theme
}

const AREA_COLORS = ['var(--nrg-chart-3)', 'var(--nrg-chart-5)', 'var(--nrg-chart-2)', 'var(--nrg-chart-1)', 'var(--nrg-chart-6)', 'var(--nrg-chart-4)', 'var(--nrg-chart-7)', 'var(--nrg-warning)', 'var(--nrg-chart-9)', 'var(--nrg-chart-10)']

const INDUSTRY_QUERY_SUGGESTIONS = [
  'What AI capabilities do Indian research institutions offer?',
  'Find industry-academia collaboration examples in renewable energy',
  'Which institutions are strongest for semiconductor partnerships?',
]

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
  return detail || 'NRG could not complete this request. Your audit trail is safe; refine the query or retry.'
}

export function IndustryDashboard({ onThemeToggle, theme }: IndustryDashboardProps) {
  const { user } = useAuth()
  const { addAuditEntry, grantConsent, getConsentStatus } = useDPDPStore()
  const hasExistingConsent = getConsentStatus('research_access')?.granted
  const [showDPDPConsent, setShowDPDPConsent] = useState(!hasExistingConsent)
  const [activeTab, setActiveTab] = useState<'opportunities' | 'researchers' | 'analytics' | 'rights'>('opportunities')
  const [currentQuery, setCurrentQuery] = useState('')
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null)
  const [queryError, setQueryError] = useState<string | null>(null)
  const [queryValidation, setQueryValidation] = useState<string | null>(null)
  const [isSlowQuery, setIsSlowQuery] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [collaborationFilter, setCollaborationFilter] = useState<string>('all')

  const { data: statsData } = useQuery({
    queryKey: ['stats', user?.id],
    queryFn: () => queryService.fetchStats(),
    staleTime: 30 * 1000,
    enabled: !!user,
  })

  useEffect(() => {
    document.title = getDashboardDocumentTitle('industry', activeTab)
  }, [activeTab])

  const handleSearch = useCallback(async () => {
    const submittedQuery = currentQuery.trim()
    if (!submittedQuery) {
      setQueryValidation('Enter a research question before searching.')
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
      addAuditEntry({ action: 'data_accessed', persona: 'industry', details: `Partnership query: ${submittedQuery}` })
    } catch (err: any) {
      setQueryError(toFriendlyQueryError(err))
    } finally {
      window.clearTimeout(slowTimer)
      setIsSearching(false)
      setIsSlowQuery(false)
    }
  }, [currentQuery, addAuditEntry])

  const opportunities = useMemo(() => [
    {
      id: '1',
      title: 'Joint AI Research Initiative',
      titleHi: 'संयुक्त एआई शोध पहल',
      institution: 'IIT Delhi',
      researchArea: 'Artificial Intelligence',
      collaborationType: 'joint_research' as const,
      potential: 'high' as const,
      matchScore: 92,
      description: 'Seeking industry partners for applied AI research in healthcare diagnostics. Government funded, IP shared.',
    },
    {
      id: '2',
      title: 'Battery Technology Licensing',
      titleHi: 'बैटरी प्रौद्योगिकी लाइसेंसिंग',
      institution: 'IISc Bangalore',
      researchArea: 'Renewable Energy',
      collaborationType: 'licensing' as const,
      potential: 'high' as const,
      matchScore: 88,
      description: 'Advanced solid-state battery technology ready for commercialization. Exclusive licensing available.',
    },
    {
      id: '3',
      title: 'Semiconductor Research Partnership',
      titleHi: 'अर्धचालक शोध साझेदारी',
      institution: 'IIT Bombay',
      researchArea: 'Semiconductor',
      collaborationType: 'joint_research' as const,
      potential: 'medium' as const,
      matchScore: 76,
      description: 'Collaborative research on next-generation chip design. India semiconductor mission aligned.',
    },
    {
      id: '4',
      title: 'Pharmaceutical Research Funding',
      titleHi: 'फार्मास्यूटिकल शोध वित्तपोषण',
      institution: 'NIPER',
      researchArea: 'Pharmaceuticals',
      collaborationType: 'funding' as const,
      potential: 'high' as const,
      matchScore: 85,
      description: 'Novel drug delivery systems research seeking industrial funding partner for clinical trials.',
    },
    {
      id: '5',
      title: 'Quantum Computing Consulting',
      titleHi: 'क्वांटम कंप्यूटिंग परामर्श',
      institution: 'IIT Madras',
      researchArea: 'Quantum Computing',
      collaborationType: 'consulting' as const,
      potential: 'medium' as const,
      matchScore: 71,
      description: 'Expert consulting on quantum cryptography implementation for financial sector.',
    },
    {
      id: '6',
      title: 'Electric Vehicle Infrastructure Research',
      titleHi: 'इलेक्ट्रिक वाहन अवसंरचना शोध',
      institution: 'IIT Delhi',
      researchArea: 'Electric Vehicles',
      collaborationType: 'joint_research' as const,
      potential: 'high' as const,
      matchScore: 90,
      description: 'EV charging infrastructure optimization research with real-world deployment pilot.',
    },
  ], [])

  const filteredOpportunities = useMemo(() => {
    if (collaborationFilter === 'all') return opportunities
    return opportunities.filter(o => o.collaborationType === collaborationFilter)
  }, [opportunities, collaborationFilter])

  const consentExpiringCount = useDPDPStore((s) => {
    const threshold = Date.now() + 30 * 24 * 60 * 60 * 1000;
    return Object.values(s.consents).filter((c) => c.expiresAt && c.expiresAt < threshold && c.granted).length;
  })

  const researchAreaData = useMemo(() => {
    if (statsData?.research_areas?.length) {
      return statsData.research_areas.map((r: string, i: number) => ({
        area: r,
        count: Math.max(90, 420 - i * 37),
        color: AREA_COLORS[i % AREA_COLORS.length],
      }))
    }
    return [
      { area: 'AI & Machine Learning', count: 423, color: 'var(--nrg-chart-3)' },
      { area: 'Semiconductor Tech', count: 312, color: 'var(--nrg-chart-5)' },
      { area: 'Renewable Energy', count: 287, color: 'var(--nrg-chart-2)' },
      { area: 'Biotechnology', count: 234, color: 'var(--nrg-chart-1)' },
      { area: 'Pharmaceuticals', count: 198, color: 'var(--nrg-chart-6)' },
    ]
  }, [statsData?.research_areas])

  return (
    <ErrorBoundary title={t("auto.views.IndustryDashboard.1")}>
      <div className="nrg-app-canvas min-h-screen">
        <IndustryHeader onThemeToggle={onThemeToggle} theme={theme} />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-2 -mb-px overflow-x-auto border-b border-nrg-border">
          {(['opportunities', 'researchers', 'analytics', 'rights'] as const).map((tab) => (
            <motion.button
              key={tab}
              onClick={() => setActiveTab(tab)}
              aria-label={`${tab} tab`}
              aria-current={activeTab === tab ? 'page' : undefined}
              className={`nrg-tab flex items-center gap-1.5 whitespace-nowrap rounded-t-xl capitalize ${
                activeTab === tab
                  ? 'active'
                  : 'text-nrg-muted hover:text-nrg-text'
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              data-testid={`tab-${tab}`}
            >
              {tab}
            </motion.button>
          ))}
        </div>

        <ConsentBanner
          role="industry"
          expiringCount={consentExpiringCount}
        />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <TierDataNotice />
        </div>

        <main id="main-content" tabIndex={-1} className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 relative z-10">
          {activeTab === 'opportunities' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatsCard
                  label={t("auto.views.IndustryDashboard.2")}
                  labelHi="साझेदारी के अवसर"
                  value={statsData?.total_researchers ?? 847}
                  sublabel="Active opportunities"
                  accentColor="var(--nrg-chart-3)"
                  icon={<HeartHandshake size={20} />}
                  delay={0}
                  data-testid="stat-opportunities"
                />
                <StatsCard
                  label={t("auto.views.IndustryDashboard.3")}
                  labelHi="साझेदार संस्थान"
                  value={statsData?.total_institutions ?? 156}
                  sublabel="IITs, IISc, NITs, AIIMS"
                  accentColor="var(--nrg-chart-2)"
                  icon={<Building2 size={20} />}
                  delay={100}
                  data-testid="stat-institutions"
                />
                <StatsCard
                  label={t("auto.views.IndustryDashboard.4")}
                  labelHi="सक्रिय शोधकर्ता"
                  value={statsData?.total_researchers ?? 3421}
                  sublabel="Available for collab"
                  accentColor="var(--nrg-chart-1)"
                  icon={<Users size={20} />}
                  delay={200}
                  data-testid="stat-researchers"
                />
                <StatsCard
                  label={t("auto.views.IndustryDashboard.5")}
                  labelHi="शोध प्रकाशन"
                  value={statsData?.total_publications ?? 12847}
                  sublabel="In partnering institutions"
                  accentColor="var(--nrg-chart-5)"
                  icon={<FileText size={20} />}
                  delay={300}
                  data-testid="stat-publications"
                />
              </div>

              <WidgetErrorBoundary title={t("auto.views.IndustryDashboard.6")}>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-nrg-text">
                      {t("auto.views.IndustryDashboard.7")}<span className="text-sm font-normal text-nrg-muted ml-2 font-devanagari">साझेदारी के अवसर</span>
                    </h2>
                    <p className="text-sm text-nrg-muted">
                      {filteredOpportunities.length} {t("auto.views.IndustryDashboard.8")}</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <select
                      value={collaborationFilter}
                      onChange={(e) => setCollaborationFilter(e.target.value)}
                      aria-label={t("auto.views.IndustryDashboard.9")}
                      className="px-3 py-2 rounded-xl border border-nrg-border bg-[var(--nrg-surface)] text-sm text-nrg-text"
                      data-testid="filter-collaboration-type"
                    >
                      <option value="all">{t("auto.views.IndustryDashboard.9")}</option>
                      <option value="joint_research">{t("auto.views.IndustryDashboard.10")}</option>
                      <option value="funding">{t("auto.views.IndustryDashboard.11")}</option>
                      <option value="licensing">{t("auto.views.IndustryDashboard.12")}</option>
                      <option value="consulting">{t("auto.views.IndustryDashboard.13")}</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredOpportunities.map((opp, i) => (
                    <motion.div
                      key={opp.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <OpportunityCard {...opp} />
                    </motion.div>
                  ))}
                </div>
              </WidgetErrorBoundary>

              <WidgetErrorBoundary title={t("auto.views.IndustryDashboard.14")}>
                <div className="nrg-panel p-5">
                  <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                    <div>
                      <h3 className="text-sm font-semibold text-nrg-text">{t("auto.views.IndustryDashboard.15")}</h3>
                      <p className="text-xs text-nrg-muted">{t("auto.views.IndustryDashboard.16")}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {INDUSTRY_QUERY_SUGGESTIONS.map((suggestion) => (
                        <button
                          key={suggestion}
                          type="button"
                          onClick={() => {
                            setCurrentQuery(suggestion)
                            setQueryValidation(null)
                          }}
                          className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 transition hover:border-emerald-300 hover:bg-emerald-100 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200"
                        >
                          {suggestion.length > 56 ? `${suggestion.slice(0, 54)}...` : suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex flex-col gap-3 sm:flex-row">
                    <div className="relative flex-1">
                      <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-nrg-muted" aria-hidden="true" />
                      <label htmlFor="industry-search-input" className="sr-only">{t("auto.views.IndustryDashboard.17")}</label>
                      <input
                        id="industry-search-input"
                        type="text"
                        value={currentQuery}
                        onChange={(e) => {
                          setCurrentQuery(e.target.value)
                          if (queryValidation) setQueryValidation(null)
                        }}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        placeholder={t("auto.views.IndustryDashboard.18")}
                        className="min-h-12 w-full rounded-xl border border-nrg-border bg-[var(--nrg-surface)] py-2.5 pl-10 pr-4 text-sm text-nrg-text placeholder:text-nrg-muted focus:border-emerald-500 focus:outline-none"
                        data-testid="industry-search-input"
                      />
                    </div>
                    <motion.button
                      onClick={handleSearch}
                      disabled={isSearching || !currentQuery.trim()}
                      className="min-h-12 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-5 py-2.5 text-sm font-medium text-white shadow-md hover:shadow-lg disabled:opacity-50 sm:w-auto"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      data-testid="industry-search-submit"
                    >
                      {isSearching ? 'Searching...' : 'Search'}
                    </motion.button>
                  </div>
                  {queryValidation && (
                    <p className="mt-2 text-sm text-rose-600" role="alert">{queryValidation}</p>
                  )}
                  {isSearching && (
                    <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-100" aria-live="polite">
                      <QueryPhaseProgress domain="industry" isSlowQuery={isSlowQuery} />
                      <p className="mt-2 text-xs">{getQueryStatusCopy({ isSlowQuery, domain: 'industry' })}</p>
                    </div>
                  )}
                  {queryResult && (
                    <div className="mt-4">
                      {isEmptyResultResponse(queryResult.response) ? (
                        <EmptyState
                          title={t("auto.views.IndustryDashboard.19")}
                          body="Try widening sector, maturity, or state filters. Industry mode only shows anonymized aggregate opportunities."
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
                          answer_confidence={queryResult.answer_confidence}
                          sqlQuery={queryResult.sql_query}
                          rowsReturned={queryResult.sql_results?.length}
                          auditEventId={queryResult.audit_event_id || queryResult.query_id}
                        />
                      )}
                    </div>
                  )}
                  {queryError && (
                    <div className="mt-4">
                      <ErrorState
                        title={t("auto.views.IndustryDashboard.20")}
                        message={queryError}
                        severity="error"
                        onRetry={handleSearch}
                      />
                    </div>
                  )}
                </div>
              </WidgetErrorBoundary>
            </motion.div>
          )}

          {activeTab === 'researchers' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <WidgetErrorBoundary title={t("auto.views.IndustryDashboard.21")}>
                <ResearchAreasBarChart
                  data={researchAreaData}
                  title={t("auto.views.IndustryDashboard.22")}
                  titleHi="शोधकर्ता विशेषज्ञता क्षेत्र"
                  subtitle={t("auto.views.IndustryDashboard.23")}
                />
              </WidgetErrorBoundary>

              <WidgetErrorBoundary title={t("auto.views.IndustryDashboard.24")}>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[
                    { institution: 'IIT Delhi', institutionHi: 'आईआईटी दिल्ली', researcherCount: 1245, collaborationTypes: ['Joint Research', 'Consulting'], topAreas: ['AI', 'Robotics'], matchScore: 88 },
                    { institution: 'IISc Bangalore', institutionHi: 'आईएससी बेंगलुरु', researcherCount: 892, collaborationTypes: ['Joint Research', 'Licensing', 'Funding'], topAreas: ['Biotech', 'Materials'], matchScore: 85 },
                    { institution: 'IIT Bombay', institutionHi: 'आईआईटी बॉम्बे', researcherCount: 1456, collaborationTypes: ['Joint Research', 'Consulting'], topAreas: ['Semiconductors', 'AI'], matchScore: 91 },
                    { institution: 'AIIMS Delhi', institutionHi: 'एम्स दिल्ली', researcherCount: 567, collaborationTypes: ['Funding', 'Joint Research'], topAreas: ['Medical', 'Biotech'], matchScore: 79 },
                    { institution: 'IIT Madras', institutionHi: 'आईआईटी मद्रास', researcherCount: 1089, collaborationTypes: ['Consulting', 'Joint Research'], topAreas: ['Quantum', 'AI'], matchScore: 83 },
                    { institution: 'NIT Surathkal', institutionHi: 'एनआईटी सूरतकल', researcherCount: 678, collaborationTypes: ['Joint Research'], topAreas: ['Energy', 'EV'], matchScore: 76 },
                  ].map((inst, i) => (
                    <motion.div
                      key={inst.institution}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <CollaborationPotentialCard {...inst} />
                    </motion.div>
                  ))}
                </div>
              </WidgetErrorBoundary>
            </motion.div>
          )}

          {activeTab === 'analytics' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <WidgetErrorBoundary title={t("auto.views.IndustryDashboard.25")}>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-2">
                    <ResearchAreasBarChart
                      data={researchAreaData}
                      title={t("auto.views.IndustryDashboard.26")}
                      titleHi="वाणिज्यिक शोध मांग"
                      subtitle={t("auto.views.IndustryDashboard.27")}
                    />
                  </div>
                  <div className="nrg-panel p-5">
                    <h2 className="text-base font-semibold text-nrg-text">{t("auto.views.IndustryDashboard.28")}</h2>
                    <p className="mt-1 text-sm text-nrg-muted">{t("auto.views.IndustryDashboard.29")}</p>
                    <div className="mt-5 space-y-4">
                      {[
                        ['High-potential matches', '4 of 6', 'text-emerald-600'],
                        ['IP licensing candidates', '1 active', 'text-blue-600'],
                        ['Joint research candidates', '3 active', 'text-saffron-700'],
                      ].map(([label, value, color]) => (
                        <div key={label} className="flex items-center justify-between rounded-xl border border-nrg-border bg-[var(--glass-bg)] px-4 py-3">
                          <span className="text-sm text-slate-600 dark:text-slate-300">{label}</span>
                          <span className={`text-sm font-semibold ${color}`}>{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </WidgetErrorBoundary>
            </motion.div>
          )}

          {activeTab === 'rights' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <WidgetErrorBoundary title={t("auto.views.IndustryDashboard.30")}>
                <DPDPPanel role="industry" />
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

export default IndustryDashboard
