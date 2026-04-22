import axios from 'axios';
import { authService } from './authService';

const API_BASE = '';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export const CONSENT_SCOPES = {
  research_access: 'Access research data',
  profile_storage: 'Store user profile',
  query_history: 'Store query history',
  audit_logging: 'Include in audit logs',
  analytics: 'Use for analytics',
} as const;

export type ConsentScope = keyof typeof CONSENT_SCOPES;

export interface ConsentRecord {
  scope: string;
  version: number;
  granted_at: string;
  revoked_at: string | null;
  active: boolean;
  description: string;
}

export const dpdpService = {
  async grantConsent(scope: string): Promise<{ success: boolean; consent_id?: string; granted_at?: string; error?: string }> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.post(
        `/consent?scope=${encodeURIComponent(scope)}`,
        {},
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      return response.data;
    });
  },

  async revokeConsent(scope: string): Promise<{ success: boolean; revoked_at?: string; error?: string }> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.delete(
        `/consent/${encodeURIComponent(scope)}`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      return response.data;
    });
  },

  async listConsents(): Promise<{ consents: ConsentRecord[] }> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.get('/me/consents', {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      return response.data;
    });
  },

  async exportUserData(): Promise<Blob> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.get('/me/data', {
        headers: { Authorization: `Bearer ${accessToken}` },
        responseType: 'blob',
      });
      return response.data;
    });
  },

  async eraseUserData(): Promise<{ success: boolean; consents_deleted?: number; events_anonymized?: number }> {
    return authService.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.delete('/me/data', {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      return response.data;
    });
  },
};