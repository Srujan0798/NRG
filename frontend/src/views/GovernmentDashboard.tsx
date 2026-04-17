import { useState, useEffect } from 'react';
import { PermissionBoundary } from '../components/PermissionBoundary';
import { TierBadge } from '../components/TierBadge';
import { SkeletonLoader } from '../components/SkeletonLoader';
import { DPDPConsentDialog } from '../components/DPDPConsentDialog';
import { useAuth } from '../hooks/useAuth';

export function GovernmentDashboard() {
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* National Metrics */}
          <PermissionBoundary tier={2}>
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-600 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 group">
              <h2 className="text-lg font-semibold text-gray-800 mb-2 group-hover:text-blue-600 transition">📊 National Research Metrics</h2>
              <p className="text-sm text-gray-600 mb-4">Aggregate publication output, citation indices, and funding ROI.</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-blue-50 p-3 rounded text-center border border-blue-100">
                  <div className="text-2xl font-bold text-blue-700">12,847</div>
                  <div className="text-xs text-blue-500">Publications (FY25)</div>
                </div>
                <div className="bg-green-50 p-3 rounded text-center border border-green-100">
                  <div className="text-2xl font-bold text-green-700">₹4.2Cr</div>
                  <div className="text-xs text-green-500">Research Funding</div>
                </div>
              </div>
            </div>
          </PermissionBoundary>

          {/* Institutional Heatmap */}
          <PermissionBoundary tier={2}>
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-orange-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
              <h2 className="text-lg font-semibold text-gray-800 mb-2">🗺️ Institutional Heatmap</h2>
              <p className="text-sm text-gray-600 mb-4">Geographic distribution of research output across India.</p>
              <div className="h-32 bg-orange-50 rounded border border-orange-100 flex items-center justify-center text-orange-400 text-sm">
                [India Map Visualization]
              </div>
            </div>
          </PermissionBoundary>

          {/* Policy Impact Analysis */}
          <PermissionBoundary tier={2}>
            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-teal-500 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 group">
              <h2 className="text-lg font-semibold text-gray-800 mb-2 group-hover:text-teal-600 transition">📋 Policy Impact Analysis</h2>
              <p className="text-sm text-gray-600 mb-4">Correlate policy changes with research outcomes.</p>
              <div className="space-y-2">
                <div className="text-xs bg-teal-50 p-2 rounded text-teal-700 border border-teal-100">NEP 2020 Impact: +18% STEM output</div>
                <div className="text-xs bg-teal-50 p-2 rounded text-teal-700 border border-teal-100">NRF Funding: +24% interdisciplinary</div>
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
