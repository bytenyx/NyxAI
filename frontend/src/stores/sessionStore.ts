import { create } from 'zustand'
import type { Session, SessionListItem } from '../types'

interface SessionState {
  sessions: SessionListItem[]
  currentSession: Session | null
  isLoading: boolean
  searchQuery: string
  messages: Array<{ role: 'user' | 'assistant'; content: string }>
  loading: boolean

  setSessions: (sessions: SessionListItem[]) => void
  setCurrentSession: (session: Session | null) => void
  addSession: (session: SessionListItem) => void
  updateSession: (session: SessionListItem) => void
  removeSession: (sessionId: string) => void
  setLoading: (loading: boolean) => void
  setSearchQuery: (query: string) => void
  addMessage: (role: 'user' | 'assistant', content: string) => void
  clearMessages: () => void
}

export const useSessionStore = create<SessionState>((set) => ({
  sessions: [],
  currentSession: null,
  isLoading: false,
  searchQuery: '',
  messages: [],
  loading: false,

  setSessions: (sessions) => set({ sessions }),

  setCurrentSession: (session) => set({ currentSession: session }),

  addSession: (session) =>
    set((state) => ({
      sessions: [session, ...state.sessions],
    })),

  updateSession: (session) =>
    set((state) => ({
      sessions: state.sessions.map((s) => (s.id === session.id ? session : s)),
      currentSession:
        state.currentSession?.id === session.id
          ? (session as unknown as Session)
          : state.currentSession,
    })),

  removeSession: (sessionId) =>
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== sessionId),
      currentSession:
        state.currentSession?.id === sessionId ? null : state.currentSession,
    })),

  setLoading: (loading) => set({ isLoading: loading }),

  setSearchQuery: (query) => set({ searchQuery: query }),

  addMessage: (role, content) =>
    set((state) => ({
      messages: [...state.messages, { role, content }],
    })),

  clearMessages: () => set({ messages: [] }),
}))
