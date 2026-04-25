import React, { useState, useCallback, useMemo } from 'react'
import { motion } from 'framer-motion'
import { IndustryHeader } from '../components/Industry/IndustryHeader'
import { OpportunityCard, CollaborationPotentialCard } from '../components/Industry/OpportunityCards'
import { StatsCard } from '../components/StatsCard'
import { ErrorState } from '../components/ErrorState'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { WidgetErrorBoundary } from '../components/WidgetErrorBoundary'
import { AnswerPanel } from '../components/AnswerPanel'
import { DPDPConsentDialog } from '../components/DPDPConsentDialog'
import { ConsentBanner } from '../components/ConsentBanner'
import { DPDPPanel } from '../components/DPDPPanel'
import { ResearchAreasBarChart } from '../components/DataViz'
import { useAuth } from '../hooks/useAuth'
import { useDPDPStore } from '../stores/dpdpStore'
import { queryService, QueryResponse } from '../services/queryService'
import { useQuery } from '@tanstack/react-query'
import { Building2, Users, FileText, HeartHandshake, Search } from 'lucide-react'
import type { Theme } from '../hooks/useTheme'

interface IndustryDashboardProps {
  onThemeToggle: () => void
  theme: Theme
}

const AREA_COLORS = ['#10b981', '#6366f1', '#2563eb', '#ff6b35', '#ec4899', '#c49538', '#8b5cf6', '#f59e0b', '#06b6d4', '#84cc16']

