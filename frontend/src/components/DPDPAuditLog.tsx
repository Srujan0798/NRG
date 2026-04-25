import { useDPDPStore } from '../stores/dpdpStore';
import { useState } from 'react';

export function DPDPAuditLog() {
  const { auditLog, clearAuditLog } = useDPDPStore();
  const [verifyStatus, setVerifyStatus] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);

  const formatTimestamp = (ts: number) => {
    return new Date(ts).toLocaleString('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  };

  const getActionBadge = (action: string) => {
    const map: Record<string, string> = {
      consent_granted: 'bg-green-100 text-green-700 border-green-200',
      consent_withdrawn: 'bg-red-100 text-red-700 border-red-200',
      data_accessed: 'bg-blue-100 text-blue-700 border-blue-200',
      purpose_limitation: 'bg-amber-100 text-amber-700 border-amber-200',
      data_export: 'bg-purple-100 text-purple-700 border-purple-200',
    };
    return map[action] || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const verifyIntegrity = async () => {
    setVerifying(true);
    setVerifyStatus(null);
    try {
      const response = await fetch('/health', { signal: AbortSignal.timeout(5000) });
      const payload = await response.json();
      const chainValid = payload?.audit?.chain_valid;
      const chainLength = payload?.audit?.chain_length ?? 0;
      setVerifyStatus(chainValid === false
        ? `Audit chain integrity compromised across ${chainLength.toLocaleString('en-IN')} events.`
        : `Audit chain intact across ${chainLength.toLocaleString('en-IN')} events.`
      );
    } catch {
      setVerifyStatus('Unable to verify integrity right now. Please try again.');
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-800"><span aria-hidden="true">📋</span> DPDP Audit Log</h3>
          <p className="text-xs text-gray-500">Sovereign compliance trail (last {auditLog.length} entries)</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={verifyIntegrity}
            disabled={verifying}
            className="text-xs font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50 transition"
          >
            {verifying ? 'Verifying...' : 'Verify integrity'}
          </button>
          {auditLog.length > 0 && (
            <button
              onClick={clearAuditLog}
              className="text-xs text-gray-500 hover:text-red-600 transition"
              aria-label="Clear audit log"
            >
              Clear Log
            </button>
          )}
        </div>
      </div>

      {verifyStatus && (
        <div className="mx-4 mt-4 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">
          {verifyStatus}
        </div>
      )}

      {auditLog.length === 0 ? (
        <div className="p-8 text-center text-gray-400 text-sm">
          No audit entries yet. Actions will be logged here.
        </div>
      ) : (
        <div className="max-h-80 overflow-y-auto scrollbar-thin">
          {auditLog.map((entry) => (
            <div key={entry.id} className="px-4 py-3 border-b border-gray-100 hover:bg-gray-50 transition text-sm">
              <div className="flex items-center gap-2 mb-1">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getActionBadge(entry.action)}`}>
                  {entry.action.replace(/_/g, ' ')}
                </span>
                <span className="text-gray-400 text-xs">{formatTimestamp(entry.timestamp)}</span>
              </div>
              <div className="text-gray-700">{entry.details}</div>
              {entry.ip && <div className="text-gray-400 text-xs mt-0.5">IP: {entry.ip}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
