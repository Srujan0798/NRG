import { useDPDPStore } from '../stores/dpdpStore';
import { useState } from 'react';
import { t } from '../i18n'
import { fetchWithTimeout } from '../utils/fetchWithTimeout'

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
      consent_granted: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800',
      consent_withdrawn: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800',
      data_accessed: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800',
      purpose_limitation: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800',
      data_export: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800',
    };
    return map[action] || 'bg-[var(--glass-bg)] text-nrg-muted border-nrg-border';
  };

  const verifyIntegrity = async () => {
    setVerifying(true);
    setVerifyStatus(null);
    try {
      const response = await fetchWithTimeout('/health', { timeoutMs: 5000 });
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
    <div className="nrg-panel overflow-hidden">
      <div className="px-4 py-3 bg-[var(--glass-bg)] border-b border-nrg-border flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-nrg-text"><span aria-hidden="true">📋</span> {t("auto.components.DPDPAuditLog.1")}</h3>
          <p className="text-xs text-nrg-muted">{t("auto.components.DPDPAuditLog.2")}{auditLog.length} {t("auto.components.DPDPAuditLog.3")}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={verifyIntegrity}
            disabled={verifying}
            className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 disabled:opacity-50 transition"
          >
            {verifying ? 'Verifying...' : 'Verify integrity'}
          </button>
          {auditLog.length > 0 && (
            <button
              onClick={clearAuditLog}
              className="text-xs text-nrg-muted hover:text-red-600 transition"
              aria-label={t("auto.components.DPDPAuditLog.4")}
            >
              {t("auto.components.DPDPAuditLog.5")}</button>
          )}
        </div>
      </div>

      {verifyStatus && (
        <div className="mx-4 mt-4 rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 px-3 py-2 text-sm text-green-700 dark:text-green-300">
          {verifyStatus}
        </div>
      )}

      {auditLog.length === 0 ? (
        <div className="p-8 text-center text-nrg-muted text-sm">
          {t("auto.components.DPDPAuditLog.6")}</div>
      ) : (
        <div className="max-h-80 overflow-y-auto scrollbar-thin">
          {auditLog.map((entry) => (
            <div key={entry.id} className="px-4 py-3 border-b border-nrg-border/40 hover:bg-[var(--glass-bg)] transition text-sm">
              <div className="flex items-center gap-2 mb-1">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getActionBadge(entry.action)}`}>
                  {entry.action.replace(/_/g, ' ')}
                </span>
                <span className="text-nrg-muted text-xs">{formatTimestamp(entry.timestamp)}</span>
              </div>
              <div className="text-nrg-text">{entry.details}</div>
              {entry.ip && <div className="text-nrg-muted text-xs mt-0.5">IP: {entry.ip}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
