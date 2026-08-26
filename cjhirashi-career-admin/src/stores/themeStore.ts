import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Theme mode selected by the user. `system` follows the OS-level
 * `prefers-color-scheme` media query.
 */
export type ThemeMode = 'light' | 'system' | 'dark'

/** The actual theme applied to the DOM (never `system`). */
export type ResolvedTheme = 'light' | 'dark'

interface ThemeState {
  theme: ThemeMode
  resolvedTheme: ResolvedTheme
  setTheme: (theme: ThemeMode) => void
}

const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined'

const systemPrefersDark = (): boolean =>
  isBrowser && typeof window.matchMedia === 'function'
    ? window.matchMedia('(prefers-color-scheme: dark)').matches
    : false

const resolveTheme = (theme: ThemeMode): ResolvedTheme =>
  theme === 'system' ? (systemPrefersDark() ? 'dark' : 'light') : theme

/**
 * Applies the resolved theme to <html data-theme="...">. This is the same
 * attribute set synchronously by the blocking inline script in index.html
 * (before first paint), so calling this again on hydration is idempotent
 * and does not cause a flash of incorrect theme.
 */
const applyThemeToDom = (resolved: ResolvedTheme): void => {
  if (isBrowser) {
    document.documentElement.setAttribute('data-theme', resolved)
  }
}

export const THEME_STORAGE_KEY = 'admin-theme-store'

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'system',
      resolvedTheme: resolveTheme('system'),

      setTheme: (theme) => {
        const resolvedTheme = resolveTheme(theme)
        applyThemeToDom(resolvedTheme)
        set({ theme, resolvedTheme })
      },
    }),
    {
      name: THEME_STORAGE_KEY,
      onRehydrateStorage: () => (state) => {
        // Re-sync the DOM + resolvedTheme once the persisted value (if any)
        // has been read from localStorage. The inline script in index.html
        // already applied a best-effort value pre-paint; this just makes
        // sure the React/Zustand state matches it exactly.
        if (state) {
          const resolvedTheme = resolveTheme(state.theme)
          state.resolvedTheme = resolvedTheme
          applyThemeToDom(resolvedTheme)
        }
      },
    }
  )
)

if (isBrowser && typeof window.matchMedia === 'function') {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

  const handleSystemThemeChange = (): void => {
    const { theme } = useThemeStore.getState()
    if (theme !== 'system') return
    const resolvedTheme = resolveTheme('system')
    applyThemeToDom(resolvedTheme)
    useThemeStore.setState({ resolvedTheme })
  }

  if (typeof mediaQuery.addEventListener === 'function') {
    mediaQuery.addEventListener('change', handleSystemThemeChange)
  } else if (typeof (mediaQuery as MediaQueryList).addListener === 'function') {
    // Safari < 14 fallback
    ;(mediaQuery as MediaQueryList).addListener(handleSystemThemeChange)
  }
}
