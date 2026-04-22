import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Download, Trash2, CheckCircle2, XCircle, RefreshCw, AlertTriangle, Loader2 } from 'lucide-react';
import { useDPDPStore } from '../stores/dpdpStore';
import { dpdpService, CONSENT_SCOPES } from '../services/dpdpService';
import type { ConsentScope } from '../services/dpdpService';

interface DPDPPanelProps {
  role?: 'researcher' | 'government' | 'industry';
  onClose?: () => void;
}

function ConfirmationDialog({
  title,
  message,
  confirmLabel,
  confirmDanger,
  onConfirm,
  onCancel,
}: {
  title: string;
  message: string;
  confirmLabel: string;
  confirmDanger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-white dark:bg-navy-800 rounded-2xl shadow-2xl max-w-sm w-full mx-4 overflow-hidden border border-slate-200 dark:border-navy-700"
      >
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            {confirmDanger ? (
              <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                <AlertTriangle size={18} className="text-red-600 dark:text-red-400" />
              </div>
            ) : (
              <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                <Shield size={18} className="text-amber-600 dark:text-amber-400" />
              </div>
            )}
            <div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">{title}</h3>
            </div>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">{message}</p>
          <div className="flex gap-3">
            <button
              onClick={onCancel}
              className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-navy-600 text-slate-700 dark:text-slate-300 text-sm font-medium hover:bg-slate-50 dark:hover:bg-navy-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              className={`flex-1 px-4 py-2.5 rounded-xl text-sm font-medium text-white transition-colors ${
                confirmDanger
                  ? 'bg-red-500 hover:bg-red-600'
                  : 'bg-amber-500 hover:bg-amber-600'
              }`}
            >
              {confirmLabel}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export function DPDPPanel({ role = 'researcher', onClose }: DPDPPanelProps) {
  const { consents, syncWithBackend, withdrawConsent, grantConsent, exportUserData, eraseUserData, getExpiringConsents } = useDPDPStore();
  const [isExporting, setIsExporting] = useState(false);
  const [isErasing, setIsErasing] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);
  const [eraseSuccess, setEraseSuccess] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState<{ type: 'erase' | null }>({ type: null });
  const [syncing, setSyncing] = useState(false);

  const expiringConsents = getExpiringConsents(30);

  useEffect(() => {
    const sync = async () => {
      setSyncing(true);
      await syncWithBackend();
      setSyncing(false);
    };
    sync();
  }, []);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const blob = await exportUserData();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `nrg-data-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setIsExporting(false);
    }
  };

  const handleErase = async () => {
    setConfirmDialog({ type: null });
    setIsErasing(true);
    try {
      await eraseUserData();
      setEraseSuccess(true);
      setTimeout(() => {
        setEraseSuccess(false);
        onClose?.();
      }, 2000);
    } catch (err) {
      console.error('Erasure failed:', err);
    } finally {
      setIsErasing(false);
    }
  };

  return (
    <div className="space-y-6">
      <AnimatePresence>
        {confirmDialog.type === 'erase' && (
          <ConfirmationDialog
            title="Erase All My Data"
            message="This will permanently anonymize your query history and delete your consent records. This action cannot be undone within the 30-day grace period per DPDP Act 2023."
            confirmLabel="Erase My Data"
            confirmDanger
            onConfirm={handleErase}
            onCancel={() => setConfirmDialog({ type: null })}
          />
        )}
      </AnimatePresence>

      {eraseSuccess && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl p-4 flex items-center gap-3"
        >
          <CheckCircle2 size={18} className="text-green-600 dark:text-green-400 shrink-0" />
          <p className="text-sm text-green-800 dark:text-green-200">
            Data erasure initiated. You will be logged out and redirected shortly.
          </p>
        </motion.div>
      )}

      {expiringConsents.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl p-4"
        >
          <p className="text-sm text-amber-800 dark:text-amber-200 flex items-center gap-2">
            <AlertTriangle size={16} className="shrink-0" />
            <strong>{expiringConsents.length} consent{expiringConsents.length > 1 ? 's' : ''}</strong> will
            expire within 30 days. Please review and re-consent to maintain access.
          </p>
        </motion.div>
      )}

      <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 dark:border-navy-700 flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">Data Processing Consents</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">Per DPDP Act 2023 · आपके अधिकार</p>
          </div>
          <button
            onClick={() => { setSyncing(true); syncWithBackend().finally(() => setSyncing(false)); }}
            disabled={syncing}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300 transition-colors"
            data-testid="sync-consent-btn"
          >
            <RefreshCw size={12} className={syncing ? 'animate-spin' : ''} />
            {syncing ? 'Syncing…' : 'Sync'}
          </button>
        </div>

        <div className="divide-y divide-slate-100 dark:divide-navy-700">
          {(Object.keys(CONSENT_SCOPES) as ConsentScope[]).map((scope) => {
            const record = consents[scope];
            const isGranted = record?.granted ?? false;
            const expiresAt = record?.expiresAt ? new Date(record.expiresAt).toLocaleDateString('en-IN') : null;

            return (
              <div key={scope} className="px-5 py-4 flex items-center gap-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  isGranted ? 'bg-green-100 dark:bg-green-900/30' : 'bg-slate-100 dark:bg-navy-700'
                }`}>
                  {isGranted ? (
                    <CheckCircle2 size={16} className="text-green-600 dark:text-green-400" />
                  ) : (
                    <XCircle size={16} className="text-slate-400 dark:text-slate-500" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 dark:text-white">
                    {CONSENT_SCOPES[scope]}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Scope: <code className="text-xs">{scope}</code>
                    {expiresAt && isGranted && (
                      <span className="ml-2 text-green-600 dark:text-green-400">Expires: {expiresAt}</span>
                    )}
                  </p>
                </div>

                <div className="shrink-0">
                  {isGranted ? (
                    <button
                      onClick={() => withdrawConsent(scope)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium border border-red-200 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                      data-testid={`revoke-${scope}`}
                    >
                      Revoke
                    </button>
                  ) : (
                    <button
                      onClick={() => grantConsent(scope, 365)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400 hover:bg-violet-200 dark:hover:bg-violet-900/50 transition-colors"
                      data-testid={`grant-${scope}`}
                    >
                      Grant
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <Download size={16} className="text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-white">Export My Data</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">DPDP Right to Access</p>
            </div>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 mb-4">
            Download all your query history, consent records, and audit trail as a JSON file.
          </p>
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="w-full px-4 py-2.5 rounded-xl text-sm font-medium bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            data-testid="export-data-btn"
          >
            {isExporting ? (
              <><Loader2 size={14} className="animate-spin" /> Preparing export…</>
            ) : exportSuccess ? (
              <><CheckCircle2 size={14} /> Downloaded!</>
            ) : (
              <><Download size={14} /> Download Data</>
            )}
          </button>
        </div>

        <div className="bg-white dark:bg-navy-800 rounded-2xl border border-red-200 dark:border-red-900/50 shadow-md p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <Trash2 size={16} className="text-red-600 dark:text-red-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-white">Erase My Data</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">DPDP Right to Erasure</p>
            </div>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 mb-4">
            Permanently delete your PII. Query history will be anonymized and consent records removed. 30-day grace period applies.
          </p>
          <button
            onClick={() => setConfirmDialog({ type: 'erase' })}
            disabled={isErasing}
            className="w-full px-4 py-2.5 rounded-xl text-sm font-medium bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            data-testid="erase-data-btn"
          >
            {isErasing ? (
              <><Loader2 size={14} className="animate-spin" /> Erasing…</>
            ) : (
              <><Trash2 size={14} /> Request Erasure</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}