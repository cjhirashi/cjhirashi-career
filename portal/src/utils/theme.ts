import { ResolvedTheme, ThemeMode } from '@/types'

/**
 * Theme engine shared by the blocking inline script in index.html and the
 * Zustand UI store. Keep this logic in sync with the <script> in index.html
 * (that copy must stay dependency-free/inlineable, so it is duplicated
 * there in plain JS - any behavioral change here should be mirrored there).
 */

export const THEME_STORAGE_KEY = 'theme'

export const THEME_MODES: ThemeMode[] = ['light', 'system', 'dark']

export const isThemeMode = (value: unknown): value is ThemeMode =>
  value === 'light' || value === 'system' || value === 'dark'

export const systemPrefersDark = (): boolean =>
  typeof window !== 'undefined' &&
  typeof window.matchMedia === 'function' &&
  window.matchMedia('(prefers-color-scheme: dark)').matches

export const resolveTheme = (mode: ThemeMode): ResolvedTheme =>
  mode === 'system' ? (systemPrefersDark() ? 'dark' : 'light') : mode

export const getStoredTheme = (): ThemeMode => {
  if (typeof window === 'undefined') return 'system'
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY)
    return isThemeMode(stored) ? stored : 'system'
  } catch {
    return 'system'
  }
}

export const persistTheme = (mode: ThemeMode): void => {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, mode)
  } catch {
    // localStorage may be unavailable (private mode, disabled) - ignore.
  }
}

/**
 * Applies the resolved theme to <html> via both the data-theme attribute
 * (used by the CSS custom properties in index.css) and the `dark` class
 * (used by Tailwind's `dark:` variant). Returns the resolved theme.
 */
export const applyTheme = (mode: ThemeMode): ResolvedTheme => {
  const resolved = resolveTheme(mode)
  if (typeof document !== 'undefined') {
    const root = document.documentElement
    root.setAttribute('data-theme', resolved)
    root.classList.toggle('dark', resolved === 'dark')
  }
  return resolved
}
