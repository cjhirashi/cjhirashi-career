import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  applyTheme,
  getStoredTheme,
  isThemeMode,
  persistTheme,
  resolveTheme,
  systemPrefersDark,
  THEME_MODES,
  THEME_STORAGE_KEY,
} from '@/utils/theme'

describe('theme utils', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    document.documentElement.classList.remove('dark')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('THEME_MODES', () => {
    it('lists the three supported modes in pill order', () => {
      expect(THEME_MODES).toEqual(['light', 'system', 'dark'])
    })
  })

  describe('isThemeMode', () => {
    it('accepts valid modes', () => {
      expect(isThemeMode('light')).toBe(true)
      expect(isThemeMode('system')).toBe(true)
      expect(isThemeMode('dark')).toBe(true)
    })

    it('rejects invalid values', () => {
      expect(isThemeMode('blue')).toBe(false)
      expect(isThemeMode(null)).toBe(false)
      expect(isThemeMode(undefined)).toBe(false)
      expect(isThemeMode(42)).toBe(false)
    })
  })

  describe('systemPrefersDark', () => {
    it('reflects matchMedia matches', () => {
      vi.spyOn(window, 'matchMedia').mockReturnValue({
        matches: true,
        media: '(prefers-color-scheme: dark)',
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      } as unknown as MediaQueryList)

      expect(systemPrefersDark()).toBe(true)
    })
  })

  describe('resolveTheme', () => {
    it('resolves light/dark modes to themselves', () => {
      expect(resolveTheme('light')).toBe('light')
      expect(resolveTheme('dark')).toBe('dark')
    })

    it('resolves system mode using the OS preference', () => {
      vi.spyOn(window, 'matchMedia').mockReturnValue({
        matches: true,
      } as MediaQueryList)
      expect(resolveTheme('system')).toBe('dark')

      vi.spyOn(window, 'matchMedia').mockReturnValue({
        matches: false,
      } as MediaQueryList)
      expect(resolveTheme('system')).toBe('light')
    })
  })

  describe('getStoredTheme / persistTheme', () => {
    it('defaults to system when nothing is stored', () => {
      expect(getStoredTheme()).toBe('system')
    })

    it('round-trips a persisted preference', () => {
      persistTheme('dark')
      expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')
      expect(getStoredTheme()).toBe('dark')
    })

    it('falls back to system for corrupted storage values', () => {
      window.localStorage.setItem(THEME_STORAGE_KEY, 'not-a-theme')
      expect(getStoredTheme()).toBe('system')
    })
  })

  describe('applyTheme', () => {
    it('sets data-theme and toggles the dark class for light', () => {
      const resolved = applyTheme('light')
      expect(resolved).toBe('light')
      expect(document.documentElement.getAttribute('data-theme')).toBe('light')
      expect(document.documentElement.classList.contains('dark')).toBe(false)
    })

    it('sets data-theme and toggles the dark class for dark', () => {
      const resolved = applyTheme('dark')
      expect(resolved).toBe('dark')
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })
  })
})
