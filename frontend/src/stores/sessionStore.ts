import { create } from 'zustand'
import type { Session } from '../types'

interface SessionState {
  currentSession: Session | null
  messages: Array<{ role: 'user' | 'assistant'; content: string }>
  loading: boolean
  setCurrentSession: (session: Session | null) => void
  addMessage: (role: 'user' | 'assistant', content: string) => void
  setLoading: (loading: boolean) => void
  clearMessages: () => void
}

export const useSessionStore = create<SessionState>((set) => ({
  currentSession: null,
  messages: [],
  loading: false,
  setCurrentSession: (session) => set({ currentSession: session }),
  addMessage: (role, content) =>
    set((state) => ({ messages: [...state.messages, { role, content }] })),
  setLoading: (loading) => set({ loading }),
  clearMessages: () => set({ messages: [] }),
}))
