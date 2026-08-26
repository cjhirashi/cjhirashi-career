import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useThemeStore } from '@/stores/themeStore'

describe('themeStore', () => {
  beforeEach(() => {
    useThemeStore.setState({ theme: 'system', resolvedTheme: 'light' })
    document.documentElement.removeAttribute('data-theme')
  })

  it('should default to system theme', () => {
    expect(useThemeStore.getState().theme).toBe('system')
  })

  it('should switch to light theme', () => {
    useThemeStore.getState().setTheme('light')
    expect(useThemeStore.getState().theme).toBe('light')
    expect(useThemeStore.getState().resolvedTheme).toBe('light')
  })

  it('should switch to dark theme', () => {
    useThemeStore.getState().setTheme('dark')
    expect(useThemeStore.getState().theme).toBe('dark')
    expect(useThemeStore.getState().resolvedTheme).toBe('dark')
  })

  it('should apply data-theme attribute to <html> when theme changes', () => {
    useThemeStore.getState().setTheme('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')

    useThemeStore.getState().setTheme('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('should resolve "system" using matchMedia (mocked as light by default)', () => {
    useThemeStore.getState().setTheme('system')
    expect(useThemeStore.getState().resolvedTheme).toBe('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('should resolve "system" to dark when the OS prefers dark', () => {
    const matchMediaMock = vi.fn().mockImplementation((query: string) => ({
      matches: true,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: matchMediaMock,
    })

    useThemeStore.getState().setTheme('system')
    expect(useThemeStore.getState().resolvedTheme).toBe('dark')
  })
})
