import React, { useState, useEffect, useRef } from 'react';
import { t } from '../i18n'

export interface DPDPConsentDialogProps {
  isOpen: boolean;
  onApprove: () => void;
  onDeny: () => void;
  dataPurpose?: string;
  retentionDays?: number;
}

export function DPDPConsentDialog({
  isOpen,
  onApprove,
  onDeny,
  dataPurpose = 'Research data analysis and knowledge graph enrichment',
  retentionDays = 365
}: DPDPConsentDialogProps) {
  const [acknowledged, setAcknowledged] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);
  const denyButtonRef = useRef<HTMLButtonElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement;
      denyButtonRef.current?.focus();
    } else if (previousActiveElement.current) {
      previousActiveElement.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onDeny();
      }
      if (e.key === 'Tab') {
        const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (!focusable || focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onDeny]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-sm"
      role="presentation"
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dpdp-dialog-title"
        aria-describedby="dpdp-dialog-desc"
        className="nrg-panel max-w-md w-full mx-4 overflow-hidden border-saffron-200/80"
      >
        <div className="bg-gradient-to-r from-saffron-50/90 to-amber-50/80 dark:from-saffron-900/30 dark:to-amber-900/20 px-6 py-4 border-b border-nrg-border">
          <div className="flex items-center gap-3">
            <span role="img" aria-label={t("auto.components.DPDPConsentDialog.1")} className="text-2xl">🛡️</span>
            <div>
              <h2 id="dpdp-dialog-title" className="text-lg font-bold text-nrg-text">{t("auto.components.DPDPConsentDialog.2")}</h2>
              <p id="dpdp-dialog-desc" className="text-xs text-nrg-muted">{t("auto.components.DPDPConsentDialog.3")}</p>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 space-y-4">
          <div className="rounded-lg p-3 text-sm border border-blue-200/70 bg-blue-50/75 dark:bg-blue-900/20 dark:border-blue-800/50">
            <div className="font-semibold text-blue-800 dark:text-blue-300 mb-1">{t("auto.components.DPDPConsentDialog.4")}</div>
            <div className="text-blue-700 dark:text-blue-200/90">{dataPurpose}</div>
          </div>

          <div className="rounded-lg p-3 text-sm border border-green-200/70 bg-green-50/75 dark:bg-green-900/20 dark:border-green-800/50">
            <div className="font-semibold text-green-800 dark:text-green-300 mb-1">{t("auto.components.DPDPConsentDialog.5")}</div>
            <div className="text-green-700 dark:text-green-200/90">{retentionDays} {t("auto.components.DPDPConsentDialog.6")}</div>
          </div>

          <div className="bg-[var(--glass-bg)] border border-nrg-border rounded-lg p-3 text-xs space-y-1 text-nrg-muted">
            <div className="font-semibold">{t("auto.components.DPDPConsentDialog.7")}</div>
            <ul className="list-disc list-inside space-y-0.5 ml-1">
              <li>{t("auto.components.DPDPConsentDialog.8")}</li>
              <li>{t("auto.components.DPDPConsentDialog.9")}</li>
              <li>{t("auto.components.DPDPConsentDialog.10")}</li>
              <li>{t("auto.components.DPDPConsentDialog.11")}</li>
            </ul>
          </div>

          <label htmlFor="dpdp-ack-checkbox" className="flex items-start gap-2 text-sm cursor-pointer">
            <input
              id="dpdp-ack-checkbox"
              type="checkbox"
              checked={acknowledged}
              onChange={(e) => setAcknowledged(e.target.checked)}
              className="mt-0.5 w-4 h-4 text-saffron-600 border-nrg-border rounded focus:ring-saffron-500"
            />
            <span className="text-nrg-text">
              {t("auto.components.DPDPConsentDialog.12")}</span>
          </label>
        </div>

        <div className="px-6 py-4 bg-[var(--glass-bg)] border-t border-nrg-border flex gap-3">
          <button
            ref={denyButtonRef}
            onClick={onDeny}
            className="flex-1 px-4 py-2 border border-nrg-border rounded-lg text-nrg-text hover:bg-saffron-500/10 transition font-medium"
          >
            {t("auto.components.DPDPConsentDialog.13")}</button>
          <button
            onClick={onApprove}
            disabled={!acknowledged}
            aria-disabled={!acknowledged}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition ${
              acknowledged
                ? 'nrg-btn-primary'
                : 'bg-[var(--nrg-border)] text-nrg-muted cursor-not-allowed'
            }`}
          >
            {t("auto.components.DPDPConsentDialog.14")}</button>
        </div>
      </div>
    </div>
  );
}
