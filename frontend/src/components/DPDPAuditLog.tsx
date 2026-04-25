import { useDPDPStore } from '../stores/dpdpStore';
import { format } from 'date-fns';

export function DPDPAuditLog() {
  const { auditLog, clearAuditLog } = useDPDPStore();

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

  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-800"><span aria-hidden="true">📋</span> DPDP Audit Log</h3>
          <p className="text-xs text-gray-500">Sovereign compliance trail (last {auditLog.length} entries)</p>
        </div>
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
