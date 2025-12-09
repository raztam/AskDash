import { create } from 'zustand'
import type { DatabaseConnection, ChatSessionListItem, ChatMessage } from '../types'
import { databaseService } from '../services/database'
import { chatService } from '../services/chat'

interface AppState {
  // Database connections
  databases: DatabaseConnection[]
  selectedDatabaseId: number | null
  isLoadingDatabases: boolean

  // Chat sessions
  sessions: ChatSessionListItem[]
  selectedSessionId: number | null
  currentMessages: ChatMessage[]
  isLoadingSessions: boolean

  // UI state
  showSql: boolean
  isSidebarOpen: boolean
  isAskingQuestion: boolean
  showAddDatabaseModal: boolean

  // Actions
  fetchDatabases: () => Promise<void>
  selectDatabase: (id: number | null) => void
  addDatabase: (db: DatabaseConnection) => void
  removeDatabase: (id: number) => void

  fetchSessions: (databaseId?: number) => Promise<void>
  selectSession: (id: number | null) => Promise<void>
  addSession: (session: ChatSessionListItem) => void
  removeSession: (id: number) => void

  addMessage: (message: ChatMessage) => void
  setMessages: (messages: ChatMessage[]) => void

  setShowSql: (show: boolean) => void
  toggleSidebar: () => void
  setIsAskingQuestion: (asking: boolean) => void
  setShowAddDatabaseModal: (show: boolean) => void
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  databases: [],
  selectedDatabaseId: null,
  isLoadingDatabases: false,

  sessions: [],
  selectedSessionId: null,
  currentMessages: [],
  isLoadingSessions: false,

  showSql: false,
  isSidebarOpen: true,
  isAskingQuestion: false,
  showAddDatabaseModal: false,

  // Database actions
  fetchDatabases: async () => {
    set({ isLoadingDatabases: true })
    try {
      const databases = await databaseService.getAll()
      set({ databases, isLoadingDatabases: false })

      // Select first database if none selected
      if (!get().selectedDatabaseId && databases.length > 0) {
        get().selectDatabase(databases[0].id)
      }
    } catch (error) {
      console.error('Failed to fetch databases:', error)
      set({ isLoadingDatabases: false })
    }
  },

  selectDatabase: (id: number | null) => {
    set({
      selectedDatabaseId: id,
      selectedSessionId: null,
      currentMessages: [],
    })
    if (id) {
      get().fetchSessions(id)
    }
  },

  addDatabase: (db: DatabaseConnection) => {
    set((state) => ({
      databases: [...state.databases, db],
    }))
  },

  removeDatabase: (id: number) => {
    set((state) => ({
      databases: state.databases.filter((db) => db.id !== id),
      selectedDatabaseId: state.selectedDatabaseId === id ? null : state.selectedDatabaseId,
    }))
  },

  // Session actions
  fetchSessions: async (databaseId?: number) => {
    set({ isLoadingSessions: true })
    try {
      const sessions = await chatService.getSessions(databaseId)
      set({ sessions, isLoadingSessions: false })
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
      set({ isLoadingSessions: false })
    }
  },

  selectSession: async (id: number | null) => {
    set({ selectedSessionId: id })

    if (id) {
      try {
        const session = await chatService.getSession(id)
        set({ currentMessages: session.messages || [] })
      } catch (error) {
        console.error('Failed to fetch session:', error)
        set({ currentMessages: [] })
      }
    } else {
      set({ currentMessages: [] })
    }
  },

  addSession: (session: ChatSessionListItem) => {
    set((state) => ({
      sessions: [session, ...state.sessions],
    }))
  },

  removeSession: (id: number) => {
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== id),
      selectedSessionId: state.selectedSessionId === id ? null : state.selectedSessionId,
      currentMessages: state.selectedSessionId === id ? [] : state.currentMessages,
    }))
  },

  // Message actions
  addMessage: (message: ChatMessage) => {
    set((state) => ({
      currentMessages: [...state.currentMessages, message],
    }))
  },

  setMessages: (messages: ChatMessage[]) => {
    set({ currentMessages: messages })
  },

  // UI actions
  setShowSql: (show: boolean) => set({ showSql: show }),

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

  setIsAskingQuestion: (asking: boolean) => set({ isAskingQuestion: asking }),

  setShowAddDatabaseModal: (show: boolean) => set({ showAddDatabaseModal: show }),
}))
