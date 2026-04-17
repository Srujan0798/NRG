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

interface QueryState {
  history: QueryHistoryEntry[];
  currentQuery: string;
  isSearching: boolean;
  lastResult: unknown;
  
  setCurrentQuery: (query: string) => void;
  setIsSearching: (loading: boolean) => void;
  addToHistory: (entry: Omit<QueryHistoryEntry, 'id' | 'timestamp'>) => void;
  clearHistory: () => void;
  setLastResult: (result: unknown) => void;
}

export const useQueryStore = create<QueryState>()(
  persist(
    (set, get) => ({
      history: [],
      currentQuery: '',
      isSearching: false,
      lastResult: null,

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
    }),
    {
      name: 'nrg-query-state',
      partialize: (state) => ({ history: state.history }),
    }
  )
);
