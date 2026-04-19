import { useState, useEffect, useCallback } from 'react';
import { PermissionBoundary } from '../components/PermissionBoundary';
import { TierBadge } from '../components/TierBadge';
import { SkeletonLoader } from '../components/SkeletonLoader';
import { DPDPConsentDialog } from '../components/DPDPConsentDialog';
import { GlassCard } from '../components/GlassCard';
import { useAuth } from '../hooks/useAuth';
import { useQueryStore } from '../stores/queryStore';
import { useDPDPStore } from '../stores/dpdpStore';
import { queryService } from '../services/queryService';
import { useQuery } from '@tanstack/react-query';

export function IndustryDashboard() {
  const { user } = useAuth();
  const { history, currentQuery, isSearching, setCurrentQuery, addToHistory, setIsSearching, setLastResult } = useQueryStore();
  const { grantConsent, addAuditEntry } = useDPDPStore();

  const [isLoading, setIsLoading] = useState(true);
  const [showDPDPConsent, setShowDPDPConsent] = useState(false);
  const [dpdpApproved, setDpdpApproved] = useState(false);
  const [queryResult, setQueryResult] = useState<string | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

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
      setQueryResult(result.response);
      setLastResult(result);
      addToHistory({
        query: currentQuery,
        persona: 'industry',
        resultsCount: result.verification_status ? 10 : 0
      });
      addAuditEntry({
        action: 'data_accessed',
        persona: user?.role || 'industry',
        details: `Query: ${currentQuery}`
      });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.response?.data?.message || error.message || 'Search failed';
      setQueryError(message);
      addToHistory({
        query: currentQuery,
        persona: 'industry',
        resultsCount: 0,
        error: message
      });
    } finally {
      setIsSearching(false);
    }
  }, [currentQuery, addToHistory, addAuditEntry, setIsSearching, setLastResult, user]);

  if (isLoading) {
    return (
      <div className="iitgn-industry-dashboard min-h-screen bg-gradient-to-br from-emerald-50 to-teal-100">
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 py-4 animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-2" />
            <div className="h-4 bg-gray-100 rounded w-1/4" />
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">
          <SkeletonLoader type="list" count={3} />
        </main>
      </div>
    );
  }

  return (
    <div className="iitgn-industry-dashboard min-h-screen bg-gradient-to-br from-emerald-50 to-teal-100">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              उद्योग नवाचार मंच
            </h1>
            <p className="text-sm text-gray-500 tracking-wide">
              National Research Intelligence Platform · Industry Innovation
            </p>
          </div>
          <div className="flex items-center gap-4">
            {user && <TierBadge tier={user.tier} role={user.role} />}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <PermissionBoundary tier={3}>
          <GlassCard accent="industry" title="Research Partner Discovery" description="Find academic partners for R&D collaboration" className="mb-6">
            <div className="flex gap-2">
              <input
                type="text"
                value={currentQuery}
                onChange={(e) => setCurrentQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Enter query (e.g., 'AI researchers in Maharashtra')..."
                className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition text-sm"
              />
              <button
                onClick={handleSearch}
                disabled={isSearching || !currentQuery}
                className="px-6 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSearching ? 'Discovering...' : 'Discover'}
              </button>
            </div>

            {isSearching && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <div className="animate-spin h-4 w-4 border-2 border-emerald-500 border-t-transparent rounded-full"></div>
                  Discovering research partners...
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
                    <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                    Partner Discovery Results
                  </h3>
                </div>
                <div className="p-4">
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">{queryResult}</pre>
                </div>
              </div>
            )}
          </GlassCard>
        </PermissionBoundary>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <PermissionBoundary tier={3}>
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-emerald-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 group">
              <h2 className="text-lg font-semibold text-gray-800 mb-2 group-hover:text-emerald-600 transition">Research Capacity</h2>
              <p className="text-sm text-gray-600 mb-4">Available research capacity and expertise areas.</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-emerald-50 p-3 rounded text-center border border-emerald-100">
                  <div className="text-2xl font-bold text-emerald-700">
                    {statsLoading ? '...' : statsData?.total_researchers || 0}
                  </div>
                  <div className="text-xs text-emerald-500">Researchers</div>
                </div>
                <div className="bg-cyan-50 p-3 rounded text-center border border-cyan-100">
                  <div className="text-2xl font-bold text-cyan-700">
                    {statsLoading ? '...' : statsData?.total_publications || 0}
                  </div>
                  <div className="text-xs text-cyan-500">Publications</div>
                </div>
              </div>
            </div>
          </PermissionBoundary>

          <PermissionBoundary tier={3}>
            <div
              className="bg-white rounded-lg shadow-md p-6 border-l-4 border-cyan-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 cursor-pointer"
              onClick={() => setShowDPDPConsent(true)}
            >
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Research Expertise</h2>
              <p className="text-sm text-gray-600 mb-4">Top research specializations available.</p>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {statsLoading ? (
                  <SkeletonLoader type="list" count={3} />
                ) : statsData?.research_areas?.slice(0, 5).map((area: string) => (
                  <div key={area} className="border border-cyan-200 rounded p-2 bg-cyan-50 hover:bg-cyan-100 transition">
                    <div className="text-xs font-medium text-cyan-800">{area}</div>
                  </div>
                ))}
              </div>
            </div>
          </PermissionBoundary>

          <PermissionBoundary tier={3}>
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-amber-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Research Distribution</h2>
              <p className="text-sm text-gray-600 mb-4">Geographic distribution of research capacity.</p>
              <div className="h-32 bg-amber-50 rounded border border-amber-100 p-3 overflow-y-auto">
                {statsLoading ? (
                  <SkeletonLoader type="list" count={3} />
                ) : statsData?.state_distribution?.slice(0, 5).map((state: any) => (
                  <div key={state.state} className="flex justify-between text-xs py-1">
                    <span className="text-amber-800">{state.state}</span>
                    <span className="text-amber-600 font-medium">{state.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </PermissionBoundary>

          <PermissionBoundary tier={3}>
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-rose-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Commercial Data Compliance</h2>
              <p className="text-sm text-gray-600 mb-4">DPDP-compliant data usage for commercial research.</p>
              <div className={`p-3 rounded text-xs transition ${dpdpApproved ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}`}>
                {dpdpApproved ? (
                  <>Data agreements tracked Purpose limitation enforced</>
                ) : (
                  <>Consent required for commercial data access</>
                )}
              </div>
            </div>
          </PermissionBoundary>
        </div>

        {history.length > 0 && (
          <GlassCard accent="sovereign" title="Recent Industry Queries" className="mt-6">
            <div className="space-y-2">
              {history.slice(0, 5).map((entry) => (
                <div key={entry.id} className="text-sm py-2 border-b border-gray-100 last:border-0">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700 truncate font-medium">{entry.query}</span>
                    <span className="text-gray-400 text-xs ml-4">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                  </div>
                  {entry.error ? (
                    <div className="mt-1 text-xs text-rose-600 bg-rose-50 px-2 py-1 rounded border border-rose-100">
                      Security Message: {entry.error}
                    </div>
                  ) : (
                    <div className="text-gray-400 text-xs mt-0.5">{entry.resultsCount} potential partners found</div>
                  )}
                </div>
              ))}
            </div>
          </GlassCard>
        )}
      </main>

      <DPDPConsentDialog
        isOpen={showDPDPConsent}
        onApprove={() => {
          setDpdpApproved(true);
          setShowDPDPConsent(false);
        }}
        onDeny={() => setShowDPDPConsent(false)}
        dataPurpose="Commercial research partnership matching and market intelligence"
        retentionDays={180}
      />
    </div>
  );
}
