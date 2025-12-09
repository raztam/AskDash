import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types'
import { authService } from '../services/auth'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  login: (username: string, password: string) => Promise<void>
  register: (data: { username: string; email: string; password: string; password2: string }) => Promise<void>
  logout: () => void
  setTokens: (access: string, refresh: string) => void
  fetchUser: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authService.login({ username, password })
          set({
            accessToken: response.access,
            refreshToken: response.refresh,
            isAuthenticated: true,
            isLoading: false,
          })
          // Fetch user details
          await get().fetchUser()
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : 'Login failed'
          set({
            error: message,
            isLoading: false,
            isAuthenticated: false,
          })
          throw error
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null })
        try {
          await authService.register(data)
          set({ isLoading: false })
          // After registration, login the user
          await get().login(data.username, data.password)
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : 'Registration failed'
          set({
            error: message,
            isLoading: false,
          })
          throw error
        }
      },

      logout: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        })
      },

      setTokens: (access: string, refresh: string) => {
        set({
          accessToken: access,
          refreshToken: refresh,
          isAuthenticated: true,
        })
      },

      fetchUser: async () => {
        try {
          const user = await authService.getCurrentUser()
          set({ user })
        } catch (error) {
          console.error('Failed to fetch user:', error)
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
    }
  )
)
