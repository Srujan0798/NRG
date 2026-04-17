import { useState, useEffect } from 'react';
import { PermissionBoundary } from '../components/PermissionBoundary';
import { TierBadge } from '../components/TierBadge';
import { SkeletonLoader } from '../components/SkeletonLoader';
import { DPDPConsentDialog } from '../components/DPDPConsentDialog';
import { useAuth } from '../hooks/useAuth';

export function IndustryDashboard() {
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [showDPDPConsent, setShowDPDPConsent] = useState(false);
  const [dpdpApproved, setDpdpApproved] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 1200);
    return () => clearTimeout(timer);
  }, []);

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
      {/* Devanagari Header */}
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

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Technology Transfer */}
          <PermissionBoundary tier={3}>
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-emerald-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 group">
              <h2 className="text-lg font-semibold text-gray-800 mb-2 group-hover:text-emerald-600 transition">🔄 Technology Transfer</h2>
              <p className="text-sm text-gray-600 mb-4">Patents, licenses, and commercialization opportunities.</p>
              <div className="space-y-2">
                <div className="text-xs bg-emerald-50 p-2 rounded text-emerald-700 border border-emerald-100">14 patents available for licensing</div>
                <div className="text-xs bg-emerald-50 p-2 rounded text-emerald-700 border border-emerald-100">3 active industry partnerships</div>
                <button className="mt-2 w-full bg-emerald-600 text-white py-2 rounded-md hover:bg-emerald-700 transition text-sm font-medium">
                  Explore Patents
                </button>
              </div>
            </div>
          </PermissionBoundary>

          {/* Research Partnership Matching */}
          <PermissionBoundary tier={3}>
            <div 
              className="bg-white rounded-lg shadow-md p-6 border-l-4 border-cyan-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 cursor-pointer"
              onClick={() => setShowDPDPConsent(true)}
            >
              <h2 className="text-lg font-semibold text-gray-800 mb-2">🤝 Partnership Matching</h2>
              <p className="text-sm text-gray-600 mb-4">AI-matched academic partners for industry challenges.</p>
              <div className="space-y-2">
                <div className="border border-cyan-200 rounded p-2 bg-cyan-50 hover:bg-cyan-100 transition">
                  <div className="text-xs font-medium text-cyan-800">IIT Bombay - AI/ML</div>
                  <div className="text-xs text-cyan-600">98% match for your R&D needs</div>
                </div>
                <div className="border border-cyan-200 rounded p-2 bg-cyan-50 hover:bg-cyan-100 transition">
                  <div className="text-xs font-medium text-cyan-800">IISc - Materials Science</div>
                  <div className="text-xs text-cyan-600">87% match for your R&D needs</div>
                </div>
              </div>
            </div>
          </PermissionBoundary>

          {/* Market Intelligence */}
          <PermissionBoundary tier={3}>
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-amber-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
              <h2 className="text-lg font-semibold text-gray-800 mb-2">📈 Market Intelligence</h2>
              <p className="text-sm text-gray-600 mb-4">Research trends aligned with market opportunities.</p>
              <div className="h-32 bg-amber-50 rounded border border-amber-100 flex items-center justify-center text-amber-400 text-sm">
                [Trend Analysis Chart]
              </div>
            </div>
          </PermissionBoundary>

          {/* DPDP Commercial Compliance */}
          <PermissionBoundary tier={3}>
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-rose-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
              <h2 className="text-lg font-semibold text-gray-800 mb-2">⚖️ Commercial Data Compliance</h2>
              <p className="text-sm text-gray-600 mb-4">DPDP-compliant data usage for commercial research.</p>
              <div className={`p-3 rounded text-xs transition ${dpdpApproved ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}`}>
                {dpdpApproved ? (
                  <>✅ Data agreements tracked · Purpose limitation enforced</>
                ) : (
                  <>⚠️ Consent required for commercial data access</>
                )}
              </div>
            </div>
          </PermissionBoundary>
        </div>
      </main>

      {/* DPDP Consent Dialog */}
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
