import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { dpdpService, CONSENT_SCOPES } from '../services/dpdpService';

export interface DPDPAuditEntry {
  id: string;
  action: 'consent_granted' | 'consent_withdrawn' | 'data_accessed' | 'purpose_limitation' | 'data_export' | 'data_erasure';
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
  isSyncing: boolean;
  lastSyncedAt: number | null;

  grantConsent: (purpose: string, retentionDays: number) => Promise<void>;
  withdrawConsent: (purpose: string) => Promise<void>;
  syncWithBackend: () => Promise<void>;
  addAuditEntry: (entry: Omit<DPDPAuditEntry, 'id' | 'timestamp'>) => void;
  setWithdrawalMode: (active: boolean) => void;
  getConsentStatus: (purpose: string) => ConsentRecord | undefined;
  getExpiringConsents: (days: number) => ConsentRecord[];
  clearAuditLog: () => void;
  exportUserData: () => Promise<Blob>;
  eraseUserData: () => Promise<void>;
}

export const useDPDPStore = create<DPDPState>()(
  persist(
    (set, get) => ({
      consents: {},
      auditLog: [],
      isWithdrawalMode: false,
      isSyncing: false,
      lastSyncedAt: null,

      grantConsent: async (purpose, retentionDays) => {
        const grantedAt = Date.now();
        const expiresAt = grantedAt + retentionDays * 24 * 60 * 60 * 1000;

        set((state) => ({
          consents: {
            ...state.consents,
            [purpose]: { purpose, granted: true, grantedAt, retentionDays, expiresAt },
          },
        }));

        try {
          await dpdpService.grantConsent(purpose);
        } catch (err) {
          console.warn(`Failed to sync grant_consent to backend for scope "${purpose}":`, err);
        }

        set((state) => ({
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

      withdrawConsent: async (purpose) => {
        set((state) => ({
          consents: {
            ...state.consents,
            [purpose]: {
              ...state.consents[purpose],
              granted: false,
              withdrawnAt: Date.now(),
            },
          },
        }));

        try {
          await dpdpService.revokeConsent(purpose);
        } catch (err) {
          console.warn(`Failed to sync revoke_consent to backend for scope "${purpose}":`, err);
        }

        set((state) => ({
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

      syncWithBackend: async () => {
        set({ isSyncing: true });
        try {
          const { consents: backendConsents } = await dpdpService.listConsents();
          const now = Date.now();
          const merged: Record<string, ConsentRecord> = {};

          for (const scope of Object.keys(CONSENT_SCOPES)) {
            const backendRecord = backendConsents.find(c => c.scope === scope);
            const localRecord = get().consents[scope];

            if (backendRecord?.active) {
              merged[scope] = {
                purpose: scope,
                granted: true,
                grantedAt: new Date(backendRecord.granted_at).getTime(),
                retentionDays: 365,
                expiresAt: new Date(backendRecord.granted_at).getTime() + 365 * 24 * 60 * 60 * 1000,
              };
            } else if (backendRecord && !backendRecord.active) {
              merged[scope] = {
                purpose: scope,
                granted: false,
                grantedAt: new Date(backendRecord.granted_at).getTime(),
                withdrawnAt: backendRecord.revoked_at ? new Date(backendRecord.revoked_at).getTime() : undefined,
                retentionDays: 365,
                expiresAt: undefined,
              };
            } else if (localRecord) {
              merged[scope] = localRecord;
            }
          }

          set({ consents: merged, lastSyncedAt: now, isSyncing: false });
        } catch (err) {
          console.warn('Failed to sync consents with backend:', err);
          set({ isSyncing: false });
        }
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

      exportUserData: async () => {
        set((state) => ({
          auditLog: [
            {
              id: crypto.randomUUID(),
              timestamp: Date.now(),
              action: 'data_export',
              persona: 'researcher',
              details: 'User requested data export',
            },
            ...state.auditLog.slice(0, 199),
          ],
        }));
        return dpdpService.exportUserData();
      },

      eraseUserData: async () => {
        set((state) => ({
          auditLog: [
            {
              id: crypto.randomUUID(),
              timestamp: Date.now(),
              action: 'data_erasure',
              persona: 'researcher',
              details: 'User requested data erasure',
            },
            ...state.auditLog.slice(0, 199),
          ],
        }));
        await dpdpService.eraseUserData();
        set({ consents: {}, auditLog: [] });
      },
    }),
    {
      name: 'nrg-dpdp-state',
      partialize: (state) => ({ consents: state.consents, auditLog: state.auditLog }),
    }
  )
);