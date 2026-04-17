import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface DPDPAuditEntry {
  id: string;
  action: 'consent_granted' | 'consent_withdrawn' | 'data_accessed' | 'purpose_limitation' | 'data_export';
  timestamp: number;
  persona: string;
  details: string;
  ip?: string;
}

export interface ConsentRecord {
  purpose: string;
  granted: boolean;
  grantedAt?: number;
  withdrawnAt?: number;
  retentionDays: number;
  expiresAt?: number;
}

interface DPDPState {
  consents: Record<string, ConsentRecord>;
  auditLog: DPDPAuditEntry[];
  isWithdrawalMode: boolean;

  grantConsent: (purpose: string, retentionDays: number) => void;
  withdrawConsent: (purpose: string) => void;
  addAuditEntry: (entry: Omit<DPDPAuditEntry, 'id' | 'timestamp'>) => void;
  setWithdrawalMode: (active: boolean) => void;
  getConsentStatus: (purpose: string) => ConsentRecord | undefined;
  getExpiringConsents: (days: number) => ConsentRecord[];
  clearAuditLog: () => void;
}

export const useDPDPStore = create<DPDPState>()(
  persist(
    (set, get) => ({
      consents: {},
      auditLog: [],
      isWithdrawalMode: false,

      grantConsent: (purpose, retentionDays) => {
        const grantedAt = Date.now();
        const expiresAt = grantedAt + retentionDays * 24 * 60 * 60 * 1000;
        
        set((state) => ({
          consents: {
            ...state.consents,
            [purpose]: { purpose, granted: true, grantedAt, retentionDays, expiresAt },
          },
          auditLog: [
            {
              id: crypto.randomUUID(),
              timestamp: Date.now(),
              action: 'consent_granted',
              persona: 'researcher',
              details: `Consent granted for: ${purpose} (${retentionDays} days)`,
            },
            ...state.auditLog.slice(0, 199),
          ],
        }));
      },

      withdrawConsent: (purpose) => {
        set((state) => ({
          consents: {
            ...state.consents,
            [purpose]: {
              ...state.consents[purpose],
              granted: false,
              withdrawnAt: Date.now(),
            },
          },
          auditLog: [
            {
              id: crypto.randomUUID(),
              timestamp: Date.now(),
              action: 'consent_withdrawn',
              persona: 'researcher',
              details: `Consent withdrawn for: ${purpose}`,
            },
            ...state.auditLog.slice(0, 199),
          ],
        }));
      },

      addAuditEntry: (entry) => set((state) => ({
        auditLog: [
          {
            ...entry,
            id: crypto.randomUUID(),
            timestamp: Date.now(),
          },
          ...state.auditLog.slice(0, 199),
        ],
      })),

      setWithdrawalMode: (active) => set({ isWithdrawalMode: active }),

      getConsentStatus: (purpose) => get().consents[purpose],

      getExpiringConsents: (days) => {
        const now = Date.now();
        const threshold = now + days * 24 * 60 * 60 * 1000;
        return Object.values(get().consents).filter(
          (c) => c.expiresAt && c.expiresAt < threshold && c.granted
        );
      },

      clearAuditLog: () => set({ auditLog: [] }),
    }),
    {
      name: 'nrg-dpdp-state',
      partialize: (state) => ({ consents: state.consents, auditLog: state.auditLog }),
    }
  )
);
