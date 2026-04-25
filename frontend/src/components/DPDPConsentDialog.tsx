import React, { useState, useEffect, useRef } from 'react';

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
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      role="presentation"
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dpdp-dialog-title"
        aria-describedby="dpdp-dialog-desc"
        className="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 overflow-hidden border border-yellow-200"
      >
        <div className="bg-gradient-to-r from-yellow-50 to-amber-50 px-6 py-4 border-b border-yellow-200">
          <div className="flex items-center gap-3">
            <span role="img" aria-label="Shield protection" className="text-2xl">🛡️</span>
            <div>
              <h2 id="dpdp-dialog-title" className="text-lg font-bold text-gray-900">DPDP Consent Required</h2>
              <p id="dpdp-dialog-desc" className="text-xs text-gray-600">डेटा संरक्षण अनुमति · Data Protection Authorization</p>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 space-y-4">
          <div className="bg-blue-50 rounded-lg p-3 text-sm">
            <div className="font-semibold text-blue-800 mb-1">Purpose of Data Use</div>
            <div className="text-blue-700">{dataPurpose}</div>
          </div>

          <div className="bg-green-50 rounded-lg p-3 text-sm">
            <div className="font-semibold text-green-800 mb-1">Data Retention Period</div>
            <div className="text-green-700">{retentionDays} days from access date</div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3 text-xs space-y-1 text-gray-700">
            <div className="font-semibold">Your Rights (DPDP Act 2023):</div>
            <ul className="list-disc list-inside space-y-0.5 ml-1">
              <li>Right to withdraw consent at any time</li>
              <li>Right to data portability</li>
              <li>Right to correction and erasure</li>
              <li>Right to grievance redressal</li>
            </ul>
          </div>

          <label htmlFor="dpdp-ack-checkbox" className="flex items-start gap-2 text-sm cursor-pointer">
            <input
              id="dpdp-ack-checkbox"
              type="checkbox"
              checked={acknowledged}
              onChange={(e) => setAcknowledged(e.target.checked)}
              className="mt-0.5 w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            />
            <span className="text-gray-700">
              I understand and consent to the data usage as described above, per India's DPDP Act 2023.
            </span>
          </label>
        </div>

        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3">
          <button
            ref={denyButtonRef}
            onClick={onDeny}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition font-medium"
          >
            Deny Access
          </button>
          <button
            onClick={onApprove}
            disabled={!acknowledged}
            aria-disabled={!acknowledged}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition ${
              acknowledged
                ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            Approve & Continue
          </button>
        </div>
      </div>
    </div>
  );
}
