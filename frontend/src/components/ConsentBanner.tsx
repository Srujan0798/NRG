import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, X, ChevronDown } from 'lucide-react';

interface ConsentBannerProps {
  role?: 'researcher' | 'government' | 'industry';
  onManageConsent?: () => void;
  expiringCount?: number;
}

const ROLE_LABELS = {
  researcher: {
    persona: 'Researcher',
    personaHi: 'शोधकर्ता',
    line1: 'Your research queries are processed to deliver insights from India\'s national research database.',
    line2: 'Your name, affiliation, and query history are retained for 12 months per DPDP Act 2023.',
  },
  government: {
    persona: 'Government Official',
    personaHi: 'सरकारी अधिकारी',
    line1: 'Your policy queries and session data are processed to provide national research intelligence.',
    line2: 'Data is retained per government data governance guidelines. You may request erasure at any time.',
  },
  industry: {
    persona: 'Industry Partner',
    personaHi: 'उद्योग भागीदार',
    line1: 'Your partnership queries and collaboration preferences are used to match with research institutions.',
    line2: 'Anonymized researcher data may be shared for legitimate research collaboration purposes.',
  },
} as const;

export function ConsentBanner({ role = 'researcher', onManageConsent, expiringCount = 0 }: ConsentBannerProps) {
  const [dismissed, setDismissed] = useState(false);
  const labels = ROLE_LABELS[role];

  if (dismissed) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ height: 0, opacity: 0 }}
        animate={{ height: 'auto', opacity: 1 }}
        exit={{ height: 0, opacity: 0 }}
        transition={{ duration: 0.3 }}
        className="overflow-hidden"
      >
        <div className="bg-gradient-to-r from-saffron-50/70 to-nrg-navy-50/80 border-b border-nrg-border backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex items-center gap-4">
              <div className="shrink-0 w-8 h-8 rounded-full bg-saffron-100/70 dark:bg-saffron-900/30 flex items-center justify-center">
                <Shield size={14} className="text-saffron-700 dark:text-saffron-300" />
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm text-nrg-text">
                  <span className="font-semibold">DPDP Act 2023:</span>{' '}
                  {labels.line1}
                </p>
                <p className="text-xs text-nrg-muted mt-0.5">
                  {labels.line2}
                  {expiringCount > 0 && (
                    <span className="ml-2 inline-flex items-center gap-1 bg-saffron-500/20 text-saffron-800 dark:text-saffron-200 px-2 py-0.5 rounded-full text-xs">
                      {expiringCount} consent{expiringCount > 1 ? 's' : ''} expiring soon
                    </span>
                  )}
                </p>
              </div>

              <div className="shrink-0 flex items-center gap-2">
                {onManageConsent && (
                  <button
                    onClick={onManageConsent}
                    className="text-xs font-medium text-saffron-700 dark:text-saffron-300 hover:text-saffron-900 dark:hover:text-saffron-100 flex items-center gap-1 transition-colors"
                    data-testid="manage-consent-btn"
                  >
                    Manage Consent
                    <ChevronDown size={12} />
                  </button>
                )}
                <button
                  onClick={() => setDismissed(true)}
                  className="w-6 h-6 rounded flex items-center justify-center text-saffron-500 hover:text-saffron-700 hover:bg-saffron-100/70 dark:hover:bg-saffron-900/40 transition-colors"
                  aria-label="Dismiss consent banner"
                  data-testid="dismiss-consent-banner"
                >
                  <X size={14} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
