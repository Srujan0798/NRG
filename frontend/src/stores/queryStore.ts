import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface QueryHistoryEntry {
  id: string;
  query: string;
  timestamp: number;
  persona: 'researcher' | 'government' | 'industry';
  resultsCount: number;
  error?: string;
}

export interface StreamingQuerySnapshot {
  phase: 'idle' | 'understanding' | 'parsing' | 'planning' | 'planned' | 'searching_records' | 'checking_documents' | 'querying' | 'executing' | 'synthesizing' | 'verifying' | 'verified' | 'error';
  answer: string;
  auditEventId?: string;
  error?: string;
}

export interface PersonaSwitchSnapshot {
  from: 'researcher' | 'government' | 'industry' | 'anonymous';
  to: 'researcher' | 'government' | 'industry';
  switchedAt: number;
  lastQuery?: string;
}

interface QueryState {
  history: QueryHistoryEntry[];
  currentQuery: string;
  isSearching: boolean;
  lastResult: unknown;
  streaming: StreamingQuerySnapshot;
  personaSwitch: PersonaSwitchSnapshot | null;
  
  setCurrentQuery: (query: string) => void;
  setIsSearching: (loading: boolean) => void;
  addToHistory: (entry: Omit<QueryHistoryEntry, 'id' | 'timestamp'>) => void;
  clearHistory: () => void;
  setLastResult: (result: unknown) => void;
  setStreaming: (snapshot: Partial<StreamingQuerySnapshot>) => void;
  resetStreaming: () => void;
  switchPersona: (snapshot: Omit<PersonaSwitchSnapshot, 'switchedAt'>) => void;
}

const initialStreaming: StreamingQuerySnapshot = {
  phase: 'idle',
  answer: '',
};

export const useQueryStore = create<QueryState>()(
  persist(
    (set, _get) => ({
      history: [],
      currentQuery: '',
      isSearching: false,
      lastResult: null,
      streaming: initialStreaming,
      personaSwitch: null,

      setCurrentQuery: (query) => set({ currentQuery: query }),
      setIsSearching: (loading) => set({ isSearching: loading }),
      
      addToHistory: (entry) => set((state) => ({
        history: [
          {
            ...entry,
            id: crypto.randomUUID(),
            timestamp: Date.now(),
          },
          ...state.history.slice(0, 49), // Keep last 50
        ],
      })),

      clearHistory: () => set({ history: [] }),
      setLastResult: (result) => set({ lastResult: result }),
      setStreaming: (snapshot) => set((state) => ({
        streaming: { ...state.streaming, ...snapshot },
      })),
      resetStreaming: () => set({ streaming: initialStreaming }),
      switchPersona: (snapshot) => set({
        personaSwitch: {
          ...snapshot,
          switchedAt: Date.now(),
        },
      }),
    }),
    {
      name: 'nrg-query-state',
      partialize: (state) => ({ history: state.history }),
    }
  )
);
