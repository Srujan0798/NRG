import { useState, useEffect, useCallback } from 'react';
import { PermissionBoundary } from '../components/PermissionBoundary';
import { TierBadge } from '../components/TierBadge';
import { SkeletonLoader } from '../components/SkeletonLoader';
import { DPDPConsentDialog } from '../components/DPDPConsentDialog';
import { GlassCard } from '../components/GlassCard';
import { useAuth } from '../hooks/useAuth';
import { useQueryStore } from '../stores/queryStore';
import { useDPDPStore } from '../stores/dpdpStore';
import { queryService, QueryResponse } from '../services/queryService';
import { useQuery } from '@tanstack/react-query';
import { AnswerPanel } from '../components/AnswerPanel';

export function GovernmentDashboard() {
  const { user } = useAuth();
  const { history, currentQuery, isSearching, setCurrentQuery, addToHistory, setIsSearching, setLastResult } = useQueryStore();
  const { grantConsent, addAuditEntry } = useDPDPStore();

  const [isLoading, setIsLoading] = useState(true);
  const [showDPDPConsent, setShowDPDPConsent] = useState(false);
  const [dpdpApproved, setDpdpApproved] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

  // React Query for stats
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', user?.id],
    queryFn: () => queryService.fetchStats(),
    staleTime: 30 * 1000,
    enabled: !!user,
  });

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 1200);
    return () => clearTimeout(timer);
  }, []);

  const handleSearch = useCallback(async () => {
    if (!currentQuery.trim()) return;

    setIsSearching(true);
      setQueryResult(null);
      setQueryError(null);
      try {
        const result = await queryService.query({ query: currentQuery });
      setQueryResult(result);
      setLastResult(result);
      addToHistory({
        query: currentQuery,
        persona: 'government',
        resultsCount: result.verification_status ? 10 : 0
      });
      addAuditEntry({
        action: 'data_accessed',
        persona: user?.role || 'government',
        details: `Query: ${currentQuery}`
      });
    } catch (error: any) {
      console.error('Search error:', error);
      const message = error.response?.data?.detail || error.response?.data?.message || error.message || 'Search failed';
      setQueryError(message);
      addToHistory({
        query: currentQuery,
        persona: 'government',
        resultsCount: 0,
        error: message
      });
    } finally {
      setIsSearching(false);
    }
  }, [currentQuery, addToHistory, addAuditEntry, setIsSearching, setLastResult, user]);

  if (isLoading) {
    return (
      <div className="iitgn-government-dashboard min-h-screen bg-gradient-to-br from-slate-50 to-gray-200">
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 py-4 animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-2" />
            <div className="h-4 bg-gray-100 rounded w-1/4" />
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">
          <SkeletonLoader type="chart" />
        </main>
      </div>
    );
  }

  return (
    <div className="iitgn-government-dashboard min-h-screen bg-gradient-to-br from-slate-50 to-gray-200">
      {/* Devanagari Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              राष्ट्रीय नीति विश्लेषण
            </h1>
            <p className="text-sm text-gray-500 tracking-wide">
              National Research Intelligence Platform · Government Analytics
            </p>
          </div>
          <div className="flex items-center gap-4">
            {user && <TierBadge tier={user.tier} role={user.role} />}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Query Interface */}
        <PermissionBoundary tier={2}>
          <GlassCard accent="government" title="National Research Query" description="Query across aggregated research data" className="mb-6">
            <div className="flex gap-2">
              <input
                type="text"
                value={currentQuery}
                onChange={(e) => setCurrentQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Enter query (e.g., 'Research trends in Gujarat')..."
                className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition text-sm"
              />
              <button
                onClick={handleSearch}
                disabled={isSearching || !currentQuery}
                className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSearching ? 'Analyzing...' : 'Query'}
              </button>
            </div>

            {isSearching && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  Analyzing national research data...
                </div>
              </div>
            )}

            {queryError && (
              <div className="mt-4 p-4 bg-rose-50 rounded-lg border border-rose-200">
                <div className="flex items-start gap-2">
                  <span className="text-rose-500">⚠️</span>
                  <div className="text-sm text-rose-700">
                    <span className="font-semibold">Error:</span> {queryError}
                  </div>
                </div>
              </div>
            )}

            {queryResult && (
              <div className="mt-4 bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
                  <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    Research Intelligence Report
                  </h3>
                </div>
                <div className="p-4">
                  <AnswerPanel
                    response={queryResult.response}
                    citations={queryResult.citations || []}
                    provenance={queryResult.provenance}
                    warnings={queryResult.warnings}
                  />
                </div>
              </div>
            )}
          </GlassCard>
        </PermissionBoundary>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* National Metrics */}
          <PermissionBoundary tier={2}>
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-600 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 group">
              <h2 className="text-lg font-semibold text-gray-800 mb-2 group-hover:text-blue-600 transition">📊 National Research Metrics</h2>
              <p className="text-sm text-gray-600 mb-4">Aggregate publication output and research capacity.</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-blue-50 p-3 rounded text-center border border-blue-100">
                  <div className="text-2xl font-bold text-blue-700">
                    {statsLoading ? '...' : statsData?.total_researchers?.toLocaleString() || 0}
                  </div>
                  <div className="text-xs text-blue-500">Researchers</div>
                </div>
                <div className="bg-green-50 p-3 rounded text-center border border-green-100">
                  <div className="text-2xl font-bold text-green-700">
                    {statsLoading ? '...' : statsData?.total_publications?.toLocaleString() || 0}
                  </div>
                  <div className="text-xs text-green-500">Publications</div>
                </div>
              </div>
            </div>
          </PermissionBoundary>

          {/* Research Areas Distribution */}
          <PermissionBoundary tier={2}>
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-teal-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 group">
              <h2 className="text-lg font-semibold text-gray-800 mb-2 group-hover:text-teal-600 transition">📋 Research Areas</h2>
              <p className="text-sm text-gray-600 mb-4">Distribution by research specialization.</p>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {statsLoading ? (
                  <SkeletonLoader type="list" count={3} />
                ) : statsData?.research_area_distribution?.slice(0, 5).map((area: any) => (
                  <div key={area.area} className="flex justify-between items-center text-xs bg-teal-50 p-2 rounded border border-teal-100">
                    <span className="text-teal-800 font-medium">{area.area}</span>
                    <span className="text-teal-600">{area.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </PermissionBoundary>

          {/* State Distribution */}
          <PermissionBoundary tier={2}>
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-orange-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
              <h2 className="text-lg font-semibold text-gray-800 mb-2">🗺️ State Distribution</h2>
              <p className="text-sm text-gray-600 mb-4">Geographic distribution of researchers.</p>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {statsLoading ? (
                  <SkeletonLoader type="list" count={3} />
                ) : statsData?.state_distribution?.slice(0, 5).map((state: any) => (
                  <div key={state.state} className="flex justify-between items-center text-xs bg-orange-50 p-2 rounded border border-orange-100">
                    <span className="text-orange-800 font-medium">{state.state}</span>
                    <span className="text-orange-600">{state.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </PermissionBoundary>

          {/* DPDP Compliance Dashboard */}
          <PermissionBoundary tier={2}>
            <div
              className="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 cursor-pointer"
              onClick={() => setShowDPDPConsent(true)}
            >
              <h2 className="text-lg font-semibold text-gray-800 mb-2">🔒 Sovereign Data Compliance</h2>
              <p className="text-sm text-gray-600 mb-4">DPDP Act 2023 compliance monitoring and audit trails.</p>
              <div className={`p-3 rounded text-xs transition ${dpdpApproved ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                {dpdpApproved ? (
                  <>✅ Audit logs active · Consent framework operational</>
                ) : (
                  <>⚠️ Authorization required for full audit access</>
                )}
              </div>
            </div>
          </PermissionBoundary>
        </div>

        {/* Query History */}
        {history.length > 0 && (
          <GlassCard accent="sovereign" title="Recent Government Queries" className="mt-6">
            <div className="space-y-2">
              {history.slice(0, 5).map((entry) => (
                <div key={entry.id} className="text-sm py-2 border-b border-gray-100 last:border-0">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700 truncate font-medium">{entry.query}</span>
                    <span className="text-gray-400 text-xs ml-4">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                  </div>
                  {entry.error ? (
                    <div className="mt-1 text-xs text-rose-600 bg-rose-50 px-2 py-1 rounded border border-rose-100">
                      🛡️ Security Message: {entry.error}
                    </div>
                  ) : (
                    <div className="text-gray-400 text-xs mt-0.5">{entry.resultsCount} results found</div>
                  )}
                </div>
              ))}
            </div>
          </GlassCard>
        )}
      </main>

      {/* DPDP Consent Dialog */}
      <DPDPConsentDialog
        isOpen={showDPDPConsent}
        onApprove={() => {
          setDpdpApproved(true);
          setShowDPDPConsent(false);
        }}
        onDeny={() => setShowDPDPConsent(false)}
        dataPurpose="Government analytics and policy impact assessment"
        retentionDays={730}
      />
    </div>
  );
}
