import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { useUIStore } from '@/stores/uiStore'
import { THEME_STORAGE_KEY } from '@/utils/theme'

describe('useUIStore', () => {
  beforeEach(() => {
    window.localStorage.clear()
    useUIStore.setState({ theme: 'system', resolvedTheme: 'light', mobileMenuOpen: false })
  })

  afterEach(() => {
    useUIStore.setState({ mobileMenuOpen: false })
  })

  it('exposes the default theme/mobileMenu state', () => {
    const state = useUIStore.getState()
    expect(state.mobileMenuOpen).toBe(false)
    expect(['light', 'system', 'dark']).toContain(state.theme)
  })

  it('setTheme updates state, persists to localStorage and applies the DOM attribute', () => {
    useUIStore.getState().setTheme('dark')

    const state = useUIStore.getState()
    expect(state.theme).toBe('dark')
    expect(state.resolvedTheme).toBe('dark')
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('setTheme("light") reverts the DOM attribute', () => {
    useUIStore.getState().setTheme('dark')
    useUIStore.getState().setTheme('light')

    expect(useUIStore.getState().theme).toBe('light')
    expect(useUIStore.getState().resolvedTheme).toBe('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('toggleMobileMenu flips mobileMenuOpen', () => {
    expect(useUIStore.getState().mobileMenuOpen).toBe(false)
    useUIStore.getState().toggleMobileMenu()
    expect(useUIStore.getState().mobileMenuOpen).toBe(true)
    useUIStore.getState().toggleMobileMenu()
    expect(useUIStore.getState().mobileMenuOpen).toBe(false)
  })

  it('setMobileMenuOpen sets an explicit value', () => {
    useUIStore.getState().setMobileMenuOpen(true)
    expect(useUIStore.getState().mobileMenuOpen).toBe(true)
    useUIStore.getState().setMobileMenuOpen(false)
    expect(useUIStore.getState().mobileMenuOpen).toBe(false)
  })

  it('setLoading and setError update their respective fields', () => {
    useUIStore.getState().setLoading(true)
    expect(useUIStore.getState().loading).toBe(true)

    useUIStore.getState().setError('boom')
    expect(useUIStore.getState().error).toBe('boom')

    useUIStore.getState().setError(null)
    expect(useUIStore.getState().error).toBeNull()
  })
})
