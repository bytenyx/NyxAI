import { create } from 'zustand'
import type { DataSource } from '../types/datasource'
import type { Knowledge } from '../types/knowledge'

interface SettingsState {
  isOpen: boolean
  activeTab: 'datasource' | 'knowledge' | 'agentConfig'
  slidePanel: {
    open: boolean
    mode: 'add' | 'edit'
    type: 'datasource' | 'knowledge'
    data?: DataSource | Knowledge
  } | null

  datasources: DataSource[]
  knowledge: Knowledge[]
  knowledgeTags: string[]

  openSettings: () => void
  closeSettings: () => void
  setActiveTab: (tab: 'datasource' | 'knowledge' | 'agentConfig') => void
  openSlidePanel: (
    mode: 'add' | 'edit',
    type: 'datasource' | 'knowledge',
    data?: DataSource | Knowledge
  ) => void
  closeSlidePanel: () => void
  setDatasources: (datasources: DataSource[]) => void
  setKnowledge: (knowledge: Knowledge[]) => void
  setKnowledgeTags: (tags: string[]) => void
}

export const useSettingsStore = create<SettingsState>((set) => ({
  isOpen: false,
  activeTab: 'datasource',
  slidePanel: null,
  datasources: [],
  knowledge: [],
  knowledgeTags: [],

  openSettings: () => set({ isOpen: true }),
  closeSettings: () => set({ isOpen: false, slidePanel: null }),
  setActiveTab: (tab) => set({ activeTab: tab }),

  openSlidePanel: (mode, type, data) =>
    set({
      slidePanel: { open: true, mode, type, data },
    }),

  closeSlidePanel: () => set({ slidePanel: null }),

  setDatasources: (datasources) => set({ datasources }),
  setKnowledge: (knowledge) => set({ knowledge }),
  setKnowledgeTags: (tags) => set({ knowledgeTags: tags }),
}))
