import { create } from 'zustand'
import { UIState } from '@/types'
import { applyTheme, getStoredTheme, persistTheme } from '@/utils/theme'

// Read the persisted/system preference and (re)apply it to the DOM.
// This is idempotent with the blocking inline script in index.html, so it
// never causes a visible flash/flip on mount - it just syncs React state
// with whatever the DOM already reflects.
const initialTheme = getStoredTheme()
const initialResolvedTheme = applyTheme(initialTheme)

export const useUIStore = create<UIState>(set => ({
  theme: initialTheme,
  resolvedTheme: initialResolvedTheme,
  mobileMenuOpen: false,
  loading: false,
  error: null,

  setTheme: (theme) => {
    persistTheme(theme)
    const resolvedTheme = applyTheme(theme)
    set({ theme, resolvedTheme })
  },

  toggleMobileMenu: () =>
    set(state => ({
      mobileMenuOpen: !state.mobileMenuOpen,
    })),

  setMobileMenuOpen: (open: boolean) => set({ mobileMenuOpen: open }),

  setLoading: (loading: boolean) => set({ loading }),

  setError: (error: string | null) => set({ error }),
}))

// Keep resolvedTheme in sync with OS-level changes while the user's
// preference is 'system' (e.g. switching the OS from light to dark).
if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

  const handleSystemChange = () => {
    if (useUIStore.getState().theme !== 'system') return
    const resolvedTheme = applyTheme('system')
    useUIStore.setState({ resolvedTheme })
  }

  if (typeof mediaQuery.addEventListener === 'function') {
    mediaQuery.addEventListener('change', handleSystemChange)
  } else if (typeof mediaQuery.addListener === 'function') {
    // Safari < 14 fallback
    mediaQuery.addListener(handleSystemChange)
  }
}
