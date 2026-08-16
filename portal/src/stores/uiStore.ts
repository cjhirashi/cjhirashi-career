import { create } from 'zustand'
import { UIState } from '@/types'

export const useUIStore = create<UIState>(set => ({
  theme: 'light',
  mobileMenuOpen: false,
  loading: false,
  error: null,

  toggleTheme: () =>
    set(state => ({
      theme: state.theme === 'light' ? 'dark' : 'light',
    })),

  toggleMobileMenu: () =>
    set(state => ({
      mobileMenuOpen: !state.mobileMenuOpen,
    })),

  setLoading: (loading: boolean) => set({ loading }),

  setError: (error: string | null) => set({ error }),
}))
