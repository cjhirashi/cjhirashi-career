import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import { User } from '@/types'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  tokenExpiresAt: Date | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  setUser: (user: User | null) => void
  setTokens: (accessToken: string, refreshToken: string, expiresIn: number) => void
  setAccessToken: (token: string, expiresIn: number) => void
  setError: (error: string | null) => void
  setLoading: (isLoading: boolean) => void
  logout: () => void
  clearError: () => void
  isTokenExpired: () => boolean
  shouldRefreshToken: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    immer((set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      tokenExpiresAt: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setUser: (user) => {
        set((state) => {
          state.user = user
          state.isAuthenticated = user !== null
        })
      },

      setTokens: (accessToken, refreshToken, expiresIn) => {
        set((state) => {
          state.accessToken = accessToken
          state.refreshToken = refreshToken
          state.tokenExpiresAt = new Date(Date.now() + expiresIn * 1000)
        })
      },

      setAccessToken: (accessToken, expiresIn) => {
        set((state) => {
          state.accessToken = accessToken
          state.tokenExpiresAt = new Date(Date.now() + expiresIn * 1000)
        })
      },

      setError: (error) => {
        set((state) => {
          state.error = error
        })
      },

      setLoading: (isLoading) => {
        set((state) => {
          state.isLoading = isLoading
        })
      },

      logout: () => {
        set((state) => {
          state.user = null
          state.accessToken = null
          state.refreshToken = null
          state.tokenExpiresAt = null
          state.isAuthenticated = false
          state.error = null
        })
      },

      clearError: () => {
        set((state) => {
          state.error = null
        })
      },

      isTokenExpired: () => {
        const state = get()
        if (!state.tokenExpiresAt) return true
        return new Date() > state.tokenExpiresAt
      },

      shouldRefreshToken: () => {
        const state = get()
        if (!state.tokenExpiresAt) return false
        const now = new Date()
        const timeUntilExpiry = state.tokenExpiresAt.getTime() - now.getTime()
        const fifteenMinutes = 15 * 60 * 1000
        return timeUntilExpiry < fifteenMinutes && timeUntilExpiry > 0
      },
    })),
    {
      name: 'auth-store',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        tokenExpiresAt: state.tokenExpiresAt
          ? state.tokenExpiresAt.toISOString()
          : null,
        isAuthenticated: state.isAuthenticated,
      }),
      merge: (persistedState: any, currentState) => {
        const merged = {
          ...currentState,
          ...persistedState,
        }

        if (typeof persistedState.tokenExpiresAt === 'string' && persistedState.tokenExpiresAt) {
          merged.tokenExpiresAt = new Date(persistedState.tokenExpiresAt)
        }

        return merged
      },
    }
  )
)