export function IndustryDashboard({ onThemeToggle, theme }: IndustryDashboardProps) {
  const { user } = useAuth()
  const { addAuditEntry, grantConsent, getConsentStatus } = useDPDPStore()
  const hasExistingConsent = getConsentStatus('Research data analysis')?.granted
  const [showDPDPConsent, setShowDPDPConsent] = useState(!hasExistingConsent)
  const [activeTab, setActiveTab] = useState<'opportunities' | 'researchers' | 'analytics' | 'rights'>('opportunities')
  const [currentQuery, setCurrentQuery] = useState('')
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null)
  const [queryError, setQueryError] = useState<string | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [collaborationFilter, setCollaborationFilter] = useState<string>('all')

  const { data: statsData } = useQuery({
    queryKey: ['stats', user?.id],
    queryFn: () => queryService.fetchStats(),
    staleTime: 30 * 1000,
    enabled: !!user,
  })

  const handleSearch = useCallback(async () => {
    if (!currentQuery.trim()) return
    setIsSearching(true)
    setQueryError(null)
    try {
      const result = await queryService.query({ query: currentQuery })
      setQueryResult(result)
      addAuditEntry({ action: 'data_accessed', persona: 'industry', details: `Partnership query: ${currentQuery}` })
    } catch (err: any) {
      setQueryError(err.message || 'Search failed')
    } finally {
      setIsSearching(false)
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
        count: Math.floor(Math.random() * 300) + 100,
        color: AREA_COLORS[i % AREA_COLORS.length],
      }))
    }
    return [
      { area: 'AI & Machine Learning', count: 423, color: '#10b981' },
      { area: 'Semiconductor Tech', count: 312, color: '#6366f1' },
      { area: 'Renewable Energy', count: 287, color: '#2563eb' },
      { area: 'Biotechnology', count: 234, color: '#ff6b35' },
      { area: 'Pharmaceuticals', count: 198, color: '#ec4899' },
    ]
  }, [statsData?.research_areas])

  return (
    <ErrorBoundary title="Industry Dashboard failed to load">
      <div className="min-h-screen bg-slate-50 dark:bg-navy-900">
        <IndustryHeader onThemeToggle={onThemeToggle} theme={theme} />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-1 -mb-px overflow-x-auto border-b border-slate-200 dark:border-navy-700">
          {(['opportunities', 'researchers', 'analytics', 'rights'] as const).map((tab) => (
            <motion.button
              key={tab}
              onClick={() => setActiveTab(tab)}
              aria-label={`${tab} tab`}
              aria-current={activeTab === tab ? 'page' : undefined}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 whitespace-nowrap capitalize ${
                activeTab === tab
                  ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
                  : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:border-slate-300 dark:hover:border-navy-600'
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

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {activeTab === 'opportunities' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatsCard
                  label="Partnership Opportunities"
                  labelHi="साझेदारी के अवसर"
                  value={statsData?.total_researchers ?? 847}
                  sublabel="Active opportunities"
                  accentColor="#10b981"
                  icon={<HeartHandshake size={20} />}
                  delay={0}
                  data-testid="stat-opportunities"
                />
                <StatsCard
                  label="Partner Institutions"
                  labelHi="साझेदार संस्थान"
                  value={statsData?.total_institutions ?? 156}
                  sublabel="IITs, IISc, NITs, AIIMS"
                  accentColor="#2563eb"
                  icon={<Building2 size={20} />}
                  delay={100}
                  data-testid="stat-institutions"
                />
                <StatsCard
                  label="Active Researchers"
                  labelHi="सक्रिय शोधकर्ता"
                  value={statsData?.total_researchers ?? 3421}
                  sublabel="Available for collab"
                  accentColor="#ff6b35"
                  icon={<Users size={20} />}
                  delay={200}
                  data-testid="stat-researchers"
                />
                <StatsCard
                  label="Research Publications"
                  labelHi="शोध प्रकाशन"
                  value={statsData?.total_publications ?? 12847}
                  sublabel="In partnering institutions"
                  accentColor="#6366f1"
                  icon={<FileText size={20} />}
                  delay={300}
                  data-testid="stat-publications"
                />
              </div>

              <WidgetErrorBoundary title="Opportunities list failed to load">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                      Partnership Opportunities
                      <span className="text-sm font-normal text-slate-500 ml-2 font-devanagari">साझेदारी के अवसर</span>
                    </h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {filteredOpportunities.length} opportunities found · Anonymized researcher data
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <select
                      value={collaborationFilter}
                      onChange={(e) => setCollaborationFilter(e.target.value)}
                      className="px-3 py-2 rounded-xl border border-slate-200 dark:border-navy-600 bg-white dark:bg-navy-800 text-sm text-slate-900 dark:text-white"
                      data-testid="filter-collaboration-type"
                    >
                      <option value="all">All Types</option>
                      <option value="joint_research">Joint Research</option>
                      <option value="funding">Research Funding</option>
                      <option value="licensing">IP Licensing</option>
                      <option value="consulting">Consulting</option>
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

              <WidgetErrorBoundary title="Search panel failed to load">
                <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md p-5">
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Search Research Network</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-devanagari">शोध नेटवर्क खोजें</p>
                  </div>
                  <div className="flex gap-3">
                    <div className="flex-1 relative">
                      <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true" />
                      <label htmlFor="industry-search-input" className="sr-only">Search research network</label>
                      <input
                        id="industry-search-input"
                        type="text"
                        value={currentQuery}
                        onChange={(e) => setCurrentQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        placeholder="Search by research area, institution, or topic..."
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-navy-600 bg-white dark:bg-navy-800 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:border-emerald-500"
                        data-testid="industry-search-input"
                      />
                    </div>
                    <motion.button
                      onClick={handleSearch}
                      disabled={isSearching}
                      className="px-5 py-2.5 rounded-xl text-sm font-medium bg-gradient-to-r from-emerald-500 to-emerald-600 text-white shadow-md hover:shadow-lg disabled:opacity-50"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      data-testid="industry-search-submit"
                    >
                      {isSearching ? 'Searching...' : 'Search'}
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
                        title="Search Failed"
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
              <WidgetErrorBoundary title="Research areas chart failed to load">
                <ResearchAreasBarChart
                  data={researchAreaData}
                  title="Researcher Expertise Areas"
                  titleHi="शोधकर्ता विशेषज्ञता क्षेत्र"
                  subtitle="Distribution of anonymized researchers by expertise"
                />
              </WidgetErrorBoundary>

              <WidgetErrorBoundary title="Collaboration cards failed to load">
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

          {activeTab === 'rights' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <WidgetErrorBoundary title="Data rights panel failed to load">
                <DPDPPanel role="industry" />
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

export default IndustryDashboard
